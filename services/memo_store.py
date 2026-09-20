"""memo_store 模块（services 包）
备忘录存储（纯逻辑层，不依赖 Flask、不处理 HTTP）。

备忘以 JSON 文件形式存放在项目根目录下的"备忘录"文件夹里：
    {BASE_DIR}/备忘录/memos.json
与"工作日志"（logs.json）、"待办事项"（todos.json）同一套设计：
可直接查看 / 备份；首次写入时自动创建。

职责：围绕"备忘录"提供增删改查，以及图片文件的存取：
- add_memo()      新增一条备忘，返回自增 id
- all_memos()     按 id 倒序列出全部备忘（最新在前）
- get_memo()      按 id 取单条备忘（编辑弹窗预填用）
- update_memo()   修改某条的标题/内容/图片
- delete_memo()   按 id 删除（连同其图片文件一起删除）
- save_image()    保存一张图片到图片目录，返回文件名
- valid_image_name() 校验图片文件名是否合法（防路径穿越）

图片不写进 JSON（避免文件膨胀），而是以文件形式存放在"备忘录/images/"下，
memos.json 每条备忘只记录图片文件名列表。删除备忘 / 编辑时移除的图片，
其文件会一并清理，避免留下孤儿文件。

与 todo_store 的拆分思路一致：蓝图（memos.py）只做参数解析与渲染，
存储细节全部收敛到这里，方便以后换数据库而不动路由层。
"""

import json  # JSON 序列化：备忘库单文件存储
import os  # 判断文件是否存在、建目录
import re  # 校验图片文件名格式，防路径穿越
import threading  # 读写文件互斥，避免并发新增/编辑时互相覆盖
import uuid  # 生成图片文件唯一名
from datetime import datetime  # 生成创建/修改时间

from config import IMAGE_EXTENSIONS, MEMO_FILE, MEMO_IMAGE_DIR  # 图片扩展名白名单 + 存储路径

_lock = threading.Lock()  # 所有读写都拿同一把锁，保证进程内串行

_TIME_FMT = "%Y-%m-%d %H:%M:%S"  # 存储的时间格式


def _load() -> dict:
    """读取并解析备忘库；文件缺失/损坏时返回空库。"""
    if not os.path.exists(MEMO_FILE):
        return {"next_id": 1, "memos": []}
    try:
        with open(MEMO_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):  # 文件被改坏等异常情况：按空库处理
        return {"next_id": 1, "memos": []}
    if not isinstance(data, dict) or not isinstance(data.get("memos"), list):
        return {"next_id": 1, "memos": []}
    data.setdefault(
        "next_id", max((rec["id"] for rec in data["memos"]), default=0) + 1
    )
    return data


def _save(data: dict) -> None:
    """把整个备忘库写回文件（先写临时文件再原子替换，避免写一半损坏）。"""
    os.makedirs(os.path.dirname(MEMO_FILE), exist_ok=True)
    tmp = MEMO_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, MEMO_FILE)


def _to_row(rec: dict) -> dict:
    """把存储记录转成统一字典：时间为 datetime（与模板/蓝图约定一致）。"""
    return {
        "id": rec["id"],
        "title": rec.get("title", ""),  # 标题（可空，空时页面显示正文前几行）
        "content": rec["content"],
        "category": rec.get("category", ""),  # 分类（自由填写，可空）
        "images": rec.get("images", []),  # 图片文件名列表（完整文件名，如 abc123.png）
        "created_at": datetime.strptime(rec["created_at"], _TIME_FMT),
        "updated_at": (
            datetime.strptime(rec["updated_at"], _TIME_FMT)
            if rec["updated_at"]
            else None
        ),
    }


# 图片文件名必须是 uuid.hex（32 位十六进制）+ 合法图片扩展名。
# 这样既防路径穿越（无目录分隔符），也排除任意文件名。
_VALID_IMAGE_NAME_RE = re.compile(
    r"^[0-9a-f]{32}\.(?:png|jpe?g|gif|bmp|webp|svg|ico)$", re.IGNORECASE
)


def valid_image_name(name: str) -> bool:
    """校验图片文件名是否合法（用于路由和清理前的白名单过滤）。"""
    return bool(name) and bool(_VALID_IMAGE_NAME_RE.fullmatch(name))


def save_image(data: bytes, ext: str) -> str:
    """保存一张图片到图片目录，返回生成的文件名（不会与已有文件重名）。"""
    os.makedirs(MEMO_IMAGE_DIR, exist_ok=True)
    name = uuid.uuid4().hex + ext
    with open(os.path.join(MEMO_IMAGE_DIR, name), "wb") as f:
        f.write(data)
    return name


def _delete_image_files(names) -> None:
    """删除一组图片文件（仅合法的文件名）；失败静默忽略，不影响主流程。"""
    for name in names:
        if not valid_image_name(name):
            continue
        try:
            os.remove(os.path.join(MEMO_IMAGE_DIR, name))
        except OSError:
            pass


def _normalize_images(images) -> list:
    """规整外部传入的图片列表：去重、去空，只保留合法文件名。"""
    out = []
    seen = set()
    for name in images or []:
        name = (name or "").strip()
        if not name or name in seen or not valid_image_name(name):
            continue
        out.append(name)
        seen.add(name)
    return out


def add_memo(title: str, content: str, category: str = "", images=None) -> int:
    """新增一条备忘，返回新记录 id。category 为分类（自由填写，可空）。images 为图片文件名列表。"""
    images = _normalize_images(images)
    category = (category or "").strip()
    with _lock:
        data = _load()
        new_id = data["next_id"]
        data["memos"].append(
            {
                "id": new_id,
                "title": title,
                "content": content,
                "category": category,
                "images": images,
                "created_at": datetime.now().strftime(_TIME_FMT),
                "updated_at": None,
            }
        )
        data["next_id"] = new_id + 1
        _save(data)
        return new_id


def all_memos() -> list:
    """按 id 倒序返回全部备忘（最新在前）。"""
    with _lock:
        data = _load()
    rows = [_to_row(r) for r in data["memos"]]
    rows.sort(key=lambda r: r["id"], reverse=True)
    return rows


def get_memo(memo_id: int):
    """按 id 取单条备忘；不存在返回 None。"""
    with _lock:
        data = _load()
    for rec in data["memos"]:
        if rec["id"] == memo_id:
            return _to_row(rec)
    return None


def update_memo(memo_id: int, title: str, content: str, category: str = "", images=None) -> bool:
    """修改某条备忘的标题/内容/分类/图片；返回是否真的更新到（id 不存在返回 False）。

    编辑时被移除的旧图片文件会一并删除，避免留下孤儿文件。
    """
    images = _normalize_images(images)
    category = (category or "").strip()
    removed = []
    with _lock:
        data = _load()
        for rec in data["memos"]:
            if rec["id"] == memo_id:
                old = set(rec.get("images", []))
                new = set(images)
                removed = list(old - new)  # 被移除的旧图片
                rec["title"] = title
                rec["content"] = content
                rec["category"] = category
                rec["images"] = images
                rec["updated_at"] = datetime.now().strftime(_TIME_FMT)
                _save(data)
                break
        else:
            return False
    _delete_image_files(removed)  # 释放锁后再删文件，避免持有锁太久
    return True


def delete_memo(memo_id: int) -> bool:
    """按 id 删除备忘；返回是否真的删到（id 不存在返回 False）。关联图片一并删除。"""
    removed = []
    with _lock:
        data = _load()
        new_memos = []
        found = False
        for rec in data["memos"]:
            if rec["id"] == memo_id:
                found = True
                removed = rec.get("images", [])
            else:
                new_memos.append(rec)
        if not found:
            return False
        data["memos"] = new_memos
        _save(data)
    _delete_image_files(removed)  # 释放锁后再删文件，避免持有锁太久
    return True

"""memo_store 模块（services 包）
备忘录存储（纯逻辑层，不依赖 Flask、不处理 HTTP）。

备忘以 JSON 文件形式存放在项目根目录下的"备忘录"文件夹里：
    {BASE_DIR}/备忘录/memos.json
与"工作日志"（logs.json）、"待办事项"（todos.json）同一套设计：
可直接查看 / 备份；首次写入时自动创建。

职责：围绕"备忘录"提供增删改查：
- add_memo()      新增一条备忘，返回自增 id
- all_memos()     按 id 倒序列出全部备忘（最新在前）
- get_memo()      按 id 取单条备忘（编辑弹窗预填用）
- update_memo()   修改某条的标题/内容
- delete_memo()   按 id 删除

与 todo_store 的拆分思路一致：蓝图（memos.py）只做参数解析与渲染，
存储细节全部收敛到这里，方便以后换数据库而不动路由层。
"""

import json  # JSON 序列化：备忘库单文件存储
import os  # 判断文件是否存在、建目录
import threading  # 读写文件互斥，避免并发新增/编辑时互相覆盖
from datetime import datetime  # 生成创建/修改时间

from config import MEMO_FILE  # 备忘存储文件（位于项目根目录下的"备忘录"文件夹）

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
        "created_at": datetime.strptime(rec["created_at"], _TIME_FMT),
        "updated_at": (
            datetime.strptime(rec["updated_at"], _TIME_FMT)
            if rec["updated_at"]
            else None
        ),
    }


def add_memo(title: str, content: str) -> int:
    """新增一条备忘，返回新记录 id。"""
    with _lock:
        data = _load()
        new_id = data["next_id"]
        data["memos"].append(
            {
                "id": new_id,
                "title": title,
                "content": content,
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


def update_memo(memo_id: int, title: str, content: str) -> bool:
    """修改某条备忘的标题/内容；返回是否真的更新到（id 不存在返回 False）。"""
    with _lock:
        data = _load()
        for rec in data["memos"]:
            if rec["id"] == memo_id:
                rec["title"] = title
                rec["content"] = content
                rec["updated_at"] = datetime.now().strftime(_TIME_FMT)
                _save(data)
                return True
        return False


def delete_memo(memo_id: int) -> bool:
    """按 id 删除备忘；返回是否真的删到（id 不存在返回 False）。"""
    with _lock:
        data = _load()
        before = len(data["memos"])
        data["memos"] = [rec for rec in data["memos"] if rec["id"] != memo_id]
        if len(data["memos"]) == before:
            return False
        _save(data)
        return True

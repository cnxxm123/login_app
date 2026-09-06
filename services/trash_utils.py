"""trash_utils 模块（services 包）
回收站（纯逻辑层，不依赖 Flask）。

设计：删除不是物理清除，而是把文件/目录移动到 TRASH_DIR（软删除），
每个条目旁写一个同名 .json 记录"原始路径 + 删除时间"，供一键还原。
确认无误后才彻底删除或清空（那才是真正的物理删除）。

【为什么放在 BASE_DIR/_trash 而不放在 TEXT_DIR 里？】
- 浏览/搜索的根是 TEXT_DIR，回收站放外面就不会被当作普通内容误浏览
- 与 _thumbs 同级的项目私有目录，物理删除时不污染内容目录
"""

import json
import os
import shutil
import time

from config import TRASH_DIR
from services.path_utils import safe_path  # 还原时校验原路径仍落在 TEXT_DIR 内


def ensure_trash_dir():
    """确保回收站目录存在（幂等）。"""
    os.makedirs(TRASH_DIR, exist_ok=True)


def _unique_dest(name: str) -> str:
    """返回回收站内不冲突的目标路径；重名时追加时间戳后缀。"""
    dest = os.path.join(TRASH_DIR, name)
    if not os.path.lexists(dest):
        return dest
    base, ext = os.path.splitext(name)
    ts = time.strftime("%Y%m%d_%H%M%S")
    dest = os.path.join(TRASH_DIR, f"{base}__{ts}{ext}")
    n = 1
    while os.path.lexists(dest):
        dest = os.path.join(TRASH_DIR, f"{base}__{ts}_{n}{ext}")
        n += 1
    return dest


def move_to_trash(subpath: str) -> bool:
    """把 TEXT_DIR 下的文件/目录移入回收站，并记录原始路径。

    用 shutil.move 而非 os.replace：内容目录（TEXT_DIR）与回收站
    可能不在同一磁盘，os.replace 跨盘会抛 WinError 17；
    shutil.move 同盘走 rename（快），跨盘自动退化为 复制+删除。
    返回是否成功（路径非法/不存在返回 False）。
    """
    target = safe_path(subpath)  # 先校验，确保待删除项在 TEXT_DIR 内
    if target is None or not os.path.lexists(target):
        return False
    ensure_trash_dir()
    dest = _unique_dest(os.path.basename(subpath))
    shutil.move(target, dest)
    meta = {"original": subpath, "deleted_at": time.strftime("%Y-%m-%d %H:%M:%S")}
    with open(dest + ".json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False)
    return True


def _entry(name: str) -> str | None:
    """回收站条目安全解析：只允许 TRASH_DIR 下的单层名称，拒绝目录穿越。

    回收站条目都是平铺在 TRASH_DIR 根下的，因此 name 不允许含路径分隔符；
    再用 realpath + commonpath 双重确认最终路径仍在 TRASH_DIR 之内。
    """
    if not name or name in (".", "..") or "/" in name or "\\" in name:
        return None
    entry = os.path.join(TRASH_DIR, name)
    trash_real = os.path.realpath(TRASH_DIR)
    if os.path.commonpath([trash_real, os.path.realpath(entry)]) != trash_real:
        return None
    return entry


def list_trash() -> list[dict]:
    """列出回收站全部条目（不含 .json 元数据文件），按删除时间倒序。

    返回 [{"name", "is_dir", "original", "deleted_at"}, ...]；
    .json 元数据丢失时 original/deleted_at 为空串，不影响展示。
    """
    ensure_trash_dir()
    items = []
    with os.scandir(TRASH_DIR) as it:
        for e in it:
            if e.name.endswith(".json"):  # 跳过元数据文件
                continue
            meta = {}
            meta_path = e.path + ".json"
            if os.path.exists(meta_path):
                try:
                    with open(meta_path, encoding="utf-8") as f:
                        meta = json.load(f)
                except (OSError, ValueError):
                    meta = {}
            items.append({
                "name": e.name,
                "is_dir": e.is_dir(),
                "original": meta.get("original", ""),
                "deleted_at": meta.get("deleted_at", ""),
            })
    items.sort(key=lambda i: i["deleted_at"], reverse=True)  # 最新删除的排最前
    return items


def restore(name: str) -> tuple[bool, str]:
    """把条目还原到原位置；返回 (是否成功, 结果信息)。

    信息取值：
    - "conflict"：原位置已存在同名项 → 前端提示 409
    - "bad_path"：记录的原始路径非法（如已被手动篡改）→ 拒绝
    - 成功时返回原始相对路径，供跳回原目录
    还原时若原父目录已不存在，会自动重建（exist_ok=True）。
    """
    entry = _entry(name)
    if entry is None or not os.path.lexists(entry):
        return False, "not_found"
    meta_path = entry + ".json"
    if not os.path.exists(meta_path):
        return False, "not_found"  # 缺元数据无法得知原位置，按不存在处理
    with open(meta_path, encoding="utf-8") as f:
        meta = json.load(f)
    dest = safe_path(meta.get("original", ""))
    if dest is None:
        return False, "bad_path"
    if os.path.lexists(dest):
        return False, "conflict"
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    # 同盘 rename / 跨盘复制+删除（回收站与内容盘可能不在同一磁盘）
    shutil.move(entry, dest)
    try:
        os.remove(meta_path)
    except OSError:
        pass
    return True, meta.get("original", "")


def permanent_delete(name: str) -> bool:
    """彻底删除单个条目（物理删除，不可恢复）。"""
    entry = _entry(name)
    if entry is None or not os.path.lexists(entry):
        return False
    if os.path.isdir(entry) and not os.path.islink(entry):
        shutil.rmtree(entry)
    else:
        os.remove(entry)
    try:
        os.remove(entry + ".json")
    except OSError:
        pass
    return True


def empty_trash() -> int:
    """清空回收站（全部物理删除）；返回删除的条目数。"""
    ensure_trash_dir()
    count = 0
    with os.scandir(TRASH_DIR) as it:
        for e in it:
            if e.is_dir() and not e.is_symlink():
                shutil.rmtree(e.path)
            else:
                try:
                    os.remove(e.path)
                except OSError:
                    continue
            count += 1
    return count

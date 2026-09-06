"""game_utils 模块（services 包）
游戏卸载/还原（纯逻辑层，不依赖 Flask）。

设计：与文本回收站（trash_utils）同样的"软删除"思路 ——
卸载游戏不是把文件夹物理删掉，而是整体移动到 GAME_UNINSTALL_DIR
（_removed_games）里，旁边写一个同名 .json 记录原游戏名与卸载时间，
可在"已卸载游戏"页一键还原；确认无误后才彻底删除。

【为什么放在 BASE_DIR/_removed_games 而不放进 GAME_DIR？】
- 大厅是扫描 GAME_DIR 下含 index.html 的文件夹，移出去后自动从大厅消失
- 与 _trash / _thumbs 同级的项目私有目录，不会污染游戏目录
- 卸载不等于删除，保留还原机会更安全（用户手滑点错也能找回）
"""

import json
import os
import shutil
import time

from config import GAME_DIR, GAME_UNINSTALL_DIR


def ensure_uninstall_dir():
    """确保卸载备份目录存在（幂等）。"""
    os.makedirs(GAME_UNINSTALL_DIR, exist_ok=True)


def _safe_game_name(name: str) -> str | None:
    """校验游戏名：必须是 GAME_DIR 下的单层目录名，拒绝目录穿越。

    游戏名来自 URL/表单，用户可能传 "../../x" 之类，若直接拼接路径
    会逃逸到 game/ 之外。这里要求：
    1) 非空、不能是 . / ..、不能含路径分隔符（\ /）与空字节；
    2) 用 realpath + commonpath 双重确认最终路径仍在 GAME_DIR 内。
    合法时返回对应绝对路径，否则返回 None。
    """
    if not name or name in (".", "..") or "/" in name or "\\" in name or "\x00" in name:
        return None
    target = os.path.realpath(os.path.join(GAME_DIR, name))
    base = os.path.realpath(GAME_DIR)
    if os.path.commonpath([base, target]) != base:
        return None  # 越界（或不在同一盘符），拒绝
    return target


def _unique_dest(name: str) -> str:
    """返回备份目录内不冲突的目标路径；重名时追加时间戳后缀。

    同一天卸载再还原再卸载同一个游戏时，备份目录里可能已有同名文件夹，
    追加时间戳避免互相覆盖（与 trash_utils._unique_dest 同一思路）。
    """
    dest = os.path.join(GAME_UNINSTALL_DIR, name)
    if not os.path.lexists(dest):
        return dest
    ts = time.strftime("%Y%m%d_%H%M%S")
    dest = os.path.join(GAME_UNINSTALL_DIR, f"{name}__{ts}")
    n = 1
    while os.path.lexists(dest):
        dest = os.path.join(GAME_UNINSTALL_DIR, f"{name}__{ts}_{n}")
        n += 1
    return dest


def _entry(name: str) -> str | None:
    """备份条目安全解析：只允许 GAME_UNINSTALL_DIR 下的单层名称，拒绝目录穿越。

    与 trash_utils._entry 同一思路：先排除含路径分隔符的名字，
    再用 realpath + commonpath 确认最终路径仍在备份目录内。
    """
    if not name or name in (".", "..") or "/" in name or "\\" in name:
        return None
    entry = os.path.join(GAME_UNINSTALL_DIR, name)
    base = os.path.realpath(GAME_UNINSTALL_DIR)
    if os.path.commonpath([base, os.path.realpath(entry)]) != base:
        return None
    return entry


def uninstall(name: str) -> bool:
    """卸载游戏：把 GAME_DIR 下的游戏文件夹移入备份目录，并记录原游戏名。

    用 shutil.move 而非 os.replace：两者同盘走 rename（快），
    shutil.move 跨盘自动退化为 复制+删除，更稳妥。
    返回是否成功（游戏不存在/名字非法返回 False）。
    """
    target = _safe_game_name(name)
    if target is None or not os.path.lexists(target):
        return False
    ensure_uninstall_dir()
    dest = _unique_dest(name)
    shutil.move(target, dest)
    # 写元数据：原游戏名 + 卸载时间，供还原与展示
    meta = {"game": name, "uninstalled_at": time.strftime("%Y-%m-%d %H:%M:%S")}
    with open(dest + ".json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False)
    return True


def list_uninstalled() -> list[dict]:
    """列出已卸载游戏（不含 .json 元数据文件），按卸载时间倒序。

    返回 [{"name", "uninstalled_at"}, ...]；.json 元数据丢失时
    uninstalled_at 为空串，不影响展示。
    """
    ensure_uninstall_dir()
    items = []
    with os.scandir(GAME_UNINSTALL_DIR) as it:
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
                "uninstalled_at": meta.get("uninstalled_at", ""),
            })
    items.sort(key=lambda i: i["uninstalled_at"], reverse=True)  # 最新卸载的排最前
    return items


def restore(name: str) -> tuple[bool, str]:
    """把已卸载游戏还原回 GAME_DIR；返回 (是否成功, 结果信息)。

    信息取值：
    - "not_found"：备份目录里没这个条目
    - "conflict"：GAME_DIR 里已有同名游戏 → 前端提示 409
    - 成功时返回游戏名，供跳回大厅
    """
    entry = _entry(name)
    if entry is None or not os.path.lexists(entry):
        return False, "not_found"
    meta_path = entry + ".json"
    meta = {}
    if os.path.exists(meta_path):
        try:
            with open(meta_path, encoding="utf-8") as f:
                meta = json.load(f)
        except (OSError, ValueError):
            pass
    game = meta.get("game", "") or name  # 优先用记录的原始名，丢失时退回条目名
    if game in ("", ".", "..") or "/" in game or "\\" in game:
        return False, "not_found"
    dest = os.path.join(GAME_DIR, game)
    if os.path.lexists(dest):
        return False, "conflict"  # 大厅里已有同名游戏，避免覆盖
    os.makedirs(GAME_DIR, exist_ok=True)
    shutil.move(entry, dest)
    try:
        os.remove(meta_path)  # 删掉元数据，条目已被"消费"
    except OSError:
        pass
    return True, game


def permanent_delete(name: str) -> bool:
    """彻底删除已卸载游戏（物理删除，不可恢复）。"""
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

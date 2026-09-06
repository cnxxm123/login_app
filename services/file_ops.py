"""file_ops 模块（services 包）
文件/目录移动、复制、批量操作（纯逻辑层，不依赖 Flask）。

只做一件事：围绕"移动/复制"提供安全的单条目与批量操作，
供 manage 蓝图（移动/复制/批量移动/批量复制）使用。

【与其它模块的分工】
- 路径安全校验来自 services/path_utils（纯逻辑层）
- 删除仍走回收站（services/trash_utils，软删除），本模块不做删除
- 批量删除直接复用 trash_utils.move_to_trash，不需要本模块

【命名冲突策略】
目标目录已存在同名项时，不报错，而是自动追加 " (2)" / " (3)"… 序号重命名
（与 Windows 资源管理器"复制 → 名称 (2)"的行为一致）。
批量操作时即使个别条目重名也不会让整批失败。
"""

import os
import shutil

from services.path_utils import safe_path  # 路径安全校验


def _unique_name(dest_dir: str, name: str) -> str:
    """在 dest_dir 内生成不冲突的目标名。

    若 name 已存在，则依次尝试 "原名 (2).ext"、"原名 (3).ext"…
    直到找到空闲名字。用 lexists（软链接也算存在），避免覆盖任何内容。
    """
    base, ext = os.path.splitext(name)
    candidate = name
    n = 2
    while os.path.lexists(os.path.join(dest_dir, candidate)):
        candidate = f"{base} ({n}){ext}"
        n += 1
    return candidate


def _dest_dir(dest_subpath: str) -> str | None:
    """解析目标目录并确认其存在且是目录；非法时返回 None。"""
    dest_dir = safe_path(dest_subpath)  # 防目录穿越
    if dest_dir is None or not os.path.isdir(dest_dir):
        return None
    return dest_dir


def _into_self(src: str, dest_dir: str) -> bool:
    """目录是否会被移/复制进它自己的子目录（禁止，否则会递归/逻辑混乱）。

    源是目录、且目标目录位于源目录内部（commonpath 取公共前缀等于源）时返回 True。
    """
    src_real = os.path.realpath(src)
    dest_real = os.path.realpath(dest_dir)
    return os.path.isdir(src) and os.path.commonpath([src_real, dest_real]) == src_real


def move_item(src_subpath: str, dest_subpath: str) -> tuple[bool, str]:
    """移动单个条目到目标目录；返回 (是否成功, 信息)。

    信息取值：
    - 成功：实际落盘的目标名（可能与原名不同，因重名被自动加序号）
    - 失败：错误码字符串 —— "not_found"（源不存在）/ "bad_dest"（目标目录无效）
      / "into_self"（把目录移进自己的子目录）
    用 shutil.move：同盘走 rename（快），跨盘自动退化为复制+删除。
    """
    src = safe_path(src_subpath)  # 防目录穿越
    if src is None or not os.path.lexists(src):
        return False, "not_found"
    dest_dir = _dest_dir(dest_subpath)
    if dest_dir is None:
        return False, "bad_dest"
    if os.path.realpath(os.path.dirname(src)) == os.path.realpath(dest_dir):
        return False, "bad_dest"  # 目标就是当前所在目录，无需移动
    if _into_self(src, dest_dir):
        return False, "into_self"
    new_name = _unique_name(dest_dir, os.path.basename(src))
    shutil.move(src, os.path.join(dest_dir, new_name))
    return True, new_name


def copy_item(src_subpath: str, dest_subpath: str) -> tuple[bool, str]:
    """复制单个条目到目标目录；返回 (是否成功, 信息)。

    信息取值与 move_item 相同。文件用 copy2（保留修改时间等元数据），
    目录用 copytree 递归复制；目标名冲突时自动加序号。
    """
    src = safe_path(src_subpath)  # 防目录穿越
    if src is None or not os.path.lexists(src):
        return False, "not_found"
    dest_dir = _dest_dir(dest_subpath)
    if dest_dir is None:
        return False, "bad_dest"
    if _into_self(src, dest_dir):
        return False, "into_self"
    new_name = _unique_name(dest_dir, os.path.basename(src))
    dest = os.path.join(dest_dir, new_name)
    if os.path.isdir(src):
        shutil.copytree(src, dest)
    else:
        shutil.copy2(src, dest)
    return True, new_name


def move_items(src_subpaths: list, dest_subpath: str) -> tuple[int, int, bool, list]:
    """批量移动；返回 (成功数, 失败数, 目标目录是否有效, 失败详情列表)。

    目标目录无效时直接返回 valid=False（此时成功数恒为 0），由路由层据此返回 400。
    逐条调用 move_item，单个失败不影响其它条目（自动跳过，重名会自动加序号）。
    """
    if _dest_dir(dest_subpath) is None:
        return 0, len(src_subpaths), False, ["目标目录无效或不存在"]
    ok = fail = 0
    errors = []
    for sp in src_subpaths:
        if not sp:
            continue
        ok_, msg = move_item(sp, dest_subpath)
        if ok_:
            ok += 1
        else:
            fail += 1
            errors.append(f"{sp}: {msg}")
    return ok, fail, True, errors


def copy_items(src_subpaths: list, dest_subpath: str) -> tuple[int, int, bool, list]:
    """批量复制；返回 (成功数, 失败数, 目标目录是否有效, 失败详情列表)。"""
    if _dest_dir(dest_subpath) is None:
        return 0, len(src_subpaths), False, ["目标目录无效或不存在"]
    ok = fail = 0
    errors = []
    for sp in src_subpaths:
        if not sp:
            continue
        ok_, msg = copy_item(sp, dest_subpath)
        if ok_:
            ok += 1
        else:
            fail += 1
            errors.append(f"{sp}: {msg}")
    return ok, fail, True, errors

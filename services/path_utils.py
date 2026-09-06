"""path_utils 模块（services 包）
路径安全校验（纯逻辑层，不依赖 Flask）。

只做一件事：把相对 text 目录的路径解析为绝对路径，并确保不越界，
防止"目录穿越"攻击。所有需要访问磁盘路径的蓝图都从这里取安全路径。
"""

import os

from config import TEXT_DIR


def safe_path(subpath: str) -> str | None:
    """将相对 TEXT_DIR 的路径解析为绝对路径；越界或非法时返回 None。

    【为什么要做路径安全校验？】
    用户可在 URL 里输入任意路径，若直接拼接可能造成"目录穿越"：
    例如 subpath="../../etc/passwd" 会访问到 text 目录之外的文件。
    这里先取真实路径（realpath 会解析 ..），再检查是否仍在 text 目录内，
    不在就返回 None，由调用方返回 404，杜绝越权访问。
    """
    base = os.path.realpath(TEXT_DIR)                           # text 目录真实绝对路径
    target = os.path.realpath(os.path.join(TEXT_DIR, subpath))  # 拼接后的真实绝对路径
    # commonpath 求两者的公共前缀路径；若等于 base 说明 target 在 text 目录之内
    if os.path.commonpath([base, target]) != base:
        return None  # 越界（或不在同一盘符），拒绝访问
    return target

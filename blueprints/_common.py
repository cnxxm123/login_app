"""blueprints 包内部共享工具模块
供 logs / todos 蓝图复用，避免 _valid_date、_valid_category、_group_label 等函数
在两处重复定义。
"""

import datetime

from config import WORK_CATEGORIES  # 类别白名单，供 _valid_category 校验

_WEEKDAYS = "一二三四五六日"  # 周几的中文显示，供 _group_label 使用


def valid_date(s: str) -> bool:
    """校验日期字符串是否为合法 YYYY-MM-DD。"""
    try:
        datetime.date.fromisoformat(s)
        return True
    except (ValueError, TypeError):
        return False


def valid_category(s: str) -> bool:
    """校验类别是否在 WORK_CATEGORIES 白名单内（防提交任意类别）。"""
    return s in WORK_CATEGORIES


def group_label(d: datetime.date) -> str:
    """返回日期分组的显示标签：今天 / 昨天 / 「2026年9月4日 周五」。"""
    today = datetime.date.today()
    if d == today:
        return "今天"
    if d == today - datetime.timedelta(days=1):
        return "昨天"
    return f"{d.year}年{d.month}月{d.day}日 周{_WEEKDAYS[d.weekday()]}"


def safe_int_id(value, default=0) -> int:
    """安全地将表单 id 参数转为 int，失败时抛出 ValueError 或返回 default。

    用于统一 logs / todos / memos 三处 POST 接口中获取 id 的方式，
    避免各处用不同的默认值（"" vs 0）导致的细微不一致。
    """
    try:
        return int(value or default)
    except (ValueError, TypeError):
        raise ValueError(f"无效的 id: {value!r}") from None
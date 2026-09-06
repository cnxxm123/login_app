"""stats_utils 模块（services 包）
磁盘占用统计（纯逻辑层，只做计算，不依赖 Flask）。

职责：扫描 TEXT_DIR，按两种维度统计磁盘占用：
- 按文件类型（文本/图片/PDF/视频/音频/Office/其它）→ 饼图/条形图用
- 按目录（TEXT_DIR 的直接子目录 + 根目录文件）→ 目录占用可视化用

【性能考虑】
- 只调用一次 os.scandir/os.walk 遍历整棵目录树，边遍历边累加，
  不重复扫描；单次统计开销与文件总数成正比。
- 大小用字节累加，返回后再由前端/模板格式化（保留原始字节数最准确）。
"""

import os

from config import (
    AUDIO_EXTENSIONS,
    IMAGE_EXTENSIONS,
    OFFICE_EXTENSIONS,
    PDF_EXTENSIONS,
    TEXT_EXTENSIONS,
    TEXT_DIR,
    VIDEO_EXTENSIONS,
)

# 文件类型分类表：扩展名 → 分类名
# "其它"兜底所有未列出的扩展名
_TYPE_RULES = (
    (TEXT_EXTENSIONS, "文本"),
    (IMAGE_EXTENSIONS, "图片"),
    (PDF_EXTENSIONS, "PDF"),
    (VIDEO_EXTENSIONS, "视频"),
    (AUDIO_EXTENSIONS, "音频"),
    (OFFICE_EXTENSIONS, "Office"),
)


def _categorize(ext: str) -> str:
    """按扩展名归类文件类型；未命中任何已知类别返回"其它"。"""
    for exts, name in _TYPE_RULES:
        if ext in exts:
            return name
    return "其它"


def disk_stats() -> dict:
    """扫描 TEXT_DIR，返回统计结果字典。

    返回结构：
    {
        "total_size": 总字节数,
        "total_files": 总文件数,
        "by_type": [{"name", "size", "count"}, ...] 按大小降序,
        "by_dir":  [{"name", "size", "count"}, ...] 按大小降序（含根目录文件"根目录"）,
    }
    """
    # 类型累加器：{分类名: {"size": int, "count": int}}
    type_acc: dict = {}
    # 目录累加器：{一级子目录名 或 "根目录": {"size": int, "count": int}}
    dir_acc: dict = {}
    total_size = 0
    total_files = 0

    # 根目录下的直接条目按名字归类：子目录归到其名下，文件归到"根目录"
    with os.scandir(TEXT_DIR) as it:
        for entry in it:
            if entry.is_dir(follow_symlinks=False):
                dir_acc.setdefault(entry.name, {"size": 0, "count": 0})
            else:
                dir_acc.setdefault("根目录", {"size": 0, "count": 0})

    # 单次遍历整棵目录树：os.walk 自顶向下，逐文件累计
    for root, _dirs, files in os.walk(TEXT_DIR):
        # 当前目录相对 TEXT_DIR 的路径；根目录用 "" 表示
        rel_root = os.path.relpath(root, TEXT_DIR)
        bucket = rel_root.split(os.sep)[0] if rel_root != "." else "根目录"
        for name in files:
            full = os.path.join(root, name)
            try:
                size = os.path.getsize(full)
            except OSError:
                continue  # 文件被并发删除/无权限时跳过，不影响整体统计
            ext = os.path.splitext(name)[1].lower()
            cat = _categorize(ext)

            total_size += size
            total_files += 1

            t = type_acc.setdefault(cat, {"size": 0, "count": 0})
            t["size"] += size
            t["count"] += 1

            d = dir_acc.setdefault(bucket, {"size": 0, "count": 0})
            d["size"] += size
            d["count"] += 1

    # 汇总为列表并按大小降序，便于前端从大到小展示
    by_type = [
        {"name": name, **acc}
        for name, acc in type_acc.items()
    ]
    by_dir = [
        {"name": name, **acc}
        for name, acc in dir_acc.items()
    ]
    by_type.sort(key=lambda x: x["size"], reverse=True)
    by_dir.sort(key=lambda x: x["size"], reverse=True)

    return {
        "total_size": total_size,
        "total_files": total_files,
        "by_type": by_type,
        "by_dir": by_dir,
    }

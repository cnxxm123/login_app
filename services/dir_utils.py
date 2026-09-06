"""dir_utils 模块（services 包）
目录操作（纯逻辑层，不依赖 Flask）。

只做一件事：围绕"目录"提供列举、自然排序、递归搜索、目录图片列表，
供 browser 蓝图（目录浏览/搜索）和 view 蓝图（图片长条预览）使用。
"""

import os
import re

from config import CODE_LANGUAGES, IMAGE_EXTENSIONS, TEXT_DIR, TEXT_EXTENSIONS

# services 包内互相引用；这些模块之间不存在循环依赖，因此直接顶层导入即可
from services.path_utils import safe_path  # 路径安全校验
from services.text_utils import read_text_file  # 多编码读取（utf-8/gbk）


def natural_key(name: str):
    """自然排序键：数字部分按数值比较，其余按文本比较。

    【为什么需要它？】
    字符串默认排序按字符逐个比较："10" < "2"（因为先比较 '1' 和 '2'），
    结果变成 1, 10, 11, 2 —— 很不自然。
    我们想要 1, 2, 10, 11 的"自然顺序"。
    实现：把字符串按数字切分（如 "1章10节" → ['1','章','10','节']），
    数字段转成 int 参与比较、文本段转小写比较。

    返回的列表用于 sort 的 key：Python 会逐个元素比较两个列表，
    直到分出大小，等效于按"第一个数、第一个词、第二个数…"的规则排序。
    用 (0, int) 或 (1, str) 的二元组，是让数字段和文本段类型不同也不报错。
    """
    return [
        (0, int(part)) if part.isdigit() else (1, part.lower())
        for part in re.split(r"(\d+)", name)
    ]


def list_entries(subpath: str) -> tuple[list[str], list[str]] | None:
    """列出目录下所有子目录与文档名（均按自然排序）；路径非法或不是目录时返回 None。"""
    target = safe_path(subpath)  # 路径校验：确保不越界
    # isdir 判断是否真的是目录，防止把文件路径当目录遍历
    if target is None or not os.path.isdir(target):
        return None

    dirs, files = [], []
    # os.scandir 比 os.listdir 更高效：边遍历边判断类型，不用先读全量列表
    with os.scandir(target) as it:
        for entry in it:
            if entry.is_dir():
                # 过滤缓存目录，避免页面出现无关项
                if entry.name == "__pycache__":
                    continue
                dirs.append(entry.name)
            elif entry.is_file():
                # 过滤编译缓存文件
                if entry.name.endswith(".pyc"):
                    continue
                files.append(entry.name)
    # 用自定义的自然排序键排序，实现 1,2,10 而非 1,10,2
    dirs.sort(key=natural_key)
    files.sort(key=natural_key)
    return dirs, files


def search_files(base_subpath: str, keyword: str) -> list[dict]:
    """在 base_subpath 目录下递归搜索文件名/目录名包含 keyword 的条目。

    返回 [{"path": 相对 text 目录的路径, "name": 名称, "is_dir": 是否目录}, ...]，
    按路径字典序排列。路径合法但 base 不是目录时返回空列表。
    """
    base = safe_path(base_subpath)
    if base is None or not os.path.isdir(base):
        return []
    ql = keyword.lower()  # 不区分大小写匹配
    results = []
    for root, dirs, files in os.walk(base):
        dirs[:] = [d for d in dirs if d != "__pycache__"]  # 剪枝，不搜缓存目录
        for name in dirs:
            if ql in name.lower():
                rel = os.path.relpath(os.path.join(root, name), TEXT_DIR).replace("\\", "/")
                results.append({"path": rel, "name": name, "is_dir": True})
        for name in files:
            if name.endswith(".pyc"):
                continue
            if ql in name.lower():
                rel = os.path.relpath(os.path.join(root, name), TEXT_DIR).replace("\\", "/")
                results.append({"path": rel, "name": name, "is_dir": False})
    results.sort(key=lambda r: r["path"].lower())
    return results


def search_content(base_subpath: str, keyword: str) -> list[dict]:
    """在 base_subpath 目录下递归搜索【文件内容】包含 keyword 的文本/代码文件。

    与 search_files（按文件名）互补：这里读文件内容做子串匹配。

    返回 [{"path", "name", "snippet"}, ...]，按路径字典序排列。
    - snippet：命中位置附近的一段原文，用于在结果列表里展示上下文
    - 只搜文本/代码类文件（图片、视频、PDF 等二进制跳过），并自动跳过缓存目录

    【为什么只搜文本/代码文件？】
    二进制文件无法按字符串匹配；且文本目录下多数是可读文档，
    读 utf-8/gbk 解码后做大小写不敏感的子串查找即可。
    """
    base = safe_path(base_subpath)
    if base is None or not os.path.isdir(base):
        return []
    ql = keyword.lower()  # 关键字转小写，实现"不区分大小写"匹配
    results = []
    for root, dirs, files in os.walk(base):
        dirs[:] = [d for d in dirs if d != "__pycache__"]  # 剪枝，不搜缓存目录
        for name in files:
            if name.endswith(".pyc"):
                continue
            ext = os.path.splitext(name)[1].lower()
            # 只搜可读文本/代码类文件，其它类型（图片/视频/PDF）跳过
            if ext not in TEXT_EXTENSIONS and ext not in CODE_LANGUAGES:
                continue
            content, _ = read_text_file(os.path.join(root, name))
            if content is None:  # 解码失败（如二进制伪装成文本）→ 跳过
                continue
            idx = content.lower().find(ql)  # 内容里找关键字（不区分大小写）
            if idx == -1:
                continue
            # 截取命中位置前后一小段作为摘要，换行折叠成一行便于在列表里展示
            start = max(0, idx - 30)
            end = min(len(content), idx + len(keyword) + 50)
            snippet = content[start:end].replace("\r", " ").replace("\n", " ").strip()
            rel = os.path.relpath(os.path.join(root, name), TEXT_DIR).replace("\\", "/")
            results.append({"path": rel, "name": name, "snippet": snippet})
    results.sort(key=lambda r: r["path"].lower())
    return results


def dir_all_images(subpath: str) -> list | None:
    """若某目录"无子目录、且直接文件全是图片"，返回全部图片；否则返回 None。

    这是"图集/漫画文件夹"的判定函数，同时被两处复用：
    - browser 蓝图算文件夹封面（第一张图 + 数量，决定卡片是否进入"封面区"）；
    - view 蓝图的 /gallery 图集阅读页（列出全部图片供全屏翻页阅读）。

    返回 [{"name", "path"}, ...]（与 dir_images 同构），path 是相对 text 目录
    的相对路径；不符合条件时返回 None（调用方据此走普通文件夹逻辑）。
    """
    entries = list_entries(subpath)
    if entries is None:  # 路径非法或不是目录
        return None
    sub_dirs, sub_files = entries
    if sub_dirs:  # 里面还有子目录 → 不算"图集"
        return None
    if not sub_files:  # 空文件夹 → 没有图片
        return None
    images = [
        {
            "name": f,
            "path": os.path.join(subpath, f).replace("\\", "/"),
        }
        for f in sub_files
        if os.path.splitext(f)[1].lower() in IMAGE_EXTENSIONS
    ]
    if len(images) != len(sub_files):  # 混有非图片文件 → 不算"全是图片"
        return None
    return images


# 文件夹封面专用文件名（不含扩展名）。任何文件夹内放一张名为"封面"的图片，
# 即可作为该文件夹的封面；进入文件夹/图集阅读时这张图会被隐藏。
COVER_IMAGE_STEM = "封面"


def is_cover_image(filename: str) -> bool:
    """判断文件名是否为"封面"图片：主干（不含扩展名）叫"封面"且为图片格式。

    【用在哪里】目录浏览的文件夹列表、图集/图片预览都要把"封面"图排除掉，
    否则它既是封面又会出现在文件夹内容里（用户要求"点击文件夹里面时不显示"）。
    """
    stem, ext = os.path.splitext(filename)
    return stem == COVER_IMAGE_STEM and ext.lower() in IMAGE_EXTENSIONS


def find_cover_image(subpath: str) -> str | None:
    """返回目录下名为"封面"的图片的相对路径（自然排序第一个）；没有则返回 None。

    供 browser 蓝图算文件夹封面用：有"封面"图则优先拿它当封面，
    而不是图集默认的第一张图。
    """
    entries = list_entries(subpath)
    if entries is None:  # 路径非法或不是目录
        return None
    _, files = entries
    for f in files:
        if is_cover_image(f):
            return os.path.join(subpath, f).replace("\\", "/")
    return None


def dir_images(subpath: str) -> list:
    """返回"当前图片所在目录"里的全部图片（自然排序），供长条漫画式预览。

    返回 [{"name", "path"}, ...]，其中 path 是相对 text 目录的相对路径，
    调用方（模板）据此为每张图生成 /media/... 地址。
    """
    parent_dir = os.path.dirname(subpath)            # 当前图片所在目录
    entries = list_entries(parent_dir)               # 复用上面的列目录逻辑
    if entries is None:
        return []
    _, files = entries
    return [
        {
            "name": f,
            "path": os.path.join(parent_dir, f).replace("\\", "/"),
        }
        for f in files
        if os.path.splitext(f)[1].lower() in IMAGE_EXTENSIONS
    ]


def dir_media(subpath: str, extensions: set) -> list:
    """返回"当前音视频所在目录"里的全部同类媒体文件（自然排序），供连播使用。

    extensions 传 AUDIO_EXTENSIONS 或 VIDEO_EXTENSIONS，只收集同一类型的媒体，
    这样"音频连播"与"视频连播"互不混入。

    返回 [{"name", "path"}, ...]（与 dir_images 同构），path 是相对 text 目录
    的相对路径，调用方据此为每项生成带签名令牌的 /media/... 地址。
    """
    parent_dir = os.path.dirname(subpath)            # 当前媒体所在目录
    entries = list_entries(parent_dir)               # 复用列目录逻辑
    if entries is None:
        return []
    _, files = entries
    return [
        {
            "name": f,
            "path": os.path.join(parent_dir, f).replace("\\", "/"),
        }
        for f in files
        if os.path.splitext(f)[1].lower() in extensions
    ]

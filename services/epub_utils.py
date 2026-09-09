"""epub_utils 模块（services 包）
EPUB 电子书解析服务（纯逻辑层，不依赖 Flask）。

使用 Python 标准库（zipfile + xml.etree.ElementTree）解析 EPUB 文件：
- EPUB 本质是一个 ZIP 压缩包，内含 XHTML 章节、OPF 元数据、NCX/NAV 目录等
- 支持 EPUB 2（NCX 目录）和 EPUB 3（NAV 目录）两种格式
- 解析结果缓存于内存，避免重复解压
"""

import os
import zipfile
from xml.etree import ElementTree as ET

# ── 命名空间映射 ──────────────────────────────────────────────
# EPUB 内 XML 文件使用各种命名空间，ElementTree 解析时会自动展开为
# {namespace}tag 格式，这里统一管理所有可能出现的命名空间
NS = {
    "container": "urn:oasis:names:tc:opendocument:xmlns:container",
    "opf": "http://www.idpf.org/2007/opf",
    "dc": "http://purl.org/dc/elements/1.1/",
    "ncx": "http://www.daisy.org/z3986/2005/ncx/",
    "xhtml": "http://www.w3.org/1999/xhtml",
    "epub": "http://www.idpf.org/2007/ops",
}

# ── 解析结果缓存 ──────────────────────────────────────────────
# 键为文件绝对路径，值为 parse_epub() 返回的 dict
# 避免重复解析同一个 EPUB 文件（阅读器翻页时会频繁调用）
_cache: dict[str, dict] = {}


def _resolve_ns(tag: str) -> str:
    """将命名空间前缀转换为完整 Clark 表示法。

    例如 "opf:item" → "{http://www.idpf.org/2007/opf}item"
    """
    if ":" in tag:
        prefix, local = tag.split(":", 1)
        ns = NS.get(prefix)
        if ns:
            return f"{{{ns}}}{local}"
    return tag


def _find_elem(parent, tag: str):
    """在父元素下查找子元素，自动处理命名空间。"""
    return parent.find(_resolve_ns(tag))


def _findall_elem(parent, tag: str):
    """在父元素下查找所有匹配子元素。"""
    return parent.findall(_resolve_ns(tag))


def _text(el) -> str:
    """安全获取元素的文本内容。"""
    return (el.text or "").strip() if el is not None else ""


def _attr(el, name: str) -> str:
    """安全获取元素属性值。"""
    return (el.get(name) or "").strip() if el is not None else ""


def parse_epub(filepath: str) -> dict | None:
    """解析 EPUB 文件，返回结构化数据。

    返回格式：
    {
        "title": str,           # 书名
        "author": str,          # 作者
        "cover_href": str,      # 封面图片在 EPUB 内的相对路径
        "chapters": [           # 目录章节列表（来自 NCX/NAV）
            {"id": str, "title": str, "href": str, "play_order": int}
        ],
        "spine": [              # 阅读顺序
            {"idref": str, "href": str}
        ],
        "resources": {id: href} # 所有资源映射
    }
    解析失败返回 None。
    """
    if not os.path.isfile(filepath):
        return None

    # 检查缓存：如果文件修改时间未变，直接返回缓存
    cache_key = os.path.abspath(filepath)
    mtime = os.path.getmtime(filepath)
    cached = _cache.get(cache_key)
    if cached and cached.get("_mtime") == mtime:
        return cached

    try:
        with zipfile.ZipFile(filepath, "r") as zf:
            # ── 1. 定位 OPF 文件 ──────────────────────────────
            opf_path = _find_opf_path(zf)
            if not opf_path:
                return None

            # ── 2. 解析 OPF 文件 ──────────────────────────────
            opf_data = _parse_opf(zf, opf_path)
            if not opf_data:
                return None

            # ── 3. 解析目录（NCX 或 NAV） ──────────────────────
            chapters = _parse_toc(zf, opf_data)

            result = {
                "title": opf_data["title"],
                "author": opf_data["author"],
                "cover_href": opf_data["cover_href"],
                "chapters": chapters,
                "spine": opf_data["spine"],
                "resources": opf_data["resources"],
                "_mtime": mtime,
            }
            _cache[cache_key] = result
            return result
    except (zipfile.BadZipFile, OSError, ET.ParseError, KeyError):
        return None


def _find_opf_path(zf: zipfile.ZipFile) -> str | None:
    """从 container.xml 中定位 OPF 文件的路径。"""
    try:
        container_xml = zf.read("META-INF/container.xml")
    except KeyError:
        # 某些 EPUB 文件可能在大小写不敏感的文件系统上
        try:
            container_xml = zf.read("META-INF/container.xml".lower())
        except KeyError:
            return None

    root = ET.fromstring(container_xml)
    # 查找 <rootfile> 元素，其 full-path 属性指向 OPF 文件
    rootfile = _find_elem(root, "container:rootfiles/container:rootfile")
    if rootfile is None:
        # 尝试不带命名空间
        for rf in root.iter("rootfile"):
            path = _attr(rf, "full-path")
            if path:
                return path
        return None
    return _attr(rootfile, "full-path")


def _parse_opf(zf: zipfile.ZipFile, opf_path: str) -> dict | None:
    """解析 OPF 文件，提取元数据、清单（manifest）和书脊（spine）。"""
    try:
        opf_xml = zf.read(opf_path)
    except KeyError:
        return None

    # OPF 文件所在目录，用于解析相对路径
    opf_dir = os.path.dirname(opf_path)

    root = ET.fromstring(opf_xml)

    # ── 元数据 ──────────────────────────────────────────────
    title = "未知书名"
    author = "未知作者"
    cover_id = ""

    metadata = _find_elem(root, "opf:metadata")
    if metadata is not None:
        # 书名
        title_el = _find_elem(metadata, "dc:title")
        title = _text(title_el) or title

        # 作者
        creator_el = _find_elem(metadata, "dc:creator")
        author = _text(creator_el) or author

        # 封面图片 ID（meta name="cover"）
        for meta in metadata.findall(_resolve_ns("opf:meta")):
            if meta.get("name") == "cover":
                cover_id = meta.get("content", "")
                break
        # EPUB 3 封面可能用 properties="cover-image"
        if not cover_id:
            mani = _find_elem(root, "opf:manifest")
            if mani is not None:
                for item in mani.findall(_resolve_ns("opf:item")):
                    if item.get("properties") == "cover-image":
                        cover_id = item.get("id", "")
                        break

    # ── 清单（manifest）：所有资源文件 ──────────────────────
    resources: dict[str, str] = {}
    cover_href = ""

    manifest = _find_elem(root, "opf:manifest")
    if manifest is not None:
        for item in manifest.findall(_resolve_ns("opf:item")):
            item_id = _attr(item, "id")
            item_href = _attr(item, "href")
            if item_id and item_href:
                # 将相对路径解析为相对于 OPF 目录的路径
                full_href = os.path.normpath(
                    os.path.join(opf_dir, item_href)
                ).replace("\\", "/")
                resources[item_id] = full_href
                if item_id == cover_id:
                    cover_href = full_href

    # ── 书脊（spine）：阅读顺序 ──────────────────────────────
    spine = []
    spine_elem = _find_elem(root, "opf:spine")
    if spine_elem is not None:
        for itemref in spine_elem.findall(_resolve_ns("opf:itemref")):
            idref = _attr(itemref, "idref")
            href = resources.get(idref, "")
            if idref:
                spine.append({"idref": idref, "href": href})

    # 如果 spine 为空，尝试用 manifest 中所有 HTML 文件作为备用
    if not spine:
        for rid, href in resources.items():
            if href.lower().endswith((".xhtml", ".html", ".htm")):
                spine.append({"idref": rid, "href": href})

    return {
        "title": title,
        "author": author,
        "cover_href": cover_href,
        "spine": spine,
        "resources": resources,
        "opf_dir": opf_dir,
    }


def _parse_toc(zf: zipfile.ZipFile, opf_data: dict) -> list[dict]:
    """解析目录：优先 NCX（EPUB 2），其次 NAV（EPUB 3）。"""
    chapters: list[dict] = []

    # ── 尝试 NCX 目录 ──────────────────────────────────────
    # NCX 文件的 ID 通常在 spine 的 toc 属性中指定
    ncx_href = ""
    for rid, href in opf_data["resources"].items():
        if href.lower().endswith(".ncx"):
            ncx_href = href
            break

    if ncx_href:
        try:
            ncx_xml = zf.read(ncx_href)
            ncx_root = ET.fromstring(ncx_xml)
            chapters = _parse_ncx(ncx_root, ncx_href)
            if chapters:
                return chapters
        except (KeyError, ET.ParseError):
            pass

    # ── 尝试 NAV 目录（EPUB 3） ─────────────────────────────
    for rid, href in opf_data["resources"].items():
        if "nav" in rid.lower() and href.lower().endswith((".xhtml", ".html", ".htm")):
            try:
                nav_xml = zf.read(href)
                nav_root = ET.fromstring(nav_xml)
                chapters = _parse_nav(nav_root, href)
                if chapters:
                    return chapters
            except (KeyError, ET.ParseError):
                pass

    # ── 兜底：用 spine 生成章节列表 ─────────────────────────
    # 把 spine 里的每一项都当作一个章节，标题取文件名
    for i, item in enumerate(opf_data["spine"], 1):
        href = item["href"]
        name = os.path.basename(href)
        # 去掉扩展名作为标题
        title = os.path.splitext(name)[0]
        chapters.append({
            "id": item["idref"],
            "title": title,
            "href": item["href"],
            "play_order": i,
        })

    return chapters


def _parse_ncx(ncx_root: ET.Element, ncx_href: str) -> list[dict]:
    """解析 NCX 目录文件（EPUB 2）。"""
    chapters: list[dict] = []
    ncx_dir = os.path.dirname(ncx_href)

    # 查找 <navMap> 下的 <navPoint> 列表
    navmap = _find_elem(ncx_root, "ncx:navMap")
    if navmap is None:
        return chapters

    for navpoint in navmap.findall(_resolve_ns("ncx:navPoint")):
        play_order = _attr(navpoint, "playOrder")
        try:
            order = int(play_order)
        except (ValueError, TypeError):
            order = 0

        # 标题
        label = _find_elem(navpoint, "ncx:navLabel/ncx:text")
        title = _text(label) or "无标题"

        # 链接
        content = _find_elem(navpoint, "ncx:content")
        src = _attr(content, "src") if content is not None else ""

        # 解析 href（可能带 #fragment）
        href = src.split("#")[0] if src else ""
        if href:
            full_href = os.path.normpath(
                os.path.join(ncx_dir, href)
            ).replace("\\", "/")

            chapters.append({
                "id": _attr(navpoint, "id"),
                "title": title,
                "href": full_href,
                "play_order": order,
            })

    return chapters


def _parse_nav(nav_root: ET.Element, nav_href: str) -> list[dict]:
    """解析 NAV 目录文件（EPUB 3）。"""
    chapters: list[dict] = []
    nav_dir = os.path.dirname(nav_href)

    # 查找 <nav epub:type="toc"> 中的 <ol> 列表
    for nav in nav_root.iter(_resolve_ns("xhtml:nav")):
        if nav.get(_resolve_ns("epub:type")) == "toc":
            _parse_nav_ol(nav, nav_dir, chapters, 0)
            break
    # 如果没找到带 epub:type 的 nav，尝试所有 nav 元素
    if not chapters:
        for nav in nav_root.iter("nav"):
            _parse_nav_ol(nav, nav_dir, chapters, 0)
            if chapters:
                break

    return chapters


def _parse_nav_ol(parent, nav_dir: str, chapters: list[dict], level: int):
    """递归解析 NAV 中的 <ol> 列表。"""
    for ol in parent.findall(_resolve_ns("xhtml:ol")):
        for li in ol.findall(_resolve_ns("xhtml:li")):
            if li is None:
                continue
            a_tag = li.find(_resolve_ns("xhtml:a"))
            if a_tag is not None:
                title = _text(a_tag) or "无标题"
                src = _attr(a_tag, "href")
                href = src.split("#")[0] if src else ""
                if href:
                    full_href = os.path.normpath(
                        os.path.join(nav_dir, href)
                    ).replace("\\", "/")
                    chapters.append({
                        "id": _attr(a_tag, "id") or f"nav_{len(chapters)}",
                        "title": title,
                        "href": full_href,
                        "play_order": len(chapters) + 1,
                    })
            # 递归处理嵌套的 <ol>（子章节）
            _parse_nav_ol(li, nav_dir, chapters, level + 1)


def get_epub_chapter_content(filepath: str, chapter_href: str) -> str | None:
    """从 EPUB 中读取指定章节的 HTML 内容。

    chapter_href 是 EPUB 内部相对路径（如 OEBPS/chapter1.xhtml）。
    返回章节的 HTML 字符串，读取失败返回 None。
    """
    if not os.path.isfile(filepath):
        return None

    try:
        with zipfile.ZipFile(filepath, "r") as zf:
            # 尝试直接读取
            try:
                return zf.read(chapter_href).decode("utf-8")
            except KeyError:
                pass
            # 尝试在 namelist 中模糊匹配（处理大小写或路径差异）
            for name in zf.namelist():
                if name.lower().endswith(chapter_href.lower().split("/")[-1]):
                    return zf.read(name).decode("utf-8")
            return None
    except (zipfile.BadZipFile, OSError, UnicodeDecodeError):
        return None


def get_epub_resource(filepath: str, resource_path: str) -> tuple[bytes | None, str | None]:
    """从 EPUB 中读取内嵌资源（图片、CSS 等）。

    返回 (bytes, mime_type) 元组，读取失败返回 (None, None)。
    """
    if not os.path.isfile(filepath):
        return None, None

    # MIME 类型映射
    ext = os.path.splitext(resource_path)[1].lower()
    mime_map = {
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".png": "image/png", ".gif": "image/gif",
        ".bmp": "image/bmp", ".webp": "image/webp",
        ".svg": "image/svg+xml", ".ico": "image/x-icon",
        ".css": "text/css", ".ttf": "font/ttf",
        ".otf": "font/otf", ".woff": "font/woff",
        ".woff2": "font/woff2",
    }
    mime_type = mime_map.get(ext, "application/octet-stream")

    try:
        with zipfile.ZipFile(filepath, "r") as zf:
            # 直接读取
            try:
                return zf.read(resource_path), mime_type
            except KeyError:
                pass
            # 模糊匹配
            target_name = resource_path.lower().split("/")[-1]
            for name in zf.namelist():
                if name.lower().endswith(target_name):
                    return zf.read(name), mime_type
            return None, None
    except (zipfile.BadZipFile, OSError):
        return None, None


def clear_cache(filepath: str | None = None):
    """清除缓存。不传参数则清除全部缓存。"""
    if filepath:
        _cache.pop(os.path.abspath(filepath), None)
    else:
        _cache.clear()
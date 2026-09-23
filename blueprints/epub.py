"""epub 模块（blueprints 包）
EPUB 电子书阅读蓝图：/epub/<path> 阅读器页面。

提供 EPUB 文件的浏览器内阅读功能：
- /epub/<path>              渲染阅读器页面
- /epub/api/info/<path>     返回书籍元数据和章节目录 JSON
- /epub/api/chapter/<path>/<chapter_id> 返回指定章节的 HTML 内容
- /epub/api/resource/<path>/<resource_path> 返回内嵌资源（图片/CSS 等）
"""

import os

from flask import Blueprint, Response, abort, jsonify, render_template, request

from services.epub_utils import (
    get_epub_chapter_content,
    get_epub_resource,
    parse_epub,
)
from services.path_utils import safe_path
from blueprints.personal import get_resource_state, record_resource_history

# 创建"EPUB"蓝图；模板里 url_for('epub.xxx') 的 epub 即此名字
epub_bp = Blueprint("epub", __name__)


@epub_bp.route("/epub/<path:subpath>")
def epub_reader(subpath: str):
    """EPUB 阅读器页面：渲染带目录导航的浏览器内电子书阅读器。"""
    target = safe_path(subpath)
    if target is None or not os.path.isfile(target):
        abort(404)

    # 校验是否为 EPUB 文件
    ext = os.path.splitext(target)[1].lower()
    if ext != ".epub":
        abort(404)

    # 获取书籍基本信息（用于页面标题）
    book = parse_epub(target)
    title = book["title"] if book else os.path.basename(target)

    parent = os.path.dirname(subpath).replace("\\", "/")
    record_resource_history(subpath)
    personal_state = get_resource_state(subpath)

    return render_template(
        "epub_reader.html",
        filename=os.path.basename(target),
        book_title=title,
        path=subpath,
        parent=parent,
        personal_state=personal_state,
    )


@epub_bp.route("/epub/api/info/<path:subpath>")
def epub_info(subpath: str):
    """返回书籍元数据 JSON：书名、作者、封面、章节目录。"""
    target = safe_path(subpath)
    if target is None or not os.path.isfile(target):
        abort(404)

    book = parse_epub(target)
    if not book:
        return jsonify({"error": "无法解析 EPUB 文件"}), 400

    return jsonify({
        "title": book["title"],
        "author": book["author"],
        "cover_href": book["cover_href"],
        "chapters": book["chapters"],
        "spine": book["spine"],
    })


@epub_bp.route("/epub/api/chapter/<path:subpath>/<chapter_id>")
def epub_chapter(subpath: str, chapter_id: str):
    """返回指定章节的 HTML 内容。"""
    target = safe_path(subpath)
    if target is None or not os.path.isfile(target):
        abort(404)

    # 先获取书籍信息，根据 chapter_id 找到对应的 href
    book = parse_epub(target)
    if not book:
        return jsonify({"error": "无法解析 EPUB 文件"}), 400

    # 查找章节对应的 href
    chapter_href = ""
    for ch in book["chapters"]:
        if ch["id"] == chapter_id:
            chapter_href = ch["href"]
            break

    # 如果目录里没找到，尝试从 spine 中查找
    if not chapter_href:
        for item in book["spine"]:
            if item["idref"] == chapter_id:
                chapter_href = item["href"]
                break

    if not chapter_href:
        return jsonify({"error": "章节未找到"}), 404

    content = get_epub_chapter_content(target, chapter_href)
    if content is None:
        return jsonify({"error": "无法读取章节内容"}), 500

    return jsonify({"content": content, "href": chapter_href})


@epub_bp.route("/epub/api/resource/<path:subpath>/<path:resource_path>")
def epub_resource(subpath: str, resource_path: str):
    """返回 EPUB 内嵌资源（图片、CSS 字体等）。"""
    target = safe_path(subpath)
    if target is None or not os.path.isfile(target):
        abort(404)

    data, mime_type = get_epub_resource(target, resource_path)
    if data is None:
        abort(404)

    return Response(data, mimetype=mime_type or "application/octet-stream")
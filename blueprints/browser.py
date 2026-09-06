"""browser 模块（blueprints 包）
文件浏览蓝图：主页（根目录）、目录浏览、搜索。

【本模块做什么】
处理"浏览 text 目录"的三大页面：
- /              主页：显示根目录
- /browse/<path> 目录页：子目录→按钮，文档→列表，可递归
- /search       按文件名/内容递归搜索（关键字 q，可限定起始目录 path）
"""

import os

from flask import Blueprint, abort, jsonify, redirect, render_template, request, url_for

from config import (
    AUDIO_EXTENSIONS,
    CODE_LANGUAGES,
    IMAGE_EXTENSIONS,
    MAX_FORM_PARTS,
    MAX_UPLOAD_BYTES,
    PDF_EXTENSIONS,
    TEXT_EXTENSIONS,
    VIDEO_EXTENSIONS,
)  # 扩展名配置表（决定文档用哪种预览方式）+ 上传上限（供页面提醒）
from services.dir_utils import dir_all_images, find_cover_image, is_cover_image, list_entries, search_content, search_files  # 纯逻辑：列目录 / 递归搜索 / 图集判定 / 封面图
from services.media_utils import get_video_duration  # 视频时长探测
from services.path_utils import safe_path  # 相对路径 → 安全绝对路径（越界防护）
from services import tag_store  # 文件标签读写（浏览页卡片显示标签用）

# 创建"浏览"蓝图；模板里 url_for('browser.xxx') 的 browser 即此名字
browser_bp = Blueprint("browser", __name__)


def browse_context(subpath: str) -> dict | None:
    """构建目录浏览页上下文：列出子目录与文档；路径非法或不是目录时返回 None。

    返回的 dict 会被 render_template(**ctx) 展开为模板变量：
    - path        当前相对路径（'' 表示根目录）
    - parent      上一级相对路径（'' 表示已在根目录）
    - breadcrumbs 面包屑导航：[(目录名, 相对路径), ...]
    - dirs_cover  有封面的子目录列表：[{name, url, cover}, ...]（优先展示）
    - dirs_plain  无封面的子目录列表：[{name, url}, ...]（独立分区展示）
    - files       文档列表：  [{name, url}, ...]（渲染成列表项）
    """
    entries = list_entries(subpath)  # 纯逻辑：列目录（含 __pycache__ 过滤）
    if entries is None:
        return None  # 路径非法或不是目录 → 由调用方返回 404
    dirs, files = entries

    def rel(name: str) -> str:
        # 把"当前子路径 + 名字"拼成完整相对路径。
        # Windows 用 \ 拼接，URL 需要用 /，所以 replace 统一分隔符。
        return os.path.join(subpath, name).replace("\\", "/")

    # 上一级相对路径；os.path.dirname 取所在目录，根目录时为 ''
    parent = os.path.dirname(subpath).replace("\\", "/")

    # 面包屑：例如 "Python进阶学习/爬虫" 拆成
    # [("Python进阶学习", "Python进阶学习"), ("爬虫", "Python进阶学习/爬虫")]
    # 每一级都能单独点击跳转，方便逐层返回
    crumbs, cur = [], ""
    for part in subpath.split("/"):  # 按 / 切成各级目录名
        if not part:  # 跳过空串（如开头/结尾的多余分隔符）
            continue
        cur = os.path.join(cur, part).replace("\\", "/")  # 累加路径
        crumbs.append((part, cur))  # (显示名, 可跳转的相对路径)

    dir_entries = []
    for d in dirs:
        # 封面：优先取文件夹内名为"封面"的图片；否则仅"图集"（无子目录、全是图片）
        # 文件夹取第一张图。返回 {url, count, gallery}，没有封面则为 None。
        cover = folder_cover_info(rel(d))
        dir_entries.append({
            "name": d,
            "path": rel(d),  # 相对路径（供打包下载使用）
            # 有封面且是"图集"的文件夹（全是图片）点击直接进全屏图集阅读器；
            # 普通文件夹（即使有"封面"图当封面）仍进目录浏览页。
            "url": url_for("view.view_gallery", subpath=rel(d)) if cover and cover["gallery"] else url_for("browser.browse", subpath=rel(d)),
            # 图集阅读页与视频/文档查看页一致，新标签页打开（不打断目录浏览）；
            # 普通文件夹浏览保持当前标签页。
            "new_tab": bool(cover and cover["gallery"]),
            "cover": cover,
        })
    # 隐藏"封面"图片：它只当文件夹封面用，浏览文件夹内容时不显示
    # （如搜索"封面"仍能直接搜到/打开，不受影响）
    visible_files = [f for f in files if not is_cover_image(f)]
    file_entries = build_file_items(visible_files, rel)
    # 一次性批量查出当前目录所有条目（文件夹+文件）的标签，
    # 避免每个条目单独查数据库造成大量小查询（N+1 问题）
    all_paths = [d["path"] for d in dir_entries] + [f["path"] for f in file_entries]
    tags_map = tag_store.tags_for_paths(all_paths)
    for d in dir_entries:
        d["tags"] = tags_map.get(d["path"], [])
    for f in file_entries:
        f["tags"] = tags_map.get(f["path"], [])

    # 按"是否有封面"拆分文件夹：有封面的（图片文件夹）排在前区展示，
    # 无封面的（纯文件夹）独立成区，网格各自换行，不再混排
    dirs_cover = [d for d in dir_entries if d["cover"]]
    dirs_plain = [d for d in dir_entries if not d["cover"]]

    return {
        "path": subpath,
        "parent": parent,
        "breadcrumbs": crumbs,
        # url_for 根据"路由名 + 参数"生成 URL（如 /browse/爬虫基础）。
        # 好处：路由地址变了模板不用改。
        "dirs_cover": dirs_cover,
        "dirs_plain": dirs_plain,
        "files": file_entries,
    }


def image_thumb_url(subpath: str) -> str:
    """图片的缩略图 URL；SVG/ICO 等不需要缩略的格式退回原图 URL。

    缩略图由 Pillow 生成并缓存（400px 内 JPEG），卡片/封面加载它而非原图，
    目录里图片多时显著减少流量与内存占用；查看页仍加载原图保证清晰度。
    """
    fext = os.path.splitext(subpath)[1].lower()
    if fext in (".svg", ".ico"):  # 与 get_image_thumb 的豁免一致：矢量/极小图不缩略
        return url_for("media.media", subpath=subpath)
    return url_for("media.imgthumb", subpath=subpath)


def cover_thumb_url(subpath: str) -> str:
    """文件夹封面的图片 URL：走高清缩略图（900px、质量 88），SVG/ICO 退回原图。

    封面卡片比普通文件卡片大得多，用 400px 缩略图放大后会发虚，
    故封面单独用 /imgcover 高清缩略图，保证所有文件夹封面清晰。
    """
    fext = os.path.splitext(subpath)[1].lower()
    if fext in (".svg", ".ico"):  # 矢量/极小图不缩略，直接原图
        return url_for("media.media", subpath=subpath)
    return url_for("media.imgcover", subpath=subpath)


def folder_cover_info(subpath: str) -> dict | None:
    """文件夹封面信息：返回 {"url": 封面缩略图地址, "count": 图集图片数或 None, "gallery": 是否图集}。

    封面优先级（自定"封面"功能）：
    1. 文件夹内有一张名为"封面"的图片（任意文件夹都适用）→ 用它当封面；
    2. 否则仅当该文件夹是"图集"（无子目录、直接文件全是图片）时，取第一张图当封面。
    两者都没有 → 返回 None（普通文件夹，卡片走"无封面"分区）。

    - gallery=True：纯图片图集，点击卡片直接进全屏图集阅读器；
      gallery=False：普通文件夹（可能含子目录/文档），点击仍进目录浏览。
    - count 为图集内**可见**图片数（"封面"图只作封面、阅读时不显示，故不计入）。
    """
    images = dir_all_images(subpath)  # 图集判定（无子目录 / 全图片），非图集时为 None
    cover_img = find_cover_image(subpath)  # 目录内名为"封面"的图片，没有则 None
    if cover_img:  # 有"封面"图 → 一律用它当封面
        visible = (
            [i for i in images if not is_cover_image(i["name"])] if images else None
        )
        return {
            "url": cover_thumb_url(cover_img),
            "count": len(visible) if visible is not None else None,
            "gallery": images is not None,
        }
    if not images:  # 非图集且无"封面"图 → 无封面
        return None
    first = images[0]["path"]
    return {"url": cover_thumb_url(first), "count": len(images), "gallery": True}


def safe_file_size(subpath: str) -> int:
    """读取文件字节数（供列表视图展示大小）；读不到时返回 0 而不是抛错。

    使用 safe_path 解析绝对路径，路径非法（如刚被删除）时优雅降级。
    """
    try:
        return os.path.getsize(safe_path(subpath))
    except (OSError, TypeError):
        return 0


def build_file_items(files, rel):
    """把目录里的文件转成前端展示项（卡片网格用）。

    - 视频（含 m3u8）：指向 view 查看页，由自定义网页播放器播放（static/js/player.js，
      控制栏/进度条/倍速/连播均在查看页内）；查看页内部生成 /media 流地址。
    - PDF：直接指向 media 蓝图的 /media 二进制流（浏览器原生查看器）。
    - 图片：走 view 查看页（长条漫画式），卡片缩略图用压缩缩略图（/imgthumb），
      仅 SVG/ICO 这类无需缩略的格式退回原图。
    - 其余文本文件走 view 蓝图的 /view 查看页。
    external=True 表示"点击后在新标签页打开"（PDF/视频/图片/文本查看页均适用），
    模板据此加 target="_blank"。
    返回 [{"name", "kind", "external", "thumb", "url"}, ...]。
    """
    items = []
    for f in files:
        fext = os.path.splitext(f)[1].lower()
        if fext in VIDEO_EXTENSIONS:
            # 视频一律进 view 查看页的自定义播放器（不再直接打开 /media 原生播放）。
            # 查看页内部会生成 /media 流地址；同目录自动连播也依赖查看页。
            # m3u8 分片流无法抽帧，故无封面。
            kind = "video"
            thumb = url_for("media.thumb", subpath=rel(f)) if fext != ".m3u8" else None
            url, external = url_for("view.view_file", subpath=rel(f)), True
        elif fext in PDF_EXTENSIONS:
            kind, thumb = "text", None
            url, external = url_for("media.media", subpath=rel(f)), True
        elif fext in AUDIO_EXTENSIONS:
            # 音频：直接指向 /media 二进制流，交给浏览器自带播放器播放。
            kind, thumb = "audio", None
            url, external = url_for("media.media", subpath=rel(f)), True
        elif fext in IMAGE_EXTENSIONS:
            kind, thumb = "image", image_thumb_url(rel(f))
            url, external = url_for("view.view_file", subpath=rel(f)), True
        else:
            kind, thumb = "text", None
            url, external = url_for("view.view_file", subpath=rel(f)), True
        items.append({
            "name": f,
            "path": rel(f),  # 相对路径（供单文件下载按钮使用）
            "kind": kind,    # 供模板选缩略图/图标
            "external": external,
            "thumb": thumb,
            "url": url,
            "size": safe_file_size(rel(f)),  # 文件字节数（列表视图显示大小，读失败为 0）
            # 是否可在网页上编辑：命中文本/代码扩展名才给编辑按钮（二进制文件不可编辑）
            "editable": fext in TEXT_EXTENSIONS or fext in CODE_LANGUAGES,
        })
    return items


def render_browse(subpath: str):
    """渲染目录浏览页；路径非法时返回 404。

    browse 和 main 共用本函数，避免重复代码：
    main 是"根目录浏览"（subpath=''），browse 是"子目录浏览"。
    """
    ctx = browse_context(subpath)
    if ctx is None:
        # abort(404) 让 Flask 返回"页面不存在"，而不是崩溃
        abort(404)
    # **ctx 把字典展开成关键字参数：
    # render_template("main.html", path=..., dirs=..., files=..., ...)
    return render_template(
        "main.html",
        max_form_parts=MAX_FORM_PARTS,   # 上传限制：单次最多文件数（页面点击上传时提醒用）
        max_upload_bytes=MAX_UPLOAD_BYTES,  # 上传限制：单次请求体总大小上限
        **ctx,
    )


@browser_bp.route("/")
def main():
    """主页：浏览 text 目录的根目录。"""
    return render_browse("")  # 空字符串代表根目录


@browser_bp.route("/browse/<path:subpath>")
def browse(subpath: str):
    """浏览某个文件夹：子目录渲染为按钮，文档渲染为列表，支持递归。

    <path:subpath> 是 Flask 的"路径转换器"：
    普通 <xxx> 不匹配斜杠，而 <path:xxx> 能匹配包含 / 的多级路径，
    因此 /browse/爬虫基础/第一节 会作为整体传给 subpath。
    目录可以无限嵌套，因为每层都调用同一个路由继续浏览。
    """
    return render_browse(subpath)


@browser_bp.route("/search")
def search():
    """按文件名或文件内容递归搜索：?q=关键字&path=起始目录&mode=name|content

    mode 决定搜哪一层：
    - name（默认）：只匹配文件名/目录名（search_files）
    - content：读文本/代码文件内容做匹配（search_content），结果带摘要
    """
    q = request.args.get("q", "").strip()
    base = request.args.get("path", "").strip()
    mode = request.args.get("mode", "name").strip()  # name=按文件名 / content=按内容
    if not q:  # 没输入关键字 → 直接返回起始目录页
        if base:
            return redirect(url_for("browser.browse", subpath=base))
        return redirect(url_for("browser.main"))
    # 按所选模式调用对应的搜索函数（纯逻辑层）
    if mode == "content":
        results = search_content(base, q)
    else:
        results = search_files(base, q)
    return render_template(
        "search.html",
        q=q,
        base=base,
        mode=mode if mode in ("name", "content") else "name",
        results=results,
    )


@browser_bp.route("/duration/<path:subpath>")
def duration(subpath: str):
    """返回视频时长（秒）的 JSON：{"duration": 123.45 | null}。

    文件卡片 JS 逐个拉取本接口，把时长渲染成缩略图右下角角标。
    用 ffmpeg 探测并缓存（见 get_video_duration），路径先经 safe_path 校验防越界。
    """
    target = safe_path(subpath)
    if target is None or not os.path.isfile(target):
        return jsonify({"duration": None})
    fext = os.path.splitext(target)[1].lower()
    if fext not in VIDEO_EXTENSIONS:
        return jsonify({"duration": None})
    return jsonify({"duration": get_video_duration(target)})


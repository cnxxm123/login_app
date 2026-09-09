"""view 模块（blueprints 包）
查看蓝图：/view/<path> 查看文档/图片/PDF/视频。

只做一件事：把文件按类型渲染成"查看页面"。
- 文本/代码文件 → 读取内容并渲染成 Markdown HTML
- 图片 → 同目录全部图片长条纵向预览（懒加载）
- PDF → 通过 media 蓝图在新标签页用浏览器原生查看器打开
- 视频 → 页面内嵌浏览器原生 <video> 播放器，直接加载 media 蓝图的二进制流

【与其它模块的分工】
- 路径校验来自 services/path_utils，读文件/渲染来自 services/text_utils，
  目录图片列表来自 services/dir_utils（纯逻辑层）
- PDF/视频的二进制流由 media 蓝图返回，这里只负责拼 URL / 渲染页面
"""

import os

from flask import Blueprint, abort, redirect, render_template, url_for

from config import (
    AUDIO_EXTENSIONS,
    CODE_LANGUAGES,
    EPUB_EXTENSIONS,
    IMAGE_EXTENSIONS,
    OFFICE_EXTENSIONS,
    PDF_EXTENSIONS,
    TEXT_EXTENSIONS,
    VIDEO_EXTENSIONS,
)  # 扩展名配置表
from services.dir_utils import dir_all_images, dir_images, dir_media, is_cover_image  # 图集判定 / 目录图片列表 / 目录音视频列表 / 封面图判定
from services.office_utils import render_office_to_html  # Office 文档解析（docx/xlsx/xls）
from services.path_utils import safe_path                # 路径安全校验
from services.text_utils import read_text_file, render_content_to_html  # 读文本 + Markdown 渲染

# 创建"查看"蓝图；模板里 url_for('view.xxx') 的 view 即此名字
view_bp = Blueprint("view", __name__)


@view_bp.route("/view/<path:subpath>")
def view_file(subpath: str):
    """查看某个文档/图片/PDF/视频的内容。"""
    target = safe_path(subpath)  # 防目录穿越：只允许访问 text 目录内文件
    # isfile 确认目标确实是文件（不是目录/不存在），否则 404
    if target is None or not os.path.isfile(target):
        abort(404)

    ext = os.path.splitext(target)[1].lower()  # 取扩展名（如 .md），并转小写

    # EPUB 文件重定向到专用的 EPUB 阅读器
    if ext in EPUB_EXTENSIONS:
        return redirect(url_for("epub.epub_reader", subpath=subpath))

    content, encoding = None, None             # 文件内容与编码（文本预览用）
    content_html = None                        # 渲染后的 HTML（文本预览用）
    office_html = None                         # Office 文档解析出的 HTML（docx/xlsx/xls 预览用）
    media_type = None   # 媒体预览类型："image" | "pdf" | "video" | "audio" | "office" | None（None=文本预览）
    media_url = None    # 媒体文件的访问地址（经 media 蓝图流式返回）
    images = []         # 图片预览：所在目录的全部图片（长条漫画式纵向排列）
    image_urls = []     # 图片预览地址列表（单页阅读器翻页 / 记忆位置用）
    playlist = []       # 音视频连播列表：[{"name","path","url"}, ...]（整目录同类媒体）
    playlist_index = 0  # 当前文件在连播列表中的下标

    # 可预览文本 = 常规文本扩展名 或 代码扩展名（如 .c/.java 等）
    if ext in TEXT_EXTENSIONS or ext in CODE_LANGUAGES:
        content, encoding = read_text_file(target)  # 尝试 utf-8/gbk 读取
        if content is not None:  # 读取成功才渲染
            content_html = render_content_to_html(content, ext)
    elif ext in IMAGE_EXTENSIONS:
        # 图片：同目录全部图片纵向排成一列，像看长条漫画一样滚动
        media_type = "image"
        images = dir_images(subpath)
        # 排除"封面"图：它只作文件夹封面，不参与长条预览；
        # 但若用户直接打开的就是"封面"图本身（如从搜索结果进入），仍要能看。
        if not is_cover_image(os.path.basename(subpath)):
            images = [img for img in images if not is_cover_image(img["name"])]
        # 生成每张图的访问地址（经 media 蓝图流式返回），供前端单页阅读器翻页
        image_urls = [url_for("media.media", subpath=i["path"]) for i in images]
    elif ext in PDF_EXTENSIONS:
        # PDF：通过 media 蓝图加载，在新标签页用浏览器内置查看器打开
        media_type = "pdf"
        media_url = url_for("media.media", subpath=subpath)
    elif ext in OFFICE_EXTENSIONS:
        # Office 文档：服务端解析成 HTML 后在页面内直接展示（无需下载）
        media_type = "office"
        office_html = render_office_to_html(target, ext)
    elif ext in AUDIO_EXTENSIONS or ext in VIDEO_EXTENSIONS:
        # 音频/视频：通过 media 蓝图加载，页面内嵌浏览器原生播放器。
        # 同时构建"整目录同类媒体"的连播列表（播放结束自动切下一首/集）。
        media_type = "audio" if ext in AUDIO_EXTENSIONS else "video"
        media_url = url_for("media.media", subpath=subpath)
        playlist = [
            {
                "name": item["name"],
                "path": item["path"],
                "url": url_for("media.media", subpath=item["path"]),
                # B 站式右侧"接下来播放"列表缩略图（仅视频有；m3u8 分片流无法抽帧，无封面）
                "thumb": (
                    url_for("media.thumb", subpath=item["path"])
                    if media_type == "video"
                    and os.path.splitext(item["path"])[1].lower() != ".m3u8"
                    else None
                ),
            }
            for item in dir_media(
                subpath, AUDIO_EXTENSIONS if ext in AUDIO_EXTENSIONS else VIDEO_EXTENSIONS
            )
        ]
        # 当前文件在连播列表里的下标（前端据此高亮当前曲目/集）
        for i, item in enumerate(playlist):
            if item["path"] == subpath:
                playlist_index = i
                break

    # 返回"上一级"相对路径，供模板里的返回按钮使用
    parent = os.path.dirname(subpath).replace("\\", "/")
    return render_template(
        "view.html",
        filename=os.path.basename(target),  # 文件名（不含路径）
        path=subpath,
        parent=parent,
        ext=ext or "(无扩展名)",            # 无扩展名时显示提示文字
        is_text=content is not None,        # 模板据此决定显示内容还是"不可预览"
        content_html=content_html,          # 渲染好的 Markdown HTML
        office_html=office_html,            # Office 文档解析出的 HTML
        encoding=encoding,                  # 用于提示该文件的编码
        media_type=media_type,              # 媒体类型（image/pdf/video/audio/office/None）
        media_url=media_url,                # 媒体加载地址
        images=images,                      # 图片预览用的全部图片列表
        image_urls=image_urls,              # 图片地址列表（单页阅读器用）
        playlist=playlist,                  # 音视频连播列表
        playlist_index=playlist_index,      # 当前文件在连播列表中的下标
    )


@view_bp.route("/gallery/<path:subpath>")
def view_gallery(subpath: str):
    """图集阅读页：点击"封面文件夹"（全是图片的目录）时进入的全屏漫画阅读器。

    - 目标必须是 TEXT_DIR 内的**目录**，且"无子目录、直接文件全是图片"
      （判定逻辑收敛在 services.dir_utils.dir_all_images）；
    - 不符合图集条件时回退到普通目录浏览页（如内容后来被改动）；
    - 页面直接加载第一张图并全屏展示，左右箭头翻页、右上角显示页码，
      单页/长条两种阅读模式可切换。
    """
    if dir_all_images(subpath) is None:
        # 不是"纯图片图集" → 退回目录浏览，不报 404，保证始终可浏览
        return redirect(url_for("browser.browse", subpath=subpath))
    images = dir_all_images(subpath) or []
    # 排除"封面"图：它只作文件夹封面，进入图集阅读时不显示
    images = [img for img in images if not is_cover_image(img["name"])]
    if not images:
        # 排除封面后没有可读图片（如文件夹里只有"封面"一张）→ 退回目录浏览
        return redirect(url_for("browser.browse", subpath=subpath))
    # 每张图直接加载原图（media 蓝图流式返回），供前端单页阅读器翻页
    image_urls = [
        url_for("media.media", subpath=img["path"])
        for img in images
    ]
    # 缩略图栏：加载 /imgthumb 压缩缩略图（JPG）而非原图，图多时不卡
    thumb_urls = [
        url_for("media.imgthumb", subpath=img["path"])
        for img in images
    ]
    parent = os.path.dirname(subpath).replace("\\", "/")
    return render_template(
        "gallery.html",
        gallery_name=os.path.basename(subpath),  # 图集名（如漫画书名），用于标题
        path=subpath,
        parent=parent,
        images=images,       # [{name, path}, ...]（长条模式逐张渲染用）
        image_urls=image_urls,  # 全部图片的访问地址（单页模式翻页用）
        thumb_urls=thumb_urls,  # 全部图片的压缩缩略图地址（缩略图导航栏用）
    )

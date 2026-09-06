"""media 模块（blueprints 包）
媒体流蓝图：/media/<path> 以二进制流返回文件，/thumb/<path> 视频封面缩略图。

只做一件事：把图片/PDF/视频以"二进制流"形式返回给浏览器原生渲染/播放。

【与其它模块的分工】
- 路径校验来自 services/path_utils，视频抽帧来自 services/media_utils（纯逻辑层）
- 查看页由 view 蓝图负责，下载附件由 download 蓝图负责
"""

import os

from flask import Blueprint, Response, abort, send_file

from config import (
    AUDIO_EXTENSIONS,
    AUDIO_MIME,
    IMAGE_EXTENSIONS,
    IMAGE_MIME,
    PDF_EXTENSIONS,
    VIDEO_EXTENSIONS,
    VIDEO_MIME,
)  # 扩展名配置表
from services.media_utils import ensure_playable, get_cover_thumb, get_image_thumb, get_video_thumb  # 视频兼容转换 + 封面抽帧 + 图片缩略图
from services.path_utils import safe_path         # 路径安全校验

# 创建"媒体"蓝图；模板里 url_for('media.xxx') 的 media 即此名字
media_bp = Blueprint("media", __name__)


@media_bp.route("/media/<path:subpath>")
def media(subpath: str):
    """以二进制流返回图片/PDF/视频文件内容（仅限 text 目录内）。

    send_file 由 Flask 直接流式发送文件（支持 Range 请求，可拖动进度条），
    并带上正确的 MIME 类型，浏览器才能直接渲染图片/内嵌 PDF/播放视频，
    而不是当成附件下载。视频交给浏览器自带播放器原生播放。
    """
    target = safe_path(subpath)  # 防目录穿越
    if target is None or not os.path.isfile(target):
        abort(404)
    ext = os.path.splitext(target)[1].lower()
    if ext in VIDEO_EXTENSIONS:
        # 先做手机兼容转换（HEVC→H.264 / moov 前置），返回可播放路径
        playable = ensure_playable(target)
        return send_file(playable, mimetype=VIDEO_MIME.get(ext, "video/mp4"))
    if ext in AUDIO_EXTENSIONS:
        # 音频：直接流式返回，浏览器原生 <audio> 播放（同样支持 Range 拖动进度）
        return send_file(target, mimetype=AUDIO_MIME.get(ext, "audio/mpeg"))
    if ext in IMAGE_EXTENSIONS:
        resp = send_file(target, mimetype=IMAGE_MIME.get(ext, "application/octet-stream"))
        # 图片 URL 恒定不变，允许浏览器缓存 1 小时，
        # 避免大图（动辄几 MB）在反复翻页时重复下载导致加载慢/失败
        resp.headers["Cache-Control"] = "public, max-age=3600"
        return resp
    if ext in PDF_EXTENSIONS:
        return send_file(target, mimetype="application/pdf")
    abort(404)


@media_bp.route("/thumb/<path:subpath>")
def thumb(subpath: str):
    """返回视频封面缩略图（JPG）；无法抽帧时返回 404。

    首帧由 ffmpeg 生成并缓存，之后直接读缓存，速度快。
    """
    target = safe_path(subpath)  # 防目录穿越
    if target is None or not os.path.isfile(target):
        abort(404)
    data = get_video_thumb(target)
    if data is None:
        abort(404)
    return Response(data, mimetype="image/jpeg")


@media_bp.route("/imgthumb/<path:subpath>")
def imgthumb(subpath: str):
    """返回图片压缩缩略图（JPG）；不支持的格式（SVG/ICO 等）返回 404。

    图片卡片与文件夹封面统一走这里加载缩略图而非原图，
    目录里图片多时能显著减少流量与内存占用（原图仅查看页才加载）。
    缩略图由 Pillow 缩放生成并缓存，之后直接读缓存，速度快。
    """
    target = safe_path(subpath)  # 防目录穿越
    if target is None or not os.path.isfile(target):
        abort(404)
    data = get_image_thumb(target)
    if data is None:
        abort(404)
    return Response(data, mimetype="image/jpeg")


@media_bp.route("/imgcover/<path:subpath>")
def imgcover(subpath: str):
    """返回文件夹封面高清缩略图（JPG）；不支持的格式（SVG/ICO 等）返回 404。

    与 /imgthumb 的区别：缩放尺寸更大（900px 内、质量 88），供文件夹封面
    卡片展示；普通文件卡片仍走 /imgthumb（400px），页面加载更快。
    """
    target = safe_path(subpath)  # 防目录穿越
    if target is None or not os.path.isfile(target):
        abort(404)
    data = get_cover_thumb(target)
    if data is None:
        abort(404)
    return Response(data, mimetype="image/jpeg")

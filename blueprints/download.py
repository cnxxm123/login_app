"""download 模块（blueprints 包）
下载蓝图：/download/<path> 下载单个文件或把目录打包成 zip。

【本模块做什么】
- 目标是单个文件 → 以附件形式直接返回原文件（支持断点续传）
- 目标是目录 → 用内存 BytesIO 打包成 zip 再返回

【与其它模块的分工】
- 在线预览（图片/PDF/视频流式返回）由 media 蓝图负责，这里只做"下载附件"
- 路径安全校验来自 services/path_utils（纯逻辑层）
"""

import io
import os
import zipfile

from flask import Blueprint, abort, send_file

from services.path_utils import safe_path    # 路径安全校验

# 创建"下载"蓝图；模板里 url_for('download.xxx') 的 download 即此名字
download_bp = Blueprint("download", __name__)


@download_bp.route("/download/<path:subpath>")
def download_dir(subpath: str):
    """下载：单个文件 → 直接原样返回；目录 → 打包成 zip。

    典型用途：漫画目录一键打包下载 / 单独下载某个文件。
    - zip 内相对路径按目录结构保留（不含 __pycache__ / .pyc）
    - 用 BytesIO 在内存里生成，再流式返回给浏览器
    """
    target = safe_path(subpath)  # 防目录穿越
    if target is None:
        abort(404)

    # 单个文件：直接以附件形式返回原文件（无需打包）
    if os.path.isfile(target):
        return send_file(
            target,
            as_attachment=True,
            download_name=os.path.basename(target),
            conditional=True,  # 支持断点续传 / 进度条
        )

    if not os.path.isdir(target):
        abort(404)

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(target):
            dirs[:] = [d for d in dirs if d != "__pycache__"]  # 剪枝，不打包缓存
            for name in files:
                if name.endswith(".pyc"):
                    continue
                full = os.path.join(root, name)
                arc = os.path.relpath(full, target)  # zip 内相对路径
                zf.write(full, arc)
    buf.seek(0)
    base = os.path.basename(target) or "download"
    return send_file(
        buf,
        as_attachment=True,
        download_name=f"{base}.zip",
        mimetype="application/zip",
    )

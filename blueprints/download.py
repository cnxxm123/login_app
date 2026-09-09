"""download 模块（blueprints 包）
下载蓝图：/download/<path> 下载单个文件或把目录打包成 zip。

【本模块做什么】
- 目标是单个文件 → 以附件形式直接返回原文件（支持断点续传）
- 目标是目录 → 用内存 BytesIO 打包成 zip 再返回

【与其它模块的分工】
- 在线预览（图片/PDF/视频流式返回）由 media 蓝图负责，这里只做"下载附件"
- 路径安全校验来自 services/path_utils（纯逻辑层）
"""

import os
import sys
import tempfile
import zipfile
from urllib.parse import quote as _url_quote

from flask import Blueprint, abort, Response, send_file

from services.path_utils import safe_path    # 路径安全校验

# 创建"下载"蓝图；模板里 url_for('download.xxx') 的 download 即此名字
download_bp = Blueprint("download", __name__)


@download_bp.route("/download/<path:subpath>")
def download_dir(subpath: str):
    """下载：单个文件 → 直接原样返回；目录 → 打包成 zip。

    典型用途：漫画目录一键打包下载 / 单独下载某个文件。
    - zip 内相对路径按目录结构保留（不含 __pycache__ / .pyc）
    - 目录打包**写入磁盘临时文件**（而非内存 BytesIO）：
      大目录（几个 GB）打包时内存占用恒定，不会撑爆内存导致卡顿；
      临时文件在响应发送完毕后自动删除，不残留垃圾。
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

    # 用 mkstemp 创建临时 zip：返回 (fd, 路径)，立即关闭 fd，
    # 之后只通过路径操作，避免句柄泄漏。
    fd, tmp_path = tempfile.mkstemp(suffix=".zip")
    os.close(fd)
    try:
        # zipfile 直接写文件路径（磁盘），压缩过程占用内存恒定
        with zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(target):
                dirs[:] = [d for d in dirs if d != "__pycache__"]  # 剪枝，不打包缓存
                for name in files:
                    if name.endswith(".pyc"):
                        continue
                    full = os.path.join(root, name)
                    arc = os.path.relpath(full, target)  # zip 内相对路径
                    zf.write(full, arc)
    except Exception:
        # 打包失败：立即删掉临时文件，避免残留占用磁盘
        try:
            os.remove(tmp_path)
        except OSError:
            pass
        raise

    # 流式发送 zip，发送完（或客户端中断）后由生成器的 finally 删除临时文件。
    # 不直接用 send_file：send_file 对磁盘文件走文件包装器，close 回调不可靠；
    # 生成器在迭代结束/异常/断开时必然执行 finally，保证临时文件被清理。
    def generate():
        try:
            with open(tmp_path, "rb") as f:
                while True:
                    chunk = f.read(64 * 1024)
                    if not chunk:
                        break
                    yield chunk
        finally:
            try:
                os.remove(tmp_path)
                print(f"[download] cleaned {tmp_path}", file=sys.stderr)
            except OSError as e:
                print(f"[download] cleanup failed {tmp_path}: {e}", file=sys.stderr)

    base = os.path.basename(target) or "download"
    filename = f"{base}.zip"
    resp = Response(generate(), mimetype="application/zip")
    # 中文文件名用 RFC 5987 编码（filename*=UTF-8''...），避免下载名乱码
    resp.headers["Content-Disposition"] = (
        "attachment; "
        f"filename=\"download.zip\"; filename*=UTF-8''{_url_quote(filename)}"
    )
    # 预知总大小：浏览器据此显示下载进度条（生成器响应不会自动带 Content-Length）
    resp.headers["Content-Length"] = str(os.path.getsize(tmp_path))
    return resp
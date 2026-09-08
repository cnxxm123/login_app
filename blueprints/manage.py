"""manage 模块（blueprints 包）
管理蓝图：文件上传、新建文件夹、在线文本编辑。

路由前缀：/upload、/mkdir、/edit、/save。
操作完成后重定向回操作所在的目录页，避免停留在失效路径：
- 在当前目录内新增内容的操作（mkdir/upload）跳回当前目录。

【与其它模块的分工】
- 路径安全校验来自 services/path_utils（纯逻辑层）
"""

import os

from flask import Blueprint, abort, redirect, render_template, request, url_for

from config import CODE_LANGUAGES, TEXT_EXTENSIONS
from services.path_utils import safe_path
from services.text_utils import read_text_file

manage_bp = Blueprint("manage", __name__)


def _redirect_here(subpath: str):
    """操作完成后跳回当前目录（subpath 为空 → 根目录）。

    用于 mkdir / upload 这类不改变当前目录自身路径的操作，
    让用户留在原地继续操作，而不是被弹回上级目录。
    """
    if subpath:
        return redirect(url_for("browser.browse", subpath=subpath))
    return redirect(url_for("browser.main"))


def _save_upload(target: str, f):
    """把单个上传文件保存到 target 下。

    普通上传：f.filename 只是文件名 → 直接保存到 target；
    文件夹上传：前端用 JS 把 webkitRelativePath（如 "漫画/第1话/001.jpg"）
    作为上传文件名提交，这里据此逐级建目录还原目录结构。

    【防目录穿越】对文件名里的每个路径段做校验：
    不允许空段 / "." / ".."，不允许含盘符(冒号)或空字节；
    最后再用 realpath 确认最终路径落在 target 之内，
    杜绝 ../、软链接等逃逸到 text 目录之外。
    """
    rel = (f.filename or "").replace("\\", "/").lstrip("/")  # 统一分隔符并去掉开头的 /
    parts = rel.split("/")
    if not parts or not parts[-1]:
        return  # 空文件名：跳过
    for p in parts:
        if p in ("", ".", "..") or ":" in p or "\x00" in p:
            return  # 非法路径段：丢弃该文件
    dest = os.path.join(target, *parts)
    # realpath 会解析 .. 与软链接；dest 不在 target 内说明已逃逸，拒绝保存
    real_target = os.path.realpath(target)
    if os.path.commonpath([real_target, os.path.realpath(dest)]) != real_target:
        return
    os.makedirs(os.path.dirname(dest), exist_ok=True)  # 逐级创建父目录
    f.save(dest)


def _do_upload(subpath: str):
    """把请求里的多个文件保存到指定目录（同名直接覆盖；文件夹上传自动建目录）。"""
    target = safe_path(subpath)
    if target is None or not os.path.isdir(target):
        abort(404)
    for f in request.files.getlist("files"):
        _save_upload(target, f)
    return _redirect_here(subpath)  # 留在当前目录


@manage_bp.route("/upload/", methods=["POST"])
def upload_root():
    """上传到根目录（subpath 为空时 <path:> 无法匹配，需单独一条路由）。"""
    return _do_upload("")


@manage_bp.route("/upload/<path:subpath>", methods=["POST"])
def upload(subpath: str):
    """上传：把请求里的多个文件保存到当前目录。"""
    return _do_upload(subpath)


def _do_mkdir(subpath: str):
    """在当前目录下新建文件夹。

    文件夹名取表单字段 new_folder：去首尾空格后，
    不允许为空 / "." / ".." / 含路径分隔符（防目录穿越）；
    同名存在时返回 409。
    """
    target = safe_path(subpath)
    if target is None or not os.path.isdir(target):
        abort(404)
    name = (request.form.get("new_folder") or "").strip()
    if not name or name in (".", "..") or "/" in name or "\\" in name:
        abort(400)
    new_path = os.path.join(target, name)
    if os.path.exists(new_path):
        abort(409)  # 同名文件/文件夹已存在
    os.mkdir(new_path)
    return _redirect_here(subpath)  # 留在当前目录


@manage_bp.route("/mkdir/", methods=["POST"])
def mkdir_root():
    """在根目录新建文件夹（subpath 为空时 <path:> 无法匹配，需单独一条路由）。"""
    return _do_mkdir("")


@manage_bp.route("/mkdir/<path:subpath>", methods=["POST"])
def mkdir(subpath: str):
    """新建文件夹：new_folder 为表单字段，在当前目录下创建。"""
    return _do_mkdir(subpath)


def _is_editable(target: str) -> bool:
    """该文件是否可在网页上编辑：命中文本/代码扩展名才允许（二进制不可编辑）。"""
    ext = os.path.splitext(target)[1].lower()
    return ext in TEXT_EXTENSIONS or ext in CODE_LANGUAGES


@manage_bp.route("/edit/<path:subpath>", methods=["GET"])
def edit(subpath: str):
    """在线文本编辑器：读取文本文件内容并渲染编辑页。

    只允许编辑文本/代码类文件（_is_editable 校验），其余返回 400；
    路径非法或文件不存在返回 404。内容读取沿用 view 的多编码读取
    （utf-8 → gbk），页面顶部提示原编码，保存时统一写 utf-8。
    """
    target = safe_path(subpath)
    if target is None or not os.path.isfile(target):
        abort(404)
    if not _is_editable(target):
        abort(400)
    content, enc = read_text_file(target)
    if content is None:
        abort(400)  # 无法识别的编码：禁止编辑，防止保存后乱码
    parent = os.path.dirname(subpath).replace("\\", "/")
    return render_template(
        "editor.html",
        content=content,
        filename=os.path.basename(subpath),
        path=subpath,
        enc=enc,
        parent=parent,
    )


@manage_bp.route("/save/<path:subpath>", methods=["POST"])
def save(subpath: str):
    """保存编辑内容：把表单 content 写回文本文件（统一 utf-8）。

    只允许编辑文本/代码类文件；保存成功后跳回查看页并带 saved=1，
    前端据此弹出"已保存"提示。内容来自服务端随模板下发，无需担心
    markdown 渲染注入（保存的是原文，不做任何解析）。
    """
    target = safe_path(subpath)
    if target is None or not os.path.isfile(target):
        abort(404)
    if not _is_editable(target):
        abort(400)
    content = request.form.get("content") or ""
    # 先校验编码再落盘：读不出原文就不允许改（防止乱码文件被覆盖）
    if read_text_file(target)[0] is None:
        abort(400)
    with open(target, "w", encoding="utf-8") as f:
        f.write(content)
    return redirect(url_for("view.view_file", subpath=subpath, saved=1))

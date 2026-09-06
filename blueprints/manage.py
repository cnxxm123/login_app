"""manage 模块（blueprints 包）
管理蓝图：文件上传、重命名、删除（文件/文件夹）、新建文件夹、
在线文本编辑、移动/复制、批量操作（批量移动/复制/删除）。

路由前缀：/upload、/rename、/delete、/mkdir、/edit、/save、
/move、/copy、/batch_move、/batch_copy、/batch_delete。
操作完成后重定向回操作所在的目录页，避免停留在失效路径：
- 改变条目自身路径的操作（rename/delete/move/copy 等）跳回其上级目录；
- 在当前目录内新增内容的操作（mkdir/upload）跳回当前目录。

【与其它模块的分工】
- 路径安全校验来自 services/path_utils（纯逻辑层）
- 移动/复制/批量操作的核心逻辑来自 services/file_ops（纯逻辑层）
- 删除为"软删除"：不再物理清除，而是移入回收站（services/trash_utils），可还原
"""

import json
import os

from flask import Blueprint, abort, jsonify, redirect, render_template, request, url_for

from config import CODE_LANGUAGES, TEXT_EXTENSIONS
from services import file_ops, trash_utils
from services.path_utils import safe_path
from services.text_utils import read_text_file

manage_bp = Blueprint("manage", __name__)


def _redirect_back(subpath: str):
    """操作完成后跳回目标条目的上级目录（上级可能为空 → 根目录）。"""
    parent = os.path.dirname(subpath).replace("\\", "/")
    if parent:
        return redirect(url_for("browser.browse", subpath=parent))
    return redirect(url_for("browser.main"))


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
    不允许为空 / "." / ".." / 含路径分隔符（防目录穿越），
    与 rename 的新名称校验保持一致；同名存在时返回 409。
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


@manage_bp.route("/rename/<path:subpath>", methods=["POST"])
def rename(subpath: str):
    """重命名：new_name 为表单字段；拒绝包含路径分隔符或与现同名。"""
    target = safe_path(subpath)
    if target is None or not os.path.exists(target):
        abort(404)
    new_name = (request.form.get("new_name") or "").strip()
    # 防目录穿越：新名称里不允许出现路径分隔符
    if not new_name or "/" in new_name or "\\" in new_name:
        abort(400)
    new_path = os.path.join(os.path.dirname(target), new_name)
    if os.path.exists(new_path):
        abort(409)  # 同名文件已存在
    os.rename(target, new_path)
    return _redirect_back(subpath)


@manage_bp.route("/delete/<path:subpath>", methods=["POST"])
def delete(subpath: str):
    """删除：软删除，把文件/目录移入回收站（可还原，前端有确认弹窗）。"""
    if not trash_utils.move_to_trash(subpath):
        abort(404)
    return _redirect_back(subpath)


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


def _json_redirect_error(msg: str, status: int):
    """批量/移动复制接口返回统一 JSON 错误体。"""
    return jsonify({"ok": False, "error": msg}), status


def _parse_paths() -> list:
    """从表单解析条目路径列表（paths 可多值，也用逗号分隔兜底）。"""
    raw = request.form.getlist("paths")
    paths = []
    for p in raw:
        paths += [x for x in p.split(",") if x]
    return paths


@manage_bp.route("/move/<path:subpath>", methods=["POST"])
def move(subpath: str):
    """移动单个条目：dest_subpath 为表单字段（目标目录相对路径）。"""
    dest = (request.form.get("dest_subpath") or "").strip()
    ok, msg = file_ops.move_item(subpath, dest)
    if not ok:
        return _json_redirect_error(
            {"not_found": "源文件不存在", "bad_dest": "目标目录无效", "into_self": "不能移动到自己的子目录"}.get(msg, "移动失败"),
            400 if msg != "not_found" else 404,
        )
    return jsonify({"ok": True, "name": msg})


@manage_bp.route("/copy/<path:subpath>", methods=["POST"])
def copy(subpath: str):
    """复制单个条目：dest_subpath 为表单字段（目标目录相对路径）。"""
    dest = (request.form.get("dest_subpath") or "").strip()
    ok, msg = file_ops.copy_item(subpath, dest)
    if not ok:
        return _json_redirect_error(
            {"not_found": "源文件不存在", "bad_dest": "目标目录无效", "into_self": "不能复制到自己的子目录"}.get(msg, "复制失败"),
            400 if msg != "not_found" else 404,
        )
    return jsonify({"ok": True, "name": msg})


@manage_bp.route("/batch_move/", methods=["POST"])
def batch_move():
    """批量移动：paths 为条目列表（表单多值/逗号分隔），dest_subpath 为目标目录。"""
    paths = _parse_paths()
    if not paths:
        return _json_redirect_error("未选择任何条目", 400)
    ok, fail, valid, errors = file_ops.move_items(paths, (request.form.get("dest_subpath") or "").strip())
    if not valid:
        return _json_redirect_error("目标目录无效", 400)
    return jsonify({"ok": True, "succeed": ok, "failed": fail, "errors": errors})


@manage_bp.route("/batch_copy/", methods=["POST"])
def batch_copy():
    """批量复制：paths 为条目列表（表单多值/逗号分隔），dest_subpath 为目标目录。"""
    paths = _parse_paths()
    if not paths:
        return _json_redirect_error("未选择任何条目", 400)
    ok, fail, valid, errors = file_ops.copy_items(paths, (request.form.get("dest_subpath") or "").strip())
    if not valid:
        return _json_redirect_error("目标目录无效", 400)
    return jsonify({"ok": True, "succeed": ok, "failed": fail, "errors": errors})


@manage_bp.route("/batch_delete/", methods=["POST"])
def batch_delete():
    """批量删除：paths 为条目列表（表单多值/逗号分隔），逐条软删除进回收站。"""
    paths = _parse_paths()
    if not paths:
        return _json_redirect_error("未选择任何条目", 400)
    ok = fail = 0
    errors = []
    for p in paths:
        if trash_utils.move_to_trash(p):
            ok += 1
        else:
            fail += 1
            errors.append(p)
    return jsonify({"ok": True, "succeed": ok, "failed": fail, "errors": errors})

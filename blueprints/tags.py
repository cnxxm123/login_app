"""tags 模块（blueprints 包）
文件标签蓝图：标签管理页、按标签筛选、打标签 / 取消标签。

路由前缀：/tags、/tags/filter、/tag/set、/tag/remove、/tag/get。

【本模块做什么】
- /tags           标签管理页：列出全部标签及使用次数，可点标签筛选
- /tags/filter    按标签筛选：展示打了某标签的全部文件/目录
- /tag/set        打标签：把某路径的标签整体替换为指定列表（前端弹窗编辑）
- /tag/remove     取消标签：移除某路径下的某个标签
- /tag/get        查询标签：返回某路径当前全部标签（编辑弹窗预填用）

【与其它模块的分工】
- 数据库读写全部委托给 services/tag_store（纯逻辑层），本模块只处理 HTTP
- 路径合法性校验复用 services/path_utils 的 safe_path（防目录穿越）
- 文件条目展示复用 browser 的 build_file_items，保证卡片样式一致
"""

import os

from flask import Blueprint, jsonify, redirect, render_template, request, url_for

from blueprints.browser import build_file_items  # 复用浏览页的卡片构建
from services import tag_store  # 标签数据库读写（纯逻辑层）
from services.path_utils import safe_path  # 路径安全校验

# 创建"标签"蓝图；模板里 url_for('tags.xxx') 的 tags 即此名字
tags_bp = Blueprint("tags", __name__)


@tags_bp.route("/tags")
def index():
    """标签管理页：列出全部标签及使用次数。"""
    return render_template(
        "tags.html",
        tags=tag_store.all_tags(),  # [{"name", "count"}, ...]
    )


@tags_bp.route("/tags/filter")
def filter_page():
    """按标签筛选：?tag=标签名 展示打了该标签的全部文件/目录。

    只保留仍真实存在的条目（文件被删除后标签残留，这里自动跳过）。
    """
    tag = (request.args.get("tag") or "").strip()
    if not tag:
        return redirect(url_for("tags.index"))
    dirs, files = [], []
    for p in tag_store.paths_by_tag(tag):  # 打该标签的路径（打标时间倒序）
        target = safe_path(p)
        if target is None:
            continue  # 路径非法（越界/不存在）→ 跳过
        if os.path.isdir(target):
            dirs.append({"path": p, "name": os.path.basename(p), "tags": tag_store.get_tags(p)})
        elif os.path.isfile(target):
            # 复用浏览页的卡片构建逻辑（缩略图/图标/外链/编辑按钮等），
            # rel 直接返回该文件自身的完整相对路径，build_file_items 就能正常工作
            item = build_file_items([os.path.basename(p)], lambda n: p)[0]
            item["tags"] = tag_store.get_tags(p)
            files.append(item)
    return render_template(
        "filter.html",
        tag=tag,
        dirs=dirs,
        files=files,
    )


@tags_bp.route("/tag/get", methods=["GET"])
def tag_get():
    """查询某路径当前全部标签，返回 JSON（编辑弹窗预填用）。"""
    path = (request.args.get("path") or "").strip()
    if not path:
        return jsonify({"ok": False, "error": "缺少路径"}), 400
    return jsonify({"ok": True, "tags": tag_store.get_tags(path)})


@tags_bp.route("/tag/set", methods=["POST"])
def tag_set():
    """打标签：把 path 的标签整体替换为 tags（可逗号分隔多个）。

    表单字段：path（相对路径）、tags（逗号分隔标签串，可空=清空标签）。
    先校验路径真实存在（在 text 目录内且存在），再交给 tag_store 落库。
    """
    path = (request.form.get("path") or "").strip()
    tags = (request.form.get("tags") or "").strip()
    if not path or safe_path(path) is None:
        return jsonify({"ok": False, "error": "路径无效"}), 400
    if not tag_store.set_tags(path, tags):
        return jsonify({"ok": False, "error": "保存失败"}), 500
    return jsonify({"ok": True, "tags": tag_store.get_tags(path)})


@tags_bp.route("/tag/remove", methods=["POST"])
def tag_remove():
    """取消标签：移除 path 下的某个标签。

    表单字段：path（相对路径）、tag（要移除的标签名）。
    """
    path = (request.form.get("path") or "").strip()
    tag = (request.form.get("tag") or "").strip()
    if not path or not tag:
        return jsonify({"ok": False, "error": "参数不完整"}), 400
    if not tag_store.remove_tag(path, tag):
        return jsonify({"ok": False, "error": "标签不存在"}), 404
    return jsonify({"ok": True})


@tags_bp.route("/tag/delete", methods=["POST"])
def tag_delete():
    """删除整个标签：从标签表删除，并清掉所有文件上的该标签。

    表单字段：tag（标签名）。操作不可恢复，前端需二次确认。
    """
    name = (request.form.get("tag") or "").strip()
    if not name:
        return jsonify({"ok": False, "error": "缺少标签名"}), 400
    if not tag_store.delete_tag(name):
        return jsonify({"ok": False, "error": "标签不存在"}), 404
    return jsonify({"ok": True})

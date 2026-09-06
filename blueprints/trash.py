"""trash 模块（blueprints 包）
回收站蓝图：查看 / 还原 / 彻底删除 / 清空。

路由前缀：/trash。
- GET  /trash              回收站列表页
- POST /trash/restore/<name>  还原到原位置（原位置被占则 409）
- POST /trash/delete/<name>   彻底删除（不可恢复）
- POST /trash/empty           清空回收站

【与其它模块的分工】
- 回收站纯逻辑在 services/trash_utils（移动/列表/还原/清除）
- 删除入口在 blueprints/manage（改为移入回收站的软删除）
"""

import os

from flask import Blueprint, abort, redirect, render_template, url_for

from services import trash_utils

trash_bp = Blueprint("trash", __name__)


@trash_bp.route("/trash")
def index():
    """回收站列表页：展示所有已删除条目及原位置 / 删除时间。"""
    items = trash_utils.list_trash()
    return render_template("trash.html", items=items)


@trash_bp.route("/trash/restore/<name>", methods=["POST"])
def restore(name: str):
    """还原：移回原位置；原位置已有同名项返回 409，成功后跳回原目录。"""
    ok, result = trash_utils.restore(name)
    if not ok:
        if result == "conflict":
            abort(409)
        abort(404)
    parent = os.path.dirname(result).replace("\\", "/")
    if parent:
        return redirect(url_for("browser.browse", subpath=parent))
    return redirect(url_for("browser.main"))


@trash_bp.route("/trash/delete/<name>", methods=["POST"])
def delete(name: str):
    """彻底删除单个条目（物理删除，前端有二次确认）。"""
    if not trash_utils.permanent_delete(name):
        abort(404)
    return redirect(url_for("trash.index"))


@trash_bp.route("/trash/empty", methods=["POST"])
def empty():
    """清空回收站（全部物理删除，前端有二次确认）。"""
    trash_utils.empty_trash()
    return redirect(url_for("trash.index"))

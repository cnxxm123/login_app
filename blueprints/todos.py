"""todos 模块（blueprints 包）
待办事项蓝图：待办列表页 + 增 / 改 / 删 / 完成切换 / 拖拽排序 / 导出接口。

路由前缀：/todos、/todo/add、/todo/update、/todo/delete、/todo/toggle、/todo/reorder、/todo/export。

【本模块做什么】
- /todos          待办页：按日期分组展示全部待办，标注「今天 / 昨天」，显示截止日期与完成状态
- /todo/add       新增待办：表单 todo_date、content、due_date（可选）
- /todo/update    修改待办：表单 id、todo_date、content、due_date
- /todo/toggle    切换完成状态：表单 id
- /todo/delete    删除待办：表单 id
- /todo/reorder   拖拽排序后批量更新 sort_order
- /todo/export    导出全部待办为 Markdown 文本

【与其它模块的分工】
- 待办读写全部委托给 services/todo_store（纯逻辑层，JSON 文件存储），本模块只处理 HTTP
- 与 logs 蓝图的写法保持一致：POST 接口返回 JSON，页面用 fetch 调用
"""

import datetime  # 日期解析
import json  # 序列化待办内容给前端编辑弹窗预填

from flask import Blueprint, Response, jsonify, render_template, request
from markupsafe import Markup, escape  # 安全转义待办正文后插入 <br>

from blueprints._common import group_label, safe_int_id, valid_date  # 共享工具
from services import todo_store  # 待办读写（纯逻辑层）

# 创建"待办事项"蓝图；模板里 url_for('todos.xxx') 的 todos 即此名字
todos_bp = Blueprint("todos", __name__)


@todos_bp.route("/todos")
def index():
    """待办事项页：按日期倒序分组展示全部待办。"""
    rows = todo_store.all_todos()
    today = datetime.date.today().isoformat()
    groups = []  # [{"label", "date", "todos": [{id, todo_date, content, time, done, due_date, due_overdue, edited}]}]
    for row in rows:
        d = datetime.date.fromisoformat(row["todo_date"])
        # 截止日期判断是否过期
        due_overdue = False
        if row.get("due_date"):
            try:
                due_overdue = not row["done"] and datetime.date.fromisoformat(row["due_date"]) < datetime.date.today()
            except (ValueError, TypeError):
                pass
        item = {
            "id": row["id"],
            "todo_date": row["todo_date"],
            "content_html": Markup(str(escape(row["content"])).replace("\n", "<br>")),
            "time": row["created_at"].strftime("%H:%M"),
            "done": row["done"],
            "due_date": row.get("due_date") or None,  # 截止日期（可选）
            "due_overdue": due_overdue,  # 是否已过期
            "edited": row["updated_at"] is not None and row["updated_at"] > row["created_at"],
        }
        if groups and groups[-1]["date"] == row["todo_date"]:
            groups[-1]["todos"].append(item)
        else:
            groups.append({"label": group_label(d), "date": row["todo_date"], "todos": [item]})
    # 编辑弹窗预填用：{id: {content, due_date}} 的 JSON 映射
    todos_json = json.dumps(
        {str(r["id"]): {"content": r["content"], "due_date": r["due_date"]} for r in rows},
        ensure_ascii=False,
    ).replace("<", "\\u003c")
    return render_template(
        "todos.html",
        groups=groups,
        total=len(rows),
        today_count=sum(1 for r in rows if r["todo_date"] == today),
        undone_count=sum(1 for r in rows if not r["done"]),
        todos_json=todos_json,
    )


@todos_bp.route("/todo/add", methods=["POST"])
def todo_add():
    """新增待办。表单字段：todo_date、content、due_date（可选）。"""
    todo_date = (request.form.get("todo_date") or "").strip()
    content = (request.form.get("content") or "").strip()
    due_date = (request.form.get("due_date") or "").strip()
    if not valid_date(todo_date):
        return jsonify({"ok": False, "error": "日期格式不正确"}), 400
    if due_date and not valid_date(due_date):
        return jsonify({"ok": False, "error": "截止日期格式不正确"}), 400
    if not content:
        return jsonify({"ok": False, "error": "内容不能为空"}), 400
    return jsonify({"ok": True, "id": todo_store.add_todo(todo_date, content, due_date)})


@todos_bp.route("/todo/update", methods=["POST"])
def todo_update():
    """修改待办。表单字段：id、todo_date、content、due_date（可选）。"""
    try:
        todo_id = safe_int_id(request.form.get("id"))
    except ValueError:
        return jsonify({"ok": False, "error": "参数不正确"}), 400
    todo_date = (request.form.get("todo_date") or "").strip()
    content = (request.form.get("content") or "").strip()
    due_date = (request.form.get("due_date") or "").strip()
    if not valid_date(todo_date):
        return jsonify({"ok": False, "error": "日期格式不正确"}), 400
    if due_date and not valid_date(due_date):
        return jsonify({"ok": False, "error": "截止日期格式不正确"}), 400
    if not content:
        return jsonify({"ok": False, "error": "内容不能为空"}), 400
    if not todo_store.update_todo(todo_id, todo_date, content, due_date):
        return jsonify({"ok": False, "error": "待办不存在"}), 404
    return jsonify({"ok": True})


@todos_bp.route("/todo/toggle", methods=["POST"])
def todo_toggle():
    try:
        todo_id = safe_int_id(request.form.get("id"))
    except ValueError:
        return jsonify({"ok": False, "error": "参数不正确"}), 400
    if not todo_store.toggle_done(todo_id):
        return jsonify({"ok": False, "error": "待办不存在"}), 404
    return jsonify({"ok": True})


@todos_bp.route("/todo/delete", methods=["POST"])
def todo_delete():
    try:
        todo_id = safe_int_id(request.form.get("id"))
    except ValueError:
        return jsonify({"ok": False, "error": "参数不正确"}), 400
    if not todo_store.delete_todo(todo_id):
        return jsonify({"ok": False, "error": "待办不存在"}), 404
    return jsonify({"ok": True})


@todos_bp.route("/todo/reorder", methods=["POST"])
def todo_reorder():
    """拖拽排序后批量更新 sort_order。JSON 正文：[{id, sort_order}, ...]。"""
    try:
        orders = request.get_json(force=True)
    except Exception:
        return jsonify({"ok": False, "error": "数据格式不正确"}), 400
    if not isinstance(orders, list):
        return jsonify({"ok": False, "error": "数据格式不正确"}), 400
    todo_store.reorder_todos(orders)
    return jsonify({"ok": True})


@todos_bp.route("/todo/export")
def todo_export():
    """导出全部待办为 Markdown 文本（.md 下载）。"""
    rows = todo_store.all_todos()
    today = datetime.date.today().isoformat()
    lines = ["# 待办事项", "", f"导出时间：{today}", "", "---", ""]
    cur_date = None
    for r in rows:
        if r["todo_date"] != cur_date:
            cur_date = r["todo_date"]
            lines.append(f"## {cur_date}")
            lines.append("")
        status = "[✓]" if r["done"] else "[ ]"
        due = f' (截止: {r["due_date"]})' if r.get("due_date") else ""
        lines.append(f"- {status}{due} {r['content']}")
    lines.append("")
    content = "\n".join(lines)
    return Response(
        content.encode("utf-8"),
        mimetype="text/markdown",
        headers={"Content-Disposition": "attachment; filename=todos.md"},
    )

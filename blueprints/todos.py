"""todos 模块（blueprints 包）
待办事项蓝图：待办列表页 + 增 / 改 / 删 / 完成切换接口。

路由前缀：/todos、/todo/add、/todo/update、/todo/delete、/todo/toggle。

【本模块做什么】
- /todos          待办页：按日期分组展示全部待办，标注「今天 / 昨天」，显示完成状态
- /todo/add       新增待办：表单 todo_date（YYYY-MM-DD）、category（类别）、content
- /todo/update    修改待办：表单 id、todo_date、category、content
- /todo/toggle    切换完成状态：表单 id
- /todo/delete    删除待办：表单 id

【与其它模块的分工】
- 待办读写全部委托给 services/todo_store（纯逻辑层，JSON 文件存储），本模块只处理 HTTP
- 与 logs 蓝图的写法保持一致：POST 接口返回 JSON，页面用 fetch 调用
"""

import datetime  # 日期解析 / 今天 / 昨天 判断
import json  # 序列化待办内容给前端编辑弹窗预填

from flask import Blueprint, jsonify, render_template, request
from markupsafe import Markup, escape  # 安全转义待办正文后插入 <br>

from config import WORK_CATEGORIES  # 工作类别白名单（上架游戏 / 更新游戏 / 问题处理）
from services import log_store  # 工作日志读写：完成待办时转移到今天的日志
from services import todo_store  # 待办读写（纯逻辑层）

# 创建"待办事项"蓝图；模板里 url_for('todos.xxx') 的 todos 即此名字
todos_bp = Blueprint("todos", __name__)

_WEEKDAYS = "一二三四五六日"  # 周几的中文显示


def _valid_date(s: str) -> bool:
    """校验日期字符串是否为合法 YYYY-MM-DD。"""
    try:
        datetime.date.fromisoformat(s)
        return True
    except (ValueError, TypeError):
        return False


def _valid_category(s: str) -> bool:
    """校验类别是否在白名单内（防提交任意类别破坏界面配色）。"""
    return s in WORK_CATEGORIES


def _group_label(d: datetime.date) -> str:
    """返回日期分组的显示标签：今天 / 昨天 / 「2026年9月4日 周五」。"""
    today = datetime.date.today()
    if d == today:
        return "今天"
    if d == today - datetime.timedelta(days=1):
        return "昨天"
    return f"{d.year}年{d.month}月{d.day}日 周{_WEEKDAYS[d.weekday()]}"


@todos_bp.route("/todos")
def index():
    """待办事项页：按日期倒序分组展示全部待办。"""
    rows = todo_store.all_todos()
    groups = []  # [{"label", "date", "todos": [{id, todo_date, category, content, time, done, edited}]}]
    for row in rows:
        d = datetime.date.fromisoformat(row["todo_date"])
        item = {
            "id": row["id"],
            "todo_date": row["todo_date"],
            "category": row["category"],
            # 正文先整体 HTML 转义（防 XSS），再把换行替换为 <br>，包装成 Markup 直接渲染
            "content_html": Markup(str(escape(row["content"])).replace("\n", "<br>")),
            # 创建时间 HH:MM，用于列表左侧时间戳
            "time": row["created_at"].strftime("%H:%M"),
            "done": row["done"],
            # 是否被编辑过（updated_at 晚于 created_at），显示小圆点提示
            "edited": row["updated_at"] is not None and row["updated_at"] > row["created_at"],
        }
        if groups and groups[-1]["date"] == row["todo_date"]:
            groups[-1]["todos"].append(item)
        else:
            groups.append({"label": _group_label(d), "date": row["todo_date"], "todos": [item]})
    today = datetime.date.today().isoformat()
    # 编辑弹窗预填用：{id: 记录} 的 JSON 映射（含类别与内容），直接嵌进页面 <script>。
    # ensure_ascii=False 保留中文；再把 < 转义成 \u003c，防止内容里的 </script> 破坏脚本标签。
    todos_json = json.dumps(
        {str(r["id"]): {"category": r["category"], "content": r["content"]} for r in rows},
        ensure_ascii=False,
    ).replace("<", "\\u003c")
    return render_template(
        "todos.html",
        groups=groups,
        total=len(rows),
        today_count=sum(1 for r in rows if r["todo_date"] == today),
        undone_count=sum(1 for r in rows if not r["done"]),  # 未完成数量统计
        todos_json=todos_json,
        categories=WORK_CATEGORIES,  # 类别列表，供新增/编辑弹窗下拉选择
    )


@todos_bp.route("/todo/add", methods=["POST"])
def todo_add():
    """新增待办。

    表单字段：todo_date（YYYY-MM-DD）、category（类别）、content（正文，非空）。
    返回 JSON：{ok, id} 或 {ok: False, error}。
    """
    todo_date = (request.form.get("todo_date") or "").strip()
    category = (request.form.get("category") or "").strip()
    content = (request.form.get("content") or "").strip()
    if not _valid_date(todo_date):
        return jsonify({"ok": False, "error": "日期格式不正确"}), 400
    if not _valid_category(category):
        return jsonify({"ok": False, "error": "请选择正确的类别"}), 400
    if not content:
        return jsonify({"ok": False, "error": "内容不能为空"}), 400
    return jsonify({"ok": True, "id": todo_store.add_todo(todo_date, category, content)})


@todos_bp.route("/todo/update", methods=["POST"])
def todo_update():
    """修改待办。

    表单字段：id（待办 id）、todo_date、category、content。
    """
    try:
        todo_id = int(request.form.get("id") or 0)
    except (ValueError, TypeError):
        return jsonify({"ok": False, "error": "参数不正确"}), 400
    todo_date = (request.form.get("todo_date") or "").strip()
    category = (request.form.get("category") or "").strip()
    content = (request.form.get("content") or "").strip()
    if not _valid_date(todo_date):
        return jsonify({"ok": False, "error": "日期格式不正确"}), 400
    if not _valid_category(category):
        return jsonify({"ok": False, "error": "请选择正确的类别"}), 400
    if not content:
        return jsonify({"ok": False, "error": "内容不能为空"}), 400
    if not todo_store.update_todo(todo_id, todo_date, category, content):
        return jsonify({"ok": False, "error": "待办不存在"}), 404
    return jsonify({"ok": True})


@todos_bp.route("/todo/toggle", methods=["POST"])
def todo_toggle():
    """切换完成状态。

    核心规则：从"未完成"勾选为"完成"时，把该待办**转移到工作日志**——
    以今天的日期、待办原有的类别和内容写入一条日志，然后删除原待办。
    这样今天的"问题处理/上架游戏/更新游戏"成果会汇总到今天的日志里。

    已完成的旧数据（历史遗留）取消勾选则仅恢复为未完成，不做转移。
    返回 JSON：{ok, moved}，moved=True 表示本次操作产生了转移。
    """
    try:
        todo_id = int(request.form.get("id") or 0)
    except (ValueError, TypeError):
        return jsonify({"ok": False, "error": "参数不正确"}), 400
    todo = todo_store.get_todo(todo_id)
    if todo is None:
        return jsonify({"ok": False, "error": "待办不存在"}), 404
    if not todo["done"]:
        # 未完成 → 完成：转移到今天的工作日志（保留类别与内容），并从待办移除
        log_store.add_log(
            datetime.date.today().isoformat(),  # 完成日期，即"今天"
            todo["category"],
            todo["content"],
        )
        todo_store.delete_todo(todo_id)
        return jsonify({"ok": True, "moved": True})
    # 已完成 → 未完成：只恢复状态（历史遗留的已完成数据），不产生转移
    todo_store.toggle_done(todo_id)
    return jsonify({"ok": True, "moved": False})


@todos_bp.route("/todo/delete", methods=["POST"])
def todo_delete():
    """删除待办。表单字段：id。"""
    try:
        todo_id = int(request.form.get("id") or 0)
    except (ValueError, TypeError):
        return jsonify({"ok": False, "error": "参数不正确"}), 400
    if not todo_store.delete_todo(todo_id):
        return jsonify({"ok": False, "error": "待办不存在"}), 404
    return jsonify({"ok": True})

"""logs 模块（blueprints 包）
工作日志蓝图：日志列表页 + 增 / 改 / 删接口。

路由前缀：/logs、/log/add、/log/update、/log/delete。

【本模块做什么】
- /logs          工作日志页：按日期分组展示全部日志，标注「今天 / 昨天」
- /log/add       新增日志：表单 log_date（YYYY-MM-DD）、content
- /log/update    修改日志：表单 id、log_date、content
- /log/delete    删除日志：表单 id

【与其它模块的分工】
- 日志读写全部委托给 services/log_store（纯逻辑层，JSON 文件存储），本模块只处理 HTTP
- 与 tags 蓝图的写法保持一致：POST 接口返回 JSON，页面用 fetch 调用
"""

import datetime  # 日期解析 / 今天 / 昨天 判断
import json  # 序列化日志内容给前端编辑弹窗预填

from flask import Blueprint, jsonify, render_template, request
from markupsafe import Markup, escape  # 安全转义日志正文后插入 <br>

from services import log_store  # 工作日志读写（纯逻辑层）

# 创建"工作日志"蓝图；模板里 url_for('logs.xxx') 的 logs 即此名字
logs_bp = Blueprint("logs", __name__)

_WEEKDAYS = "一二三四五六日"  # 周几的中文显示


def _valid_date(s: str) -> bool:
    """校验日期字符串是否为合法 YYYY-MM-DD。"""
    try:
        datetime.date.fromisoformat(s)
        return True
    except (ValueError, TypeError):
        return False


def _group_label(d: datetime.date) -> str:
    """返回日期分组的显示标签：今天 / 昨天 / 「2026年9月4日 周五」。"""
    today = datetime.date.today()
    if d == today:
        return "今天"
    if d == today - datetime.timedelta(days=1):
        return "昨天"
    return f"{d.year}年{d.month}月{d.day}日 周{_WEEKDAYS[d.weekday()]}"


@logs_bp.route("/logs")
def index():
    """工作日志页：按日期倒序分组展示全部日志。"""
    rows = log_store.all_logs()
    groups = []  # [{"label", "date", "logs": [{id, log_date, content, time, edited}]}]
    for row in rows:
        d = datetime.date.fromisoformat(row["log_date"])
        item = {
            "id": row["id"],
            "log_date": row["log_date"],
            # 正文先整体 HTML 转义（防 XSS），再把换行替换为 <br>，包装成 Markup 直接渲染。
            # 注意：不能对 Markup 直接 .replace，werkzeug 会把替换串也转义成 &lt;br&gt;
            "content_html": Markup(str(escape(row["content"])).replace("\n", "<br>")),
            # 创建时间 HH:MM，用于列表左侧时间戳
            "time": row["created_at"].strftime("%H:%M"),
            # 是否被编辑过（updated_at 晚于 created_at），显示小圆点提示
            "edited": row["updated_at"] is not None and row["updated_at"] > row["created_at"],
        }
        if groups and groups[-1]["date"] == row["log_date"]:
            groups[-1]["logs"].append(item)
        else:
            groups.append({"label": _group_label(d), "date": row["log_date"], "logs": [item]})
    today = datetime.date.today().isoformat()
    # 编辑弹窗预填用：{id: 内容} 的 JSON 映射，直接嵌进页面 <script>。
    # ensure_ascii=False 保留中文；再把 < 转义成 \u003c，防止内容里的 </script> 破坏脚本标签。
    logs_json = json.dumps(
        {str(r["id"]): r["content"] for r in rows}, ensure_ascii=False
    ).replace("<", "\\u003c")
    return render_template(
        "logs.html",
        groups=groups,
        total=len(rows),
        today_count=sum(1 for r in rows if r["log_date"] == today),
        logs_json=logs_json,
    )


@logs_bp.route("/log/add", methods=["POST"])
def log_add():
    """新增日志。

    表单字段：log_date（YYYY-MM-DD）、content（正文，非空）。
    返回 JSON：{ok, id} 或 {ok: False, error}。
    """
    log_date = (request.form.get("log_date") or "").strip()
    content = (request.form.get("content") or "").strip()
    if not _valid_date(log_date):
        return jsonify({"ok": False, "error": "日期格式不正确"}), 400
    if not content:
        return jsonify({"ok": False, "error": "内容不能为空"}), 400
    return jsonify({"ok": True, "id": log_store.add_log(log_date, content)})


@logs_bp.route("/log/update", methods=["POST"])
def log_update():
    """修改日志。

    表单字段：id（日志 id）、log_date、content。
    """
    try:
        log_id = int(request.form.get("id") or 0)
    except (ValueError, TypeError):
        return jsonify({"ok": False, "error": "参数不正确"}), 400
    log_date = (request.form.get("log_date") or "").strip()
    content = (request.form.get("content") or "").strip()
    if not _valid_date(log_date):
        return jsonify({"ok": False, "error": "日期格式不正确"}), 400
    if not content:
        return jsonify({"ok": False, "error": "内容不能为空"}), 400
    if not log_store.update_log(log_id, log_date, content):
        return jsonify({"ok": False, "error": "日志不存在"}), 404
    return jsonify({"ok": True})


@logs_bp.route("/log/delete", methods=["POST"])
def log_delete():
    """删除日志。表单字段：id。"""
    try:
        log_id = int(request.form.get("id") or 0)
    except (ValueError, TypeError):
        return jsonify({"ok": False, "error": "参数不正确"}), 400
    if not log_store.delete_log(log_id):
        return jsonify({"ok": False, "error": "日志不存在"}), 404
    return jsonify({"ok": True})

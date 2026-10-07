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
- POST 接口返回 JSON，页面用 fetch 调用
"""

import datetime  # 日期解析
import io  # 内存缓冲区：用于在内存中生成 Excel 文件再返回给客户端下载
import json  # 序列化日志内容给前端编辑弹窗预填

from flask import Blueprint, jsonify, render_template, request, Response
from markupsafe import Markup, escape  # 安全转义日志正文后插入 <br>
from openpyxl import Workbook  # 生成 .xlsx Excel 文件
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side  # Excel 单元格样式

from blueprints._common import group_label, safe_int_id, valid_category, valid_date  # 共享工具
from config import WORK_CATEGORIES  # 工作类别白名单（上架游戏 / 更新游戏 / 工单处理）
from services import log_store  # 工作日志读写（纯逻辑层）

# 创建"工作日志"蓝图；模板里 url_for('logs.xxx') 的 logs 即此名字
logs_bp = Blueprint("logs", __name__)


def _group_categories(items: list) -> list:
    """把同一天的记录按类别分组：类别白名单顺序在前，未分类（老数据）放最后。"""
    cat_map = {c: [] for c in WORK_CATEGORIES}
    uncat = []
    for item in items:
        if item["category"] in cat_map:
            cat_map[item["category"]].append(item)
        else:
            uncat.append(item)  # 空类别等未知值归入"未分类"
    cats = [{"cat": c, "items": cat_map[c]} for c in WORK_CATEGORIES if cat_map[c]]
    if uncat:
        cats.append({"cat": "未分类", "uncat": True, "items": uncat})
    return cats


@logs_bp.route("/logs")
def index():
    """工作日志页：按日期倒序分组展示全部日志。"""
    rows = log_store.all_logs()
    groups = []  # [{"label", "date", "logs": [{id, log_date, category, content, time, edited}]}]
    for row in rows:
        d = datetime.date.fromisoformat(row["log_date"])
        item = {
            "id": row["id"],
            "log_date": row["log_date"],
            "category": row["category"],
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
            groups.append({"label": group_label(d), "date": row["log_date"], "logs": [item]})
    # 日期分组内再按类别分组（cats），供模板渲染可折叠的类别子分组
    for g in groups:
        g["cats"] = _group_categories(g["logs"])
    today = datetime.date.today().isoformat()
    # 编辑弹窗预填用：{id: 记录} 的 JSON 映射（含类别与内容），直接嵌进页面 <script>。
    # ensure_ascii=False 保留中文；再把 < 转义成 \u003c，防止内容里的 </script> 破坏脚本标签。
    logs_json = json.dumps(
        {str(r["id"]): {"category": r["category"], "content": r["content"]} for r in rows},
        ensure_ascii=False,
    ).replace("<", "\\u003c")
    return render_template(
        "logs.html",
        groups=groups,
        total=len(rows),
        today_count=sum(1 for r in rows if r["log_date"] == today),
        logs_json=logs_json,
        categories=WORK_CATEGORIES,  # 类别列表，供新增/编辑弹窗下拉选择
    )


@logs_bp.route("/log/add", methods=["POST"])
def log_add():
    """新增日志。

    表单字段：log_date（YYYY-MM-DD）、category（类别）、content（正文，非空）。
    返回 JSON：{ok, id} 或 {ok: False, error}。
    """
    log_date = (request.form.get("log_date") or "").strip()
    category = (request.form.get("category") or "").strip()
    content = (request.form.get("content") or "").strip()
    if not valid_date(log_date):
        return jsonify({"ok": False, "error": "日期格式不正确"}), 400
    if not valid_category(category):
        return jsonify({"ok": False, "error": "请选择正确的类别"}), 400
    if not content:
        return jsonify({"ok": False, "error": "内容不能为空"}), 400
    return jsonify({"ok": True, "id": log_store.add_log(log_date, category, content)})


@logs_bp.route("/log/update", methods=["POST"])
def log_update():
    """修改日志。

    表单字段：id（日志 id）、log_date、category、content。
    """
    try:
        log_id = safe_int_id(request.form.get("id"))
    except ValueError:
        return jsonify({"ok": False, "error": "参数不正确"}), 400
    log_date = (request.form.get("log_date") or "").strip()
    category = (request.form.get("category") or "").strip()
    content = (request.form.get("content") or "").strip()
    if not valid_date(log_date):
        return jsonify({"ok": False, "error": "日期格式不正确"}), 400
    if not valid_category(category):
        return jsonify({"ok": False, "error": "请选择正确的类别"}), 400
    if not content:
        return jsonify({"ok": False, "error": "内容不能为空"}), 400
    if not log_store.update_log(log_id, log_date, category, content):
        return jsonify({"ok": False, "error": "日志不存在"}), 404
    return jsonify({"ok": True})


@logs_bp.route("/log/delete", methods=["POST"])
def log_delete():
    """删除日志。表单字段：id。"""
    try:
        log_id = safe_int_id(request.form.get("id"))
    except ValueError:
        return jsonify({"ok": False, "error": "参数不正确"}), 400
    if not log_store.delete_log(log_id):
        return jsonify({"ok": False, "error": "日志不存在"}), 404
    return jsonify({"ok": True})


@logs_bp.route("/log/export")
def log_export():
    """导出全部工作日志为 Excel 表格（.xlsx 下载）。"""
    rows = log_store.all_logs()

    # 创建 Excel 工作簿
    wb = Workbook()
    ws = wb.active
    ws.title = "工作日志"

    # ---------- 表头样式 ----------
    header_font = Font(name="微软雅黑", bold=True, size=11, color="FFFFFF")
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    header_alignment = Alignment(horizontal="center", vertical="center")
    thin_border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin"),
    )

    # ---------- 写表头 ----------
    headers = ["日期", "类别", "内容"]
    for col_idx, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_alignment
        cell.border = thin_border

    # ---------- 写数据行 ----------
    body_font = Font(name="微软雅黑", size=10)
    body_alignment = Alignment(vertical="center", wrap_text=True)

    for row_idx, r in enumerate(rows, 2):
        # 日期
        ws.cell(row=row_idx, column=1, value=r["log_date"])
        # 类别
        ws.cell(row=row_idx, column=2, value=r.get("category", ""))
        # 内容
        ws.cell(row=row_idx, column=3, value=r["content"])
        # 应用数据行样式
        for col_idx in range(1, 4):
            cell = ws.cell(row=row_idx, column=col_idx)
            cell.font = body_font
            cell.alignment = body_alignment
            cell.border = thin_border

    # ---------- 设置列宽 ----------
    ws.column_dimensions["A"].width = 14   # 日期
    ws.column_dimensions["B"].width = 16   # 类别
    ws.column_dimensions["C"].width = 60   # 内容

    # ---------- 冻结首行（表头固定，滚动时可见）----------
    ws.freeze_panes = "A2"

    # ---------- 写入内存缓冲区并返回下载 ----------
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": "attachment; filename=logs.xlsx",
        },
    )

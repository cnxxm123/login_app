"""memos 模块（blueprints 包）
备忘录蓝图：备忘列表页 + 增 / 改 / 删接口。

路由：/memos、/memo/add、/memo/update、/memo/delete。

【本模块做什么】
- /memos        备忘页：卡片网格展示全部备忘（最新在前），支持前端搜索
- /memo/add     新增备忘：表单 title（可空）、content（非空）
- /memo/update  修改备忘：表单 id、title、content
- /memo/delete  删除备忘：表单 id

【与其它模块的分工】
- 备忘读写全部委托给 services/memo_store（纯逻辑层，JSON 文件存储），本模块只处理 HTTP
- 与 logs / todos 蓝图的写法保持一致：POST 接口返回 JSON，页面用 fetch 调用
"""

import json  # 序列化备忘内容给前端编辑弹窗预填

from flask import Blueprint, jsonify, render_template, request
from markupsafe import Markup, escape  # 安全转义备忘正文后插入 <br>

from services import memo_store  # 备忘读写（纯逻辑层）

# 创建"备忘录"蓝图；模板里 url_for('memos.xxx') 的 memos 即此名字
memos_bp = Blueprint("memos", __name__)


@memos_bp.route("/memos")
def index():
    """备忘录页：卡片网格展示全部备忘（最新在前）。"""
    rows = memo_store.all_memos()
    items = []  # [{id, title, content_html, time, edited}]
    for row in rows:
        items.append(
            {
                "id": row["id"],
                "title": row["title"],
                # 正文先整体 HTML 转义（防 XSS），再把换行替换为 <br>，包装成 Markup 直接渲染
                "content_html": Markup(str(escape(row["content"])).replace("\n", "<br>")),
                # 创建时间，卡片底部时间戳：今天只显示 HH:MM，否则显示日期
                "time": row["created_at"].strftime("%Y-%m-%d %H:%M"),
                # 是否被编辑过（updated_at 晚于 created_at），显示小圆点提示
                "edited": row["updated_at"] is not None and row["updated_at"] > row["created_at"],
            }
        )
    # 编辑弹窗预填用：{id: 记录} 的 JSON 映射，直接嵌进页面 <script>。
    # ensure_ascii=False 保留中文；再把 < 转义成 \u003c，防止内容里的 </script> 破坏脚本标签。
    memos_json = json.dumps(
        {str(r["id"]): {"title": r["title"], "content": r["content"]} for r in rows},
        ensure_ascii=False,
    ).replace("<", "\\u003c")
    return render_template("memos.html", items=items, total=len(rows), memos_json=memos_json)


@memos_bp.route("/memo/add", methods=["POST"])
def memo_add():
    """新增备忘。

    表单字段：title（标题，可空）、content（正文，非空）。
    返回 JSON：{ok, id} 或 {ok: False, error}。
    """
    title = (request.form.get("title") or "").strip()
    content = (request.form.get("content") or "").strip()
    if not content:
        return jsonify({"ok": False, "error": "内容不能为空"}), 400
    return jsonify({"ok": True, "id": memo_store.add_memo(title, content)})


@memos_bp.route("/memo/update", methods=["POST"])
def memo_update():
    """修改备忘。

    表单字段：id、title、content（非空）。
    返回 JSON：{ok: True} 或 {ok: False, error}。
    """
    try:
        memo_id = int(request.form.get("id", ""))
    except ValueError:
        return jsonify({"ok": False, "error": "参数错误"}), 400
    title = (request.form.get("title") or "").strip()
    content = (request.form.get("content") or "").strip()
    if not content:
        return jsonify({"ok": False, "error": "内容不能为空"}), 400
    if not memo_store.update_memo(memo_id, title, content):
        return jsonify({"ok": False, "error": "备忘不存在"}), 404
    return jsonify({"ok": True})


@memos_bp.route("/memo/delete", methods=["POST"])
def memo_delete():
    """删除备忘。

    表单字段：id。
    返回 JSON：{ok: True} 或 {ok: False, error}。
    """
    try:
        memo_id = int(request.form.get("id", ""))
    except ValueError:
        return jsonify({"ok": False, "error": "参数错误"}), 400
    if not memo_store.delete_memo(memo_id):
        return jsonify({"ok": False, "error": "备忘不存在"}), 404
    return jsonify({"ok": True})

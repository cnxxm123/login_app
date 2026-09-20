"""memos 模块（blueprints 包）
备忘录蓝图：备忘列表页 + 增 / 改 / 删 / 图片上传与展示接口。

路由：/memos、/memo/add、/memo/update、/memo/delete、/memo/upload_image、/memo/image/<filename>。

【本模块做什么】
- /memos                备忘页：卡片网格展示全部备忘（最新在前），支持前端搜索
- /memo/add             新增备忘：表单 title（可空）、content（非空）、images（可多）
- /memo/update          修改备忘：表单 id、title、content、images
- /memo/delete          删除备忘：表单 id
- /memo/upload_image    上传一张图片，返回图片访问 URL（供编辑弹窗实时预览）
- /memo/image/<filename> 以二进制返回图片（供卡片/弹窗展示）

【与其它模块的分工】
- 备忘读写与图片文件存取全部委托给 services/memo_store（纯逻辑层），本模块只处理 HTTP
- 与 logs / todos 蓝图的写法保持一致：POST 接口返回 JSON，页面用 fetch 调用
"""

import json  # 序列化备忘内容给前端编辑弹窗预填
import os  # 图片路径拼接与扩展名判断

from flask import Blueprint, abort, jsonify, render_template, request, send_file, url_for
from markupsafe import Markup, escape  # 安全转义备忘正文后插入 <br>

from config import IMAGE_EXTENSIONS, IMAGE_MIME, MEMO_IMAGE_DIR  # 图片扩展名白名单 / MIME / 存放目录
from services import memo_store  # 备忘读写 + 图片文件存取（纯逻辑层）
from blueprints._common import safe_int_id  # 统一 id 参数解析

# 创建"备忘录"蓝图；模板里 url_for('memos.xxx') 的 memos 即此名字
memos_bp = Blueprint("memos", __name__)

# 单张图片大小上限（10MB）：避免有人上传超大图拖垮磁盘/内存
MAX_MEMO_IMAGE_BYTES = 10 * 1024 * 1024


@memos_bp.route("/memos")
def index():
    """备忘录页：卡片网格展示全部备忘（最新在前）。支持 ?category=xxx 筛选。"""
    rows = memo_store.all_memos()
    # 收集所有已使用的分类（去重、排序），供前端筛选下拉使用
    categories = sorted({r["category"].strip() for r in rows if r.get("category", "").strip()})
    # URL 查询参数筛选（服务端过滤，也支持客户端切换时前端自行过滤）
    filter_cat = (request.args.get("category") or "").strip()
    items = []  # [{id, title, content_html, category, time, edited, images}]
    for row in rows:
        if filter_cat and row.get("category", "").strip() != filter_cat:
            continue
        items.append(
            {
                "id": row["id"],
                "title": row["title"],
                "category": row.get("category", "").strip(),
                # 正文先整体 HTML 转义（防 XSS），再把换行替换为 <br>，包装成 Markup 直接渲染
                "content_html": Markup(str(escape(row["content"])).replace("\n", "<br>")),
                # 创建时间，卡片底部时间戳：今天只显示 HH:MM，否则显示日期
                "time": row["created_at"].strftime("%Y-%m-%d %H:%M"),
                # 是否被编辑过（updated_at 晚于 created_at），显示小圆点提示
                "edited": row["updated_at"] is not None and row["updated_at"] > row["created_at"],
                # 图片文件名列表，卡片直接渲染缩略图
                "images": row["images"],
            }
        )
    # 编辑弹窗预填用：{id: 记录} 的 JSON 映射，直接嵌进页面 <script>。
    # ensure_ascii=False 保留中文；再把 < 转义成 \u003c，防止内容里的 </script> 破坏脚本标签。
    memos_json = json.dumps(
        {str(r["id"]): {"title": r["title"], "content": r["content"], "category": r.get("category", "").strip(), "images": r["images"]} for r in rows},
        ensure_ascii=False,
    ).replace("<", "\\u003c")
    return render_template("memos.html", items=items, total=len(rows), filter_cat=filter_cat, categories=categories, memos_json=memos_json, image_url=url_for("memos.memo_image", filename="__NAME__"))


@memos_bp.route("/memo/add", methods=["POST"])
def memo_add():
    """新增备忘。

    表单字段：title（标题，可空）、content（正文，非空）、category（分类，可空）、images（可重复的图片文件名）。
    返回 JSON：{ok, id} 或 {ok: False, error}。
    """
    title = (request.form.get("title") or "").strip()
    content = (request.form.get("content") or "").strip()
    category = (request.form.get("category") or "").strip()
    images = request.form.getlist("images")
    if not content:
        return jsonify({"ok": False, "error": "内容不能为空"}), 400
    return jsonify({"ok": True, "id": memo_store.add_memo(title, content, category, images)})


@memos_bp.route("/memo/update", methods=["POST"])
def memo_update():
    """修改备忘。

    表单字段：id、title、content（非空）、category（分类，可空）、images（可重复的图片文件名）。
    返回 JSON：{ok: True} 或 {ok: False, error}。
    """
    try:
        memo_id = safe_int_id(request.form.get("id"))
    except ValueError:
        return jsonify({"ok": False, "error": "参数不正确"}), 400
    title = (request.form.get("title") or "").strip()
    content = (request.form.get("content") or "").strip()
    category = (request.form.get("category") or "").strip()
    images = request.form.getlist("images")
    if not content:
        return jsonify({"ok": False, "error": "内容不能为空"}), 400
    if not memo_store.update_memo(memo_id, title, content, category, images):
        return jsonify({"ok": False, "error": "备忘不存在"}), 404
    return jsonify({"ok": True})


@memos_bp.route("/memo/delete", methods=["POST"])
def memo_delete():
    """删除备忘。

    表单字段：id。
    返回 JSON：{ok: True} 或 {ok: False, error}。
    """
    try:
        memo_id = safe_int_id(request.form.get("id"))
    except ValueError:
        return jsonify({"ok": False, "error": "参数不正确"}), 400
    if not memo_store.delete_memo(memo_id):
        return jsonify({"ok": False, "error": "备忘不存在"}), 404
    return jsonify({"ok": True})


@memos_bp.route("/memo/upload_image", methods=["POST"])
def memo_upload_image():
    """上传一张图片（编辑弹窗内选择图片后立即上传，返回访问 URL 供预览）。

    表单字段：image（文件）。返回 JSON：{ok, filename, url} 或 {ok: False, error}。
    """
    f = request.files.get("image")
    if not f or not f.filename:
        return jsonify({"ok": False, "error": "未选择图片"}), 400
    ext = os.path.splitext(f.filename)[1].lower()
    if ext not in IMAGE_EXTENSIONS:
        return jsonify({"ok": False, "error": "不支持的图片格式"}), 400
    data = f.read()
    if not data:
        return jsonify({"ok": False, "error": "图片内容为空"}), 400
    if len(data) > MAX_MEMO_IMAGE_BYTES:
        return jsonify({"ok": False, "error": "单张图片不能超过 10MB"}), 400
    filename = memo_store.save_image(data, ext)
    return jsonify({"ok": True, "filename": filename, "url": url_for("memos.memo_image", filename=filename)})


@memos_bp.route("/memo/image/<filename>")
def memo_image(filename):
    """以二进制返回备忘图片（卡片缩略图 / 编辑弹窗预览都用它）。

    只接受 store 校验过的合法文件名（uuid.hex + 图片扩展名），防目录穿越。
    """
    name = os.path.basename(filename)
    if not memo_store.valid_image_name(name):
        abort(404)
    path = os.path.join(MEMO_IMAGE_DIR, name)
    if not os.path.isfile(path):
        abort(404)
    ext = os.path.splitext(name)[1].lower()
    return send_file(path, mimetype=IMAGE_MIME.get(ext, "application/octet-stream"))

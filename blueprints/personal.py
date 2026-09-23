"""个人中心蓝图：收藏、最近浏览和阅读/播放进度。"""

import math
import os
from datetime import datetime

from flask import Blueprint, abort, jsonify, render_template, request, url_for

from config import (
    AUDIO_EXTENSIONS,
    EPUB_EXTENSIONS,
    IMAGE_EXTENSIONS,
    OFFICE_EXTENSIONS,
    PDF_EXTENSIONS,
    TEXT_DIR,
    VIDEO_EXTENSIONS,
)
from services.dir_utils import dir_all_images, is_cover_image
from services.path_utils import safe_path
from services.personal_store import (
    delete_favorite,
    delete_progress,
    get_state,
    get_states,
    list_favorites,
    list_history,
    list_progress,
    record_history,
    save_progress,
    set_favorite,
)

personal_bp = Blueprint("personal", __name__)
_PROGRESS_KINDS = {"seconds", "chapter", "page", "scroll"}
_KIND_ICONS = {
    "dir": "📁",
    "gallery": "🖼️",
    "image": "🖼️",
    "video": "🎬",
    "audio": "🎵",
    "epub": "📖",
    "pdf": "📕",
    "office": "📊",
    "text": "📄",
    "file": "📦",
}


def _json_error(message: str, status: int = 400):
    return jsonify({"ok": False, "error": message}), status


def _json_body():
    if not request.is_json:
        return None
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else None


def _kind_for(target: str) -> str:
    if os.path.isdir(target):
        return "dir"
    ext = os.path.splitext(target)[1].lower()
    if ext in VIDEO_EXTENSIONS:
        return "video"
    if ext in AUDIO_EXTENSIONS:
        return "audio"
    if ext in EPUB_EXTENSIONS:
        return "epub"
    if ext in IMAGE_EXTENSIONS:
        return "image"
    if ext in PDF_EXTENSIONS:
        return "pdf"
    if ext in OFFICE_EXTENSIONS:
        return "office"
    if ext in {".md", ".txt", ".py", ".html", ".css", ".js", ".json", ".xml", ".yaml", ".yml"}:
        return "text"
    return "file"


def _stored_key(path) -> str | None:
    """规范化可能已失效的存储 key；仅用于删除，不要求资源仍存在。"""
    if not isinstance(path, str) or not path.strip() or len(path) > 2048 or "\x00" in path:
        return None
    raw = path.strip().replace("\\", "/").strip("/")
    try:
        target = safe_path(raw)
        base = os.path.realpath(TEXT_DIR)
        canonical = os.path.relpath(target, base).replace("\\", "/") if target else ""
    except (OSError, ValueError):
        return None
    if canonical in ("", ".") or canonical.startswith("../"):
        return None
    return canonical


def _resource(path) -> dict | None:
    """验证外部路径并返回从磁盘推导的可信资源信息。"""
    if not isinstance(path, str) or not path.strip() or len(path) > 2048 or "\x00" in path:
        return None
    raw = path.strip().replace("\\", "/").strip("/")
    try:
        target = safe_path(raw)
    except (OSError, ValueError):
        return None
    if target is None or not os.path.exists(target):
        return None
    base = os.path.realpath(TEXT_DIR)
    try:
        canonical = os.path.relpath(target, base).replace("\\", "/")
    except ValueError:
        return None
    if canonical in ("", ".") or canonical.startswith("../"):
        return None
    try:
        stat = os.stat(target)
    except OSError:
        return None
    is_dir = os.path.isdir(target)
    return {
        "path": canonical,
        "target": target,
        "title": os.path.basename(target),
        "kind": _kind_for(target),
        "is_dir": is_dir,
        "size_bytes": None if is_dir else stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
    }


def _item_data(resource: dict) -> dict:
    return {key: resource[key] for key in (
        "path", "title", "kind", "is_dir", "size_bytes", "mtime_ns"
    )}


def _resource_url(resource: dict) -> tuple[str, str]:
    path = resource["path"]
    kind = resource["kind"]
    if resource["is_dir"]:
        images = dir_all_images(path)
        if images and any(not is_cover_image(img["name"]) for img in images):
            return url_for("view.view_gallery", subpath=path), "gallery"
        return url_for("browser.browse", subpath=path), "dir"
    if kind == "epub":
        return url_for("epub.epub_reader", subpath=path), kind
    return url_for("view.view_file", subpath=path), kind


def _progress_from_row(row: dict) -> dict | None:
    kind = row.get("progress_kind")
    if not kind:
        return None
    return {
        "kind": kind,
        "position": row.get("position") or 0,
        "total": row.get("total"),
        "locator": row.get("locator"),
        "completed": bool(row.get("completed")),
        "updated_at": row.get("progress_updated_at"),
    }


def _format_seconds(value) -> str:
    seconds = max(0, int(value or 0))
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours}:{minutes:02d}:{seconds:02d}" if hours else f"{minutes}:{seconds:02d}"


def _progress_label(progress: dict | None) -> tuple[str | None, int | None]:
    if not progress:
        return None, None
    position = float(progress.get("position") or 0)
    total = progress.get("total")
    percent = None
    if total and float(total) > 0:
        percent = max(0, min(100, round(position / float(total) * 100)))
    kind = progress.get("kind")
    if kind == "seconds":
        label = f"播放至 {_format_seconds(position)}"
    elif kind == "chapter":
        label = f"第 {max(1, int(position))} 章"
    elif kind == "page":
        label = f"第 {max(1, int(position))} 页"
    else:
        label = f"已阅读 {percent or 0}%"
    return label, percent


def _decorate(row: dict) -> dict:
    resource = _resource(row.get("path"))
    progress = _progress_from_row(row)
    label, percent = _progress_label(progress)
    item = dict(row)
    item.update({
        "exists": resource is not None,
        "url": None,
        "icon": _KIND_ICONS.get(row.get("kind"), "📄"),
        "progress": progress,
        "progress_label": label,
        "progress_percent": percent,
    })
    if resource:
        item["url"], display_kind = _resource_url(resource)
        # 普通混合目录的图片序列以目录保存进度，继续时直接打开 locator 图片。
        if (
            resource["is_dir"]
            and display_kind == "dir"
            and progress
            and progress.get("kind") == "page"
            and progress.get("locator")
        ):
            locator_resource = _resource(progress["locator"])
            if locator_resource and locator_resource["kind"] == "image":
                item["url"] = url_for("view.view_file", subpath=locator_resource["path"])
        item["kind"] = display_kind
        item["icon"] = _KIND_ICONS.get(display_kind, "📄")
        item["title"] = resource["title"]
    for key in ("favorited_at", "last_viewed_at", "progress_updated_at"):
        if item.get(key):
            item[key + "_text"] = datetime.fromtimestamp(item[key]).strftime("%m-%d %H:%M")
    return item


def get_resource_state(path: str) -> dict:
    """供其他蓝图向模板注入当前资源状态。"""
    resource = _resource(path)
    return get_state(resource["path"]) if resource else {"favorite": False, "progress": None}


def get_resource_states(paths: list[str]) -> dict[str, dict]:
    """供目录页一次性读取卡片状态，返回键保持调用方路径格式。"""
    mapping = {}
    canonical = []
    for path in paths:
        resource = _resource(path)
        if resource:
            mapping[path] = resource["path"]
            canonical.append(resource["path"])
    states = get_states(canonical)
    return {path: states.get(canon, {"favorite": False, "progress": None}) for path, canon in mapping.items()}


def record_resource_history(path: str) -> None:
    """供成功渲染内容页的蓝图记录浏览历史。"""
    resource = _resource(path)
    if resource:
        record_history(_item_data(resource))


@personal_bp.route("/personal")
def index():
    favorites = [_decorate(row) for row in list_favorites()]
    history = [_decorate(row) for row in list_history()]
    progress = [_decorate(row) for row in list_progress()]
    return render_template(
        "personal.html",
        favorites=favorites,
        history=history,
        progress_items=progress,
        stats={
            "favorites": len(favorites),
            "history": len(history),
            "progress": len(progress),
        },
    )


@personal_bp.route("/api/personal/state")
def state():
    resource = _resource(request.args.get("path"))
    if not resource:
        return _json_error("资源不存在或路径无效", 404)
    return jsonify({"ok": True, "path": resource["path"], **get_state(resource["path"])})


@personal_bp.route("/api/personal/state/batch", methods=["POST"])
def state_batch():
    data = _json_body()
    if data is None or not isinstance(data.get("paths"), list):
        return _json_error("需要 JSON paths 数组")
    if len(data["paths"]) > 500:
        return _json_error("单次最多查询 500 个资源")
    resources = [res for path in data["paths"] if (res := _resource(path))]
    states = get_states([res["path"] for res in resources])
    return jsonify({"ok": True, "states": states})


@personal_bp.route("/api/personal/favorite", methods=["PUT"])
def favorite():
    data = _json_body()
    if data is None or not isinstance(data.get("favorite"), bool):
        return _json_error("需要 JSON path 和布尔型 favorite")
    resource = _resource(data.get("path"))
    if not resource:
        # 失效资源仍允许按已存规范 key 取消收藏。
        stale_key = _stored_key(data.get("path"))
        if not data["favorite"] and stale_key:
            delete_favorite(stale_key)
            return jsonify({"ok": True, "path": stale_key, "favorite": False})
        return _json_error("资源不存在或路径无效", 404)
    value = set_favorite(_item_data(resource), data["favorite"])
    return jsonify({"ok": True, "path": resource["path"], "favorite": value})


@personal_bp.route("/api/personal/history", methods=["POST"])
def history():
    data = _json_body()
    resource = _resource(data.get("path") if data else None)
    if not resource:
        return _json_error("资源不存在或路径无效", 404)
    record_history(_item_data(resource))
    return jsonify({"ok": True, "path": resource["path"]})


@personal_bp.route("/api/personal/progress", methods=["PUT", "DELETE"])
def progress():
    data = _json_body()
    if data is None:
        return _json_error("需要 JSON 请求体")
    resource = _resource(data.get("path"))
    if request.method == "DELETE":
        key = resource["path"] if resource else _stored_key(data.get("path"))
        if not key:
            return _json_error("路径无效", 400)
        delete_progress(key)
        return jsonify({"ok": True, "path": key, "progress": None})
    if not resource:
        return _json_error("资源不存在或路径无效", 404)

    kind = data.get("kind")
    if kind not in _PROGRESS_KINDS:
        return _json_error("进度类型必须是 seconds、chapter、page 或 scroll")
    try:
        position = float(data.get("position", 0))
        total_value = data.get("total")
        total = float(total_value) if total_value is not None else None
    except (TypeError, ValueError):
        return _json_error("position 或 total 格式无效")
    if not math.isfinite(position) or position < 0:
        return _json_error("position 必须是非负有限数值")
    if total is not None and (not math.isfinite(total) or total <= 0):
        return _json_error("total 必须是正有限数值")
    if total is not None:
        position = min(position, total)
    locator = data.get("locator")
    if locator is not None and (not isinstance(locator, str) or len(locator) > 1000):
        return _json_error("locator 格式无效")
    completed = data.get("completed", False)
    if not isinstance(completed, bool):
        return _json_error("completed 必须是布尔值")
    save_progress(
        _item_data(resource), kind, position, total, locator, completed
    )
    return jsonify({
        "ok": True,
        "path": resource["path"],
        "progress": get_state(resource["path"])["progress"],
    })

"""todo_store 模块（services 包）
待办事项存储（纯逻辑层，不依赖 Flask、不处理 HTTP）。

待办以 JSON 文件形式存放在项目根目录下的"待办事项"文件夹里：
    {BASE_DIR}/待办事项/todos.json
与"工作日志"（logs.json）同一套设计：可直接查看 / 备份；首次写入时自动创建。

职责：围绕"待办事项"提供增删改查：
- add_todo()      新增一条待办，返回自增 id
- all_todos()     按 sort_order / id 倒序列出全部待办
- get_todo()      按 id 取单条待办（编辑弹窗预填用）
- update_todo()   修改某条的日期/内容/截止日期
- toggle_done()   切换某条的完成 / 未完成状态
- delete_todo()   按 id 删除
- reorder_todos() 批量更新 sort_order（拖拽排序后保存新顺序）
"""

import json
import os
import threading
from datetime import datetime

from config import TODO_FILE

_lock = threading.Lock()

_TIME_FMT = "%Y-%m-%d %H:%M:%S"


def _load() -> dict:
    if not os.path.exists(TODO_FILE):
        return {"next_id": 1, "todos": []}
    try:
        with open(TODO_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return {"next_id": 1, "todos": []}
    if not isinstance(data, dict) or not isinstance(data.get("todos"), list):
        return {"next_id": 1, "todos": []}
    data.setdefault(
        "next_id", max((rec["id"] for rec in data["todos"]), default=0) + 1
    )
    return data


def _save(data: dict) -> None:
    os.makedirs(os.path.dirname(TODO_FILE), exist_ok=True)
    tmp = TODO_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, TODO_FILE)


def _to_row(rec: dict) -> dict:
    """把存储记录转成统一字典。"""
    return {
        "id": rec["id"],
        "todo_date": rec["todo_date"],
        "content": rec["content"],
        "done": bool(rec.get("done", False)),
        "due_date": rec.get("due_date") or None,  # 截止日期（可选，格式 YYYY-MM-DD）
        "sort_order": rec.get("sort_order", 0),  # 拖拽排序用，同组内数值越小越靠前
        "created_at": datetime.strptime(rec["created_at"], _TIME_FMT),
        "updated_at": (
            datetime.strptime(rec["updated_at"], _TIME_FMT)
            if rec["updated_at"]
            else None
        ),
    }


def add_todo(todo_date: str, content: str, due_date: str = "") -> int:
    """新增一条待办，返回新记录 id。due_date 为截止日期（可选）。"""
    with _lock:
        data = _load()
        new_id = data["next_id"]
        data["todos"].append(
            {
                "id": new_id,
                "todo_date": todo_date,
                "content": content,
                "done": False,
                "due_date": due_date or None,
                "sort_order": 0,
                "created_at": datetime.now().strftime(_TIME_FMT),
                "updated_at": None,
            }
        )
        data["next_id"] = new_id + 1
        _save(data)
        return new_id


def all_todos() -> list:
    """按日期倒序返回全部待办（同一天按 sort_order 升序 → 拖拽越靠前数值越小越先显示，id 降序兜底）。"""
    with _lock:
        data = _load()
    rows = [_to_row(r) for r in data["todos"]]
    rows.sort(key=lambda r: (r["todo_date"], r["sort_order"], -r["id"]), reverse=False)
    # 日期降序：日期大的在前，同日期内 sort_order 升序
    rows.sort(key=lambda r: r["todo_date"], reverse=True)
    # 最终：日期降序 → 同日期 sort_order 升序 → id 降序兜底
    from functools import cmp_to_key
    def _cmp(a, b):
        # 日期降序
        if a["todo_date"] != b["todo_date"]:
            return -1 if a["todo_date"] > b["todo_date"] else 1
        # sort_order 升序（小在前）
        if a["sort_order"] != b["sort_order"]:
            return -1 if a["sort_order"] < b["sort_order"] else 1
        # id 降序兜底
        return -1 if a["id"] > b["id"] else 1
    rows.sort(key=cmp_to_key(_cmp))
    return rows


def get_todo(todo_id: int):
    with _lock:
        data = _load()
    for rec in data["todos"]:
        if rec["id"] == todo_id:
            return _to_row(rec)
    return None


def update_todo(todo_id: int, todo_date: str, content: str, due_date: str = "") -> bool:
    """修改某条待办的日期/内容/截止日期；返回是否真的更新到。"""
    with _lock:
        data = _load()
        for rec in data["todos"]:
            if rec["id"] == todo_id:
                rec["todo_date"] = todo_date
                rec["content"] = content
                rec["due_date"] = due_date or None
                rec["updated_at"] = datetime.now().strftime(_TIME_FMT)
                _save(data)
                return True
    return False


def toggle_done(todo_id: int) -> bool:
    with _lock:
        data = _load()
        for rec in data["todos"]:
            if rec["id"] == todo_id:
                rec["done"] = not rec["done"]
                rec["updated_at"] = datetime.now().strftime(_TIME_FMT)
                _save(data)
                return True
    return False


def delete_todo(todo_id: int) -> bool:
    with _lock:
        data = _load()
        new_todos = [rec for rec in data["todos"] if rec["id"] != todo_id]
        if len(new_todos) == len(data["todos"]):
            return False
        data["todos"] = new_todos
        _save(data)
        return True


def reorder_todos(orders: list) -> bool:
    """批量更新 sort_order。orders = [{id, sort_order}, ...]。"""
    if not orders:
        return False
    with _lock:
        data = _load()
        id_map = {rec["id"]: rec for rec in data["todos"]}
        for item in orders:
            rec = id_map.get(item["id"])
            if rec is not None:
                rec["sort_order"] = item["sort_order"]
        _save(data)
        return True

"""todo_store 模块（services 包）
待办事项存储（纯逻辑层，不依赖 Flask、不处理 HTTP）。

待办以 JSON 文件形式存放在项目根目录下的"待办事项"文件夹里：
    {BASE_DIR}/待办事项/todos.json
与"工作日志"（logs.json）同一套设计：可直接查看 / 备份；首次写入时自动创建。

职责：围绕"待办事项"提供增删改查：
- add_todo()      新增一条待办，返回自增 id
- all_todos()     按日期倒序列出全部待办（id 倒序 → 同一天内最新在前）
- get_todo()      按 id 取单条待办（编辑弹窗预填用）
- update_todo()   修改某条的日期/类别/内容
- toggle_done()   切换某条的完成 / 未完成状态
- delete_todo()   按 id 删除

与 log_store 的拆分思路一致：蓝图（todos.py）只做参数解析与渲染，
存储细节全部收敛到这里，方便以后换数据库而不动路由层。
"""

import json  # JSON 序列化：待办库单文件存储
import os  # 判断文件是否存在、建目录
import threading  # 读写文件互斥，避免并发新增/编辑时互相覆盖
from datetime import datetime  # 生成创建/修改时间

from config import TODO_FILE  # 待办存储文件（位于项目根目录下的"待办事项"文件夹）

_lock = threading.Lock()  # 所有读写都拿同一把锁，保证进程内串行

_TIME_FMT = "%Y-%m-%d %H:%M:%S"  # 存储的时间格式


def _load() -> dict:
    """读取并解析待办库；文件缺失/损坏时返回空库。"""
    if not os.path.exists(TODO_FILE):
        return {"next_id": 1, "todos": []}
    try:
        with open(TODO_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):  # 文件被改坏等异常情况：按空库处理
        return {"next_id": 1, "todos": []}
    if not isinstance(data, dict) or not isinstance(data.get("todos"), list):
        return {"next_id": 1, "todos": []}
    data.setdefault(
        "next_id", max((rec["id"] for rec in data["todos"]), default=0) + 1
    )
    return data


def _save(data: dict) -> None:
    """把整个待办库写回文件（先写临时文件再原子替换，避免写一半损坏）。"""
    os.makedirs(os.path.dirname(TODO_FILE), exist_ok=True)
    tmp = TODO_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, TODO_FILE)


def _to_row(rec: dict) -> dict:
    """把存储记录转成统一字典：日期为字符串、时间为 datetime（与模板/蓝图约定一致）。

    done 字段做布尔归一：老数据可能存的是 1/0 或 true/false，统一成 bool。
    """
    return {
        "id": rec["id"],
        "todo_date": rec["todo_date"],
        "category": rec.get("category", ""),  # 类别（上架游戏 / 更新游戏 / 问题处理）
        "content": rec["content"],
        "done": bool(rec.get("done", False)),  # 完成状态：False 未完成 / True 已完成
        "created_at": datetime.strptime(rec["created_at"], _TIME_FMT),
        "updated_at": (
            datetime.strptime(rec["updated_at"], _TIME_FMT)
            if rec["updated_at"]
            else None
        ),
    }


def add_todo(todo_date: str, category: str, content: str) -> int:
    """新增一条待办，返回新记录 id。"""
    with _lock:
        data = _load()
        new_id = data["next_id"]
        data["todos"].append(
            {
                "id": new_id,
                "todo_date": todo_date,
                "category": category,
                "content": content,
                "done": False,  # 新待办默认未完成
                "created_at": datetime.now().strftime(_TIME_FMT),
                "updated_at": None,
            }
        )
        data["next_id"] = new_id + 1
        _save(data)
        return new_id


def all_todos() -> list:
    """按日期倒序返回全部待办（同一天按 id 倒序，最新在前）。"""
    with _lock:
        data = _load()
    rows = [_to_row(r) for r in data["todos"]]
    rows.sort(key=lambda r: (r["todo_date"], r["id"]), reverse=True)
    return rows


def get_todo(todo_id: int):
    """按 id 取单条待办；不存在返回 None。"""
    with _lock:
        data = _load()
    for rec in data["todos"]:
        if rec["id"] == todo_id:
            return _to_row(rec)
    return None


def update_todo(todo_id: int, todo_date: str, category: str, content: str) -> bool:
    """修改某条待办的日期/类别/内容；返回是否真的更新到（id 不存在返回 False）。"""
    with _lock:
        data = _load()
        for rec in data["todos"]:
            if rec["id"] == todo_id:
                rec["todo_date"] = todo_date
                rec["category"] = category
                rec["content"] = content
                rec["updated_at"] = datetime.now().strftime(_TIME_FMT)
                _save(data)
                return True
    return False


def toggle_done(todo_id: int) -> bool:
    """切换某条待办的完成 / 未完成状态；返回是否真的找到（id 不存在返回 False）。"""
    with _lock:
        data = _load()
        for rec in data["todos"]:
            if rec["id"] == todo_id:
                rec["done"] = not rec["done"]  # 取反：完成 ↔ 未完成
                rec["updated_at"] = datetime.now().strftime(_TIME_FMT)
                _save(data)
                return True
    return False


def delete_todo(todo_id: int) -> bool:
    """按 id 删除待办；返回是否真的删到（id 不存在返回 False）。"""
    with _lock:
        data = _load()
        new_todos = [rec for rec in data["todos"] if rec["id"] != todo_id]
        if len(new_todos) == len(data["todos"]):
            return False
        data["todos"] = new_todos
        _save(data)
        return True

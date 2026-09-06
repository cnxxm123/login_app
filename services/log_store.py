"""log_store 模块（services 包）
工作日志存储（纯逻辑层，不依赖 Flask、不处理 HTTP）。

日志以 JSON 文件形式存放在项目文档目录（TEXT_DIR）下的"工作日志"文件夹里：
    {TEXT_DIR}/工作日志/logs.json
与浏览内容同目录，可直接查看 / 备份；文件或文件夹不存在时首次写入会自动创建。

职责：围绕"工作日志"提供增删改查：
- add_log()       新增一条日志，返回自增 id
- all_logs()      按日期倒序列出全部日志（id 倒序 → 同一天内最新在前）
- get_log()       按 id 取单条日志（编辑弹窗预填用）
- update_log()    修改某条的日期/内容
- delete_log()    按 id 删除

与 tags/tag_store 的拆分思路一致：蓝图（logs.py）只做参数解析与渲染，
存储细节全部收敛到这里。
"""

import json  # JSON 序列化：日志库单文件存储
import os  # 判断文件是否存在、建目录
import threading  # 读写文件互斥，避免并发新增/编辑时互相覆盖
from datetime import datetime  # 生成创建/修改时间

from config import LOG_FILE  # 日志存储文件（位于项目文档目录下的"工作日志"文件夹）

_lock = threading.Lock()  # 所有读写都拿同一把锁，保证进程内串行

_TIME_FMT = "%Y-%m-%d %H:%M:%S"  # 存储的时间格式


def _load() -> dict:
    """读取并解析日志库；文件缺失/损坏时返回空库。"""
    if not os.path.exists(LOG_FILE):
        return {"next_id": 1, "logs": []}
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):  # 文件被改坏等异常情况：按空库处理
        return {"next_id": 1, "logs": []}
    if not isinstance(data, dict) or not isinstance(data.get("logs"), list):
        return {"next_id": 1, "logs": []}
    data.setdefault(
        "next_id", max((rec["id"] for rec in data["logs"]), default=0) + 1
    )
    return data


def _save(data: dict) -> None:
    """把整个日志库写回文件（先写临时文件再原子替换，避免写一半损坏）。"""
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    tmp = LOG_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, LOG_FILE)


def _to_row(rec: dict) -> dict:
    """把存储记录转成统一字典：日期为字符串、时间为 datetime（与模板/蓝图约定一致）。"""
    return {
        "id": rec["id"],
        "log_date": rec["log_date"],
        "content": rec["content"],
        "created_at": datetime.strptime(rec["created_at"], _TIME_FMT),
        "updated_at": (
            datetime.strptime(rec["updated_at"], _TIME_FMT)
            if rec["updated_at"]
            else None
        ),
    }


def add_log(log_date: str, content: str) -> int:
    """新增一条日志，返回新记录 id。"""
    with _lock:
        data = _load()
        new_id = data["next_id"]
        data["logs"].append(
            {
                "id": new_id,
                "log_date": log_date,
                "content": content,
                "created_at": datetime.now().strftime(_TIME_FMT),
                "updated_at": None,
            }
        )
        data["next_id"] = new_id + 1
        _save(data)
        return new_id


def all_logs() -> list:
    """按日期倒序返回全部日志（同一天按 id 倒序，最新在前）。"""
    with _lock:
        data = _load()
    rows = [_to_row(r) for r in data["logs"]]
    rows.sort(key=lambda r: (r["log_date"], r["id"]), reverse=True)
    return rows


def get_log(log_id: int):
    """按 id 取单条日志；不存在返回 None。"""
    with _lock:
        data = _load()
    for rec in data["logs"]:
        if rec["id"] == log_id:
            return _to_row(rec)
    return None


def update_log(log_id: int, log_date: str, content: str) -> bool:
    """修改某条日志的日期与内容；返回是否真的更新到（id 不存在返回 False）。"""
    with _lock:
        data = _load()
        for rec in data["logs"]:
            if rec["id"] == log_id:
                rec["log_date"] = log_date
                rec["content"] = content
                rec["updated_at"] = datetime.now().strftime(_TIME_FMT)
                _save(data)
                return True
    return False


def delete_log(log_id: int) -> bool:
    """按 id 删除日志；返回是否真的删到（id 不存在返回 False）。"""
    with _lock:
        data = _load()
        new_logs = [rec for rec in data["logs"] if rec["id"] != log_id]
        if len(new_logs) == len(data["logs"]):
            return False
        data["logs"] = new_logs
        _save(data)
        return True

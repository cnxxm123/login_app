"""个人中心 SQLite 存储层。

以相对内容根目录的路径作为资源标识，统一保存收藏、浏览历史和阅读/播放进度。
本模块不依赖 Flask，也不访问内容文件；路径验证和资源类型推导由蓝图层负责。
"""

import os
import sqlite3
import time
from contextlib import contextmanager

from config import PERSONAL_DB_PATH

_PROGRESS_KINDS = {"seconds", "chapter", "page", "scroll"}


@contextmanager
def _connection():
    """创建一次短连接，适配 Flask 多线程请求。"""
    conn = sqlite3.connect(PERSONAL_DB_PATH, timeout=5)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 5000")
    try:
        yield conn
    finally:
        conn.close()


def init_personal_db() -> None:
    """幂等创建个人中心数据库和索引。"""
    os.makedirs(os.path.dirname(PERSONAL_DB_PATH), exist_ok=True)
    with _connection() as conn:
        conn.execute("PRAGMA journal_mode = WAL")
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS items (
                path TEXT PRIMARY KEY,
                kind TEXT NOT NULL,
                title TEXT NOT NULL,
                is_dir INTEGER NOT NULL DEFAULT 0 CHECK (is_dir IN (0, 1)),
                size_bytes INTEGER,
                mtime_ns INTEGER,
                created_at INTEGER NOT NULL,
                updated_at INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS favorites (
                path TEXT PRIMARY KEY REFERENCES items(path) ON DELETE CASCADE,
                favorited_at INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS history (
                path TEXT PRIMARY KEY REFERENCES items(path) ON DELETE CASCADE,
                last_viewed_at INTEGER NOT NULL,
                view_count INTEGER NOT NULL DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS progress (
                path TEXT PRIMARY KEY REFERENCES items(path) ON DELETE CASCADE,
                progress_kind TEXT NOT NULL CHECK (
                    progress_kind IN ('seconds', 'chapter', 'page', 'scroll')
                ),
                position REAL NOT NULL DEFAULT 0,
                total REAL,
                locator TEXT,
                completed INTEGER NOT NULL DEFAULT 0 CHECK (completed IN (0, 1)),
                updated_at INTEGER NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_favorites_time
                ON favorites(favorited_at DESC);
            CREATE INDEX IF NOT EXISTS idx_history_time
                ON history(last_viewed_at DESC);
            CREATE INDEX IF NOT EXISTS idx_progress_time
                ON progress(updated_at DESC);
            PRAGMA user_version = 1;
            """
        )
        conn.commit()


def _upsert_item(conn: sqlite3.Connection, item: dict, now: int) -> None:
    conn.execute(
        """
        INSERT INTO items
            (path, kind, title, is_dir, size_bytes, mtime_ns, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(path) DO UPDATE SET
            kind = excluded.kind,
            title = excluded.title,
            is_dir = excluded.is_dir,
            size_bytes = excluded.size_bytes,
            mtime_ns = excluded.mtime_ns,
            updated_at = excluded.updated_at
        """,
        (
            item["path"],
            item["kind"],
            item["title"],
            1 if item.get("is_dir") else 0,
            item.get("size_bytes"),
            item.get("mtime_ns"),
            now,
            now,
        ),
    )


def set_favorite(item: dict, favorite: bool) -> bool:
    """幂等设置收藏状态并返回最终状态。"""
    now = int(time.time())
    with _connection() as conn, conn:
        _upsert_item(conn, item, now)
        if favorite:
            conn.execute(
                """
                INSERT INTO favorites(path, favorited_at) VALUES (?, ?)
                ON CONFLICT(path) DO UPDATE SET favorited_at = excluded.favorited_at
                """,
                (item["path"], now),
            )
        else:
            conn.execute("DELETE FROM favorites WHERE path = ?", (item["path"],))
    return favorite


def delete_favorite(path: str) -> None:
    """按已存路径删除收藏；资源已经移动或删除时仍可清理。"""
    with _connection() as conn, conn:
        conn.execute("DELETE FROM favorites WHERE path = ?", (path,))


def record_history(item: dict) -> None:
    """记录一次真实页面访问，同一路径累计次数并更新时间。"""
    now = int(time.time())
    with _connection() as conn, conn:
        _upsert_item(conn, item, now)
        conn.execute(
            """
            INSERT INTO history(path, last_viewed_at, view_count) VALUES (?, ?, 1)
            ON CONFLICT(path) DO UPDATE SET
                last_viewed_at = excluded.last_viewed_at,
                view_count = history.view_count + 1
            """,
            (item["path"], now),
        )


def save_progress(
    item: dict,
    progress_kind: str,
    position: float,
    total: float | None = None,
    locator: str | None = None,
    completed: bool = False,
) -> None:
    """保存阅读或播放进度。"""
    if progress_kind not in _PROGRESS_KINDS:
        raise ValueError("不支持的进度类型")
    now = int(time.time())
    with _connection() as conn, conn:
        _upsert_item(conn, item, now)
        conn.execute(
            """
            INSERT INTO progress
                (path, progress_kind, position, total, locator, completed, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(path) DO UPDATE SET
                progress_kind = excluded.progress_kind,
                position = excluded.position,
                total = excluded.total,
                locator = excluded.locator,
                completed = excluded.completed,
                updated_at = excluded.updated_at
            """,
            (
                item["path"],
                progress_kind,
                position,
                total,
                locator,
                1 if completed else 0,
                now,
            ),
        )


def delete_progress(path: str) -> None:
    with _connection() as conn, conn:
        conn.execute("DELETE FROM progress WHERE path = ?", (path,))


def get_state(path: str) -> dict:
    """返回单个资源的收藏和进度状态。"""
    with _connection() as conn:
        row = conn.execute(
            """
            SELECT
                CASE WHEN f.path IS NULL THEN 0 ELSE 1 END AS favorite,
                p.progress_kind, p.position, p.total, p.locator,
                p.completed, p.updated_at
            FROM items i
            LEFT JOIN favorites f ON f.path = i.path
            LEFT JOIN progress p ON p.path = i.path
            WHERE i.path = ?
            """,
            (path,),
        ).fetchone()
    if row is None:
        return {"favorite": False, "progress": None}
    progress = None
    if row["progress_kind"]:
        progress = {
            "kind": row["progress_kind"],
            "position": row["position"],
            "total": row["total"],
            "locator": row["locator"],
            "completed": bool(row["completed"]),
            "updated_at": row["updated_at"],
        }
    return {"favorite": bool(row["favorite"]), "progress": progress}


def get_states(paths: list[str]) -> dict[str, dict]:
    """批量读取状态；未入库路径也会返回默认状态。"""
    unique = list(dict.fromkeys(paths[:500]))
    states = {path: {"favorite": False, "progress": None} for path in unique}
    if not unique:
        return states
    marks = ",".join("?" for _ in unique)
    with _connection() as conn:
        rows = conn.execute(
            f"""
            SELECT i.path,
                   CASE WHEN f.path IS NULL THEN 0 ELSE 1 END AS favorite,
                   p.progress_kind, p.position, p.total, p.locator,
                   p.completed, p.updated_at
            FROM items i
            LEFT JOIN favorites f ON f.path = i.path
            LEFT JOIN progress p ON p.path = i.path
            WHERE i.path IN ({marks})
            """,
            unique,
        ).fetchall()
    for row in rows:
        progress = None
        if row["progress_kind"]:
            progress = {
                "kind": row["progress_kind"],
                "position": row["position"],
                "total": row["total"],
                "locator": row["locator"],
                "completed": bool(row["completed"]),
                "updated_at": row["updated_at"],
            }
        states[row["path"]] = {
            "favorite": bool(row["favorite"]),
            "progress": progress,
        }
    return states


def _list_rows(query: str, limit: int) -> list[dict]:
    limit = max(1, min(int(limit), 200))
    with _connection() as conn:
        return [dict(row) for row in conn.execute(query, (limit,)).fetchall()]


def list_favorites(limit: int = 60) -> list[dict]:
    return _list_rows(
        """
        SELECT i.*, f.favorited_at,
               p.progress_kind, p.position, p.total, p.locator,
               p.completed, p.updated_at AS progress_updated_at
        FROM favorites f
        JOIN items i ON i.path = f.path
        LEFT JOIN progress p ON p.path = i.path
        ORDER BY f.favorited_at DESC LIMIT ?
        """,
        limit,
    )


def list_history(limit: int = 60) -> list[dict]:
    return _list_rows(
        """
        SELECT i.*, h.last_viewed_at, h.view_count,
               CASE WHEN f.path IS NULL THEN 0 ELSE 1 END AS favorite,
               p.progress_kind, p.position, p.total, p.locator,
               p.completed, p.updated_at AS progress_updated_at
        FROM history h
        JOIN items i ON i.path = h.path
        LEFT JOIN favorites f ON f.path = i.path
        LEFT JOIN progress p ON p.path = i.path
        ORDER BY h.last_viewed_at DESC LIMIT ?
        """,
        limit,
    )


def list_progress(limit: int = 60) -> list[dict]:
    return _list_rows(
        """
        SELECT i.*, p.progress_kind, p.position, p.total, p.locator,
               p.completed, p.updated_at AS progress_updated_at,
               CASE WHEN f.path IS NULL THEN 0 ELSE 1 END AS favorite
        FROM progress p
        JOIN items i ON i.path = p.path
        LEFT JOIN favorites f ON f.path = i.path
        WHERE p.completed = 0 AND p.position > 0
        ORDER BY p.updated_at DESC LIMIT ?
        """,
        limit,
    )

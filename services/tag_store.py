"""tag_store 模块（services 包）
文件标签存储（纯逻辑层，只负责数据库读写，不依赖 Flask、不处理 HTTP）。

职责：围绕"标签"提供增删查改：
- set_tags()          替换某文件/目录的全部标签（先清后插，事务保证原子）
- get_tags()          取单个路径的标签列表
- tags_for_paths()    批量取多个路径的标签（浏览页卡片一次性查完）
- remove_tag()        移除某个路径下的某个标签
- all_tags()          列出全部标签及各自的文件数（标签管理页用）
- paths_by_tag()      按标签返回文件路径列表（按打标时间倒序）

【为什么单独一个模块？】
与 token_generator/token_store 的拆分思路一致：
数据库读写与路由层解耦，蓝图（tags.py）只负责解析参数、拼 URL、渲染页面，
这里只做"和数据库打交道"这一件事。
"""

import hashlib  # 计算路径 md5（唯一键，避免长路径索引超长）

from db import get_connection


def _md5(path: str) -> str:
    """返回路径的 md5（32 位小写十六进制），用作 file_tags 的唯一键。"""
    return hashlib.md5(path.encode("utf-8")).hexdigest()


def _normalize(tags) -> list:
    """清洗标签列表：去空白、去空串、去重、去重名，单条最长 50 字。"""
    seen, out = set(), []
    for raw in tags or []:
        name = str(raw).strip()
        if not name or name in seen:
            continue
        seen.add(name)
        out.append(name[:50])  # 超长截断，避免写入超长标签
    return out


def _tag_id(cur, name: str) -> int:
    """按名称取标签 id；不存在则创建后返回（INSERT IGNORE + 回查）。"""
    cur.execute("SELECT id FROM tags WHERE name = %s", (name,))
    row = cur.fetchone()
    if row:
        return row[0]
    # 并发下可能同时插入同名标签，用 INSERT IGNORE 让重复插入静默跳过
    cur.execute("INSERT IGNORE INTO tags (name) VALUES (%s)", (name,))
    cur.execute("SELECT id FROM tags WHERE name = %s", (name,))
    return cur.fetchone()[0]


def set_tags(path: str, tags) -> bool:
    """把 path 的标签整体替换为 tags（列表/逗号分隔字符串均可）。

    先删除该路径现有全部标签，再逐条插入新标签；同一事务内完成，
    中途出错则整体回滚，不会出现"删了一半"的中间状态。
    返回是否成功（空标签列表 = 清空标签，同样视为成功）。
    """
    names = _normalize(tags.split(",") if isinstance(tags, str) else tags)
    path_md5 = _md5(path)
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # 先删除该路径现有标签（与 tags 表的外键无关，直接删关联行）
            cur.execute("DELETE FROM file_tags WHERE path_md5 = %s", (path_md5,))
            for name in names:
                tid = _tag_id(cur, name)
                # 唯一键 (tag_id, path_md5) 已保证不会重复插入
                cur.execute(
                    "INSERT IGNORE INTO file_tags (tag_id, path, path_md5) VALUES (%s, %s, %s)",
                    (tid, path, path_md5),
                )
        conn.commit()
        return True
    except Exception:
        conn.rollback()  # 出错回滚，保持数据一致
        return False
    finally:
        conn.close()


def get_tags(path: str) -> list:
    """返回某个路径的标签名列表（按标签名排序）。"""
    path_md5 = _md5(path)
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT t.name FROM tags t
                JOIN file_tags ft ON ft.tag_id = t.id
                WHERE ft.path_md5 = %s ORDER BY t.name
                """,
                (path_md5,),
            )
            return [row[0] for row in cur.fetchall()]
    finally:
        conn.close()


def tags_for_paths(paths: list) -> dict:
    """批量取多个路径的标签：返回 {path: [标签名, ...]}。

    浏览页卡片需要给每个文件/目录显示标签，若逐个查数据库会产生大量小查询；
    这里用一条 SQL 把指定路径全部查出，再在内存里分组，一次搞定。
    """
    if not paths:
        return {}
    md5s = [_md5(p) for p in paths]
    placeholders = ",".join(["%s"] * len(md5s))
    # md5 → 原路径 的映射（SQL 结果只有 md5，回填原路径用）
    md5_to_path = {m: p for m, p in zip(md5s, paths)}
    result = {p: [] for p in paths}
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT ft.path_md5, t.name FROM tags t
                JOIN file_tags ft ON ft.tag_id = t.id
                WHERE ft.path_md5 IN ({placeholders})
                ORDER BY t.name
                """,
                md5s,
            )
            for path_md5, name in cur.fetchall():
                original = md5_to_path.get(path_md5)
                if original is not None:
                    result[original].append(name)
    finally:
        conn.close()
    return result


def remove_tag(path: str, tag: str) -> bool:
    """移除某个路径下的某个标签；路径/标签不存在时静默返回 False。"""
    path_md5 = _md5(path)
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                DELETE ft FROM file_tags ft
                JOIN tags t ON t.id = ft.tag_id
                WHERE ft.path_md5 = %s AND t.name = %s
                """,
                (path_md5, tag),
            )
            deleted = cur.rowcount
        conn.commit()
        return deleted > 0
    except Exception:
        conn.rollback()
        return False
    finally:
        conn.close()


def delete_tag(name: str) -> bool:
    """删除整个标签：先清掉所有文件上的该标签，再删除标签本身。

    同一事务内完成；标签不存在时返回 False，不影响任何数据。
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM tags WHERE name = %s", (name,))
            row = cur.fetchone()
            if row is None:
                return False
            cur.execute("DELETE FROM file_tags WHERE tag_id = %s", (row[0],))
            cur.execute("DELETE FROM tags WHERE id = %s", (row[0],))
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        return False
    finally:
        conn.close()


def all_tags() -> list:
    """返回全部标签及使用次数：[{"name", "count"}, ...]，按次数降序。"""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT t.name, COUNT(ft.id) AS cnt
                FROM tags t
                LEFT JOIN file_tags ft ON ft.tag_id = t.id
                GROUP BY t.id, t.name
                ORDER BY cnt DESC, t.name
                """
            )
            return [{"name": r[0], "count": r[1]} for r in cur.fetchall()]
    finally:
        conn.close()


def paths_by_tag(tag: str) -> list:
    """按标签返回文件路径列表（按打标时间倒序，最新打的排最前）。"""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT ft.path FROM tags t
                JOIN file_tags ft ON ft.tag_id = t.id
                WHERE t.name = %s
                ORDER BY ft.created_at DESC, ft.id DESC
                """,
                (tag,),
            )
            return [r[0] for r in cur.fetchall()]
    finally:
        conn.close()

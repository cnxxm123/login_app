"""
db 模块
负责数据库连接与初始化：
- 自动创建 login_db 数据库

【说明】
原标签功能（tags / file_tags 表）已彻底移除，本模块只负责建库。
"""

import os  # 读取环境变量 DB_USER / DB_PASSWORD，便于跨机器部署免改代码
import pymysql  # Python 连接 MySQL 的驱动库

# 数据库连接配置（不含 database 与 password，便于先建库）
DB_CONFIG = {
    "host": "localhost",   # MySQL 跑在本机
    "user": os.environ.get("DB_USER", "root"),  # 用户名（可用环境变量 DB_USER 覆盖）
    "charset": "utf8mb4",  # utf8mb4 字符集：支持中文和 emoji
}

DB_NAME = "login_db"  # 项目专用数据库名

# 多台电脑本机 MySQL 的 root 密码不同（如原电脑 123123、这台 1234）。
# 未设置环境变量 DB_PASSWORD 时，按顺序尝试这些常见值，连上即缓存，
# 保证同一份代码换电脑也能直接启动；也可用 DB_PASSWORD 显式指定。
_DB_PASSWORD_CANDIDATES = ["1234", "123123", "", "root", "123456"]
_DB_PASSWORD_CACHE = None  # 探测成功的密码（None 表示还没探测过）


def _resolve_db_password() -> str:
    """返回本机可用的 MySQL 密码：环境变量优先，否则自动探测并缓存。"""
    global _DB_PASSWORD_CACHE
    if _DB_PASSWORD_CACHE is not None:
        return _DB_PASSWORD_CACHE
    env_pw = os.environ.get("DB_PASSWORD")
    candidates = [env_pw] if env_pw else _DB_PASSWORD_CANDIDATES
    for pw in candidates:
        try:
            conn = pymysql.connect(
                host=DB_CONFIG["host"], user=DB_CONFIG["user"], password=pw,
                charset=DB_CONFIG["charset"], connect_timeout=3,
            )
            conn.close()
            _DB_PASSWORD_CACHE = pw
            return pw
        except pymysql.MySQLError:
            continue
    raise RuntimeError(
        "无法连接本机 MySQL：请确认 MySQL 服务已启动，"
        "或用环境变量 DB_PASSWORD 指定 root 密码"
    )


def init_db():
    """建库（幂等，可重复执行）。

    "幂等" = 重复执行结果一样，不会重复建库，
    所以每次启动调用都安全。
    """
    # 连接 MySQL 服务（不带 database），创建 login_db 数据库
    conn = pymysql.connect(**{**DB_CONFIG, "password": _resolve_db_password()})
    try:
        with conn.cursor() as cur:
            # CREATE DATABASE IF NOT EXISTS：库已存在则跳过，不会报错
            cur.execute(
                f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci"
            )
        conn.commit()  # 提交事务，让上面的语句实际生效
    finally:
        conn.close()  # 无论成功失败都要关闭连接，避免占用数据库连接资源


# 允许直接运行 python db.py 单独初始化数据库（调试用）
if __name__ == "__main__":
    init_db()
    print(f"数据库 {DB_NAME} 初始化完成")

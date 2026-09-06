"""
db 模块
负责数据库连接与初始化：
1. 自动创建 login_db 数据库
2. 创建 tags / file_tags 表（文件标签）

【为什么用 MySQL 存标签？】
标签数据需要持久化（重启进程不丢），并支持按标签反查文件，
因此用 MySQL 而不是内存或文件。
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


def get_connection(database: str = DB_NAME):
    """建立到 login_db 的连接（需先执行 init_db）。

    **DB_CONFIG 把字典展开成关键字参数：
    pymysql.connect(host=..., user=..., password=..., charset=...)
    再通过 {"database": database} 指定要连接的库。
    """
    # 合并：在原配置基础上补上自动探测的密码和要连接的库
    config = {**DB_CONFIG, "password": _resolve_db_password(), "database": database}
    return pymysql.connect(**config)


def init_db():
    """建库建表（幂等，可重复执行）。

    "幂等" = 重复执行结果一样，不会重复建库/建表，
    所以每次启动调用都安全。
    """
    # 1. 连接 MySQL 服务（不带 database），创建 login_db 数据库
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

    # 2. 连接 login_db，创建标签相关表
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # 文件标签表：tags 存标签名，file_tags 存"标签 × 文件"的多对多关系
            #    - tags.name 加 UNIQUE：同一个标签只存一行（其它文件引用它的 id）
            #    - file_tags 用 (tag_id, path_md5) 做唯一键：一个文件同标签只打一次
            #    - path_md5 是路径的 md5（32 位定长），避免用长路径做索引超长（utf8mb4 索引长度受限）
            #    - 外键级联删除：删除某标签时，file_tags 里所有引用一并删除
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS tags (
                    id INT AUTO_INCREMENT PRIMARY KEY,           -- 标签自增主键
                    name VARCHAR(100) NOT NULL UNIQUE,           -- 标签名（唯一，如"教程"/"重要"）
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP -- 创建时间
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS file_tags (
                    id INT AUTO_INCREMENT PRIMARY KEY,           -- 记录自增主键
                    tag_id INT NOT NULL,                         -- 所属标签 id（外键）
                    path VARCHAR(1000) NOT NULL,                 -- 文件相对 TEXT_DIR 的路径（可读）
                    path_md5 CHAR(32) NOT NULL,                  -- 路径的 md5（用于唯一索引/查询）
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE KEY uq_tag_path (tag_id, path_md5),   -- 同一文件同一标签只打一次
                    KEY idx_path (path_md5),                     -- 按文件反查标签走此索引
                    CONSTRAINT fk_file_tags_tag FOREIGN KEY (tag_id)
                        REFERENCES tags(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """
            )
        conn.commit()
    finally:
        conn.close()


# 允许直接运行 python db.py 单独初始化数据库（调试用）
if __name__ == "__main__":
    init_db()
    print(f"数据库 {DB_NAME} 初始化完成")

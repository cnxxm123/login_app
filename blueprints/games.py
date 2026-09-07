"""games 模块（blueprints 包）：游戏蓝图。

- GET  /game                       游戏大厅页。扫描 GAME_DIR（项目内 game/）下
                                    每个含 index.html 的子文件夹，以卡片形式展示；
                                    点击卡片在【新标签页】打开对应游戏。
- GET  /game/<path>                返回游戏目录内的静态文件（index.html 及 js/css 等），
                                    供浏览器直接渲染游玩。send_from_directory 自带
                                    目录穿越防护。
- POST /game/uninstall/<name>      卸载游戏：把游戏文件夹移入备份目录（软删除，可还原）
- GET  /game/uninstalled           已卸载游戏管理页：还原 / 彻底删除
- POST /game/restore/<name>        还原已卸载游戏回大厅
- POST /game/purge/<name>          彻底删除已卸载游戏（物理删除，不可恢复）

游戏是纯前端 HTML/JS 单页，无需后端参与游戏逻辑，只是静态托管。
卸载/还原的纯逻辑在 services/game_utils（移动/列表/还原/删除）。

【暂时停用说明】2026-09-08 起游戏功能暂停启用，本文件与全部路由代码保留未删。
启用方式：在 app.py 顶部恢复 `from blueprints.games import games_bp` 的 import，
并在 create_app() 中恢复 `app.register_blueprint(games_bp)` 的注册即可。
"""

import os

from flask import Blueprint, abort, redirect, render_template, send_from_directory, url_for

from config import GAME_DIR
from services import game_utils

games_bp = Blueprint("games", __name__)

# 已知游戏的中文展示名（未收录的游戏默认沿用英文文件夹名）
# 与游戏自身 index.html 的 <title> 保持一致
GAME_NAMES = {
    "snake": "贪吃蛇",
    "breakout": "打砖块",
    "tetris": "俄罗斯方块",
    "minesweeper": "扫雷",
    "memory": "记忆翻牌",
    "idle": "能量工厂",
    "whack": "打地鼠",
    "flappy": "像素小鸟",
    "gomoku": "五子棋",
    "go": "围棋",
    "chess": "中国象棋",
    "math": "速算挑战",
    "fruitninja": "水果忍者",
}

# 已知游戏的展示图标（未收录的游戏名默认用 🎮）
# 注意：只收录当前 game/ 目录里实际存在的游戏，避免死配置
GAME_ICONS = {
    "snake": "🐍",
    "breakout": "🧱",
    "tetris": "🧩",
    "minesweeper": "💣",
    "memory": "🎴",
    "idle": "⚡",
    "whack": "🐹",
    "flappy": "🐤",
    "gomoku": "⚫",
    "go": "⚪",
    "chess": "♟️",
    "math": "🧮",
    "fruitninja": "🍉",
}


@games_bp.route("/game")
def hall():
    """游戏大厅：列出 game/ 下所有含 index.html 的游戏文件夹。"""
    games = []
    if os.path.isdir(GAME_DIR):
        for name in sorted(os.listdir(GAME_DIR)):
            d = os.path.join(GAME_DIR, name)
            if os.path.isdir(d) and os.path.isfile(os.path.join(d, "index.html")):
                games.append({
                    "name": name,
                    "display_name": GAME_NAMES.get(name, name),  # 前端显示用中文名
                    "icon": GAME_ICONS.get(name, "🎮"),
                    "url": url_for("games.file", filepath=name + "/index.html"),
                })
    return render_template("games.html", games=games)


@games_bp.route("/game/<path:filepath>")
def file(filepath: str):
    """返回游戏静态文件（index.html / js / css 等）。

    send_from_directory 会校验最终路径仍在 GAME_DIR 内，天然防目录穿越。
    """
    if not os.path.isdir(GAME_DIR):
        abort(404)
    resp = send_from_directory(GAME_DIR, filepath)
    # 游戏是频繁迭代的纯前端单页，禁止缓存，避免用户看到旧版本导致"点了没反应"
    resp.headers["Cache-Control"] = "no-store"
    return resp


@games_bp.route("/game/uninstall/<name>", methods=["POST"])
def uninstall(name: str):
    """卸载游戏：把游戏文件夹移入备份目录（软删除，可还原）。

    成功后重定向回大厅；游戏不存在/名字非法返回 404。
    """
    if not game_utils.uninstall(name):
        abort(404)
    return redirect(url_for("games.hall"))


@games_bp.route("/game/uninstalled")
def uninstalled():
    """已卸载游戏管理页：展示备份目录里的游戏，可还原或彻底删除。"""
    items = game_utils.list_uninstalled()
    # 给每个条目补中文展示名（未收录的沿用文件夹名）
    for it in items:
        it["display_name"] = GAME_NAMES.get(it["name"], it["name"])
    return render_template(
        "games_uninstalled.html",
        items=items,
    )


@games_bp.route("/game/restore/<name>", methods=["POST"])
def restore(name: str):
    """还原已卸载游戏回大厅；大厅已有同名游戏返回 409。"""
    ok, result = game_utils.restore(name)
    if not ok:
        if result == "conflict":
            abort(409)  # 目标位置已被占用，前端提示后自行处理
        abort(404)
    return redirect(url_for("games.uninstalled"))


@games_bp.route("/game/purge/<name>", methods=["POST"])
def purge(name: str):
    """彻底删除已卸载游戏（物理删除，不可恢复；前端有二次确认）。"""
    if not game_utils.permanent_delete(name):
        abort(404)
    return redirect(url_for("games.uninstalled"))

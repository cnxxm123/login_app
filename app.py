"""app 模块（项目入口）
创建并配置 Flask 应用，注册各蓝图，启动开发服务器。

【Flask 项目标准结构：三层分层，不同功能分到不同模块】
- 入口/配置层（项目根目录）
  - app.py       项目入口：把各部分组装起来并启动
  - config.py    全局配置：路径、扩展名表等
  - db.py        数据库：连接、建库
- blueprints 包（路由处理层，只处理 HTTP 交互）
  - browser.py   浏览蓝图：主页 / 目录浏览 / 搜索
  - view.py      查看蓝图：文档/图片/PDF/视频 查看页
  - media.py     媒体蓝图：图片/PDF/视频 流式返回 + 视频封面缩略图
  - download.py  下载蓝图：单文件下载 / 目录打包 zip 下载
  - manage.py    管理蓝图：上传 / 新建文件夹 / 在线编辑
  - logs.py      日志蓝图：工作日志增删改 / 转待办
  - todos.py     待办蓝图：待办增删改 / 完成切换
  - memos.py     备忘蓝图：备忘增删改 / 图片上传与展示
  - epub.py      EPUB 蓝图：电子书阅读器 / 元数据 / 章节 / 内嵌资源
- services 包（纯业务逻辑层，不依赖 Flask，不处理 HTTP）
  - path_utils.py  路径安全校验（防目录穿越）
  - dir_utils.py   列目录 / 自然排序 / 递归搜索 / 目录图片列表
  - text_utils.py  多编码读文本 / Markdown 渲染
  - media_utils.py 视频封面抽帧（ffmpeg + 缓存）
  - office_utils.py Office 文档解析（docx/xlsx/xls → HTML）
  - log_store.py   工作日志 JSON 存储
  - todo_store.py  待办事项 JSON 存储
  - memo_store.py  备忘录 JSON 存储 + 图片文件存取
  - epub_utils.py  EPUB 解析（元数据/章节/资源提取）"""

from flask import Flask  # Flask 框架核心：创建应用对象

from blueprints.browser import browser_bp     # 浏览蓝图（/、/browse/...）
from blueprints.download import download_bp   # 下载蓝图（/download/...）
from blueprints.epub import epub_bp           # EPUB 蓝图（/epub/...）
from blueprints.logs import logs_bp           # 日志蓝图（/logs、/log/add...）
from blueprints.manage import manage_bp       # 管理蓝图（/upload/...、/mkdir、/edit/...）
from blueprints.media import media_bp         # 媒体蓝图（/media/...、/thumb/...）
from blueprints.memos import memos_bp         # 备忘蓝图（/memos、/memo/add...）
from blueprints.todos import todos_bp         # 待办蓝图（/todos、/todo/add、/todo/toggle...）
from blueprints.view import view_bp           # 查看蓝图（/view/...）
from config import MAX_FORM_PARTS, MAX_UPLOAD_BYTES  # 上传上限
from db import init_db                        # 数据库初始化函数（幂等）


def create_app() -> Flask:
    """应用工厂：创建应用并注册蓝图。

    用函数封装的好处：
    1. 可以方便地创建多个应用实例（测试时很有用）
    2. 初始化逻辑集中，代码清晰
    """
    app = Flask(__name__)  # 创建 Flask 应用实例
    # 模板改动后即时生效（开发期无需每次手动重启服务）
    app.config["TEMPLATES_AUTO_RELOAD"] = True
    # 上传上限（重点针对"整个文件夹一次性打包上传"）：
    # - MAX_FORM_PARTS 默认只有 1000，文件夹里文件数一多就报 413 失败，已放宽
    # - MAX_CONTENT_LENGTH 默认无限制，这里显式给单次请求体上限，防异常超大请求
    #   单个大文件不受影响（Werkzeug 会自动把大文件暂存到磁盘临时文件，不占内存）
    # 数值统一定义在 config.py（页面提醒用的也是同一来源，见 browser.py）
    app.config["MAX_FORM_PARTS"] = MAX_FORM_PARTS
    app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_BYTES
    # 静态资源（css/js 等）不长期缓存 + HTML 页面禁用缓存：
    # 改动保存后浏览器刷新即可看到效果（Flask 非 debug 下静态默认缓存 12 小时，
    # 页面无缓存头时浏览器启发式缓存，都会导致"改了半天看不到"）
    app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0

    @app.after_request
    def no_cache_html(resp):
        # 只针对 HTML 页面，不碰 /media 流媒体等自带缓存策略的响应
        if resp.mimetype == "text/html":
            resp.headers["Cache-Control"] = "no-store"
        return resp
    app.register_blueprint(browser_bp)  # 注册浏览蓝图 → 提供主页/目录浏览
    app.register_blueprint(view_bp)     # 注册查看蓝图 → 提供 /view/...
    app.register_blueprint(media_bp)    # 注册媒体蓝图 → 提供 /media/...、/thumb/...
    app.register_blueprint(download_bp)  # 注册下载蓝图 → 提供 /download/...
    app.register_blueprint(manage_bp)    # 注册管理蓝图 → 提供 /upload/...、/mkdir、/edit/...
    app.register_blueprint(logs_bp)      # 注册日志蓝图 → 提供 /logs、/log/add、/log/update、/log/delete
    app.register_blueprint(todos_bp)     # 注册待办蓝图 → 提供 /todos、/todo/add、/todo/toggle 等
    app.register_blueprint(memos_bp)     # 注册备忘蓝图 → 提供 /memos、/memo/add、/memo/update、/memo/delete
    app.register_blueprint(epub_bp)      # 注册 EPUB 蓝图 → 提供 /epub/...
    return app


# 模块级直接创建实例，供启动或测试导入使用
app = create_app()

if __name__ == "__main__":
    # 只有"直接运行本文件"时才执行下面的代码；
    # 若被其他文件 import，则不会启动服务器（避免重复启动）。
    init_db()  # 启动前确保库表就绪（幂等，可重复执行）
    # 监听 0.0.0.0 使同一局域网内其他设备可通过 http://<本机IP>:5000 访问
    # 关闭 debug：网络暴露时开启 debugger 存在远程代码执行风险
    app.run(host="0.0.0.0", port=5000, debug=False)

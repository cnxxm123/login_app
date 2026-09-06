"""config 模块
集中管理应用级配置常量，供其他模块引用。

【为什么单独建一个配置模块？】
把路径、扩展名表这类"可变信息"集中放在一起：
- 改配置不用翻遍所有代码
- 各模块 import 同一个值，保证一致
"""

import os

# 本文件所在目录的绝对路径（E:\projectwork\login_app）
# os.path.abspath(__file__) 归一化为绝对路径；os.path.dirname 取所在目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ====================================================================
#  读取路径设置：只需要把下面 CONTENT_PATH 里的路径字符串替换成
#  你想浏览的文件夹即可（复制路径粘贴进去），改完重启服务生效。
# ====================================================================
# 示例：
#   CONTENT_PATH = r"D:\我的资料"
#   CONTENT_PATH = r"C:\Users\你的用户名\Documents"
# 说明：
#   - 用 r"..." 原始字符串，反斜杠无需转义，路径用 \ 或 / 都可以；
#   - 留空 ""（或注释掉本行）时，依次回退到环境变量 TEXT_DIR，再回退到项目内 text/。
# 本机（无 F 盘）不指定目录，留空回退到项目内 text/；如需浏览其他文件夹，
# 把下面路径字符串替换成目标目录即可（例如 CONTENT_PATH = r"D:\我的资料"）。
CONTENT_PATH = "F:\sex"

# 内容目录最终取值：CONTENT_PATH（本文件直接指定）> 环境变量 TEXT_DIR > 项目内 text/
TEXT_DIR = (
    CONTENT_PATH
    or os.environ.get("TEXT_DIR")
    or os.path.join(BASE_DIR, "text")
)

# 工作日志存储目录：放在项目根目录下（与 game 目录平级），自动新建"工作日志"文件夹。
# 日志以 JSON 文件（logs.json）保存在其中，可直接查看 / 备份；首次写入时自动创建。
LOG_DIR = os.path.join(BASE_DIR, "工作日志")
LOG_FILE = os.path.join(LOG_DIR, "logs.json")


# 视频封面缩略图缓存目录（生成后按文件指纹命名缓存，避免每次重复抽帧）
# 放在项目目录内（不在 TEXT_DIR 里），不会污染浏览内容
THUMB_DIR = os.path.join(BASE_DIR, "_thumbs")

# 图片缩略图缓存目录：图片卡片/文件夹封面加载的是压缩后的缩略图而非原图，
# 目录里图片多时能显著减少流量与内存占用；按文件指纹命名缓存，避免重复生成。
# 同样放在项目目录内（不在 TEXT_DIR 里），可随时清空（删除后会自动重新生成）。
IMG_THUMB_DIR = os.path.join(BASE_DIR, "_imgthumbs")

# 视频兼容转换缓存目录：手机浏览器不支持的视频（如 HEVC、moov 在末尾）
# 会被转码成 H.264 + moov 前置（faststart），结果缓存到这里按指纹复用。
# 同样放在项目目录内，避免污染浏览内容。
TRANSCODE_DIR = os.path.join(BASE_DIR, "_transcodes")

# 回收站目录：删除 = 移到这里的软删除，可还原；清空才真正物理删除。
# 与 _thumbs 一样放在项目目录内（不在 TEXT_DIR 里），浏览/搜索都不会误入。
TRASH_DIR = os.path.join(BASE_DIR, "_trash")

# 上传限制（同时用于 Flask 请求体校验与页面提醒，保证两侧一致）：
# - MAX_FORM_PARTS：一次 multipart 请求最多多少个"部件"（每个文件算 1 个）。
#   文件夹上传是把整棵目录打包成一次请求，文件数超过该值会报 413。
# - MAX_UPLOAD_BYTES：单次请求体总大小上限（字节）。
MAX_FORM_PARTS = 20000
MAX_UPLOAD_BYTES = 16 * 1024 * 1024 * 1024  # 16 GB

# 游戏目录：每个子文件夹含 index.html 即一个小游戏，点击后在新标签页游玩
GAME_DIR = os.path.join(BASE_DIR, "game")

# 已卸载游戏备份目录：卸载 = 把游戏文件夹移动到这里（软删除），可一键还原。
# 与 _trash（文本回收站）同样的思路：不放回 GAME_DIR 就不会再出现在大厅，
# 同时也不会被误删，确认后才彻底删除。放项目目录内，不污染游戏目录。
GAME_UNINSTALL_DIR = os.path.join(BASE_DIR, "_removed_games")

# 可预览的文本文件扩展名
# 命中这些扩展名的文件会被当成文本读取并在网页展示
# 这里用集合 set 而不是列表：判断"是否包含"时查找更快（O(1)），且天然去重
TEXT_EXTENSIONS = {
    ".py", ".md", ".txt", ".html", ".htm", ".css", ".js", ".json",
    ".yaml", ".yml", ".ini", ".cfg", ".log", ".csv", ".xml", ".sql",
}

# 代码类文件扩展名 → Markdown 代码块语言标识
# 命中此表的文件会整体放进 ```lang 代码块 中展示（方便浏览器端语法高亮）
# 例如 .py → python，渲染成 ```python ... ``` 代码块
CODE_LANGUAGES = {
    ".py": "python",
    ".c": "c", ".h": "c", ".cpp": "cpp", ".hpp": "cpp",
    ".java": "java",
    ".js": "javascript", ".ts": "typescript",
    ".html": "html", ".htm": "html", ".css": "css",
    ".json": "json", ".xml": "xml",
    ".yaml": "yaml", ".yml": "yaml", ".sql": "sql",
    ".sh": "bash", ".go": "go", ".rs": "rust",
    ".php": "php", ".rb": "ruby",
    ".ini": "ini", ".cfg": "ini", ".bat": "bat", ".ps1": "powershell",
}

# 图片类文件扩展名
# 命中这些扩展名的文件以图片形式在页面预览，并支持上一张/下一张切换
IMAGE_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".svg", ".ico",
}

# 图片扩展名 → 对应 MIME 类型（浏览器据此识别图片格式）
# 注意 .jpg 的标准 MIME 是 image/jpeg 而非 image/jpg
IMAGE_MIME = {
    ".png": "image/png",
    ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".bmp": "image/bmp",
    ".webp": "image/webp",
    ".svg": "image/svg+xml",
    ".ico": "image/x-icon",
}

# PDF 文件扩展名（以 iframe 内嵌预览）
PDF_EXTENSIONS = {".pdf"}

# 视频类文件扩展名
# 命中这些扩展名的文件通过 /media 路由返回，浏览器原生播放器播放
VIDEO_EXTENSIONS = {
    ".mp4", ".webm", ".mkv", ".mov", ".avi", ".flv", ".ts", ".m4v",
    ".mpg", ".mpeg", ".wmv", ".ogv", ".m3u8",
}

# 视频扩展名 → 对应 MIME 类型（浏览器据此识别视频格式）
VIDEO_MIME = {
    ".mp4": "video/mp4",
    ".webm": "video/webm",
    ".mkv": "video/x-matroska",
    ".mov": "video/quicktime",
    ".avi": "video/x-msvideo",
    ".flv": "video/x-flv",
    ".ts": "video/mp2t",
    ".m4v": "video/x-m4v",
    ".mpg": "video/mpeg",
    ".mpeg": "video/mpeg",
    ".wmv": "video/x-ms-wmv",
    ".ogv": "video/ogg",
    ".m3u8": "application/x-mpegURL",
}

# 音频类文件扩展名
# 命中这些扩展名的文件通过 /media 路由返回，浏览器原生播放器播放
AUDIO_EXTENSIONS = {
    ".mp3", ".flac", ".wav", ".ogg", ".m4a", ".aac", ".wma", ".opus",
}

# 音频扩展名 → 对应 MIME 类型（浏览器据此识别音频格式）
AUDIO_MIME = {
    ".mp3": "audio/mpeg",
    ".flac": "audio/flac",
    ".wav": "audio/wav",
    ".ogg": "audio/ogg",
    ".m4a": "audio/mp4",
    ".aac": "audio/aac",
    ".wma": "audio/x-ms-wma",
    ".opus": "audio/ogg",
}

# Office 文档类扩展名（在线预览，无需下载到本地）
# - .docx：Word 文档，用 python-docx 解析段落/表格/标题
# - .xlsx：Excel 工作簿，用 openpyxl 解析单元格渲染成表格
# - .xls ：旧版 Excel，用 xlrd 解析（兼容历史文件）
OFFICE_EXTENSIONS = {".docx", ".xlsx", ".xls"}


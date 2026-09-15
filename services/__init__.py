"""services 包：纯业务逻辑层（不依赖 Flask，不处理 HTTP）。

只提供可复用的函数，供 blueprints 包中的路由调用：
- path_utils.py   路径安全校验（防目录穿越）
- dir_utils.py    列目录 / 自然排序 / 递归搜索 / 目录图片列表
- text_utils.py   多编码读文本 / Markdown 渲染
- media_utils.py  视频封面抽帧 + 视频兼容转码 + 视频时长探测 + 图片缩略图（ffmpeg/Pillow + 缓存）
- office_utils.py Office 文档解析：docx/xlsx/xls → HTML（在线预览）
- log_store.py    工作日志读写（JSON 文件存储）
- todo_store.py   待办事项读写（JSON 文件存储）
- memo_store.py   备忘录读写（JSON 文件存储）+ 图片文件存取
- epub_utils.py   EPUB 解析：元数据 / 章节目录 / 章节 HTML / 内嵌资源提取
"""

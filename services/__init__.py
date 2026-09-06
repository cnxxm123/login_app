"""services 包：纯业务逻辑层（不依赖 Flask，不处理 HTTP）。

只提供可复用的函数，供 blueprints 包中的路由调用：
- path_utils.py   路径安全校验（防目录穿越）
- dir_utils.py    列目录 / 自然排序 / 递归搜索 / 目录图片列表
- text_utils.py   多编码读文本 / Markdown 渲染
- media_utils.py  视频封面抽帧 + 视频兼容转码 + 媒体访问令牌（ffmpeg + 缓存）
- trash_utils.py  文本回收站：移入 / 列出 / 还原 / 彻底删除 / 清空
- game_utils.py   游戏卸载 / 还原 / 彻底删除（软删除，备份到 _removed_games）
"""

"""blueprints 包：所有 Flask 蓝图（路由处理层）。

每个蓝图负责一类路由：
- browser.py   浏览：主页 / 目录浏览 / 搜索
- view.py      查看：文档/图片/PDF 查看页 + 通用视频播放页
- media.py     媒体：图片/PDF/视频 流式返回 + 视频封面缩略图
- download.py  下载：单文件下载 / 目录打包 zip 下载
- manage.py    管理：上传 / 新建文件夹 / 在线编辑
- logs.py      工作日志：列表 / 新增 / 编辑 / 删除 / 转为待办
- todos.py     待办事项：列表 / 新增 / 编辑 / 完成 / 删除
"""

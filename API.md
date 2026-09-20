# 接口文档（重构后）

本文档对应重构后的项目结构（`blueprints/` 路由层 + `services/` 纯逻辑层），
供后续维护、二次开发时快速查阅每个接口的地址、参数、返回与权限要求。

> 说明：本应用是**页面渲染型**（服务端渲染 HTML），并非 REST JSON 接口。
> 除上传外，多数接口通过浏览器地址栏 / 表单 / 链接访问即可，返回值以 `HTTP 状态码` 表达成败。

---

## 1. 通用约定

### 1.1 访问根路径与端口

| 项 | 值 |
| --- | --- |
| 监听地址 | `0.0.0.0:5000`（同一局域网可通过 `http://<本机IP>:5000` 访问） |
| 内容根目录 | `config.TEXT_DIR`（默认 `login_app/text/`，可用环境变量 `TEXT_DIR` 覆盖），所有"内容路径"均相对它 |
| 封面缓存目录 | `config.THUMB_DIR`（`BASE_DIR/_thumbs`），视频封面缩略图，可随时清空 |
| 图片缩略图缓存目录 | `config.IMG_THUMB_DIR`（`BASE_DIR/_imgthumbs`），图片压缩缩略图，可随时清空 |
| 转码缓存目录 | `config.TRANSCODE_DIR`（`BASE_DIR/_transcodes`），视频兼容转码缓存，可随时清空 |

### 1.2 访问控制

- **无需登录**：本应用已移除登录功能，启动后所有接口均可直接访问，无 session / 令牌校验。

### 1.3 路径参数规则（重要）

- 路由中的 `<path:subpath>` 是 Flask 的**路径转换器**，可匹配含 `/` 的多级路径，
  例如 `/browse/爬虫基础/第一节`。
- 路径参数需 **URL 编码**（中文、空格等需转义），例如：
  `text/爬虫基础/第一节/环境搭建.md` 对应
  `/view/%E7%88%AC%E8%99%AB%E5%9F%BA%E7%A1%80/%E7%AC%AC%E4%B8%80%E8%8A%82/%E7%8E%AF%E5%A2%83%E6%90%AD%E5%BB%BA.md`。
- 所有磁盘访问都经过 `services/path_utils.safe_path()` 校验：
  路径解析后必须仍位于 `TEXT_DIR` 内，否则返回 `404`（防目录穿越）。

### 1.4 常见状态码

| 状态码 | 含义 |
| --- | --- |
| `200` | 成功（页面 / 文件流） |
| `302` | 重定向（操作完成后跳回上级目录、空搜索跳回起始目录、图集条件不满足回退目录浏览） |
| `400` | 参数非法（如新建文件夹名称含路径分隔符） |
| `404` | 路径不存在 / 越界 / 非目标类型（目录穿越时也返回 404） |
| `409` | 冲突（如新建文件夹时名称已存在） |

---

## 2. 浏览接口（`blueprints/browser.py`）

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/` | 主页：浏览 `TEXT_DIR` 根目录 |
| GET | `/browse/<path:subpath>` | 浏览指定目录 |
| GET | `/search` | 按文件名 / 内容递归搜索 |
| GET | `/duration/<path:subpath>` | 视频时长 JSON（卡片角标） |

### 2.1 GET / 与 GET /browse/<path:subpath>

- 渲染 `templates/main.html`（文件夹卡片 + 文件卡片网格）。
- 页面上下文：`path`、`parent`、`breadcrumbs`（面包屑）、`dirs_cover`（有封面文件夹）、`dirs_plain`（纯文件夹）、`files`。
- 文件夹按"是否有封面"拆成两区展示：`dirs_cover`（有封面文件夹）、`dirs_plain`（纯文件夹），两区各自独立换行。
- **文件夹封面（自定"封面"图）**：封面优先级为"文件夹内名为"封面"的图片（如 `封面.jpg`，任意文件夹适用）> 纯图片图集文件夹的第一张图"。名为"封面"的图片**只作封面展示，进入文件夹 / 图集阅读时不显示**（目录文件列表、图集页、图片长条预览均排除；但搜索可直接搜到并打开它）。封面统一走 `/imgcover` **高清缩略图**（900px/质量 88），所有文件夹封面都清晰。
- **封面文件夹点击直接进入图集阅读页 `/gallery/<path>`**（见 3.2，仅 `cover.gallery=True` 的图集文件夹），不再进文件夹列表；普通文件夹（即使有"封面"图当封面）仍进目录浏览页。图集卡片角标"📁 N 张"显示**可见图片数**（不含封面图），普通封面卡片不显示"N 张"角标。
- **新标签页规则**：图集卡片（`new_tab=True`）与视频/文档/图片文件卡片（`external=True`）一样，点击在新标签页打开（`target="_blank" rel="noopener"`），不打断目录浏览；普通文件夹卡片仍原地打开目录浏览页。搜索页的文件结果同样新标签页打开，目录结果原地打开。
- 主页/浏览页还提供**网格 / 列表两种视图**：列表视图单列展示（显示文件大小与类型图标），偏好经 `main_view` 键存 localStorage 记住；目录头部显示"目录 + 文件数量"统计。
- `files` 中每个条目含：`name`、`kind`（`video`/`image`/`text`）、`thumb`（视频封面/图片缩略图）、
  `url`、`external`（是否新标签页打开）、`path`（供下载）、`size`（文件字节数，读失败为 0，列表视图显示大小）、`editable`（是否可在线编辑）。
- 视频条目的 `url` 指向**查看页** `/view/<path>`，由查看页自定义播放器播放（加载 `/media` 流地址），不再直接打开 `/media` 裸流。
- 路径非法或不是目录 → `404`。

### 2.2 GET /search

- **查询参数**:

| 参数 | 必填 | 说明 |
| --- | --- | --- |
| `q` | 是 | 搜索关键字（去首尾空格） |
| `path` | 否 | 起始目录（默认根目录） |
| `mode` | 否 | `name`（按文件名，默认）或 `content`（按文件内容） |

- `mode=content` 时读文本/代码文件内容做匹配，结果带上下文摘要（由 `services/dir_utils.search_content` 实现）。
- `q` 为空 → `302` 跳回起始目录（有 `path` 跳 `/browse/<path>`，否则跳 `/`）。
- 成功 → `200` 渲染 `templates/search.html`。

### 2.3 GET /duration/<path:subpath>

- 返回视频时长 JSON：`{"duration": 123.45 | null}`（文件卡片右下角时长角标用）。
- 由 `services/media_utils.get_video_duration` 用 ffmpeg 探测并缓存（按绝对路径 + mtime + 大小做缓存键，新文件/替换文件自动重新探测）。
- 路径非法 / 不存在 / 非视频扩展名 / ffmpeg 不可读 → `{"duration": null}`。

---

## 3. 查看接口（`blueprints/view.py`）

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/view/<path:subpath>` | 查看文档 / 图片 / PDF / Office / 视频 / 音频 |
| GET | `/gallery/<path:subpath>` | 图集/漫画全屏阅读器（纯图片目录，见 3.2） |

### 3.1 GET /view/<path:subpath>

- 目标必须是 `TEXT_DIR` 内的**文件**，否则 `404`。
- 按扩展名分派（由 `config.py` 扩展名表决定）：

| 文件类型 | 扩展名 | 行为 |
| --- | --- | --- |
| 文本/代码 | `TEXT_EXTENSIONS` ∪ `CODE_LANGUAGES` | 读内容（utf-8/gbk 自动识别）并渲染 Markdown HTML |
| 图片 | `IMAGE_EXTENSIONS` | 同目录全部图片长条预览 + 单页阅读器 |
| PDF | `PDF_EXTENSIONS` | 在新标签页用浏览器原生查看器打开 `/media/<path>` |
| Office | `OFFICE_EXTENSIONS`（docx/xlsx/xls） | 服务端解析成 HTML 在页面内直接预览（无需下载） |
| 视频 | `VIDEO_EXTENSIONS` | 页面内嵌**自定义网页播放器**（`templates/view.html` + `player.js`），加载 `/media/<path>` 二进制流；支持进度记忆/续播提示/结束覆盖层（见 3.1.1） |
| 音频 | `AUDIO_EXTENSIONS` | 页面内嵌浏览器原生 `<audio>` 播放器，加载 `/media/<path>` 二进制流 |

- 视频/音频会同时构建"整目录同类媒体"连播列表（`dir_media`），播放结束自动切下一首/集。
- 渲染 `templates/view.html`，含：`content_html`、`office_html`、`encoding`、`media_type`、`media_url`、
  `images`、`image_urls`、`playlist`（连播列表）、`playlist_index`（当前文件下标）、`parent` 等。

### 3.1.1 视频播放器（自定义控制栏 + 进度记忆）

- 播放器容器带 `data-key`（= 当前文件相对路径），播放进度按该 key 存入 localStorage（`vp_pos_<key>`，每 5 秒节流保存，播放完成自动清除）。
- **续播提示**：重新进入未看完的视频时，弹出"上次看到 分:秒 / 总时长"询问"继续播放 / 从头播放"（仅页面首次加载弹一次，切集不弹）。
- **结束覆盖层**：播放完成显示"↻ 重播"与"下一集"（播放列表 ≥ 2 项时出现），接续连播。
- 控制栏含：播放/暂停、进度条（可拖动 + 缓冲分区）、时间显示、音量滑块 + 静音、倍速菜单（0.5~2 倍）、画中画、全屏/网页全屏、播放列表开关、上一集/下一集；鼠标闲置自动隐藏控制栏，快捷键（空格/←→/↑↓/M/F 等）齐全。

### 3.2 GET /gallery/<path:subpath>（图集 / 漫画阅读）

- 目标必须是 `TEXT_DIR` 内的**目录**，且满足"图集"条件：**无子目录、直接文件全是图片**
  （判定收敛在 `services.dir_utils.dir_all_images`，与封面区卡片共用同一逻辑）。
- 不符合图集条件（如内容后来被改动）→ `302` 回退到 `/browse/<path>` 普通目录浏览，不报错。
- 渲染 `templates/gallery.html`：**全屏沉浸式漫画阅读器**（深色无侧栏独立页面，不引入 common.css/nav.html，类似视频播放页），进入即从第一张图（或记忆的页码）开始播放。
- 页面能力（参照主流漫画阅读器交互；结构/样式/逻辑三分离：模板 `gallery.html` + `static/css/gallery.css` + `static/js/gallery.js`）：

| 功能 | 说明 |
| --- | --- |
| 两种阅读模式 | 顶部分段控制器切换：**单页**（一页一图）/ **长条**（Webtoon 式全部图片纵向排开滚动） |
| 四种适配方式 | 设置弹层切换：适合屏幕 / 适合宽度 / 适合高度 / 原始大小（缩放以光标/手指为中心） |
| 缩放与平移 | 滚轮缩放、双指捏合、双击放大/还原、放大后拖拽平移（鼠标/触摸统一 pointer 事件） |
| 左右箭头翻页 | 屏幕两侧悬浮箭头，上一页 / 下一页（到头/到尾自动禁用）；**手机端不显示箭头**，改为滑动屏幕翻页（左右横滑，RTL 反转）与实体音量键翻页 |
| 右上角页码 | `当前页 / 总页数` 胶囊提示，翻页实时刷新 |
| 顶部阅读进度条 | 控制条上方细进度条显示当前阅读位置，点击任意位置跳页 |
| 自动翻页 | 设置弹层内可开关，间隔 1~30 秒可调（± 1 秒步进），到末页自动停止；长条模式不适用 |
| 翻页过渡动画 | 翻页时当前图淡入过渡，切换自然不生硬 |
| 缩略图导航栏 | 底部横向滚动小图列表（走 `/imgthumb` 压缩缩略图，图多不卡），点击任意页跳转，当前页高亮自动滚到可见，`T` 键或按钮开关 |
| 跳转页码 | 弹层输入页码直达（`数据弹层`按钮或 `J` 键） |
| 阅读方向 | 左→右 / 右→左：RTL 时箭头位置、点击翻页区域同步反转 |
| 点击翻页 | 可开关：点舞台左右区域翻页，点中间唤出/收起控制条（闲置自动隐藏，移动/翻页唤出） |
| 键盘操作 | `←`/`→`/`PageUp`/`PageDown`/`Space` 翻页，`Home`/`End` 首末页，`+`/`-` 缩放、`0` 复位、`F` 全屏、`T` 缩略图栏、`J` 跳页、`Esc` 关弹层；**手机端实体音量键（VolumeUp/Down）翻页** |
| 进度记忆 | 按"图集目录"记住上次页码（长条模式记滚动比例），再打开同一本续读 |
| 偏好记忆 | 记住模式 / 适配 / 方向 / 点击翻页 / 缩略图栏开关（localStorage），下次沿用；触屏设备默认收起缩略图栏 |

- 页面上下文：`gallery_name`（图集名）、`path`、`parent`、`images`（`[{name, path}]`，长条渲染用）、
  `image_urls`（全部图片的访问地址，供 `<img>` 加载）、
  `thumb_urls`（全部图片的 `/imgthumb` 压缩缩略图地址，供缩略图导航栏使用）。
- 图集入口：目录浏览页中"封面文件夹"（有封面的文件夹，`cover.gallery=True` 的图集）的卡片点击**直接进入本页**，不再进文件夹列表
  （由 `blueprints/browser.py` 的 `folder_cover_info` + `dir_all_images` 联合决定）。
- **名为"封面"的图片不参与阅读**：进入图集时从 `images` / `image_urls` / `thumb_urls` 中排除，不计入总页数、缩略图栏不显示（它只作文件夹封面）。

---

## 4. 媒体接口（`blueprints/media.py`）

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/media/<path:subpath>` | 以二进制流返回图片 / PDF / 视频 / 音频 |
| GET | `/thumb/<path:subpath>` | 返回视频封面缩略图（JPG） |
| GET | `/imgthumb/<path:subpath>` | 返回图片压缩缩略图（JPG） |
| GET | `/imgcover/<path:subpath>` | 返回文件夹封面高清缩略图（JPG，900px/质量 88） |

### 4.1 GET /media/<path:subpath>

- 目标必须是文件，否则 `404`。
- 按扩展名返回对应 `Content-Type`：

| 类型 | MIME |
| --- | --- |
| 图片 | `IMAGE_MIME`（如 `image/jpeg`、`image/png`） |
| PDF | `application/pdf` |
| 视频 | `VIDEO_MIME`（如 `video/mp4`；`.m3u8` 为 `application/x-mpegURL`） |
| 音频 | `AUDIO_MIME`（如 `audio/mpeg`、`audio/wav`、`audio/flac`） |
| 其它 | `404` |

- 用 `send_file` 流式发送，支持 `Range`（可拖动进度条）。
- 视频先经 `services/media_utils.ensure_playable()` 做手机兼容（HEVC→H.264 / moov 原子前置，按源文件 md5 缓存，只转一次），已兼容时直接返回原文件字节流，由**浏览器自带播放器**原生播放。
- 音频直接返回原文件字节流，由浏览器原生 `<audio>` 播放。

### 4.2 GET /thumb/<path:subpath>

- 目标必须是文件，否则 `404`。
- 用 `services/media_utils.get_video_thumb()` 抽第 1 秒的一帧（ffmpeg），缩放到宽 ~480px，
  并按视频绝对路径的 md5 命名缓存到 `_thumbs/`，之后直接读缓存。
- `.m3u8`（分片流无法定位单帧）或抽帧失败 → `404`。
- 依赖 `imageio-ffmpeg`；未安装时也返回 `404`（不影响其它功能）。

### 4.3 GET /imgthumb/<path:subpath>

- 目标必须是文件，否则 `404`。
- 用 `services/media_utils.get_image_thumb()` 经 Pillow 等比缩到 400px 以内转存 JPEG（质量 80，按 EXIF 方向转正），
  按图片绝对路径的 md5 命名缓存到 `_imgthumbs/`，之后直接读缓存。
- `.svg`（矢量缩放无损）/ `.ico`（本身极小）不缩略，卡片直接退用原图；直接请求本接口 → `404`。
- 依赖 Pillow；未安装时也返回 `404`（不影响其它功能）。

### 4.4 GET /imgcover/<path:subpath>

- 返回**文件夹封面高清缩略图**（JPG），供封面卡片展示；普通文件卡片仍走 `/imgthumb`（400px）。
- 与 `/imgthumb` 的区别：`services/media_utils.get_cover_thumb()` 等比缩到 900px 以内、JPEG 质量 88
  （封面卡片比普通文件卡片大得多，400px 缩略图放大后会发虚），缓存独立命名（`.cvr.jpg` 后缀），互不覆盖。
- `.svg`/`.ico` 退回原图、404 行为与 `/imgthumb` 一致。

---

## 5. 下载接口（`blueprints/download.py`）

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/download/<path:subpath>` | 下载单个文件 / 把目录打包成 zip |

- 路径不存在或越界 → `404`。
- 目标为**文件**：以附件形式返回原文件（`Content-Disposition: attachment`），
  开启 `conditional=True` 支持断点续传。
- 目标为**目录**：先写入**磁盘临时文件**再流式返回
  （文件名 = 目录名 + `.zip`；自动剔除 `__pycache__` 与 `.pyc`；
  打包大目录时内存占用恒定，临时文件发送完自动删除）。
- **前端交互**：所有下载入口（文件/文件夹卡片右上角 ⬇、搜索结果旁 ⬇、图片预览页"下载整本"）
  点击时先弹**自绘确认框**（`static/js/confirm-download.js`，沙箱 iframe 禁用原生 confirm），
  确认后才发起下载；取消则停留在当前页。

---

## 6. EPUB 电子书接口（`blueprints/epub.py`）

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/epub/<path:subpath>` | EPUB 阅读器页面（左侧章节导航 + 右侧阅读区） |
| GET | `/epub/api/info/<path:subpath>` | 返回书籍元数据 JSON（书名/作者/封面/章节目录） |
| GET | `/epub/api/chapter/<path:subpath>/<chapter_id>` | 返回指定章节的 HTML 内容 JSON |
| GET | `/epub/api/resource/<path:subpath>/<resource_path>` | 返回 EPUB 内嵌资源二进制流（图片/CSS 等） |

### 6.1 GET /epub/<path:subpath>

- 目标必须是 `.epub` 文件，否则 `404`。
- 渲染 `templates/epub_reader.html`：左侧可折叠章节导航栏，右侧阅读区通过 AJAX 加载章节 HTML 内容。
- 页面上下文：`filename`、`book_title`、`path`、`parent`。
- 书籍元数据（书名/作者/章节目录）由前端通过 `/epub/api/info/<path>` 异步获取。

### 6.2 GET /epub/api/info/<path:subpath>

- 返回 JSON：
```json
{
  "title": "书名",
  "author": "作者",
  "cover_href": "封面图片路径（在 EPUB 内的路径，可为空字符串）",
  "chapters": [
    {"id": "chapter_001", "title": "第一章 标题", "href": "Text/chapter1.xhtml", "level": 1},
    ...
  ],
  "spine": [
    {"idref": "chapter_001", "href": "Text/chapter1.xhtml"},
    ...
  ]
}
```
- `chapters` 来自 EPUB 的 NCX/NAV 目录，含多级嵌套（`level` 表示层级深度，1 为顶级章节）。
- `spine` 来自 EPUB 的 `<spine>` 阅读顺序，用于在目录信息不完整时补全章节映射。
- 解析失败 → `400` + `{"error": "无法解析 EPUB 文件"}`。

### 6.3 GET /epub/api/chapter/<path:subpath>/<chapter_id>

- `chapter_id` 为 `/epub/api/info` 返回的 `chapters[].id` 或 `spine[].idref`。
- 后端先根据 `chapter_id` 查找对应的 `href`，再读取 EPUB 内该文件的 HTML 内容。
- 返回 JSON：
```json
{
  "content": "<html 片段>",
  "href": "Text/chapter1.xhtml"
}
```
- 章节未找到 → `404` + `{"error": "章节未找到"}`。
- 内容读取失败 → `500` + `{"error": "无法读取章节内容"}`。

### 6.4 GET /epub/api/resource/<path:subpath>/<resource_path>

- `resource_path` 为 EPUB 内部资源路径（如图片 `images/cover.jpg`、CSS `Styles/main.css`）。
- 以二进制流返回资源内容，自动根据扩展名设置正确的 `Content-Type`（如图片 MIME、CSS `text/css`）。
- 资源不存在 → `404`。

### 6.5 EPUB 目录页入口

- 目录浏览页中，`.epub` 文件在 `files` 列表里识别为 `kind: "text"`，点击即跳转 `/epub/<path>` 打开阅读器（而非 `/view/<path>` 的普通查看页）。
- `.epub` 文件的**下载图标**正常工作：点击先弹确认框，确认后走 `/download/<path>` 下载原文件。

---

## 7. 备忘录接口（`blueprints/memos.py`）

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/memos` | 备忘录页（卡片网格，最新在前） |
| POST | `/memo/add` | 新增备忘 |
| POST | `/memo/update` | 修改备忘 |
| POST | `/memo/delete` | 删除备忘（连带图片文件） |
| POST | `/memo/upload_image` | 上传一张图片，返回访问 URL |
| GET | `/memo/image/<filename>` | 以二进制返回备忘图片 |

### 7.1 GET /memos

- 渲染 `templates/memos.html`：卡片网格展示全部备忘（最新在前），支持前端搜索过滤。
- 每张卡片：标题（可空）+ 正文预览（最多 6 行省略）+ 图片缩略图 + 创建时间 + 编辑标记。
- 页面上下文：`items`（备忘列表）、`total`（总数）、`memos_json`（编辑预填用 JSON）、`image_url`（图片访问模板 URL）。

### 7.2 POST /memo/add

- **表单字段**：

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `title` | 否 | 标题（去首尾空格，可空） |
| `content` | 是 | 正文（非空，否则 400） |
| `images` | 否 | 图片文件名列表（可重复字段，来自上传 `/memo/upload_image` 的返回值） |

- 返回 JSON：`{"ok": true, "id": 新记录id}`。

### 7.3 POST /memo/update

- **表单字段**：同 `/memo/add`，额外 `id`（必填）。
- 编辑时被移除的旧图片文件会一并删除，避免留下孤儿文件。
- 返回 JSON：`{"ok": true}` 或 `{"ok": false, "error": "..."}`（404 备忘不存在 / 400 内容为空）。

### 7.4 POST /memo/delete

- **表单字段**：`id`（必填）。
- 删除备忘时关联的图片文件一并删除。
- 返回 JSON：`{"ok": true}` 或 `{"ok": false, "error": "..."}`（404 备忘不存在）。

### 7.5 POST /memo/upload_image

- **表单字段**：`image`（文件字段，单张）。
- 校验：扩展名必须在 `IMAGE_EXTENSIONS` 白名单内，单张 ≤ 10MB。
- 文件以 uuid 文件名存入 `MEMO_IMAGE_DIR`（`备忘录/images/`），返回 JSON：
  `{"ok": true, "filename": "abc123.jpg", "url": "/memo/image/abc123.jpg"}`。
- 前端在编辑弹窗内选择图片后立即调用此接口上传，得到 `filename` 后在保存时一并提交到 `/memo/add` 或 `/memo/update`。

### 7.6 GET /memo/image/<filename>

- 以二进制返回备忘图片（卡片缩略图 / 编辑弹窗预览 / lightbox 放大查看均用此接口）。
- 仅接受 `memo_store.valid_image_name()` 校验通过的合法文件名（`uuid.hex + 图片扩展名`），防路径穿越。
- 文件不存在 → `404`。

---

## 8. 工作日志接口（`blueprints/logs.py`）

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/logs` | 工作日志页（按日期分组 / 类别折叠 / 搜索） |
| POST | `/log/add` | 新增日志 |
| POST | `/log/update` | 修改日志 |
| POST | `/log/delete` | 删除日志 |
| POST | `/log/move_todo` | 将日志转为今天的待办 |

### 8.1 GET /logs

- 渲染 `templates/logs.html`：按日期倒序分组，每日期下按类别（`WORK_CATEGORIES`：上架游戏/更新游戏/更新游戏工具/问题处理/其他）折叠排列。
- 类别彩色标签：上架游戏（绿）、更新游戏（蓝）、更新游戏工具（紫）、问题处理（橙红）、其他（灰）。
- 支持前端搜索过滤、手风琴折叠（同时只展开一个日期/类别分组）。
- 页面上下文：`groups`、`total`、`today_count`、`logs_json`（编辑预填 JSON）、`categories`。

### 8.2 POST /log/add

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `log_date` | 是 | 日期（YYYY-MM-DD） |
| `category` | 是 | 类别（必须在 `WORK_CATEGORIES` 白名单内） |
| `content` | 是 | 正文（非空） |

- 返回 JSON：`{"ok": true, "id": 新记录id}` 或 `{"ok": false, "error": "..."}`。

### 8.3 POST /log/update

- **表单字段**：`id`（必填）+ 同 `/log/add`。
- 返回 JSON：`{"ok": true}` 或 `{"ok": false, "error": "..."}`（404 日志不存在）。

### 8.4 POST /log/delete

- **表单字段**：`id`（必填）。
- 返回 JSON：`{"ok": true}` 或 `{"ok": false, "error": "..."}`（404 日志不存在）。

### 8.5 POST /log/move_todo

- **表单字段**：`id`（必填）。
- 以今天的日期、日志原有的类别与内容写入一条待办，然后删除原日志。
- 返回 JSON：`{"ok": true}` 或 `{"ok": false, "error": "..."}`。

---

## 9. 待办事项接口（`blueprints/todos.py`）

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/todos` | 待办事项页（按日期分组） |
| POST | `/todo/add` | 新增待办 |
| POST | `/todo/update` | 修改待办 |
| POST | `/todo/toggle` | 切换完成状态（勾选完成 → 转移到今天的工作日志） |
| POST | `/todo/delete` | 删除待办 |

### 9.1 GET /todos

- 渲染 `templates/todos.html`：按日期倒序分组，显示完成/未完成状态。
- 页面上下文：`groups`、`total`、`today_count`、`undone_count`、`todos_json`、`categories`。

### 9.2 POST /todo/add

- **表单字段**：`todo_date`（日期）、`category`（类别）、`content`（正文，非空）。
- 返回 JSON：`{"ok": true, "id": 新记录id}`。

### 9.3 POST /todo/update

- **表单字段**：`id`（必填）+ 同 `/todo/add`。
- 返回 JSON：`{"ok": true}`。

### 9.4 POST /todo/toggle

- **表单字段**：`id`（必填）。
- 未完成 → 完成：转移到今天的工作日志（保留类别与内容），并删除待办。
- 已完成 → 未完成：仅恢复状态，不转移。
- 返回 JSON：`{"ok": true, "moved": true/false}`。

### 9.5 POST /todo/delete

- **表单字段**：`id`（必填）。
- 返回 JSON：`{"ok": true}`。

---

## 10. 管理接口（`blueprints/manage.py`）

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/upload/` | 上传多个文件到根目录 |
| POST | `/upload/<path:subpath>` | 上传多个文件到指定目录 |
| POST | `/mkdir/` | 在根目录新建文件夹 |
| POST | `/mkdir/<path:subpath>` | 在指定目录新建文件夹 |
| GET | `/edit/<path:subpath>` | 打开在线文本编辑器 |
| POST | `/save/<path:subpath>` | 保存在线编辑内容 |

> 操作成功后统一 `302` 跳回**上级目录**（上级为空则跳 `/`），避免停留在失效路径。

### 8.1 POST /upload/ 与 /upload/<path:subpath>

- **Content-Type**: `multipart/form-data`，字段名 **`files`**（可一次传多个文件）。
- 支持**文件夹上传**：前端把 `webkitRelativePath`（如 `漫画/第1话/001.jpg`）作为文件名提交，
  后端据此逐级建目录还原目录结构。
- **防目录穿越**：对文件名每个路径段校验（不允许空/`.`/`..`/冒号/空字节），
  再用 `realpath` + `commonpath` 确认最终路径仍落在目标目录内，否则丢弃该文件。
- 目标目录不存在 → `404`。

### 8.2 POST /mkdir/ 与 /mkdir/<path:subpath>

- **参数**（表单）: `new_folder`（新文件夹名，去首尾空格）。
- `new_folder` 为空、为 `.`/`..` 或含 `/`、`\` → `400`（防目录穿越）。
- 新路径已存在 → `409`；目标目录不存在 → `404`。

### 8.3 GET /edit/<path:subpath>

- 打开在线文本编辑器（渲染 `templates/editor.html`），仅**文本类扩展名**（`config.TEXT_EXTENSIONS`）可编辑，否则 `400`。
- 用 `services/text_utils.read_text_file` 自动识别编码（utf-8 / gbk 等）读取内容。
- 目标不存在或越界 → `404`；读取失败 → `400`。
- 页面通过 `url_for('manage.save', subpath=path)` 拿到保存接口地址。

### 8.4 POST /save/<path:subpath>

- **参数**（表单）: `content`（编辑后的全文）。
- 目标必须存在且为文本类文件，否则 `400`。
- 统一以 **UTF-8** 编码写回（原编码信息在编辑页展示，前端有确认提示）。
- 成功 → `302` 跳回编辑页（可继续编辑）；目标不存在/越界 → `404`。

---

## 11. 模块依赖速查

| 接口 | 依赖的纯逻辑层（`services/`） | 依赖的配置（`config.py`） |
| --- | --- | --- |
| 浏览 `/`、`/browse` | `dir_utils.list_entries` | `IMAGE_EXTENSIONS`、`PDF_EXTENSIONS`、`VIDEO_EXTENSIONS`、`AUDIO_EXTENSIONS` |
| 搜索 `/search` | `dir_utils.search_files`、`search_content` | — |
| 时长 `/duration` | `path_utils.safe_path`、`media_utils.get_video_duration` | `VIDEO_EXTENSIONS` |
| 查看 `/view` | `path_utils.safe_path`、`dir_utils.dir_images` / `dir_media`、`text_utils.read_text_file` / `render_content_to_html`、`office_utils.render_office_to_html` | `TEXT_EXTENSIONS`、`CODE_LANGUAGES`、`IMAGE_EXTENSIONS`、`PDF_EXTENSIONS`、`VIDEO_EXTENSIONS`、`AUDIO_EXTENSIONS`、`OFFICE_EXTENSIONS` |
| 媒体 `/media` | `path_utils.safe_path`、`media_utils.ensure_playable`（视频兼容转码） | `IMAGE_MIME`、`PDF_EXTENSIONS`、`VIDEO_MIME`、`AUDIO_MIME`、`TRANSCODE_DIR` |
| 缩略图 `/thumb` | `path_utils.safe_path`、`media_utils.get_video_thumb` | `THUMB_DIR` |
| 图片缩略图 `/imgthumb` | `path_utils.safe_path`、`media_utils.get_image_thumb` | `IMG_THUMB_DIR` |
| 封面高清缩略图 `/imgcover` | `path_utils.safe_path`、`media_utils.get_cover_thumb` | `IMG_THUMB_DIR` |
| 下载 `/download` | `path_utils.safe_path` | — |
| 管理 `/upload`、`/mkdir` | `path_utils.safe_path` | — |
| 管理 `/edit`、`/save` | `path_utils.safe_path`、`text_utils.read_text_file` | `TEXT_EXTENSIONS` |
| EPUB `/epub`、`/epub/api/*` | `path_utils.safe_path`、`epub_utils.parse_epub`、`get_epub_chapter_content`、`get_epub_resource` | — |
| 备忘 `/memos`、`/memo/*` | `memo_store`（增删改查 + 图片存取 + 文件名校验） | `MEMO_DIR`、`MEMO_IMAGE_DIR` |
| 日志 `/logs`、`/log/*` | `log_store`（增删改查） | `LOG_DIR`、`WORK_CATEGORIES` |
| 待办 `/todos`、`/todo/*` | `todo_store`（增删改查 + 状态切换）、`log_store`（完成时写入日志） | `TODO_DIR`、`WORK_CATEGORIES` |

---

## 12. 二次开发指引

- **新增文件类型预览**：只需改 `config.py` 的扩展名表（如把新扩展名加进 `TEXT_EXTENSIONS`），并在 `blueprints/view.py` 的分派处补充渲染逻辑。
- **新增接口**：在对应的 `blueprints/*.py` 中加路由；若涉及磁盘路径，一律经 `services/path_utils.safe_path()` 校验。
- **修改内容根目录**：设置环境变量 `TEXT_DIR`（如 `$env:TEXT_DIR="F:\某目录"`）后重启服务；不设置则用默认 `login_app/text/`。改完保存并**删除 `__pycache__` 目录**再重启才生效。

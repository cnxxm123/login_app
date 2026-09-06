"""text_utils 模块（services 包）
文本/文档处理（纯逻辑层，不依赖 Flask）。

只做一件事：读取文本文件内容并按 Markdown 渲染成 HTML。
供 view 蓝图（文档查看页）使用。
"""

import markdown  # 把 Markdown 文本渲染成 HTML
import bleach   # 渲染产物白名单过滤，防存储型 XSS（markdown 默认保留原始 HTML）

from config import CODE_LANGUAGES

# markdown 渲染产物允许的标签白名单（在 bleach 默认集合基础上补齐表格/代码块/标题等）
_ALLOWED_TAGS = list(bleach.sanitizer.ALLOWED_TAGS) + [
    "br", "p", "pre", "h1", "h2", "h3", "h4", "h5", "h6",
    "table", "thead", "tbody", "tr", "th", "td", "caption",
    "img", "hr", "del", "sup", "sub", "span", "div",
]
# 各标签允许的属性（仅保留展示所需，其余一律剥除）
_ALLOWED_ATTRS = {
    "a": ["href", "title", "target", "rel"],       # href 另受 protocols 白名单约束
    "img": ["src", "alt", "title", "width", "height"],
    "th": ["align"],
    "td": ["align"],
    "code": ["class"],     # 语法高亮类（fenced_code 生成 class="language-python"）
    "span": ["class"],
    "div": ["class"],
}
# href/src 允许的协议（自动拦截 javascript: 等危险协议）
_ALLOWED_PROTOCOLS = {"http", "https", "mailto", "tel"}


def read_text_file(path: str) -> tuple[str | None, str | None]:
    """读取文本文件，依次尝试 utf-8 / gbk 编码，返回 (内容, 编码)。

    【为什么要尝试多种编码？】
    中文 Windows 下很多文本是 GBK 编码，而网页默认用 UTF-8。
    统一用 UTF-8 可能解码失败（抛 UnicodeDecodeError），
    所以先试 UTF-8，失败再退回到 GBK，保证中文文档能正常打开。
    返回编码是为了在页面上提示"该文件是 GBK 编码"。
    """
    for enc in ("utf-8", "gbk"):
        try:
            # with open(...) as f：文件用完自动关闭，无需手动 close
            with open(path, encoding=enc) as f:
                return f.read(), enc  # 成功 → 返回内容和所用编码
        except UnicodeDecodeError:
            continue  # 这种编码解不开，试下一种
    return None, None  # 都失败 → 视为无法预览


def render_content_to_html(content: str, ext: str) -> str:
    """将文件内容渲染为 Markdown HTML（纯函数）。

    - 代码类文件（命中 CODE_LANGUAGES）：整体包进对应语言的 fenced code block
    - 其他文本（.md 等）：直接按 Markdown 渲染，支持代码块、表格、换行

    【fenced code block 是什么？】
    即 ```python ... ``` 这种围栏式代码块，浏览器端按 python 语法高亮。
    把源码整体包进去，页面就能像看代码编辑器一样展示源码。
    """
    lang = CODE_LANGUAGES.get(ext)  # 查扩展名对应的语言标识；没有则 None
    if lang:
        # 代码文件：用 f"```{lang}\n{content}\n```" 包成围栏代码块再渲染
        raw = markdown.markdown(
            f"```{lang}\n{content}\n```",
            extensions=["fenced_code"],  # 启用围栏代码块扩展
        )
    else:
        # 普通文本/Markdown：直接渲染
        # fenced_code=代码块, tables=表格, nl2br=换行即 <br>（更贴近阅读习惯）
        raw = markdown.markdown(
            content,
            extensions=["fenced_code", "tables", "nl2br"],
        )
    # 存储型 XSS 防护：markdown 默认原样保留文件里的原始 HTML 标签
    #（如 <script>、onerror 事件），渲染结果必须再过 bleach 白名单过滤，
    # 只保留 markdown 产物允许的标签/属性，危险协议（javascript: 等）一并剥除。
    return bleach.clean(
        raw,
        tags=_ALLOWED_TAGS,
        attributes=_ALLOWED_ATTRS,
        protocols=_ALLOWED_PROTOCOLS,
        strip=True,  # 不在白名单内的标签连同内容一起移除
    )

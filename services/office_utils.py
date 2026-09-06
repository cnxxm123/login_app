"""office_utils 模块（services 包）
Office 文档解析（纯逻辑层，不依赖 Flask，不处理 HTTP）。

职责：把 docx / xlsx / xls 解析成 HTML 片段，供 view 蓝图在网页内预览。
- render_docx_to_html()  Word 文档 → 段落/标题/表格渲染成 HTML
- render_xlsx_to_html()  Excel 工作簿 → 每个工作表渲染成 <table>

【为什么单独一个模块？】
解析 Office 文件属于"纯逻辑"，与 HTTP 交互无关，
按项目三层架构放进 services 包，view 蓝图只负责调用并拼 URL。

【依赖】
- python-docx  解析 .docx（段落/表格/标题级别）
- openpyxl     解析 .xlsx（单元格/合并单元格）
- xlrd         解析 .xls（旧版 Excel）
三个库都只在解析对应格式时才 import，不影响其它功能启动。
"""

import html  # 把特殊字符转义，防止文档内容里的 <script> 等注入页面

# 常用中文档的标题级别映射（Word 内置样式），其它样式一律当普通段落
_DOCX_HEADING_MAP = {
    "heading 1": 1,
    "heading 2": 2,
    "heading 3": 3,
    "heading 4": 4,
    "heading 5": 5,
    "heading 6": 6,
}


def _esc(text: str) -> str:
    """HTML 转义：文档里的 < > & 等字符原样显示，避免被当成标签解析。"""
    return html.escape(str(text or ""))


def render_docx_to_html(path: str) -> str | None:
    """把 .docx 渲染成 HTML（段落 → <p>，标题 → <h1~h6>，表格 → <table>）。

    用 python-docx 按文档顺序遍历"块"（段落与表格交替出现），
    遇到内置标题样式就渲染成对应级标题，否则渲染成段落；
    表格单元格里的段落会先合并成一段文本再放进 <td>。
    解析失败（文件损坏/密码保护等）返回 None，由调用方提示不可预览。
    """
    try:
        from docx import Document  # python-docx 的入口类
    except Exception:
        return None
    try:
        doc = Document(path)  # 打开文档（内存中解析，不修改原文件）
    except Exception:
        return None

    parts = []  # 收集渲染出的 HTML 片段
    # doc.element.body 以文档物理顺序列出所有块；python-docx 的 block_item 迭代器
    # 会按顺序交替 yield 段落与表格，正好还原"段落中夹表格"的排版。
    from docx.table import Table  # 表格类型
    from docx.text.paragraph import Paragraph  # 段落类型

    for block in doc.element.body.iterchildren():
        # 每个 XML 节点可能是 <w:p>（段落）或 <w:tbl>（表格），
        # 用对应类包装后统一按类型处理。
        if block.tag.endswith("}p"):
            para = Paragraph(block, doc)
            _render_docx_paragraph(parts, para)
        elif block.tag.endswith("}tbl"):
            table = Table(block, doc)
            _render_docx_table(parts, table)

    return "\n".join(parts)


def _render_docx_paragraph(parts: list, para) -> None:
    """把一个 Word 段落追加为 HTML 片段（标题→<hN>，普通→<p>）。"""
    style = (para.style.name or "").strip() if para.style else ""
    key = style.lower()
    text = "".join(run.text for run in para.runs).strip()  # 合并各 run 的文本
    if not text:  # 空段落（如分页、间距占位）跳过，保持版面干净
        return
    level = _DOCX_HEADING_MAP.get(key)  # 是内置标题样式才当标题
    if level:
        parts.append(f"<h{level}>{_esc(text)}</h{level}>")
    else:
        parts.append(f"<p>{_esc(text)}</p>")


def _render_docx_table(parts: list, table) -> None:
    """把一个 Word 表格追加为 HTML <table>。"""
    rows = []
    for row in table.rows:  # 遍历每一行
        cells = []
        for cell in row.cells:
            # 单元格里可能有多个段落，用 <br> 连接成一段文本
            cell_text = "<br>".join(
                "".join(run.text for run in p.runs) for p in cell.paragraphs
            ).strip()
            cells.append(f"<td>{_esc(cell_text)}</td>")
        rows.append("<tr>" + "".join(cells) + "</tr>")
    parts.append("<table><tbody>" + "".join(rows) + "</tbody></table>")


def render_xlsx_to_html(path: str) -> str | None:
    """把 Excel 工作簿渲染成 HTML（每个工作表一个 <table>）。

    按扩展名选择解析器：
    - .xlsx → openpyxl（read_only 流式读取，大文件也省内存）
    - .xls  → xlrd（旧格式）
    合并单元格会合并显示；没有数据的空工作表自动跳过。
    """
    ext = path.lower().rsplit(".", 1)[-1]
    if ext == "xlsx":
        return _render_xlsx_openpyxl(path)
    if ext == "xls":
        return _render_xls_xlrd(path)
    return None


def _sheet_block(title: str, rows_html: list) -> str:
    """把一个工作表拼成带标题的 HTML 块。"""
    body = "".join(rows_html)
    return (
        f"<h3>📄 {_esc(title)}</h3>"
        f"<table><tbody>{body}</tbody></table>"
    )


def _render_xlsx_openpyxl(path: str) -> str | None:
    """用 openpyxl 解析 .xlsx。"""
    try:
        from openpyxl import load_workbook
    except Exception:
        return None
    try:
        # read_only + data_only：流式读值；data_only 取公式计算结果（非公式文本）
        wb = load_workbook(path, read_only=True, data_only=True)
    except Exception:
        return None
    parts = []
    try:
        for ws in wb.worksheets:
            rows = list(ws.iter_rows(values_only=True))  # 值列表，None 表示空单元格
            # 跳过整表都为空的工作表
            if not any(any(c is not None for c in r) for r in rows):
                continue
            merged = _merged_ranges(ws)  # 合并单元格范围（{(行,列): 主单元格值范围}）
            parts.append(_sheet_block(ws.title or "工作表", _xlsx_rows_to_html(rows, merged)))
    finally:
        wb.close()  # read_only 模式必须关闭以释放文件句柄
    return "\n".join(parts) if parts else "<p>（工作簿为空）</p>"


def _merged_ranges(ws) -> dict:
    """收集工作表的合并单元格：返回 {被合并的(行,列): 主单元格(行,列)}。"""
    out = {}
    for rng in getattr(ws, "merged_cells", []) or []:  # 合并区域列表
        min_r, min_c, max_r, max_c = rng.min_row, rng.min_col, rng.max_row, rng.max_col
        for r in range(min_r, max_r + 1):
            for c in range(min_c, max_c + 1):
                out[(r - 1, c - 1)] = (min_r - 1, min_c - 1)  # 从 0 开始索引
    return out


def _xlsx_rows_to_html(rows: list, merged: dict) -> list:
    """把 openpyxl 的行值转成 HTML <tr>；合并单元格只显示主格，其余填空。"""
    out = []
    for r, row in enumerate(rows):
        cells = []
        for c, val in enumerate(row):
            anchor = merged.get((r, c))  # 该格是否被合并
            if anchor and anchor != (r, c):
                cells.append("<td></td>")  # 被合并的从属格：留空
                continue
            text = "" if val is None else _esc(val)
            cells.append(f"<td>{text}</td>")
        out.append("<tr>" + "".join(cells) + "</tr>")
    return out


def _render_xls_xlrd(path: str) -> str | None:
    """用 xlrd 解析 .xls（旧版 Excel 二进制格式）。"""
    try:
        import xlrd
    except Exception:
        return None
    try:
        # 只有老版本 xlrd 支持 .xls；formatting_info 仅旧版可用，不依赖它
        book = xlrd.open_workbook(path)
    except Exception:
        return None
    parts = []
    for sheet in book.sheets():  # 每个工作表
        if sheet.nrows == 0:
            continue
        rows_html = []
        for r in range(sheet.nrows):  # 遍历每一行
            cells = []
            for c in range(sheet.ncols):  # 遍历每一列
                cell = sheet.cell(r, c)
                # 按单元格类型取显示文本（数字/日期/字符串等）
                cells.append(f"<td>{_esc(_xls_cell_text(sheet, r, c, cell))}</td>")
            rows_html.append("<tr>" + "".join(cells) + "</tr>")
        parts.append(_sheet_block(sheet.name, rows_html))
    return "\n".join(parts) if parts else "<p>（工作簿为空）</p>"


def _xls_cell_text(sheet, r: int, c: int, cell) -> str:
    """把 xlrd 单元格转成显示文本：数字 → 原样、日期 → 格式化、其它 → 字符串。"""
    if cell.ctype == 2:  # 数字
        val = cell.value
        # 整数显示不带小数点（如 100 而非 100.0）
        return str(int(val)) if float(val).is_integer() else str(val)
    if cell.ctype == 3:  # 日期
        try:
            dt = xlrd.xldate_as_datetime(cell.value, sheet.book.datemode)
            return dt.strftime("%Y-%m-%d %H:%M")
        except Exception:
            return str(cell.value)
    return str(cell.value or "")


def render_office_to_html(path: str, ext: str) -> str | None:
    """统一入口：按扩展名分派到对应解析器。

    返回可直接嵌入页面的 HTML 片段；解析失败返回 None（调用方提示不可预览）。
    """
    if ext == ".docx":
        return render_docx_to_html(path)
    if ext in (".xlsx", ".xls"):
        return render_xlsx_to_html(path)
    return None

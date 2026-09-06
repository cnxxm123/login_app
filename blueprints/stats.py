"""stats 模块（blueprints 包）
磁盘占用统计蓝图：/stats 展示按文件类型 / 目录的占用可视化。

【本模块做什么】
- /stats   统计页：调用 stats_utils.disk_stats() 扫描 TEXT_DIR，
           把"按类型"与"按目录"两组数据传给模板渲染成可视化图表。
- 图表由模板里的 CSS 条形图实现（无第三方依赖，纯色块 + 百分比宽度），
   后端只负责算数与传值。

【与其它模块的分工】
- 统计计算全部委托给 services/stats_utils（纯逻辑层），本模块只处理 HTTP
"""

from flask import Blueprint, render_template

from services.stats_utils import disk_stats  # 磁盘统计（纯逻辑）

# 创建"统计"蓝图；模板里 url_for('stats.xxx') 的 stats 即此名字
stats_bp = Blueprint("stats", __name__)

# 文件类型 → 条形图颜色（模板据此给每种类型上色，未列出的类型用灰色兜底）
TYPE_COLORS = {
    "文本": "#667eea",
    "图片": "#f59e0b",
    "PDF": "#ef4444",
    "视频": "#10b981",
    "音频": "#8b5cf6",
    "Office": "#06b6d4",
    "其它": "#94a3b8",
}


@stats_bp.route("/stats")
def index():
    """磁盘占用统计页：按文件类型 + 按目录两种维度可视化。"""
    return render_template(
        "stats.html",
        stats=disk_stats(),
        type_colors=TYPE_COLORS,
    )

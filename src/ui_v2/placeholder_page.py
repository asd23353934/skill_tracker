"""
V2 主頁面（dashboard 暫版）
完全使用 components.py 的元件 + theme_v2 的 token，不寫死數值/顏色
版面遵守 docs/DESIGN_V2.md
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
)
from src.ui_v2.theme_v2 import V2Theme as T
from src.ui_v2.components import (
    StatCard, ServiceCard, MiniStatRow,
    LineChartCard, MiniLineChartCard, RingStat, Card, StatusChip,
    ArrowComboBox,
)


class PlaceholderPage(QWidget):
    """主 dashboard — 嚴格依照 DESIGN_V2 規範"""

    def __init__(self, parent, title: str = "技能總覽", subtitle: str = ""):
        super().__init__(parent)
        self._title = title
        self._build()

    # ════════════════════════════════════════════════════════
    # 主版面
    # ════════════════════════════════════════════════════════
    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(T.S_2XL, T.S_SM, T.S_2XL, T.S_2XL)
        root.setSpacing(T.S_LG)

        # 區塊主標
        root.addWidget(T.make_label(self._title, T.FONT_SECTION))

        # ── 上排：4 KPI + 折線圖 ──
        row1 = QHBoxLayout()
        row1.setSpacing(T.S_MD)
        row1.addLayout(self._kpi_row(), 5)
        row1.addWidget(self._chart_card(), 4)
        root.addLayout(row1, 4)

        # ── 下排：服務卡 + 右側統計 ──
        row2 = QHBoxLayout()
        row2.setSpacing(T.S_MD)
        row2.addLayout(self._services_grid(), 5)
        row2.addLayout(self._right_column(), 4)
        root.addLayout(row2, 5)

    # ════════════════════════════════════════════════════════
    # 上排：4 個 StatCard
    # ════════════════════════════════════════════════════════
    def _kpi_row(self):
        lay = QHBoxLayout()
        lay.setSpacing(T.S_MD)
        # (glyph, accent, label, metric, delta, positive)
        defs = [
            ("◆", T.PURPLE, "本週使用", "3,452", "+6.4%",  True),
            ("✦", T.BLUE,   "本月使用", "12,901", "-3.1%", False),
            ("◔", T.ORANGE, "即將冷卻", "14",    "+10.3%", True),
            ("◉", T.CYAN,   "已收藏",  "82",    "+2.0%",  True),
        ]
        for g, c, lab, m, d, p in defs:
            lay.addWidget(StatCard(g, c, lab, m, d, p), 1)
        return lay

    # ════════════════════════════════════════════════════════
    # 折線圖卡
    # ════════════════════════════════════════════════════════
    def _chart_card(self):
        # 假資料 — 0~1 normalized
        pts = [0.30, 0.45, 0.38, 0.62, 0.55, 0.72, 0.80, 0.65, 0.88, 0.74, 0.92, 0.70]
        x_labels = [f"{i}月" for i in range(1, 13)]

        year = ArrowComboBox()
        year.addItems(["2026", "2025", "2024"])
        year.setFixedHeight(T.BTN_H)
        year.setMinimumWidth(96)

        return LineChartCard(
            title="月平均使用次數",
            points=pts,
            x_labels=x_labels,
            color=T.CYAN,
            right_widget=year,
        )

    # ════════════════════════════════════════════════════════
    # 服務卡 2x2
    # ════════════════════════════════════════════════════════
    def _services_grid(self):
        grid = QGridLayout()
        grid.setHorizontalSpacing(T.S_MD)
        grid.setVerticalSpacing(T.S_MD)
        # (title, subtitle, value, unit, glyph, accent, primary)
        defs = [
            ("劍士技能", "主動 + 被動 共 24 項", "24", " 項", "◆", T.PURPLE, False),
            ("法師技能", "主動 + 被動 共 18 項", "18", " 項", "◆", T.BLUE,   False),
            ("弓箭手",   "主動 + 被動 共 16 項", "16", " 項", "✦", T.ORANGE, False),
            ("盜賊",     "主動 + 被動 共 20 項", "20", " 項", "◆", T.CYAN,   True),
        ]
        for i, (n, d, v, u, g, c, p) in enumerate(defs):
            grid.addWidget(
                ServiceCard(n, d, v, u, g, c, cta_text="查看", cta_primary=p),
                i // 2, i % 2,
            )
        return grid

    # ════════════════════════════════════════════════════════
    # 右側欄：上 = 圓環 + 小指標、下 = 兩張迷你折線
    # ════════════════════════════════════════════════════════
    def _right_column(self):
        col = QVBoxLayout()
        col.setSpacing(T.S_MD)

        col.addWidget(self._ring_card(), 2)

        mini = QHBoxLayout()
        mini.setSpacing(T.S_MD)
        mini.addWidget(MiniLineChartCard(
            title="使用趨勢",
            points=[0.2, 0.35, 0.3, 0.5, 0.6, 0.55, 0.78],
            color=T.GREEN,
            status_text="良好",
        ), 1)
        mini.addWidget(MiniLineChartCard(
            title="冷卻誤差",
            points=[0.7, 0.6, 0.65, 0.5, 0.55, 0.4, 0.35],
            color=T.RED,
            status_text="警戒",
        ), 1)
        col.addLayout(mini, 2)
        return col

    # ── 圓環卡（命中率）+ 兩個 MiniStatRow ──
    def _ring_card(self):
        card = Card()
        L = card.layout()
        L.setSpacing(T.S_MD)

        head = QHBoxLayout()
        head.addWidget(T.make_label("命中率分析", T.FONT_CARD_TITLE))
        head.addStretch()
        head.addWidget(StatusChip("WEEK", T.CYAN))
        L.addLayout(head)

        body = QHBoxLayout()
        body.setSpacing(T.S_LG)
        body.addWidget(RingStat(0.78, "命中率", "78%", T.CYAN, 110), 0)

        meta = QVBoxLayout()
        meta.setSpacing(T.S_SM)
        meta.addWidget(MiniStatRow("◆", T.PURPLE, "成功施放", "324"))
        meta.addWidget(MiniStatRow("✦", T.RED,    "失敗次數", "92"))
        body.addLayout(meta, 1)

        L.addLayout(body)
        L.addStretch()
        return card

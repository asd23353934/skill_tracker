"""
V2 可重用元件 — 全部依 docs/DESIGN_V2.md
不准在頁面層直接寫 QSS 樣板；用本模組或 theme_v2 的 token
"""

from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QWidget, QComboBox,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QColor, QPen, QPainterPath, QPolygon
from PySide6.QtCore import QPoint
from src.ui_v2.theme_v2 import V2Theme as T
from src.ui_v2.lucide import lucide_pixmap


# ════════════════════════════════════════════════════════════
# ArrowComboBox — 在右側自繪向下三角箭頭
# ════════════════════════════════════════════════════════════

class ArrowComboBox(QComboBox):
    """覆蓋 paintEvent 在右側補上小三角（QSS border-trick 在 Qt 不穩）"""
    def paintEvent(self, e):  # noqa: N802
        super().paintEvent(e)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setBrush(QColor(T.TEXT_DIM))
        p.setPen(Qt.PenStyle.NoPen)
        w, h = self.width(), self.height()
        cx = w - 12
        cy = h // 2
        tri = QPolygon([
            QPoint(cx - 4, cy - 2),
            QPoint(cx + 4, cy - 2),
            QPoint(cx,     cy + 3),
        ])
        p.drawPolygon(tri)
        p.end()


# ════════════════════════════════════════════════════════════
# IconBadge — 統一的彩色圖示徽章
# ════════════════════════════════════════════════════════════

class IconBadge(QFrame):
    """彩色圓角圖示徽章（規範 §5.3）

    accent 色塊（半透明）+ accent 色 Lucide 圖示
    glyph 參數現在接受 Lucide icon 名稱（例如 "swords"、"skull"）
    """
    def __init__(self, glyph: str, accent: str, size: int = None, parent=None):
        super().__init__(parent)
        size = size or T.ICON_BADGE
        self._glyph  = glyph
        self._accent = accent
        self._size   = size
        self.setFixedSize(size, size)
        bg_alpha = T.alpha(accent, 38)
        self.setStyleSheet(
            f"QFrame {{ background: {bg_alpha};"
            f" border-radius: {T.R_MD}px; }}"
        )

    def paintEvent(self, e):  # noqa: N802
        super().paintEvent(e)
        icon_size = max(10, int(self._size * 0.55))
        pix = lucide_pixmap(self._glyph, self._accent, icon_size, stroke=1.8)
        p = QPainter(self)
        x = (self._size - icon_size) // 2
        y = (self._size - icon_size) // 2
        p.drawPixmap(x, y, pix)
        p.end()


# ════════════════════════════════════════════════════════════
# Card — 基礎卡片容器
# ════════════════════════════════════════════════════════════

class Card(QFrame):
    """基礎卡片（§6.1）"""
    def __init__(self, parent=None, padding: int = None):
        super().__init__(parent)
        self.setObjectName("v2_card")
        self.setStyleSheet(
            f"QFrame#v2_card {{ background: {T.BG_SURFACE};"
            f" border: none; border-radius: {T.R_LG}px; }}"
        )
        self._main = QVBoxLayout(self)
        p = padding if padding is not None else T.S_LG
        self._main.setContentsMargins(p, p, p, p)
        self._main.setSpacing(T.S_SM)

    def layout(self):
        return self._main


# ════════════════════════════════════════════════════════════
# DeltaChip — 變化率小標籤
# ════════════════════════════════════════════════════════════

class DeltaChip(QLabel):
    """變化率 chip（§6.4）— positive=GREEN / negative=RED"""
    def __init__(self, text: str, positive: bool, parent=None):
        super().__init__(text, parent)
        color = T.GREEN if positive else T.RED
        self.setStyleSheet(
            f"QLabel {{ color: {color};"
            f" background: {T.alpha(color, 38)};"
            f" border-radius: {T.CHIP_H // 2}px;"
            f" padding: 0 10px; font-size: 11px; font-weight: 700;"
            f" min-height: {T.CHIP_H}px; max-height: {T.CHIP_H}px; }}"
        )
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)


class StatusChip(QLabel):
    """狀態 chip（中性色）"""
    def __init__(self, text: str, accent: str = None, parent=None):
        super().__init__(text, parent)
        accent = accent or T.TEXT_DIM
        self.setStyleSheet(
            f"QLabel {{ color: {accent};"
            f" background: {T.alpha(accent, 38)};"
            f" border-radius: {T.CHIP_H // 2}px;"
            f" padding: 0 10px; font-size: 10px; font-weight: 700;"
            f" letter-spacing: 1px;"
            f" min-height: {T.CHIP_H}px; max-height: {T.CHIP_H}px; }}"
        )
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)


# ════════════════════════════════════════════════════════════
# StatCard — 4 段式 KPI 卡（§6.2）
# ════════════════════════════════════════════════════════════

class StatCard(Card):
    """4 段式：icon → label → metric → delta（垂直，靠上對齊，固定高）"""

    def __init__(self, glyph: str, accent: str,
                 label: str, metric: str, delta: str, delta_positive: bool,
                 parent=None):
        super().__init__(parent)
        self.setFixedHeight(T.CARD_STAT_H)
        L = self._main
        L.setSpacing(T.S_SM)
        L.setAlignment(Qt.AlignmentFlag.AlignTop)

        L.addWidget(IconBadge(glyph, accent))
        L.addSpacing(T.S_XS)
        L.addWidget(T.make_label(label, T.FONT_LABEL))
        L.addWidget(T.make_label(metric, T.FONT_METRIC))
        L.addWidget(self._delta_row(delta, delta_positive))
        L.addStretch()

    def _delta_row(self, text, positive):
        wrap = QWidget()
        h = QHBoxLayout(wrap)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(0)
        h.addWidget(DeltaChip(text, positive))
        h.addStretch()
        return wrap


# ════════════════════════════════════════════════════════════
# ServiceCard — 標題+icon+價格+CTA（§6.3）
# ════════════════════════════════════════════════════════════

class ServiceCard(Card):
    def __init__(self, title: str, subtitle: str, value: str, unit: str,
                 glyph: str, accent: str,
                 cta_text: str = "查看詳細", cta_primary: bool = False,
                 parent=None):
        super().__init__(parent)
        self.setFixedHeight(T.CARD_SERVICE_H)
        L = self._main
        L.setSpacing(T.S_SM)

        # 上排：標題群組 + icon
        top = QHBoxLayout()
        top.setSpacing(T.S_MD)
        text_box = QVBoxLayout()
        text_box.setSpacing(2)
        text_box.addWidget(T.make_label(title, T.FONT_CARD_TITLE))
        text_box.addWidget(T.make_label(subtitle, T.FONT_CAPTION))
        top.addLayout(text_box, 1)
        top.addWidget(IconBadge(glyph, accent, 36), 0, Qt.AlignmentFlag.AlignTop)
        L.addLayout(top)

        # 底排：金額 + CTA
        bot = QHBoxLayout()
        bot.setSpacing(T.S_XS)
        price = QHBoxLayout()
        price.setSpacing(2)
        price.addWidget(T.make_label(value, T.FONT_METRIC_SM))
        price.addWidget(T.make_label(unit, T.FONT_CAPTION))
        bot.addLayout(price)
        bot.addStretch()
        bot.addWidget(self._make_cta(cta_text, cta_primary))
        L.addLayout(bot)

    def _make_cta(self, text, primary):
        btn = QPushButton(text)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFixedHeight(28)
        if primary:
            btn.setStyleSheet(
                f"QPushButton {{ background: {T.ORANGE}; color: #ffffff;"
                f" border: none; border-radius: 14px;"
                f" padding: 0 14px; font-size: 11px; font-weight: 600; }}"
                f"QPushButton:hover {{ background: #ff9d5a; }}"
            )
        else:
            btn.setStyleSheet(
                f"QPushButton {{ background: transparent; color: {T.TEXT};"
                f" border: 1px solid {T.BORDER_HOVER};"
                f" border-radius: 14px; padding: 0 14px;"
                f" font-size: 11px; font-weight: 600; }}"
                f"QPushButton:hover {{ background: {T.BG_HOVER};"
                f" color: {T.TEXT_HI}; }}"
            )
        return btn


# ════════════════════════════════════════════════════════════
# MiniStatRow — 小指標列（icon | 標籤 | 數字）
# ════════════════════════════════════════════════════════════

class MiniStatRow(Card):
    def __init__(self, glyph: str, accent: str, label: str, value: str, parent=None):
        super().__init__(parent, padding=T.S_MD)
        self._main.setDirection(QVBoxLayout.Direction.LeftToRight)
        self._main.setSpacing(T.S_MD)

        self._main.addWidget(IconBadge(glyph, accent, 30))
        self._main.addWidget(T.make_label(label, T.FONT_BODY))
        self._main.addStretch()
        self._main.addWidget(T.make_label(value, T.FONT_METRIC_SM))


# ════════════════════════════════════════════════════════════
# LineChartCard — 自繪折線圖卡片
# ════════════════════════════════════════════════════════════

class _LineChartArea(QFrame):
    """自繪折線圖區（QPainter）"""

    def __init__(self, points: list[float], color: str, fill: bool = True, parent=None):
        super().__init__(parent)
        self._points = points        # 0-1 normalized values
        self._color  = QColor(color)
        self._fill   = fill
        self.setMinimumHeight(120)
        self.setStyleSheet("background: transparent;")

    def paintEvent(self, e):  # noqa: N802
        if not self._points:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        pad_x, pad_y = 6, 8
        chart_w, chart_h = w - pad_x * 2, h - pad_y * 2

        n = len(self._points)
        step = chart_w / max(n - 1, 1)

        # 計算座標
        coords = [
            (pad_x + i * step, pad_y + (1 - v) * chart_h)
            for i, v in enumerate(self._points)
        ]

        # 填色（選用）
        if self._fill:
            path = QPainterPath()
            path.moveTo(coords[0][0], pad_y + chart_h)
            for x, y in coords:
                path.lineTo(x, y)
            path.lineTo(coords[-1][0], pad_y + chart_h)
            path.closeSubpath()
            fill_color = QColor(self._color)
            fill_color.setAlpha(60)
            p.setBrush(fill_color)
            p.setPen(Qt.PenStyle.NoPen)
            p.drawPath(path)

        # 線
        pen = QPen(self._color, 2)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)

        path = QPainterPath()
        path.moveTo(*coords[0])
        for x, y in coords[1:]:
            path.lineTo(x, y)
        p.drawPath(path)

        # 端點圓點
        p.setBrush(self._color)
        p.setPen(Qt.PenStyle.NoPen)
        for x, y in coords:
            p.drawEllipse(int(x - 2), int(y - 2), 4, 4)

        p.end()


class LineChartCard(Card):
    """折線圖卡片（標題列 + 折線 + 底部 X 軸）"""

    def __init__(self, title: str, points: list[float], x_labels: list[str] | None,
                 color: str, right_widget: QWidget = None, parent=None):
        super().__init__(parent)
        L = self._main
        L.setSpacing(T.S_MD)

        head = QHBoxLayout()
        head.addWidget(T.make_label(title, T.FONT_CARD_TITLE))
        head.addStretch()
        if right_widget:
            head.addWidget(right_widget)
        L.addLayout(head)

        L.addWidget(_LineChartArea(points, color), 1)

        if x_labels:
            row = QHBoxLayout()
            row.setSpacing(0)
            for lab in x_labels:
                l = T.make_label(lab, T.FONT_CAPTION)
                l.setAlignment(Qt.AlignmentFlag.AlignCenter)
                T.apply_font(l, T.FONT_LABEL, color_override=T.TEXT_MUTED)
                row.addWidget(l, 1)
            L.addLayout(row)


class MiniLineChartCard(Card):
    """迷你折線卡（標題 + 狀態 chip + 折線）"""
    def __init__(self, title: str, points: list[float],
                 color: str, status_text: str, parent=None):
        super().__init__(parent, padding=T.S_MD)
        L = self._main
        L.setSpacing(T.S_SM)

        head = QHBoxLayout()
        head.addWidget(T.make_label(title, T.FONT_CARD_TITLE))
        head.addStretch()
        head.addWidget(StatusChip(status_text, color))
        L.addLayout(head)

        chart = _LineChartArea(points, color)
        chart.setMinimumHeight(60)
        L.addWidget(chart, 1)


# ════════════════════════════════════════════════════════════
# RingStat — 自繪圓環指標
# ════════════════════════════════════════════════════════════

class RingStat(QFrame):
    """圓環指標（QPainter 自繪）"""
    def __init__(self, percent: float, label: str, value_text: str,
                 color: str = None, size: int = 110, parent=None):
        super().__init__(parent)
        self._pct   = max(0.0, min(1.0, percent))
        self._label = label
        self._value = value_text
        self._color = QColor(color or T.CYAN)
        self.setFixedSize(size, size)

    def paintEvent(self, e):  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w = self.width()
        ring_w = 6
        rect = (ring_w / 2 + 1, ring_w / 2 + 1,
                w - ring_w - 2, w - ring_w - 2)

        # 背景環
        track = QPen(QColor(T.BG_HOVER), ring_w)
        track.setCapStyle(Qt.PenCapStyle.FlatCap)
        p.setPen(track)
        p.drawArc(int(rect[0]), int(rect[1]), int(rect[2]), int(rect[3]),
                  0, 360 * 16)

        # 進度環
        pen = QPen(self._color, ring_w)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        span = int(-360 * 16 * self._pct)
        p.drawArc(int(rect[0]), int(rect[1]), int(rect[2]), int(rect[3]),
                  90 * 16, span)

        # 中央文字（label 在上、value 較大在下，間距留足）
        font = self.font()
        font.setBold(True)

        # Label
        font.setPointSize(8)
        font.setLetterSpacing(font.SpacingType.AbsoluteSpacing, 1)
        p.setFont(font)
        p.setPen(QColor(T.TEXT_DIM))
        label_top = int(w * 0.28)
        label_h   = int(w * 0.18)
        p.drawText(0, label_top, w, label_h,
                   Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
                   self._label)

        # Value
        font.setPointSize(15)
        font.setLetterSpacing(font.SpacingType.AbsoluteSpacing, 0)
        p.setFont(font)
        p.setPen(QColor(T.TEXT_HI))
        p.drawText(0, label_top + label_h, w, int(w * 0.30),
                   Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
                   self._value)

        p.end()

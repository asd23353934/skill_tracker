"""
標題列元件 — PyDracula 風格 PySide6 版本
平坦深色橫幅（無裝飾線條），可拖曳移動視窗
右側整合視窗控制按鈕（最小化 / 最大化 / 關閉）
"""

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QPushButton, QFrame,
)
from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QPainter, QPen, QColor
from src.ui.theme import AppTheme


class _WindowCtrlBtn(QPushButton):
    """自定義繪製視窗控制按鈕 — QPainter 確保三個按鈕符號視覺大小完全一致"""

    MINIMIZE = "minimize"
    MAXIMIZE = "maximize"
    RESTORE  = "restore"
    CLOSE    = "close"

    def __init__(self, icon_type: str, parent=None):
        super().__init__(parent)
        self._icon_type = icon_type
        self._hovered   = False
        self.setFlat(True)

    def set_icon_type(self, icon_type: str):
        self._icon_type = icon_type
        self.update()

    def enterEvent(self, event):
        self._hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, event):  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        # 懸停背景
        if self._hovered:
            bg_hex = "#c42b1c" if self._icon_type == self.CLOSE else "#3a4556"
            painter.fillRect(0, 0, w, h, QColor(bg_hex))

        icon_color = QColor("#ffffff" if self._hovered else "#d0d8e8")
        pen = QPen(icon_color, 1.5)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.MiterJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        cx, cy = w / 2.0, h / 2.0

        if self._icon_type == self.MINIMIZE:
            painter.drawLine(QPointF(cx - 6, cy), QPointF(cx + 6, cy))

        elif self._icon_type == self.MAXIMIZE:
            painter.drawRect(QRectF(cx - 6, cy - 5, 12, 10))

        elif self._icon_type == self.RESTORE:
            # 後方方框
            painter.drawRect(QRectF(cx - 1, cy - 7, 9, 8))
            # 用 header 背景色填充前方方框區域（讓前框蓋住後框的左下角）
            bg_fill = "#3a4556" if self._hovered else AppTheme.BG_SECONDARY
            painter.setBrush(QColor(bg_fill))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRect(QRectF(cx - 8, cy - 1, 9, 8))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(pen)
            # 前方方框邊框
            painter.drawRect(QRectF(cx - 8, cy - 1, 9, 8))

        elif self._icon_type == self.CLOSE:
            painter.drawLine(QPointF(cx - 5, cy - 5), QPointF(cx + 5, cy + 5))
            painter.drawLine(QPointF(cx + 5, cy - 5), QPointF(cx - 5, cy + 5))


class Header(QWidget):
    """PyDracula 風格平坦深色標題列 — 可拖曳 + 視窗控制按鈕"""

    # 按鈕統一高度（配合 HEADER_HEIGHT=44，留 8px 上下 padding）
    _BTN_H  = 28   # 操作按鈕高度
    _CTRL_W = 38   # 視窗控制按鈕寬（三個按鈕統一寬度）
    _CTRL_H = 28   # 視窗控制按鈕高

    def __init__(self, parent, app):
        """初始化標題列

        Args:
            parent: 父元件
            app:    App 主應用實例
        """
        super().__init__(parent)
        self.app = app
        self._drag_pos = None
        self.setFixedHeight(AppTheme.HEADER_HEIGHT)
        self._build_ui()

    def _build_ui(self):
        """建構 UI — 平坦深色列，底部細線分隔"""
        self.setObjectName("app_header")
        self.setStyleSheet(
            f"QWidget#app_header {{"
            f" background-color: {AppTheme.BG_SECONDARY};"
            f" border-bottom: 1px solid {AppTheme.BORDER_GOLD_HAIRLINE}; }}"
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 4, 0)
        layout.setSpacing(6)

        # ===== 左側：標題 + 副標 + 配置名稱 =====
        title_lbl = QLabel("🍁 技能追蹤器")
        title_lbl.setStyleSheet(
            f"color: {AppTheme.GOLD_LIGHT};"
            f" font-size: 14px; font-weight: bold;"
            f" background: transparent; border: none;"
        )
        layout.addWidget(title_lbl)

        subtitle_lbl = QLabel("Artale 楓之谷")
        subtitle_lbl.setStyleSheet(
            f"color: {AppTheme.TEXT_MUTED}; font-size: 11px;"
            f" background: transparent; border: none;"
        )
        layout.addWidget(subtitle_lbl)

        self.profile_label = QLabel(f"📋 {self.app.current_profile_name}")
        self.profile_label.setStyleSheet(
            f"color: {AppTheme.TEXT_MUTED}; font-size: 11px;"
            f" background: transparent; border: none;"
        )
        layout.addWidget(self.profile_label)

        layout.addStretch()

        # ===== 中右：快捷鍵提示 =====
        self.hotkey_hint = QLabel("")
        self.hotkey_hint.setStyleSheet(
            f"color: {AppTheme.ACCENT_GREEN}; font-size: 11px; font-weight: bold;"
            f" background: transparent; border: none;"
        )
        layout.addWidget(self.hotkey_hint)

        # 更新按鈕（初始隱藏）
        self.update_btn = QPushButton("⬆ 新版本")
        self.update_btn.setFixedHeight(self._BTN_H)
        self.update_btn.clicked.connect(self.app.show_update_dialog)
        self.update_btn.setStyleSheet(
            f"QPushButton {{ background: {AppTheme.ACCENT_GREEN}; color: white;"
            f" border: none; border-radius: 4px;"
            f" padding: 0 8px; font-size: 11px; font-weight: bold; }}"
            f"QPushButton:hover {{ background: {AppTheme.ACCENT_GREEN_HOVER}; }}"
        )
        self.update_btn.hide()
        layout.addWidget(self.update_btn)

        # 清空按鍵
        clear_btn = QPushButton("清空按鍵")
        clear_btn.setFixedHeight(self._BTN_H)
        clear_btn.clicked.connect(self.app.clear_all_hotkeys)
        clear_btn.setStyleSheet(
            f"QPushButton {{ background: {AppTheme.ACCENT_RED}; color: white;"
            f" border: none; border-radius: 4px;"
            f" padding: 0 8px; font-size: 11px; font-weight: bold; }}"
            f"QPushButton:hover {{ background: #dc2626; }}"
        )
        layout.addWidget(clear_btn)

        # 配置管理
        profile_btn = QPushButton("💾 配置管理")
        profile_btn.setFixedHeight(self._BTN_H)
        profile_btn.clicked.connect(self.app.show_profile_manager)
        profile_btn.setStyleSheet(
            f"QPushButton {{ background: {AppTheme.ACCENT_PURPLE}; color: white;"
            f" border: none; border-radius: 4px;"
            f" padding: 0 8px; font-size: 11px; font-weight: bold; }}"
            f"QPushButton:hover {{ background: #7c3aed; }}"
        )
        layout.addWidget(profile_btn)

        # ===== 全選按鈕組（高度嚴格限制，不撐高 header）=====
        toggle_group = QFrame()
        toggle_group.setObjectName("toggle_group")
        toggle_group.setFixedHeight(self._BTN_H)
        toggle_group.setStyleSheet(
            f"QFrame#toggle_group {{"
            f" background: {AppTheme.BG_TERTIARY};"
            f" border: 1px solid {AppTheme.GOLD_MUTED};"
            f" border-radius: 4px; }}"
        )
        tg_layout = QHBoxLayout(toggle_group)
        tg_layout.setContentsMargins(6, 0, 6, 0)
        tg_layout.setSpacing(2)

        tg_lbl = QLabel("全選")
        tg_lbl.setStyleSheet(
            f"color: {AppTheme.TEXT_MUTED}; font-size: 10px;"
            f" background: transparent; border: none;"
        )
        tg_layout.addWidget(tg_lbl)

        toggle_defs = [
            ("常駐",    "permanent", AppTheme.ACCENT_YELLOW, "#e5a800", "#000000"),
            ("循環",    "loop",      AppTheme.ACCENT_GREEN,  "#0d9668", "#ffffff"),
            ("提前提示", "alert",    AppTheme.ACCENT_ORANGE, "#e07a2a", "#ffffff"),
        ]
        for text, key, color, hover, fg in toggle_defs:
            tb = QPushButton(text)
            tb.setFixedHeight(20)
            tb.clicked.connect(
                lambda checked=False, k=key: self.app.toggle_all(k)
            )
            tb.setStyleSheet(
                f"QPushButton {{ background: {color}; color: {fg};"
                f" border: none; border-radius: 3px;"
                f" padding: 0 6px; font-size: 10px; font-weight: bold; }}"
                f"QPushButton:hover {{ background: {hover}; }}"
            )
            tg_layout.addWidget(tb)

        layout.addWidget(toggle_group)
        layout.addSpacing(4)

        # ===== 右側：視窗控制按鈕（Windows 11 風格）=====
        layout.addSpacing(8)   # 與左側操作按鈕的視覺隔離

        min_btn = _WindowCtrlBtn(_WindowCtrlBtn.MINIMIZE)
        min_btn.setFixedSize(self._CTRL_W, self._CTRL_H)
        min_btn.setToolTip("最小化")
        min_btn.clicked.connect(self._on_minimize)
        layout.addWidget(min_btn)

        self.max_btn = _WindowCtrlBtn(_WindowCtrlBtn.MAXIMIZE)
        self.max_btn.setFixedSize(self._CTRL_W, self._CTRL_H)
        self.max_btn.setToolTip("最大化")
        self.max_btn.clicked.connect(self._toggle_maximize)
        layout.addWidget(self.max_btn)

        close_btn = _WindowCtrlBtn(_WindowCtrlBtn.CLOSE)
        close_btn.setFixedSize(self._CTRL_W, self._CTRL_H)
        close_btn.setToolTip("關閉")
        close_btn.clicked.connect(self.app.close)
        layout.addWidget(close_btn)

    # --------------------------------------------------
    # 視窗控制
    # --------------------------------------------------

    def _ctrl_btn_style(self, close: bool = False, font_size: int = 14) -> str:
        """視窗控制按鈕 QSS — Windows 11 風格（Segoe UI 字型確保符號渲染清晰）

        Args:
            close:     True 表示關閉按鈕（hover 紅色）
            font_size: 字型大小（─ 需較大以補足視覺重量）
        """
        hover_bg = "#c42b1c" if close else "#2d3748"
        hover_fg = "#ffffff" if close else AppTheme.TEXT_PRIMARY
        return (
            f"QPushButton {{ background: transparent; color: #c8d0dc;"
            f" border: none; border-radius: 0px;"
            f" font-family: 'Segoe UI', 'Arial'; font-size: {font_size}px; }}"
            f"QPushButton:hover {{ background: {hover_bg}; color: {hover_fg}; }}"
        )

    def _on_minimize(self):
        self.window().showMinimized()

    def _toggle_maximize(self):
        win = self.window()
        if win.isMaximized():
            win.showNormal()
            self.max_btn.set_icon_type(_WindowCtrlBtn.MAXIMIZE)
            self.max_btn.setToolTip("最大化")
        else:
            win.showMaximized()
            self.max_btn.set_icon_type(_WindowCtrlBtn.RESTORE)
            self.max_btn.setToolTip("還原視窗")

    # --------------------------------------------------
    # 拖曳移動視窗
    # --------------------------------------------------

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = (
                event.globalPosition().toPoint()
                - self.window().frameGeometry().topLeft()
            )
            event.accept()

    def mouseMoveEvent(self, event):
        if (event.buttons() == Qt.MouseButton.LeftButton
                and self._drag_pos is not None
                and not self.window().isMaximized()):
            self.window().move(
                event.globalPosition().toPoint() - self._drag_pos
            )
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._toggle_maximize()

    # ==================== 公開方法 ====================

    def show_update_button(self):
        self.update_btn.show()

    def update_profile_name(self, name: str):
        self.profile_label.setText(f"📋 {name}")

    def show_hotkey_hint(self, text: str, color: str):
        self.hotkey_hint.setText(text)
        self.hotkey_hint.setStyleSheet(
            f"color: {color}; font-size: 11px; font-weight: bold;"
            f" background: transparent; border: none;"
        )

    def clear_hotkey_hint(self):
        self.hotkey_hint.setText("")

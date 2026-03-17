"""
Toast 通知元件 — PySide6 版本
左下角彈出式通知，支援成功/失敗顏色，可手動關閉，自動淡出
"""

from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, QTimer
from src.ui.theme import AppTheme


class Toast(QFrame):
    """左下角浮動通知元件"""

    # 顏色對應
    COLORS = {
        "success": {"bg": "#0d3320", "border": "#10b981", "text": "#6ee7b7"},
        "error":   {"bg": "#3b1111", "border": "#ef4444", "text": "#fca5a5"},
        "info":    {"bg": "#1a2744", "border": "#3b82f6", "text": "#93bbfd"},
    }

    # 自動消失時間 (ms)
    AUTO_DISMISS_MS = 3000

    def __init__(self, parent, message: str, toast_type: str = "success"):
        """建立 Toast 通知

        Args:
            parent:     父元件（主視窗 QMainWindow）
            message:    通知文字
            toast_type: 類型 ("success" / "error" / "info")
        """
        super().__init__(parent)
        colors = self.COLORS.get(toast_type, self.COLORS["info"])
        self._dismiss_timer = None

        self.setObjectName("toast_frame")
        self.setStyleSheet(
            f"QFrame#toast_frame {{"
            f" background-color: {colors['bg']};"
            f" border: 1px solid {colors['border']};"
            f" border-radius: 8px; }}"
        )

        # 圖示對應
        icon_map = {"success": "✓", "error": "✕", "info": "ℹ"}
        icon = icon_map.get(toast_type, "ℹ")

        # 內容佈局
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)

        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet(
            f"color: {colors['border']}; font-size: 14px; font-weight: bold;"
            f" background: transparent; border: none;"
        )
        layout.addWidget(icon_lbl)

        msg_lbl = QLabel(message)
        msg_lbl.setStyleSheet(
            f"color: {colors['text']}; font-size: 12px;"
            f" background: transparent; border: none;"
        )
        layout.addWidget(msg_lbl)

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(20, 20)
        close_btn.clicked.connect(self.dismiss)
        close_btn.setStyleSheet(
            f"QPushButton {{"
            f" background: transparent; border: none;"
            f" color: {colors['text']}; font-size: 11px; }}"
            f"QPushButton:hover {{ color: {colors['border']}; }}"
        )
        layout.addWidget(close_btn)

        self.adjustSize()
        self.hide()

        # 自動消失計時器
        self._dismiss_timer = QTimer(self)
        self._dismiss_timer.setSingleShot(True)
        self._dismiss_timer.timeout.connect(self.dismiss)
        self._dismiss_timer.start(self.AUTO_DISMISS_MS)

    def dismiss(self):
        """關閉通知"""
        if self._dismiss_timer:
            self._dismiss_timer.stop()
        self.hide()
        self.deleteLater()


class ToastManager:
    """Toast 管理器 — 管理多個 Toast 的定位與堆疊"""

    MARGIN_BOTTOM = 16
    MARGIN_LEFT   = 16
    GAP           = 8

    def __init__(self, parent):
        """初始化

        Args:
            parent: 主視窗（QMainWindow）
        """
        self.parent  = parent
        self._toasts: list = []

    def show(self, message: str, toast_type: str = "success"):
        """顯示一個 Toast 通知

        Args:
            message:    文字內容
            toast_type: "success" / "error" / "info"
        """
        toast = Toast(self.parent, message, toast_type)

        # 覆寫 dismiss，在銷毀後重新計算堆疊位置
        original_dismiss = toast.dismiss

        def _dismiss_and_reposition():
            if toast in self._toasts:
                self._toasts.remove(toast)
            original_dismiss()
            self._reposition()

        toast.dismiss = _dismiss_and_reposition

        self._toasts.append(toast)
        toast.show()
        toast.adjustSize()
        self._reposition()

    def _reposition(self):
        """重新計算所有 Toast 的位置（從下往上堆疊）"""
        try:
            parent_h = self.parent.height()
        except Exception:
            return

        y_offset = self.MARGIN_BOTTOM
        for toast in reversed(self._toasts):
            try:
                if not toast.isVisible():
                    continue
                toast.adjustSize()
                toast_w = max(toast.width(), 200)
                toast_h = toast.height()
                x = self.MARGIN_LEFT
                y = parent_h - y_offset - toast_h
                toast.setGeometry(x, y, toast_w, toast_h)
                toast.raise_()
                y_offset += toast_h + self.GAP
            except Exception:
                pass

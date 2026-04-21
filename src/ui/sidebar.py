"""
固定式側邊欄導航元件 — PyDracula 風格 PySide6 版本
頂部漢堡 icon、中段 icon-only 頁面導航、底部設定按鈕
Active 狀態：左側 3px 金色細線 + 淡色背景
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QFrame
from PySide6.QtCore import Qt
from src.ui.theme import AppTheme


class Sidebar(QWidget):
    """固定寬度側邊欄導航 — PyDracula 風格"""

    # 頁面定義：(page_name, icon, tooltip)
    PAGES = [
        ("skill",   "🍁", "技能倒數"),
        ("monster", "👾", "怪物重生"),
        ("overlay", "🖼️", "覆蓋圖片"),
        ("potion",  "💰", "練功水錢"),
        ("mapleworld", "🍄", "MapleWorld 資源"),
    ]

    def __init__(self, parent, on_page_change, app):
        """初始化側邊欄

        Args:
            parent:         父元件
            on_page_change: 頁面切換回呼 callable(page_name: str)
            app:            App 主應用實例（用於底部設定按鈕）
        """
        super().__init__(parent)
        self.on_page_change = on_page_change
        self.app_ref        = app
        self.current_page   = "skill"
        self._items         = {}   # {page_name: QPushButton}

        self._build_ui()

    def _build_ui(self):
        """建構側邊欄 UI"""
        self.setObjectName("sidebar_root")
        self.setAutoFillBackground(True)
        self.setStyleSheet(
            f"Sidebar, QWidget#sidebar_root {{"
            f" background-color: {AppTheme.SIDEBAR_BG}; }}"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addSpacing(8)

        # ===== 中段：頁面導航按鈕（統一 40px 高）=====
        for page_name, icon, tooltip in self.PAGES:
            btn = QPushButton(icon)
            btn.setFixedSize(AppTheme.SIDEBAR_COLLAPSED, 40)
            btn.setToolTip(tooltip)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked=False, p=page_name: self._on_click(p))

            self._apply_btn_state(btn, page_name == self.current_page)
            self._items[page_name] = btn
            layout.addWidget(btn)
            layout.addSpacing(2)

        layout.addStretch()

        # ===== 底部：設定按鈕 =====
        settings_btn = QPushButton("⚙")
        settings_btn.setFixedSize(AppTheme.SIDEBAR_COLLAPSED, 40)
        settings_btn.setToolTip("設定")
        settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        settings_btn.clicked.connect(lambda: self.app_ref.show_settings())
        settings_btn.setStyleSheet(self._inactive_style())
        layout.addWidget(settings_btn)

        # 右側金色細線（1px 寬 QFrame 貼右邊）
        right_border = QFrame(self)
        right_border.setFrameShape(QFrame.Shape.VLine)
        right_border.setStyleSheet(
            f"color: {AppTheme.GOLD_MUTED}; background: {AppTheme.GOLD_MUTED};"
        )
        right_border.setFixedWidth(1)
        self._right_border = right_border

    def resizeEvent(self, event):  # noqa: N802
        """視窗縮放時將右側邊框置右"""
        super().resizeEvent(event)
        if hasattr(self, "_right_border"):
            self._right_border.setGeometry(
                self.width() - 1, 0, 1, self.height()
            )

    # --------------------------------------------------
    # 樣式生成
    # --------------------------------------------------

    def _active_style(self) -> str:
        """Active 頁面按鈕 QSS — 左側 3px 金色線 + 淡色背景"""
        return (
            f"QPushButton {{"
            f" background-color: {AppTheme.SIDEBAR_HOVER_BG};"
            f" color: {AppTheme.GOLD_LIGHT};"
            f" border: none;"
            f" border-left: 3px solid {AppTheme.GOLD_PRIMARY};"
            f" border-radius: 0px;"
            f" font-size: 16px; }}"
            f"QPushButton:hover {{"
            f" background-color: {AppTheme.SIDEBAR_HOVER_BG}; }}"
        )

    def _inactive_style(self) -> str:
        """Inactive 按鈕 QSS — 透明背景，hover 時淡亮"""
        return (
            f"QPushButton {{"
            f" background-color: transparent;"
            f" color: {AppTheme.SIDEBAR_ICON_INACTIVE};"
            f" border: none;"
            f" border-left: 3px solid transparent;"
            f" border-radius: 0px;"
            f" font-size: 16px; }}"
            f"QPushButton:hover {{"
            f" background-color: {AppTheme.SIDEBAR_HOVER_BG};"
            f" color: {AppTheme.TEXT_PRIMARY}; }}"
        )

    def _apply_btn_state(self, btn: QPushButton, is_active: bool):
        """套用按鈕 active / inactive 樣式

        Args:
            btn:       QPushButton 實例
            is_active: 是否為當前頁面
        """
        btn.setStyleSheet(
            self._active_style() if is_active else self._inactive_style()
        )

    # --------------------------------------------------
    # 事件處理
    # --------------------------------------------------

    def _on_click(self, page_name: str):
        """點擊頁面按鈕

        Args:
            page_name: 頁面名稱
        """
        if page_name == self.current_page:
            return
        self.current_page = page_name
        self._update_button_states()
        self.on_page_change(page_name)

    # --------------------------------------------------
    # 狀態更新
    # --------------------------------------------------

    def _update_button_states(self):
        """更新所有導航按鈕的 active / inactive 樣式"""
        for name, btn in self._items.items():
            self._apply_btn_state(btn, name == self.current_page)

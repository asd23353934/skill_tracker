"""
練功水錢 — 載入紀錄對話框（V2）
顯示紀錄清單，accept 時以 self.selected_name 回傳。
"""

from PySide6.QtWidgets import QListWidget, QPushButton
from PySide6.QtCore import Qt

from src.ui_v2.theme_v2 import V2Theme as T
from src.ui_v2.dialogs.base_dialog_v2 import BaseDialogV2


class PotionLoadDialogV2(BaseDialogV2):
    """V2 練功紀錄載入對話框

    Args:
        parent: 父元件
        app:    App 主應用實例（用於取得 config_manager）

    accept 後以 `self.selected_name` 回傳使用者選取的紀錄名
    """

    def __init__(self, parent=None, app=None):
        super().__init__(parent, title="載入練功紀錄", width=420, height=420)
        self.app = app
        self.selected_name: str = ""
        self._build_body()
        self._build_footer()

    def _build_body(self):
        L = self.body_layout()

        self._list = QListWidget()
        self._list.setStyleSheet(
            f"QListWidget {{ color: {T.TEXT_HI}; background: {T.BG_INPUT};"
            f" border: 1px solid {T.BORDER}; border-radius: {T.R_SM}px;"
            f" padding: 4px; font-size: 12px; }}"
            f"QListWidget::item {{ padding: 6px 8px; border-radius: {T.R_SM}px; }}"
            f"QListWidget::item:hover {{ background: {T.BG_HOVER}; }}"
            f"QListWidget::item:selected {{ background: {T.alpha(T.ORANGE, 70)};"
            f" color: {T.TEXT_HI}; }}"
        )
        self._list.itemDoubleClicked.connect(self._on_accept)

        names = []
        if self.app is not None and hasattr(self.app, "config_manager"):
            names = self.app.config_manager.list_potion_saves() or []
        for n in names:
            self._list.addItem(n)

        if not names:
            empty = T.make_label("（尚無任何紀錄）", T.FONT_CAPTION)
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            L.addWidget(empty)
        L.addWidget(self._list, 1)

    def _build_footer(self):
        F = self.footer_layout()

        cancel = QPushButton("取消")
        cancel.setProperty("kind", "ghost")
        cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel.setFixedHeight(T.BTN_H)
        cancel.clicked.connect(self.reject)
        F.addWidget(cancel)

        load = QPushButton("載入")
        load.setProperty("kind", "primary")
        load.setCursor(Qt.CursorShape.PointingHandCursor)
        load.setFixedHeight(T.BTN_H)
        load.clicked.connect(self._on_accept)
        F.addWidget(load)

    def _on_accept(self, *_):
        item = self._list.currentItem()
        if item is None:
            return
        self.selected_name = item.text()
        self.accept()

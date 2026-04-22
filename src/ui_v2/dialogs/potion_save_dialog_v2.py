"""
練功水錢 — 儲存紀錄對話框（V2）
輸入記錄名稱後，accept 時以 self.name 回傳。
"""

from PySide6.QtWidgets import QLineEdit, QPushButton
from PySide6.QtCore import Qt

from src.ui_v2.theme_v2 import V2Theme as T
from src.ui_v2.dialogs.base_dialog_v2 import BaseDialogV2


class PotionSaveDialogV2(BaseDialogV2):
    """V2 練功紀錄儲存對話框

    accept 後以 `self.name` 回傳使用者輸入的名稱（已去除前後空白）
    """

    def __init__(self, parent=None):
        super().__init__(parent, title="儲存練功紀錄", width=380, height=200)
        self.name: str = ""
        self._build_body()
        self._build_footer()

    def _build_body(self):
        L = self.body_layout()
        L.addWidget(T.make_label("記錄名稱", T.FONT_LABEL))

        self._name_edit = QLineEdit()
        self._name_edit.setFixedHeight(T.BTN_H)
        self._name_edit.setPlaceholderText("例：2026-04-22 夢裡")
        self._name_edit.setStyleSheet(
            f"QLineEdit {{ color: {T.TEXT_HI}; background: {T.BG_INPUT};"
            f" border: 1px solid {T.BORDER}; border-radius: {T.R_SM}px;"
            f" padding: 0 10px; font-size: 12px; }}"
            f"QLineEdit:focus {{ border-color: {T.ORANGE}; }}"
        )
        self._name_edit.returnPressed.connect(self._on_accept)
        L.addWidget(self._name_edit)
        L.addStretch()

    def _build_footer(self):
        F = self.footer_layout()

        cancel = QPushButton("取消")
        cancel.setProperty("kind", "ghost")
        cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel.setFixedHeight(T.BTN_H)
        cancel.clicked.connect(self.reject)
        F.addWidget(cancel)

        save = QPushButton("儲存")
        save.setProperty("kind", "primary")
        save.setCursor(Qt.CursorShape.PointingHandCursor)
        save.setFixedHeight(T.BTN_H)
        save.clicked.connect(self._on_accept)
        F.addWidget(save)

    def _on_accept(self):
        name = self._name_edit.text().strip()
        if not name:
            self._name_edit.setFocus()
            return
        self.name = name
        self.accept()

"""
V2 ProfileManagerDialog — profile CRUD（新增 / 複製 / 重命名 / 刪除）

切換 profile 由 skill 頁 dropdown 處理，本 dialog 不重複該入口。
所有 CRUD 委派給 AppCoreMixin.create/duplicate/rename/delete_profile，
toast 由 mixin 端 emit。
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QListWidget, QListWidgetItem, QPushButton, QInputDialog, QMessageBox,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont

from src.ui_v2.theme_v2 import V2Theme as T
from src.ui_v2.dialogs.base_dialog_v2 import BaseDialogV2


def _btn(label: str, on_click, *, primary: bool = False, danger: bool = False) -> QPushButton:
    btn = QPushButton(label)
    btn.setFixedHeight(30)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    if danger:
        bg, fg, hover = T.RED, "#ffffff", "#ff7484"
    elif primary:
        bg, fg, hover = T.ORANGE, "#ffffff", T.ORANGE_HOVER
    else:
        bg, fg, hover = T.BG_INPUT, T.TEXT, T.BG_HOVER
    btn.setStyleSheet(
        f"QPushButton {{ background: {bg}; color: {fg};"
        f" border: 1px solid {T.BORDER}; border-radius: {T.R_SM}px;"
        f" padding: 0 14px; font-size: 12px; font-weight: 600; }}"
        f"QPushButton:hover {{ background: {hover}; }}"
    )
    btn.clicked.connect(on_click)
    return btn


class ProfileManagerDialogV2(BaseDialogV2):
    """V2 配置管理對話框（CRUD only；切換在 dropdown）"""

    def __init__(self, parent, app):
        super().__init__(parent, title="配置管理", width=420, height=460)
        self.app = app
        self._build_body()
        self._build_footer()
        self._refresh_list()

    # ── 列表 ──
    def _build_body(self):
        body = self.body_layout()
        self._list = QListWidget()
        self._list.setStyleSheet(
            f"QListWidget {{ background: {T.BG_INPUT}; color: {T.TEXT};"
            f" border: 1px solid {T.BORDER}; border-radius: {T.R_SM}px;"
            f" padding: 4px; font-size: 12px; }}"
            f"QListWidget::item {{ padding: 6px 8px; border-radius: 4px; }}"
            f"QListWidget::item:selected {{"
            f" background: {T.alpha(T.ORANGE, 60)}; color: {T.TEXT_HI}; }}"
            f"QListWidget::item:hover {{ background: {T.BG_HOVER}; }}"
        )
        body.addWidget(self._list, 1)

    def _refresh_list(self):
        self._list.clear()
        cm = self.app.config_manager
        current = cm.get_current_profile()
        for name in cm.list_profiles():
            is_current = (name == current)
            display = f"{name}（當前）" if is_current else name
            item = QListWidgetItem(display)
            item.setData(Qt.ItemDataRole.UserRole, name)
            if is_current:
                # 當前 profile 用 accent 色 + 粗體（與「選中」的橘底區分）
                item.setForeground(QColor(T.ORANGE))
                f = QFont()
                f.setBold(True)
                item.setFont(f)
            self._list.addItem(item)

    def _get_selected_name(self) -> str | None:
        it = self._list.currentItem()
        if it is None:
            return None
        return it.data(Qt.ItemDataRole.UserRole)

    # ── 按鈕 ──
    def _build_footer(self):
        footer = self.footer_layout()
        footer.addWidget(_btn("切換", self._on_switch, primary=True))
        footer.addWidget(_btn("新增", self._on_create))
        footer.addWidget(_btn("複製", self._on_duplicate))
        footer.addWidget(_btn("重命名", self._on_rename))
        footer.addWidget(_btn("刪除", self._on_delete, danger=True))

    def _on_switch(self):
        name = self._get_selected_name()
        if not name:
            self.app.toast.show("請先選擇要切換的配置！", "info")
            return
        if name == self.app.config_manager.get_current_profile():
            self.app.toast.show("已經是當前配置了！", "info")
            return
        self.app.switch_profile(name)
        self._refresh_list()  # 更新「（當前）」標記

    def _on_create(self):
        name, ok = QInputDialog.getText(self, "新增配置", "輸入新配置名稱:")
        if not ok or not name.strip():
            return
        if self.app.create_profile(name.strip()):
            self._refresh_list()

    def _on_duplicate(self):
        source = self._get_selected_name()
        if not source:
            self.app.toast.show("請先選擇要複製的配置！", "info")
            return
        new_name, ok = QInputDialog.getText(
            self, "複製配置", f"輸入新配置名稱:\n(將複製自 '{source}')"
        )
        if not ok or not new_name.strip():
            return
        if self.app.duplicate_profile(source, new_name.strip()):
            self._refresh_list()

    def _on_rename(self):
        old = self._get_selected_name()
        if not old:
            self.app.toast.show("請先選擇要重命名的配置！", "info")
            return
        new_name, ok = QInputDialog.getText(
            self, "重命名配置", f"輸入新名稱:\n(當前: '{old}')", text=old
        )
        if not ok or not new_name.strip() or new_name.strip() == old:
            return
        if self.app.rename_profile(old, new_name.strip()):
            self._refresh_list()

    def _on_delete(self):
        name = self._get_selected_name()
        if not name:
            self.app.toast.show("請先選擇要刪除的配置！", "info")
            return
        reply = QMessageBox.question(
            self, "確認刪除", f"確定要刪除配置 '{name}' 嗎？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        if self.app.delete_profile(name):
            self._refresh_list()

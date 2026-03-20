"""
配置管理對話框 — PySide6 版本
RPG 金色邊框風格
"""

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QListWidget, QListWidgetItem, QMessageBox, QInputDialog, QWidget,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from src.ui.dialogs.base_dialog import BaseDialog
from src.ui.theme import AppTheme


class ProfileManagerDialog(BaseDialog):
    """配置管理對話框"""

    def __init__(self, parent, config_manager, current_settings, main_app):
        super().__init__(parent, "配置管理", 600, 520)
        self.config_manager  = config_manager
        self.current_settings = current_settings
        self.main_app        = main_app
        self.current_profile = self.config_manager.get_current_profile()
        self._build_ui()

    def _build_ui(self):
        """建構 UI"""
        layout = QVBoxLayout(self.inner)
        layout.setContentsMargins(20, 16, 20, 12)
        layout.setSpacing(8)

        # ===== 標題列 =====
        title_row = QWidget()
        title_row.setStyleSheet("background: transparent;")
        tr = QHBoxLayout(title_row)
        tr.setContentsMargins(0, 0, 0, 0)
        tr.setSpacing(6)

        title_lbl = QLabel("⚔ 配置管理")
        title_lbl.setStyleSheet(
            f"color: {AppTheme.TEXT_GOLD}; font-size: 16px; font-weight: bold;"
            f" background: transparent; border: none;"
        )
        tr.addWidget(title_lbl)
        tr.addStretch()

        cur_lbl = QLabel("當前:")
        cur_lbl.setStyleSheet(
            f"color: {AppTheme.TEXT_SECONDARY}; font-size: 12px;"
            f" background: transparent; border: none;"
        )
        tr.addWidget(cur_lbl)

        self.current_label = QLabel(self.current_profile)
        self.current_label.setStyleSheet(
            f"color: {AppTheme.GOLD_LIGHT}; font-size: 12px; font-weight: bold;"
            f" background: transparent; border: none;"
        )
        tr.addWidget(self.current_label)
        layout.addWidget(title_row)

        # ===== 配置列表 =====
        list_frame = QFrame()
        list_frame.setObjectName("list_frame")
        list_frame.setStyleSheet(
            f"QFrame#list_frame {{ background-color: {AppTheme.BG_CARD};"
            f" border: 1px solid {AppTheme.GOLD_MUTED};"
            f" border-radius: {AppTheme.CORNER_MD}px; }}"
        )
        lf_layout = QVBoxLayout(list_frame)
        lf_layout.setContentsMargins(4, 4, 4, 4)

        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet(
            f"QListWidget {{ background-color: {AppTheme.BG_CARD}; border: none;"
            f" color: {AppTheme.TEXT_PRIMARY}; font-size: 13px; }}"
            f"QListWidget::item {{ padding: 6px 12px; border-radius: 3px; }}"
            f"QListWidget::item:hover {{ background-color: {AppTheme.BG_CARD_HOVER}; }}"
            f"QListWidget::item:selected {{"
            f" background-color: {AppTheme.BG_CARD_HOVER};"
            f" color: {AppTheme.GOLD_LIGHT}; }}"
        )
        self.list_widget.itemDoubleClicked.connect(lambda _: self._switch_profile())
        lf_layout.addWidget(self.list_widget)
        layout.addWidget(list_frame)

        # ===== 按鈕組 =====
        btn_row = QWidget()
        btn_row.setStyleSheet("background: transparent;")
        br = QHBoxLayout(btn_row)
        br.setContentsMargins(0, 0, 0, 0)
        br.setSpacing(6)
        br.addStretch()

        buttons = [
            ("➕ 新增",  AppTheme.ACCENT_GREEN,  "#0d9668", "#ffffff", self._create_new_profile),
            ("📋 複製",  AppTheme.ACCENT_BLUE,   "#2563eb", "#ffffff", self._copy_profile),
            ("✏ 重命名", AppTheme.GOLD_PRIMARY,  AppTheme.GOLD_DARK, AppTheme.BG_DEEP, self._rename_profile),
            ("🔄 切換",  AppTheme.ACCENT_PURPLE, "#7c3aed", "#ffffff", self._switch_profile),
            ("🗑 刪除",  AppTheme.ACCENT_RED,    "#dc2626", "#ffffff", self._delete_profile),
        ]
        for text, color, hover, fg, cmd in buttons:
            btn = QPushButton(text)
            btn.setFixedHeight(32)
            btn.clicked.connect(cmd)
            btn.setStyleSheet(
                f"QPushButton {{ background-color: {color}; color: {fg};"
                f" border: 1px solid {AppTheme.GOLD_MUTED};"
                f" border-radius: {AppTheme.CORNER_MD}px;"
                f" padding: 3px 10px; font-size: 11px; font-weight: bold; }}"
                f"QPushButton:hover {{ background-color: {hover}; }}"
            )
            br.addWidget(btn)
        br.addStretch()
        layout.addWidget(btn_row)

        # ===== 提示 =====
        hint = QLabel("💡 雙擊配置名稱可快速切換 | 所有修改會自動保存到當前配置")
        hint.setStyleSheet(
            f"color: {AppTheme.TEXT_MUTED}; font-size: 11px;"
            f" background: transparent; border: none;"
        )
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hint)

        self._refresh_list()

    def _refresh_list(self):
        """刷新配置列表"""
        self.list_widget.clear()
        profiles = self.config_manager.list_profiles()
        for profile in profiles:
            item = QListWidgetItem()
            if profile == self.current_profile:
                item.setText(f"★ {profile}")
                item.setForeground(QColor(AppTheme.GOLD_LIGHT))
                font = item.font()
                font.setBold(True)
                item.setFont(font)
            else:
                item.setText(f"    {profile}")
            item.setData(Qt.ItemDataRole.UserRole, profile)
            self.list_widget.addItem(item)

    def _get_selected_name(self):
        """取得選取的配置名稱"""
        item = self.list_widget.currentItem()
        if item:
            return item.data(Qt.ItemDataRole.UserRole)
        return None

    def _create_new_profile(self):
        """新增配置"""
        name, ok = QInputDialog.getText(self, "新增配置", "輸入新配置名稱:")
        if not ok or not name.strip():
            return
        name = name.strip()
        if name in self.config_manager.list_profiles():
            self.main_app.toast.show(f"配置 '{name}' 已存在！", "error")
            return
        all_skills = self.main_app.skill_manager.get_all_skills().keys()
        initial_settings = {
            "hotkeys": {},
            "permanent": {sid: False for sid in all_skills},
            "loop":      {sid: False for sid in all_skills},
            "alert_enabled": {sid: False for sid in all_skills},
            "cooldown_overrides": {},
        }
        if self.config_manager.save_profile(name, initial_settings):
            self._refresh_list()

    def _copy_profile(self):
        """複製配置"""
        source = self._get_selected_name()
        if not source:
            self.main_app.toast.show("請先選擇要複製的配置！", "info")
            return
        new_name, ok = QInputDialog.getText(
            self, "複製配置", f"輸入新配置名稱:\n(將複製自 '{source}')"
        )
        if not ok or not new_name.strip():
            return
        new_name = new_name.strip()
        if new_name in self.config_manager.list_profiles():
            self.main_app.toast.show(f"配置 '{new_name}' 已存在！", "error")
            return
        source_data = self.config_manager.load_profile(source)
        if source_data and self.config_manager.save_profile(new_name, source_data):
            self._refresh_list()

    def _rename_profile(self):
        """重命名配置"""
        old_name = self._get_selected_name()
        if not old_name:
            self.main_app.toast.show("請先選擇要重命名的配置！", "info")
            return
        new_name, ok = QInputDialog.getText(
            self, "重命名配置", f"輸入新名稱:\n(當前: '{old_name}')"
        )
        if not ok or not new_name.strip() or new_name.strip() == old_name:
            return
        new_name = new_name.strip()
        if new_name in self.config_manager.list_profiles():
            self.main_app.toast.show(f"配置 '{new_name}' 已存在！", "error")
            return
        if self.config_manager.rename_profile(old_name, new_name):
            if old_name == self.current_profile:
                self.current_profile = new_name
                self.config_manager.set_current_profile(new_name)
                self.current_label.setText(new_name)
                self.main_app.current_profile_name = new_name
                self.main_app.header.update_profile_name(new_name)
            self._refresh_list()

    def _switch_profile(self):
        """切換配置"""
        name = self._get_selected_name()
        if not name:
            self.main_app.toast.show("請先選擇要切換的配置！", "info")
            return
        if name == self.current_profile:
            self.main_app.toast.show("已經是當前配置了！", "info")
            return
        profile_data = self.config_manager.load_profile(name)
        if profile_data:
            self.config_manager.set_current_profile(name)
            self.current_profile = name
            self.current_label.setText(name)
            self.result = profile_data
            self.accept()

    def _delete_profile(self):
        """刪除配置"""
        name = self._get_selected_name()
        if not name:
            self.main_app.toast.show("請先選擇要刪除的配置！", "info")
            return
        if name == self.current_profile:
            self.main_app.toast.show("無法刪除當前正在使用的配置！", "error")
            return
        reply = QMessageBox.question(
            self, "確認刪除", f"確定要刪除配置 '{name}' 嗎？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            if self.config_manager.delete_profile(name):
                self._refresh_list()

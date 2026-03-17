"""
技能細部設定對話框 — PySide6 版本
提供提前秒數、完成音效 / 提前提示音效選擇（下拉式）、自動套用設定等選項
"""

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QComboBox, QCheckBox, QScrollArea, QWidget, QFrame,
    QMessageBox, QFileDialog,
)
from PySide6.QtCore import Qt
from src.ui.dialogs.base_dialog import BaseDialog
from src.ui.theme import AppTheme


class SkillDetailDialog(BaseDialog):
    """技能細部設定對話框"""

    NO_SOUND_LABEL = "使用全域設定"

    def __init__(self, parent, skill_id, app):
        self.skill_id = skill_id
        self.app      = app
        self.skill    = app.skill_manager.get_skill(skill_id)
        skill_name    = self.skill["name"] if self.skill else skill_id

        # 音效選項映射（必須在 super().__init__ 前建立）
        self._sound_label_map = {}
        self._build_sound_options()

        super().__init__(parent, f"細部設定 — {skill_name}", 440, 580)
        self._build_ui()

    def _build_sound_options(self):
        """建立音效下拉選項映射"""
        self._sound_label_map = {self.NO_SOUND_LABEL: ""}
        if self.app.sound_manager:
            for filename in self.app.sound_manager.list_sounds():
                label = self.app.sound_manager.get_sound_label(filename)
                self._sound_label_map[label] = filename

    def _get_label_for_filename(self, filename):
        """根據檔名取得對應的下拉選項標籤"""
        if not filename:
            return self.NO_SOUND_LABEL
        for label, fname in self._sound_label_map.items():
            if fname == filename:
                return label
        return self.NO_SOUND_LABEL

    def _build_ui(self):
        """建構 UI"""
        outer = QVBoxLayout(self.inner)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # 標題
        title_lbl = QLabel(f"⚙ {self.skill['name']}")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_lbl.setStyleSheet(
            f"color: {AppTheme.TEXT_GOLD}; font-size: 16px; font-weight: bold;"
            f" background: transparent; border: none; padding: 16px 0 8px 0;"
        )
        outer.addWidget(title_lbl)

        # 可捲動內容
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(
            "QScrollArea { border: none; background: transparent; }"
            "QScrollArea > QWidget > QWidget { background: transparent; }"
        )
        content = QWidget()
        content.setStyleSheet("background: transparent;")
        cl = QVBoxLayout(content)
        cl.setContentsMargins(20, 0, 20, 8)
        cl.setSpacing(0)
        cl.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll.setWidget(content)
        outer.addWidget(scroll)

        # ===== 提前提示秒數 =====
        self._section_label(cl, "🔔 提前提示秒數")

        current_override = self.app.skill_alert_seconds_overrides.get(
            self.skill_id, None
        )
        current_val = (
            current_override if current_override is not None
            else self.app.alert_before_seconds
        )

        alert_row = QWidget()
        alert_row.setStyleSheet("background: transparent;")
        ar = QHBoxLayout(alert_row)
        ar.setContentsMargins(0, 4, 0, 4)
        ar.setSpacing(8)
        ar.addWidget(self._make_label("提前"))
        self.alert_entry = QLineEdit(str(current_val))
        self.alert_entry.setFixedSize(80, 32)
        self.alert_entry.setStyleSheet(self._lineedit_style())
        ar.addWidget(self.alert_entry)
        ar.addWidget(self._make_label("秒提示"))
        ar.addStretch()
        cl.addWidget(alert_row)

        self.use_global_alert_cb = QCheckBox(
            f"使用全域設定（目前: {self.app.alert_before_seconds}秒）"
        )
        self.use_global_alert_cb.setChecked(current_override is None)
        self.use_global_alert_cb.setStyleSheet(
            f"QCheckBox {{ color: {AppTheme.TEXT_SECONDARY}; font-size: 12px;"
            f" background: transparent; spacing: 4px; }}"
            f"QCheckBox::indicator {{ width: 14px; height: 14px; border-radius: 3px;"
            f" border: 1px solid {AppTheme.GOLD_MUTED}; background: {AppTheme.BG_TERTIARY}; }}"
            f"QCheckBox::indicator:checked {{"
            f" background: {AppTheme.GOLD_PRIMARY}; border-color: {AppTheme.GOLD_PRIMARY}; }}"
        )
        self.use_global_alert_cb.stateChanged.connect(self._on_toggle_global_alert)
        cl.addWidget(self.use_global_alert_cb)
        cl.addSpacing(4)
        self._separator(cl)

        # ===== 完成音效 =====
        self._section_label(cl, "🎵 完成音效")
        sound_row = QWidget()
        sound_row.setStyleSheet("background: transparent;")
        sr = QHBoxLayout(sound_row)
        sr.setContentsMargins(0, 4, 0, 4)
        sr.setSpacing(8)
        self.sound_combo = QComboBox()
        self.sound_combo.addItems(list(self._sound_label_map.keys()))
        current_sound = self.app.skill_sound_overrides.get(self.skill_id, "")
        self.sound_combo.setCurrentText(self._get_label_for_filename(current_sound))
        self.sound_combo.setFixedWidth(200)
        self.sound_combo.setStyleSheet(self._combo_style())
        sr.addWidget(self.sound_combo)
        preview1 = QPushButton("▶")
        preview1.setFixedSize(32, 32)
        preview1.clicked.connect(self._preview_completion_sound)
        preview1.setStyleSheet(self._small_btn_style())
        sr.addWidget(preview1)
        sr.addStretch()
        cl.addWidget(sound_row)
        self._separator(cl)

        # ===== 提前提示音效 =====
        self._section_label(cl, "🔔 提前提示音效")
        asnd_row = QWidget()
        asnd_row.setStyleSheet("background: transparent;")
        asr = QHBoxLayout(asnd_row)
        asr.setContentsMargins(0, 4, 0, 4)
        asr.setSpacing(8)
        self.alert_sound_combo = QComboBox()
        self.alert_sound_combo.addItems(list(self._sound_label_map.keys()))
        current_alert_sound = self.app.skill_alert_sound_overrides.get(
            self.skill_id, ""
        )
        self.alert_sound_combo.setCurrentText(
            self._get_label_for_filename(current_alert_sound)
        )
        self.alert_sound_combo.setFixedWidth(200)
        self.alert_sound_combo.setStyleSheet(self._combo_style())
        asr.addWidget(self.alert_sound_combo)
        preview2 = QPushButton("▶")
        preview2.setFixedSize(32, 32)
        preview2.clicked.connect(self._preview_alert_sound)
        preview2.setStyleSheet(self._small_btn_style())
        asr.addWidget(preview2)
        asr.addStretch()
        cl.addWidget(asnd_row)

        import_btn = QPushButton("＋ 匯入音效檔案")
        import_btn.setFixedHeight(28)
        import_btn.clicked.connect(self._import_sound)
        import_btn.setStyleSheet(
            f"QPushButton {{ background-color: {AppTheme.BG_TERTIARY};"
            f" color: {AppTheme.TEXT_PRIMARY}; border: 1px solid {AppTheme.GOLD_MUTED};"
            f" border-radius: {AppTheme.CORNER_SM}px; padding: 2px 8px; font-size: 11px; }}"
            f"QPushButton:hover {{ background-color: {AppTheme.GOLD_MUTED}; }}"
        )
        cl.addWidget(import_btn)
        cl.addSpacing(4)
        self._separator(cl)

        # ===== 自動設定 =====
        self._section_label(cl, "⚡ 自動設定")
        hint = QLabel("未手動設定時自動套用的參數：")
        hint.setStyleSheet(
            f"color: {AppTheme.TEXT_SECONDARY}; font-size: 11px;"
            f" background: transparent; border: none;"
        )
        cl.addWidget(hint)

        auto_row = QWidget()
        auto_row.setStyleSheet("background: transparent;")
        auto_r = QHBoxLayout(auto_row)
        auto_r.setContentsMargins(0, 4, 0, 4)
        auto_r.setSpacing(12)

        self.auto_permanent_cb = self._make_checkbox(
            "常駐",
            self.app.skill_permanent.get(self.skill_id, False),
            AppTheme.ACCENT_YELLOW,
        )
        auto_r.addWidget(self.auto_permanent_cb)

        self.auto_loop_cb = self._make_checkbox(
            "循環",
            self.app.skill_loop.get(self.skill_id, False),
            AppTheme.ACCENT_GREEN,
        )
        auto_r.addWidget(self.auto_loop_cb)

        self.auto_alert_cb = self._make_checkbox(
            "提前提示",
            self.app.skill_alert_enabled.get(self.skill_id, False),
            AppTheme.ACCENT_ORANGE,
        )
        auto_r.addWidget(self.auto_alert_cb)
        auto_r.addStretch()
        cl.addWidget(auto_row)

        # ===== 儲存按鈕 =====
        save_btn = QPushButton("✓ 儲存")
        save_btn.setFixedSize(140, 40)
        save_btn.clicked.connect(self._save)
        save_btn.setStyleSheet(
            f"QPushButton {{ background-color: {AppTheme.GOLD_PRIMARY};"
            f" color: {AppTheme.BG_DEEP}; border: 1px solid {AppTheme.GOLD_DARK};"
            f" border-radius: {AppTheme.CORNER_MD}px;"
            f" font-size: 12px; font-weight: bold; }}"
            f"QPushButton:hover {{ background-color: {AppTheme.GOLD_LIGHT}; }}"
        )
        outer.addWidget(save_btn, alignment=Qt.AlignmentFlag.AlignHCenter)
        outer.addSpacing(12)

    # --------------------------------------------------
    # UI 輔助方法
    # --------------------------------------------------

    def _make_label(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"color: {AppTheme.TEXT_PRIMARY}; font-size: 12px;"
            f" background: transparent; border: none;"
        )
        return lbl

    def _make_checkbox(self, text, checked, color):
        cb = QCheckBox(text)
        cb.setChecked(checked)
        cb.setStyleSheet(
            f"QCheckBox {{ color: {color}; font-size: 12px;"
            f" background: transparent; spacing: 4px; }}"
            f"QCheckBox::indicator {{ width: 14px; height: 14px; border-radius: 3px;"
            f" border: 1px solid {AppTheme.GOLD_MUTED}; background: {AppTheme.BG_TERTIARY}; }}"
            f"QCheckBox::indicator:checked {{"
            f" background: {color}; border-color: {color}; }}"
        )
        return cb

    def _lineedit_style(self):
        return (
            f"QLineEdit {{ background-color: {AppTheme.BG_CARD};"
            f" color: {AppTheme.TEXT_PRIMARY}; border: 1px solid {AppTheme.GOLD_MUTED};"
            f" border-radius: {AppTheme.CORNER_SM}px; padding: 3px 6px; font-size: 11px; }}"
            f"QLineEdit:focus {{ border-color: {AppTheme.GOLD_PRIMARY}; }}"
        )

    def _combo_style(self):
        return (
            f"QComboBox {{ background-color: {AppTheme.BG_CARD};"
            f" color: {AppTheme.TEXT_PRIMARY}; border: 1px solid {AppTheme.GOLD_MUTED};"
            f" border-radius: {AppTheme.CORNER_SM}px; padding: 4px 8px; font-size: 11px; }}"
            f"QComboBox::drop-down {{ background-color: {AppTheme.GOLD_PRIMARY};"
            f" border: none; width: 20px; border-radius: {AppTheme.CORNER_SM}px; }}"
            f"QComboBox QAbstractItemView {{"
            f" background-color: {AppTheme.BG_CARD}; color: {AppTheme.TEXT_PRIMARY};"
            f" selection-background-color: {AppTheme.GOLD_MUTED}; }}"
        )

    def _small_btn_style(self):
        return (
            f"QPushButton {{ background-color: {AppTheme.BG_TERTIARY};"
            f" color: {AppTheme.TEXT_PRIMARY}; border: 1px solid {AppTheme.GOLD_MUTED};"
            f" border-radius: {AppTheme.CORNER_SM}px; font-size: 12px; }}"
            f"QPushButton:hover {{ background-color: {AppTheme.GOLD_MUTED}; }}"
        )

    def _section_label(self, layout, text):
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"color: {AppTheme.GOLD_PRIMARY}; font-size: 13px; font-weight: bold;"
            f" background: transparent; border: none; padding: 8px 0 2px 0;"
        )
        layout.addWidget(lbl)

    def _separator(self, layout):
        line = QFrame()
        line.setFixedHeight(1)
        line.setStyleSheet(f"background-color: {AppTheme.GOLD_MUTED};")
        layout.addWidget(line)
        layout.addSpacing(4)

    # --------------------------------------------------
    # 音效功能
    # --------------------------------------------------

    def _get_effective_filename(self, combo, global_fallback):
        """取得選單實際對應的檔名（含全域 fallback）"""
        label    = combo.currentText()
        filename = self._sound_label_map.get(label, "")
        return filename if filename else global_fallback

    def _preview_completion_sound(self):
        """試聽完成音效（含全域 fallback）"""
        filename = self._get_effective_filename(
            self.sound_combo, self.app.global_sound
        )
        if filename and self.app.sound_manager:
            self.app.sound_manager.play(filename)

    def _preview_alert_sound(self):
        """試聽提前提示音效（含全域 fallback）"""
        filename = self._get_effective_filename(
            self.alert_sound_combo, self.app.global_alert_sound
        )
        if filename and self.app.sound_manager:
            self.app.sound_manager.play(filename)

    def _import_sound(self):
        """開啟檔案選擇器匯入音效"""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "選擇音效檔案", "",
            "音效檔案 (*.wav *.mp3);;WAV 檔案 (*.wav);;MP3 檔案 (*.mp3)"
        )
        if not filepath or not self.app.sound_manager:
            return
        new_name = self.app.sound_manager.import_sound(filepath)
        if new_name:
            self._build_sound_options()
            new_values = list(self._sound_label_map.keys())
            self.sound_combo.clear()
            self.sound_combo.addItems(new_values)
            self.alert_sound_combo.clear()
            self.alert_sound_combo.addItems(new_values)
            new_label = self.app.sound_manager.get_sound_label(new_name)
            self.sound_combo.setCurrentText(new_label)
            QMessageBox.information(self, "匯入成功", f"已成功匯入音效: {new_name}")
        else:
            QMessageBox.critical(
                self, "匯入失敗",
                "無法匯入音效檔案，請確認檔案格式為 .wav 或 .mp3"
            )

    def _on_toggle_global_alert(self):
        """切換全域提示設定時更新 entry 狀態"""
        if self.use_global_alert_cb.isChecked():
            self.alert_entry.setText(str(self.app.alert_before_seconds))

    # --------------------------------------------------
    # 儲存
    # --------------------------------------------------

    def _save(self):
        """儲存設定"""
        try:
            # 提前秒數
            if self.use_global_alert_cb.isChecked():
                self.app.skill_alert_seconds_overrides.pop(self.skill_id, None)
            else:
                alert_val = int(self.alert_entry.text())
                alert_val = max(0, alert_val)
                self.app.skill_alert_seconds_overrides[self.skill_id] = alert_val

            # 更新提前秒數按鈕（QPushButton）
            btn = self.app.alert_seconds_buttons.get(self.skill_id)
            if btn:
                actual_val  = self.app.get_alert_seconds(self.skill_id)
                is_override = self.skill_id in self.app.skill_alert_seconds_overrides
                btn.setText(f"{actual_val}s")
                self.app._apply_btn_style(
                    btn,
                    bg    = AppTheme.ACCENT_ORANGE if is_override else AppTheme.BG_TERTIARY,
                    hover = "#e07a2a"              if is_override else AppTheme.BG_SECONDARY,
                )

            # 完成音效
            sound_label = self.sound_combo.currentText()
            sound = self._sound_label_map.get(sound_label, "")
            if sound:
                self.app.skill_sound_overrides[self.skill_id] = sound
            else:
                self.app.skill_sound_overrides.pop(self.skill_id, None)

            # 提前提示音效
            alert_sound_label = self.alert_sound_combo.currentText()
            alert_sound = self._sound_label_map.get(alert_sound_label, "")
            if alert_sound:
                self.app.skill_alert_sound_overrides[self.skill_id] = alert_sound
            else:
                self.app.skill_alert_sound_overrides.pop(self.skill_id, None)

            # 自動設定（常駐/循環/提示）
            new_permanent = self.auto_permanent_cb.isChecked()
            new_loop      = self.auto_loop_cb.isChecked()
            new_alert     = self.auto_alert_cb.isChecked()

            # 互斥：常駐和循環不能同時啟用
            if new_permanent and new_loop:
                new_loop = False

            old_permanent = self.app.skill_permanent.get(self.skill_id, False)
            old_loop      = self.app.skill_loop.get(self.skill_id, False)

            self.app.skill_permanent[self.skill_id]     = new_permanent
            self.app.skill_loop[self.skill_id]          = new_loop
            self.app.skill_alert_enabled[self.skill_id] = new_alert

            # 更新 UI checkboxes（QCheckBox 引用）
            if self.skill_id in self.app.permanent_vars:
                self.app.permanent_vars[self.skill_id].setChecked(new_permanent)
            if self.skill_id in self.app.loop_vars:
                self.app.loop_vars[self.skill_id].setChecked(new_loop)
            if self.skill_id in self.app.alert_enabled_vars:
                self.app.alert_enabled_vars[self.skill_id].setChecked(new_alert)

            # 處理視窗變更
            if new_permanent and not old_permanent:
                if self.skill_id not in self.app.window_manager.active_windows:
                    self.app.window_manager.create_permanent_window(self.skill_id)
            elif not new_permanent and old_permanent:
                if self.skill_id in self.app.window_manager.active_windows:
                    self.app.window_manager.active_windows[self.skill_id].close()

            if not new_loop and old_loop:
                if self.skill_id in self.app.window_manager.active_windows:
                    self.app.window_manager.active_windows[self.skill_id].close()

            # 更新活躍視窗參數
            if self.skill_id in self.app.window_manager.active_windows:
                win = self.app.window_manager.active_windows[self.skill_id]
                win.alert_enabled        = new_alert
                win.alert_before_seconds = self.app.get_alert_seconds(self.skill_id)

            self.app.auto_save_current_profile()
            self.result = True
            self.accept()

        except ValueError:
            pass

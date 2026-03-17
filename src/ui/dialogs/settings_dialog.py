"""
設定對話框 — PySide6 版本
提供系統設定的 UI，包含位置、視窗大小、提前提示、音效選擇
RPG 金色邊框風格，音效使用下拉式選單 + 匯入按鈕
"""

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QComboBox, QCheckBox, QScrollArea, QWidget, QFrame,
    QMessageBox, QFileDialog,
)
from PySide6.QtCore import Qt
from src.ui.dialogs.base_dialog import BaseDialog
from src.ui.theme import AppTheme


class SettingsDialog(BaseDialog):
    """設定對話框"""

    WINDOW_SIZE_OPTIONS = {
        "極小 (48px)": 48,
        "小 (64px) - 預設": 64,
        "中 (80px)": 80,
        "大 (96px)": 96,
        "極大 (128px)": 128,
    }

    NO_SOUND_LABEL = "無"

    def __init__(self, parent, current_settings):
        super().__init__(parent, "設定", 480, 720)
        self.current_settings = current_settings
        self.sound_manager    = current_settings.get("sound_manager")
        self._sound_label_map = {}
        self._build_sound_options()
        self._build_ui()

    def _build_sound_options(self):
        """建立音效下拉選項映射"""
        self._sound_label_map = {self.NO_SOUND_LABEL: ""}
        if self.sound_manager:
            for filename in self.sound_manager.list_sounds():
                label = self.sound_manager.get_sound_label(filename)
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
        title_lbl = QLabel("⚙ 系統設定")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_lbl.setStyleSheet(
            f"color: {AppTheme.TEXT_GOLD}; font-size: 16px; font-weight: bold;"
            f" background: transparent; border: none; padding: 16px 0 12px 0;"
        )
        outer.addWidget(title_lbl)

        # 可捲動內容區域
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

        # ===== 位置設定 =====
        self._section_label(cl, "📍 技能視窗起始位置")
        pos_row = QWidget()
        pos_row.setStyleSheet("background: transparent;")
        pr = QHBoxLayout(pos_row)
        pr.setContentsMargins(0, 4, 0, 4)
        pr.setSpacing(8)
        pr.addWidget(self._make_label("X:"))
        self.x_entry = self._make_lineedit(
            str(self.current_settings.get("x", 960)), 100
        )
        pr.addWidget(self.x_entry)
        pr.addWidget(self._make_label("Y:"))
        self.y_entry = self._make_lineedit(
            str(self.current_settings.get("y", 540)), 100
        )
        pr.addWidget(self.y_entry)
        pr.addStretch()
        cl.addWidget(pos_row)
        cl.addSpacing(6)
        self._separator(cl)

        # ===== 視窗大小 =====
        self._section_label(cl, "📐 技能視窗大小")
        size_row = QWidget()
        size_row.setStyleSheet("background: transparent;")
        sr = QHBoxLayout(size_row)
        sr.setContentsMargins(0, 4, 0, 4)
        sr.setSpacing(8)
        sr.addWidget(self._make_label("大小:"))
        self.size_combo = QComboBox()
        self.size_combo.addItems(list(self.WINDOW_SIZE_OPTIONS.keys()))
        current_size  = self.current_settings.get("window_size", 64)
        current_label = "小 (64px) - 預設"
        for lbl, sz in self.WINDOW_SIZE_OPTIONS.items():
            if sz == current_size:
                current_label = lbl
                break
        self.size_combo.setCurrentText(current_label)
        self.size_combo.setFixedWidth(180)
        self.size_combo.setStyleSheet(self._combo_style())
        sr.addWidget(self.size_combo)
        sr.addStretch()
        cl.addWidget(size_row)
        hint1 = QLabel("💡 推薦使用「小」或「中」大小")
        hint1.setStyleSheet(self._hint_style())
        cl.addWidget(hint1)
        cl.addSpacing(4)
        self._separator(cl)

        # ===== 提前提示 =====
        self._section_label(cl, "🔔 提前提示音設定")
        alert_row = QWidget()
        alert_row.setStyleSheet("background: transparent;")
        ar = QHBoxLayout(alert_row)
        ar.setContentsMargins(0, 4, 0, 4)
        ar.setSpacing(8)
        ar.addWidget(self._make_label("提前"))
        self.alert_entry = self._make_lineedit(
            str(self.current_settings.get("alert_before_seconds", 0)), 80
        )
        ar.addWidget(self.alert_entry)
        ar.addWidget(self._make_label("秒提示"))
        ar.addStretch()
        cl.addWidget(alert_row)
        hint2 = QLabel("💡 設為 0 表示結束時才提示")
        hint2.setStyleSheet(self._hint_style())
        cl.addWidget(hint2)
        cl.addSpacing(4)
        self._separator(cl)

        # ===== 音效總開關 =====
        self._section_label(cl, "🔊 音效設定")
        self.sound_cb = QCheckBox("啟用倒數完成音效提示")
        self.sound_cb.setChecked(self.current_settings.get("sound", True))
        self.sound_cb.setStyleSheet(
            f"QCheckBox {{ color: {AppTheme.TEXT_PRIMARY}; font-size: 12px;"
            f" background: transparent; spacing: 4px; }}"
            f"QCheckBox::indicator {{ width: 14px; height: 14px; border-radius: 3px;"
            f" border: 1px solid {AppTheme.GOLD_MUTED}; background: {AppTheme.BG_TERTIARY}; }}"
            f"QCheckBox::indicator:checked {{"
            f" background: {AppTheme.GOLD_PRIMARY}; border-color: {AppTheme.GOLD_PRIMARY}; }}"
        )
        cl.addWidget(self.sound_cb)
        cl.addSpacing(8)
        self._separator(cl)

        # ===== 全域完成音效 =====
        self._section_label(cl, "🎵 全域完成音效")
        snd_row = QWidget()
        snd_row.setStyleSheet("background: transparent;")
        snd_r = QHBoxLayout(snd_row)
        snd_r.setContentsMargins(0, 4, 0, 4)
        snd_r.setSpacing(8)
        self.global_sound_combo = QComboBox()
        self.global_sound_combo.addItems(list(self._sound_label_map.keys()))
        self.global_sound_combo.setCurrentText(
            self._get_label_for_filename(self.current_settings.get("global_sound", ""))
        )
        self.global_sound_combo.setFixedWidth(220)
        self.global_sound_combo.setStyleSheet(self._combo_style())
        snd_r.addWidget(self.global_sound_combo)
        preview_btn1 = QPushButton("▶ 試聽")
        preview_btn1.setFixedSize(64, 32)
        preview_btn1.clicked.connect(
            lambda: self._preview_sound(self.global_sound_combo)
        )
        preview_btn1.setStyleSheet(self._small_btn_style())
        snd_r.addWidget(preview_btn1)
        snd_r.addStretch()
        cl.addWidget(snd_row)
        self._separator(cl)

        # ===== 全域提前提示音效 =====
        self._section_label(cl, "🎵 全域提前提示音效")
        asnd_row = QWidget()
        asnd_row.setStyleSheet("background: transparent;")
        asnd_r = QHBoxLayout(asnd_row)
        asnd_r.setContentsMargins(0, 4, 0, 4)
        asnd_r.setSpacing(8)
        self.global_alert_sound_combo = QComboBox()
        self.global_alert_sound_combo.addItems(list(self._sound_label_map.keys()))
        self.global_alert_sound_combo.setCurrentText(
            self._get_label_for_filename(
                self.current_settings.get("global_alert_sound", "")
            )
        )
        self.global_alert_sound_combo.setFixedWidth(220)
        self.global_alert_sound_combo.setStyleSheet(self._combo_style())
        asnd_r.addWidget(self.global_alert_sound_combo)
        preview_btn2 = QPushButton("▶ 試聽")
        preview_btn2.setFixedSize(64, 32)
        preview_btn2.clicked.connect(
            lambda: self._preview_sound(self.global_alert_sound_combo)
        )
        preview_btn2.setStyleSheet(self._small_btn_style())
        asnd_r.addWidget(preview_btn2)
        asnd_r.addStretch()
        cl.addWidget(asnd_row)
        self._separator(cl)

        # ===== 匯入自訂音效 =====
        self._section_label(cl, "📂 新增自訂音效")
        import_btn = QPushButton("＋ 匯入音效檔案 (.wav / .mp3)")
        import_btn.setFixedHeight(32)
        import_btn.clicked.connect(self._import_sound)
        import_btn.setStyleSheet(
            f"QPushButton {{ background-color: {AppTheme.BG_TERTIARY};"
            f" color: {AppTheme.TEXT_PRIMARY}; border: 1px solid {AppTheme.GOLD_MUTED};"
            f" border-radius: {AppTheme.CORNER_SM}px;"
            f" padding: 3px 10px; font-size: 11px; }}"
            f"QPushButton:hover {{ background-color: {AppTheme.GOLD_MUTED}; }}"
        )
        cl.addWidget(import_btn)
        hint3 = QLabel("💡 匯入後可在上方下拉選單中選擇")
        hint3.setStyleSheet(self._hint_style())
        cl.addWidget(hint3)
        cl.addSpacing(4)

        # ===== 儲存按鈕 =====
        save_btn = QPushButton("✓ 儲存設定")
        save_btn.setFixedSize(160, 40)
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

    def _make_lineedit(self, text, width):
        le = QLineEdit(text)
        le.setFixedWidth(width)
        le.setFixedHeight(32)
        le.setStyleSheet(
            f"QLineEdit {{ background-color: {AppTheme.BG_CARD};"
            f" color: {AppTheme.TEXT_PRIMARY}; border: 1px solid {AppTheme.GOLD_MUTED};"
            f" border-radius: {AppTheme.CORNER_SM}px; padding: 3px 6px; font-size: 11px; }}"
            f"QLineEdit:focus {{ border-color: {AppTheme.GOLD_PRIMARY}; }}"
        )
        return le

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
            f" border-radius: {AppTheme.CORNER_SM}px; font-size: 11px; }}"
            f"QPushButton:hover {{ background-color: {AppTheme.GOLD_MUTED}; }}"
        )

    def _hint_style(self):
        return (
            f"color: {AppTheme.TEXT_MUTED}; font-size: 11px;"
            f" background: transparent; border: none; padding: 2px 0;"
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

    def _preview_sound(self, combo):
        """試聽指定下拉選單目前選擇的音效"""
        label    = combo.currentText()
        filename = self._sound_label_map.get(label, "")
        if filename and self.sound_manager:
            self.sound_manager.play(filename)

    def _import_sound(self):
        """開啟檔案選擇器匯入音效"""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "選擇音效檔案", "",
            "音效檔案 (*.wav *.mp3);;WAV 檔案 (*.wav);;MP3 檔案 (*.mp3)"
        )
        if not filepath or not self.sound_manager:
            return

        new_name = self.sound_manager.import_sound(filepath)
        if new_name:
            self._build_sound_options()
            new_values = list(self._sound_label_map.keys())
            self.global_sound_combo.clear()
            self.global_sound_combo.addItems(new_values)
            self.global_alert_sound_combo.clear()
            self.global_alert_sound_combo.addItems(new_values)
            new_label = self.sound_manager.get_sound_label(new_name)
            self.global_sound_combo.setCurrentText(new_label)
            QMessageBox.information(self, "匯入成功", f"已成功匯入音效: {new_name}")
        else:
            QMessageBox.critical(
                self, "匯入失敗",
                "無法匯入音效檔案，請確認檔案格式為 .wav 或 .mp3"
            )

    def _save(self):
        """儲存設定"""
        try:
            x_val        = int(self.x_entry.text())
            y_val        = int(self.y_entry.text())
            alert_before = int(self.alert_entry.text())
        except ValueError:
            QMessageBox.critical(self, "錯誤", "請輸入有效的數字！")
            return

        if x_val < 0 or y_val < 0:
            QMessageBox.critical(self, "錯誤", "座標值不能為負數！")
            return
        if alert_before < 0:
            QMessageBox.critical(self, "錯誤", "提前秒數不能為負數！")
            return

        selected_label = self.size_combo.currentText()
        window_size    = self.WINDOW_SIZE_OPTIONS.get(selected_label, 64)
        global_sound   = self._sound_label_map.get(
            self.global_sound_combo.currentText(), ""
        )
        global_alert_sound = self._sound_label_map.get(
            self.global_alert_sound_combo.currentText(), ""
        )

        self.result = {
            "x":                    x_val,
            "y":                    y_val,
            "sound":                self.sound_cb.isChecked(),
            "alert_before_seconds": alert_before,
            "window_size":          window_size,
            "global_sound":         global_sound,
            "global_alert_sound":   global_alert_sound,
        }
        self.accept()

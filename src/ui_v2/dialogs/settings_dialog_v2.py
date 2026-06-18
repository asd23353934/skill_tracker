"""
V2 SettingsDialog — 全域設定對話框

8 個欄位 1:1 對應 V1 SettingsDialog；確認後呼叫 app.apply_settings(result)。
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSpinBox,
    QCheckBox, QComboBox, QSlider, QStyle, QStyleOptionSlider,
)
from PySide6.QtCore import Qt


class _JumpSlider(QSlider):
    """點擊任一位置直接跳到該值的 QSlider（預設只 page-step 不直觀）"""
    def mousePressEvent(self, e):  # noqa: N802
        if e.button() == Qt.MouseButton.LeftButton:
            opt = QStyleOptionSlider()
            self.initStyleOption(opt)
            handle = self.style().subControlRect(
                QStyle.ComplexControl.CC_Slider, opt,
                QStyle.SubControl.SC_SliderHandle, self,
            )
            if not handle.contains(e.position().toPoint()):
                # 點 track，不在 handle 上 → 跳到該位置
                if self.orientation() == Qt.Orientation.Horizontal:
                    pos = int(e.position().x()) - handle.width() // 2
                    span = self.width() - handle.width()
                else:
                    pos = int(e.position().y()) - handle.height() // 2
                    span = self.height() - handle.height()
                value = QStyle.sliderValueFromPosition(
                    self.minimum(), self.maximum(), pos, span,
                    opt.upsideDown,
                )
                self.setValue(value)
                e.accept()
                return
        super().mousePressEvent(e)

from src.ui_v2.theme_v2 import V2Theme as T
from src.ui_v2.dialogs.base_dialog_v2 import BaseDialogV2
from src.ui_v2.components import make_primary_button


_NO_SOUND_LABEL = "— 無 —"


def _row(label_text: str, widget: QWidget) -> QWidget:
    """label 在左、widget 在右的水平列。"""
    wrap = QWidget()
    h = QHBoxLayout(wrap)
    h.setContentsMargins(0, 0, 0, 0)
    h.setSpacing(T.S_MD)
    lbl = QLabel(label_text)
    lbl.setStyleSheet(
        f"color: {T.TEXT_DIM}; background: transparent;"
        f" font-size: 11px; font-weight: 600; min-width: 110px;"
    )
    h.addWidget(lbl)
    h.addWidget(widget, 1)
    return wrap


def _spin(value: int, lo: int, hi: int, suffix: str = "") -> QSpinBox:
    sb = QSpinBox()
    sb.setRange(lo, hi)
    sb.setValue(int(value))
    if suffix:
        sb.setSuffix(suffix)
    sb.setFixedHeight(28)
    sb.setStyleSheet(
        f"QSpinBox {{ background: {T.BG_INPUT}; color: {T.TEXT};"
        f" border: 1px solid {T.BORDER}; border-radius: {T.R_SM}px;"
        f" padding: 0 6px; font-size: 12px; }}"
        f"QSpinBox:focus {{ border-color: {T.ORANGE}; }}"
    )
    return sb


def _build_sound_combo(sound_manager, current_filename: str) -> tuple[QComboBox, dict]:
    """建 V2 樣式 combo + label→filename map。第一項固定為「— 無 —」。"""
    label_map: dict[str, str] = {_NO_SOUND_LABEL: ""}
    if sound_manager is not None:
        for fn in sound_manager.list_sounds():
            label_map[sound_manager.get_sound_label(fn)] = fn

    combo = QComboBox()
    combo.addItems(list(label_map.keys()))
    current_label = _NO_SOUND_LABEL
    for label, fn in label_map.items():
        if fn == current_filename:
            current_label = label
            break
    combo.setCurrentText(current_label)
    combo.setFixedHeight(28)
    combo.setStyleSheet(
        T.combo_qss(bg=T.BG_INPUT, border=T.BORDER, padding="0 8px")
    )
    return combo, label_map


class SettingsDialogV2(BaseDialogV2):
    """V2 設定對話框（8 欄與 V1 SettingsDialog 等價）"""

    def __init__(self, parent, app):
        super().__init__(parent, title="設定", width=460, height=620)
        self.app = app
        self._end_label_map: dict[str, str] = {}
        self._alert_label_map: dict[str, str] = {}
        self._build_form()
        self._build_footer()

    # ── 表單 ──
    def _build_form(self):
        body = self.body_layout()
        a = self.app
        sound_mgr = getattr(a, "sound_manager", None)

        # 技能視窗預設位置 X / Y
        self.x_spin = _spin(a.skill_start_x, 0, 9999)
        self.y_spin = _spin(a.skill_start_y, 0, 9999)
        xy_wrap = QWidget()
        xy_h = QHBoxLayout(xy_wrap)
        xy_h.setContentsMargins(0, 0, 0, 0)
        xy_h.setSpacing(T.S_SM)
        xy_h.addWidget(self.x_spin, 1)
        xy_h.addWidget(QLabel("×"))
        xy_h.addWidget(self.y_spin, 1)
        body.addWidget(_row("技能視窗位置", xy_wrap))

        # 完成 / 提前提示音 mute 旗標（移到聲音下拉列右邊；行為等同舊版兩個 enable checkbox）
        # 與技能詳細設定對齊：勾起 = 靜音 / 不勾 = 啟用
        self._cb_qss = (
            f"QCheckBox {{ color: {T.TEXT}; background: transparent;"
            f" font-size: 12px; spacing: 4px; }}"
        )
        self.end_mute_cb = QCheckBox("靜音")
        self.end_mute_cb.setCursor(Qt.CursorShape.PointingHandCursor)
        self.end_mute_cb.setStyleSheet(self._cb_qss)
        self.end_mute_cb.setChecked(not bool(getattr(a, "enable_end_sound", True)))
        self.alert_mute_cb = QCheckBox("靜音")
        self.alert_mute_cb.setCursor(Qt.CursorShape.PointingHandCursor)
        self.alert_mute_cb.setStyleSheet(self._cb_qss)
        self.alert_mute_cb.setChecked(not bool(getattr(a, "enable_alert_sound", True)))
        _cb_qss = self._cb_qss

        # 全域提前提示秒
        self.alert_spin = _spin(a.alert_before_seconds, 0, 99, suffix=" 秒")
        body.addWidget(_row("全域提前提示", self.alert_spin))

        # 視窗大小（小 / 中 / 大 / 超大 → 48 / 64 / 96 / 128 px）
        self.size_combo = QComboBox()
        self._size_map = {
            "小 (48 px)":  48,
            "中 (64 px)":  64,
            "大 (96 px)":  96,
            "超大 (128 px)": 128,
        }
        self.size_combo.addItems(list(self._size_map.keys()))
        cur_size = int(a.window_size or 96)
        # 找出最接近的選項；不在表內就視為「大」
        for label, px in self._size_map.items():
            if px == cur_size:
                self.size_combo.setCurrentText(label)
                break
        else:
            self.size_combo.setCurrentText("大 (96 px)")
        self.size_combo.setFixedHeight(28)
        self.size_combo.setStyleSheet(
            T.combo_qss(bg=T.BG_INPUT, border=T.BORDER, padding="0 8px")
        )
        body.addWidget(_row("技能視窗尺寸", self.size_combo))

        # 全域結束聲音
        self.end_combo, self._end_label_map = _build_sound_combo(
            sound_mgr, a.global_sound or ""
        )
        end_wrap = self._wrap_combo_with_preview(
            self.end_combo, self._end_label_map, self.end_mute_cb,
        )
        body.addWidget(_row("全域結束聲音", end_wrap))

        # 全域提前聲音
        self.alert_combo, self._alert_label_map = _build_sound_combo(
            sound_mgr, a.global_alert_sound or ""
        )
        alert_wrap = self._wrap_combo_with_preview(
            self.alert_combo, self._alert_label_map, self.alert_mute_cb,
        )
        body.addWidget(_row("全域提前聲音", alert_wrap))

        # 音量
        self.volume_slider = _JumpSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(int(a.sound_volume))
        self.volume_label = QLabel(f"{int(a.sound_volume)}%")
        self.volume_label.setStyleSheet(
            f"color: {T.TEXT_HI}; background: transparent;"
            f" font-size: 11px; font-weight: 700; min-width: 38px;"
        )
        # 記下原音量以便取消時還原
        self._original_volume = int(a.sound_volume)
        self.volume_slider.valueChanged.connect(self._on_volume_changed)
        vol_wrap = QWidget()
        vh = QHBoxLayout(vol_wrap)
        vh.setContentsMargins(0, 0, 0, 0)
        vh.setSpacing(T.S_SM)
        vh.addWidget(self.volume_slider, 1)
        vh.addWidget(self.volume_label)
        body.addWidget(_row("音量", vol_wrap))

        # 快捷鍵限定前景視窗（checkbox + 目標標籤 + 選擇按鈕 三件併同一行）
        self._hotkey_target_exe   = getattr(a, "hotkey_app_target_exe", "") or ""
        self._hotkey_target_label = getattr(a, "hotkey_app_target_label", "") or ""
        self.hotkey_filter_cb = QCheckBox("啟用")
        _has_target = bool(self._hotkey_target_exe)
        # 未選目標前不可啟用，避免「啟用卻無目標 → 靜默全域觸發」的矛盾狀態
        self.hotkey_filter_cb.setChecked(bool(getattr(a, "hotkey_app_filter_enabled", False)) and _has_target)
        self.hotkey_filter_cb.setEnabled(_has_target)
        self.hotkey_filter_cb.setStyleSheet(_cb_qss)

        self.hotkey_target_lbl = QLabel(self._hotkey_target_label or "未選擇")
        self.hotkey_target_lbl.setTextFormat(Qt.TextFormat.PlainText)  # 標題來自外部程式，防 rich-text 解讀
        self.hotkey_target_lbl.setStyleSheet(
            f"color: {T.TEXT_HI}; background: transparent; font-size: 11px;")
        pick_btn = QPushButton("選擇視窗…")
        pick_btn.setFixedHeight(28)
        pick_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        pick_btn.setStyleSheet(
            f"QPushButton {{ background: {T.BG_INPUT}; color: {T.TEXT_DIM};"
            f" border: 1px solid {T.BORDER}; border-radius: {T.R_SM}px;"
            f" padding: 0 12px; font-size: 11px; }}"
            f"QPushButton:hover {{ background: {T.BG_HOVER}; color: {T.TEXT_HI}; }}"
        )
        pick_btn.clicked.connect(self._open_window_picker)
        hotkey_wrap = QWidget()
        hotkey_h = QHBoxLayout(hotkey_wrap)
        hotkey_h.setContentsMargins(0, 0, 0, 0)
        hotkey_h.setSpacing(T.S_SM)
        hotkey_h.addWidget(self.hotkey_filter_cb)
        hotkey_h.addWidget(self.hotkey_target_lbl, 1)
        hotkey_h.addWidget(pick_btn)
        body.addWidget(_row("快捷鍵限定", hotkey_wrap))

        body.addStretch()

    def _open_window_picker(self):
        """開啟視窗挑選器，選定後更新待套用的目標 exe / 標題。"""
        from src.ui_v2.dialogs.window_picker_dialog_v2 import WindowPickerDialogV2
        dlg = WindowPickerDialogV2(self, self.app)
        if dlg.exec():
            self._hotkey_target_exe   = dlg.selected_exe()
            self._hotkey_target_label = dlg.selected_label()
            self.hotkey_target_lbl.setText(self._hotkey_target_label or "未選擇")
            self.hotkey_filter_cb.setEnabled(bool(self._hotkey_target_exe))

    def _wrap_combo_with_preview(self, combo: QComboBox, label_map: dict,
                                 mute_cb: QCheckBox) -> QWidget:
        wrap = QWidget()
        h = QHBoxLayout(wrap)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(T.S_SM)
        h.addWidget(combo, 1)
        preview = QPushButton("試聽")
        preview.setFixedHeight(28)
        preview.setCursor(Qt.CursorShape.PointingHandCursor)
        preview.setStyleSheet(
            f"QPushButton {{ background: {T.BG_INPUT}; color: {T.TEXT_DIM};"
            f" border: 1px solid {T.BORDER}; border-radius: {T.R_SM}px;"
            f" padding: 0 12px; font-size: 11px; }}"
            f"QPushButton:hover {{ background: {T.BG_HOVER};"
            f" color: {T.TEXT_HI}; }}"
        )
        preview.clicked.connect(lambda: self._preview(combo, label_map))
        h.addWidget(preview)
        h.addWidget(mute_cb)

        # 靜音 → 禁用下拉與試聽（與技能詳細設定一致）
        def _sync():
            muted = mute_cb.isChecked()
            combo.setEnabled(not muted)
            preview.setEnabled(not muted)
        _sync()
        mute_cb.toggled.connect(lambda _: _sync())
        return wrap

    def _preview(self, combo: QComboBox, label_map: dict):
        filename = label_map.get(combo.currentText(), "")
        sm = getattr(self.app, "sound_manager", None)
        if filename and sm is not None:
            sm.play(filename)

    def _on_volume_changed(self, v: int):
        """slider 變動：即時更新 label + sound_manager 音量（讓試聽即用即準）"""
        self.volume_label.setText(f"{v}%")
        sm = getattr(self.app, "sound_manager", None)
        if sm is not None:
            sm.set_volume(v / 100.0)

    # ── 底部按鈕 ──
    def _build_footer(self):
        footer = self.footer_layout()
        cancel = QPushButton("取消")
        cancel.setFixedHeight(30)
        cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel.setStyleSheet(
            f"QPushButton {{ background: transparent; color: {T.TEXT_DIM};"
            f" border: 1px solid {T.BORDER}; border-radius: {T.R_SM}px;"
            f" padding: 0 16px; font-size: 12px; }}"
            f"QPushButton:hover {{ color: {T.TEXT_HI};"
            f" border-color: {T.BORDER_HOVER}; }}"
        )
        cancel.clicked.connect(self._on_cancel)

        confirm = make_primary_button("確認", padding="0 18px", weight=700, height=30)
        confirm.clicked.connect(self._on_confirm)

        footer.addWidget(cancel)
        footer.addWidget(confirm)

    # ── 動作 ──
    def _build_result(self) -> dict:
        return {
            "x":                  int(self.x_spin.value()),
            "y":                  int(self.y_spin.value()),
            # 靜音 checkbox 與舊版 enable checkbox 為相反語意
            "enable_end_sound":   not bool(self.end_mute_cb.isChecked()),
            "enable_alert_sound": not bool(self.alert_mute_cb.isChecked()),
            "alert_before_seconds": int(self.alert_spin.value()),
            "window_size":        self._size_map.get(self.size_combo.currentText(), 96),
            "global_sound":       self._end_label_map.get(self.end_combo.currentText(), ""),
            "global_alert_sound": self._alert_label_map.get(self.alert_combo.currentText(), ""),
            "sound_volume":       int(self.volume_slider.value()),
            "hotkey_app_filter_enabled": bool(self.hotkey_filter_cb.isChecked()) and bool(self._hotkey_target_exe),
            "hotkey_app_target_exe":     self._hotkey_target_exe,
            "hotkey_app_target_label":   self._hotkey_target_label,
        }

    def _on_confirm(self):
        result = self._build_result()
        self.app.apply_settings(result)
        self.accept()

    def _on_cancel(self):
        # 試聽期間已即時改 sound_manager 音量；取消時還原為打開時的值
        sm = getattr(self.app, "sound_manager", None)
        if sm is not None:
            sm.set_volume(self._original_volume / 100.0)
        self.reject()

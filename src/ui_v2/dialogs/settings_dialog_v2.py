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
        f"QComboBox {{ background: {T.BG_INPUT}; color: {T.TEXT};"
        f" border: 1px solid {T.BORDER}; border-radius: {T.R_SM}px;"
        f" padding: 0 8px; font-size: 12px; }}"
        f"QComboBox:hover {{ border-color: {T.BORDER_HOVER}; }}"
        f"QComboBox::drop-down {{ border: none; width: 16px; }}"
    )
    return combo, label_map


class SettingsDialogV2(BaseDialogV2):
    """V2 設定對話框（8 欄與 V1 SettingsDialog 等價）"""

    def __init__(self, parent, app):
        super().__init__(parent, title="設定", width=460, height=540)
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

        # 啟用聲音
        self.sound_cb = QCheckBox("啟用聲音")
        self.sound_cb.setChecked(bool(a.enable_sound))
        self.sound_cb.setStyleSheet(
            f"QCheckBox {{ color: {T.TEXT}; background: transparent;"
            f" font-size: 12px; }}"
        )
        body.addWidget(_row("音效開關", self.sound_cb))

        # 全域提前提示秒
        self.alert_spin = _spin(a.alert_before_seconds, 0, 99, suffix=" 秒")
        body.addWidget(_row("全域提前提示", self.alert_spin))

        # 視窗大小
        self.size_spin = _spin(a.window_size, 32, 128, suffix=" px")
        body.addWidget(_row("技能視窗尺寸", self.size_spin))

        # 全域結束聲音
        self.end_combo, self._end_label_map = _build_sound_combo(
            sound_mgr, a.global_sound or ""
        )
        end_wrap = self._wrap_combo_with_preview(self.end_combo, self._end_label_map)
        body.addWidget(_row("全域結束聲音", end_wrap))

        # 全域提前聲音
        self.alert_combo, self._alert_label_map = _build_sound_combo(
            sound_mgr, a.global_alert_sound or ""
        )
        alert_wrap = self._wrap_combo_with_preview(self.alert_combo, self._alert_label_map)
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

        body.addStretch()

    def _wrap_combo_with_preview(self, combo: QComboBox, label_map: dict) -> QWidget:
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

        confirm = QPushButton("確認")
        confirm.setFixedHeight(30)
        confirm.setCursor(Qt.CursorShape.PointingHandCursor)
        confirm.setStyleSheet(
            f"QPushButton {{ background: {T.ORANGE}; color: #ffffff;"
            f" border: none; border-radius: {T.R_SM}px;"
            f" padding: 0 18px; font-size: 12px; font-weight: 700; }}"
            f"QPushButton:hover {{ background: #ff9d5a; }}"
        )
        confirm.clicked.connect(self._on_confirm)

        footer.addWidget(cancel)
        footer.addWidget(confirm)

    # ── 動作 ──
    def _build_result(self) -> dict:
        return {
            "x":                  int(self.x_spin.value()),
            "y":                  int(self.y_spin.value()),
            "sound":              bool(self.sound_cb.isChecked()),
            "alert_before_seconds": int(self.alert_spin.value()),
            "window_size":        int(self.size_spin.value()),
            "global_sound":       self._end_label_map.get(self.end_combo.currentText(), ""),
            "global_alert_sound": self._alert_label_map.get(self.alert_combo.currentText(), ""),
            "sound_volume":       int(self.volume_slider.value()),
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

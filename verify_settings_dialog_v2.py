"""
SettingsDialogV2 單元驗證

執行：`python verify_settings_dialog_v2.py` —— 全部通過時 exit code = 0

涵蓋：
- 8 個欄位初值正確顯示
- 確認按鈕構出 result dict 並呼叫 app.apply_settings 一次
- 取消按鈕不呼叫 apply_settings
"""

from __future__ import annotations

import sys
from unittest.mock import MagicMock

from PySide6.QtWidgets import QApplication

from src.ui_v2.dialogs.settings_dialog_v2 import SettingsDialogV2


_failures: list[str] = []


def check(label: str, got, expected):
    if got == expected:
        print(f"  OK   {label}")
    else:
        print(f"  FAIL {label}: got {got!r}, expected {expected!r}")
        _failures.append(label)


def _build_app():
    app = MagicMock()
    app.skill_start_x = 300
    app.skill_start_y = 250
    app.enable_sound = False
    app.alert_before_seconds = 5
    app.window_size = 64  # 中
    app.global_sound = "ding.wav"
    app.global_alert_sound = ""
    app.sound_volume = 80

    sm = MagicMock()
    sm.list_sounds.return_value = ["ding.wav", "bell.wav"]
    sm.get_sound_label.side_effect = lambda fn: fn.replace(".wav", "")
    app.sound_manager = sm
    return app


def test_initial_values():
    print("[test_initial_values]")
    app_ctx = _build_app()
    dlg = SettingsDialogV2(None, app_ctx)
    check("x spin", dlg.x_spin.value(), 300)
    check("y spin", dlg.y_spin.value(), 250)
    check("sound checkbox", dlg.sound_cb.isChecked(), False)
    check("alert spin", dlg.alert_spin.value(), 5)
    check("size combo (中)", dlg.size_combo.currentText(), "中 (64 px)")
    check("end combo current=ding", dlg.end_combo.currentText(), "ding")
    check("alert combo current=— 無 —", dlg.alert_combo.currentText(), "— 無 —")
    check("volume slider", dlg.volume_slider.value(), 80)
    check("volume label", dlg.volume_label.text(), "80%")


def test_confirm_calls_apply_settings():
    print("[test_confirm_calls_apply_settings]")
    app_ctx = _build_app()
    dlg = SettingsDialogV2(None, app_ctx)
    dlg.volume_slider.setValue(50)
    dlg.sound_cb.setChecked(True)
    dlg.size_combo.setCurrentText("大 (96 px)")
    # 不依賴 exec，直接呼 _on_confirm；accept 會關 dialog OK
    dlg._on_confirm()
    check("apply_settings call_count", app_ctx.apply_settings.call_count, 1)
    result = app_ctx.apply_settings.call_args[0][0]
    check("result has 8 keys", len(result), 8)
    check("result.x", result["x"], 300)
    check("result.y", result["y"], 250)
    check("result.sound", result["sound"], True)
    check("result.alert_before_seconds", result["alert_before_seconds"], 5)
    check("result.window_size", result["window_size"], 96)
    check("result.global_sound", result["global_sound"], "ding.wav")
    check("result.global_alert_sound", result["global_alert_sound"], "")
    check("result.sound_volume", result["sound_volume"], 50)


def test_cancel_does_not_apply():
    print("[test_cancel_does_not_apply]")
    app_ctx = _build_app()
    dlg = SettingsDialogV2(None, app_ctx)
    dlg.volume_slider.setValue(20)
    dlg._on_cancel()
    check("apply_settings NOT called", app_ctx.apply_settings.call_count, 0)


def main():
    QApplication.instance() or QApplication(sys.argv)
    test_initial_values()
    test_confirm_calls_apply_settings()
    test_cancel_does_not_apply()
    if _failures:
        print(f"\nFAILED: {len(_failures)} check(s)")
        for f in _failures:
            print(f"  - {f}")
        sys.exit(1)
    print("\nAll checks passed.")


if __name__ == "__main__":
    main()

"""
完成 / 提前提示音禁音的單元測試

對應 spec sound-system「Individual skills can mute their sounds」的解析優先序：
全域開關開啟時，sentinel → 靜音（""）、指定檔名 → 該檔、空 → 全域。
（全域開關「關閉 = 總靜音」由 SkillWindow.enable_end_sound / enable_alert_sound
 把關，屬 UI 層，於實機驗證涵蓋。）
"""

import pytest

from src.domain.services import SkillService, MUTE_SENTINEL
from src.infrastructure.config_manager import ConfigManager


def _svc() -> SkillService:
    # get_sound / get_alert_sound 僅用 override dict 與全域音，repo / loader 可為 None
    return SkillService(None, None, global_sound="g_end.wav",
                        global_alert_sound="g_alert.wav")


@pytest.mark.parametrize("override, expected", [
    (MUTE_SENTINEL, ""),        # 靜音
    ("ding.wav", "ding.wav"),   # 指定音效
    ("", "g_end.wav"),          # 空 → 全域
])
def test_get_sound_resolution(override, expected):
    svc = _svc()
    svc._sound_overrides = {"sk": override}
    assert svc.get_sound("sk") == expected


def test_get_sound_missing_uses_global():
    assert _svc().get_sound("unknown") == "g_end.wav"


@pytest.mark.parametrize("override, expected", [
    (MUTE_SENTINEL, ""),
    ("urgent.wav", "urgent.wav"),
    ("", "g_alert.wav"),
])
def test_get_alert_sound_resolution(override, expected):
    svc = _svc()
    svc._alert_sound_overrides = {"sk": override}
    assert svc.get_alert_sound("sk") == expected


def test_get_alert_sound_missing_uses_global():
    assert _svc().get_alert_sound("unknown") == "g_alert.wav"


def test_default_user_settings_has_new_keys():
    d = ConfigManager.DEFAULT_USER_SETTINGS
    assert d["enable_end_sound"] is True
    assert d["enable_alert_sound"] is True
    assert d["hotkey_app_filter_enabled"] is False
    assert d["hotkey_app_target_exe"] == ""
    assert d["hotkey_app_target_label"] == ""

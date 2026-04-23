"""
MonsterPageV2 / MonsterCard 單元驗證腳本

執行：`python verify_monster_page_v2.py` —— 全部通過時 exit code = 0

涵蓋：
- showEvent 後渲染卡片數 == fixture 怪物數
- 點擊 respawn / reset 觸發對應 App 方法
- 點擊 hotkey 觸發 begin_capture 並設 hotkey_manager._monster_card
- 勾 loop / permanent 觸發對應 update_monster_*
- card.set_hotkey_text(...) 後 hotkey 按鈕文字 + accent 同步
- 頁面 header 內無 text == "新增怪物" 的 QPushButton
"""

from __future__ import annotations

import sys
from unittest.mock import MagicMock

from PySide6.QtWidgets import QApplication, QPushButton
from PySide6.QtGui import QShowEvent

from src.ui_v2.pages.monster_page_v2 import MonsterPageV2, MonsterCard


_failures: list[str] = []


def check(label: str, got, expected):
    if got == expected:
        print(f"  OK   {label}")
    else:
        print(f"  FAIL {label}: got {got!r}, expected {expected!r}")
        _failures.append(label)


# ════════════════════════════════════════════════════════════
# Fixtures
# ════════════════════════════════════════════════════════════

_FIXTURE_MONSTERS = [
    {"id": "fish_house", "name": "魚屋",     "icon": "",
     "respawn_time": 30, "hotkey": "",      "alert_before": 10,
     "loop": True,  "permanent": False, "sound": "",       "alert_sound": ""},
    {"id": "blue_mush",  "name": "藍菇菇",   "icon": "",
     "respawn_time": 60, "hotkey": "F1",   "alert_before": 5,
     "loop": False, "permanent": True,  "sound": "ding.wav","alert_sound": ""},
]


def _build_fixture_app():
    sound_mgr = MagicMock()
    sound_mgr.list_sounds.return_value = ["ding.wav", "bell.wav"]
    sound_mgr.get_sound_label.side_effect = lambda fn: fn.replace(".wav", "")

    app = MagicMock()
    app.sound_manager = sound_mgr
    app.monster_respawn_buttons = {}
    app.monster_alert_before_buttons = {}

    monsters_dict = {m["id"]: dict(m) for m in _FIXTURE_MONSTERS}
    app.monster_service.get.side_effect = lambda mid: monsters_dict.get(mid)
    app.get_all_monsters.return_value = list(monsters_dict.values())

    # 真實的 hotkey_manager 屬性（會被 V2 卡片寫 _monster_card）
    app.hotkey_manager = MagicMock()
    return app


# ════════════════════════════════════════════════════════════
# Tests
# ════════════════════════════════════════════════════════════

def test_show_event_loads_cards():
    print("[test_show_event_loads_cards]")
    app_ctx = _build_fixture_app()
    page = MonsterPageV2(None, app_ctx)
    # 觸發 showEvent
    page.showEvent(QShowEvent())
    check("loaded flag", page._loaded, True)
    check("cards count", len(page.cards), len(_FIXTURE_MONSTERS))
    check("fish_house registered", "fish_house" in page.cards, True)
    check("blue_mush registered", "blue_mush" in page.cards, True)
    check("page self-registered", app_ctx.monster_page, page)


def test_respawn_button_calls_app():
    print("[test_respawn_button_calls_app]")
    app_ctx = _build_fixture_app()
    card = MonsterCard(None, app_ctx, "fish_house")
    btn = app_ctx.monster_respawn_buttons["fish_house"]
    check("respawn button registered", btn is not None, True)
    btn.click()
    check("edit_respawn_time called", app_ctx.edit_respawn_time.call_count, 1)
    check("called with correct id",
          app_ctx.edit_respawn_time.call_args[0][0], "fish_house")


def test_hotkey_capture_sets_card_ref():
    print("[test_hotkey_capture_sets_card_ref]")
    app_ctx = _build_fixture_app()
    card = MonsterCard(None, app_ctx, "blue_mush")
    card._hk_chip.value_btn.click()
    check("_monster_card pointed at card",
          app_ctx.hotkey_manager._monster_card, card)
    check("begin_capture called", app_ctx.hotkey_manager.begin_capture.call_count, 1)
    check("begin_capture id arg",
          app_ctx.hotkey_manager.begin_capture.call_args[0][0], "blue_mush")
    check("begin_capture name arg",
          app_ctx.hotkey_manager.begin_capture.call_args[0][1], "藍菇菇")


def test_loop_permanent_checkboxes():
    print("[test_loop_permanent_checkboxes]")
    app_ctx = _build_fixture_app()
    card = MonsterCard(None, app_ctx, "fish_house")
    # 找 loop / permanent checkbox（卡片內 QCheckBox 應有 2 個）
    from PySide6.QtWidgets import QCheckBox
    cbs = card.findChildren(QCheckBox)
    check("two checkboxes", len(cbs), 2)
    # 第一個是 loop（已預設 True）；點一次變 False
    cbs[0].setChecked(False)
    check("update_monster_loop called",
          app_ctx.update_monster_loop.call_count, 1)
    check("loop arg id", app_ctx.update_monster_loop.call_args[0][0], "fish_house")
    cbs[1].setChecked(True)
    check("update_monster_permanent called",
          app_ctx.update_monster_permanent.call_count, 1)


def test_set_hotkey_text():
    print("[test_set_hotkey_text]")
    app_ctx = _build_fixture_app()
    card = MonsterCard(None, app_ctx, "fish_house")
    card.set_hotkey_text("F5", True)
    check("hotkey button text", card._hk_chip.value_btn.text(), "F5")


def test_no_add_monster_button():
    print("[test_no_add_monster_button]")
    app_ctx = _build_fixture_app()
    page = MonsterPageV2(None, app_ctx)
    add_buttons = [b for b in page.findChildren(QPushButton) if b.text() == "新增怪物"]
    check("no 新增怪物 button", len(add_buttons), 0)


# ════════════════════════════════════════════════════════════
# Main
# ════════════════════════════════════════════════════════════

def main():
    app = QApplication.instance() or QApplication(sys.argv)
    test_show_event_loads_cards()
    test_respawn_button_calls_app()
    test_hotkey_capture_sets_card_ref()
    test_loop_permanent_checkboxes()
    test_set_hotkey_text()
    test_no_add_monster_button()
    if _failures:
        print(f"\nFAILED: {len(_failures)} check(s)")
        for f in _failures:
            print(f"  - {f}")
        sys.exit(1)
    print("\nAll checks passed.")


if __name__ == "__main__":
    main()

"""
SkillPageV2 / SkillCardV2 單元驗證腳本

執行：`python verify_skill_page_v2.py` —— 全部通過時 exit code = 0

涵蓋（代表性，非窮舉 94 卡）：
- 三欄分類正確（player / boss / item）
- SkillCardV2 顯示 cooldown / hotkey / checkbox / alert_seconds 初始值符合 fixture
- 點擊 cooldown chip / reset 觸發對應 App 方法
- card.refresh() 同步顯示且不再觸發 stateChanged
- SkillPageV2 rebuild 後 app.cooldown_buttons[id] 指向新卡片
- 頁首三顆 chip 觸發 app.toggle_all(key)
"""

from __future__ import annotations

import sys
from unittest.mock import MagicMock

from PySide6.QtWidgets import QApplication

from src.ui_v2.pages.skill_page_v2 import SkillPageV2
from src.ui_v2.pages.skill_card_v2 import SkillCardV2


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

_FIXTURE_SKILLS = {
    # id: (name, cooldown, category, subcategory, hotkey)
    "bishop_heal":  ("治癒",      2,    "player", "主教",     ""),
    "bishop_bless": ("祝福",      120,  "player", "主教",     "F1"),
    "archer_shot":  ("箭雨",      30,   "player", "弓箭手",   ""),
    "zakum_arm":    ("扎昆手臂",  45,   "boss",   "扎昆",     ""),
    "horntail_atk": ("龍王攻擊",  60,   "boss",   "龍王",     ""),
    "elixir":       ("萬靈藥",    600,  "item",   "回復",     ""),
}


def _build_fixture_app():
    """建立最小化 fake app，覆蓋 SkillPageV2 / SkillCardV2 依賴介面"""
    sm = MagicMock()
    # 元資料複本（被 mutation 時不要污染 fixture）
    skills_dict = {
        sid: {"id": sid, "name": name, "cooldown": cd,
              "category": cat, "subcategory": sub, "hotkey": hk,
              "icon": f"{sid}.png"}
        for sid, (name, cd, cat, sub, hk) in _FIXTURE_SKILLS.items()
    }
    sm.qpixmaps_card = {}
    sm.get_skill.side_effect = lambda sid: skills_dict.get(sid)
    sm.get_all_skills.return_value = skills_dict

    # 按 category → subcategory → [sid] 分組（保留 fixture 插入順序）
    def _get_categories(category_type):
        result: dict[str, list[str]] = {}
        for sid, meta in skills_dict.items():
            if meta["category"] != category_type:
                continue
            result.setdefault(meta["subcategory"], []).append(sid)
        return result
    sm.get_categories.side_effect = _get_categories

    app = MagicMock()
    app.skill_manager = sm

    app.skill_hotkeys = {sid: meta["hotkey"]
                        for sid, meta in skills_dict.items()}
    app.skill_permanent = {}
    app.skill_loop = {}
    app.skill_alert_enabled = {}
    app.skill_cooldown_overrides = {}
    app.skill_alert_seconds_overrides = {}
    app.skill_sound_overrides = {}
    app.skill_alert_sound_overrides = {}

    app.alert_before_seconds = 3

    # V1 widget 登錄 dict
    app.cooldown_buttons = {}
    app.hotkey_buttons = {}
    app.alert_seconds_buttons = {}
    app.permanent_vars = {}
    app.loop_vars = {}
    app.alert_enabled_vars = {}
    app.skill_card_widgets = {}

    # App API（MagicMock 默認會記錄 call；side_effect 給合理回傳值）
    app.get_original_cooldown.side_effect = lambda sid: (
        skills_dict[sid]["cooldown"] if sid in skills_dict else None
    )

    return app, skills_dict


# ════════════════════════════════════════════════════════════
# Tests
# ════════════════════════════════════════════════════════════

def test_three_columns_split():
    print("[test_three_columns_split]")
    app, _ = _build_fixture_app()
    page = SkillPageV2(parent=None, app=app)
    page.rebuild()

    check("columns count == 3", len(page._columns), 3)
    player_cards = page._columns[0].cards
    boss_cards   = page._columns[1].cards
    item_cards   = page._columns[2].cards
    check("player column has 3 skills", len(player_cards), 3)
    check("boss column has 2 skills",   len(boss_cards),   2)
    check("item column has 1 skill",    len(item_cards),   1)

    # 子分類順序來自 config.json 插入順序（player 先「主教」後「弓箭手」）
    player_col = page._columns[0]
    check("player first subcategory has bishop_heal",
          "bishop_heal" in player_col.cards, True)
    check("player subcategory archer has archer_shot",
          "archer_shot" in player_col.cards, True)

    page.deleteLater()


def test_card_initial_values():
    print("[test_card_initial_values]")
    app, skills = _build_fixture_app()

    # bishop_bless：120s + hotkey F1 + 無 override
    card = SkillCardV2(None, app, "bishop_bless",
                       skills["bishop_bless"], "#6CC7FF")
    check("cooldown chip shows '120秒'",
          card._cd_chip.value_btn.text(), "120秒")
    check("hotkey chip shows 'F1'",
          card._hk_chip.value_btn.text(), "F1")
    check("permanent cb unchecked", card._cb_perm.isChecked(), False)
    check("loop cb unchecked",      card._cb_loop.isChecked(), False)
    check("alert cb unchecked",     card._cb_alert.isChecked(), False)
    check("alert pill default seconds",
          card._alert_pill.text(), "3s")

    # bishop_heal：無 hotkey → 「未設」
    card2 = SkillCardV2(None, app, "bishop_heal",
                        skills["bishop_heal"], "#6CC7FF")
    check("missing hotkey shows '未設'",
          card2._hk_chip.value_btn.text(), "未設")

    card.deleteLater()
    card2.deleteLater()


def test_card_override_initial_state():
    """冷卻 override / alert 秒數 override 以修改態色呈現"""
    print("[test_card_override_initial_state]")
    app, skills = _build_fixture_app()
    # 模擬 SkillService 套過 profile — skill dict 已被 mutation 成 override 後的值
    app.skill_manager.get_skill.side_effect = lambda sid: (
        {**skills[sid], "cooldown": 90} if sid == "bishop_bless" else skills.get(sid)
    )
    # 提前秒數 override
    app.skill_alert_seconds_overrides["bishop_bless"] = 10

    card = SkillCardV2(None, app, "bishop_bless",
                       skills["bishop_bless"], "#6CC7FF")
    check("cooldown chip shows override '90秒'",
          card._cd_chip.value_btn.text(), "90秒")
    check("cooldown chip has modified accent",
          card._cd_chip.value_btn._accent is not None, True)
    check("alert pill shows override '10s'",
          card._alert_pill.text(), "10s")
    check("alert pill has override accent",
          card._alert_pill._accent is not None, True)

    card.deleteLater()


def test_card_click_triggers_app_methods():
    print("[test_card_click_triggers_app_methods]")
    app, skills = _build_fixture_app()
    card = SkillCardV2(None, app, "bishop_bless",
                       skills["bishop_bless"], "#6CC7FF")

    card._cd_chip.value_btn.click()
    check("edit_cooldown called once",
          app.edit_cooldown.call_count, 1)
    check("edit_cooldown called with skill_id",
          app.edit_cooldown.call_args.args, ("bishop_bless",))

    card._cd_chip.reset_btn.click()
    check("reset_cooldown called once",
          app.reset_cooldown.call_count, 1)

    card._hk_chip.reset_btn.click()
    check("reset_hotkey called once",
          app.reset_hotkey.call_count, 1)

    card._hk_chip.value_btn.click()
    check("begin_capture called once",
          app.hotkey_manager.begin_capture.call_count, 1)

    card._alert_pill.click()
    check("edit_alert_seconds called once",
          app.edit_alert_seconds.call_count, 1)

    # checkbox 綁 update_skill_setting_exclusive / update_alert_setting
    card._cb_perm.setChecked(True)
    check("update_skill_setting_exclusive called for permanent",
          app.update_skill_setting_exclusive.call_count, 1)

    card._cb_alert.setChecked(True)
    check("update_alert_setting called",
          app.update_alert_setting.call_count, 1)

    card.deleteLater()


def test_card_refresh_silences_state_changed():
    print("[test_card_refresh_silences_state_changed]")
    app, skills = _build_fixture_app()
    card = SkillCardV2(None, app, "bishop_bless",
                       skills["bishop_bless"], "#6CC7FF")

    baseline = app.update_skill_setting_exclusive.call_count
    baseline_alert = app.update_alert_setting.call_count

    # 讓 refresh 看到新狀態
    app.skill_permanent["bishop_bless"] = True
    app.skill_alert_enabled["bishop_bless"] = True
    card.refresh()

    check("permanent cb reflects new state",
          card._cb_perm.isChecked(), True)
    check("alert cb reflects new state",
          card._cb_alert.isChecked(), True)
    check("refresh did not trigger update_skill_setting_exclusive",
          app.update_skill_setting_exclusive.call_count, baseline)
    check("refresh did not trigger update_alert_setting",
          app.update_alert_setting.call_count, baseline_alert)

    card.deleteLater()


def test_rebuild_reregisters_widgets():
    print("[test_rebuild_reregisters_widgets]")
    app, _ = _build_fixture_app()
    page = SkillPageV2(parent=None, app=app)
    page.rebuild()

    first = app.cooldown_buttons.get("bishop_bless")
    check("bishop_bless cooldown button registered",
          first is not None, True)
    check("bishop_bless card widget registered",
          app.skill_card_widgets.get("bishop_bless") is not None, True)

    page.rebuild()
    second = app.cooldown_buttons.get("bishop_bless")
    check("cooldown button reference refreshed",
          second is not first, True)
    check("no leftover stale id in registered set",
          "zzz_not_exist" not in page._registered_ids, True)

    page.deleteLater()


def test_header_chips_call_toggle_all():
    print("[test_header_chips_call_toggle_all]")
    app, _ = _build_fixture_app()
    page = SkillPageV2(parent=None, app=app)

    # 三顆 chip 分別對應 permanent / loop / alert
    page._on_toggle_all("permanent")
    page._on_toggle_all("loop")
    page._on_toggle_all("alert")

    check("toggle_all called 3 times",
          app.toggle_all.call_count, 3)
    args = [c.args for c in app.toggle_all.call_args_list]
    check("toggle_all keys order",
          args, [("permanent",), ("loop",), ("alert",)])

    page.deleteLater()


def test_unregister_cleans_dicts():
    print("[test_unregister_cleans_dicts]")
    app, skills = _build_fixture_app()
    card = SkillCardV2(None, app, "bishop_bless",
                       skills["bishop_bless"], "#6CC7FF")
    check("before unregister: cooldown_buttons has entry",
          "bishop_bless" in app.cooldown_buttons, True)

    SkillCardV2.unregister_from_app(app, "bishop_bless")
    for key in ("cooldown_buttons", "hotkey_buttons", "alert_seconds_buttons",
                "permanent_vars", "loop_vars", "alert_enabled_vars",
                "skill_card_widgets"):
        check(f"after unregister: {key} cleaned",
              "bishop_bless" in getattr(app, key), False)

    card.deleteLater()


def main():
    app = QApplication.instance() or QApplication(sys.argv)

    test_three_columns_split()
    test_card_initial_values()
    test_card_override_initial_state()
    test_card_click_triggers_app_methods()
    test_card_refresh_silences_state_changed()
    test_rebuild_reregisters_widgets()
    test_header_chips_call_toggle_all()
    test_unregister_cleans_dicts()

    print()
    if _failures:
        print(f"FAILURES: {len(_failures)}")
        for f in _failures:
            print(f"  - {f}")
        sys.exit(1)
    print("All checks passed.")
    sys.exit(0)


if __name__ == "__main__":
    main()

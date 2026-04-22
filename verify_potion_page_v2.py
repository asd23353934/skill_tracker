"""
PotionPageV2 單元驗證腳本（專案無 tests/，先以獨立腳本涵蓋 spec example）
執行：`python verify_potion_page_v2.py` —— 全部通過時 exit code = 0
"""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from src.domain.potion_service import PotionService
from src.ui_v2.pages.potion_page_v2 import PotionPageV2


_failures: list[str] = []


def check(label: str, got, expected):
    if got == expected:
        print(f"  OK   {label}")
    else:
        print(f"  FAIL {label}: got {got!r}, expected {expected!r}")
        _failures.append(label)


class _FakeConfigManager:
    """最小化 config manager — 只覆蓋 V2 頁面會呼叫的 potion autosave 介面"""

    def __init__(self, autosave_data=None):
        self._autosave = autosave_data
        self._records: dict[str, dict] = {}
        self.save_calls: list[dict] = []

    def load_potion_autosave(self):
        return self._autosave

    def save_potion_autosave(self, data):
        self.save_calls.append(data)
        return True

    def delete_potion_autosave(self):
        self._autosave = None
        return True

    def list_potion_saves(self):
        return list(self._records.keys())

    def save_potion_record(self, name, data):
        self._records[name] = data
        return True

    def load_potion_record(self, name):
        return self._records.get(name)


class _FakeApp:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.toast = None


def _new_page(app):
    return PotionPageV2(parent=None, app=app)


def test_collect_form_shape():
    """PotionPageV2._collect_form() 輸出符合 PotionFormData schema"""
    print("[test_collect_form_shape]")
    cm = _FakeConfigManager(autosave_data=None)
    page = _new_page(_FakeApp(cm))

    form = page._collect_form()

    # 三個藥水 list
    for key in ("hp_potions", "mp_potions", "combined_potions"):
        check(f"{key} is list", isinstance(form.get(key), list), True)

    # 七個純量欄位
    for key in ("duration_minutes", "mesos_start", "mesos_end",
                "shop_before", "shop_after", "exp_start", "exp_end"):
        check(f"{key} is int", isinstance(form.get(key), int), True)

    # 初始狀態：三個區段皆為空
    check("hp_potions empty by default",
          len(form["hp_potions"]), 0)
    check("mp_potions empty by default",
          len(form["mp_potions"]), 0)
    check("combined_potions empty by default",
          len(form["combined_potions"]), 0)

    # 時間相關初始值
    check("duration_minutes default == 1", form["duration_minutes"], 1)

    page.deleteLater()


def test_autosave_restore_from_v1_dict():
    """V1 autosave 字典可被 V2 `_try_load_autosave` 還原（反向相容）"""
    print("[test_autosave_restore_from_v1_dict]")

    # 模擬 V1 autosave 輸出（saved_at + summary 為 V1 PotionService.serialize 產物）
    v1_autosave = {
        "saved_at": "2026-04-22T12:00:00",
        "duration_minutes": 45,
        "hp_potions": [
            {"name": "馴鹿奶", "price": 5600, "before": 200, "after": 150,
             "consumed": 50, "cost": 280000},
        ],
        "mp_potions": [],
        "combined_potions": [
            {"name": "超級藥水", "price": 35000, "before": 10, "after": 5,
             "consumed": 5, "cost": 175000},
        ],
        "mesos_start": 10000, "mesos_end": 50000,
        "shop_before": 0, "shop_after": 20000,
        "exp_start": 1000, "exp_end": 4000,
        "_timer_elapsed": 123,
    }

    cm = _FakeConfigManager(autosave_data=v1_autosave)
    page = _new_page(_FakeApp(cm))

    form = page._collect_form()
    check("duration_minutes restored", form["duration_minutes"], 45)
    check("hp_potions restored count", len(form["hp_potions"]), 1)
    check("hp_potions[0].name restored", form["hp_potions"][0]["name"], "馴鹿奶")
    check("hp_potions[0].price restored", form["hp_potions"][0]["price"], 5600)
    check("hp_potions[0].before restored", form["hp_potions"][0]["before"], 200)
    check("hp_potions[0].after restored", form["hp_potions"][0]["after"], 150)
    check("mp_potions cleared to 0", len(form["mp_potions"]), 0)
    check("combined_potions restored count", len(form["combined_potions"]), 1)
    check("mesos_start restored", form["mesos_start"], 10000)
    check("mesos_end restored",   form["mesos_end"],   50000)
    check("shop_after restored",  form["shop_after"],  20000)
    check("exp_end restored",     form["exp_end"],     4000)
    check("_timer_elapsed stored on page",
          page._timer_elapsed, 123)

    page.deleteLater()


def test_timer_controls_initial_state():
    """預設為手動模式 → 開始/重置按鈕隱藏；計時器未啟動"""
    print("[test_timer_controls_initial_state]")
    cm = _FakeConfigManager(autosave_data=None)
    page = _new_page(_FakeApp(cm))

    check("initial mode is manual", page._mode, "manual")
    check("start btn hidden in manual",
          page._timer_start_btn.isHidden(), True)
    check("reset btn hidden in manual",
          page._timer_reset_btn.isHidden(), True)
    check("tick timer not active",
          page._tick_timer.isActive(), False)
    check("timer elapsed == 0", page._timer_elapsed, 0)

    # 切到 timer 模式：按鈕顯現，tick 仍未啟動（等使用者按開始）
    page._on_mode_toggle("timer")
    check("mode switched to timer", page._mode, "timer")
    check("start btn shown in timer",
          page._timer_start_btn.isHidden(), False)
    check("reset btn shown in timer",
          page._timer_reset_btn.isHidden(), False)
    check("tick timer still idle after switch",
          page._tick_timer.isActive(), False)

    # 按開始 → tick_timer 活動
    page._on_timer_start_stop()
    check("tick timer active after start",
          page._tick_timer.isActive(), True)
    # 再按一次 → 停止
    page._on_timer_start_stop()
    check("tick timer stopped after second toggle",
          page._tick_timer.isActive(), False)

    # 累積 30 秒後按重置 → _timer_elapsed 歸零
    page._timer_elapsed = 30
    page._on_timer_reset()
    check("timer elapsed reset to 0", page._timer_elapsed, 0)

    page.deleteLater()


def test_recalc_all_matches_service_summary():
    """_recalc_all 後，summary label 值符合 PotionService.calc_summary"""
    print("[test_recalc_all_matches_service_summary]")
    cm = _FakeConfigManager(autosave_data=None)
    page = _new_page(_FakeApp(cm))

    # 清空預設列、填入已知輸入
    page._loading = True
    try:
        for sec in page._sections.values():
            sec.clear()
        page._sections["hp"].add_row(
            {"name": "test", "price": 1000, "before": 10, "after": 5}
        )
        page._mesos_start_input.setText("10000")
        page._mesos_end_input.setText("50000")
        page._shop_before_input.setText("0")
        page._shop_after_input.setText("20000")
        page._exp_start_input.setText("1000")
        page._exp_end_input.setText("4000")
        page._duration_spin.setValue(30)
    finally:
        page._loading = False

    page._recalc_all()
    expected = PotionService.calc_summary(page._collect_form())

    # income 呈現為 "+1,580,000" 風格
    check("income label starts with +",
          page._summary_labels["income"].text().startswith("+"), True)
    check("expense label starts with -",
          page._summary_labels["expense"].text().startswith("-"), True)
    check("net label uses signed format",
          page._summary_labels["net"].text(), f"{expected['net']:+,}")

    page.deleteLater()


def main():
    app = QApplication.instance() or QApplication(sys.argv)
    test_collect_form_shape()
    test_autosave_restore_from_v1_dict()
    test_timer_controls_initial_state()
    test_recalc_all_matches_service_summary()

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

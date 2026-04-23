"""
ProfileManagerDialogV2 + AppCoreMixin profile CRUD 單元驗證

執行：`python verify_profile_crud_v2.py` —— 全部通過時 exit code = 0
"""

from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

from PySide6.QtWidgets import QApplication, QMessageBox

from src.ui_v2.dialogs.profile_manager_dialog_v2 import ProfileManagerDialogV2
from src.ui_v2.pages.skill_page_v2 import SkillPageV2
from src.ui.app_core import AppCoreMixin


_failures: list[str] = []


def check(label: str, got, expected):
    if got == expected:
        print(f"  OK   {label}")
    else:
        print(f"  FAIL {label}: got {got!r}, expected {expected!r}")
        _failures.append(label)


def _build_app(profiles=None, current="A"):
    app = MagicMock()
    profiles = profiles or ["A", "B", "C"]
    app.config_manager.list_profiles.return_value = profiles
    app.config_manager.get_current_profile.return_value = current
    app.config_manager.save_profile.return_value = True
    app.config_manager.load_profile.return_value = {"hotkeys": {}}
    app.config_manager.rename_profile.return_value = True
    app.config_manager.delete_profile.return_value = True
    sm = MagicMock()
    sm.get_all_skills.return_value = {"s1": {}, "s2": {}, "s3": {}}
    app.skill_manager = sm
    return app


# ════════════════════════════════════════════════════════════
# Dialog tests
# ════════════════════════════════════════════════════════════

def test_dialog_renders_current_marked():
    print("[test_dialog_renders_current_marked]")
    app_ctx = _build_app(["A", "B", "C"], current="B")
    dlg = ProfileManagerDialogV2(None, app_ctx)
    check("list count", dlg._list.count(), 3)
    item_b = dlg._list.item(1)
    check("B item text ends with 當前",
          item_b.text().endswith("（當前）"), True)
    from PySide6.QtCore import Qt
    check("B UserRole == 'B'", item_b.data(Qt.ItemDataRole.UserRole), "B")


def test_create_button_calls_app():
    print("[test_create_button_calls_app]")
    app_ctx = _build_app()
    app_ctx.create_profile.return_value = True
    dlg = ProfileManagerDialogV2(None, app_ctx)
    with patch.object(__import__("PySide6.QtWidgets", fromlist=["QInputDialog"]).QInputDialog,
                      "getText", return_value=("NewName", True)):
        dlg._on_create()
    check("create_profile called", app_ctx.create_profile.call_count, 1)
    check("called with NewName",
          app_ctx.create_profile.call_args[0][0], "NewName")


def test_duplicate_requires_selection():
    print("[test_duplicate_requires_selection]")
    app_ctx = _build_app()
    dlg = ProfileManagerDialogV2(None, app_ctx)
    dlg._list.clearSelection()
    dlg._on_duplicate()
    check("duplicate_profile NOT called",
          app_ctx.duplicate_profile.call_count, 0)
    check("toast info called", app_ctx.toast.show.call_count, 1)


def test_delete_with_confirm_calls_app():
    print("[test_delete_with_confirm_calls_app]")
    app_ctx = _build_app()
    app_ctx.delete_profile.return_value = True
    dlg = ProfileManagerDialogV2(None, app_ctx)
    dlg._list.setCurrentRow(1)  # "B"
    with patch.object(QMessageBox, "question",
                      return_value=QMessageBox.StandardButton.Yes):
        dlg._on_delete()
    check("delete_profile called once", app_ctx.delete_profile.call_count, 1)
    check("called with 'B'", app_ctx.delete_profile.call_args[0][0], "B")


# ════════════════════════════════════════════════════════════
# Mixin direct test
# ════════════════════════════════════════════════════════════

def test_mixin_delete_current_returns_false():
    print("[test_mixin_delete_current_returns_false]")
    # 用最小 stub 直接測 mixin 行為
    class Ctx(AppCoreMixin):
        def __init__(self):
            self.current_profile_name = "X"
            self.config_manager = MagicMock()
            self.toast = MagicMock()
    ctx = Ctx()
    result = ctx.delete_profile("X")
    check("returns False", result, False)
    check("config_manager.delete_profile NOT called",
          ctx.config_manager.delete_profile.call_count, 0)


# ════════════════════════════════════════════════════════════
# SkillPage refresh test
# ════════════════════════════════════════════════════════════

def test_refresh_does_not_fire_switch():
    print("[test_refresh_does_not_fire_switch]")
    # 用既有 fixture 思路建最小 app
    app_ctx = MagicMock()
    sm = MagicMock()
    sm.get_skill.return_value = None
    sm.get_all_skills.return_value = {}
    sm.get_categories.return_value = {}
    app_ctx.skill_manager = sm
    app_ctx.config_manager.list_profiles.return_value = ["A", "B"]
    app_ctx.config_manager.get_current_profile.return_value = "A"

    page = SkillPageV2(None, app_ctx)
    # 建構時 connect 已 fire 過，重置計數
    app_ctx.switch_profile.reset_mock()

    # patch list_profiles 加新 profile
    app_ctx.config_manager.list_profiles.return_value = ["A", "B", "C"]
    page.refresh_profile_selector()
    check("combo has 3 items", page._profile_combo.count(), 3)
    check("currentText still A", page._profile_combo.currentText(), "A")
    check("switch_profile NOT called during refresh",
          app_ctx.switch_profile.call_count, 0)


# ════════════════════════════════════════════════════════════
# Main
# ════════════════════════════════════════════════════════════

def main():
    QApplication.instance() or QApplication(sys.argv)
    test_dialog_renders_current_marked()
    test_create_button_calls_app()
    test_duplicate_requires_selection()
    test_delete_with_confirm_calls_app()
    test_mixin_delete_current_returns_false()
    test_refresh_does_not_fire_switch()
    if _failures:
        print(f"\nFAILED: {len(_failures)} check(s)")
        for f in _failures:
            print(f"  - {f}")
        sys.exit(1)
    print("\nAll checks passed.")


if __name__ == "__main__":
    main()

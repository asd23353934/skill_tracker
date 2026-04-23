# profile-crud-v2 Specification

## Purpose

TBD - created by archiving change 'profile-crud-v2'. Update Purpose after archive.

## Requirements

### Requirement: AppCoreMixin SHALL provide 4 profile CRUD methods

The system SHALL add 4 methods to `src/ui/app_core.py` (`AppCoreMixin`):

1. **`create_profile(name: str) -> bool`**
   - Returns False with toast `"配置 '{name}' 已存在！"` (kind="error") if `name in config_manager.list_profiles()`
   - Otherwise builds default skill state for ALL skill ids from `self.skill_manager.get_all_skills()`:
     `{"hotkeys": {}, "permanent": {sid: False, ...}, "loop": {sid: False, ...}, "alert_enabled": {sid: False, ...}, "cooldown_overrides": {}}`
   - Calls `config_manager.save_profile(name, default_state)`; on success: toast `"已新增配置「{name}」"` (success), call `_refresh_skill_page_v2_profile_selector()`, return True
   - Validates `name.strip() != ""`; empty → False with toast `"配置名稱不可為空"` (error)

2. **`duplicate_profile(source: str, new_name: str) -> bool`**
   - Same name validation as create
   - Loads source via `config_manager.load_profile(source)`; if None: toast `"無法載入來源配置 '{source}'"` (error), return False
   - Calls `config_manager.save_profile(new_name, source_data)`; on success: toast `"已複製配置「{source}」→「{new_name}」"` (success) + refresh + True

3. **`rename_profile(old_name: str, new_name: str) -> bool`**
   - new_name validation as create
   - Calls `config_manager.rename_profile(old_name, new_name)`; if returns falsy: toast `"重命名失敗"` (error), return False
   - On success: if `old_name == self.current_profile_name`, set `self.current_profile_name = new_name` AND `config_manager.set_current_profile(new_name)`. Then toast `"已重命名「{old_name}」→「{new_name}」"` (success) + refresh + True

4. **`delete_profile(name: str) -> bool`**
   - If `name == self.current_profile_name`: toast `"無法刪除當前正在使用的配置！"` (error), return False
   - Calls `config_manager.delete_profile(name)`; if returns falsy: toast `"刪除失敗"` (error), False
   - On success: toast `"已刪除配置「{name}」"` (success) + refresh + True

The shared refresh helper `_refresh_skill_page_v2_profile_selector()` SHALL call `getattr(self, "skill_page_v2", None).refresh_profile_selector()` if both attribute and method exist.

#### Scenario: Create with duplicate name fails

- **GIVEN** `config_manager.list_profiles()` returns `["A"]`
- **WHEN** `app.create_profile("A")` is called
- **THEN** returns False, no save_profile call, error toast shown

#### Scenario: Rename current profile updates self.current_profile_name

- **GIVEN** `app.current_profile_name == "A"`, `config_manager.rename_profile("A","B")` returns True
- **WHEN** `app.rename_profile("A", "B")` is called
- **THEN** `app.current_profile_name == "B"` and `config_manager.set_current_profile` was called once with `"B"`

#### Scenario: Delete current profile is blocked

- **GIVEN** `app.current_profile_name == "Default"`
- **WHEN** `app.delete_profile("Default")` is called
- **THEN** returns False, `config_manager.delete_profile` is NOT called, error toast shown


<!-- @trace
source: profile-crud-v2
updated: 2026-04-23
code:
  - skill_tracker.spec
  - src/ui_v2/pages/skill_page_v2.py
  - src/ui_v2/dialogs/__init__.py
  - src/ui/app_core.py
  - profiles/預設配置.json
  - docs/PROJECT.md
  - src/ui_v2/dialogs/profile_manager_dialog_v2.py
  - verify_profile_crud_v2.py
-->

---
### Requirement: SkillPageV2 SHALL refresh profile selector after CRUD

The system SHALL add `refresh_profile_selector()` to `SkillPageV2` in `src/ui_v2/pages/skill_page_v2.py`. The method SHALL:

- Re-read `app.config_manager.list_profiles()` and `app.config_manager.get_current_profile()`
- Repopulate the existing ArrowComboBox without firing currentTextChanged (use `blockSignals(True/False)` around `clear()` + `addItems()` + `setCurrentText()`)
- Be safe to call when the profile selector hasn't been built yet (early return)

#### Scenario: Refresh after add picks up new profile

- **GIVEN** SkillPageV2 with selector showing `["A"]`, current = "A"
- **WHEN** ConfigManager.list_profiles is patched to return `["A", "B"]` and `page.refresh_profile_selector()` is called
- **THEN** combo items are now `["A", "B"]` and currentText is still "A" (current didn't change), AND `app.switch_profile` was NOT called during refresh


<!-- @trace
source: profile-crud-v2
updated: 2026-04-23
code:
  - skill_tracker.spec
  - src/ui_v2/pages/skill_page_v2.py
  - src/ui_v2/dialogs/__init__.py
  - src/ui/app_core.py
  - profiles/預設配置.json
  - docs/PROJECT.md
  - src/ui_v2/dialogs/profile_manager_dialog_v2.py
  - verify_profile_crud_v2.py
-->

---
### Requirement: SkillPageV2 SHALL expose profile manager button

The system SHALL add a small icon button next to the profile selector in `_build_profile_selector` (or right after addWidget(combo)). The button SHALL:

- Use `lucide_pixmap("settings", T.TEXT_DIM, 14, stroke=1.6)` icon, fixed size 28×28, transparent background, hover background = T.BG_HOVER
- On click, instantiate `ProfileManagerDialogV2(self.window(), self.app)` and call `.exec()` (modal)

If `self.app is None` (preview-only mode), the button SHALL still render but click is a silent no-op.

#### Scenario: Click opens manager dialog

- **GIVEN** SkillPageV2 wired with V2AppContext
- **WHEN** the profile manager button is clicked
- **THEN** a `ProfileManagerDialogV2` is created and `.exec()` is invoked


<!-- @trace
source: profile-crud-v2
updated: 2026-04-23
code:
  - skill_tracker.spec
  - src/ui_v2/pages/skill_page_v2.py
  - src/ui_v2/dialogs/__init__.py
  - src/ui/app_core.py
  - profiles/預設配置.json
  - docs/PROJECT.md
  - src/ui_v2/dialogs/profile_manager_dialog_v2.py
  - verify_profile_crud_v2.py
-->

---
### Requirement: ProfileManagerDialogV2 SHALL render list with current profile marked

The system SHALL implement `ProfileManagerDialogV2(parent, app)` in `src/ui_v2/dialogs/profile_manager_dialog_v2.py` extending `BaseDialogV2` with title `"配置管理"`. The dialog SHALL:

- Render a `QListWidget` populated from `app.config_manager.list_profiles()`
- Append `"（當前）"` suffix to the entry whose name equals `app.config_manager.get_current_profile()`
- Store the raw name in `Qt.ItemDataRole.UserRole` so display suffix doesn't pollute name-based operations
- Refresh list after every successful CRUD operation by calling its own `_refresh_list()`

#### Scenario: Current profile marked

- **GIVEN** profiles `["Default", "Boss"]`, current = `"Boss"`
- **WHEN** dialog is rendered
- **THEN** list shows `["Default", "Boss（當前）"]` in that order; UserRole data for the Boss entry equals `"Boss"`


<!-- @trace
source: profile-crud-v2
updated: 2026-04-23
code:
  - skill_tracker.spec
  - src/ui_v2/pages/skill_page_v2.py
  - src/ui_v2/dialogs/__init__.py
  - src/ui/app_core.py
  - profiles/預設配置.json
  - docs/PROJECT.md
  - src/ui_v2/dialogs/profile_manager_dialog_v2.py
  - verify_profile_crud_v2.py
-->

---
### Requirement: ProfileManagerDialogV2 SHALL provide 4 CRUD buttons

The system SHALL render 4 buttons under the list, each wired to the matching `app.create_profile / duplicate_profile / rename_profile / delete_profile`:

1. **新增**: prompts via `QInputDialog.getText(self, "新增配置", "輸入新配置名稱:")`; if user enters non-empty name, call `app.create_profile(name)`; on True refresh list

2. **複製**: requires a list selection (no selection → toast `"請先選擇要複製的配置！"` info, return); prompts `QInputDialog` with placeholder hinting source name; on True refresh

3. **重命名**: requires a list selection; prompts `QInputDialog` pre-filled with current name; if user enters different non-empty name, call `app.rename_profile(old, new)`; on True refresh

4. **刪除**: requires a list selection; opens `QMessageBox.question` confirmation; on Yes call `app.delete_profile(name)`; on True refresh

All button actions SHALL be no-op if user cancels the prompt or confirmation. Toasts come from the `apply_*` mixin methods, NOT inline in dialog.

#### Scenario: Delete with confirmation Yes calls app.delete_profile

- **GIVEN** dialog with list selection on "Boss"
- **WHEN** user clicks 刪除 and selects Yes in confirmation
- **THEN** `app.delete_profile("Boss")` is called once

#### Scenario: Rename to same name is no-op

- **WHEN** user opens 重命名 prompt and submits the same name unchanged
- **THEN** `app.rename_profile` is NOT called


<!-- @trace
source: profile-crud-v2
updated: 2026-04-23
code:
  - skill_tracker.spec
  - src/ui_v2/pages/skill_page_v2.py
  - src/ui_v2/dialogs/__init__.py
  - src/ui/app_core.py
  - profiles/預設配置.json
  - docs/PROJECT.md
  - src/ui_v2/dialogs/profile_manager_dialog_v2.py
  - verify_profile_crud_v2.py
-->

---
### Requirement: ProfileManagerDialogV2 export SHALL be added to dialogs package

The system SHALL add `from src.ui_v2.dialogs.profile_manager_dialog_v2 import ProfileManagerDialogV2` and `"ProfileManagerDialogV2"` to `__all__` in `src/ui_v2/dialogs/__init__.py`.

#### Scenario: Import from package works

- **WHEN** `from src.ui_v2.dialogs import ProfileManagerDialogV2` is executed
- **THEN** the import succeeds without ImportError

<!-- @trace
source: profile-crud-v2
updated: 2026-04-23
code:
  - skill_tracker.spec
  - src/ui_v2/pages/skill_page_v2.py
  - src/ui_v2/dialogs/__init__.py
  - src/ui/app_core.py
  - profiles/預設配置.json
  - docs/PROJECT.md
  - src/ui_v2/dialogs/profile_manager_dialog_v2.py
  - verify_profile_crud_v2.py
-->
## 1. 前置驗證

- [x] 1.1 跑既有 verify：`python verify_skill_page_v2.py && python verify_monster_page_v2.py && python verify_toast_v2.py && python verify_settings_dialog_v2.py` 全綠

## 2. AppCoreMixin SHALL provide 4 profile CRUD methods

- [x] 2.1 落實 Requirement「AppCoreMixin SHALL provide 4 profile CRUD methods」第 1 項：在 `src/ui/app_core.py` 末段新增 `create_profile(name)`：strip + 空字串檢查 → 若 `name in list_profiles()` 回 False+error toast → 否則建構 default state（permanent/loop/alert_enabled 對所有 skill_id 設 False、hotkeys / cooldown_overrides 空）→ 呼 `config_manager.save_profile(name, state)` → 成功 toast + `_refresh_skill_page_v2_profile_selector()` + 回 True
- [x] 2.2 第 2 項：實作 `duplicate_profile(source, new_name)`：name 校驗（同 create）→ `load_profile(source)` 失敗 error toast → `save_profile(new_name, source_data)` 成功 toast「已複製配置「{source}」→「{new_name}」」 + refresh + True
- [x] 2.3 第 3 項：實作 `rename_profile(old_name, new_name)`：name 校驗 → `config_manager.rename_profile(old, new)` 失敗 error toast 「重命名失敗」→ 成功時若 `old_name == self.current_profile_name`：`self.current_profile_name = new_name` + `config_manager.set_current_profile(new_name)`；toast「已重命名「{old}」→「{new}」」 + refresh + True
- [x] 2.4 第 4 項：實作 `delete_profile(name)`：若 `name == self.current_profile_name` 回 False + error toast「無法刪除當前正在使用的配置！」→ 否則 `config_manager.delete_profile(name)`，失敗 error toast → 成功 toast「已刪除配置「{name}」」 + refresh + True
- [x] 2.5 加 helper `_refresh_skill_page_v2_profile_selector()`：`page = getattr(self, "skill_page_v2", None); if page and hasattr(page, "refresh_profile_selector"): page.refresh_profile_selector()`
- [x] 2.6 import smoke：`python -c "from src.ui.app_core import AppCoreMixin; assert all(hasattr(AppCoreMixin, m) for m in ['create_profile','duplicate_profile','rename_profile','delete_profile'])"`

## 3. SkillPageV2 SHALL refresh profile selector after CRUD

- [x] 3.1 落實 Requirement「SkillPageV2 SHALL refresh profile selector after CRUD」：在 `src/ui_v2/pages/skill_page_v2.py` `SkillPageV2` 加 `refresh_profile_selector()` 方法：取 `self._profile_combo`（建構時要存 ref）；early return if None；blockSignals(True) → clear() → addItems(list_profiles()) → setCurrentText(get_current_profile()) → blockSignals(False)
- [x] 3.2 修改 `_build_profile_selector` 把 ArrowComboBox 存到 `self._profile_combo`，然後 return
- [x] 3.3 import smoke：`python -c "from src.ui_v2.pages.skill_page_v2 import SkillPageV2; assert hasattr(SkillPageV2, 'refresh_profile_selector')"`

## 4. SkillPageV2 SHALL expose profile manager button

- [x] 4.1 落實 Requirement「SkillPageV2 SHALL expose profile manager button」：在 `_build_profile_selector` return 之前，於 selector 旁建構一個 QPushButton（28×28 transparent，icon 用 `lucide_pixmap("settings", T.TEXT_DIM, 14, stroke=1.6)`，hover bg = T.BG_HOVER）；click → `self._open_profile_manager()`
- [x] 4.2 改 `_build_profile_selector` 回 QWidget 容器（combo + 按鈕水平包裝），呼叫端不變
- [x] 4.3 加 `_open_profile_manager()`：`if self.app is None: return`；`from src.ui_v2.dialogs import ProfileManagerDialogV2; ProfileManagerDialogV2(self.window(), self.app).exec()`

## 5. ProfileManagerDialogV2 SHALL render list with current profile marked

- [x] 5.1 落實 Requirement「ProfileManagerDialogV2 SHALL render list with current profile marked」：新建 `src/ui_v2/dialogs/profile_manager_dialog_v2.py` `class ProfileManagerDialogV2(BaseDialogV2)`，`__init__(parent, app)`，title="配置管理"，width=420 height=460
- [x] 5.2 在 `_build` 加 QListWidget self._list，padding/style；呼 `self._refresh_list()` 初始化
- [x] 5.3 實作 `_refresh_list()`：clear → 取 `app.config_manager.list_profiles()` 與 `get_current_profile()` → 對每個 profile 建 QListWidgetItem(text=name + ("（當前）" if is_current else ""))，setData(UserRole, raw_name) → addItem
- [x] 5.4 實作 helper `_get_selected_name() -> str | None`：取 currentItem 的 UserRole

## 6. ProfileManagerDialogV2 SHALL provide 4 CRUD buttons

- [x] 6.1 落實 Requirement「ProfileManagerDialogV2 SHALL provide 4 CRUD buttons」第 1 顆：QPushButton「新增」→ `_on_create`：`QInputDialog.getText(self, "新增配置", "輸入新配置名稱:")`，user 取消 / 空字串 return；呼 `self.app.create_profile(name)`；True 才 `self._refresh_list()`
- [x] 6.2 第 2 顆：QPushButton「複製」→ `_on_duplicate`：`source = self._get_selected_name()`；None → `app.toast.show("請先選擇要複製的配置！", "info")`；否則 `QInputDialog.getText(..., 預設 hint 含 source)`；呼 `app.duplicate_profile(source, new_name)`；成功 refresh
- [x] 6.3 第 3 顆：QPushButton「重命名」→ `_on_rename`：`old = _get_selected_name()`；None → info toast；`QInputDialog.getText(self, "重命名", f"輸入新名稱:\n(當前: '{old}')", text=old)`；空 / 同名 return；呼 `app.rename_profile(old, new)`；成功 refresh
- [x] 6.4 第 4 顆：QPushButton「刪除」→ `_on_delete`：`name = _get_selected_name()`；None → info toast；`QMessageBox.question(self, "確認刪除", f"確定要刪除配置 '{name}' 嗎？", Yes|No)`；Yes 才呼 `app.delete_profile(name)`；成功 refresh
- [x] 6.5 4 顆按鈕 V2 樣式（fixed height 30, padding 0 14px, font-size 12, T.BG_INPUT 底 / T.BORDER；hover T.BG_HOVER）；橫排 footer（用 `self.footer_layout()`）

## 7. ProfileManagerDialogV2 export SHALL be added to dialogs package

- [x] 7.1 落實 Requirement「ProfileManagerDialogV2 export SHALL be added to dialogs package」：`src/ui_v2/dialogs/__init__.py` import + 加入 __all__
- [x] 7.2 import smoke：`python -c "from src.ui_v2.dialogs import ProfileManagerDialogV2"` 通過

## 8. 驗證腳本

- [x] 8.1 新建 `verify_profile_crud_v2.py`，仿其他 verify_*：建 QApplication、MagicMock app；提供 list_profiles + get_current_profile + skill_manager.get_all_skills (回 dict 含 3 個 sid) + 4 個 CRUD 方法（mock 紀錄 call）
- [x] 8.2 test_dialog_renders_current_marked: list_profiles=["A","B","C"], get_current_profile="B"; build dialog；assert _list 3 項，第 2 項 text 結尾「（當前）」、UserRole == "B"
- [x] 8.3 test_create_button_calls_app: monkey patch QInputDialog.getText 回 ("NewName", True)；點新增按鈕；assert `app.create_profile.assert_called_once_with("NewName")`
- [x] 8.4 test_duplicate_requires_selection: 沒選任何項目就點複製 → `app.duplicate_profile.call_count == 0`，`app.toast.show` 被呼一次（info kind）
- [x] 8.5 test_delete_blocks_current: 選當前 profile + 點刪除（patch QMessageBox 回 Yes）；確認 `app.delete_profile` **被呼**（block 邏輯在 mixin、不在 dialog）；mixin 的真實阻擋驗證放 8.6
- [x] 8.6 test_mixin_delete_current_returns_false: 直接測 mixin 行為 — 用單獨 fake context 設 `current_profile_name="X"`，呼 `instance.delete_profile("X")` 回 False、`config_manager.delete_profile.call_count == 0`
- [x] 8.7 test_refresh_does_not_fire_switch: build SkillPageV2 → 直接呼 `page.refresh_profile_selector()` → assert `app.switch_profile.call_count == 0`
- [x] 8.8 全腳本 exit 0

## 9. 手動驗證

- [x] 9.1 `python main.py` 啟動 V2，skill 頁 profile dropdown 旁可見小齒輪按鈕；點開 ProfileManagerDialogV2
- [x] 9.2 點「新增」→ 輸入 `BOSS_test` → toast「已新增配置「BOSS_test」」、list 多一項、dropdown 也多一項
- [x] 9.3 選 BOSS_test → 點「複製」→ 輸入 `BOSS_test_copy` → toast、list+dropdown 同步多一項
- [x] 9.4 選 BOSS_test_copy → 點「重命名」→ 改 `BOSS_v2` → toast、list+dropdown 名稱同步更新
- [x] 9.5 選 BOSS_v2 → 點「刪除」→ 確認 → toast、list+dropdown 少一項；嘗試刪除當前 profile → toast「無法刪除當前正在使用的配置！」、list 不變
- [x] 9.6 透過 dropdown 切到 BOSS_test → 用 dialog 重命名為 `BOSS_v3` → 確認 dropdown 顯示新名、`current_profile_name` 已同步（連續再切回原 profile 應正常）
- [x] 9.7 V1 (`python main.py --v1`) header 配置管理對話框互動仍維持原行為，無 regression

## 10. 收尾

- [x] 10.1 跑 `/simplify` 與 `/spectra-audit`
- [x] 10.2 同步 docs/PROJECT.md：`src/ui_v2/dialogs/` 條目加入 `profile_manager_dialog_v2.py`；`src/ui/app_core.py` 條目補「+ create/duplicate/rename/delete_profile」
- [ ] 10.3 commit + archive

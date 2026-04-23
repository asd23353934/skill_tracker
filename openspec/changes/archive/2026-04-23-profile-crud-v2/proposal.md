## Why

V2 預覽中 skill 頁 profile dropdown 只能**切換**現有 profile（透過 `app.switch_profile`），無法 CRUD：

- 新增新 profile → 必須切回 V1 走 `header → 配置 → 新增...`
- 複製當前 profile 為新名稱 → V1 only
- 重命名現有 profile → V1 only
- 刪除 profile → V1 only

V1 `ProfileManagerDialog`（`src/ui/dialogs/profile_dialog.py`）一個 list + 5 個按鈕（新增 / 複製 / 重命名 / 切換 / 刪除）涵蓋所有操作，但完全寫在 V1 dialog 內、未抽到 mixin。V2 若 inline 重做這些操作會出現 V1 / V2 雙份 ConfigManager 呼叫的維護負擔。

## What Changes

- 新增 `src/ui_v2/dialogs/profile_manager_dialog_v2.py`：
  - `ProfileManagerDialogV2(parent, app)` 繼承 `BaseDialogV2`
  - 顯示 profile QListWidget（從 `app.config_manager.list_profiles()`），當前 profile 加 `（當前）` suffix
  - 4 顆按鈕：新增 / 複製 / 重命名 / 刪除
  - 切換不再放這裡（已在 dropdown），focus on CRUD
  - 不需要 OK / Cancel — 操作即時生效，右上 ✕ 關閉
- 新增 `AppCoreMixin` 4 個方法到 `src/ui/app_core.py`：
  - `create_profile(name)` — 含預設 skill state，呼叫 `config_manager.save_profile`
  - `duplicate_profile(source, new_name)` — load_profile + save_profile
  - `rename_profile(old, new)` — 呼 `config_manager.rename_profile`；若改的是當前 profile，同步 `self.current_profile_name`
  - `delete_profile(name)` — 呼 `config_manager.delete_profile`；當前 profile 不可刪
  - 每個方法成功後 `self.toast.show(...)` 回饋；失敗（重名 / 不存在）回 False + 對應 error toast
- `src/ui_v2/pages/skill_page_v2.py`：profile dropdown 旁加齒輪 / 編輯小按鈕 → `lambda: ProfileManagerDialogV2(self.window(), self.app).exec()`
- CRUD 操作完成後自動 refresh：
  - SkillPageV2 提供 `refresh_profile_selector()` 方法（重讀 list_profiles + 維持當前選擇）
  - `AppCoreMixin.create_profile / rename_profile / delete_profile` 末段呼叫 `getattr(self, "skill_page_v2", None).refresh_profile_selector()`（與既有 refresh_status_counts 同 pattern）

## Non-Goals

- **不改 V1 ProfileManagerDialog**：V1 既有對話框與 header 入口完全保留。
- **不改 ConfigManager profile API**：`list_profiles / save_profile / load_profile / rename_profile / delete_profile / get_current_profile / set_current_profile` 維持現狀。
- **不引入 profile 匯入 / 匯出**：JSON 匯入匯出、複製/貼上、雲端同步皆不在範圍。
- **不在 dialog 內提供切換按鈕**：切換已由 dropdown 處理，避免兩條入口造成混淆。
- **不為新 profile 自動載入特定預設 skill state**：沿用 V1 `_create_new_profile` 的 default（permanent / loop / alert_enabled 全 False、hotkeys / cooldown_overrides 空）。
- **不寫單元測試 fixture 對 4 個 mixin 方法的全 coverage**：抽 service 後再說；這次 verify 跑 import smoke + 對話框構造 + 1 組 CRUD 流程即可。

## Capabilities

### New Capabilities

- `profile-crud-v2`: V2 profile 管理對話框 + AppCoreMixin 4 個 CRUD 方法（create / duplicate / rename / delete），與 V1 ProfileManagerDialog 操作對等。

### Modified Capabilities

(none)

## Impact

- Affected specs: 新增 `profile-crud-v2`
- Affected code:
  - New:
    - `src/ui_v2/dialogs/profile_manager_dialog_v2.py`
    - `verify_profile_crud_v2.py`
  - Modified:
    - `src/ui/app_core.py`（4 個 CRUD 方法）
    - `src/ui_v2/pages/skill_page_v2.py`（dropdown 旁加管理按鈕 + refresh_profile_selector）
    - `src/ui_v2/dialogs/__init__.py`（export ProfileManagerDialogV2）
  - Removed: 無

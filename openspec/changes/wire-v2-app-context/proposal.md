## Summary

讓 V2 preview shell（`main_v2.py` / `V2AppContext`）共用 V1 App 的 domain backing（SkillManager / HotkeyManager / WindowManager / SoundManager）與共通 App 行為方法，解鎖 wire-v2-skill-page 的手動回歸（12.1–12.4）並讓 V2 頁面在預覽模式下可實際操作。

## Motivation

V2 preview shell 目前只做顏色/版面示意，`V2AppContext` 明確宣告不包含 `skill_manager` / `hotkey_manager` / `window_manager` / `sound_manager`（見 `main_v2.py:37-38`）。結果：

- `SkillPageV2.rebuild()` 走 `hasattr(app, "skill_manager")` 保護傘直接 return，V2 預覽下頁面留白。
- `SkillCardV2` 依賴的 13 個 App 方法（`edit_cooldown` / `reset_cooldown` / `reset_hotkey` / `update_skill_setting_exclusive` / `update_alert_setting` / `edit_alert_seconds` / `toggle_all` / `update_hotkey_display` / `get_alert_seconds` / `get_original_cooldown` / `auto_save_current_profile` / `show_skill_detail` / `on_skill_triggered`）散落在 `src/ui/app.py` 中，V1 App 類直接持有，V2 shell 無從取得。
- wire-v2-skill-page 的手動回歸 12.1–12.4（驗證技能卡覆寫 / 熱鍵捕捉 / 倒數觸發 / Detail dialog 套用）因此無法進行。

## Proposed Solution

抽 `src/ui/app_core.py`（`AppCoreMixin`）：

1. `_init_domain_backing(config_manager)` 負責依序建立：`SkillManager` → `HotkeyManager` → `WindowManager` → `SoundManager` → `OverlayManager`；維護 App 層狀態 dict（`skill_hotkeys` / `skill_permanent` / `skill_loop` / `skill_alert_enabled` / `skill_cooldown_overrides` / `skill_alert_seconds_overrides` / `skill_sound_overrides` / `skill_alert_sound_overrides`）以及 V1 widget 登錄 dict（`cooldown_buttons` / `hotkey_buttons` / `alert_seconds_buttons` / `permanent_vars` / `loop_vars` / `alert_enabled_vars` / `skill_card_widgets`）。
2. 把 13 個共通 App 行為方法從 `src/ui/app.py` 搬進 mixin，維持原簽名／行為；V1 App 改為 `class App(QMainWindow, AppCoreMixin)` 繼承後呼叫 `self._init_domain_backing(self.config_manager)`。
3. `main_v2.py` 的 `V2AppContext` 同樣繼承 `AppCoreMixin`，在 `__init__` 最後呼叫 `self._init_domain_backing(config_manager)`，即取得完整 domain backing；V2 shell 的頁面無需改動即可操作真資料。
4. `src/ui_v2/dialogs/skill_detail_dialog_v2.py` 已用 App API 寫入 override，確認它讀寫的都是 mixin 上的 dict 屬性，不再依賴具體子類。

## Non-Goals

- 不重寫 V1 App 的 UI（頂部列 / 狀態列 / 視窗管理皆維持原樣）。
- 不更動 Manager 類的公開 API（`SkillManager` / `HotkeyManager` / `WindowManager` / `SoundManager` / `OverlayManager` 介面維持現狀）。
- 不在 V2 shell 實作 profile 切換 UI（V2 shell 先用 V1 的 `config_manager.current_profile`，UI 切換延後）。
- 不處理 V2 視覺還原度或字體微調（已在 wire-v2-skill-page 內處理）。

## Alternatives Considered

- **在 V2AppContext 中手動複製 13 個方法**：維護成本高、行為會漂移，否決。
- **讓 V2 頁面改走一套 V2-only service**：形同重寫 `SkillService` 與 Manager 鏈，範圍爆炸且與 V1 無法共用狀態。否決。
- **把方法全搬到 `SkillService`**：部分方法依賴 UI（Toast / Dialog / WindowManager），不適合移到零 Qt 的 domain 層。

## Impact

- Affected specs: `app-core-backing`（新 capability）、`skill-service`（僅文件釐清共用狀態 dict 歸屬，不改行為）
- Affected code:
  - New:
    - `src/ui/app_core.py`（AppCoreMixin）
    - `openspec/specs/app-core-backing/spec.md`（delta spec）
  - Modified:
    - `src/ui/app.py`（改為繼承 mixin；移除已上移的共通方法）
    - `main_v2.py`（`V2AppContext` 繼承 mixin，呼叫 `_init_domain_backing`）
    - `src/ui_v2/dialogs/skill_detail_dialog_v2.py`（確保只用 mixin 上的屬性）
  - Removed: （無）

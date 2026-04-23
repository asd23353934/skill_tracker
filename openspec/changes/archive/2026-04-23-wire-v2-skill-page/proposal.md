## Why

V2 預覽 shell 中僅 `skill_page_v2.py` 仍使用假資料 `DEMO_DATA`，所有控件（冷卻 InputChip、熱鍵 InputChip、常/循/提 checkbox、提前秒數 pill、⋮ 詳細設定、全選 chip）點擊只跳 "此功能尚未接 V2" Toast。相較之下 V1 `SkillPage` 已完整接線到 App 狀態（94 個技能 × 8 種 per-skill override、config/profile 雙向同步、hotkey 擷取、窗口生命週期、聲音覆寫）。本次變更將 V2 技能頁從視覺殼升級為可完整替代 V1 的功能頁，讓使用者可在 V2 shell 完成日常冷卻追蹤。

## What Changes

- **讀取真實資料**：SkillPageV2 改從 `app.skill_manager.get_skills() / get_items()` 取得 94 個技能元資料，並依 `category` / `subcategory` 分組。
- **SkillCard 雙向綁定**（每張卡）：
  - 冷卻秒數 chip：顯示 `skill_cooldown_overrides[id]` 或原始 cooldown；點擊開啟編輯對話框；重置按鈕清除 override。
  - 熱鍵 chip：顯示 `skill_hotkeys[id]`；點擊呼叫 `hotkey_manager.begin_capture(id, name)`；重置按鈕清空並解綁。
  - 常/循/提 checkbox：綁定 `skill_permanent/skill_loop/skill_alert_enabled[id]`；常駐切換同步開關 `window_manager` 的常駐視窗。
  - 提前秒數 pill：顯示 `skill_alert_seconds_overrides[id]` 或全域 `alert_before_seconds`；點擊開啟編輯對話框。
  - ⋮ 詳細設定：開啟 `SkillDetailDialogV2`，編輯 `skill_sound_overrides[id]` / `skill_alert_sound_overrides[id]` / 自訂圖示。
- **頁首快速切換**：`常駐 / 循環 / 提醒` 三顆 chip 呼叫 `app.toggle_all('permanent'|'loop'|'alert')` 一鍵全開/全關。
- **執行緒安全**：hotkey 擷取回來的狀態更新必須透過 `app.after(0, ...) / dispatcher.schedule()` 排回主執行緒才能刷新卡片。
- **刷新策略**：
  - `showEvent` 首次顯示時 rebuild 全頁（延遲到 app 初始化完成後）。
  - profile 切換時由 `app.register_rebuild_callback` 觸發 rebuild。
  - 單張卡片狀態變更走局部更新（`skill_card_v2.refresh()`），不 rebuild 全頁。
- **持久化**：每次狀態變更呼叫 `config_manager.save_profile(current, snapshot)`；snapshot 沿用 V1 `SkillPage._build_profile_snapshot()` 的八欄結構。
- **SkillDetailDialogV2** 目前只是殼；本次擴充使其可讀寫 `skill_sound_overrides` / `skill_alert_sound_overrides` / `skill_icon_overrides` 並提供試聽。

## Non-Goals (optional)

- 不重構 V1 SkillPage；V1 保留，兩頁共用同一份 profile 狀態（last-writer-wins）。
- 不改動 `SkillManager` / `HotkeyManager` / `WindowManager` / `ConfigManager` 的公開介面；僅新增 V2 頁面消費者。
- 不新增 `skill-cooldown` spec 的新 Requirement（行為契約沿用既有 V1 spec）。
- 不處理多選/批次編輯 UI（V1 亦無）。

## Capabilities

### New Capabilities

- `skill-cooldown-ui-v2`: V2 紫色漸層 shell 中技能冷卻頁面與 App/ConfigManager/HotkeyManager 的接線契約，涵蓋 94 技能 × 8 per-skill override 的雙向同步、rebuild 策略與執行緒安全。

### Modified Capabilities

(none)

## Impact

- Affected specs: 新增 `skill-cooldown-ui-v2`
- Affected code:
  - Modified:
    - src/ui_v2/pages/skill_page_v2.py
    - src/ui_v2/dialogs/skill_detail_dialog_v2.py
  - New:
    - src/ui_v2/pages/skill_card_v2.py
    - src/ui_v2/pages/skill_column_v2.py
    - verify_skill_page_v2.py
  - Removed: (none)

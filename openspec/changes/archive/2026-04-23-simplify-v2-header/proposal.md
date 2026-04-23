## Summary

簡化 V2 全域 `HeaderV2`：移除無實際功能的視覺元素（avatar / greeting / subtitle / 鈴鐺 / 人 icon / 橘色 + CTA），把「默認配置」profile dropdown 從全域 header 搬進 `SkillPageV2` 內並接到 V1 既有 `ConfigManager` profile 切換邏輯。HeaderV2 縮窄為「拖曳區 + 視窗控制按鈕」純功能列。

## Motivation

V2 preview 啟動後 header 占用 80px，但實質功能性只剩右上三個視窗控制按鈕（min / max / close）。其他元素皆是 placeholder：

- avatar / greeting / subtitle — 純裝飾，無資料來源
- profile dropdown — hardcoded `["默認配置", "輔助配置", "BOSS 配置"]`，未接 `ConfigManager.list_profiles()` / `set_current_profile()`
- 橘色 + CTA — 無 click handler
- 鈴鐺 / 人 GlyphBtn — display-only，無 callback

Profile dropdown 是唯一值得保留的功能元素，但**它只影響技能倒數狀態**（hotkeys / cooldown overrides / permanent / alert 都屬技能），其他頁面（monster / overlay / potion / mapleworld）對 profile 無感。放在全域 header 給人「全應用都會切」的錯覺，反而誤導；搬到 skill 頁內位置更直覺，且 header 騰出的空間讓主內容多 80px 高度。

## Proposed Solution

1. **HeaderV2 縮減**：`src/ui_v2/header_v2.py` 中 `HeaderV2._build` 移除 avatar / greeting / subtitle / profile combo / 橘色 CTA / GlyphBtn 鈴鐺 / GlyphBtn 人 共 7 段元素，整個 header 縮為「左側拖曳 padding + 右側 3 個 WinCtrlBtn（min / max / close）」。`HEADER_H` 維持原值或視情況降低（保留拖曳手感，由 design 決定）。

2. **Profile Dropdown 搬到 SkillPageV2**：在 `src/ui_v2/pages/skill_page_v2.py` 既有 `_build_shell` 頂部 bar 內，於「技能倒數」title 與 stretch 之間插入 ProfileSelector 元件。元件：
   - 從 `app.config_manager.list_profiles()` 動態取選項
   - 預設值取 `app.config_manager.get_current_profile()`
   - `currentTextChanged` → 呼叫新增的 `app.switch_profile(name)` 方法（見 §3）

3. **App 層加 `switch_profile(name)` 方法到 AppCoreMixin**：接收 profile 名稱 → 呼叫 `config_manager.set_current_profile(name)` + `_load_profile_state(name)` 重新同步 SkillService → 觸發 V2 SkillPageV2.rebuild() 重建技能卡片。V1 既有 `_apply_profile` 流程不動（V1 走 ProfileManagerDialog）。

4. **Profile dropdown UI 元件**：直接用 `ArrowComboBox`（既有 V2 元件）+ V2 樣式，不需新類別。

## Non-Goals

- **不改 V1 Header**：V1 沿用 ProfileManagerDialog 開全屏對話框切 profile，行為不變。
- **不改 ConfigManager profile API**：`list_profiles / get_current_profile / set_current_profile` 維持現狀。
- **不引入 profile 切換動畫**：直接 rebuild，無 fade / slide。
- **不在 V2 header 加新功能**（搜尋框、選單按鈕等）— 純精簡。
- **不刪除 `_NoopHeader` stub**（V2AppContext 中）— 與 wire-v2-skill-page 解耦。
- **不處理 V2 monster / overlay / potion / mapleworld 對 profile-switch 的反應**：目前那些頁面狀態不來自 profile（怪物在 config.json 全域可變區、overlay 同），切 profile 無需重繪。

## Alternatives Considered

- **保留 header 但只移除無功能元素**：avatar / greeting 屬視覺風格；移除後 header 顯得空蕩，profile dropdown 留在那裡反而擁擠。否決。
- **Profile dropdown 留 header、僅接線**：仍給人「全應用切」的錯覺，且 header 視覺仍肥大。否決。
- **完全砍掉 header、視窗控制按鈕浮在 PreviewWindow 內**：要重作無框視窗拖曳邏輯，破壞既有抽象。否決。

## Impact

- Affected specs: 新增 `v2-header-shell`
- Affected code:
  - Modified:
    - `src/ui_v2/header_v2.py`（縮減 _build；可能調整 `HEADER_H`）
    - `src/ui_v2/pages/skill_page_v2.py`（top bar 插入 ProfileSelector + 連動 rebuild）
    - `src/ui/app_core.py`（新增 `switch_profile(name)` 方法）
    - `src/ui_v2/theme_v2.py`（若調 `HEADER_H` 才動）
  - New: 無
  - Removed: 無（HeaderV2 內部段落以原檔內 deletion 處理；不刪整檔）

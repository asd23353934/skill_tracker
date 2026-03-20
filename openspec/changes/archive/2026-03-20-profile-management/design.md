## Context

Profile 系統由 `ConfigManager` 提供 CRUD，`App` 負責載入與應用。
所有 Profile 以 `{name}.json` 儲存於 `profiles/` 目錄，
`config.json → settings.current_profile` 記錄目前使用中的 Profile 名稱。

切換 Profile 的完整流程（`_apply_profile()`）：
1. 重置所有技能的 `cooldown` 到原始值、`hotkey` 清空
2. 套用 profile 的 `hotkeys`、`cooldown_overrides`
3. 套用 profile 的 `permanent`、`loop`、`alert_enabled`、各種 override

## Goals / Non-Goals

**Goals:**
- 記錄 Profile CRUD 行為契約（含檔名安全驗證規則）
- 記錄 `_apply_profile()` 的重置與套用順序
- 記錄缺失欄位補足機制

**Non-Goals:**
- 修改現有 Profile 格式
- 支援 Profile 匯出 / 匯入

## Decisions

### 檔名安全驗證（Path Traversal 防護）

`_validate_filename()` 拒絕包含 `/`、`\`、`..` 的名稱，防止路徑穿越攻擊。
空字串亦被拒絕。所有 CRUD 方法呼叫前均先驗證。

### 切換時先重置後套用

`_apply_profile()` 先將所有技能重置為預設狀態（hotkey 清空、cooldown 還原），
再套用新 Profile 的設定，確保無舊設定殘留。

### load_profile 缺失欄位補足

舊版 Profile 可能缺少新增的欄位（如 `alert_seconds_overrides`），
`load_profile()` 以空字典補足，保持向後相容。

## Risks / Trade-offs

- [風險] Profile 名稱驗證僅基於字元黑名單，合法但奇特的名稱（如純數字）均被接受
  → 緩解：足以防止路徑穿越；UI 層另有輸入提示
- [風險] `_apply_profile()` 不發出任何 Qt signal，UI 需自行在呼叫後重新整理
  → 緩解：App 在切換後呼叫對應 UI refresh 方法

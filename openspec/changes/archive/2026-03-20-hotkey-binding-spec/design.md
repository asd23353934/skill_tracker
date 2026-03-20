## Context

快捷鍵綁定系統由 `HotkeyManager` 負責，透過 `pynput.keyboard.Listener` 全域監聽鍵盤事件。
系統支援兩個獨立命名空間：技能（`profiles/{name}.json → hotkeys`）與怪物（`config.json → monsters[].hotkey`）。
兩者快捷鍵互不衝突，同一按鍵可同時指定給一個技能與一個怪物。

目前狀態：
- 核心邏輯已在 `hotkey_manager.py` 實作，但無正式規格
- 捕捉流程為互斥模式：`waiting_for` 非空時停止正常觸發
- 快捷鍵統一正規化為大寫字串（`key_str = key_name.upper()`）

## Goals / Non-Goals

**Goals:**
- 正式記錄快捷鍵系統的行為契約（捕捉、衝突、觸發、儲存）
- 明確區分技能命名空間與怪物命名空間的隔離規則
- 記錄執行緒安全要求

**Non-Goals:**
- 修改現有實作邏輯
- 支援組合鍵（Ctrl+X 等）
- 跨平台快捷鍵支援（目前僅 Windows）

## Decisions

### 快捷鍵命名空間隔離

技能與怪物使用獨立命名空間，相同按鍵可同時指定給一個技能與一個怪物。

**理由**：技能觸發與怪物計時為不同功能，用戶可能合理地希望同一按鍵觸發兩者。
衝突清除僅在同一命名空間內執行（技能清技能、怪物清怪物）。

### 快捷鍵儲存位置分離

- 技能快捷鍵：`profiles/{name}.json → hotkeys`（配置可變區）
- 怪物快捷鍵：`config.json → monsters[].hotkey`（全域可變區）

**理由**：符合現有 DATA_FORMAT.md 規範——技能狀態屬於配置，怪物為全域狀態。

### 捕捉期間暫停觸發

進入捕捉模式（`enabled = False`）時，所有正常快捷鍵觸發暫停，直到捕捉完成或失敗。

**理由**：避免捕捉目標鍵時意外觸發技能或怪物計時。

### 執行緒安全：UI 操作必須回主執行緒

`pynput` Listener 在 daemon thread 執行，所有 UI 更新必須透過 `app.after(0, func)` 排回主執行緒。

## Risks / Trade-offs

- [風險] 捕捉模式下若應用程式無法回應鍵盤（如另一視窗攔截），`waiting_for` 將永遠不清除
  → 緩解：用戶可點擊其他 UI 元素取消（待確認 UI 層實作）

- [風險] 怪物快捷鍵寫入 `config.json` 靜態區附近，若程式中止可能損壞資料
  → 緩解：寫入前先完整讀取並覆寫整個 monsters 陣列

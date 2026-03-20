## Why

目前專案中訊息顯示方式不統一：35 處使用 `QMessageBox`（中央阻塞彈窗），僅 3 處使用既有的 Toast 系統（左下浮動非阻塞）。阻塞式彈窗打斷使用者操作流程，與桌面工具的輕量互動體驗不符。統一改用 Toast 可提升 UI 一致性與操作流暢度。

## What Changes

- 將所有 `QMessageBox.information()`、`QMessageBox.warning()`、`QMessageBox.critical()` 替換為 `app.toast.show(message, type)` 呼叫
- 需要使用者確認的 `QMessageBox.question()`（刪除確認、覆蓋確認等）**保留為對話框**，因其需要阻塞等待使用者回應
- 啟動失敗的 `QMessageBox.critical(None, ...)` 保留，因為此時 App 尚未初始化，Toast 系統不可用
- 對話框（dialogs/）中的訊息需透過 callback 或參數將 `app` 引用傳入，以存取 toast 系統
- `setToolTip` 懸停提示維持不變（非通知訊息）

## Capabilities

### New Capabilities

- `unified-toast-notification`: 統一所有非阻塞提示訊息（成功、警告、錯誤）透過左下角 Toast 系統顯示

### Modified Capabilities

(none)

## Impact

- Affected code:
  - `src/ui/app.py` — 2 處 QMessageBox
  - `src/ui/pages/mapleworld_page.py` — 10 處 QMessageBox
  - `src/ui/pages/overlay_page.py` — 2 處 QMessageBox
  - `src/ui/dialogs/potion_save_dialog.py` — 約 12 處 QMessageBox
  - `src/ui/dialogs/settings_dialog.py` — 5 處 QMessageBox
  - `src/ui/dialogs/profile_dialog.py` — 9 處 QMessageBox
  - `src/ui/dialogs/skill_detail_dialog.py` — 2 處 QMessageBox

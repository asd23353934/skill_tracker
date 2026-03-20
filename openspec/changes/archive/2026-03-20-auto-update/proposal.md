# auto-update

## Why

自動更新系統（`Updater`）透過 GitHub Release API 檢查版本，並提供下載功能，
但版本比較邏輯、asset 選擇優先順序、下載流程均無正式規格文件。

## What Changes

- 建立 `auto-update` 規格，正式記錄：
  - GitHub Release API 檢查流程與 timeout 設定
  - 版本比較邏輯（`packaging` 優先，fallback 數值比較）
  - asset 選擇優先順序（`.exe` > archive > fallback URL）
  - 下載流程（串流分塊、progress callback、失敗清理）
  - `update_launcher.bat` 啟動機制

## Capabilities

### New Capabilities

- `auto-update`: 自動更新規格，涵蓋版本檢查、asset 選擇、下載、啟動器機制

### Modified Capabilities

（無）

## Impact

- Affected specs: `auto-update`（新建）
- Affected code:
  - `src/ui/updater.py`（核心實作）
  - `src/ui/dialogs/update_dialog.py`（更新通知 UI）

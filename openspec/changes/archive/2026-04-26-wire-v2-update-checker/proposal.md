## Why

V2 預覽 shell（`main_v2.py` / `PreviewWindow`）目前完全沒有自動更新檢查機制：啟動時不會背景查詢 GitHub Release、偵測到新版時沒有任何提示、使用者也無從手動觸發。V1 的 `App`（`src/ui/app.py:98`）會在啟動 1 秒後跑 `_check_for_updates`，並用 `UpdateDialog` 顯示更新提示，這個能力必須延伸到 V2，使用者升級到 V2 之後才不會錯過版本更新。

## What Changes

- 在 V2 啟動流程加入「啟動 1 秒後背景檢查 GitHub Release」的排程，行為與 V1 等價。
- 偵測到新版本時，在主執行緒以 `PreviewWindow` 為父視窗開啟 V1 既有的 `UpdateDialog`，提供下載/安裝按鈕。
- 網路失敗、`requests` 未安裝、或無新版時 SHALL NOT 彈出對話框、SHALL NOT 中斷啟動流程；錯誤僅寫入 console / log，不向使用者顯示噪音。
- 完整複用 `src/infrastructure/updater.py` 的 `Updater.check_for_updates()` 與 `src/ui/dialogs/update_dialog.py` 的 `UpdateDialog`，不在 V2 重新實作下載邏輯或 UI。
- 新增 `verify_v2_update_checker.py` 驗證腳本，覆蓋三條路徑：(a) 有新版時 `UpdateDialog` 正確開啟、(b) 無新版時不彈窗、(c) 網路失敗時不 crash。
- HeaderV2 不新增任何按鈕（`v2-header-shell` 規範限制只能放 window controls + 拖曳區），更新入口僅靠自動彈窗，不暴露手動觸發 UI。

## Non-Goals

- 不新增 V2 settings dialog 中的「手動檢查更新」按鈕（屬於後續變更）。
- 不重寫 `Updater` 或 `UpdateDialog` 的內部行為，亦不更動 `auto-update` 既有的 V1 觸發路徑。
- 不為 V2 設計獨立的更新 UI（沿用 V1 對話框，避免雙份維護）。
- 不打包進度顯示元件、不引入新依賴。

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `auto-update`: 新增「V2 預覽 shell 啟動排程」與「V2 對話框父視窗指定」兩項需求；既有 V1 行為保持不變。

## Impact

- Affected specs: `auto-update`
- Affected code:
  - Modified:
    - main_v2.py (在 `PreviewWindow.__init__` 末段排程 `QTimer.singleShot(1000, ...)` 觸發更新檢查；以 `app_ctx.after()` 把結果排回主執行緒)
  - New:
    - verify_v2_update_checker.py (驗證腳本：三條路徑用 monkeypatch 模擬 `Updater.check_for_updates()` 回傳值)
  - Reused unchanged:
    - src/infrastructure/updater.py (`Updater.check_for_updates`)
    - src/ui/dialogs/update_dialog.py (`UpdateDialog`)

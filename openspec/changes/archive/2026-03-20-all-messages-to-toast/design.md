## Context

專案已有完整的 `ToastManager` 系統（`src/ui/toast.py`），定位於左下角，支援 `success` / `error` / `info` 三種類型。目前僅 3 處呼叫 `app.toast.show()`，其餘 35 處訊息仍使用 `QMessageBox`（阻塞式中央彈窗）。

主要挑戰：`dialogs/` 目錄下的對話框（`ProfileDialog`、`SettingsDialog`、`PotionSaveDialog`、`SkillDetailDialog`）繼承自 `BaseDialog`，部分實例的建立方式導致取得 `app.toast` 的路徑不一致。

## Goals / Non-Goals

**Goals:**
- 所有 `QMessageBox.information()`、`QMessageBox.warning()`、`QMessageBox.critical()` 替換為 `app.toast.show()`
- Toast 類型對應：information → `"info"`、warning → `"info"`（警示但不嚴重）、critical → `"error"`
- 對話框類中透過 `self.app` 存取 Toast（`BaseDialog` 已持有 `app` 引用）

**Non-Goals:**
- `QMessageBox.question()` 確認對話框**不替換**，因需阻塞等待使用者回應
- 啟動前（`app.py` L97 的 `QMessageBox.critical(None, ...)` ）不替換，因 Toast 系統尚未初始化
- `setToolTip` 懸停提示不變動
- 不修改 `Toast` / `ToastManager` 本身的實作

## Decisions

### 對話框存取 app.toast 的方式

`BaseDialog.__init__` 接收 `app` 並儲存為 `self.app`。所有繼承的對話框直接使用 `self.app.toast.show(...)` 即可，無需額外傳參。

**替代方案**：透過 callback 傳入 `show_toast` 函數。
**拒絕原因**：`self.app` 已可用，引入 callback 增加不必要的介面複雜度。

### QMessageBox.warning 對應 Toast 類型

`QMessageBox.warning` 語意介於 info 與 error 之間，現有 Toast 無 `"warning"` 類型。
**決策**：`warning` 一律對應 `"info"` 類型（藍色）；只有程式錯誤/操作失敗才用 `"error"`（紅色）。

**替代方案**：新增 `"warning"` 類型（黃色）至 `Toast`。
**拒絕原因**：超出此次範圍，可獨立做。當前 `info` 藍色足夠傳達提示語意。

### mapleworld_page.py 的 Toast 存取

`MapleworldPage` 為 `QWidget`，透過 `self.app`（建構時傳入）存取 Toast。

## Risks / Trade-offs

- [Risk] 部分 `QMessageBox.information` 訊息較長，Toast 寬度固定可能截斷 → Mitigation：`msg_lbl` 已為 `QLabel`，可設 `wordWrap` 或截斷，視實際測試結果決定
- [Risk] `QMessageBox.critical` 彈窗使用者習慣看到強調視覺，改為 Toast 紅框可能被忽略 → Mitigation：3 秒自動消失，重要錯誤訊息維持 Toast `"error"` 類型以紅色邊框區分

## Migration Plan

無破壞性變更，逐檔替換即可。執行 `python main.py` 觀察訊息是否正確以 Toast 顯示。

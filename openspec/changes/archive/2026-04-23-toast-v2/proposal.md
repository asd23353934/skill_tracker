## Why

V2 預覽（`python main.py --v2`）目前 `toast` 槽位是 `_NoopToast`（main_v2.py），所有通知只 print 到 stdout，使用者完全看不到。`AppCoreMixin` 多處共用方法呼叫 `self.toast.show(msg, kind)` —— `clear_all_hotkeys` 完成後、未來 settings dialog 儲存後、autosave 失敗 / network error 等都靠 toast 反饋。沒 toast 等於使用者操作後沒任何回饋訊號，UX 嚴重缺失。

## What Changes

- 新增 `src/ui_v2/toast_v2.py`，內含：
  - `ToastV2(QFrame)` —— 單則 toast widget，按 V2Theme 視覺（V2 圓角 / V2 顏色 / V2 字型），沿用 V1 的 fade-in / fade-out / 自動消失行為（3000 ms 自動關閉）
  - `ToastManagerV2` —— 容器 + 排隊管理；同 V1 ToastManager API：`show(message, kind)`、`kind ∈ {"info", "success", "warning", "error"}`
- 在 `main_v2.py` 中：
  - `PreviewWindow.__init__` 末段建立 `ToastManagerV2(self)`，賦值到 `app_ctx.toast`
  - 移除舊 `_NoopToast` 類定義
- toast 浮現位置：PreviewWindow **右下角**（V2 視覺一致性；V1 在左下角，刻意分流避免被同 monitor 同位置重疊）
- toast 容器使用 `QApplication.activeWindow()` 為 parent 不可行（V2 dialog 開啟時會擋）—— 直接以 PreviewWindow 為 parent，固定 z-order on top

## Non-Goals

- **不改 V1 ToastManager / Toast**：V1 既有 `src/ui/toast.py` 完全不動。
- **不引入新 toast 種類**：沿用 V1 的 4 種 (`info`/`success`/`warning`/`error`)；`warning` 走與 V1 相同的橘色處理。
- **不接 settings dialog**：設定對話框另開 spec；本 change 只負責 toast 系統本身能跑。
- **不抽 V1 / V2 共用 ToastManager 介面**：兩個類各自獨立，避免 V1 改動牽連。
- **不實作 toast 點擊跳轉 / 動作按鈕**：V1 也沒有，V2 維持簡單通知。

## Capabilities

### New Capabilities

- `toast-v2`: V2 預覽介面的視覺通知系統，沿用 V1 ToastManager 的 `show(msg, kind)` API 介面但獨立實作，視覺風格符合 V2Theme。

### Modified Capabilities

(none)

## Impact

- Affected specs: 新增 `toast-v2`
- Affected code:
  - New: `src/ui_v2/toast_v2.py`、`verify_toast_v2.py`
  - Modified: `main_v2.py`（移除 `_NoopToast`、改用 `ToastManagerV2`）
  - Removed: 無

# 架構規則

## 職責分離

- **App (app.py)**: 只做協調，初始化各 Manager，串接事件，包含 `_Dispatcher` 執行緒安全排程
- **Manager 類別**: 各自負責單一領域 (config / skill / hotkey / window / overlay / sound)
- **UI 元件**: 接收 callback，不直接操作其他元件的狀態
- **Pages**: 繼承 QWidget，透過 `self.app` 存取應用狀態，放在 `pages/` 目錄
- **dialog/**: 所有對話框繼承 `BaseDialog`

## 狀態管理

- 技能狀態 (`permanent`, `loop`, `alert_enabled`) 集中在 App 實例
- UI 狀態透過 Qt 訊號/槽雙向同步
- 狀態變更後呼叫 `config_manager.save_profile()` 持久化

## 事件模式

- 使用 callback 函數或 Qt 訊號傳遞事件
- 鍵盤事件走 pynput daemon thread → `_Dispatcher.schedule()` 排回主執行緒
- 倒數計時走 `QTimer` 輪詢 (100ms)

## 執行緒安全

- pynput listener 為 daemon thread，**不可直接操作 UI**
- UI 更新必須在主執行緒，跨執行緒呼叫使用 `app.after(ms, func)`：
  - `ms=0`：透過 `_Dispatcher` Signal/Slot (QueuedConnection) 立即排隊
  - `ms>0`：`_Dispatcher` 先排回主執行緒，再用 `QTimer.singleShot` 延遲
- 網路請求 (更新檢查) 用 `QTimer.singleShot` 延遲啟動，不阻塞 UI

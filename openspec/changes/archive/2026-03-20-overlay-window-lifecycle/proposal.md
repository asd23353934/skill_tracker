# overlay-window-lifecycle

## Why

浮動圖片視窗（Overlay）系統管理複雜的視窗生命週期、透明度/位置/尺寸持久化，
以及使用者資料路徑策略，但均無正式規格，後續維護難以確認行為正確性。

## What Changes

- 建立 `overlay-window-lifecycle` 規格，正式記錄：
  - 視窗開關（toggle / open / close / close_all）生命週期
  - 透明度/位置/尺寸的即時更新與持久化規則
  - 圖片格式限制與初始尺寸計算（最長邊 ≤ 600px）
  - 使用者資料路徑策略（exe 同層 vs 開發模式）
  - 新增/刪除覆蓋圖的完整流程

## Capabilities

### New Capabilities

- `overlay-window-lifecycle`: 浮動圖片視窗規格，涵蓋生命週期、持久化、格式限制、路徑策略

### Modified Capabilities

（無）

## Impact

- Affected specs: `overlay-window-lifecycle`（新建）
- Affected code:
  - `src/ui/overlay_manager.py`（核心管理器）
  - `src/ui/overlay_window.py`（浮動視窗實作）
  - `src/ui/pages/overlay_page.py`（UI 頁面）
  - `config.json → overlays[]`（資料欄位）

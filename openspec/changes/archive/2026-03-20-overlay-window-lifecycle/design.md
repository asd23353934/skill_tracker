## Context

`OverlayManager` 管理所有浮動圖片視窗的生命週期，使用 `active_windows: dict`（overlay_id → OverlayWindow）追蹤開啟中的視窗。
Overlay 資料存於 `config.json → overlays[]`，包含：`id`, `name`, `file`, `alpha`, `x`, `y`, `width`, `height`。
圖片檔案存於 `overlays/` 目錄（使用者可寫入位置）。

使用者資料路徑由 `_user_path()` 決定：
- 打包模式（`sys.frozen`）：exe 所在目錄
- 開發模式：專案根目錄

## Goals / Non-Goals

**Goals:**
- 記錄視窗生命週期（toggle/open/close/close_all）
- 記錄持久化觸發時機（alpha/位置/尺寸）
- 記錄圖片格式白名單與初始尺寸計算
- 記錄使用者資料路徑策略

**Non-Goals:**
- 修改現有 Overlay 機制
- 支援非圖片類型的 Overlay（如影片）

## Decisions

### 尺寸調整策略：關閉後重新開啟

`resize_window()` 的實作為：先記錄當前位置、更新資料、關閉視窗、50ms 後重新開啟。
這是因為 OverlayWindow 建立時以固定尺寸初始化，不支援動態調整大小。

**決策**：spec 明確記錄此 50ms 重開策略，避免未來誤認為 bug。

### 使用者資料路徑與打包相容

`_user_path()` 解決 PyInstaller 打包後 `sys.executable` 與開發模式的路徑差異。
使用者資料（overlays/、sounds/、profiles/）必須使用 `_user_path()`，不可使用 `resource_path()`。

### 圖片格式白名單

允許的格式：`.png`, `.jpg`, `.jpeg`, `.bmp`, `.gif`, `.webp`。
其他格式（如 `.tiff`）直接拒絕，`add_overlay()` 返回 `None`。

### 初始尺寸計算

新增 Overlay 時：以 PIL 讀取原始尺寸，最長邊縮放至不超過 600px（保持長寬比）。
無法讀取時退化為 200×200。

## Risks / Trade-offs

- [風險] 尺寸調整時有 50ms 閃爍（視窗短暫消失再出現）
  → 緩解：屬已知設計折衷，spec 明確記錄
- [風險] GIF 格式僅顯示第一幀（OverlayWindow 不支援動畫）
  → 緩解：spec 中不保證 GIF 動畫支援

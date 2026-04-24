## Why

V2 資源中心（MapleWorldPageV2）的「掃描資源」按鈕目前只跳 toast「尚未接到 V2」，核心掃描/解碼邏輯全數嵌在 V1 頁面 `src/ui/pages/mapleworld_page.py` 的 400+ 行私有方法內（_start_scan / _scan_worker / _start_web_scan / _web_cache_worker / _extract_all_dds / _extract_images_from_bytes）。若直接複製到 V2 會造成 V1 / V2 兩份重複解碼邏輯，日後維護成本過高。需抽出為獨立 infrastructure 模組，讓 V1 / V2 頁面共用。

## What Changes

- 新增 `src/infrastructure/mapleworld_scanner.py` — 純 Python + PIL + requests，無 Qt 依賴，提供：
  - `scan_unity(game_path, on_progress, on_done)` — 掃描 `resource_cache/` 下 `.win.mod`，抽出 DDS 與嵌入式圖像，解碼為 PNG 寫入 `images/mapleworld/`
  - `scan_web(game_path, on_progress, on_done)` — 掃描 `Vuplex.WebView/` 快取，支援 4 個 phase（直接位元組掃描 / gzip 解壓 / URL 下載 / base64 解碼）
  - DDS 多圖抽取 helper（`_extract_all_dds` 等價物）
  - Bytes → 多格式圖片抽取 helper（`_extract_images_from_bytes` 等價物）
  - 背景執行緒由模組負責啟動；callback 由呼叫端在自己的 UI 執行緒排回
- `src/ui/pages/mapleworld_page.py`：
  - 移除上述私有方法本體，改為呼叫 `mapleworld_scanner` 的公開 API
  - 保留 V1 UI 控件（進度條、狀態列、掃描按鈕）與完成後 `_on_scan_done` / `_on_web_scan_done` 的 UI 回寫邏輯
- `src/ui_v2/pages/mapleworld_page_v2.py`：
  - `_on_scan` 改為呼叫 `mapleworld_scanner.scan_unity`（與對應的 web 掃描），進度以 toast / 狀態列呈現，完成後重新 `_scan_dir` + `_render_grid`
  - 掃描進行中按鈕置為 disabled，避免重複觸發
- 不改 PNG 輸出位置（仍在 `images/mapleworld/`）
- 不改 `config.json` / `config_user.json` / `profiles/` 結構
- 不改 V1 / V2 既有 UI 版面

## Non-Goals

- 不新增掃描結果來源（不支援其他遊戲路徑 / 其他快取格式）
- 不改變解碼演算法或輸出檔名規則（維持 `{UUID}.png` / `{UUID}_{index}.png`）
- 不處理掃描進度的細緻化（維持 V1 原本的每 500 個檔報一次）
- 不引入新的第三方依賴（繼續用 PIL / requests / 標準庫）
- 不把 V1 頁面下架（V1 / V2 並存，使用 `--v1` 入口的使用者仍可掃描）
- 不把「圖片放大預覽」或「選取匯出」等 UI 行為抽出 — 僅限掃描/解碼/寫檔路徑
- 不在此變更中實作 V2 的「已掃描結果列表」的進階 UI（保留現有 `_scan_dir` + grid 顯示即可）

## Capabilities

### New Capabilities

- `mapleworld-scanner`: 純 infrastructure 層掃描服務，無 Qt 依賴；提供 Unity `.win.mod` DDS / 嵌入式圖像解碼與 Vuplex.WebView 快取多 phase 提取 API，以 callback 回報進度與完成結果。

### Modified Capabilities

（無 — V1 / V2 頁面僅為 caller 行為改動，不涉及 spec 層級需求變動）

## Impact

- Affected specs:
  - New: `mapleworld-scanner`
- Affected code:
  - New:
    - src/infrastructure/mapleworld_scanner.py
  - Modified:
    - src/ui/pages/mapleworld_page.py
    - src/ui_v2/pages/mapleworld_page_v2.py
  - Removed:
    - （無獨立檔案移除；V1 內私有方法本體刪除後改 import）

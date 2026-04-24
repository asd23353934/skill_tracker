## 1. 建立 scanner 模組骨架

- [x] 1.1 新增 `src/infrastructure/mapleworld_scanner.py`，撰寫 module docstring 說明 callback 在 worker thread 執行、確保 scanner module has no Qt dependency（只 import stdlib / PIL / requests）
- [x] 1.2 依設計「模組邊界：純 infrastructure、callback 介面」定義公開 API 簽章：`scan_unity(game_path, on_progress, on_done)`、`scan_web(game_path, on_progress, on_done)`，內部以 `threading.Thread(daemon=True)` 啟動 worker

## 2. 搬移解碼 helper

- [x] 2.1 將 V1 `_extract_all_dds` 搬到 scanner 並改為 module-level `extract_all_dds`；依設計「私有 helper 公開為模組級函式」確認簽章與行為對齊 Extraction helpers are module-level and reusable 要求
- [x] 2.2 將 V1 `_extract_images_from_bytes` 搬到 scanner 並改為 module-level `extract_images_from_bytes`，保留多格式（PNG/JPEG/WebP/GIF）偵測邏輯

## 3. 搬移 Unity 掃描 worker

- [x] 3.1 搬移 `_scan_worker` 本體到 scanner 成為 `scan_unity` 的 worker；呼叫 `extract_all_dds` / `extract_images_from_bytes`，寫入 `images/mapleworld/{uuid}.png`；這對應 scan_unity extracts images from .win.mod files 要求
- [x] 3.2 在 `scan_unity` 檢查 `resource_cache/` 目錄存在性，不存在時呼叫 `on_done([], 0, fatal_msg)` 後返回
- [x] 3.3 保留 V1 現有的每 500 檔一次 `on_progress` 進度字串格式
- [x] 3.4 per-file `try/except` 隔離失敗，累計 errors 並最終由 `on_done` 回報；這對應 Scanner tolerates per-file decode errors 要求

## 4. 搬移 Web 掃描 worker

- [x] 4.1 搬移 `_web_cache_worker` 本體（含 Phase 0 檔案列舉、Phase 1 byte-scan、Phase 2 gzip、Phase 3 URL 下載、Phase 4 base64 解碼）到 scanner 成為 `scan_web` 的 worker；這對應 scan_web extracts images from Vuplex.WebView cache 要求
- [x] 4.2 在 `scan_web` 檢查 `Vuplex.WebView/` 目錄存在性，不存在時呼叫 `on_done([], 0, fatal_msg)`
- [x] 4.3 保留 V1 的 `web_` / `cdn_` 檔名前綴規則，確保 V2 grid 可正確分類到 WebView tab

## 5. V1 接線

- [x] 5.1 `src/ui/pages/mapleworld_page.py` 移除 `_scan_worker` / `_web_cache_worker` / `_extract_all_dds` / `_extract_images_from_bytes` 四個方法本體（依設計「V1 頁面的改動範圍」）
- [x] 5.2 `_start_scan` 改為呼叫 `mapleworld_scanner.scan_unity`，傳入用 `app.after(0, ...)` 包裝的 `on_progress` / `on_done`；這對應 UI pages delegate scanning to the scanner module 要求（V1 部分）
- [x] 5.3 `_start_web_scan` 改為呼叫 `mapleworld_scanner.scan_web`，callback 同樣 dispatch 回主執行緒
- [x] 5.4 保留 V1 既有 `_on_scan_done` / `_on_web_scan_done` 完成後的 UI 更新行為不動
- [x] 5.5 手動 smoke test：啟動 `python main.py --v1` 跑一次 Unity 掃描與 Web 掃描，驗證輸出 PNG 數與行為與重構前一致

## 6. V2 接線

- [x] 6.1 `src/ui_v2/pages/mapleworld_page_v2.py` 的 `_on_scan` 改為呼叫 `mapleworld_scanner.scan_unity`；依設計「V2 頁面的 UI 整合」先做路徑驗證 + 按鈕 disabled + toast「掃描中…」
- [x] 6.2 `on_progress` 更新 `_stat_lbl`、`on_done` 重新呼叫 `_scan_dir()` + `_render_grid()` 並顯示完成 toast、重新 enable 按鈕；這對應 UI pages delegate scanning to the scanner module 要求（V2 部分）
- [x] 6.3 callback 一律透過 `self.app.after(0, ...)` 回主執行緒
- [x] 6.4 手動 smoke test：啟動 `python main.py` 進入 V2 資源中心，執行 Unity 掃描並確認新圖片出現在 grid

## 7. 驗證與收尾

- [x] 7.1 執行 `python -c "import src.infrastructure.mapleworld_scanner"` 在乾淨環境確認無 Qt import side-effect
- [x] 7.2 執行 `python check_release.py`（或專案既有 verify script）確認無 regression
- [x] 7.3 依 CLAUDE.md 規範跑 `/simplify` + `/security-review` 後再 commit

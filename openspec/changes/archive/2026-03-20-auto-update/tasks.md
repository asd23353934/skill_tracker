## 1. 版本檢查規格驗證

- [x] 1.1 確認 `check_for_updates()` 在 `HAS_REQUESTS=False` 時立即返回 error dict，符合「Version check queries GitHub Release API」規格
- [x] 1.2 確認 API 請求 timeout 為 5 秒，網路/HTTP 錯誤返回 error dict，符合「Version check」規格

## 2. 版本比較規格驗證

- [x] 2.1 確認 `_compare_versions()` 優先使用 `packaging.version.parse()`，符合「Version comparison uses packaging with numeric fallback」規格（對照設計決策「版本比較優先順序」）
- [x] 2.2 確認 fallback 為整數列表比較，異常時返回 `False`，符合「Version comparison」規格

## 3. Asset 選擇規格驗證

- [x] 3.1 確認 asset 選擇優先順序：`.exe` > archive > fallback URL，符合「Download asset is selected by priority」規格（對照設計決策「Asset 選擇優先順序」）

## 4. 下載規格驗證

- [x] 4.1 確認 `download_update()` 使用 8192-byte 串流分塊，符合「Download streams with progress callback」規格（對照設計決策「下載失敗清理」）
- [x] 4.2 確認下載失敗時刪除暫存檔並返回 `False`，符合「Failed download is cleaned up」規格

## 5. 啟動器路徑驗證

- [x] 5.1 確認 `get_launcher_path()` 使用 `resource_path()` 解析路徑，符合「Update launcher path uses resource_path」規格

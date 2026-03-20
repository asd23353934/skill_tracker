## Context

`Updater` 透過 `requests.get(GITHUB_API_URL, timeout=5)` 查詢最新 release。
版本比較使用 `packaging.version.parse()`（若已安裝），否則 fallback 到數值分段比較。
下載使用串流分塊（`iter_content(chunk_size=8192)`），支援進度回調。

更新流程：
1. 應用啟動後延遲（`QTimer.singleShot`）執行 `check_for_updates()`
2. 若有新版本，顯示 `UpdateDialog` 通知使用者
3. 使用者確認後，呼叫 `download_update()` 下載到暫存目錄
4. 啟動 `update_launcher.bat` 執行實際更新替換

## Goals / Non-Goals

**Goals:**
- 記錄版本比較優先順序（packaging 優先）
- 記錄 asset 選擇優先順序
- 記錄下載失敗時的清理機制

**Non-Goals:**
- 修改更新流程
- 支援非 GitHub 的更新來源

## Decisions

### 版本比較優先順序

優先使用 `packaging.version.parse()`（語意版本比較），
不可用時 fallback 到整數列表比較（`[int(x) for x in ver.split('.')]`）。
任何比較異常均返回 `False`（視為無更新，避免誤觸發）。

### Asset 選擇優先順序

1. `.exe`（最優先）
2. `.7z` / `.zip` / `.tar.gz`（備選）
3. 硬編碼 fallback URL（`skill_tracker_v{version}.zip`）

### 下載失敗清理

下載失敗時刪除不完整的暫存檔，防止下次誤用損壞檔案。

## Risks / Trade-offs

- [風險] `requests` 模組未安裝時更新功能停用（靜默）
  → 緩解：`HAS_REQUESTS` 旗標控制，spec 標注為可選依賴
- [風險] API 請求 timeout 為 5 秒，網路慢時可能誤判
  → 緩解：屬已知折衷；失敗返回 `error` 欄位，不影響主程式

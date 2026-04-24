## Context

V1 MapleWorld 頁面 `src/ui/pages/mapleworld_page.py` 將掃描與解碼邏輯以私有方法形式嵌在 UI 類別內（~400 行）。V2 MapleWorldPageV2 目前僅能讀取既有 `images/mapleworld/` PNG，「掃描資源」按鈕僅顯示 toast。V1 / V2 頁面同時存在（使用者可用 `--v1` 啟動舊介面），未來還要維護兩條 UI，但掃描邏輯應只有一份。

約束：
- 不得引入 Qt 依賴到 infrastructure 層（遵循 `docs/ARCHITECTURE.md` 職責分離）
- 背景執行緒不可直接觸碰 UI — 呼叫端負責以 `app.after(0, ...)` 把 callback 排回主執行緒
- 維持既有檔名 / 輸出路徑 / 解碼規則，避免影響既有使用者資料

## Goals / Non-Goals

**Goals**

- 把掃描與解碼純邏輯從 UI 抽離到 `src/infrastructure/mapleworld_scanner.py`
- 提供 V1 / V2 可共用的最小 API
- 保留既有行為：輸出目錄、檔名、phase 策略、錯誤容忍

**Non-Goals**

- 不優化掃描效能
- 不改解碼演算法 / 不新增格式支援
- 不下架 V1 頁面
- 不做 UI 共用元件（V1 / V2 UI 仍各自獨立）

## Decisions

### 模組邊界：純 infrastructure、callback 介面

將新模組放在 `src/infrastructure/mapleworld_scanner.py`，對外公開：

```
scan_unity(game_path: str, on_progress: Callable[[str], None], on_done: Callable[[list, int, str|None], None]) -> None
scan_web(game_path: str, on_progress: Callable[[str], None], on_done: Callable[[list, int, str|None], None]) -> None
```

兩個 API 內部各自 `threading.Thread(daemon=True).start()`，立即返回。`on_progress(msg)` / `on_done(saved, errors, fatal)` 在 worker 執行緒被呼叫；呼叫端（V1 / V2 UI）自行用 `app.after(0, ...)` dispatch 回主執行緒。

`saved` 型別沿用 V1 現狀：`list[tuple[name, PIL.Image, save_path, dir_type]]`（Unity）/ `list[tuple[name, PIL.Image, save_path, source_tag]]`（Web），讓 V1 UI 幾乎零改動；V2 目前只需重掃目錄不需 PIL image，可忽略多餘欄位。

**為何選 callback 而非 QThread/Signal**：infrastructure 層不能 import Qt；callback 是最小公約數，V1 / V2 都能接。

**替代方案**：回傳 `queue.Queue` 讓 UI 輪詢 — 拒絕，增加 UI 端輪詢時序複雜度。

### 私有 helper 公開為模組級函式

`_extract_all_dds` / `_extract_images_from_bytes` 改名為 `extract_all_dds` / `extract_images_from_bytes`，模組級函式（非類別方法），保留同簽章行為。

**為何**：這兩個 helper 是純演算法、無狀態，不該綁在 UI 類別上。

### V1 頁面的改動範圍

V1 `_scan_worker` / `_web_cache_worker` 整體被 `scan_unity` / `scan_web` 取代；V1 頁面只保留 `_start_scan` / `_start_web_scan` 的 UI 設定（按鈕 disable、狀態字、progress bar 顯示），然後委派給 scanner；callback 以 lambda 包住 `app.after(0, ...)` 排回主執行緒。

`_on_scan_done` / `_on_web_scan_done` 完成後回寫 UI（列表、縮圖、done 狀態）維持不動。

### V2 頁面的 UI 整合

V2 `_on_scan` 改為：
1. 驗證 game_path（存在 `resource_cache/`）
2. 按鈕 disabled + toast「掃描中…」
3. 呼叫 `scan_unity`，`on_progress` → 更新 `_stat_lbl`；`on_done` → 重新 `_scan_dir()` + `_render_grid()` + toast 完成訊息 + 重新 enable 按鈕

初版只接 Unity 掃描；Web 掃描（改在另一按鈕或下拉選項）先不加入 V2 UI，避免擴張本次範圍。若使用者 V2 有需求，後續變更再補。

## Risks / Trade-offs

- [執行緒安全：PIL Image 跨執行緒傳遞] → PIL 影像物件在 worker 執行緒建立後透過 callback 傳給 UI 執行緒；V1 目前就是這樣做的，PIL 物件為不可變影像資料，讀取安全。V2 不使用這些 PIL 物件（直接重掃目錄），進一步降低風險。
- [callback 於 worker 執行緒觸發，呼叫端若忘記 dispatch 會崩] → 在 scanner docstring / module header 明示「on_progress / on_done 會在 worker 執行緒被呼叫，UI 呼叫端必須自行排回主執行緒」，並在 V1 / V2 接線處統一用 `self.app.after(0, lambda: ...)`。
- [V1 既有行為被動到] → 保留 `_scan_worker` / `_web_cache_worker` 的 try/except 結構、錯誤計數、進度字串格式，以最小差異移植；V1 人工 smoke test（跑一次 Unity 掃描）驗證。
- [V2 進度/完成訊息過於簡陋] → 可接受，初版只求能用；後續 UX 調整不列入本次。

## Migration Plan

- 本專案為桌面 app，無伺服器部署；使用者升級 = 下次 release ZIP
- `images/mapleworld/` 已有的 PNG 保留（輸出規則不變）
- 無資料庫遷移

Rollback：git revert 此 change；V1 行為完全回復。

## Open Questions

（無）

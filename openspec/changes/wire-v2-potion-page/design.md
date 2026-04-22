## Context

V2 預覽 shell 的藥水頁 `src/ui_v2/pages/potion_page_v2.py` 是純視覺殼：所有資料是模組層級的 `DEMO_*` 常量，整頁用 `_potion_section() / _PotionRow` 等「一次建構不更新」的 top-level 函數產生，沒有任何輸入事件綁定、沒有 state、所有按鈕連到 `self._toast_pending()`。

上一個 change 已將計算 / autosave / 紀錄序列化抽到 `src.domain.potion_service.PotionService`（零 Qt），本 change 把 V2 頁面從視覺殼接線成可運作頁面。V1 頁面 `src/ui/pages/potion_cost_page.py` 保留不動 — 兩者共用同一份 `potion_autosave.json`，必須處理並存問題。

相關資源：
- Service：`src/domain/potion_service.py`（DEFAULTS / calc_* / save|load|clear_autosave / serialize / deserialize）
- V1 參考：`src/ui/pages/potion_cost_page.py`（_PotionRow / _PotionSection / _do_autosave / _try_load_autosave / 計時器流程）
- V2 對話框基底：`src/ui_v2/dialogs/base_dialog_v2.py`
- V1 對話框參考：`src/ui/dialogs/potion_save_dialog.py`
- 視覺規範：`docs/DESIGN_V2.md`（顏色 / 間距 / IconBadge）

## Goals / Non-Goals

**Goals:**

- V2 藥水頁的所有使用者互動（輸入、新增/刪除藥水列、儲存/載入、手動/計時器切換、全部重置）都接上 `PotionService`，行為與 V1 對齊
- autosave 檔案格式與 V1 完全一致，切換 V1/V2 可無痛接續編輯
- 右側摘要即時反映左側輸入（使用 V1 的 500ms debounce 節流）
- V2 頁載入時自動還原 autosave（含計時器秒數）

**Non-Goals:**

- 不改 `PotionService` API
- 不改 V1 頁面（若 V1 出現 bug 另開 change）
- 不處理 V1/V2 同時開啟寫同一 autosave 檔的 race condition — 假設使用者一次只開一個入口，以「最後寫入者勝」為可接受行為
- 不實作 V2 紀錄檔 rename / delete UI（留給後續）
- 不加測試框架（專案目前無 `tests/`，沿用 `verify_*.py` 獨立腳本模式）
- 不把右下角「數量計算機」接到 service（純 UI 小工具）

## Decisions

### V2 頁面從函數式組裝改為有狀態 class 組合

**現狀**：`_potion_section() / _PotionRow` 是 top-level 函數，每呼叫一次建出一個 QFrame，沒有保留參照。輸入欄無法被動態讀取，因為 caller 根本沒存參照。

**決策**：把 `_PotionRow / _PotionSection` 改為 class（與 V1 結構對齊），由 `PotionPageV2` 持有 `_hp_section / _mp_section / _combined_section` 三個 section 實例；每個 section 持有一個 `_rows: list[_PotionRow]`。共享的小工具函數（`_input / _icon_btn / _text_btn / _readonly_metric / _section_card`）保留為 top-level helper。

**為何不保持函數式**：輸入事件綁定需要穩定的 widget 參照；否則要在 QFrame tree walk 去抓，又脆弱又慢。

### 資料流：UI 到 _collect_form() 到 Service 再回寫 UI

**決策**：完全複製 V1 的流水線：
1. 每個 `_PotionRow` 提供 `get_data() -> dict`（回 `{name, price, before, after, consumed, cost}`）
2. `PotionPageV2._collect_form()` 蒐集所有 section 的 rows + 楓幣/商店/經驗/分鐘 欄位，回一個 `PotionFormData` dict
3. `_recalc_all()` 呼叫 `PotionService.calc_summary(form)`，用回傳的 8 key dict 更新右側「本次練功摘要」顯示
4. 同一條路徑觸發 `_schedule_autosave()`（500ms debounce）之後呼 `PotionService.save_autosave(form, timer_elapsed=self._timer_elapsed)`

**為何不在 service 內部做 debounce**：service 必須無 Qt 依賴，debounce 需 QTimer；且 V1 已驗證這個分工。

### 輸入事件全走 textChanged / valueChanged 到 _on_input_changed() 單一匯流

**決策**：所有 QLineEdit / QSpinBox 在建立時直接 `widget.textChanged.connect(self._on_input_changed)`；`_on_input_changed()` 做兩件事：`_recalc_all()` + `_schedule_autosave()`。新增/刪除藥水列也呼叫同一個 slot。

**為何不各自綁各自**：信號分散會漏綁。單一匯流簡單且 V1 已驗證。

### 右側本次練功摘要六列標籤綁 self._summary_labels: dict[str, QLabel]

**決策**：建立右側卡片時把八個數值 `QLabel` 放進 dict（key：`income / expense / net / exp_total / net_10 / net_60 / exp_10 / exp_60`），`_recalc_all()` 時逐 key `setText(f"{v:+,}")`。顏色在建立時就設好，不動態換色（保持視覺穩定）。

**為何不直接 rebuild 整塊摘要**：每鍵盤事件 rebuild 成本高、會閃；V1 也走 label update。

### V2 紀錄對話框新建，不沿用 V1

**決策**：新增 `src/ui_v2/dialogs/potion_save_dialog_v2.py` 與 `potion_load_dialog_v2.py`，繼承 `BaseDialogV2`。內部走 `PotionService.serialize / deserialize`（V1 對話框原本直接摸 config_manager，V2 統一從 service 出）。

**為何不共用 V1 對話框**：V1 對話框 QSS 不符 V2 主題（紫色漸層 vs 深色），外觀違和。但邏輯面透過 service 共用。

### V1/V2 併用 potion_autosave.json 採最後寫入者勝

**決策**：不加檔案鎖、不加修改時間檢查。assumption：使用者一次只開一個入口。V2 頁啟動時若偵測到 autosave，無條件還原，視同繼續上次編輯。

**為何不做 cross-process 同步**：成本高（需 file lock 或 watchdog），收益低（非常規使用情境）。若使用者回報衝突，再另開 change 處理。

### 計時器模式：QTimer 1s tick，累計存 self._timer_elapsed（秒）

**決策**：與 V1 同一模式 — 按「開始」啟 QTimer，每秒累加 `_timer_elapsed += 1`，每 60 秒把 `_timer_elapsed // 60` 寫回分鐘 QSpinBox；autosave 把 `_timer_elapsed` 透過 `save_autosave(form, timer_elapsed=...)` keyword 傳入；還原時讀 `record["_timer_elapsed"]`。

**為何不另開 timer 服務**：計時器 tick 純 UI 行為，不需要跨頁共用；service 已暴露 keyword 介面剛好夠用。

## Risks / Trade-offs

- **V1/V2 共用 autosave 的邊緣併發** → 明確寫進 non-goals，靠使用者習慣自律；若社群回報，補 file lock
- **大範圍改寫 `potion_page_v2.py`（約 550 行 到 預計 700+ 行）可能意外破壞視覺** → mitigation：保留所有 `_section_card / _input / _readonly_metric / IconBadge` 等視覺 helper 不動，只改 state 接線部分；每個 section 完成後以肉眼回歸視覺
- **函數式改為 class 改造可能漏綁事件信號** → mitigation：所有輸入事件統一走 `_on_input_changed()` 匯流；補 `verify_potion_page_v2.py` 驗證 `_collect_form()` 產出 dict 結構對
- **V2 對話框初版 QSS 可能不完美** → 先求功能面 parity，視覺微調另行 iterate

## Why

V1 的 `src/ui/pages/potion_cost_page.py` 是一個 1582 行的肥檔，計算邏輯（單列成本、分區小計、總費用、淨收益、時薪、狩獵時間）、autosave、序列化、儲存/載入紀錄全部直接寫在 QWidget 子類別與其內部小元件裡。

V2 已經拉出新的 `src/ui_v2/pages/potion_page_v2.py` UI shell，但因所有計算/持久化邏輯與 V1 widget 耦合，目前 V2 主要按鈕只能 toast「尚未接 V2，請暫用 V1」。要解鎖 V2 完整接線，必須先把 logic 從 V1 widget 拆出成獨立、純 Python、無 Qt 依賴的 service，讓兩個 UI 殼共用同一份 source of truth。

## What Changes

- 新增 `src/domain/services.py` 內 `PotionService` 類別（或新檔 `src/domain/potion_service.py` —— 由 design 階段決定），負責：
  - 單列成本計算（藥水單價 × 數量）
  - 分區小計（HP / MP / 補給 三區）
  - 全局總計（總費用、淨收益、時薪、狩獵時間 mode 換算）
  - autosave 讀/寫/清除
  - 儲存紀錄序列化 / 反序列化
- 新增 `PotionState` 資料形狀（TypedDict 或 dataclass），明確列出每個欄位（rows、meso、exp、time mode、hunt seconds 等）
- 重構 `src/ui/pages/potion_cost_page.py`：
  - 行為不變，視覺不變
  - 計算/persistence 全部委派給 `PotionService`
  - 內部小元件（`_PotionRow`, `_PotionSection`, `_QuantityCalcSection`, `_SummaryPanel`）只負責 UI 與資料蒐集，不再自行算數
- `ConfigManager.save_potion_autosave / load_potion_autosave / delete_potion_autosave` 仍是 IO 入口，但呼叫方統一從 service 出去（不直接從 page 呼叫 config_manager）
- 不變更 V2 page 行為（仍維持 `_toast_pending`），V2 接線在後續另一個 change 處理

## Non-Goals

- **不接 V2 potion 頁**：V2 接線涉及 UI 重組與 Qt 訊號重連，本 change 只負責 service 抽取，V2 接線留給下個 spec
- **不改變使用者可見行為**：V1 頁面所有計算結果、autosave 時機、儲存對話框流程必須完全相同，純技術重構
- **不改 `config.json` / `profiles/*.json` / `potion_autosave.json` 資料格式**：autosave 檔的 schema 不動
- **不抽 UI 子元件到 components.py**：`_PotionRow` 等仍留在 V1 檔案內，僅抽 logic
- **不引入新依賴**：純 Python stdlib + 既有 PySide6 / Pillow

## Capabilities

### New Capabilities

- `potion-cost-service`: 提供 `PotionService` 純邏輯類別，集中處理藥水費用計算（單列、分區、全局）、autosave 讀寫、紀錄序列化，讓多個 UI 實作（V1 / V2）共用同一份計算與持久化邏輯

### Modified Capabilities

(none)

## Impact

- Affected specs: 新增 `potion-cost-service`
- Affected code:
  - 新增：`src/domain/potion_service.py`（或加入既有 `src/domain/services.py`，由 design 決定）
  - 重構：`src/ui/pages/potion_cost_page.py`（行為不變、行數應顯著減少）
  - 不動：`src/infrastructure/config_manager.py`（autosave IO 仍在這裡）
  - 不動：`src/ui_v2/pages/potion_page_v2.py`（本 change 不接 V2）
- 風險：V1 potion 頁是使用者高頻使用功能，重構後須以「逐欄手動驗證」方式確保 autosave 行為、計算數字、儲存/載入流程完全等價

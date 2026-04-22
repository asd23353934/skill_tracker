## 1. 建立 service 骨架

- [ ] 1.1 依設計決策「Service 放在 `src/domain/potion_service.py`（新檔）」建立 `PotionService` 類別，並依「狀態以 TypedDict 表示，計算為純函式 / 純方法」加入 `PotionRowData / PotionSectionData / PotionFormData` 三層 TypedDict
- [ ] 1.2 驗證 `PotionService remains free of Qt dependencies` —— 檔案不可 import PySide6 / src.ui / src.ui_v2，並以純 Python 解譯器跑一次 `from src.domain.potion_service import PotionService` 驗證
- [ ] 1.3 把 V1 `_POTION_DEFAULTS` 整份搬到 `PotionService.DEFAULTS`，實作 `PotionService provides default potion catalog`（hp / mp / combined 三組，name + price 完全一致）

## 2. 計算邏輯

- [ ] 2.1 實作 `calc_row_cost(row)` —— `PotionService computes per-row cost`：`max(0, before-after) * price`，缺 key 視為 0
- [ ] 2.2 實作 `calc_section_subtotal(rows)` —— `PotionService computes section subtotal`：`calc_row_cost` 的總和，空 list 回 0
- [ ] 2.3 實作 `calc_summary(form)` —— `PotionService computes full summary`：產出 `income / expense / net / exp_total / net_10 / exp_10 / net_60 / exp_60` 8 個 key，分母用 `max(1, duration_minutes)`，計算結果 dict key 保持與 V1 完全一致

## 3. 持久化與序列化

- [ ] 3.1 實作 `__init__(self, config_manager)` 與 `save_autosave / load_autosave / clear_autosave` —— `PotionService persists autosave via injected ConfigManager`（純委派 ConfigManager 既有方法，不加節流）
- [ ] 3.2 實作 `serialize(form, *, with_timestamp=True)` 與 `deserialize(data)` —— `PotionService serializes and deserializes records`，欄位與 V1 `get_form_data() / load_form_data()` 字典 schema 完全一致

## 4. 單元驗證

- [ ] 4.1 新增 `tests/domain/test_potion_service.py`（如專案無 tests/，建立最小 pytest 結構或退而用獨立 `verify_potion_service.py` 腳本）
- [ ] 4.2 覆蓋 spec 內所有 example：calc_row_cost 5 種邊界、calc_section_subtotal 空+多筆、calc_summary minutes=0 與 30 分鐘 hunt example
- [ ] 4.3 round-trip 驗證：`deserialize(serialize(form)) == form` 對於有 row + 完整數值的 form 成立

## 5. 重構 V1 page（行為不變）

- [ ] 5.1 `src/ui/pages/potion_cost_page.py` import `PotionService`，依設計決策「`_POTION_DEFAULTS` 改名為 `PotionService.DEFAULTS`」改寫所有 reference，移除原模組常量
- [ ] 5.2 `_PotionRow.get_data` 內 `consumed * price` 改呼 `PotionService.calc_row_cost`
- [ ] 5.3 `_PotionSection.get_subtotal` 改呼 `PotionService.calc_section_subtotal`
- [ ] 5.4 `PotionCostPage._recalc_all` summary dict 構造改呼 `PotionService.calc_summary`，傳入由 page 蒐集的 form dict（計算結果 dict key 保持與 V1 完全一致）
- [ ] 5.5 `_do_autosave / _try_load_autosave / _clear_autosave` 改呼 service 方法（Qt timer 留在 page，service 只負責資料）
- [ ] 5.6 `_on_save / _on_load` 透過 `PotionService.serialize / deserialize` 處理對話框資料，移除 page 內重複的 dict 構造
- [ ] 5.7 確認 `_parse_int` / `_fmt` 留 page —— 不抽到 service，因屬 UI 字串轉換工具

## 6. 手動回歸

- [ ] 6.1 啟動 `python main.py`，開 potion 頁，逐欄輸入 hp / mp / combined 各 1 筆，比對重構前後 summary 數字（income / expense / net / 時薪）一致
- [ ] 6.2 等 500ms+ 觸發 autosave，關閉程式重啟，確認所有欄位（含 timer_elapsed）完整還原
- [ ] 6.3 驗證儲存紀錄 → 載入紀錄 對話框流程不變，存出的 JSON 與重構前 V1 產出 schema 一致（key 順序可不同，但 key 集合 + 值要相同）
- [ ] 6.4 「全部重置」按鈕清空所有欄位 + 刪除 autosave 檔，行為不變
- [ ] 6.5 切換手動分鐘模式 ↔ timer 模式，並驗證 minutes=0 時時薪欄位不崩潰（Service 內 `max(1, minutes)` 防呆）

## 7. 收尾

- [ ] 7.1 跑 `/simplify` 與 `/spectra:audit` 檢視 service + 重構後 page 無 dead code / hacky pattern
- [ ] 7.2 同步 docs/PROJECT.md：在「專案結構」章節 `src/domain/` 下補 `potion_service.py` 與一句說明
- [ ] 7.3 commit 訊息註明：純技術重構、行為不變、為 V2 接線預留入口；本 change 不 bump version

## 1. 重構基底：函數式組裝改為有狀態 class 組合

- [x] 1.1 依設計決策「V2 頁面從函數式組裝改為有狀態 class 組合」，將 `_potion_section()` 改寫為 `_PotionSectionV2(QFrame)` class，內部持有 `self._rows: list[_PotionRowV2]`，並提供 `add_row(data) / remove_row(row) / clear() / get_rows_data()` 方法
- [x] 1.2 將 `_PotionRow` 改寫為 `_PotionRowV2(QFrame)` class，持有 name/price/before/after 四個 QLineEdit 的 self 參照，並提供 `get_data() -> PotionRowData` 回 `{name, price, before, after, consumed, cost}`；每個輸入欄建立時即 `textChanged.connect(parent_page._on_input_changed)`
- [x] 1.3 `_PotionRowV2` 的刪除按鈕 `x` icon 連到 `parent_section.remove_row(self)` → 觸發 `_on_input_changed`；`_PotionSectionV2` 的「新增藥水」按鈕連到 `add_row({})` → 觸發 `_on_input_changed`；「清除全部」按鈕連到 `clear()` → 觸發 `_on_input_changed`，以達成 `V2 potion page supports row add, delete, and section clear`
- [x] 1.4 保留所有視覺 helper（`_input / _icon_btn / _text_btn / _readonly_metric / _section_card / IconBadge`）不動，只改 state 接線部分

## 2. 頁面啟動：load default catalog from PotionService + autosave 還原

- [x] 2.1 `PotionPageV2.__init__` 新增 `self._service = PotionService(app.config_manager)`、`self._timer_elapsed: int = 0`、`self._loading: bool = False`，移除所有 `DEMO_*` 模組常量（`DEMO_HP / DEMO_MP / DEMO_MIX / DEMO_MESO / DEMO_SHOP / DEMO_EXP / DEMO_MIN`）
- [x] 2.2 依需求「V2 potion page starts with empty sections」，`_build()` 建立三個 section 時**不**預填任何 row（不讀 DEFAULTS）；使用者僅能透過每區「新增藥水」按鈕或載入 autosave/紀錄來新增 row
- [x] 2.3 依需求「V2 potion page restores autosave on load」，在 `_build()` 完成 UI 組裝後呼叫 `_try_load_autosave()`：`self._service.load_autosave()` 有回傳則 `self._loading = True` → 逐欄填入 → 還原 `_timer_elapsed` → `self._loading = False` → `_recalc_all()`；無 autosave 時維持三個空 section 的初始畫面

## 3. 資料流匯流：UI → _collect_form() → Service → 回寫 UI

- [x] 3.1 依設計決策「資料流：UI 到 _collect_form() 到 Service 再回寫 UI」，實作 `PotionPageV2._collect_form() -> PotionFormData`，蒐集三個 section 的 rows + mesos/shop/exp 的 before/after QLineEdit 值 + duration QSpinBox 值 + `_timer_elapsed`
- [x] 3.2 依設計決策「輸入事件全走 textChanged / valueChanged 到 _on_input_changed() 單一匯流」，實作 `_on_input_changed(self, *_)`：若 `self._loading` 直接 return；否則 `_recalc_all()` + `_schedule_autosave()`
- [x] 3.3 將 mesos / shop / exp 的所有 `_input(...)` 改為存入 self 屬性（如 `self._mesos_start_input` 等），並在建立時 `textChanged.connect(self._on_input_changed)`；duration QSpinBox 綁 `valueChanged.connect(self._on_input_changed)`

## 4. 摘要即時重算：recomputes summary on every input change

- [x] 4.1 依設計決策「右側本次練功摘要六列標籤綁 self._summary_labels: dict[str, QLabel]」，改寫 `_summary_card()` 為頁面的 method（取用 `self`），建立時把 income/expense/net/exp_total/net_10/net_60/exp_10/exp_60 八個 `QLabel` 存進 `self._summary_labels`
- [x] 4.2 依需求「V2 potion page recomputes summary on every input change」，實作 `_recalc_all()`：呼叫 `PotionService.calc_summary(self._collect_form())`，逐 key `self._summary_labels[k].setText(self._fmt(v))`（保留正負號格式：收入 +、支出 -、淨值 ±）
- [x] 4.3 同步更新各 section header 的「合計」顯示 → 呼叫 `PotionService.calc_section_subtotal(...)` 得到每區小計，更新對應 `section._total_label`

## 5. 自動保存：writes autosave with 500ms debounce

- [x] 5.1 依需求「V2 potion page writes autosave with 500ms debounce」，新增 `self._autosave_timer = QTimer(self)`、`self._autosave_timer.setSingleShot(True)`、`self._autosave_timer.setInterval(500)`、`self._autosave_timer.timeout.connect(self._do_autosave)`
- [x] 5.2 實作 `_schedule_autosave(self)`：若 `self._loading` 直接 return；否則 `self._autosave_timer.start()`（re-start 達成 debounce）
- [x] 5.3 實作 `_do_autosave(self)`：`self._service.save_autosave(self._collect_form(), timer_elapsed=self._timer_elapsed)`

## 6. 紀錄對話框：save and load record dialogs

- [x] 6.1 依設計決策「V2 紀錄對話框新建，不沿用 V1」，新增 `src/ui_v2/dialogs/potion_save_dialog_v2.py` 定義 `PotionSaveDialogV2(BaseDialogV2)`：包含「記錄名稱」QLineEdit + 確認/取消按鈕；`accept` 時回 `self.name`
- [x] 6.2 新增 `src/ui_v2/dialogs/potion_load_dialog_v2.py` 定義 `PotionLoadDialogV2(BaseDialogV2)`：從 `app.config_manager.list_potion_saves()` 取清單顯示為 QListWidget，選取後回 `self.selected_name`（rename/delete 不做）
- [x] 6.3 在 `src/ui_v2/dialogs/__init__.py` 匯出兩個新對話框
- [x] 6.4 依需求「V2 potion page provides save and load record dialogs」，`PotionPageV2` 新增 `_on_save()`：開 `PotionSaveDialogV2` → 確認後 `serialized = PotionService.serialize(self._collect_form())` → `app.config_manager.save_potion_record(dlg.name, serialized)`
- [x] 6.5 `PotionPageV2` 新增 `_on_load()`：開 `PotionLoadDialogV2` → 確認後 `record = app.config_manager.load_potion_record(dlg.selected_name)` → `restored = PotionService.deserialize(record)` → `self._loading = True` → 逐欄填入 → `self._loading = False` → `_recalc_all()` + `_schedule_autosave()`

## 7. 時間來源：manual and timer duration modes

- [x] 7.1 依設計決策「計時器模式：QTimer 1s tick，累計存 self._timer_elapsed（秒）」，新增 `self._tick_timer = QTimer(self)`、interval 1000ms、`timeout.connect(self._on_tick)`；新增 `self._mode: str = "manual"` 記錄當前模式
- [x] 7.2 實作 `_on_mode_toggle(mode)`：切到 `"manual"` 時 `self._tick_timer.stop()`、duration QSpinBox 可編輯、隱藏 start/reset 按鈕；切到 `"timer"` 時 QSpinBox 設 readOnly、顯示 start/reset 按鈕，但**不自動啟動** tick timer；切換本身不重置 `_timer_elapsed`
- [x] 7.3 實作 `_on_tick()`：`self._timer_elapsed += 1` → 更新 timer 顯示 Label（HH:MM:SS 格式 helper 複製自 V1 `_fmt_elapsed`）→ 若 `_timer_elapsed % 60 == 0`：`duration_spin.setValue(max(1, self._timer_elapsed // 60))` → 觸發 `_on_input_changed`
- [x] 7.4 依需求「V2 potion page supports manual and timer duration modes」，把頂部「手動 / 計時器」兩個 chip 按鈕的 clicked 連到 `_on_mode_toggle(...)`，並以視覺 styling 表示當前模式
- [x] 7.5 在時間列加入 `self._timer_start_btn`（開始/停止 toggle）與 `self._timer_reset_btn`：start 按鈕切換 `self._tick_timer` 啟停並同步按鈕文字圖示（開始/停止 ↔ play/square）；reset 按鈕停止 tick、`_timer_elapsed = 0`、display 回 00:00:00、`duration_spin` 歸 1；兩按鈕僅在 timer 模式顯示

## 8. 清除與全部重置：clear and reset actions purge state

- [x] 8.1 依需求「V2 potion page clear and reset actions purge state」，實作 `_on_clear()`：QMessageBox 確認 → `_clear_all_inputs()`（所有 row 移除、mesos/shop/exp 歸零、duration 歸 1）→ `_recalc_all()` → `_schedule_autosave()`；**不**呼叫 `clear_autosave`
- [x] 8.2 實作 `_on_reset_all()`：QMessageBox 確認 → `_clear_all_inputs()` → `self._timer_elapsed = 0` → `self._service.clear_autosave()` → `_recalc_all()`
- [x] 8.3 將頂部工具列四個按鈕（清除 / 全部重置 / 載入紀錄 / 儲存）的 `_toast_pending` 連接全部移除，改連到 `_on_clear / _on_reset_all / _on_load / _on_save`；移除 `_toast_pending` method

## 9. 並存策略與風險處理：V1/V2 共用 autosave

- [x] 9.1 依設計決策「V1/V2 併用 potion_autosave.json 採最後寫入者勝」，不加檔案鎖、不加修改時間檢查；只在 `_try_load_autosave` 完成時以 toast 提示「已還原上次編輯內容」（複用 V1 文案），維持 V1/V2 一致體驗
- [x] 9.2 確認 `src/ui_v2/pages/potion_page_v2.py` 頂部 docstring 與實作一致，刪除「尚未接線」相關描述

## 10. 驗證

- [x] 10.1 新增 `verify_potion_page_v2.py`：instantiate 一個 dummy `PotionPageV2`（以 QApplication 在無 show 情境建立），驗證 `_collect_form()` 產出 dict 有 `hp_potions / mp_potions / combined_potions` 三個 list + `duration_minutes / mesos_start / mesos_end / shop_before / shop_after / exp_start / exp_end` 七個欄位
- [x] 10.2 驗證 `verify_potion_page_v2.py` 內 mock `PotionService.load_autosave` 回固定 dict，確認頁面建立後欄位正確還原；並檢查 V1 autosave 檔可被 V2 `_try_load_autosave` 成功讀取（反向相容）
- [ ] 10.3 手動回歸：`python main.py --v2` 開 V2 potion 頁 → 輸入 hp/mp/combined 各 1 筆，比對摘要數字與 V1 一致；等 500ms+ 觸發 autosave，重啟後欄位完整還原；切換手動 ↔ 計時器，60 秒後分鐘欄位自動 +1
- [ ] 10.4 手動回歸：測試儲存紀錄 → 載入紀錄流程；V1 存的紀錄要能在 V2 載入（反之亦然）
- [ ] 10.5 手動回歸：「清除」後 autosave 仍在、「全部重置」後 autosave 消失

## 11. 收尾

- [x] 11.1 跑 `/simplify` 與 `/spectra:audit` 檢視 V2 page 與新對話框無 dead code / hacky pattern
- [x] 11.2 docs/PROJECT.md 在 V2 頁面結構區塊補註 potion_page_v2「已接線（透過 PotionService）」、新增 `potion_save_dialog_v2.py / potion_load_dialog_v2.py`
- [x] 11.3 commit 訊息註明：V2 potion 頁接線完成、共用 V1 autosave、不 bump version

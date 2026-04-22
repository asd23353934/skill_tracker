## Context

V1 `src/ui/pages/potion_cost_page.py` 是 1582 行 monolith。該檔內含：

- 4 個內部 widget 類別（`_PotionRow`, `_PotionSection`, `_QuantityCalcSection`, `_SummaryPanel`）
- 主類別 `PotionCostPage(QWidget)`，建構 UI + 接所有 callback + 算數 + autosave + timer + 儲存/載入對話框
- 模組常量 `_POTION_DEFAULTS`（hp / mp / combined 三組預設藥水資料）
- IO 呼叫：`app.config_manager.{save,load,delete}_potion_autosave(...)`

V2 `src/ui_v2/pages/potion_page_v2.py` 已用新視覺殼重寫，但因所有計算/serialize 邏輯被 widget 牢牢綁住，目前只能 toast「尚未接 V2」。

`src/domain/services.py` 已存在（內有 `SkillService`），是放置 `PotionService` 的合理位置；但本檔已逾 200 行且 SkillService 與藥水費用屬不同領域，故新檔 `src/domain/potion_service.py` 較清晰。

## Goals / Non-Goals

**Goals:**

- 將 V1 potion 頁的純邏輯（計算 / autosave 資料整形 / serialize / 預設資料）抽到無 Qt 依賴的 `PotionService`
- V1 行為、視覺、autosave 檔格式、儲存紀錄檔格式完全不變
- V2 後續接線時，能直接 `from src.domain.potion_service import PotionService` 重用同一份邏輯
- `_POTION_DEFAULTS` 成為 service 的公開常量（V2 也要顯示同一份預設藥水）

**Non-Goals:**

- 不接 V2 page（另一個 change 處理）
- 不抽 UI 子元件（`_PotionRow` 等仍留 V1 檔內）
- 不重構 `ConfigManager` 的 autosave IO 介面
- 不改 autosave / 儲存紀錄的 JSON schema（向下相容既有使用者檔案）
- 不引入 dataclass / pydantic（state 用 TypedDict + dict）

## Decisions

### Service 放在 `src/domain/potion_service.py`（新檔）

`src/domain/services.py` 已包含 SkillService 與其他 skill 相關邏輯，混入 potion 會稀釋焦點。新檔讓兩個領域獨立演進。

**Alternatives considered:**

- 加入既有 `services.py`：拒絕，混合領域、未來 service 增加會更亂
- 放 `src/ui/` 旁邊：拒絕，service 必須無 Qt 依賴、可被 V2 重用

### 狀態以 TypedDict 表示，計算為純函式 / 純方法

`PotionService` 提供 `PotionRowData`, `PotionSectionData`, `PotionFormData` 三層 TypedDict，分別對應 V1 既有 `_PotionRow.get_data()`, `_PotionSection.get_data()`, `PotionCostPage.get_form_data()` 的字典形狀。**不引入 dataclass** —— 要保持 dict 進 dict 出，autosave 直接 `json.dump`，向下相容無痛。

API 形狀：

```python
class PotionService:
    DEFAULTS: dict[str, list[dict]]  # 公開常量

    @staticmethod
    def calc_row_cost(row: PotionRowData) -> int: ...
    @staticmethod
    def calc_section_subtotal(section: list[PotionRowData]) -> int: ...
    @staticmethod
    def calc_summary(form: PotionFormData) -> dict: ...
    # 含 income / expense / net / exp / 時薪換算

    def __init__(self, config_manager): ...
    def save_autosave(self, form: PotionFormData) -> None: ...
    def load_autosave(self) -> PotionFormData | None: ...
    def clear_autosave(self) -> None: ...

    @staticmethod
    def serialize(form: PotionFormData, *, with_timestamp: bool = True) -> dict: ...
    @staticmethod
    def deserialize(data: dict) -> PotionFormData: ...
```

**Alternatives considered:**

- dataclass：型別更強，但要寫 `to_dict` / `from_dict`，且和現有 dict-based JSON schema 對齊較囉嗦，不值得
- 純 module-level functions（無 class）：拒絕，autosave IO 需要 config_manager 注入，class 裝載依賴較自然

### Qt timer 留在 page，service 只負責資料

V1 的 `_autosave_timer`（QTimer，500ms throttle）+ `_loading` flag 是 Qt 與 UI 行為，留在 page。service 純粹被呼叫一次寫一次，不負責節流 / 不負責 dirty tracking。

**Alternatives considered:**

- service 內含 throttle 計時：拒絕，service 不能依賴 Qt，且 V1/V2 page 行為可能不同（V2 可能用不同節流策略），讓 page 自己決定何時呼叫

### 計算結果 dict key 保持與 V1 完全一致

`calc_summary` 回傳的 dict key 必須是 `income / expense / net / exp_total / net_10 / exp_10 / net_60 / exp_60`，跟 V1 `_recalc_all` 寫進 `_summary_panel.refresh()` 的 dict 字字相符。這樣重構時 V1 端只是把那串計算搬到 service call，呼叫端不變。

### `_POTION_DEFAULTS` 改名為 `PotionService.DEFAULTS`

模組常量遷到 service class 屬性，V2 import service 即可拿到同一份預設清單，避免兩邊複製。V1 原 `_POTION_DEFAULTS` 變成 `PotionService.DEFAULTS` 的別名（過渡期 1 commit），確認無 reference 後刪除。

### `_parse_int` / `_fmt` 留 page

這兩個是 UI-string ↔ int 轉換的小工具，本質上服務 QLineEdit。留在 page 不抽，避免 service 沾到 UI 字串格式。

## Risks / Trade-offs

- **[Risk] 重構後 autosave 行為微異** → Mitigation：tasks.md 明列「逐欄手動驗證」步驟（含開新 profile / 改值 / 等 500ms / 重啟 / 確認還原），不能只靠程式碼比對
- **[Risk] `calc_summary` 的時薪換算（minutes 防 0）邏輯重現錯誤** → Mitigation：把 V1 既有的 `max(1, minutes)` 邏輯原樣搬，並在 service 加單元測試（`test_potion_service.py`，至少 5 個 case：minutes=0/1/60、空 row、混合區）
- **[Risk] `_loading` flag 與 service 互動失誤導致載入時誤觸 autosave** → Mitigation：`_loading` 仍由 page 持有；service 不知道 loading 概念，page 在載入完成前不呼叫 `service.save_autosave`
- **[Trade-off] TypedDict 比 dataclass 弱型別** → 接受：JSON 進出無痛、向下相容簡單，loss of compile-time check 用單元測試補

## Migration Plan

1. 新增 `src/domain/potion_service.py`（含 service + DEFAULTS + TypedDicts），純粹新增不影響任何既有檔
2. 新增 `tests/domain/test_potion_service.py`（若專案無 tests/，先建立簡單 pytest 結構或用獨立 `verify_potion_service.py` 腳本）
3. 重構 `potion_cost_page.py`：
   - import service
   - 替換 `_POTION_DEFAULTS` → `PotionService.DEFAULTS`
   - `_PotionRow.get_data` 內的 `consumed * price` 改呼 `PotionService.calc_row_cost`
   - `_PotionSection.get_subtotal` 改呼 `PotionService.calc_section_subtotal`
   - `PotionCostPage._recalc_all` 中 summary dict 構造改呼 `PotionService.calc_summary`
   - `_do_autosave / _try_load_autosave / _clear_autosave` 改呼 `service.save_autosave / load_autosave / clear_autosave`
   - `_on_save / _on_load` 透過 `PotionService.serialize / deserialize` 處理對話框資料
4. 手動回歸（清單列在 tasks.md）
5. Commit

**Rollback:** 重構在單一 commit；revert 即還原 V1 行為。`potion_autosave.json` schema 不變，無資料層 rollback 顧慮。

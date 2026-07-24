## Context

`version.py` 的 `CHANGELOG` 是一個長期手動維護的 triple-quoted 字串，`get_changelog()` 原樣回傳整包文字，`get_version()` 回傳 `VERSION`。目前完全沒有 UI 讀取這兩個函數。

側邊欄（`src/ui_v2/sidebar_v2.py` 第 99-113 行）底部已經有一個顯示 `v{VERSION}` 的靜態 `QLabel`（`T.TEXT_MUTED`、9px），是使用者已經會注意到、且天然適合掛點擊事件的位置。

對話框一律繼承 `src/ui_v2/dialogs/base_dialog_v2.py::BaseDialogV2`：`body_layout()` 回傳一個已經以 `stretch=1` 加進外層卡片的 `QVBoxLayout`，本身不含捲動容器，需要捲動清單時要自己在 `body_layout()` 裡塞一個 `QScrollArea`（`command_page_v2.py::_build` 已有現成寫法可參照：`QScrollArea` + `setWidgetResizable(True)` + 內部 `QVBoxLayout` 一路 `addWidget` 卡片）。

`CHANGELOG` 字串裡的版本區塊格式並不一致：多數新版本是單層 `- ` bullet list，但部分較早版本（如 v4.10.0）用 emoji 分類標題（如 `🎯 新增技能`）搭配底下縮排兩格的子項目。這個差異是既有資料的既定事實（changelog 是人工撰寫的歷史紀錄，不會回頭改格式），因此解析策略必須對兩種格式都不出錯，而不是假設單一格式。

## Goals / Non-Goals

**Goals:**

- 側邊欄版本號可點擊，開啟顯示完整版本歷史的唯讀對話框。
- 依 `vX.Y.Z (YYYY-MM-DD)` 標頭把 `get_changelog()` 的原始字串切成一筆一筆版本區塊，最新在最上面，每個版本一張卡片（標頭 + 內容），可捲動瀏覽全部歷史。
- 對「非預期格式」容錯：切不出任何版本標頭時，整段字串當一個區塊呈現；不丟例外、不顯示空白對話框。

**Non-Goals:**

- 不解析版本區塊內部的 bullet 階層／emoji 分類，內容原樣（含原始換行與縮排）呈現為一段文字。
- 不新增 changelog 撰寫/編輯介面。
- 不串接 GitHub Release 的 `release_notes`（`updater.py::check_for_updates()` 已抓到但這次不使用）。
- 不改變 `version.py` 的 `CHANGELOG` 字串內容、格式慣例，或 `get_changelog()` 的回傳型別（維持回傳原始字串，解析邏輯放在新對話框那一側，不動 `version.py`）。

## Decisions

### 版本區塊解析：正規表示式切段落，不做階層解析

新增一個模組層級函數（放在 `changelog_dialog_v2.py` 內，不動 `version.py`）：

```python
_VERSION_HEADER_RE = re.compile(
    r"^v(?P<version>\S+)\s*\((?P<date>[^)]*)\)\s*$", re.MULTILINE
)
```

解析步驟：
1. 對 `get_changelog()` 回傳的原始字串跑 `_VERSION_HEADER_RE.finditer(text)`，取得每個標頭的 `version` / `date` 與其在字串中的位置。
2. 每個區塊的內容 = 從「該標頭下一行的分隔線（`---...`）之後」到「下一個標頭開始之前」的原始文字，`strip()` 頭尾空白後保留內部原始換行與縮排。
3. 標頭底下緊接的分隔線（`-------------------`）本身不算內容，用一個簡單規則跳過：內容區塊擷取時，若第一行是純 `-` 字元組成則丟棄該行。
4. 若一個版本都切不出來（`finditer` 無結果），整段 `get_changelog()` 字串當作單一區塊，標頭顯示為目前 `version.get_version()`（因為至少當前版本一定存在），內容就是整段原始文字。
5. 解析函數獨立成 `_parse_changelog(text: str) -> list[tuple[str, str, str]]`（回傳 `(version, date, body)` 的 list），方便之後若要單元測試可以直接測（本次沒有新增測試檔案，因為 `tests/` 目錄目前只涵蓋 domain/infrastructure 純邏輯層，UI 對話框沒有既有測試慣例可循，這次不引入新的測試模式）。

### 對話框版面：QScrollArea + 逐版本卡片

比照 `command_page_v2.py::_build` 的捲動清單寫法：`body_layout()` 裡放一個 `QScrollArea`（`setWidgetResizable(True)`），內部 `QWidget` + `QVBoxLayout`，逐一 `addWidget` 每個版本的卡片。

每張卡片：`QFrame`（`background: T.BG_ELEVATED`、`border: 1px solid T.BORDER`、`border-radius: T.R_SM`，與 `command_page_v2.py` 的 `_build_simple_card` 同一視覺語言），內部 `QVBoxLayout`：
- 標頭列：`T.make_label(f"v{version}", T.FONT_CARD_TITLE, T.ORANGE)` + 一個顯示日期的次要 `QLabel`（`T.TEXT_DIM`，小字），同一行並排。
- 內容：`QLabel(body)`，`setTextFormat(Qt.TextFormat.PlainText)`、`setWordWrap(True)`，字級比照現有卡片說明文字（11-12px，`T.TEXT_DIM`）。

對話框整體：`ChangelogDialogV2(BaseDialogV2)`，`title="更新日記"`，尺寸比照其他中型對話框（`width=480, height=560`，與 `ProfileManagerDialogV2` 同量級但略高，因為內容是可捲動清單）。不需要 footer 按鈕（純唯讀瀏覽），`footer_layout()` 保持預設（僅 `addStretch()`，沒有內容）。

### 側邊欄版本號可點擊

`sidebar_v2.py` 現有版本 `QLabel` 改造：
- `setCursor(Qt.CursorShape.PointingHandCursor)`
- `setToolTip("點擊查看更新日記")`
- 由於 `QLabel` 預設不發 `clicked` 訊號，改用 `mousePressEvent` override（比照 `base_dialog_v2.py::_CloseBtn` 或直接包一層極簡的可點擊 `QLabel` 子類別，命名 `_ClickableLabel`，`clicked = Signal()`，`mousePressEvent` 裡 `if e.button() == Qt.MouseButton.LeftButton: self.clicked.emit()`）取代原本的純 `QLabel`。
- 點擊時建立 `ChangelogDialogV2(self, ...)` 並 `.exec()`（modal，比照 `ProfileManagerDialogV2` 的開啟方式，避免使用者切分頁時對話框状態混亂）。
- `ChangelogDialogV2` 不需要 `app` 參數操作應用狀態（純顯示 `version.py` 的資料），建構子簽名可以只吃 `parent`，不必依賴 `app_ctx`。

## Risks / Trade-offs

- [風險] `CHANGELOG` 字串未來若新增第三種格式（例如標頭後面直接接內容、沒有分隔線），解析可能誤判內容範圍 → 緩解：解析函數對「找不到分隔線」的情況直接把分隔線那一步跳過（不強制要求一定要有分隔線才能算合法區塊），對格式異動有一定容忍度；真的解析失敗時的 fallback（整段字串當一塊）保證不會顯示空白或當機。
- [風險] `get_changelog()` 目前每次呼叫都回傳同一份 module-level 字串（無 I/O、無外部依賴），解析成本是一次性字串處理（regex + 字串切片），版本數量目前約 30 筆、字串長度數千字元，效能可忽略；若未來版本數量成長到數百筆，仍是一次性、對話框開啟時才執行的操作，不在任何 hot path 上，不需要額外快取機制。
- [風險] 新增 `_ClickableLabel` 類別與現有 `InputChip`（`skill_card_v2.py`）等既有可點擊元件在職責上有一點重疊 → 緩解：`InputChip` 是「值 + 重置雙按鈕」的複合元件，用在這裡明顯過度設計；`_ClickableLabel` 只是單一 `QLabel` 加 `clicked` signal，範疇更小、更貼近側邊欄版本號這種單一靜態文字的需求，不適合共用既有元件。

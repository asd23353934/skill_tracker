## 1. 版本區塊解析（版本區塊解析：正規表示式切段落，不做階層解析）

- [x] 1.1 在新檔 `src/ui_v2/dialogs/changelog_dialog_v2.py` 實作 `_VERSION_HEADER_RE = re.compile(r"^v(?P<version>\S+)\s*\((?P<date>[^)]*)\)\s*$", re.MULTILINE)` 與函數 `_parse_changelog(text: str) -> list[tuple[str, str, str]]`：用 `_VERSION_HEADER_RE.finditer(text)` 取得每個標頭位置，切出每個版本的 body（下一個標頭開始之前的原始文字，`strip()` 頭尾空白、保留內部換行縮排；若 body 第一行是純 `-` 字元組成的分隔線則丟棄該行），實作 Changelog dialog parses the changelog into per-version blocks 需求
- [x] 1.2 `_parse_changelog` 對「找不到任何標頭」的情況 fallback：回傳單一 `(version.get_version(), "", text.strip())` 區塊，不拋例外
- [x] 1.3 手動驗證 `_parse_changelog` 對目前 `version.py` 真實的 `CHANGELOG` 字串（混合單層 bullet 與 emoji 分類縮排兩種既有格式）能切出正確筆數的版本區塊，且每筆的 version/date 都正確

## 2. ChangelogDialogV2 對話框（對話框版面：QScrollArea + 逐版本卡片）

- [x] 2.1 在 `src/ui_v2/dialogs/changelog_dialog_v2.py` 新增 `class ChangelogDialogV2(BaseDialogV2)`，建構子簽名 `__init__(self, parent=None)`（不需要 `app_ctx`），呼叫 `super().__init__(parent, title="更新日記", width=480, height=560)`
- [x] 2.2 在 `body_layout()` 放入 `QScrollArea`（`setWidgetResizable(True)`，比照 `command_page_v2.py::_build` 的捲動清單寫法），內部 `QWidget` + `QVBoxLayout`，對 `_parse_changelog(version.get_changelog())` 的每個區塊呼叫 `_build_version_card(version, date, body)` 並 `addWidget`，實作 Changelog dialog renders version blocks as a scrollable list 需求
- [x] 2.3 實作 `_build_version_card(version, date, body) -> QFrame`：`QFrame`（`background: T.BG_ELEVATED`、`border: 1px solid T.BORDER`、`border-radius: T.R_SM`，比照 `command_page_v2.py::_build_simple_card` 視覺語言）內含標頭列（`T.make_label(f"v{version}", T.FONT_CARD_TITLE, T.ORANGE)` + 日期 `QLabel`，`T.TEXT_DIM` 小字，同一行）與內容 `QLabel(body)`（`setTextFormat(Qt.TextFormat.PlainText)`、`setWordWrap(True)`、`T.TEXT_DIM` 11-12px）

## 3. 側邊欄版本號可點擊（側邊欄版本號可點擊）

- [x] 3.1 在 `src/ui_v2/sidebar_v2.py` 新增 `_ClickableLabel(QLabel)` 子類別：`clicked = Signal()`，override `mousePressEvent`，`if e.button() == Qt.MouseButton.LeftButton: self.clicked.emit()`
- [x] 3.2 把第 99-113 行原本顯示 `v{VERSION}` 的純 `QLabel` 換成 `_ClickableLabel`，加上 `setCursor(Qt.CursorShape.PointingHandCursor)` 與 `setToolTip("點擊查看更新日記")`，實作 Sidebar version label opens the changelog dialog 需求
- [x] 3.3 把 `_ClickableLabel.clicked` 接到一個開啟對話框的 slot：`from src.ui_v2.dialogs.changelog_dialog_v2 import ChangelogDialogV2` 後 `ChangelogDialogV2(self).exec()`（modal，比照 `ProfileManagerDialogV2` 的開啟方式）

## 4. 驗證

- [x] 4.1 啟動應用程式，點擊側邊欄底部版本號，確認彈出「更新日記」對話框、游標 hover 時變手指
- [x] 4.2 確認對話框內版本區塊依新到舊排列（最上面是目前版本），捲動可看到更早的版本（含 v4.10.0 那種 emoji 分類縮排格式的版本，內容需完整顯示不缺行）
- [x] 4.3 執行 `python -m pytest tests/ -v` 確認既有測試依然全數通過

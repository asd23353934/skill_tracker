## Why

`version.py` 已經有完整的 `CHANGELOG` 字串與 `get_changelog()`，但目前沒有任何 UI 讀取它——使用者只能開原始碼或看 GitHub Release 頁面才知道每個版本改了什麼。V2 UI 側邊欄底部已經有一個顯示目前版本號（`v{VERSION}`）的 `QLabel`（`src/ui_v2/sidebar_v2.py`），但它只是純文字、沒有任何互動；這是一個現成、使用者已經會去看的位置，適合掛上點擊事件開啟版本歷史。

## What Changes

- `src/ui_v2/sidebar_v2.py` 底部的版本號 `QLabel` 改為可點擊（游標變手指、hover 有提示），點擊後開啟新對話框顯示完整更新日記。
- 新增 `ChangelogDialogV2`（繼承 `BaseDialogV2`，比照 `profile_manager_dialog_v2.py` / `update_dialog_v2.py` 的建構方式），把 `version.get_changelog()` 的原始字串解析成一筆一筆版本區塊（依 `vX.Y.Z (YYYY-MM-DD)` 標頭切分），最新版本在最上面，用可捲動清單呈現：每個版本一個小卡片，標頭顯示版本號＋日期（比照現有卡片標題樣式），下方顯示該版本的完整內容文字（保留原始換行/縮排，不強行解析 bullet 階層——現有 changelog 歷史條目格式不一致，有的是單層 `- ` 清單，有的是 emoji 分類標題底下再縮排子項目，統一解析成 bullet 樹風險高、對使用者體感也沒有明顯差異）。
- 解析失敗或格式不符時的容錯：找不到任何 `vX.Y.Z (` 標頭時，整段字串當作單一區塊呈現，不當機、不顯示空白對話框。

## Non-Goals

- 不新增 changelog 撰寫/編輯功能，`CHANGELOG` 字串仍由開發者手動維護在 `version.py`。
- 不去抓 GitHub Release 的 `release_notes`（`src/infrastructure/updater.py` 的 `check_for_updates()` 已經有抓但目前沒人用）；這次只做本地 `version.py` 的 `CHANGELOG` 顯示，遠端 release notes 顯示是不同範疇，之後有需要再另開 change。
- 不做 bullet 階層/emoji 分類的結構化解析，只依版本標頭切段落，段落內文字原樣呈現。
- 不改變 `version.py` 既有的 `CHANGELOG` 字串內容或格式慣例。

## Capabilities

### New Capabilities

- `changelog-viewer`: 側邊欄版本號可點擊，開啟顯示完整版本歷史的對話框，資料來源為 `version.get_changelog()`。

### Modified Capabilities

(none)

## Impact

- Affected specs: changelog-viewer
- Affected code:
  - New:
    - src/ui_v2/dialogs/changelog_dialog_v2.py
  - Modified:
    - src/ui_v2/sidebar_v2.py

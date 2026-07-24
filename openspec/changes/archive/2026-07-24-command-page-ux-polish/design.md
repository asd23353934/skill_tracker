## Context

`command_page_v2.py` 是較早期完成的頁面，分組標題目前只是一個 `QLabel`（`_build_group_header`），指令卡片（`_build_simple_card` / `_NeedsNameCard`）各自手刻 `QFrame` + 手動 QSS 字串。相較之下，`skill_page_v2.py` 的 `_CATEGORY_DEFS`（`("player", "玩家技能", "swords", T.BLUE)` 這種 `(key, title, glyph, accent)` 四元組）與 `skill_column_v2.py` 的欄位標頭（`IconBadge(glyph, accent, 28)` + 標題 + `StatusChip(f"{hk_total}/{total}", accent)`）已經是專案內成熟的「分組標頭」視覺語言，`src/ui_v2/components.py` 也已提供 `IconBadge` / `StatusChip` 共用元件。

指令頁的卡片本體（`_build_simple_card` / `_NeedsNameCard`）用色與圓角（`T.BG_ELEVATED` + `T.R_SM`）其實已經與 `skill_card_v2.py` 的卡片一致，真正與其他頁面拉開差距的地方是「分組標頭沒有 icon / 沒有數量提示」，讀起來比較單調。

另外兩個需求（needs_name 提示文字依指令區分、快捷鍵限定攔截時的使用者回饋）是行為層修正，不涉及版面。

實作分組標頭後，曾額外嘗試把 `_NeedsNameCard` 改成 `setFixedWidth(680)` + `AlignLeft` 來解決「太寬、名稱欄位太小」的回饋，但這個調整沒有記錄進本文件、也違反了下方原本就存在的 Non-Goal（「needs_name 整列規則維持不變」），實際效果是 needs_name 卡片與同分組內滿版寬度的 no-arg 兩欄卡片（`_build_pair_row`）寬度對不齊，使用者回饋「整體看沒有很整齊與滿版」。這次一併撤銷該調整，回到滿版寬度，只保留其中「放大輸入框高度／字級」這個確實改善可用性的部分。

另外使用者發現：把「複製指令」的快捷鍵和「技能倒數」的快捷鍵設成同一個按鍵時，只有技能會觸發，指令完全不會被檢查。追查 `hotkey_manager.py` 的 `_on_key_press` 後發現這是既有的 early-return 結構：技能命中就 `return`，怪物命中也 `return`，導致「技能→怪物→指令」的檢查鏈只要前面命中就完全跳過後面。這其實跟 `hotkey-binding` spec 裡「Hotkey namespaces are isolated」需求的 scenario（「Same key bound to skill and monster: pressing F1 triggers the skill first, then the monster」，兩者都應觸發）互相矛盾 —— 是既有的規格與程式碼不一致，這次一併修正，並把指令命名空間也納入「共同觸發」的規則裡。

## Goals / Non-Goals

**Goals:**

- 指令頁分組標頭改用 `IconBadge` + `StatusChip`，比照 `skill_column_v2.py` 的欄位標頭語言，讓使用者一眼分辨「常用 / 交易 / 聊天 / 隊伍 / 封鎖 / 其他」六個分組。
- needs_name 卡片的名稱輸入 placeholder 依指令而定，避免暗示所有 needs_name 指令都要打 `#代碼`。
- 快捷鍵限定攔截觸發時，透過既有 `app.toast`（`ToastManagerV2.show`）給出明確提示，取代靜默 `return`。
- 設定對話框「快捷鍵限定」列補上一行用途說明文字。
- needs_name 卡片寬度回到與 no-arg 卡片一致的滿版寬度，同時保留放大後的輸入框尺寸（高度 32px、字級 13px）。
- 快捷鍵三個命名空間（技能／怪物／指令）改為共同觸發：同一按鍵命中多個命名空間時全部觸發，`_app_filter_blocks()` 檢查與攔截 toast 只對整次按鍵評估一次。

**Non-Goals:**

- 不新增或移除 `_GROUPS` / `_Command` 資料結構欄位，不改變指令目錄內容。
- 不把卡片本體（`_build_simple_card` / `_NeedsNameCard`）重寫成 `src/ui_v2/components.py` 的 `Card` 元件 — 兩者的非對稱 margin（水平 `T.S_MD`、垂直 `T.S_SM`/`T.S_XS`）與 `Card` 目前只支援單一 padding 值的建構子不相容，且現有卡片配色／圓角（`BG_ELEVATED` + `R_SM`）已經與 `skill_card_v2.py` 一致，重寫沒有實質視覺收益，純屬變動風險。
- 不改變快捷鍵限定的比對邏輯（`_app_filter_blocks` 的 exe 比對方式不變），只在攔截發生時補上回饋。
- 不變動指令頁的分組順序或欄位配置邏輯（`_build_group_body` 的 no-arg 兩欄配對 / needs_name 整列規則維持不變 —— needs_name 卡片維持滿版寬度）。
- 不改變「同一命名空間內」的衝突清除規則（技能綁同一鍵會清掉另一個技能的舊綁定、怪物同理）；只改變「不同命名空間之間」從互斥改為共同觸發。

## Decisions

### 分組標頭改用 IconBadge + StatusChip

`_build_group_header(title, first)` 目前回傳單一 `QLabel`。改為回傳一個水平列：`IconBadge(glyph, accent, 22)` + 標題 `QLabel`（沿用 `T.FONT_LABEL`）+ `StatusChip(str(count), accent)`（該分組指令數量），其餘排版（`first` 時上緣不留白、非首組留 `T.S_SM` 上緣）不變。

`_GROUPS` 的 6 個分組對應的 `(glyph, accent)`（皆取自 `src/ui_v2/icons/` 現有檔案與 `V2Theme` 現有色票，不新增圖示資源）：

| 分組 | glyph | accent |
| --- | --- | --- |
| 常用 | `star` | `T.ORANGE` |
| 交易 / 私訊 | `coins` | `T.BLUE` |
| 聊天頻道 | `globe` | `T.CYAN` |
| 隊伍 / 公會 | `user` | `T.GREEN` |
| 封鎖 | `eye-off` | `T.RED` |
| 其他 | `settings` | `T.PURPLE` |

這個對照表以獨立字典（例如 `_GROUP_ICON: dict[str, tuple[str, str]]`，key 為分組標題）維護，不需要改動 `_GROUPS` 本身的 `(title, [_Command])` 結構，`_build_group_header` 依標題查表取得 glyph/accent。

### needs_name placeholder 依指令區分

`_Command` 增加一個欄位（例如 `name_hint: str`，或直接讓 `_NAME_PLACEHOLDER` 邏輯依 `cmd.key == "whisper"` 特判）。只有 `/密語` 的名稱輸入框顯示含 `#代碼` 字樣的提示（沿用目前文字「輸入玩家名稱（含 #代碼）後按複製」），其餘 needs_name 指令改用不含 `#代碼` 字樣的提示（例如「輸入玩家名稱後按複製」）。`_NeedsNameCard.__init__` 建立 `self._input` 時依 `cmd` 決定套用哪一句。

傾向直接在 `_Command` 加欄位而非用 key 特判字串：`_Command` 已是資料驅動設計（docstring 明言「增刪指令只動 _GROUPS」），新增一個 `name_hint: str = ""` 欄位（空字串時 fallback 到不含代碼的通用提示）比在程式碼裡寫死 `cmd.key == "whisper"` 更符合現有資料驅動慣例，未來若其他指令也需要代碼可直接在 `_GROUPS` 裡標註。

### 快捷鍵限定攔截時顯示 toast

`hotkey_manager.py` 的 `_on_key_press` 三個分支（技能／怪物／指令）在 `self._app_filter_blocks()` 為真時目前直接 `return`。改為在 `return` 前呼叫 `self.app.after(0, lambda: self.app.toast.show(<message>, "warning"))`，訊息內容統一為「目前視窗不是指定的目標視窗，快捷鍵未觸發」（三個分支共用同一句訊息，不需要依技能/怪物/指令分別造句，因為使用者關心的是「有沒有觸發」而非哪個命名空間）。

`app.toast` 呼叫只能在主執行緒（依 `toast-v2` spec 規範），所以必須透過 `self.app.after(0, ...)` 排回主執行緒，不可在 pynput daemon thread 直接呼叫，這點與現有 `trigger_skill` / `trigger_monster` 呼叫方式一致。

> 這個決策後續被「快捷鍵三命名空間改為共同觸發」取代：原本設計是「三個分支各自檢查、各自可能各跳一次 toast」，共同觸發版本改成整次按鍵只檢查一次、最多跳一次 toast，見下方新決策。

### 設定對話框補充說明文字

`settings_dialog_v2.py` 的「快捷鍵限定」列（`_row("快捷鍵限定", hotkey_wrap)`）維持原本 checkbox + 標籤 + 選視窗按鈕的水平列，在其下方新增一個小字 `QLabel`（`T.TEXT_MUTED`、11px，`setWordWrap(True)`），文字為「啟用後，快捷鍵只在下方指定的視窗為前景視窗時才會觸發，避免切到瀏覽器等其他視窗時誤觸」。做法比照 `command_page_v2.py` 已有的 hint QLabel 樣式（`T.TEXT_DIM`、12px），只是字級與顏色改用更低調的 `T.TEXT_MUTED` / 11px 以呈現「輔助說明」而非主要提示的視覺層級。

### 指令頁卡片版面：撤銷 needs_name 卡片固定寬度調整

撤銷先前的 `self.setFixedWidth(680)`（`_NeedsNameCard.__init__`）與 `v.addWidget(_NeedsNameCard(cmd, self), 0, Qt.AlignmentFlag.AlignLeft)`（`_build_group_body`），改回原本的 `self.setMaximumWidth(680)` 移除、`v.addWidget(_NeedsNameCard(cmd, self))`（無 stretch/alignment 參數，預設撐滿 `QVBoxLayout` 寬度，與 `_build_pair_row` 的兩欄卡片總寬一致）。

`QVBoxLayout.addWidget(widget)`（不帶 alignment）預設會把子元件撐滿版面寬度；一旦加上 `alignment` 參數，Qt 改用該元件的 `sizeHint()` 決定寬度（「依內容縮）而非撐滿，這也是為什麼先前試過 `setMaximumWidth(560)` 與 `setMaximumWidth(680)` 視覺上完全沒有差異 —— 兩者都遠大於 `sizeHint()` 算出的實際寬度，`maximumWidth` 從未真正成為限制寬度的那個因素；改成 `setFixedWidth` 才會生效，但 `setFixedWidth(680)` 本身就是造成「跟滿版的 no-arg 卡片對不齊」的直接原因。移除 alignment 並拿掉寬度限制後，卡片自然撐滿、和 no-arg 卡片對齊。

輸入框的 `setFixedHeight(32)` 與 `font-size: 13px`（連同「新增並複製」按鈕的 `height=32`）維持不變，這部分改善不受寬度調整影響。

### 快捷鍵三命名空間改為共同觸發（不互斥）

`_on_key_press` 目前結構是「技能命中 → 觸發 → return」「怪物命中 → 觸發 → return」「指令命中 → 觸發」，任何一個命名空間命中就會直接跳過後面的檢查。改為：先分別查出三個命名空間各自是否命中（`skill_id` / `monster_id` / `cmd_target`），只要三者皆為空就直接 return（不付出 `_app_filter_blocks()` 的查詢成本，維持原本「平常按鍵不查前景」的效能特性）；只要至少一個命中，才呼叫一次 `_app_filter_blocks()`；若被攔截，呼叫一次 `_notify_app_filter_blocked()` 後 return（不逐一命名空間各跳一次 toast）；若未被攔截，對每個命中的命名空間各自呼叫 `self.app.after(0, ...)` 分派觸發（技能／怪物／指令三者互不影響，皆各自觸發）。

指令命名空間的查詢維持原本的前置條件：`command_page` 存在且 `config_manager.get_command_hotkeys_enabled()` 為真時才查 `get_command_hotkey_target(key_name)`；這兩個前置條件不成立時，`cmd_target` 視為 `None`，不影響技能／怪物是否觸發。

此修正同時讓程式碼與 `hotkey-binding` spec 既有的「Hotkey namespaces are isolated」需求（同一按鍵綁技能與怪物時兩者都應觸發）恢復一致，並把指令命名空間也納入相同的共同觸發規則。

## Risks / Trade-offs

- [風險] 分組標頭改動涉及 6 個分組的 icon/accent 主觀選擇，可能與使用者預期不完全一致 → 緩解：所有選色/圖示皆取自現有資源與色票，不引入新依賴；如使用者對特定分組的圖示有意見，屬於後續可快速調整的資料表項目，不影響架構。
- [風險] toast 訊息在快速連續按鍵時可能被連續觸發、疊加過多提示 → 緩解：`ToastManagerV2` 本身已管理多個 toast 疊加顯示（既有機制），不需要在本次改動額外加節流；若使用體感上太吵，可在後續調整為節流，非本次範圍。
- [風險] `_Command` 新增 `name_hint` 欄位屬於資料結構變動，需同步檢查是否有其他程式碼假設 `_Command` 欄位數量（例如以位置而非關鍵字建構 `_Command`）→ 緩解：`_GROUPS` 目前全部以關鍵字引數建構 `_Command`（`_Command("reply", "/回覆", ...)` 為位置引數，需確認建構呼叫都要補上新欄位或給預設值，實作時逐一檢查 `_GROUPS` 內所有 `_Command(...)` 呼叫）。
- [風險] 快捷鍵改成共同觸發後，若技能與指令綁同一鍵，按一下鍵會同時彈出技能倒數視窗與指令複製回饋（`CommandCopyFlashV2`），畫面上可能同時出現兩種提示 → 緩解：這正是使用者要的效果（複製指令與技能倒數同時觸發），且兩者本來就是各自獨立的浮動 UI，互不遮擋邏輯已存在（技能倒數視窗與指令複製回饋本來就可能因為使用者操作而同時出現在畫面上），不需要額外處理。
- [風險] 撤銷 `setFixedWidth` 改回滿版寬度後，若某個 needs_name 指令一次記住很多名稱（chips 很多），滿版寬度下 `FlowLayout` 可容納的每行 chip 數變多，換行行為會跟固定寬度時不同 → 這是預期中的正常行為（滿版本來就该讓內容有更多可用空間），不是需要緩解的風險。

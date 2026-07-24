## 1. needs_name placeholder 依指令區分（needs_name 名稱輸入提示文字，Player name input hint reflects code requirement per command）

- [x] 1.1 在 `src/ui_v2/pages/command_page_v2.py` 的 `_Command` dataclass 新增 `name_hint: str = ""` 欄位，實作 Player name input hint reflects code requirement per command 需求
- [x] 1.2 在 `_GROUPS` 中為 `/密語`（whisper）的 `_Command` 設定含 `#代碼` 字樣的 `name_hint`（沿用現有文字「輸入玩家名稱（含 #代碼）後按複製」），其餘 needs_name 指令的 `name_hint` 留空或設為不含 `#代碼` 字樣的通用提示（例如「輸入玩家名稱後按複製」）
- [x] 1.3 修改 `_NeedsNameCard.__init__` 建立 `self._input` 時，改用 `cmd.name_hint`（空字串時 fallback 到通用提示常數）取代目前寫死的 `_NAME_PLACEHOLDER`

## 2. 快捷鍵限定攔截時顯示 toast（快捷鍵限定攔截時顯示 toast / Window-scoped hotkey triggering）

- [x] 2.1 在 `src/ui/hotkey_manager.py` 的 `_on_key_press` 中，技能分支（`skill_id` 命中且 `_app_filter_blocks()` 為真）改為在 `return` 前呼叫 `self.app.after(0, lambda: self.app.toast.show("目前視窗不是指定的目標視窗，快捷鍵未觸發", "warning"))`，實作 Window-scoped hotkey triggering 的攔截回饋
- [x] 2.2 對怪物分支（`monster_id` 命中且 `_app_filter_blocks()` 為真）套用相同的 toast 提示邏輯
- [x] 2.3 對指令快捷鍵分支（`target` 命中且 `_app_filter_blocks()` 為真）套用相同的 toast 提示邏輯
- [x] 2.4 確認三個分支共用同一句訊息字串（避免重複硬編碼，可抽成模組層級常量），並確認 toast 呼叫皆透過 `self.app.after(0, ...)` 排回主執行緒，不在 pynput daemon thread 直接呼叫

## 3. 設定對話框補充快捷鍵限定說明（設定對話框補充說明文字 / Settings dialog explains the window-scoped hotkey filter）

- [x] 3.1 在 `src/ui_v2/dialogs/settings_dialog_v2.py` 的「快捷鍵限定」列（`_row("快捷鍵限定", hotkey_wrap)`）下方新增一個 `QLabel`，樣式比照現有 hint 文字慣例（`T.TEXT_MUTED`、11px、`setWordWrap(True)`），文字為「啟用後，快捷鍵只在下方指定的視窗為前景視窗時才會觸發，避免切到瀏覽器等其他視窗時誤觸」，實作 Settings dialog explains the window-scoped hotkey filter 需求

## 4. 指令頁分組標頭重新設計（分組標頭改用 IconBadge + StatusChip）

- [x] 4.1 在 `src/ui_v2/pages/command_page_v2.py` 新增分組 → (glyph, accent) 對照表 `_GROUP_ICON`，依 design.md 的對照表填入六組：常用→(`star`, `T.ORANGE`)、交易 / 私訊→(`coins`, `T.BLUE`)、聊天頻道→(`globe`, `T.CYAN`)、隊伍 / 公會→(`user`, `T.GREEN`)、封鎖→(`eye-off`, `T.RED`)、其他→(`settings`, `T.PURPLE`)
- [x] 4.2 從 `src/ui_v2/components.py` import `IconBadge` 與 `StatusChip`，改寫 `_build_group_header(title, first)`：回傳一個水平列，內含 `IconBadge(glyph, accent, 22)`、標題 `QLabel`（沿用 `T.FONT_LABEL`）、`StatusChip(str(count), accent)`（該分組指令數量），維持 `first` 時上緣不留白、非首組留 `T.S_SM` 上緣的既有間距規則
- [x] 4.3 更新 `_build`（呼叫 `_build_group_header` 處）傳入分組指令數量，使 `StatusChip` 顯示正確數字

## 5. 驗證

- [x] 5.1 啟動應用程式，切到「指令」頁，確認六個分組標頭皆顯示對應 icon、標題與數量 chip，且 `/密語` 卡片的名稱輸入提示含 `#代碼` 字樣、其餘 needs_name 卡片不含
- [x] 5.2 在設定對話框開啟「快捷鍵限定」、選定一個非目前前景的目標視窗後，於非目標視窗按下已綁定的技能／怪物／指令快捷鍵，確認皆不觸發原本行為且跳出提示 toast；切回目標視窗後按下同一快捷鍵確認正常觸發且不跳提示
- [x] 5.3 確認設定對話框「快捷鍵限定」列下方顯示新增的說明文字
- [x] 5.4 執行 `python -m pytest tests/ -v` 確認既有測試通過

## 6. 指令頁卡片版面：撤銷 needs_name 卡片固定寬度調整

- [x] 6.1 在 `src/ui_v2/pages/command_page_v2.py` 的 `_NeedsNameCard.__init__` 移除 `self.setFixedWidth(680)`，保留 `self._input.setFixedHeight(32)` 與 QLineEdit `font-size: 13px`、`copy_btn` 的 `height=32` 不變
- [x] 6.2 在 `_build_group_body` 把 `v.addWidget(_NeedsNameCard(cmd, self), 0, Qt.AlignmentFlag.AlignLeft)` 改回 `v.addWidget(_NeedsNameCard(cmd, self))`（移除 stretch/alignment 參數），讓 needs_name 卡片恢復撐滿寬度、與 `_build_pair_row` 的兩欄 no-arg 卡片對齊

## 7. 快捷鍵三命名空間改為共同觸發（不互斥）（Hotkey trigger dispatch）

- [x] 7.1 在 `src/ui/hotkey_manager.py` 重構 `_on_key_press`：先分別查出 `skill_id`（`skill_manager.get_skill_by_hotkey`）、`monster_id`（`app.get_monster_by_hotkey`）、`cmd_target`（僅當 `app.command_page` 存在且 `config_manager.get_command_hotkeys_enabled()` 為真時查 `config_manager.get_command_hotkey_target`），三者皆為空（`None`/falsy）時直接 `return`
- [x] 7.2 三者至少一個命中時，呼叫一次 `self._app_filter_blocks()`；為真時呼叫一次 `self._notify_app_filter_blocked()` 後 `return`（不再依技能／怪物／指令個別重複檢查或個別跳 toast）
- [x] 7.3 未被攔截時，對每個命中的命名空間各自呼叫 `self.app.after(0, ...)` 分派觸發：`skill_id` 命中呼叫 `window_manager.trigger_skill(skill_id)`、`monster_id` 命中呼叫 `window_manager.trigger_monster(monster_id)`、`cmd_target` 命中則解析 `cmd_key, name = cmd_target` 後呼叫 `cmd_page.trigger_hotkey(ck, nm)`，三者互不影響、皆各自觸發，實作 Hotkey trigger dispatch 需求的共同觸發行為
- [x] 7.4 更新 `src/ui_v2/pages/command_page_v2.py` 檔案開頭 docstring 裡「指令命名空間與技能／怪物是各自獨立的...但實際觸發時 HotkeyManager 依「技能→怪物→指令」順序比對，若按鍵同時被技能或怪物占用，指令不會觸發」這段描述，改為說明技能／怪物／指令三個命名空間現在會共同觸發（同一按鍵命中多個命名空間時全部觸發，不互斥）

## 8. 驗證（版面一致性與快捷鍵共同觸發）

- [x] 8.1 啟動應用程式，切到「指令」頁，確認 needs_name 卡片（如 /邀請組隊）與同分組內 no-arg 兩欄卡片（如 /箭頭、/關閉）寬度一致、左右對齊到相同版面邊界，且名稱輸入框仍維持放大後的高度與字級
- [x] 8.2 把一個技能的快捷鍵與一個指令（如 /全體）的快捷鍵設成同一個按鍵，切回主視窗按下該鍵，確認技能倒數與指令複製（`CommandCopyFlashV2` 或 toast）皆有觸發，而不是只有技能觸發
- [x] 8.3 執行 `python -m pytest tests/ -v` 確認既有測試依然全數通過

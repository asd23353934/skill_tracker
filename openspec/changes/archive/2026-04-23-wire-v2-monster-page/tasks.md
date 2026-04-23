## 1. 前置驗證與盤點

- [x] 1.1 跑 `python verify_skill_page_v2.py` 確認 `wire-v2-app-context` 已上線且綠
- [x] 1.2 在 `src/ui/app.py` 標出 8 個怪物方法的起訖行：`edit_respawn_time` / `reset_respawn_time` / `reset_monster_hotkey` / `edit_monster_alert_before` / `update_monster_alert_sound` / `update_monster_end_sound` / `update_monster_loop` / `update_monster_permanent`
- [x] 1.3 在 `src/ui/hotkey_manager.py` 找到 monster callback 觸發 `card.update_hotkey_display(...)` 的位置，記下行號

## 2. AppCoreMixin exposes 8 monster interaction methods

- [x] 2.1 落實 Requirement「AppCoreMixin exposes 8 monster interaction methods」第一批：把 `edit_respawn_time` / `reset_respawn_time` / `reset_monster_hotkey` 三個方法整段從 `src/ui/app.py` 剪到 `src/ui/app_core.py` 的 `AppCoreMixin` 末段，簽名 / 行為一字不變；App 內這三個方法定義刪除（不留 stub）
- [x] 2.2 同樣搬 `edit_monster_alert_before` / `update_monster_alert_sound` / `update_monster_end_sound`
- [x] 2.3 同樣搬 `update_monster_loop` / `update_monster_permanent`
- [x] 2.4 驗證 `App.edit_respawn_time.__qualname__.startswith("AppCoreMixin.")` —— `python -c "from src.ui.app import App; assert App.edit_respawn_time.__qualname__.startswith('AppCoreMixin.')"` 必須通過
- [x] 2.5 import smoke：`python -c "from main_v2 import V2AppContext; from src.ui.app import App; print(App.edit_respawn_time, V2AppContext.edit_respawn_time)"` 必須印出兩個同源 mixin function

## 3. HotkeyManager callback updates V1 or V2 monster card

- [x] 3.1 落實 Requirement「HotkeyManager callback updates V1 or V2 monster card」：在 `src/ui/hotkey_manager.py` monster 綁定成功後的 callback 區段，把 `card.update_hotkey_display(text, has_hotkey)` 改為 `(getattr(card, "set_hotkey_text", None) or card.update_hotkey_display)(text, has_hotkey)`，沿用既有 `app.after(0, ...)` 包裝
- [x] 3.2 V1 回歸：`python main.py`，在 monster 頁綁一個熱鍵，確認 chip 文字立即更新（V1 走 `update_hotkey_display`）

## 4. V2 monster page lists current profile monsters

- [x] 4.1 落實 Requirement「V2 monster page lists current profile monsters」第一步：在 `src/ui_v2/pages/monster_page_v2.py` 移除 `DEMO_MONSTERS` 常量
- [x] 4.2 `MonsterPageV2.__init__` 加 `self._loaded = False`、`self._cards_layout` 引用；`_build` 不再迴圈 DEMO_MONSTERS，改保留 `inner` 容器空白
- [x] 4.3 加 `showEvent(self, e)`：當 `not self._loaded and self.app is not None` 時，呼叫 `self.app.get_all_monsters()` 取列表，逐筆 `MonsterCard(inner, self.app, m["id"])` append；設 `self._loaded = True`；末段 `super().showEvent(e)`
- [x] 4.4 import smoke：`python -c "from src.ui_v2.pages.monster_page_v2 import MonsterPageV2"` 必須通過

## 5. MonsterCard wires interactions to App methods（拆解 build）

- [x] 5.1 落實 Requirement「MonsterCard wires interactions to App methods」介面變更：把 `MonsterCard.__init__` 簽名改為 `(parent, app, monster_id)`；內部 `self.monster = app.monster_service.get(monster_id)` 取得目前狀態並存欄位（name / icon_name / accent / respawn / hotkey / alert_before / loop / permanent / end_sound / alert_sound）
- [x] 5.2 respawn 顯示區改為按鈕（QPushButton with `_v2_apply_accent`），click → `app.edit_respawn_time(monster_id)`；reset icon → `app.reset_respawn_time(monster_id)`；按鈕註冊到 `app.monster_respawn_buttons[monster_id]`
- [x] 5.3 hotkey 顯示區改為按鈕，click → `app.hotkey_manager._monster_card = self; app.hotkey_manager.begin_capture(monster_id, self.monster["name"])`；reset → `app.reset_monster_hotkey(monster_id)`；新增 `set_hotkey_text(text, has_hotkey)` 方法
- [x] 5.4 alert pill 改為按鈕，click → `app.edit_monster_alert_before(monster_id)`；註冊到 `app.monster_alert_before_buttons[monster_id]`
- [x] 5.5 loop / permanent QCheckBox 各自 `stateChanged` → `app.update_monster_loop(monster_id, bool)` / `app.update_monster_permanent(monster_id, bool)`
- [x] 5.6 end-sound / alert-sound combo `currentTextChanged` → `app.update_monster_end_sound(monster_id, filename)` / `app.update_monster_alert_sound(monster_id, filename)`；初值取 `self.monster.get("sound") / "alert_sound"`

## 6. V2 monster page removes the add-monster button

- [x] 6.1 落實 Requirement「V2 monster page removes the add-monster button」：在 `MonsterPageV2._build` 移除 `add_btn` 區塊（QPushButton "新增怪物" + setIcon + setStyleSheet + clicked.connect + bar.addWidget）；header 留 title 「怪物重生」 + hint「按下快捷鍵...」
- [x] 6.2 移除類別內的 `_toast_pending` 方法（已無使用）

## 7. 驗證腳本

- [x] 7.1 新增 `verify_monster_page_v2.py`，仿 `verify_skill_page_v2.py`：用 `_FakeApp` + `_FakeMonsterService` 覆蓋 `get_all_monsters` / `monster_service.get` / 8 個 monster 方法（mock 紀錄 call）
- [x] 7.2 test: `MonsterPageV2.showEvent` 後渲染卡片數 == fixture 怪物數
- [x] 7.3 test: 點 respawn 按鈕觸發 `app.edit_respawn_time(id)`；reset 觸發 `app.reset_respawn_time(id)`
- [x] 7.4 test: 點 hotkey 按鈕觸發 `app.hotkey_manager.begin_capture(id, name)`；hotkey_manager._monster_card 指向卡片
- [x] 7.5 test: 勾 loop / permanent 觸發對應 `app.update_monster_loop / update_monster_permanent` 各一次
- [x] 7.6 test: `card.set_hotkey_text("F5", True)` 後 hotkey 按鈕文字 == "F5"
- [x] 7.7 test: 頁面 header 內無 text == "新增怪物" 的 QPushButton
- [x] 7.8 全腳本通過 exit 0

## 8. 手動回歸

- [x] 8.1 `python main.py --v2` 啟動，monster 頁顯示所有 profile 內怪物（不再是 4 張 demo）
- [x] 8.2 點 respawn → V1 input dialog → 改值 → chip 顯示新秒數 + accent
- [x] 8.3 點 hotkey → 按 F5 → chip 顯示 "F5"；觸發 F5 → 該怪物計時視窗出現
- [x] 8.4 勾常駐 → 怪物計時視窗常駐顯示；取消勾選 → 視窗關閉
- [x] 8.5 改音效 → 觸發計時 → 結束時播放新音效
- [x] 8.6 V1 `python main.py` monster 頁所有互動無 regression

## 9. 收尾

- [x] 9.1 跑 `/simplify` 與 `/spectra-audit` 檢視 mixin 補丁 + V2 monster page diff
- [x] 9.2 同步 docs/PROJECT.md：在 `src/ui/app_core.py` 條目加註已含怪物 8 方法
- [ ] 9.3 commit：純技術接線、V1 行為等價、不 bump version

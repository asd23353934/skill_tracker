## Context

V2 shell (`main_v2.py` / `src/ui_v2/`) 為紫色漸層 dashboard 改版，目前 potion / overlay / mapleworld 已接線，剩 `skill_page_v2.py` 與 `monster_page_v2.py` 仍為純 UI 殼。本次專注 skill 頁。

V1 `SkillPage` 的狀態矩陣最複雜：
- 94 個技能（skills + items），分 player / boss / item 三大類，各含多個 subcategory。
- 每技能 8 欄可覆寫狀態：`hotkeys` / `permanent` / `loop` / `alert_enabled` / `cooldown_overrides` / `alert_seconds_overrides` / `sound_overrides` / `alert_sound_overrides`。
- 狀態存在 `profiles/{name}.json`，App 透過 property 委派（`app.skill_hotkeys` 等）代理到當前 profile。
- hotkey 觸發在 pynput daemon thread，所有 UI 更新必須經 `app.after(0, func)`。

V2 shell 已提供 `SkillCard` / `SkillColumn` 視覺殼，但全部使用 `DEMO_DATA` 假資料、按鈕只跳 Toast。需將真實資料與 callback 接入，同時維持 V2 設計語言（IconBadge、InputChip、pill）。

## Goals / Non-Goals

**Goals:**

- V2 技能頁可完整替代 V1 日常使用（冷卻觸發、熱鍵擷取、常駐視窗、提醒聲音覆寫）。
- V1 / V2 共用同一份 profile 狀態（last-writer-wins）；兩頁可同時存在，切換時 rebuild。
- 保留 V2 設計語言（InputChip、IconBadge、紫色漸層）。
- 寫回時走既有 `config_manager.save_profile(name, snapshot)`，不新增寫入路徑。

**Non-Goals:**

- 不重寫 V1 SkillPage；V1 保留到 V2 全頁接線完成後再評估下線。
- 不改動 SkillManager / HotkeyManager / WindowManager / ConfigManager 公開 API。
- 不新增批次多選 / 拖曳排序 UI。
- 不調整 94 技能的 category / subcategory 配置（由 config.json 決定）。

## Decisions

### Decision: 拆出 SkillCardV2 / SkillColumnV2 到獨立檔

**選擇**：把現有 `skill_page_v2.py` 的 `SkillCard` / `SkillColumn` 類別拆到 `skill_card_v2.py` / `skill_column_v2.py`，由 `skill_page_v2.py` 匯入組裝。

**理由**：
- 現檔 ~560 行已吃重；加接線後每張卡需追蹤 8 狀態 × 4 callback，易突破 800 行。
- 拆檔後 `skill_card_v2.py` 負責 per-skill 綁定（最密集），`skill_column_v2.py` 負責欄位分組，`skill_page_v2.py` 只做頁面組裝與 app-level callback（toggle_all / showEvent rebuild）。
- `verify_skill_page_v2.py` 可分別對 card / column / page 三層寫斷言。

**替代方案**：保留單檔、只加 region 註解。拒絕原因：檔案肥大難 navigate、diff review 困難。

### Decision: 複用 V1 App 方法而非新增 V2 專屬 callback

**選擇**：V2 SkillCard 直接呼叫 `app.update_skill_setting_exclusive` / `app.edit_cooldown` / `app.reset_hotkey` 等 V1 既有方法。

**理由**：
- V1 App 方法已包含「狀態寫入 + save_profile + 常駐視窗同步 + toast」完整流程。
- 若為 V2 另寫一份會產生狀態雙寫風險（V1 / V2 不同步）。
- V1 方法是以 `skill_id` 為參數，不依賴 V1 特定 widget 實例，V2 可直接呼叫。

**例外**：若 V1 方法硬連到 V1 widget（例如 `app._apply_btn_style(widget, ...)` 直接操作 QPushButton），V2 需改為讀值後自行繪製。這類情況由 Card 內部自己處理，不動 App 層。

**替代方案**：在 V2 SkillCard 內自行 `config_manager.save_profile(...)`。拒絕原因：錯過常駐視窗生命週期同步。

### Decision: rebuild 策略 — 粗粒度 + 局部 refresh

**選擇**：
- **全頁 rebuild**：`showEvent`（首次顯示）、`app.profile_changed` 訊號（切換 profile 後）。
- **局部 refresh**：單張卡片狀態變更 → 只呼叫 `card.refresh()` 重繪該卡控件狀態，不 rebuild 整頁。
- **hotkey 擷取完成**：hotkey_manager 透過 `app.skill_hotkey_buttons` 尋找目標 widget 並呼叫 `.refresh()`；V2 需註冊到同一個表。

**理由**：
- 全頁 rebuild（94 卡）約 >100ms，頻繁觸發會卡頓。
- 單卡 refresh 只更新 QPushButton 文字 + 樣式，<1ms。
- V1 已用同模式（`app.cooldown_buttons` / `app.hotkey_buttons` / `app.alert_seconds_buttons` / `app.permanent_vars` / `app.loop_vars` / `app.alert_enabled_vars`）；V2 沿用這些 dict，註冊 `skill_id → V2Card` 即可讓 V1 App 方法無須區分 V1/V2。

### Decision: V2 Card refresh 介面契約

**選擇**：V2 `SkillCardV2` 公開 `refresh()` 方法，內部依 `skill_id` 重讀 app state 並更新：
- 冷卻 chip 文字（`override ?? original`）與修改態色（override → CYAN bg）。
- 熱鍵 chip 文字（`hotkeys[id] or '未設'`）與色（有按鍵 → YELLOW）。
- 三 checkbox 的 `setChecked`（`blockSignals` 避免觸發 callback）。
- 提前秒數 pill 文字（`alert_seconds_overrides[id] ?? alert_before_seconds`）。

V1 既有的 `app.cooldown_buttons[id].setText(...)` 等直接操作在 V2 須替換為 `app.skill_card_widgets[id].refresh()`；為了向下相容，V2 Card 建構時把自己與所有控件註冊到 V1 的 dict（`app.cooldown_buttons[id] = self.cooldown_chip.value_btn`），讓 V1 已編寫的直接 `setText` 仍可工作。

### Decision: SkillDetailDialogV2 擴充

**選擇**：擴充現有 `src/ui_v2/dialogs/skill_detail_dialog_v2.py`，加入：
- 自訂圖示（QFileDialog 選檔 → 複製到 `overlays_user/` → 寫 `skill_icon_overrides`）— **若 V1 有此功能才加**；若 V1 沒有則不加。
- 結束聲音下拉 + 試聽按鈕 → 讀寫 `skill_sound_overrides[id]`。
- 提前聲音下拉 + 試聽按鈕 → 讀寫 `skill_alert_sound_overrides[id]`。
- 從清單移除按鈕（profile 層移除，不影響 config.json 靜態區）。

**理由**：V1 `SkillDetailDialog` 已實作此行為，V2 對話框只是殼。擴充既有檔比新增檔維持單一對話框來源。

### Decision: 頁首「全選」chip 行為

**選擇**：三顆 chip（常駐/循環/提醒）點擊呼叫 `app.toggle_all('permanent'|'loop'|'alert')`；V2 不做確認對話框，依 V1 行為 single-click 全開/全關。

**理由**：V1 行為相同；V2 chip 放在頁首右側，與 V2 設計語言一致（`ChipResetBtn` 風格）。

## Risks / Trade-offs

- **雙頁共存的狀態同步風險** → V1 / V2 同時開啟時，修改 V2 狀態後切到 V1 頁，V1 SkillPage 需在 `showEvent` 重新讀 app state。**Mitigation**：V1 `SkillPage` 已在建構時讀 app state，但不一定有 `showEvent rebuild`；需驗證並視情況補上。
- **94 卡 rebuild 速度** → 初次 rebuild 可能超過 100ms。**Mitigation**：將 SkillManager 的 `qpixmaps_card` cache 確認在啟動時載入（V1 已做），避免 rebuild 時同步讀圖。
- **V1 App 方法直接操作 V1 widget 的耦合** → 若 `app.update_skill_setting_exclusive` 直接呼叫 V1 checkbox 的 `isChecked()`，會對 V2 checkbox 失敗。**Mitigation**：審視 V1 App 方法，把「從 widget 讀狀態」的路徑改為「從 app state 讀」，或把 widget 改用同一份 V1 dict 註冊。
- **hotkey daemon thread dispatch** → V2 Card 若直接被 pynput thread 呼叫 `refresh()` 會 crash。**Mitigation**：hotkey_manager 已透過 `app.after(0, ...)` 排隊；V2 Card 不在 daemon thread 被呼叫，只要維持這條路徑即可。
- **verify 腳本涵蓋度** → 94 卡 × 8 狀態 × 4 callback 斷言爆炸。**Mitigation**：verify 只涵蓋「代表性卡片」：player/boss/item 各 1 張，驗證 rebuild、checkbox 雙向、hotkey 註冊、冷卻覆寫 → reset 流程，不窮舉 94 卡。

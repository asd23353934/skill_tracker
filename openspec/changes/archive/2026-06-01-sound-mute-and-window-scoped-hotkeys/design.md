## Context

技能冷卻追蹤器（PySide6 桌面 App）目前的提示音由單一全域旗標 enable_sound 控制（設定對話框「啟用聲音」），同時關掉完成音與提前音；skill_window 在完成（_on_finish）與提前提示（_trigger_alert）兩處都讀同一旗標。每技能音效以 profile 的 skill_sound_overrides / skill_alert_sound_overrides 表達，空字串代表「使用全域」，無法表達「單獨靜音」。

快捷鍵由 pynput 全域監聽（hotkey_manager._on_key_press，daemon thread），目前在任何前景視窗都會觸發，於非遊戲視窗易誤觸。

本設計沿用既有架構（全域設定存 config_user.json、每技能狀態存 profile override dict、pynput 觸發點、BaseDialogV2 對話框、資源中心卡片網格），把改動面壓到最小。

## Goals / Non-Goals

**Goals:**

- 完成音與提前提示音可各自獨立禁音（全域層級）
- 個別技能可單獨靜音其完成音／提前音，與「使用全域」明確區分
- 提供可開關的「快捷鍵僅在指定前景視窗時觸發」，並能用畫面縮圖辨識目標視窗
- 不新增第三方相依；不破壞既有使用者設定（自動遷移）

**Non-Goals:**

- 不支援多個目標視窗（單一目標）
- 不做技能小窗下方文字（使用者已排除）
- 非 Windows 平台不另做視窗限定實作
- 不支援最小化視窗的畫面縮圖（退回程式圖示 + 標題）

## Decisions

### 全域聲音拆成兩個獨立開關並遷移 enable_sound

設定對話框把單一「啟用聲音」改為兩個勾選框「完成提示音」「提前提示音」，對應新 settings 欄位 enable_end_sound / enable_alert_sound（存 config_user.json）。skill_window 完成音改讀 enable_end_sound、提前音改讀 enable_alert_sound。載入設定時若舊檔只有 enable_sound、無新欄位，則兩者皆取 enable_sound 值（遷移）。
- 替代方案：保留單一開關 + 另加「提前音」子開關 → 語意不對稱、較難理解，否決。

### 每技能靜音以 sentinel 值表達三態

每技能音效需要三態：使用全域 / 指定音效 / 靜音。沿用既有 skill_sound_overrides / skill_alert_sound_overrides，新增一個保留字 sentinel（例如 "__mute__"）代表「靜音」，與空字串（使用全域）、實際檔名（指定音效）區分。技能細節對話框下拉新增「靜音（不播放）」純文字選項對應此 sentinel。
- 替代方案：新增獨立的 per-skill bool dict（skill_sound_muted）→ 多一組 profile 欄位與序列化路徑，較零散，否決。

### 全域與每技能的優先順序（全域關 = 總靜音）

SkillService.get_sound_for_skill / get_alert_sound_for_skill 的解析順序：全域該類開關關閉 → 直接回空（總靜音，凌駕一切）；全域開啟時，override 為 sentinel → 回空（單獨靜音）；override 為檔名 → 回該檔名；override 為空 → 回全域音檔。
- 全域開關屬「總閘」直覺；每技能僅在全域開啟時生效。

### 視窗縮圖用 PrintWindow 而非截螢幕

挑選器開啟時自身為最前景，截螢幕區域會抓到挑選器或被遮擋內容。改用 Windows PrintWindow（PW_RENDERFULLCONTENT = 2）讓目標視窗自行繪出內容，再轉 QPixmap，與 z-order 無關。
- 替代方案：QScreen.grabWindow(hwnd) → 實為截螢幕區域，挑選器在前景時失效，否決。
- 限制：最小化視窗 PrintWindow 取不到 → 退回顯示程式圖示 + 標題。

### 前景視窗比對只在快捷鍵命中後執行，以 exe 名稱比對

hotkey_manager._on_key_press 先以既有邏輯比對到技能／怪物快捷鍵後，才呼叫 window_enum.get_foreground_exe() 比對目標 exe；不符則忽略。如此一般打字不付出額外成本。比對用執行檔名稱（非視窗標題），遊戲重開或標題含角色名變動仍可辨識。捕捉快捷鍵模式（waiting_for 路徑）在比對之前，不受此限。
- 替代方案：每次按鍵都查前景 → 無謂成本；用視窗標題比對 → 標題易變，皆否決。
- 執行緒：get_foreground_exe 僅用 ctypes（user32/psapi），不碰 Qt，於 daemon thread 安全。

### 視窗列舉與縮圖獨立為 infrastructure 模組

新增 src/infrastructure/window_enum.py（Qt-free，ctypes）：list_windows()（hwnd / title / pid / exe）、get_foreground_exe()、capture_window_thumbnail(hwnd) 回傳 RGBA bytes（縮圖）。UI 層負責把 bytes 轉 QPixmap（沿用 skill_window 的 PIL→QPixmap 模式），維持 infrastructure 不依賴 Qt。
- 與既有 mapleworld_scanner 一樣屬「外部邊界 / OS」模組。

### 視窗挑選器為獨立對話框（縮圖卡片網格）

新增 src/ui_v2/dialogs/window_picker_dialog_v2.py（繼承 BaseDialogV2），可捲動縮圖卡片網格，每張卡片 = 視窗畫面縮圖 + 標題（過長截斷），點選橘框高亮、雙擊或「確認」選定，附「重新整理」鈕重抓快照。設定對話框只放開關 + 目前目標 + 「選擇視窗…」按鈕開啟此挑選器。
- 沿用資源中心 mapleworld_widgets_v2 卡片網格樣式。

## Risks / Trade-offs

- [GPU 加速 / Chromium 視窗（Chrome、Electron，可能含部分遊戲）被遮擋時，即使 PW_RENDERFULLCONTENT 仍可能回傳空白畫面] → 實測確認此限制：挑選器在最前景時目標被遮擋，這類 app 縮圖會是白底（標題仍可辨識）。列為已知限制，待以實際遊戲視窗實測後再決定是否改用 DWM 即時預覽（DwmRegisterThumbnail）。
- [最小化視窗無法擷取畫面] → 退回程式圖示 + 標題，卡片仍可選。
- [兩個程式同 exe 名（少見）會同時符合] → 可接受；單一遊戲情境足夠。
- [挑選器一次擷取多個視窗縮圖可能略慢] → 縮圖縮放至小尺寸、開啟時一次擷取 + 手動重新整理，不做即時更新。
- [enable_sound 移除造成舊版回退讀不到] → 載入時保留相容讀取，遷移時不刪除舊鍵，降低風險。
- [設定對話框新增列使高度不足] → 調整對話框高度。

## Migration Plan

1. config_manager.DEFAULT_USER_SETTINGS 新增 enable_end_sound / enable_alert_sound（預設 True）與 hotkey_app_filter_enabled（False）/ hotkey_app_target_exe / hotkey_app_target_label（空）。
2. app_core 載入設定時：若無 enable_end_sound / enable_alert_sound 但有 enable_sound，兩者皆取 enable_sound；之後以兩個新欄位為準。保留 enable_sound 鍵不刪，作為相容。
3. 既有 profile 的 override dict 不需遷移；未設定者行為不變（使用全域）。
4. 回退策略：新欄位皆有預設值，移除本變更後舊版仍可讀 config_user.json（忽略未知鍵）。

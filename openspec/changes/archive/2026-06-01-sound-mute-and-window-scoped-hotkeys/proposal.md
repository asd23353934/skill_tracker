## Why

技能冷卻追蹤器的提示音目前只有單一全域開關，完成音與提前提示音綁在一起無法分開，也無法針對個別技能靜音；同時全域快捷鍵在任何視窗都會觸發，在非遊戲視窗（打字／聊天）時容易誤觸技能計時。本次實作兩項使用者明確要求的設定：提示音分開禁音（全域 + 每技能），以及「只在指定前景視窗（遊戲）時才觸發快捷鍵」。

## What Changes

提示音禁音（全域 + 每技能）
- 設定對話框的單一「啟用聲音」開關拆成兩個獨立開關：完成提示音、提前提示音
- 技能細節對話框的兩個音效下拉（冷卻完成 / 提前提示）各新增「靜音（不播放）」選項，可單獨靜音某技能
- 三態語意：使用全域 / 指定音效 / 靜音；全域該類關閉視為總靜音，凌駕每技能設定
- 既有 enable_sound 設定值自動遷移為兩個新開關（原為關 → 兩者皆關；原為開 → 兩者皆開）

快捷鍵限定前景視窗（可開關）
- 設定對話框新增開關「只在指定視窗觸發快捷鍵」與目標視窗選擇入口
- 新增視窗挑選器對話框：以縮圖卡片網格列出目前開啟的視窗，顯示每個視窗的畫面縮圖供辨識，點選後設定為目標
- 開關開啟時，僅當指定程式（以執行檔名稱比對）為最前景視窗，已註冊的技能／怪物快捷鍵才會觸發；捕捉快捷鍵時不受限
- 前景比對只在「按到已註冊快捷鍵之後」才執行，避免每次按鍵的額外成本

## Non-Goals

- 不處理多個目標視窗（僅單一目標）
- 不做技能小窗下方顯示文字（使用者已明確排除）
- 視窗限定為 Windows 專屬，不為其他平台另做實作
- 不支援最小化視窗的畫面縮圖（退回顯示程式圖示 + 標題）

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `sound-system`: 完成音與提前提示音改為可獨立禁音；新增每技能「靜音（不播放）」狀態，並定義全域與每技能的優先順序
- `hotkey-binding`: 新增「僅在指定前景視窗時才觸發快捷鍵」的可開關行為，以及以畫面縮圖辨識的目標視窗選擇

## Impact

- Affected specs: sound-system（modified）、hotkey-binding（modified）
- Affected code:
  - New:
    - src/infrastructure/window_enum.py（Qt-free，ctypes 列舉視窗 / 取前景 exe / PrintWindow 縮圖）
    - src/ui_v2/dialogs/window_picker_dialog_v2.py（縮圖卡片網格挑選器，繼承 BaseDialogV2）
  - Modified:
    - src/ui_v2/dialogs/settings_dialog_v2.py（兩個聲音開關 + 快捷鍵限定區）
    - src/ui_v2/dialogs/skill_detail_dialog_v2.py（每技能「靜音」選項）
    - src/ui/skill_window.py（完成音 / 提前音改吃各自開關）
    - src/ui/hotkey_manager.py（觸發前比對前景視窗 exe）
    - src/domain/services.py（get_sound_for_skill / get_alert_sound_for_skill 處理靜音 sentinel）
    - src/infrastructure/config_manager.py（DEFAULT_USER_SETTINGS 新增欄位與 enable_sound 遷移）
    - src/ui/app_core.py（apply_settings 與載入設定串接新欄位）
  - Removed: (none)
- Dependencies: 無新增第三方套件；視窗列舉與縮圖透過 ctypes 呼叫 Windows API（user32 / gdi32）
- Platform: 快捷鍵視窗限定為 Windows 專屬（與既有 pynput / winsound / MCI 一致）

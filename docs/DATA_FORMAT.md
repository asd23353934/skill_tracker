# 資料格式

## 資料分區原則

| 分區 | 位置 | 性質 | 說明 |
|------|------|------|------|
| 靜態區 | `config.json` → `skills` / `items` | **唯讀** | 技能/道具元資料，隨版本更新覆蓋 |
| 全域可變區 | `config_user.json` → `settings` / `monsters` / `overlays` | 可變 | 跨配置共用，gitignored 不入 ZIP |
| 配置可變區 | `profiles/{name}.json` | 可變 | 每個配置獨立的使用者狀態，gitignored |

### 靜態區允許的欄位（skills / items）

靜態區只存放**不因使用者操作而改變**的元資料：

```
id, name, icon, cooldown, category, subcategory
```

> **禁止**在靜態區存放任何使用者狀態（快捷鍵、開關、覆寫值等）。

### 配置可變區存放的欄位（profiles）

所有**因使用者、因配置而異**的狀態，一律存到 `profiles/{name}.json`：

```
hotkeys, permanent, loop, alert_enabled,
cooldown_overrides, alert_seconds_overrides,
sound_overrides, alert_sound_overrides
```

> `sound_overrides` / `alert_sound_overrides` 的值為三態：缺鍵或 `""` = 使用預設
> （所有技能預設為念出名稱的 TTS 語音，無對應 TTS 時 fallback 全域聲音）；
> 實際檔名 = 指定音效；保留字 `"__mute__"`（`MUTE_SENTINEL`）= 靜音（該技能此類音效永不播放）。

---

## config.json 結構

```json
{
  "skills": [
    { "id": "", "name": "", "icon": "", "cooldown": 0, "category": "", "subcategory": "" }
  ],
  "items": [
    { "id": "", "name": "", "icon": "", "cooldown": 0, "category": "item", "subcategory": "" }
  ],
  "settings": { "player_name": "", "skill_start_x": 0, "skill_start_y": 0, "current_profile": "" },
  "monsters": [
    { "id": "", "name": "", "icon": "", "respawn_time": 0, "hotkey": "", "alert_before": 0, "loop": false, "permanent": false }
  ],
  "overlays": [
    { "id": "", "name": "", "file": "", "alpha": 1.0, "x": 0, "y": 0, "width": 0, "height": 0 }
  ]
}
```

- `skills` / `items`：唯讀，`ConfigManager` 以初始快照覆寫以防意外修改
- `settings`：僅存跨配置的全域設定（視窗位置、完成/提前提示音開關 `enable_end_sound` / `enable_alert_sound`、音量、快捷鍵限定 `hotkey_app_filter_enabled` / `hotkey_app_target_exe` / `hotkey_app_target_label`、指令頁 per-command 玩家名稱 `command_names`、指令頁快捷鍵 `command_hotkeys`、current_profile 等）
  - `command_names`：指令頁「需玩家名稱」指令的名稱記憶，結構為 `{ <指令key>: ["名稱1", ...] }`（每個指令各自一份、最近在前、去重、上限 20，名稱含 `#代碼` 原樣保存）。讀寫走 `ConfigManager.get_command_names` / `add_command_name` / `remove_command_name` / `rename_command_name`。
  - 升級相容（per-key fallback）：舊版單一共用清單 `command_recent_names` 仍可讀 — **未曾寫入過的指令 key**（不在 `command_names` map 中）以其作為唯讀初始來源；某指令 key 一旦被寫入（含被刪到空清單）即以 map 內的值為準、不再回填舊清單。fallback 以「key 是否在 map 中」判斷而非「map 是否存在」，避免對任一指令的首次刪除連帶清空其他尚未操作指令的繼承名單。
  - `command_hotkeys`：指令頁快捷鍵（指令層級 / MRU 觸發），結構為 `{ <指令key>: "KEY" }`。
  - `command_name_hotkeys`：指令頁快捷鍵（名稱層級，needs_name 指令下特定名稱專屬），結構為 `{ <指令key>: { <名稱>: "KEY" } }`。
  - 兩者共用同一份按鍵去重池（設定其中一筆會清掉另一層裡值相同的按鍵），確保同一實體按鍵在「指令」命名空間裡只對應唯一觸發目標；改名會遷移該名稱的專屬快捷鍵、刪除名稱會連帶清除其快捷鍵，避免孤兒綁定。與技能／怪物是各自獨立的命名空間（僅指令彼此之間去重，不互相清除）；`HotkeyManager` 實際觸發時三個命名空間不互斥，同一按鍵若同時綁在技能／怪物／指令上，全部會一起觸發。按下快捷鍵＝觸發一次「複製」：指令層級複製最近使用的名稱，名稱層級固定複製綁定當下的那個名稱，皆等同點擊該指令卡的複製鈕 / 名稱 chip。讀寫走 `ConfigManager.get_command_hotkey` / `get_command_name_hotkey` / `get_command_hotkey_target` / `set_command_hotkey` / `set_command_name_hotkey`。
  - `command_hotkeys_enabled`：指令快捷鍵觸發總開關（bool，預設 `true`）。關閉後 `HotkeyManager` 比對按鍵時整個跳過指令命名空間，任何指令快捷鍵按下都不會觸發複製；不影響設定／清除快捷鍵本身。讀寫走 `ConfigManager.get_command_hotkeys_enabled` / `set_command_hotkeys_enabled`。
- `monsters` / `overlays`：各自的狀態完整存於此，不拆到 profiles

## config_user.json（user 可變區實際儲存位置）

從 `config-static-merge` 起，`settings` / `monsters` / `overlays` 三個全域可變區實際**只**儲存在 `config_user.json`（與 `config.json` 同層）。`ConfigManager` 啟動時：

- 一律讀 `config.json` 取靜態區（`skills` / `items`）
- 若 `config_user.json` 存在 → 讀入後覆蓋 in-memory 的 settings / monsters / overlays
- 若 `config_user.json` 不存在 + `config.json` 含 `_user_data_stripped: true` → 建空白 user 檔（防止讀到 release placeholder）
- 若 `config_user.json` 不存在 + 無 stripped 標記（pre-split 升級）→ 從 `config.json` 抽出三欄寫成 user 檔

`save()` 只寫 `config_user.json`，`config.json` 在程式運行期間磁碟內容不變。

`config_user.json` 加入 `.gitignore`，不入版控；release ZIP 也不打包。

## profiles/{name}.json 結構

```json
{
  "hotkeys": {},
  "permanent": {},
  "loop": {},
  "alert_enabled": {},
  "cooldown_overrides": {},
  "alert_seconds_overrides": {},
  "sound_overrides": {},
  "alert_sound_overrides": {}
}
```

---

## 檔案實際落點（打包後）

| 檔案 | 位置 | 理由 |
|------|------|------|
| `config.json` | `_internal/`（`resource_path`） | 靜態唯讀區，隨 ZIP 覆蓋更新 |
| `config_user.json` | **exe 同層**（`user_data_path`） | 更新解壓只覆蓋 `_internal/`，user 資料必須在外面 |
| `profiles/` | **exe 同層** | 同上 |
| `potion_saves/` / `potion_autosave.json` | **exe 同層** | 同上 |

`ConfigManager(config_path, user_dir=...)`：`config_path` 指靜態區，`user_dir` 指
user 可變區目錄。`user_dir` 省略時退回與 `config.json` 同層（開發模式 / 測試 —— 兩者
本來就同層，行為不變）。打包入口 `main_v2.py` 明確傳入 `user_data_path("")`。

> ⚠️ v4.10.2 以前 user 檔寫在 `_internal/`（= config.json 同層）。該目錄是 PyInstaller
> bundle，release ZIP 解壓時會逐檔覆寫 —— 只要 ZIP 內混進 `_internal/config_user.json`，
> 使用者的設定就會被打回預設值。`ConfigManager._migrate_legacy_user_dir()` 負責在升級後
> 把舊位置的資料接過來（只在新位置不存在時複製，絕不覆蓋使用者現有資料）。

## 升級行為

- `config.json` 隨 release ZIP 更新（靜態區覆蓋 → 新技能 / items 自動帶入）
- `config_user.json` / `profiles/` 在 ZIP 內不存在 → 升級不會覆蓋使用者個人狀態
  - 由 `zip_release.py` 的 `is_user_data()` 在打包時排除，壓完再回讀 ZIP 二次確認，
    驗出使用者資料就刪檔並中止發布
- 第一次安裝的使用者會由 `ConfigManager` 自建 `config_user.json`（從 `DEFAULT_USER_SETTINGS`）和預設 profile

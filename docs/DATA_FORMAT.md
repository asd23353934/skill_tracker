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

> `sound_overrides` / `alert_sound_overrides` 的值為三態：缺鍵或 `""` = 使用全域；
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
- `settings`：僅存跨配置的全域設定（視窗位置、完成/提前提示音開關 `enable_end_sound` / `enable_alert_sound`、音量、快捷鍵限定 `hotkey_app_filter_enabled` / `hotkey_app_target_exe` / `hotkey_app_target_label`、current_profile 等）
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

## 升級行為

- `config.json` 隨 release ZIP 更新（靜態區覆蓋 → 新技能 / items 自動帶入）
- `config_user.json` / `profiles/` 在 ZIP 內不存在 → 升級不會覆蓋使用者個人狀態
- 第一次安裝的使用者會由 `ConfigManager` 自建 `config_user.json`（從 `DEFAULT_USER_SETTINGS`）和預設 profile

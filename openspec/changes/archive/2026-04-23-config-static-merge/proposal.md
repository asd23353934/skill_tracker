## Problem

升級覆蓋安裝（含 in-app 自動更新）時，ZIP 內的 `config.json` 會直接覆蓋使用者本地版本，連帶把以下個人狀態重置：

- `settings.skill_start_x / skill_start_y / window_size`（技能視窗位置與大小）
- `settings.sound_volume / global_sound / global_alert_sound / enable_sound`
- `settings.hint_position_x / hint_position_y`（hotkey hint 顯示位置）
- `settings.alert_before_seconds`（全域提前秒）
- `settings.player_name / current_profile`
- `monsters[]`（自訂怪物列表，含 hotkey）
- `overlays[]`（自訂浮動圖片）

`docs/DATA_FORMAT.md` 早已規範「靜態區（skills/items）= 唯讀」「全域可變區（settings/monsters/overlays）= 不該被覆蓋」，但 `ConfigManager` 與 release pipeline 都把它們混在同一檔案，分區規則僅止於文件、未落實到程式。

## Root Cause

1. **單檔混合儲存**：`config.json` 同時含靜態 metadata 與全域可變狀態
2. **PyInstaller spec 整檔打包**：`('config.json', '.')` 無條件把開發者本機的 settings/monsters/overlays 也包進去
3. **`ConfigManager.load_config` 直接讀 `config.json`**：沒有「先看 user 版、否則用 bundled」的合併邏輯

結果：升級 = bundled 完整覆蓋本地 = user 全失。

## Proposed Solution

採用「靜態 + 可變」分檔 + ConfigManager 載入合併：

1. **新增 user 可變區檔案 `config_user.json`**（同層目錄）：
   - 內容只含 `{"settings": {...}, "monsters": [...], "overlays": [...]}`
   - 不在 git tracking、不在 PyInstaller datas
   - 第一次啟動由 ConfigManager migration helper 自動建立

2. **改寫 `ConfigManager.load_config()`**（src/infrastructure/config_manager.py）：
   - 一律讀 `config.json` 取靜態區（skills / items）
   - 若 `config_user.json` 存在 → 取其 settings / monsters / overlays 覆蓋 in-memory config
   - 若 `config_user.json` 不存在 → 從現有 `config.json` 抽出 settings / monsters / overlays 寫成 `config_user.json`（一次性 migration）

3. **改寫 `ConfigManager.save()`**：
   - 寫回 `config_user.json` 只含 settings / monsters / overlays
   - `config.json` 內的 settings / monsters / overlays 在記憶體可變、但**不寫回磁碟**（保持 ZIP 內 bundled 版乾淨）

4. **release pipeline strip 腳本** `scripts/strip_config_for_release.py`：
   - 在 `pyinstaller skill_tracker.spec` 之前執行
   - 讀 `config.json` → settings 重置為文件規定的最小欄位、monsters 留空 list、overlays 留空 list、原檔備份成 `config.json.dev_backup`
   - PyInstaller build 完恢復備份（`.dev_backup` → `config.json`）
   - 開發者本機平日使用不受影響

5. **PyInstaller spec 不變**：`config.json` 仍打包，但 strip 後內容只有純靜態 + 空白可變區骨架

6. **既有 user 升級行為**（重要）：
   - 舊版 user 從未產生 `config_user.json` → 新版第一次啟動 ConfigManager 會從現有 `config.json`（**user 本地的、未被 ZIP 覆蓋的**）抽 settings/monsters/overlays 寫成 `config_user.json`
   - **問題**：升級 ZIP 已先用 stripped `config.json` 覆蓋了 user 的 → 來不及抽
   - **解法**：migration helper 改為偵測升級時 ZIP 是否含「stripped 標記」（在 stripped config.json 加 `"_user_data_stripped": true` 標記），若 user 本地 `config.json` 有此標記但無 `config_user.json` → 不能 migrate，改提示「請從備份還原」 + 寫空白 user 檔
   - **更安全的解法**：發 strip 版前的最後一個 release 用一支 `pre_strip_migrator.py` 內嵌進 exe，user 升舊版 → 跑一次 → 自動把當時 config.json 的可變區搬到 config_user.json（搬完後即使下次升 strip 版也安全）。但這要先發一個過渡版本

## Non-Goals

- **不改 profile schema**：profiles/{name}.json 維持現狀。
- **不改 V1 / V2 UI**：所有設定對話框繼續 read/write 同樣的 `app.config_manager.set_settings(...)` API；ConfigManager 內部分檔對 UI 透明。
- **不引入雲端 / 跨機同步**：`config_user.json` 維持本地 only。
- **不調整 ConfigManager 公開 API**（`get_settings / set_settings / list_profiles / save / load_config`）：僅內部實作分檔，呼叫端不知道。
- **不抽 settings 到 profile**：仍是全域可變區（不同 profile 共用）。
- **不打包過渡 migrator**（即上面「更安全的解法」）：若 user 從很舊版本直接跳這版，他們的 settings 會在升級瞬間遺失（已被 ZIP 覆蓋）。發布 changelog 必須明確警告這次「請先備份 config.json」。**這是 trade-off**，避免發兩個 release。

## Success Criteria

1. **新安裝**：第一次跑 → 自動建 config_user.json（settings 用 stripped config.json 內的 default、monsters/overlays 為空）；改設定後重啟 → 設定保留
2. **升級覆蓋（ZIP 解壓）**：
   - 已有 config_user.json 的 user → ZIP 內 stripped config.json 覆蓋本地 config.json，但 config_user.json 不在 ZIP → 完整保留 → 重啟所有設定都在
   - 沒有 config_user.json 但有舊 config.json 的 user（從這版第一次升級） → ZIP 已先覆蓋 → settings 遺失（在 changelog 警告）；首次啟動建空白 config_user.json
3. **開發者本機**：日常修改 settings 改本地 config_user.json，不會弄髒要 commit 的 config.json
4. **release ZIP 內 config.json**：settings 為 default minimal、monsters/overlays 為空 list

## Impact

- Affected code:
  - Modified:
    - `src/infrastructure/config_manager.py`（load/save 內部分檔；migration helper）
    - `docs/DATA_FORMAT.md`（補上 config_user.json 段落、解除「待修正」標記）
    - `.gitignore`（補 `config_user.json`；config.json 仍 tracked）
  - New:
    - `scripts/strip_config_for_release.py`（release-time strip + backup/restore）
    - `verify_config_migration.py`（單元驗證 migration / 分檔讀寫）
  - Removed: 無

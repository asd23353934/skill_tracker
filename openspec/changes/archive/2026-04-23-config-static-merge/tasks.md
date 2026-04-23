## 1. 前置探查與驗證

- [x] 1.1 讀 `src/infrastructure/config_manager.py` 的 `load_config` / `save` / `set_settings` 路徑，記下所有寫 `self.config` 的位置
- [x] 1.2 跑既有 verify（verify_skill_page_v2 / monster / toast / settings_dialog / profile_crud）全綠作 baseline

## 2. Global mutable zone stored in separate config_user.json

- [x] 2.1 落實 Requirement「Global mutable zone stored in separate config_user.json」第 1 步：在 `ConfigManager.__init__` 加 `self.user_config_path = os.path.join(os.path.dirname(config_path), "config_user.json")`，改寫 `load_config` 流程：先讀 `config.json` 進 `self.config`，再 read-or-migrate user 可變區
- [x] 2.2 加 `_load_or_migrate_user_config()`：若 `config_user.json` 存在 → 讀入後用 dict update 蓋 `self.config["settings"] / monsters / overlays`；若不存在 → 檢查 `config.json` 是否有 `_user_data_stripped` 標記，無標記則從 `self.config` 抽出這三欄寫成 `config_user.json`（migration from pre-split 版本），有標記則建空白 user 檔（user 首次用新版 + 已被 stripped config.json 覆蓋 — 見 §4）
- [x] 2.3 改寫 `ConfigManager.save()`：原本寫整個 `self.config` 回 `config.json`；改為把 `self.config` 的 settings / monsters / overlays 切出來寫 `config_user.json`，`config.json` 保持檔案不變（不改磁碟）
- [x] 2.4 `set_settings` / `set_current_profile` 等 mutator 維持原 API，寫到 in-memory self.config；後續呼叫 save() 會落到 user 檔
- [x] 2.5 import smoke：`python -c "from src.infrastructure.config_manager import ConfigManager; print('OK')"` 通過

## 3. ConfigManager skips migration when config.json marked stripped

- [x] 3.1 落實 Requirement「ConfigManager skips migration when config.json marked stripped」：在 `_load_or_migrate_user_config` 第 2 步邏輯內加「is_stripped = self.config.get('_user_data_stripped') is True」判斷分支；is_stripped + 無 user 檔 → 建空 user 檔（settings 使用 documented default hard-coded dict、monsters=[] / overlays=[]）
- [x] 3.2 documented default dict 內容：player_name="玩家1"、skill_start_x/y 由 QApplication.primaryScreen 計算中心、enable_sound=True、sound_volume=100、window_size=64、alert_before_seconds=0、hint_position_x/y=0 / 0、global_sound="" / global_alert_sound=""、current_profile="預設配置"
- [x] 3.3 若 `QApplication` 尚未建（ConfigManager 很早 init），skill_start_x/y 先用 None 寫入 config_user.json；運行時 AppCoreMixin._load_profile_state 已有 primary_screen fallback，不會崩

## 4. Release ZIP ships sanitized config.json

- [x] 4.1 落實 Requirement「Release ZIP ships sanitized config.json」：新建 `scripts/strip_config_for_release.py`，argparse 支援 `--restore`
- [x] 4.2 正向模式（無 flag）：讀 `config.json` → 備份為 `config.json.dev_backup`（若已存在則 print warning 並 exit 1，避免蓋掉上一次的）→ 覆蓋 `config.json`：保留 skills / items、settings 改為 documented default dict、monsters=[]、overlays=[]、頂層加 `_user_data_stripped=true`
- [x] 4.3 `--restore` 模式：若 `config.json.dev_backup` 存在 → `os.replace(backup, config.json)`；若不存在 → exit 1 + print warning
- [x] 4.4 手動驗證：在乾淨 git working tree 執行 strip → 看 config.json 被改、備份存在；執行 --restore → 恢復原樣、備份消失；`git diff config.json` 應為空

## 5. PyInstaller 整合

- [x] 5.1 `skill_tracker.spec` 不動（`('config.json', '.')` 保留）— 打包流程改為：strip → pyinstaller → restore
- [x] 5.2 更新 README / docs/RELEASE.md：發布 build 指令序列從 `pyinstaller skill_tracker.spec` 改為：
     ```
     python scripts/strip_config_for_release.py
     pyinstaller skill_tracker.spec
     python scripts/strip_config_for_release.py --restore
     ```
- [x] 5.3 `.gitignore` 加入 `config.json.dev_backup`（避免誤 commit 備份檔）

## 6. 文件同步

- [x] 6.1 `docs/DATA_FORMAT.md`：把「已知問題」章節的 config_user.json 分檔記錄更新為「已修復」；加上 ConfigManager 分檔邏輯說明
- [x] 6.2 `.gitignore` 加 `config_user.json`（user 可變區、每台機器獨立）
- [x] 6.3 說明 user 本地是否要保留 `config.json` 為 tracked：是（靜態區隨版本更新），但注意 commit 前跑 strip（見 §7）

## 7. 開發者 workflow 保障

- [x] 7.1 新增 pre-commit 提示（README 一段）：「如 config.json 被動到，commit 前先跑 strip 腳本確認」
- [x] 7.2 選配：加 `scripts/check_config_clean.py` 檢查 `config.json` 的 monsters/overlays 是否為空、settings 是否為 default → CI 或 pre-commit hook 呼叫（此 task 選做，若做完再加到 tasks.md；不做則此 task 結束不勾選）

## 8. 驗證腳本

- [x] 8.1 新建 `verify_config_migration.py`；建暫時 tmpdir 模擬 `config.json` + 各種 user 檔情境
- [x] 8.2 test_fresh_install_creates_user_file: tmpdir 只放 config.json（含 stripped marker）→ ConfigManager 初始化 → assert `config_user.json` 被建立、含 default settings、monsters=[]、overlays=[]
- [x] 8.3 test_migration_from_pre_split: tmpdir 只放 config.json（無 stripped marker + 含 sound_volume=50、monsters=[{...}]、overlays=[{...}]） → ConfigManager 初始化 → assert `config_user.json` 被建、含那三欄、值等同遷入前
- [x] 8.4 test_existing_user_file_wins: tmpdir 放 config.json（含 stripped marker + settings.sound_volume=100）+ config_user.json（settings.sound_volume=50）→ init → `cm.get_settings("sound_volume") == 50`
- [x] 8.5 test_save_writes_only_user_file: init → set_settings("sound_volume", 75) + save() → read config.json byte-for-byte 不變、read config_user.json 含 sound_volume=75
- [x] 8.6 test_static_zone_refreshed_from_bundled: tmpdir 先跑 init（此時 config_user.json 被建）→ 新寫 config.json skills 加一筆 new_skill → 重 init → `cm.config["skills"]` 含 new_skill（bundled 更新生效）、settings / monsters / overlays 來自 user 檔（不受影響）
- [x] 8.7 全腳本 exit 0

## 9. 手動驗證

- [x] 9.1 `python scripts/strip_config_for_release.py` → 看 config.json.dev_backup 存在、config.json settings 乾淨、monsters=[] overlays=[]
- [x] 9.2 `python scripts/strip_config_for_release.py --restore` → 備份消失、config.json 回到 strip 前狀態、`git diff config.json` 空
- [x] 9.3 模擬全新安裝：刪本機 config_user.json，重跑 strip → pyinstaller → restore；跑 dist 內 exe → exit 後看 dist/skill_tracker/_internal/ 沒 config_user.json（沒跑夠久）→ 跑第二次 → 檢查 `_internal/config_user.json` 存在且 settings=default
- [x] 9.4 模擬升級：保留 _internal/config_user.json（手動改 sound_volume=20）、重 build 覆蓋 _internal/config.json → 跑 exe → 開 settings dialog → 音量應顯示 20（保留）
- [x] 9.5 V1 與 V2 雙路徑各跑一次，全部 settings / monsters / overlays 操作無 regression

## 10. 收尾

- [x] 10.1 跑 `/simplify` 與 `/spectra-audit`
- [x] 10.2 同步 docs/PROJECT.md：`src/infrastructure/config_manager.py` 條目補「+ config_user.json 分檔」；`scripts/` 條目新增 strip_config_for_release.py 行
- [x] 10.3 commit + archive
- [x] 10.4 release changelog 加警告：「從 v<previous> 直接升級此版會在升級瞬間丟失 config.json 內的 settings / monsters / overlays；請先備份 config.json 或手動 copy 為 config_user.json 再升級」

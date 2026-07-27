# 版本管理與發布

## 發布 — 只有一條路

```bash
python release.py
```

`release.py` 是**唯一**的打包入口，從前置檢查跑到產出 ZIP，中間沒有需要人工介入
的步驟。不要手動去跑底下的個別步驟 —— 流程分散正是 v4.10.2 事故的成因。

發布前先跑：

```bash
python bump_version.py
```

（版本遞增是決策，刻意留在流程外；`release.py` 會印出即將發布的版本號。）

### release.py 做了什麼

| 步驟 | 內容 |
|------|------|
| 1. 前置檢查 | images/ 有圖示、icon.ico 存在、overlays/ 存在、**所有 .ps1 帶 UTF-8 BOM**、沒有殘留的 `config.json.dev_backup`、列出 dist/ 內待排除的使用者資料 |
| 2. strip | `config.json` 的 user 可變區重設為出廠預設並加上 `_user_data_stripped` 標記 |
| 3. build | `pyinstaller skill_tracker.spec` |
| 4. restore | 還原 `config.json` —— 放在 `finally`，**build 失敗也一定會還原** |
| 5. zip | 排除所有使用者資料，壓完回讀 ZIP 驗證；驗出使用者資料就刪檔並中止 |

選項：`--no-build` 跳過 PyInstaller，直接用現有 `dist/` 重新打包。

### 為什麼要有這些防護

v4.10.2 的事故：使用者資料當時寫在 PyInstaller 的 `_internal/`，開發者在 `dist/`
跑 exe 驗證後生成的 `config_user.json`（全預設值）被打包進 ZIP，
`update_launcher.ps1` 解壓時逐檔覆寫，使用者的設定全被打回預設。

現在有三道獨立防線：

1. **落點**：使用者資料一律放執行檔同層，`ConfigManager` 的 `user_dir` 預設就是
   正確位置（省略參數不會退回舊的危險落點）
2. **打包排除**：`zip_release.py` 依 `helpers.USER_DATA_FILES` / `USER_DATA_DIRS` 排除
3. **產物驗證**：壓完回讀 ZIP，驗出使用者資料就刪檔、中止發布

> **新增任何一種使用者可寫檔案時，必須同步加進 `src/infrastructure/helpers.py` 的
> `USER_DATA_FILES` / `USER_DATA_DIRS`。** 那是單一來源，漏加就會重演同一個 bug。

---

## 版本管理

- 版本號唯一定義在 `version.py` 的 `VERSION` 變數
- `version.py` 也提供 `get_version()`、`get_changelog()` 等工具函數
- Changelog 格式: emoji 標記 (🎉 新版 / ✨ 功能 / 🐛 修復 / ✅ 任務)
- 使用 `bump_version.py` 自動遞增版本

---

## 開發常用指令

```bash
# 執行
python main.py

# 安裝依賴
pip install -r requirements.txt

# 跑單元測試（純邏輯層：domain / infrastructure）
python -m pytest tests/ -v
```

UI 層以根目錄的 `verify_*.py` 腳本驗證（各自獨立執行，全綠 exit 0）。

---

## 個別步驟（僅供除錯，正常發布不要單獨跑）

`release.py` 內部會依序呼叫這些；單獨跑的唯一時機是流程中斷後要手動收尾。

```bash
# strip / restore config.json 的 user 可變區
python scripts/strip_config_for_release.py
python scripts/strip_config_for_release.py --restore

# 打包
pyinstaller skill_tracker.spec

# 壓縮為 ZIP（含使用者資料排除 + 產物驗證）
python zip_release.py
```

⚠️ strip 之後若沒 restore，`config.json` 會留在出廠預設狀態被 commit 掉。
`release.py` 用 `finally` 保證還原，手動跑就得自己記得。

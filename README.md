# 🎮 技能追蹤器 - Artale 楓之谷

單機版技能冷卻追蹤工具

---

## 🚀 快速開始

### 1. 安裝依賴
```bash
pip install -r requirements.txt
```

### 2. 運行程式
```bash
python main.py
```

---

## 📦 發布前注意

發布只有一條路：

```bash
python release.py
```

前置檢查 → strip config → build → restore → zip，一條龍跑完，不要單獨跑底下的步驟。

- `settings` / `monsters` / `overlays` 從 `config-static-merge` 起儲存到 `config_user.json`（已在 `.gitignore`）
- 打包後 `config_user.json` / `profiles/` / `potion_saves/` 一律放在**執行檔同層**，不在 `_internal/`
  —— 後者是 PyInstaller bundle，更新解壓會逐檔覆寫，user 資料放進去會被洗掉
- **新增任何使用者可寫檔案時，必須同步加進 `src/infrastructure/helpers.py` 的
  `USER_DATA_FILES` / `USER_DATA_DIRS`** —— 那是打包排除的單一來源，漏加就會在使用者更新時覆蓋掉他們的資料
- 完整流程與防線說明見 `docs/RELEASE.md`

---

## ✨ 功能特色

- ✅ 技能倒數追蹤
- ✅ 快捷鍵設定
- ✅ 秒數自訂
- ✅ 常駐技能
- ✅ 配置管理
- ✅ 技能重置
- ✅ 提示音禁音（完成 / 提前分別開關，每技能可單獨靜音）
- ✅ 語音提示（所有技能完成 / 提前自動念出名稱，可改音效或靜音）
- ✅ 快捷鍵限定前景視窗（只在指定遊戲視窗觸發）
- ✅ 指令快速複製（Artale 遊戲指令一鍵複製到剪貼簿，需名稱者以名稱 chip 增刪改、各指令獨立記憶）
- ✅ 指令快捷鍵（可綁實體按鍵快速複製指令，needs_name 指令的每個名稱可各自綁一把鍵；總開關可暫時關閉觸發；快捷鍵小窗／複製回饋皆為螢幕級浮動提示）
- ✅ 練功收支分析（支出藥水／收入楓幣商店與物品取得，可選練功地圖自動帶出掉落，算出淨收益）
- ✅ 經驗值計算器（輸入等級／經驗％／目標等級＋練功效率，估算升級還需經驗與時間）
- ✅ 更新日記（側邊欄版本號可點擊，開啟對話框依版本瀏覽完整更新紀錄）

---

詳細文檔：`docs/PROJECT.md` / `docs/ARCHITECTURE.md` / `docs/DATA_FORMAT.md` / `docs/RELEASE.md`

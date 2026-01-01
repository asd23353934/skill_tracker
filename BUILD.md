# 技能追蹤器 - 打包說明

## 環境需求
```bash
pip install pyinstaller pillow pynput
```

## 打包步驟

### Step 0: 發布前清理（重要！）
```bash
# 自動清理到初始狀態
python clean_for_release.py

# 檢查是否正確
python check_release.py
```

**清理腳本會：**
- ✅ 恢復 config.json 到初始狀態
- ✅ 刪除所有測試配置，只保留預設配置.json
- ✅ 清空預設配置的內容
- ✅ 刪除 __pycache__ 和打包檔案

### Step 1: 打包

#### 方法 1：使用 spec 文件（推薦）
```bash
pyinstaller skill_tracker.spec
```

#### 方法 2：直接打包（目錄模式）
```bash
pyinstaller --name=技能追蹤器 ^
    --onedir ^
    --windowed ^
    --icon=icon.ico ^
    --add-data "images;images" ^
    --add-data "config.json;." ^
    --add-data "profiles;profiles" ^
    --hidden-import=pynput.keyboard._win32 ^
    --hidden-import=pynput.mouse._win32 ^
    main.py
```

### Step 2: 測試
```bash
cd dist/技能追蹤器
技能追蹤器.exe
```

**測試項目：**
- ✅ 程式正常啟動
- ✅ 顯示「預設配置」
- ✅ 所有技能無快捷鍵
- ✅ 所有技能顯示原始秒數（灰色）

### Step 3: 壓縮發布
```bash
# 壓縮整個資料夾
dist/技能追蹤器/ → 技能追蹤器_v1.0.1.zip
```

## 打包後文件結構
```
dist/技能追蹤器/
├── 技能追蹤器.exe        ← 主程式
├── config.json           ← 技能初始值（可編輯）
├── images/               ← 技能圖示資料夾
│   ├── bishop_holy_symbol.png
│   ├── snow_crystal.png
│   └── ...
├── profiles/             ← 配置檔案資料夾
│   └── 預設配置.json     ← 唯一的配置
├── _internal/            ← 程式依賴（自動生成）
└── ...其他 DLL 文件
```

## 初始狀態要求

### config.json
```json
{
  "settings": {
    "current_profile": "預設配置",  // ✅ 必須
    "skill_send": {},               // ✅ 空的
    "skill_receive": {},            // ✅ 空的
    "skill_permanent": {}           // ✅ 空的
  }
}
```

### profiles/
```
profiles/
└── 預設配置.json  // ✅ 只有這一個
```

### 預設配置.json
```json
{
  "hotkeys": {},             // ✅ 空的
  "send": {},                // ✅ 空的
  "receive": {},             // ✅ 空的
  "permanent": {},           // ✅ 空的
  "cooldown_overrides": {}   // ✅ 空的
}
```

## 程式啟動行為

### 情境 1：正常啟動（預設配置存在）
```
1. 讀取 config.json
2. current_profile = "預設配置"
3. 檢查 profiles/預設配置.json 存在 ✅
4. 載入預設配置（全部空值）
5. 所有技能使用 config.json 的初始值
```

### 情境 2：預設配置不存在
```
1. 讀取 config.json
2. current_profile = "預設配置"
3. 檢查 profiles/預設配置.json 不存在 ❌
4. 自動創建預設配置.json
5. 載入預設配置
```

### 情境 3：當前配置不存在
```
1. 讀取 config.json
2. current_profile = "測試配置"
3. 檢查 profiles/測試配置.json 不存在 ❌
4. ⚠️ 當前配置無效
5. 自動切換到 "預設配置"
6. 更新 config.json: current_profile = "預設配置"
```

### 情境 4：完全初始狀態
```
1. 讀取 config.json
2. current_profile = ""（空的）
3. 自動設定為 "預設配置"
4. 創建預設配置.json（如果不存在）
5. 載入預設配置
```

## 自動修正機制

**ConfigManager.ensure_default_profile() 會：**
1. ✅ 確保「預設配置」存在
2. ✅ 檢查當前配置是否有效
3. ✅ 如果無效，自動切換到預設配置
4. ✅ 如果未設定，自動設定為預設配置

**控制台訊息：**
```
✅ 已創建預設配置
⚠️ 當前配置 'XXX' 不存在，自動切換到 '預設配置'
ℹ️ 未設定當前配置，使用 '預設配置'
```

## 為什麼使用目錄模式？

**優點：**
1. ✅ 使用者可以自行編輯 `config.json` 新增技能
2. ✅ 使用者可以自行替換 `images/` 中的圖示
3. ✅ 配置檔案 `profiles/` 獨立存放，方便備份
4. ✅ 啟動速度較快（不需解壓）
5. ✅ 更新技能只需替換 `config.json`

## 使用者可自訂項目

### 1. 新增技能
編輯 `config.json`，在 `skills` 陣列中新增：
```json
{
  "id": "new_skill",
  "name": "新技能",
  "icon": "new_skill.png",
  "cooldown": 120,
  "hotkey": "",
  "category": "player",
  "subcategory": "測試"
}
```

### 2. 替換圖示
將新圖示放入 `images/` 資料夾，命名對應即可

### 3. 備份配置
複製整個 `profiles/` 資料夾

## 發布檢查清單

運行檢查腳本：
```bash
python check_release.py
```

**必須通過：**
- ✅ config.json 處於初始狀態
- ✅ current_profile = "預設配置"
- ✅ skill_send/receive/permanent = {}
- ✅ profiles/ 只有預設配置.json
- ✅ 預設配置.json 內容全部為空
- ✅ images/ 包含所有圖示
- ✅ icon.ico 存在

## 常見問題

### Q: 打包後 profiles/ 資料夾是空的？
A: 使用 spec 文件打包，確保有 `('profiles', 'profiles')`

### Q: 程式啟動後不是預設配置？
A: 運行 `clean_for_release.py` 清理

### Q: 如何測試自動修正？
A: 
1. 刪除 `profiles/預設配置.json`
2. 啟動程式
3. 應該自動創建並使用預設配置

### Q: 使用者刪除所有配置會怎樣？
A: 程式會自動創建預設配置，不會崩潰

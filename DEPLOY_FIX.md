# Render.com 部署配置

## 正確的部署設定

### 專案結構
```
SkillTracker/
├── relay_server.py          ← 伺服器文件（需要在根目錄）
├── requirements.txt         ← 依賴文件
└── render.yaml             ← Render 配置（可選）
```

### 方法 1: 直接部署（推薦）

**Step 1: 準備文件**

確保 `relay_server.py` 在專案根目錄。

**Step 2: Render.com 設定**

```
Build Command: (留空，不需要)
Start Command: python relay_server.py --host 0.0.0.0 --port $PORT
```

⚠️ **注意**: 路徑是 `relay_server.py`，不是 `/opt/render/project/src/relay_server.py`

---

### 方法 2: 使用 render.yaml（自動化）

創建 `render.yaml` 在專案根目錄：

```yaml
services:
  - type: web
    name: skilltracker-relay
    env: python
    plan: free
    buildCommand: ""
    startCommand: python relay_server.py --host 0.0.0.0 --port $PORT
    envVars:
      - key: PYTHON_VERSION
        value: 3.10.0
```

---

### 方法 3: 單文件部署

如果你只想部署中繼伺服器，創建一個獨立的 repo：

```bash
mkdir skilltracker-relay
cd skilltracker-relay

# 複製伺服器文件
cp /path/to/SkillTracker/relay_server.py .

# 創建 requirements.txt（可以是空的）
touch requirements.txt

# Git
git init
git add .
git commit -m "Initial commit"
git push
```

然後在 Render.com 連接這個 repo。

---

### 疑難排解

#### 錯誤 1: No such file or directory

**原因**: Render 找不到文件

**解決**:
```bash
# 檢查文件是否在根目錄
ls -la
# 應該看到 relay_server.py

# 如果文件在子目錄，修改 Start Command:
cd src && python relay_server.py --host 0.0.0.0 --port $PORT
```

#### 錯誤 2: Module not found

**原因**: 缺少依賴

**解決**: 確保 `requirements.txt` 存在（即使是空的）

---

## Railway.app 部署（更簡單，推薦）

Railway.app 會自動檢測 Python 文件。

### 快速部署

**方法 1: GitHub**
```
1. 上傳 relay_server.py 到 GitHub
2. Railway → New Project → Deploy from GitHub
3. 選擇 repo
4. 自動部署 ✅
```

**方法 2: CLI**
```bash
# 安裝 Railway CLI
npm i -g @railway/cli

# 登入
railway login

# 初始化
railway init

# 部署
railway up
```

**方法 3: 拖放**
```
1. Railway → New Project
2. 拖放 relay_server.py 文件
3. 自動部署 ✅
```

---

## 最簡單的方法：使用公共中繼伺服器

如果部署太麻煩，我可以提供一個備用方案：使用 **ngrok** 臨時部署。

### ngrok 快速部署

```bash
# 1. 下載 ngrok
# Windows: https://ngrok.com/download

# 2. 本地運行伺服器
python relay_server.py --host 127.0.0.1 --port 8888

# 3. 開啟新終端，運行 ngrok
ngrok tcp 8888

# 4. 獲得公開地址
# 例如: tcp://0.tcp.ngrok.io:12345
```

**優點**: 超級簡單，1 分鐘完成
**缺點**: 臨時地址，重啟後會變

---

## 推薦方案排序

1. **Railway.app** ⭐⭐⭐⭐⭐
   - 最簡單
   - 永久免費
   - 自動配置

2. **本地 + ngrok** ⭐⭐⭐⭐☆
   - 快速測試
   - 不需要註冊
   - 臨時使用

3. **Render.com** ⭐⭐⭐☆☆
   - 免費
   - 需要正確配置
   - 可能休眠

4. **Oracle Cloud 永久免費** ⭐⭐⭐⭐☆
   - 完全免費
   - 需要技術知識
   - 最穩定

---

## 立即可用的測試伺服器

我幫你創建一個測試用的配置：

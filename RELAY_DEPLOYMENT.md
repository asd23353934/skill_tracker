# 中繼伺服器部署指南

## 🎯 目的

提供一個**免費的中繼伺服器**，讓用戶無需任何設定就能跨網路連線。

---

## 🆓 免費部署選項

### 方案 1: Railway.app（推薦）

**優點：**
- ✅ 完全免費（每月 500 小時）
- ✅ 自動部署
- ✅ 固定網址
- ✅ 簡單

**步驟：**

1. 註冊 Railway.app
   ```
   https://railway.app/
   ```

2. 點擊 "New Project" → "Deploy from GitHub repo"

3. 上傳代碼（或使用命令行）:
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

4. 配置環境變數:
   ```
   PORT=8888
   ```

5. 獲取網址:
   ```
   railway domain
   # 例如: https://skilltracker-relay.railway.app
   ```

---

### 方案 2: Render.com

**優點：**
- ✅ 免費方案
- ✅ 自動 SSL
- ✅ 簡單部署

**步驟：**

1. 註冊 Render.com
   ```
   https://render.com/
   ```

2. New → Web Service

3. 連接 GitHub

4. 設定:
   ```
   Build Command: pip install -r requirements.txt
   Start Command: python relay_server.py --host 0.0.0.0 --port $PORT
   ```

5. 部署完成後獲取網址

---

### 方案 3: Heroku（限制較多）

**缺點：**
- ⚠️ 需要信用卡驗證
- ⚠️ 休眠機制（不活躍時會休眠）

**步驟：**

1. 創建 `Procfile`:
   ```
   web: python relay_server.py --host 0.0.0.0 --port $PORT
   ```

2. 創建 `runtime.txt`:
   ```
   python-3.10.0
   ```

3. 部署:
   ```bash
   heroku create skilltracker-relay
   git push heroku main
   ```

---

## 🏠 自己架設

### VPS 方案

**適合：**
- 想完全控制
- 有固定 IP
- 熟悉 Linux

**推薦 VPS：**
- AWS Lightsail ($3.50/月)
- DigitalOcean ($4/月)
- Vultr ($2.50/月)
- Oracle Cloud（永久免費方案）

**部署步驟：**

```bash
# 1. SSH 連線到 VPS
ssh user@your-vps-ip

# 2. 安裝 Python
sudo apt update
sudo apt install python3 python3-pip

# 3. 上傳代碼
scp relay_server.py user@your-vps-ip:~/

# 4. 運行
python3 relay_server.py --host 0.0.0.0 --port 8888

# 5. 使用 systemd 設定開機自啟（可選）
sudo nano /etc/systemd/system/relay.service
```

**systemd 配置：**
```ini
[Unit]
Description=SkillTracker Relay Server
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu
ExecStart=/usr/bin/python3 /home/ubuntu/relay_server.py
Restart=always

[Install]
WantedBy=multi-user.target
```

**啟用服務：**
```bash
sudo systemctl enable relay
sudo systemctl start relay
sudo systemctl status relay
```

---

## 📝 配置客戶端

修改 `src/core/relay_client.py`:

```python
RELAY_SERVERS = [
    # 你的 Railway 伺服器
    ('skilltracker-relay.railway.app', 443),  # Railway 使用 HTTPS
    
    # 或你的 Render 伺服器
    ('skilltracker-relay.onrender.com', 443),
    
    # 或你的 VPS
    ('your-vps-ip', 8888),
    
    # 本地測試
    ('127.0.0.1', 8888),
]
```

---

## 🧪 測試

### 測試伺服器

```bash
# 啟動伺服器
python relay_server.py

# 應該看到:
# ============================================================
# 🌐 中繼伺服器啟動中...
# ============================================================
# 監聽地址: 0.0.0.0:8888
# ============================================================
# ✅ 伺服器已啟動，等待連線...
```

### 測試客戶端

```bash
# 終端 1: 客戶端 1
python -c "from src.core.relay_client import test_relay; test_relay()"

# 終端 2: 客戶端 2  
python -c "from src.core.relay_client import test_relay; test_relay()"
```

---

## 🔒 安全性

### 基本安全措施

1. **限制連線數**
   ```python
   # relay_server.py
   MAX_CLIENTS_PER_ROOM = 10
   MAX_ROOMS = 100
   ```

2. **添加認證**（可選）
   ```python
   # 要求 API Key
   def verify_api_key(key):
       return key == "your-secret-key"
   ```

3. **速率限制**
   ```python
   from collections import defaultdict
   import time
   
   rate_limits = defaultdict(list)
   
   def rate_limit(ip, max_requests=10, window=60):
       now = time.time()
       requests = rate_limits[ip]
       # 清除舊記錄
       requests = [t for t in requests if now - t < window]
       # 檢查限制
       if len(requests) >= max_requests:
           return False
       requests.append(now)
       rate_limits[ip] = requests
       return True
   ```

---

## 💰 成本估算

| 方案 | 成本 | 性能 | 適用人數 |
|------|------|------|---------|
| Railway.app | 免費 | 中 | < 10 人 |
| Render.com | 免費 | 中 | < 10 人 |
| Oracle Cloud | 免費 | 高 | < 50 人 |
| AWS Lightsail | $3.5/月 | 高 | < 100 人 |
| DigitalOcean | $4/月 | 高 | < 100 人 |

---

## 🎯 推薦方案

### 個人使用（< 5 人）
→ **Railway.app**（免費、簡單）

### 小團隊（5-20 人）
→ **Render.com**（免費、穩定）

### 公開使用（20+ 人）
→ **Oracle Cloud 永久免費方案**（免費但需要設定）

### 商業用途
→ **AWS/DigitalOcean**（付費但可靠）

---

## 📊 部署檢查清單

- [ ] 伺服器已部署並運行
- [ ] 可以從外網訪問
- [ ] 防火牆已開放端口
- [ ] 客戶端配置了正確的伺服器地址
- [ ] 測試連線成功
- [ ] （可選）設定 SSL/TLS
- [ ] （可選）設定監控和日誌
- [ ] （可選）設定自動重啟

---

## 🆘 常見問題

### Q: Railway 免費額度夠用嗎？
A: 夠用。500 小時/月 = 每天 16.6 小時，足夠個人或小團隊使用。

### Q: 伺服器會休眠嗎？
A: Railway 不會，Render 免費方案會（15 分鐘無活動）。

### Q: 需要固定 IP 嗎？
A: 不需要，使用域名即可。

### Q: 延遲會高嗎？
A: 比 P2P 稍高（+50-100ms），但對技能追蹤器影響不大。

### Q: 可以多人共用一個伺服器嗎？
A: 可以，伺服器支援多個房間同時運行。

---

最後更新: 2025-01-01

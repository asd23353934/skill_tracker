# 🔧 中繼伺服器客戶端配置速查表

## 快速配置

部署完中繼伺服器後，只需要修改一個文件：

**`src/core/relay_client.py`** 的第 14-24 行

---

## 配置範例

### 使用 Railway.app

```python
RELAY_SERVERS = [
    # Railway 伺服器（自動 HTTPS）
    ('your-app-name.up.railway.app', 443),
]
```

**如何獲取地址：**
1. Railway Dashboard → 你的專案
2. Settings → Generate Domain
3. 複製網址（例如：`skilltracker-relay.up.railway.app`）
4. 使用端口 443（Railway 自動提供 HTTPS）

---

### 使用 Render.com

```python
RELAY_SERVERS = [
    # Render 伺服器
    ('your-app-name.onrender.com', 443),
]
```

**如何獲取地址：**
1. Render Dashboard → 你的服務
2. 複製網址（例如：`skilltracker-relay.onrender.com`）
3. 使用端口 443

---

### 使用 ngrok

```python
RELAY_SERVERS = [
    # ngrok 地址（每次都會變）
    ('0.tcp.ngrok.io', 12345),  # ← 端口號每次不同
]
```

**如何獲取地址：**
1. 運行 `ngrok tcp 8888`
2. 看到類似：`Forwarding: tcp://0.tcp.ngrok.io:12345`
3. 使用：`0.tcp.ngrok.io` 和端口 `12345`

---

### 使用自己的 VPS

```python
RELAY_SERVERS = [
    # VPS 伺服器
    ('123.45.67.89', 8888),  # 你的 VPS IP
]
```

---

### 多個備用伺服器

```python
RELAY_SERVERS = [
    # 主要伺服器
    ('main-server.railway.app', 443),
    
    # 備用伺服器
    ('backup-server.onrender.com', 443),
    
    # 本地測試
    ('127.0.0.1', 8888),
]
```

程式會按順序嘗試連線，直到成功。

---

## 完整配置文件

**`src/core/relay_client.py`** 完整版：

```python
"""
中繼伺服器客戶端
用於 NAT 穿透失敗時的備用方案
"""

import socket
import json
import threading
import time


class RelayClient:
    """中繼伺服器客戶端"""
    
    # ===============================================
    # ⬇️ 只需要修改這裡 ⬇️
    # ===============================================
    RELAY_SERVERS = [
        # 你的中繼伺服器地址
        ('your-server.railway.app', 443),
        
        # 本地測試（可選）
        ('127.0.0.1', 8888),
    ]
    # ===============================================
    # ⬆️ 修改完成 ⬆️
    # ===============================================
    
    # ... 其他代碼不用改 ...
```

---

## 測試配置

修改完成後，測試連線：

```bash
# 在專案目錄執行
python -c "from src.core.relay_client import test_relay; test_relay()"
```

**成功的話會看到：**
```
🔗 嘗試連線到中繼伺服器: your-server.railway.app:443
✅ 已連線到中繼伺服器
   房間: TEST123
   角色: 主機
```

**失敗的話會看到：**
```
🔗 嘗試連線到中繼伺服器: your-server.railway.app:443
❌ 連線失敗: [Errno 111] Connection refused
```

如果失敗，檢查：
1. 伺服器地址是否正確
2. 伺服器是否正在運行
3. 端口是否正確（Railway/Render 用 443，ngrok 用動態端口）

---

## 常見錯誤

### 錯誤 1: Connection refused

**原因**: 伺服器未運行或地址錯誤

**解決**:
```
1. 確認伺服器正在運行
2. 檢查地址和端口是否正確
3. 嘗試用瀏覽器訪問地址（應該看到連線錯誤，但至少證明地址可達）
```

### 錯誤 2: Connection timeout

**原因**: 網路問題或防火牆

**解決**:
```
1. 檢查本地網路連線
2. 檢查防火牆設定
3. 嘗試使用不同網路（手機熱點）
```

### 錯誤 3: Name or service not known

**原因**: 域名錯誤

**解決**:
```
1. 確認域名拼寫正確
2. 檢查是否包含 http:// 或 https://（不要加）
3. 確認域名已生效（新域名可能需要等待）
```

---

## 快速除錯

```bash
# 測試伺服器是否可達
ping your-server.railway.app

# 測試端口是否開放（Windows）
telnet your-server.railway.app 443

# 測試端口是否開放（Mac/Linux）
nc -zv your-server.railway.app 443
```

---

## 提示

1. **Railway 和 Render 都使用 HTTPS**
   - 端口必須是 443
   - 不要用 8888

2. **ngrok 地址每次都會變**
   - 每次重啟 ngrok 都要更新配置
   - 考慮升級到付費版獲得固定地址

3. **可以配置多個伺服器**
   - 程式會自動嘗試下一個
   - 建議至少配置 2 個備用

4. **測試時先用本地**
   - 先在本地測試：`('127.0.0.1', 8888)`
   - 確認程式邏輯正確
   - 再部署到雲端

---

**需要幫助？**

參考完整文件：
- `DEPLOY_FIX.md` - 部署疑難排解
- `RELAY_DEPLOYMENT.md` - 詳細部署指南
- `relay-server-deploy/README.md` - 伺服器部署說明

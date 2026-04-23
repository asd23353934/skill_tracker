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
python main.py        # V2 UI（預設）
python main.py --v1   # V1 舊版 UI（保留 opt-in）
```

---

## 📦 發布前注意

- `settings` / `monsters` / `overlays` 從 `config-static-merge` 起儲存到 `config_user.json`（已在 `.gitignore`）
- 如有動到 `config.json`，commit 前可手動跑一次 `python scripts/strip_config_for_release.py` 確認 user 可變區乾淨；確認後 `--restore` 還原
- 完整打包流程見 `docs/RELEASE.md`

---

## ✨ 功能特色

- ✅ 技能倒數追蹤
- ✅ 快捷鍵設定
- ✅ 秒數自訂
- ✅ 常駐技能
- ✅ 配置管理
- ✅ 技能重置

---

詳細文檔：`docs/PROJECT.md` / `docs/ARCHITECTURE.md` / `docs/DATA_FORMAT.md` / `docs/RELEASE.md`

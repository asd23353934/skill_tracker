# 版本管理與發布

## 版本管理

- 版本號唯一定義在 `version.py` 的 `VERSION` 變數
- `version.py` 也提供 `get_version()`、`get_changelog()` 等工具函數
- Changelog 格式: emoji 標記 (🎉 新版 / ✨ 功能 / 🐛 修復 / ✅ 任務)
- 使用 `bump_version.py` 自動遞增版本

## 常用指令

```bash
# 執行
python main.py

# 安裝依賴
pip install -r requirements.txt

# 版本遞增（互動式）
python bump_version.py

# 發布前清理
python clean_for_release.py

# 發布前檢查
python check_release.py

# 打包
pyinstaller skill_tracker.spec

# 壓縮為 ZIP 發布檔
python zip_release.py
```

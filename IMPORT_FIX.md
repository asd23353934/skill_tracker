# 導入路徑修復說明

## 🐛 問題描述

```
ModuleNotFoundError: No module named 'src.utils.styles'
```

## 🔧 原因

刪除 `src/utils/` 和 `src/core/` 目錄中的重複文件後，部分文件仍使用舊的導入路徑：
- ❌ `from src.utils.styles import ...`
- ❌ `from src.utils.helpers import ...`

實際文件位置在：
- ✅ `src/ui/styles.py`
- ✅ `src/ui/helpers.py`

## ✅ 修復方法

### 自動修復（已完成）

批量替換所有 `src.utils` 為 `src.ui`：

```bash
find src/ui -name "*.py" -exec sed -i 's/from src\.utils\./from src.ui./g' {} \;
```

### 手動修復

如果需要手動修復，編輯以下文件：

1. **src/ui/main_window.py**
   ```python
   # 修改前
   from src.utils.styles import Colors, Fonts, Sizes
   from src.utils.helpers import resource_path
   
   # 修改後
   from src.ui.styles import Colors, Fonts, Sizes
   from src.ui.helpers import resource_path
   ```

2. **src/ui/components.py**
   ```python
   # 修改前
   from src.utils.styles import Colors, Sizes
   from src.utils.helpers import darken_color
   
   # 修改後
   from src.ui.styles import Colors, Sizes
   from src.ui.helpers import darken_color
   ```

3. **src/ui/skill_window.py**
   ```python
   # 修改前
   from src.utils.styles import Colors, Sizes
   
   # 修改後
   from src.ui.styles import Colors, Sizes
   ```

4. **src/ui/skill_manager.py**
   ```python
   # 修改前
   from src.utils.helpers import resource_path
   
   # 修改後
   from src.ui.helpers import resource_path
   ```

5. **src/ui/dialogs.py**
   ```python
   # 修改前
   from src.utils.styles import Colors, Fonts
   
   # 修改後
   from src.ui.styles import Colors, Fonts
   ```

## ✅ 驗證

運行檢查腳本：

```bash
python check_imports.py
```

預期輸出：
```
🔍 檢查 Python 文件導入...

✅ src/ui/main_window.py
✅ src/ui/components.py
✅ src/ui/dialogs.py
✅ src/ui/skill_window.py
✅ src/ui/skill_manager.py
✅ src/ui/config_manager.py
✅ src/ui/helpers.py
✅ src/ui/styles.py
✅ src/ui/updater.py

✅ 所有文件導入正確！
```

## 📦 最新版本

**SkillTracker_Standalone_Fixed.tar.gz** - 已修復導入問題

## 🎯 修復確認

- ✅ 所有 `src.utils.*` 改為 `src.ui.*`
- ✅ 刪除無用文件（skill_tracker.py, main.py）
- ✅ 通過導入檢查
- ✅ 無語法錯誤

## 🚀 現在可以運行

```bash
python main.py
```

或使用啟動腳本：

```bash
python run.bat  # Windows
./run.sh        # Linux/Mac
```

@echo off
chcp 65001 >nul
echo ========================================
echo 🚀 技能追蹤器 - 一鍵發布
echo ========================================
echo.

echo 📋 Step 1: 清理環境
python clean_for_release.py
if errorlevel 1 (
    echo ❌ 清理失敗！
    pause
    exit /b 1
)
echo.

echo 📋 Step 2: 檢查狀態
python check_release.py
if errorlevel 1 (
    echo ❌ 檢查未通過！
    pause
    exit /b 1
)
echo.

echo 📋 Step 3: 打包程式
pyinstaller skill_tracker.spec
if errorlevel 1 (
    echo ❌ 打包失敗！
    pause
    exit /b 1
)
echo.

echo ========================================
echo ✅ 發布完成！
echo ========================================
echo.
echo 📦 打包結果: dist\技能追蹤器\
echo.
echo 📋 接下來的步驟:
echo   1. 測試: cd dist\技能追蹤器 ^&^& 技能追蹤器.exe
echo   2. 壓縮為 ZIP
echo   3. 創建 GitHub Release
echo.
pause

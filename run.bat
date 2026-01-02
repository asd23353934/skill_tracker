@echo off
chcp 65001 >nul
echo ============================================================
echo 技能追蹤器啟動程式
echo ============================================================
echo.

echo [1/3] 清理 Python 緩存...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d" 2>nul
del /s /q *.pyc 2>nul
echo ✓ 緩存已清理

echo.
echo [2/3] 檢查依賴...
python -c "import tkinter" 2>nul
if errorlevel 1 (
    echo ✗ tkinter 未安裝
    pause
    exit /b 1
)

python -c "import requests" 2>nul
if errorlevel 1 (
    echo ✗ requests 未安裝，正在安裝...
    pip install requests
)
echo ✓ 依賴檢查完成

echo.
echo [3/3] 啟動程式...
echo ============================================================
echo.
python main.py

if errorlevel 1 (
    echo.
    echo ============================================================
    echo 程式執行出錯，按任意鍵查看詳細訊息...
    echo ============================================================
    pause
)

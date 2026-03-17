@echo off
chcp 65001 >nul

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python not found
    pause
    exit
)

pip install -r requirements.txt
pip install pyinstaller
pyinstaller skill_tracker.spec
if %errorlevel% neq 0 (
    echo PyInstaller failed
    pause
    exit
)

python zip_release.py

pause

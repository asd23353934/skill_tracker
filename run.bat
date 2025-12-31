@echo off
chcp 65001 >nul

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python not found
    pause
    exit
)

pip show pynput >nul 2>&1
if %errorlevel% neq 0 (
    pip install -r requirements.txt
)

python skill_tracker.py

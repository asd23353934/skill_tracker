@echo off
chcp 65001 >nul

echo Installing required packages...
pip install -r requirements.txt

echo.
echo Done!
pause

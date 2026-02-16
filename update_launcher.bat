@echo off
chcp 65001 >nul 2>&1
title 技能追蹤器 - 更新中

echo ============================================
echo   技能追蹤器 - 自動更新
echo ============================================
echo.

REM 參數: %1=下載的檔案路徑  %2=應用程式目錄  %3=應用程式exe路徑
set "DOWNLOAD_FILE=%~1"
set "APP_DIR=%~2"
set "APP_EXE=%~3"

if "%DOWNLOAD_FILE%"=="" (
    echo [錯誤] 未指定下載檔案路徑
    pause
    exit /b 1
)

if "%APP_DIR%"=="" (
    echo [錯誤] 未指定應用程式目錄
    pause
    exit /b 1
)

echo [1/4] 等待應用程式關閉...
timeout /t 3 /nobreak >nul

REM 確保程式已關閉
:wait_loop
tasklist /FI "IMAGENAME eq 技能追蹤器.exe" 2>nul | find /I "技能追蹤器.exe" >nul
if not errorlevel 1 (
    echo       程式仍在運行，等待中...
    timeout /t 2 /nobreak >nul
    goto :wait_loop
)

echo [2/4] 正在備份舊版本...
if exist "%APP_DIR%\技能追蹤器.exe.bak" del /f /q "%APP_DIR%\技能追蹤器.exe.bak"
if exist "%APP_DIR%\技能追蹤器.exe" (
    move /y "%APP_DIR%\技能追蹤器.exe" "%APP_DIR%\技能追蹤器.exe.bak" >nul 2>&1
)

echo [3/4] 正在安裝更新...

REM 判斷下載的檔案類型
set "EXT=%~x1"

if /I "%EXT%"==".exe" (
    REM 直接覆蓋 exe
    copy /y "%DOWNLOAD_FILE%" "%APP_DIR%\技能追蹤器.exe" >nul 2>&1
    if errorlevel 1 (
        echo [錯誤] 複製新版本失敗，正在還原...
        if exist "%APP_DIR%\技能追蹤器.exe.bak" (
            move /y "%APP_DIR%\技能追蹤器.exe.bak" "%APP_DIR%\技能追蹤器.exe" >nul 2>&1
        )
        pause
        exit /b 1
    )
) else if /I "%EXT%"==".zip" (
    REM 解壓縮 zip
    echo       解壓縮中...
    powershell -NoProfile -Command "Expand-Archive -Path '%DOWNLOAD_FILE%' -DestinationPath '%APP_DIR%' -Force" >nul 2>&1
    if errorlevel 1 (
        echo [錯誤] 解壓縮失敗，正在還原...
        if exist "%APP_DIR%\技能追蹤器.exe.bak" (
            move /y "%APP_DIR%\技能追蹤器.exe.bak" "%APP_DIR%\技能追蹤器.exe" >nul 2>&1
        )
        pause
        exit /b 1
    )
) else (
    echo [錯誤] 不支援的檔案格式: %EXT%
    if exist "%APP_DIR%\技能追蹤器.exe.bak" (
        move /y "%APP_DIR%\技能追蹤器.exe.bak" "%APP_DIR%\技能追蹤器.exe" >nul 2>&1
    )
    pause
    exit /b 1
)

echo [4/4] 清理暫存檔案...
del /f /q "%DOWNLOAD_FILE%" >nul 2>&1
if exist "%APP_DIR%\技能追蹤器.exe.bak" del /f /q "%APP_DIR%\技能追蹤器.exe.bak" >nul 2>&1

echo.
echo ============================================
echo   更新完成！正在重新啟動...
echo ============================================
echo.

REM 重新啟動應用程式
if exist "%APP_DIR%\技能追蹤器.exe" (
    start "" "%APP_DIR%\技能追蹤器.exe"
) else if exist "%APP_EXE%" (
    start "" "%APP_EXE%"
)

timeout /t 2 /nobreak >nul
exit

@echo off
chcp 65001 >nul 2>&1

REM 參數: %1=下載的檔案路徑  %2=應用程式目錄  %3=應用程式exe路徑
set "DOWNLOAD_FILE=%~1"
set "APP_DIR=%~2"
set "APP_EXE=%~3"

if "%DOWNLOAD_FILE%"=="" exit /b 1
if "%APP_DIR%"=="" exit /b 1

REM [1/4] 等待應用程式關閉（3秒）
timeout /t 3 /nobreak >nul

REM 確保程式已關閉
:wait_loop
tasklist /FI "IMAGENAME eq 技能追蹤器.exe" 2>nul | find /I "技能追蹤器.exe" >nul
if not errorlevel 1 (
    timeout /t 2 /nobreak >nul
    goto :wait_loop
)

REM [2/4] 備份舊版本
if exist "%APP_DIR%\技能追蹤器.exe.bak" del /f /q "%APP_DIR%\技能追蹤器.exe.bak"
if exist "%APP_DIR%\技能追蹤器.exe" (
    move /y "%APP_DIR%\技能追蹤器.exe" "%APP_DIR%\技能追蹤器.exe.bak" >nul 2>&1
)

REM [3/4] 安裝更新
set "EXT=%~x1"

if /I "%EXT%"==".exe" (
    copy /y "%DOWNLOAD_FILE%" "%APP_DIR%\技能追蹤器.exe" >nul 2>&1
    if errorlevel 1 (
        if exist "%APP_DIR%\技能追蹤器.exe.bak" (
            move /y "%APP_DIR%\技能追蹤器.exe.bak" "%APP_DIR%\技能追蹤器.exe" >nul 2>&1
        )
        exit /b 1
    )
) else if /I "%EXT%"==".zip" (
    powershell -NoProfile -Command ^
        "try { Add-Type -AssemblyName System.IO.Compression.FileSystem; [System.IO.Compression.ZipFile]::ExtractToDirectory($args[0], $args[1], $true) } catch { exit 1 }" ^
        -- "%DOWNLOAD_FILE%" "%APP_DIR%"
    if errorlevel 1 (
        if exist "%APP_DIR%\技能追蹤器.exe.bak" (
            move /y "%APP_DIR%\技能追蹤器.exe.bak" "%APP_DIR%\技能追蹤器.exe" >nul 2>&1
        )
        exit /b 1
    )
) else (
    REM 不支援的格式，還原備份
    if exist "%APP_DIR%\技能追蹤器.exe.bak" (
        move /y "%APP_DIR%\技能追蹤器.exe.bak" "%APP_DIR%\技能追蹤器.exe" >nul 2>&1
    )
    exit /b 1
)

REM [4/4] 清理暫存檔案
del /f /q "%DOWNLOAD_FILE%" >nul 2>&1
if exist "%APP_DIR%\技能追蹤器.exe.bak" del /f /q "%APP_DIR%\技能追蹤器.exe.bak" >nul 2>&1

REM 重新啟動應用程式
if exist "%APP_DIR%\技能追蹤器.exe" (
    start "" "%APP_DIR%\技能追蹤器.exe"
) else if exist "%APP_EXE%" (
    start "" "%APP_EXE%"
)

exit /b 0

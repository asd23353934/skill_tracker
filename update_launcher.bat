@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1

REM 參數: %1=下載的檔案路徑  %2=應用程式目錄  %3=應用程式exe路徑  %4=應用程式PID
set "DOWNLOAD_FILE=%~1"
set "APP_DIR=%~2"
set "APP_EXE=%~3"
set "APP_PID=%~4"
set "LOG_FILE=%APP_DIR%\update_log.txt"

if "%DOWNLOAD_FILE%"=="" exit /b 1
if "%APP_DIR%"=="" exit /b 1

REM 從 APP_EXE 取得檔名（不含副檔名）
for %%F in ("%APP_EXE%") do set "EXE_NAME=%%~nF"
if "%EXE_NAME%"=="" set "EXE_NAME=skill_tracker"

echo %date% %time%  === Update started (BAT) === >> "%LOG_FILE%"
echo %date% %time%  DownloadFile=%DOWNLOAD_FILE% >> "%LOG_FILE%"
echo %date% %time%  AppDir=%APP_DIR% >> "%LOG_FILE%"
echo %date% %time%  AppExe=%APP_EXE% >> "%LOG_FILE%"
echo %date% %time%  AppPid=%APP_PID% >> "%LOG_FILE%"
echo %date% %time%  ExeName=%EXE_NAME% >> "%LOG_FILE%"

REM [1/4] 等待應用程式關閉
echo %date% %time%  [1/4] Waiting for app to exit... >> "%LOG_FILE%"
timeout /t 3 /nobreak >nul

set "WAIT_COUNT=0"
:wait_loop
if %WAIT_COUNT% GEQ 30 goto :wait_done
if "%APP_PID%"=="" goto :wait_by_name
REM 優先用 PID 偵測
tasklist /FI "PID eq %APP_PID%" 2>nul | find /I "%APP_PID%" >nul
if errorlevel 1 goto :wait_done
goto :wait_next

:wait_by_name
tasklist /FI "IMAGENAME eq %EXE_NAME%.exe" 2>nul | find /I "%EXE_NAME%.exe" >nul
if errorlevel 1 goto :wait_done

:wait_next
echo %date% %time%    App still running, waiting... (%WAIT_COUNT%s) >> "%LOG_FILE%"
timeout /t 2 /nobreak >nul
set /a WAIT_COUNT+=2
goto :wait_loop

:wait_done
echo %date% %time%    App exited (waited %WAIT_COUNT%s) >> "%LOG_FILE%"

REM [2/4] 備份舊版本
echo %date% %time%  [2/4] Backing up old exe... >> "%LOG_FILE%"
if exist "%APP_DIR%\%EXE_NAME%.exe.bak" del /f /q "%APP_DIR%\%EXE_NAME%.exe.bak"
if exist "%APP_DIR%\%EXE_NAME%.exe" (
    move /y "%APP_DIR%\%EXE_NAME%.exe" "%APP_DIR%\%EXE_NAME%.exe.bak" >nul 2>&1
    if errorlevel 1 (
        echo %date% %time%    ERROR: Failed to backup exe >> "%LOG_FILE%"
        call :write_marker "備份舊版失敗（exe 可能被防毒或其他程式鎖定）"
        call :show_dialog "無法備份舊版執行檔，可能有其他程式正在使用它。" "請關閉所有 skill_tracker 視窗後重試。"
        goto :restart
    )
    echo %date% %time%    Backup created >> "%LOG_FILE%"
)

REM [3/4] 安裝更新
echo %date% %time%  [3/4] Installing update... >> "%LOG_FILE%"
set "EXT=%~x1"

if /I "%EXT%"==".exe" (
    copy /y "%DOWNLOAD_FILE%" "%APP_DIR%\%EXE_NAME%.exe" >nul 2>&1
    if errorlevel 1 (
        echo %date% %time%    ERROR: Failed to copy exe >> "%LOG_FILE%"
        goto :restore_and_restart
    )
    echo %date% %time%    Copied exe directly >> "%LOG_FILE%"
) else if /I "%EXT%"==".zip" (
    REM ZIP 內含頂層資料夾，解壓縮目標應為 APP_DIR 的上一層
    for %%F in ("%APP_DIR:~0,-1%") do set "PARENT_DIR=%%~dpF"
    echo %date% %time%    Extracting ZIP to !PARENT_DIR! ... >> "%LOG_FILE%"
    set "PS_SRC=%DOWNLOAD_FILE%"
    set "PS_DST=!PARENT_DIR!"
    powershell -NoProfile -WindowStyle Hidden -Command ^
        "try { Expand-Archive -Path $env:PS_SRC -DestinationPath $env:PS_DST -Force } catch { exit 1 }"
    if errorlevel 1 (
        echo %date% %time%    ERROR: ZIP extraction failed >> "%LOG_FILE%"
        goto :restore_and_restart
    )
    REM 驗證新 exe 是否存在
    if not exist "%APP_DIR%\%EXE_NAME%.exe" (
        echo %date% %time%    ERROR: Extraction OK but exe not found >> "%LOG_FILE%"
        goto :restore_and_restart
    )
    echo %date% %time%    Extraction OK, exe verified >> "%LOG_FILE%"
) else if /I "%EXT%"==".7z" (
    REM 尋找 7-Zip
    set "SEVENZIP="
    where 7z.exe >nul 2>&1
    if not errorlevel 1 set "SEVENZIP=7z.exe"
    if "!SEVENZIP!"=="" if exist "%ProgramFiles%\7-Zip\7z.exe" set "SEVENZIP=%ProgramFiles%\7-Zip\7z.exe"
    if "!SEVENZIP!"=="" if exist "%ProgramFiles(x86)%\7-Zip\7z.exe" set "SEVENZIP=%ProgramFiles(x86)%\7-Zip\7z.exe"
    if "!SEVENZIP!"=="" (
        echo %date% %time%    ERROR: 7-Zip not found >> "%LOG_FILE%"
        goto :restore_and_restart
    )
    "!SEVENZIP!" x "%DOWNLOAD_FILE%" -o"%APP_DIR%" -y >nul 2>&1
    if errorlevel 1 (
        echo %date% %time%    ERROR: 7z extraction failed >> "%LOG_FILE%"
        goto :restore_and_restart
    )
    echo %date% %time%    7z extraction OK >> "%LOG_FILE%"
) else (
    echo %date% %time%    ERROR: Unsupported format: %EXT% >> "%LOG_FILE%"
    goto :restore_and_restart
)

REM 安裝成功：清理暫存檔案
del /f /q "%DOWNLOAD_FILE%" >nul 2>&1
if exist "%APP_DIR%\%EXE_NAME%.exe.bak" del /f /q "%APP_DIR%\%EXE_NAME%.exe.bak" >nul 2>&1
echo %date% %time%    Cleanup done >> "%LOG_FILE%"
goto :restart

:restore_and_restart
echo %date% %time%    Restoring backup... >> "%LOG_FILE%"
if exist "%APP_DIR%\%EXE_NAME%.exe.bak" (
    move /y "%APP_DIR%\%EXE_NAME%.exe.bak" "%APP_DIR%\%EXE_NAME%.exe" >nul 2>&1
    echo %date% %time%    Backup restored >> "%LOG_FILE%"
)
call :write_marker "更新安裝失敗（已自動還原舊版）"
call :show_dialog "更新安裝失敗，已還原為舊版。" "建議從 GitHub 手動下載最新版。"

:restart
REM [4/4] 重新啟動應用程式
echo %date% %time%  [4/4] Restarting app... >> "%LOG_FILE%"
if exist "%APP_DIR%\%EXE_NAME%.exe" goto :restart_primary
if exist "%APP_EXE%" goto :restart_fallback
echo %date% %time%    ERROR: No exe found to restart >> "%LOG_FILE%"
call :write_marker "更新後找不到任何可重啟的 exe"
call :show_dialog "更新失敗：找不到可重啟的執行檔。" "請從 GitHub 手動下載最新版並解壓覆蓋。"
goto :restart_done

:restart_primary
start "" "%APP_DIR%\%EXE_NAME%.exe"
echo %date% %time%    Started %EXE_NAME%.exe >> "%LOG_FILE%"
goto :restart_done

:restart_fallback
start "" "%APP_EXE%"
echo %date% %time%    Started %APP_EXE% (fallback) >> "%LOG_FILE%"
goto :restart_done

:restart_done

echo %date% %time%  === Update finished (BAT) === >> "%LOG_FILE%"
exit /b 0

REM =========================================================
REM Sub-routines: write marker + show MessageBox（失敗時提示用戶）
REM =========================================================
:write_marker
REM %~1 = reason
set "MARKER_PATH=%APP_DIR%\update_failed.txt"
echo timestamp: %date% %time%> "%MARKER_PATH%"
echo reason: %~1>> "%MARKER_PATH%"
echo %date% %time%    Failure marker written: %MARKER_PATH% >> "%LOG_FILE%"
exit /b 0

:show_dialog
REM %~1 = reason, %~2 = instruction
REM 用 env var 傳遞訊息，避免 PowerShell 字串拼接被單引號 / 換行 break（注入防禦）
set "DLG_REASON=%~1"
set "DLG_INSTRUCTION=%~2"
powershell -NoProfile -Command "Add-Type -AssemblyName System.Windows.Forms; [void][System.Windows.Forms.MessageBox]::Show($env:DLG_REASON + [Environment]::NewLine + [Environment]::NewLine + $env:DLG_INSTRUCTION, '自動更新失敗', 'OK', 'Warning')" >nul 2>&1
set "DLG_REASON="
set "DLG_INSTRUCTION="
exit /b 0

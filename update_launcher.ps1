# update_launcher.ps1
# 更新替換腳本：等待舊程式關閉 → 備份 → 解壓 → 驗證 → 重啟
param(
    [string]$DownloadFile,
    [string]$AppDir,
    [string]$AppExe,
    [int]$AppPid = 0
)

if (-not $DownloadFile -or -not $AppDir) { exit 1 }

# ── Logging ──
$logFile = Join-Path $AppDir "update_log.txt"
function Write-Log($msg) {
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $line = "$ts  $msg`r`n"
    [System.IO.File]::AppendAllText($logFile, $line, [System.Text.Encoding]::UTF8)
}

# ── Failure handling ──
# 兩道防線：
#   1. 立即跳 MessageBox 告知使用者（同步，使用者按 OK 才會回來）
#   2. 寫 update_failed.txt 到 AppDir，主程式下次啟動時讀此檔顯示 toast
function Write-FailureMarker {
    param([string]$reason, [string]$detail = "")
    try {
        $markerPath = Join-Path $AppDir "update_failed.txt"
        $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        $lines = @("timestamp: $ts", "reason: $reason")
        if ($detail) { $lines += "detail: $detail" }
        $lines | Out-File -FilePath $markerPath -Encoding utf8
        Write-Log "  Failure marker written: $markerPath"
    } catch {
        Write-Log "  Write-FailureMarker failed: $_"
    }
}

function Show-FailureDialog {
    param([string]$reason, [string]$instruction = "")
    try {
        Add-Type -AssemblyName System.Windows.Forms -ErrorAction SilentlyContinue
        $msg = "技能追蹤器自動更新失敗：`r`n`r`n$reason"
        if ($instruction) { $msg += "`r`n`r`n$instruction" }
        [System.Windows.Forms.MessageBox]::Show(
            $msg, "自動更新失敗",
            [System.Windows.Forms.MessageBoxButtons]::OK,
            [System.Windows.Forms.MessageBoxIcon]::Warning
        ) | Out-Null
    } catch {
        Write-Log "  Show-FailureDialog failed: $_"
    }
}

try {
    Write-Log "=== Update started ==="
    Write-Log "DownloadFile=$DownloadFile"
    Write-Log "AppDir=$AppDir"
    Write-Log "AppExe=$AppExe"
    Write-Log "AppPid=$AppPid"
    Write-Log "PS Version=$($PSVersionTable.PSVersion)"

    # 從 $AppExe 取得執行檔名稱
    $exeFileName = if ($AppExe) { [System.IO.Path]::GetFileNameWithoutExtension($AppExe) } else { "" }
    if (-not $exeFileName) { $exeFileName = "skill_tracker" }
    Write-Log "exeFileName=$exeFileName"

    # [1/4] 等待應用程式關閉（最多 30 秒）
    Write-Log "[1/4] Waiting for app to exit..."
    Start-Sleep -Seconds 3

    $waited = 0
    while ($waited -lt 30) {
        $stillRunning = $false
        if ($AppPid -gt 0) {
            # 優先用 PID 偵測（避免中文進程名編碼問題）
            $proc = Get-Process -Id $AppPid -ErrorAction SilentlyContinue
            if ($proc) { $stillRunning = $true }
        } else {
            # Fallback: 用名稱偵測
            $proc = Get-Process -Name $exeFileName -ErrorAction SilentlyContinue
            if ($proc) { $stillRunning = $true }
        }
        if (-not $stillRunning) { break }
        Write-Log "  App still running, waiting... ($waited s)"
        Start-Sleep -Seconds 2
        $waited += 2
    }
    Write-Log "  App exited (waited ${waited}s)"

    # [2/4] 備份舊版 exe
    Write-Log "[2/4] Backing up old exe..."
    $oldExe = Join-Path $AppDir "$exeFileName.exe"
    $bakExe = Join-Path $AppDir "$exeFileName.exe.bak"

    if (Test-Path $bakExe) {
        Remove-Item $bakExe -Force -ErrorAction SilentlyContinue
    }

    if (Test-Path $oldExe) {
        try {
            Move-Item $oldExe $bakExe -Force -ErrorAction Stop
            Write-Log "  Backup created: $bakExe"
        } catch {
            Write-Log "  ERROR: Failed to backup exe: $_"
            Write-Log "  Aborting update - exe may still be locked"
            Write-FailureMarker "備份舊版失敗（exe 可能被防毒或其他程式鎖定）" "$_"
            Show-FailureDialog "無法備份舊版執行檔，可能有其他程式正在使用它。" "請關閉所有 skill_tracker 視窗後重試，或從 GitHub 手動下載最新版。"
            if (Test-Path $oldExe) { Start-Process -FilePath $oldExe }
            exit 1
        }
    } else {
        Write-Log "  Old exe not found at $oldExe, skipping backup"
    }

    # [3/4] 安裝更新
    Write-Log "[3/4] Installing update..."
    $ext = [System.IO.Path]::GetExtension($DownloadFile).ToLower()
    $success = $false
    $installError = ""

    try {
        if ($ext -eq ".exe") {
            Copy-Item $DownloadFile $oldExe -Force -ErrorAction Stop
            $success = $true
            Write-Log "  Copied exe directly"
        }
        elseif ($ext -eq ".zip") {
            $parentDir = Split-Path $AppDir -Parent
            Write-Log "  Extracting ZIP to $parentDir ..."
            Expand-Archive -LiteralPath $DownloadFile -DestinationPath $parentDir -Force
            # 驗證新 exe 是否存在
            if (Test-Path $oldExe) {
                $success = $true
                Write-Log "  Extraction OK, new exe verified at $oldExe"
            } else {
                Write-Log "  ERROR: Extraction completed but exe not found at $oldExe"
                $installError = "解壓 ZIP 完成但找不到新版 exe（ZIP 結構可能異常）"
                $success = $false
            }
        }
        else {
            Write-Log "  ERROR: Unsupported format: $ext"
            $installError = "不支援的更新檔格式：$ext"
            $success = $false
        }
    }
    catch {
        Write-Log "  ERROR: Installation failed: $_"
        $installError = "安裝過程發生錯誤：$_"
        $success = $false
    }

    if (-not $success) {
        Write-Log "  Restoring backup..."
        if (Test-Path $bakExe) {
            Move-Item $bakExe $oldExe -Force -ErrorAction SilentlyContinue
            Write-Log "  Backup restored"
        }
        Write-FailureMarker $installError
        Show-FailureDialog $installError "已自動還原舊版。建議從 GitHub 手動下載最新版。"
    }
    else {
        # 清理暫存與備份
        Remove-Item $DownloadFile -Force -ErrorAction SilentlyContinue
        Remove-Item $bakExe -Force -ErrorAction SilentlyContinue
        Write-Log "  Cleanup done"
    }

    # [4/4] 重新啟動應用程式
    Write-Log "[4/4] Restarting app..."
    if (Test-Path $oldExe) {
        Start-Process -FilePath $oldExe
        Write-Log "  Started $oldExe"
    }
    elseif ($AppExe -and (Test-Path $AppExe)) {
        Start-Process -FilePath $AppExe
        # PS 5.1 對 Write-Log (expression) 的 expression group 有 parse quirk；用變數預建避開
        $startedMsg = "  Started $AppExe [fallback]"
        Write-Log $startedMsg
    }
    else {
        Write-Log "  ERROR: No exe found to restart"
        Write-FailureMarker "更新後找不到任何可重啟的 exe"
        Show-FailureDialog "更新失敗：找不到可重啟的執行檔。" "請從 GitHub 手動下載 skill_tracker 最新版並解壓覆蓋。"
    }

    $finishedMsg = "=== Update finished, success=$success ==="
    Write-Log $finishedMsg
}
catch {
    Write-Log "UNHANDLED ERROR: $_"
    Write-Log $_.ScriptStackTrace
    Write-FailureMarker "更新過程發生未處理錯誤" "$_"
    Show-FailureDialog "更新過程發生未預期錯誤。" "已嘗試還原舊版。請從 GitHub 手動下載最新版。"
    # 嘗試還原並重啟
    $oldExe = Join-Path $AppDir "$exeFileName.exe"
    $bakExe = Join-Path $AppDir "$exeFileName.exe.bak"
    if ((Test-Path $bakExe) -and -not (Test-Path $oldExe)) {
        Move-Item $bakExe $oldExe -Force -ErrorAction SilentlyContinue
    }
    if (Test-Path $oldExe) { Start-Process -FilePath $oldExe }
    elseif ($AppExe -and (Test-Path $AppExe)) { Start-Process -FilePath $AppExe }
    exit 1
}

exit 0

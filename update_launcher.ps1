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
    "$ts  $msg" | Out-File -FilePath $logFile -Append -Encoding utf8
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
                $success = $false
            }
        }
        else {
            Write-Log "  ERROR: Unsupported format: $ext"
            $success = $false
        }
    }
    catch {
        Write-Log "  ERROR: Installation failed: $_"
        $success = $false
    }

    if (-not $success) {
        Write-Log "  Restoring backup..."
        if (Test-Path $bakExe) {
            Move-Item $bakExe $oldExe -Force -ErrorAction SilentlyContinue
            Write-Log "  Backup restored"
        }
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
        Write-Log "  Started $AppExe (fallback)"
    }
    else {
        Write-Log "  ERROR: No exe found to restart"
    }

    Write-Log "=== Update finished (success=$success) ==="
}
catch {
    Write-Log "UNHANDLED ERROR: $_"
    Write-Log $_.ScriptStackTrace
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

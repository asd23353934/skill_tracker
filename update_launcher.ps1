# update_launcher.ps1
# 更新替換腳本：等待舊程式關閉 → 解壓 → 重啟
# 呼叫方式：powershell -WindowStyle Hidden -ExecutionPolicy Bypass -File update_launcher.ps1 <下載檔> <應用目錄> <應用exe路徑>
param(
    [string]$DownloadFile,
    [string]$AppDir,
    [string]$AppExe
)

if (-not $DownloadFile -or -not $AppDir) { exit 1 }

# 從 $AppExe 取得執行檔名稱（避免硬編碼中文，防止編碼問題）
$exeFileName = if ($AppExe) { [System.IO.Path]::GetFileNameWithoutExtension($AppExe) } else { "" }
if (-not $exeFileName) { $exeFileName = "技能追蹤器" }

# [1/4] 等待應用程式關閉（最多 30 秒）
Start-Sleep -Seconds 3
$waited = 0
while ($waited -lt 30) {
    $proc = Get-Process -Name $exeFileName -ErrorAction SilentlyContinue
    if (-not $proc) { break }
    Start-Sleep -Seconds 2
    $waited += 2
}

# [2/4] 備份舊版 exe
$oldExe = Join-Path $AppDir "$exeFileName.exe"
$bakExe = Join-Path $AppDir "$exeFileName.exe.bak"
if (Test-Path $bakExe) { Remove-Item $bakExe -Force -ErrorAction SilentlyContinue }
if (Test-Path $oldExe) { Move-Item $oldExe $bakExe -Force -ErrorAction SilentlyContinue }

# [3/4] 安裝更新
$ext = [System.IO.Path]::GetExtension($DownloadFile).ToLower()
$success = $false

try {
    if ($ext -eq ".exe") {
        Copy-Item $DownloadFile $oldExe -Force
        $success = $true
    }
    elseif ($ext -eq ".zip") {
        # APP_DIR 的上一層（ZIP 包含頂層資料夾 "技能追蹤器\"）
        $parentDir = Split-Path $AppDir -Parent
        # Expand-Archive -Force 在 PowerShell 5.0+ (Windows 10 內建) 皆可用
        Expand-Archive -LiteralPath $DownloadFile -DestinationPath $parentDir -Force
        $success = $true
    }
    else {
        # 不支援的格式
        $success = $false
    }
}
catch {
    $success = $false
}

if (-not $success) {
    # 還原備份
    if (Test-Path $bakExe) {
        Move-Item $bakExe $oldExe -Force -ErrorAction SilentlyContinue
    }
}
else {
    # 清理暫存與備份
    Remove-Item $DownloadFile -Force -ErrorAction SilentlyContinue
    Remove-Item $bakExe -Force -ErrorAction SilentlyContinue
}

# [4/4] 重新啟動應用程式
if (Test-Path $oldExe) {
    Start-Process -FilePath $oldExe
}
elseif ($AppExe -and (Test-Path $AppExe)) {
    Start-Process -FilePath $AppExe
}

exit 0

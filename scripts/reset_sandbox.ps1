# 重設 sandbox 到指定版本，方便測試自動更新流程（本機 dry-run）
#
# 用法：
#   .\scripts\reset_sandbox.ps1 -Version v4.3.5
#
# 動作：
#   1. 殺掉可能還在跑的 sandbox 內 skill_tracker process
#   2. 從 GitHub release 下載指定版本 ZIP（用 gh CLI；已 cache 在 %TEMP% 不重抓）
#   3. 清空 C:\Temp\skill_tracker_sandbox\ 後解壓 ZIP
#   4. 確認 launcher .ps1/.bat 在 top-level（PyInstaller 6.x 放 _internal/，
#      release ZIP 應由 zip_release.py 補到 top-level；本 script 額外驗證）
#
# 依賴：gh CLI 已登入（與 skill_tracker repo 同 owner asd23353934）

param(
    [Parameter(Mandatory = $true)]
    [string]$Version
)

$ErrorActionPreference = "Stop"

$sandbox = "C:\Temp\skill_tracker_sandbox"
$appDir  = "$sandbox\skill_tracker"
$zipName = "skill_tracker_$Version.zip"
$tempZip = "$env:TEMP\$zipName"

Write-Host "=== Reset sandbox to $Version ==="

# Kill 可能還在跑的 sandbox process
$killed = 0
Get-Process -Name skill_tracker -ErrorAction SilentlyContinue | ForEach-Object {
    if ($_.Path -and $_.Path -like "$sandbox*") {
        Write-Host "  kill PID $($_.Id) ($($_.Path))"
        Stop-Process -Id $_.Id -Force
        $killed++
    }
}
if ($killed -gt 0) { Start-Sleep -Milliseconds 500 }

# 下載 ZIP（gh release download；cache 在 %TEMP%）
if (-not (Test-Path $tempZip)) {
    Write-Host "  download $Version ZIP from GitHub release..."
    & gh release download $Version --pattern "*.zip" --output $tempZip
    if (-not (Test-Path $tempZip)) {
        Write-Host "[FAIL] ZIP not found after gh release download"
        exit 1
    }
} else {
    $size = (Get-Item $tempZip).Length / 1MB
    Write-Host ("  reuse cached ZIP {0} ({1:F1} MB)" -f $tempZip, $size)
}

# Clean + extract
if (Test-Path $sandbox) { Remove-Item $sandbox -Recurse -Force }
New-Item -ItemType Directory -Path $sandbox -Force | Out-Null
Write-Host "  expand to $sandbox ..."
Expand-Archive -LiteralPath $tempZip -DestinationPath $sandbox -Force

# Verify exe + launcher 都在 top-level
$exe = "$appDir\skill_tracker.exe"
if (-not (Test-Path $exe)) {
    Write-Host "[FAIL] exe not at $exe"
    Write-Host "  ZIP 內結構可能異常 — 確認 zip_release.py post-process 跑過"
    exit 1
}
$exeInfo = Get-Item $exe
Write-Host ""
Write-Host "[OK] Sandbox ready"
Write-Host ("  exe: {0} bytes / {1}" -f $exeInfo.Length, $exeInfo.LastWriteTime)

foreach ($f in @("update_launcher.ps1", "update_launcher.bat")) {
    $p = "$appDir\$f"
    if (Test-Path $p) {
        Write-Host "  [OK] $f present"
    } else {
        Write-Host "  [WARN] $f missing — auto-update will fail"
    }
}

# Verify ps1 帶 BOM
$ps1 = "$appDir\update_launcher.ps1"
if (Test-Path $ps1) {
    $bom = [System.IO.File]::ReadAllBytes($ps1)[0..2]
    if ($bom[0] -eq 0xEF -and $bom[1] -eq 0xBB -and $bom[2] -eq 0xBF) {
        Write-Host "  [OK] ps1 has UTF-8 BOM"
    } else {
        Write-Host ("  [WARN] ps1 missing UTF-8 BOM ({0:X2} {1:X2} {2:X2}) — PS 5.1 中文 parse will fail" -f $bom[0], $bom[1], $bom[2])
    }
}

Write-Host ""
Write-Host "Next:"
Write-Host "  1. 啟動 sandbox：& `"$exe`""
Write-Host "  2. 等 1-2 秒 header 右上出現「↑ vNEW」 chip"
Write-Host "  3. 點 chip → UpdateDialog → 開始更新"
Write-Host "  4. 應自動下載 + swap + 重啟為 latest 版本"

# 自動更新 sandbox 測試 — 截圖記錄
#
# 用法（兩個視窗，順序很重要）：
#   1. 先在 PowerShell 視窗 A 跑：
#        .\verify_sandbox_screenshot.ps1
#      它會每 1.5 秒截一張全螢幕到 sandbox_test_shots/，最多 5 分鐘
#
#   2. 在另一個視窗 B 立刻啟動 sandbox 內舊版：
#        & "C:\Temp\sandbox_v434\skill_tracker.exe"
#
#   3. 看 sandbox 跳「v4.3.4 → v4.3.5」更新對話框 → 點「開始更新」
#      → 等下載 → launcher swap → 重啟為 v4.3.5
#
#   4. 升級完成後在視窗 A 按 Ctrl+C 結束截圖
#
# 結束後可選擇：
#   python verify_sandbox_screenshot_to_gif.py    # 把 PNG 拼成 GIF（用 Pillow）

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$shotsDir = "C:\Temp\sandbox_test_shots"
$maxFrames = 200    # 200 張 × 1.5s = 5 分鐘
$intervalSec = 1.5

if (Test-Path $shotsDir) {
    Write-Host "[note] 既存 $shotsDir 將被刪掉重建"
    Remove-Item $shotsDir -Recurse -Force
}
New-Item -ItemType Directory -Path $shotsDir -Force | Out-Null
Write-Host "[setup] Screenshot output: $shotsDir"
Write-Host "[setup] 開始截圖（最多 $maxFrames 張，每 $intervalSec 秒一張）"
Write-Host "[setup] 請在另一個視窗啟動 sandbox 內 skill_tracker.exe"
Write-Host "[setup] 完成後在本視窗按 Ctrl+C 中止"
Write-Host ""

$bounds = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
Write-Host "[setup] Screen size: $($bounds.Width) x $($bounds.Height)"
Write-Host ""

$frame = 0
$startTime = Get-Date
try {
    while ($frame -lt $maxFrames) {
        $frame++
        $elapsed = ((Get-Date) - $startTime).TotalSeconds
        $bmp = New-Object System.Drawing.Bitmap $bounds.Width, $bounds.Height
        $g = [System.Drawing.Graphics]::FromImage($bmp)
        $g.CopyFromScreen($bounds.Location, [System.Drawing.Point]::Empty, $bounds.Size)
        $name = "shot_{0:D4}_{1:F1}s.png" -f $frame, $elapsed
        $path = Join-Path $shotsDir $name
        $bmp.Save($path, [System.Drawing.Imaging.ImageFormat]::Png)
        $g.Dispose()
        $bmp.Dispose()
        Write-Host "  [$frame/$maxFrames] ($([math]::Round($elapsed,1))s) -> $name"
        Start-Sleep -Milliseconds ([int]($intervalSec * 1000))
    }
    Write-Host "[done] 達到最大張數，自動停止"
} finally {
    Write-Host ""
    Write-Host "[done] 共截 $frame 張到 $shotsDir"
}

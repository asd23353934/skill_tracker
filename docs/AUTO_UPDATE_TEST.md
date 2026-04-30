# 自動更新測試流程

每次 release 新版後跑一遍，確認升級流程沒 regression。

## 完整流程

1. **完成新 release**（gh release create vNEW + ZIP）。

2. **重置 sandbox 為前一版**：

   ```powershell
   .\scripts\reset_sandbox.ps1 -Version vPREV
   ```

   > 例：剛 release v4.3.7 → `.\scripts\reset_sandbox.ps1 -Version v4.3.6`

   script 會：
   - 殺掉 sandbox 內可能還在跑的 process
   - `gh release download vPREV` 抓 ZIP（cache 在 `%TEMP%`）
   - 解壓到 `C:\Temp\skill_tracker_sandbox\`
   - 驗證 launcher .ps1/.bat 在 top-level + ps1 含 UTF-8 BOM

3. **啟動 sandbox**：

   ```powershell
   & "C:\Temp\skill_tracker_sandbox\skill_tracker\skill_tracker.exe"
   ```

4. **預期看到**：
   - 主視窗安靜出現，狀態列右下顯示 `vPREV`
   - ~1 秒後 header 右上角出現「↑ vNEW」橘色 chip + 右下 toast info
   - 點 chip → UpdateDialog 跳出（vPREV → vNEW）
   - 點「開始更新」→ 進度條跑滿 70 MB
   - 應用關閉 → launcher 在背景替換 exe → 重啟
   - 5-8 秒後新版自動跑起來，狀態列右下變 `vNEW`

5. **失敗 debug**：

   ```powershell
   cat "C:\Temp\skill_tracker_sandbox\skill_tracker\update_log.txt"
   ```

   看 launcher 走到哪一步停。

## 已知雷（v4.3.6 全修，留作 regression 防線）

| 雷 | 症狀 | 防線 |
|---|---|---|
| ps1 缺 UTF-8 BOM | PS 5.1 cp950 讀中文 → [3/4] silent skip | reset_sandbox 驗 BOM；source ps1 git 內含 BOM |
| `DETACHED_PROCESS \| CREATE_NO_WINDOW` | launcher 啟動立刻死 | update_dialog_v2 只用 `CREATE_NO_WINDOW` |
| PyInstaller 6.x 放 launcher 到 `_internal/` | 主程式找不到 | zip_release.py post-process 複製到 top-level |
| ZIP 頂層名 ≠ AppDir 名 | 解壓位置錯 → exe 沒被替換 | sandbox 用 `C:\Temp\skill_tracker_sandbox\skill_tracker\` 對齊 |
| 雙引號 `$var (text)` PS 5.1 quirk | parse 失敗 | ps1 內 Write-Log 用變數預建 pattern |

## 跨專案踩雷紀錄

詳見 `~/Desktop/gitlab/hsin-dev-notes/_shared/desktop-app-update.md`

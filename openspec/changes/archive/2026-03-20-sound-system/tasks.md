## 1. 內建音效版本管理驗證

- [x] 1.1 確認 `_ensure_builtin_sounds()` 讀取 `.builtin_version`，版本過低時重新產生所有音效，符合「Builtin sounds are versioned and auto-regenerated」規格（對照設計決策「內建音效版本管理」）
- [x] 1.2 確認版本相符時只補齊缺失音效檔，不全部重新產生

## 2. WAV / MP3 播放路徑驗證

- [x] 2.1 確認 WAV 播放使用 `winsound.PlaySound()`，符合「WAV files are played via winsound」規格（對照設計決策「播放為非阻塞背景執行緒」）
- [x] 2.2 確認 MP3 播放使用 MCI `mciSendStringW`，alias 格式為 `snd{counter}`，符合「MP3 files are played via Windows MCI」規格（對照設計決策「MCI 互斥鎖防止 alias 衝突」）
- [x] 2.3 確認 MCI 播放使用 `_mci_lock` 互斥，符合「MCI playback is mutually exclusive」規格

## 3. 遷移映射驗證

- [x] 3.1 確認 `migrate_sound_filename()` 正確映射三個舊檔名，符合「Legacy sound filenames are migrated」規格

## 4. 音效匯入驗證

- [x] 4.1 確認 `import_sound()` 只接受 `.wav`/`.mp3`，符合「Sound import copies file to sounds directory」規格
- [x] 4.2 確認同名衝突時加 `_{counter}` 後綴，符合「Import with name collision」規格

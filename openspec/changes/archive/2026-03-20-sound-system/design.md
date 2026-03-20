## Context

`SoundManager` 在初始化時呼叫 `_ensure_builtin_sounds()` 確保內建音效存在。
播放使用背景執行緒（daemon thread）以避免阻塞 UI。
WAV 透過 `winsound.PlaySound()`（Windows 內建），MP3 透過 Windows MCI（`winmm.dll`）。

內建音效清單（`BUILTIN_SOUNDS`）定義音調序列，由 `_generate_wav()` 動態產生 WAV 檔案。

## Goals / Non-Goals

**Goals:**
- 記錄內建音效版本管理規則（何時重新產生）
- 記錄 WAV/MP3 播放路徑與 MCI 互斥鎖
- 記錄舊音效遷移映射
- 記錄音效匯入流程

**Non-Goals:**
- 跨平台音效支援（目前僅 Windows）
- 同時播放多個音效（MCI 互斥設計不支援）

## Decisions

### 內建音效版本管理

版本號（`_SOUND_VERSION`）遞增時，所有內建音效重新產生。
版本資訊存於 `sounds/.builtin_version` 文字檔。
版本低於當前時，先清理已知的舊版檔案，再重新產生所有內建音效。

### MCI 互斥鎖防止 alias 衝突

同一時間只能有一個 MCI 播放，使用 `threading.Lock()` 保護 `_mci_counter` 與 alias 分配。
MCI alias 格式為 `snd{counter}`（全域遞增，不重複）。

### 播放為非阻塞背景執行緒

`_play_async()` 啟動 daemon thread，播放不阻塞主執行緒。
MP3 阻塞在 `_play_mp3_blocking()`（MCI `play … wait`），但在背景執行緒中。

### 舊音效遷移

舊版三個音效（`beep_1/2/3.wav`）對應到新音效：
- `beep_1.wav` → `soft_bell.wav`
- `beep_2.wav` → `alert_double.wav`
- `beep_3.wav` → `alert_urgent.wav`

## Risks / Trade-offs

- [風險] `winsound` 與 `winmm.dll` 僅在 Windows 可用；非 Windows 環境靜默跳過
  → 緩解：`HAS_WINSOUND` 旗標控制，spec 標注 Windows-only
- [風險] MCI 互斥鎖導致同時播放兩個音效時第二個被丟棄
  → 緩解：屬已知設計折衷，spec 明確記錄「不支援同時播放」

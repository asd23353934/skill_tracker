"""
音效管理模組
處理音效的載入與播放，支援 .wav 與 .mp3 格式
WAV 使用 winsound (Windows 內建) 播放
MP3 使用 Windows MCI (winmm.dll) 播放
不依賴 pygame
"""

import os
import wave
import struct
import math
import threading
import ctypes
from src.infrastructure.helpers import user_data_path

try:
    import winsound
    HAS_WINSOUND = True
except ImportError:
    HAS_WINSOUND = False


# Windows MCI 播放器（支援 mp3）
_winmm = None
try:
    _winmm = ctypes.windll.winmm
except Exception:
    pass

# MCI 播放鎖（同一時間只能有一個 MCI 播放，避免 alias 衝突）
_mci_lock = threading.Lock()
_mci_counter = 0


def _mci_send(command):
    """發送 MCI 指令

    Args:
        command: MCI 指令字串

    Returns:
        int: 錯誤碼（0 表示成功）
    """
    if _winmm is None:
        return -1
    buf = ctypes.create_unicode_buffer(256)
    err = _winmm.mciSendStringW(command, buf, 255, 0)
    return err


def _play_mp3_blocking(filepath):
    """使用 MCI 播放 MP3（阻塞直到結束）

    Args:
        filepath: MP3 檔案完整路徑
    """
    global _mci_counter
    with _mci_lock:
        _mci_counter += 1
        alias = f"snd{_mci_counter}"

    try:
        # 剝除可能破壞 MCI 指令的字元（雙引號、換行），避免指令注入
        escaped = filepath.translate({ord('"'): None, ord('\r'): None, ord('\n'): None})
        _mci_send(f'open "{escaped}" type mpegvideo alias {alias}')
        _mci_send(f'play {alias} wait')
        _mci_send(f'close {alias}')
    except Exception:
        try:
            _mci_send(f'close {alias}')
        except Exception:
            pass


# 內建音效定義：(名稱, 頻率列表, 每段持續ms)
# 使用 (0, ms) 表示靜音間隔，讓多聲音效有明確的斷點
BUILTIN_SOUNDS = {
    "chime_up.wav": {
        "label": "上行提示音",
        "tones": [(523, 100), (0, 30), (659, 100), (0, 30), (784, 160)],
    },
    "chime_down.wav": {
        "label": "下行提示音",
        "tones": [(784, 100), (0, 30), (659, 100), (0, 30), (523, 160)],
    },
    "ding.wav": {
        "label": "叮咚",
        "tones": [(1047, 120), (0, 60), (784, 200)],
    },
    "alert_double.wav": {
        "label": "雙響提示",
        "tones": [(880, 100), (0, 80), (880, 100)],
    },
    "alert_urgent.wav": {
        "label": "緊急提示",
        "tones": [(988, 80), (0, 40), (988, 80), (0, 40), (988, 80)],
    },
    "soft_bell.wav": {
        "label": "柔和鈴聲",
        "tones": [(660, 250)],
    },
    "notify_bright.wav": {
        "label": "明亮通知",
        "tones": [(880, 80), (0, 40), (1109, 80), (0, 40), (1319, 140)],
    },
    "complete.wav": {
        "label": "完成提示",
        "tones": [(523, 80), (0, 30), (659, 80), (0, 30), (784, 80), (0, 30), (1047, 200)],
    },
}


def _generate_wav(filepath, tones, sample_rate=44100, volume=0.5):
    """使用 wave 模組產生標準 WAV 檔案

    Args:
        filepath: 輸出路徑
        tones: [(freq_hz, duration_ms), ...]
        sample_rate: 取樣率
        volume: 音量 (0-1)
    """
    samples = []
    for freq, dur_ms in tones:
        n_samples = int(sample_rate * dur_ms / 1000)
        if freq == 0:
            samples.extend([0] * n_samples)
            continue
        for i in range(n_samples):
            t = i / sample_rate
            val = volume * math.sin(2 * math.pi * freq * t)
            # 淡入淡出避免爆音
            fade_samples = min(int(sample_rate * 0.01), n_samples // 4)
            if fade_samples > 0:
                if i < fade_samples:
                    val *= i / fade_samples
                elif i > n_samples - fade_samples:
                    val *= (n_samples - i) / fade_samples
            samples.append(int(val * 32767))

    # 使用 wave 模組寫入標準格式 WAV（16-bit mono）
    n_channels = 1
    sample_width = 2  # 16-bit
    with wave.open(filepath, "wb") as wf:
        wf.setnchannels(n_channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(sample_rate)
        raw = b""
        for s in samples:
            clamped = max(-32768, min(32767, s))
            raw += struct.pack("<h", clamped)
        wf.writeframes(raw)


class SoundManager:
    """音效管理器"""

    def __init__(self):
        """初始化音效管理器"""
        self.sounds_dir = user_data_path("sounds")

        # 確保音效目錄存在
        if not os.path.exists(self.sounds_dir):
            try:
                os.makedirs(self.sounds_dir, exist_ok=True)
            except Exception:
                pass

        # 產生內建音效
        self._ensure_builtin_sounds()

    def _ensure_builtin_sounds(self):
        """確保內建音效檔案存在，版本更新時重新產生"""
        # 版本標記：若音效格式有更新則遞增此數字
        _SOUND_VERSION = 6
        version_file = os.path.join(self.sounds_dir, ".builtin_version")

        # 讀取已安裝版本
        current_version = 0
        if os.path.exists(version_file):
            try:
                with open(version_file, "r") as f:
                    current_version = int(f.read().strip())
            except Exception:
                pass

        need_regen = current_version < _SOUND_VERSION

        if need_regen:
            # 清理舊版內建音效檔案
            _OLD_BUILTIN_FILES = ["beep_1.wav", "beep_2.wav", "beep_3.wav"]
            for old_file in _OLD_BUILTIN_FILES:
                old_path = os.path.join(self.sounds_dir, old_file)
                if os.path.exists(old_path):
                    try:
                        os.remove(old_path)
                    except Exception:
                        pass

        for filename, info in BUILTIN_SOUNDS.items():
            filepath = os.path.join(self.sounds_dir, filename)
            if need_regen or not os.path.exists(filepath):
                try:
                    _generate_wav(filepath, info["tones"])
                except Exception:
                    pass

        # 寫入版本標記
        if need_regen:
            try:
                with open(version_file, "w") as f:
                    f.write(str(_SOUND_VERSION))
            except Exception:
                pass

    # 舊音效 → 新音效的遷移映射
    _MIGRATION_MAP = {
        "beep_1.wav": "soft_bell.wav",
        "beep_2.wav": "alert_double.wav",
        "beep_3.wav": "alert_urgent.wav",
    }

    def migrate_sound_filename(self, filename):
        """將已刪除的舊音效檔名遷移為新音效

        Args:
            filename: 原始音效檔名

        Returns:
            遷移後的檔名（若無需遷移則原樣返回）
        """
        if filename in self._MIGRATION_MAP:
            return self._MIGRATION_MAP[filename]
        return filename

    def list_sounds(self):
        """列出所有可用的音效檔案

        Returns:
            list[str]: 音效檔案名稱列表
        """
        if not os.path.exists(self.sounds_dir):
            return []
        return sorted([
            f for f in os.listdir(self.sounds_dir)
            if f.lower().endswith(('.wav', '.mp3'))
        ])

    def get_sound_label(self, filename):
        """取得音效的顯示名稱

        Args:
            filename: 檔案名稱

        Returns:
            顯示用名稱（內建音效回傳中文名，自訂音效回傳檔名）
        """
        if filename in BUILTIN_SOUNDS:
            return BUILTIN_SOUNDS[filename]["label"]
        return filename

    def _play_async(self, filepath):
        """在背景執行緒播放音效（非阻塞，自動判斷 WAV / MP3）

        Args:
            filepath: 音效檔案完整路徑
        """
        is_mp3 = filepath.lower().endswith('.mp3')

        def _worker():
            try:
                if is_mp3:
                    _play_mp3_blocking(filepath)
                elif HAS_WINSOUND:
                    winsound.PlaySound(filepath, winsound.SND_FILENAME)
            except Exception:
                pass

        t = threading.Thread(target=_worker, daemon=True)
        t.start()

    def play(self, filename):
        """播放指定音效

        Args:
            filename: 音效檔案名稱 (在 sounds/ 目錄下)
        """
        if not filename:
            return

        filepath = os.path.join(self.sounds_dir, filename)
        if not os.path.exists(filepath):
            return

        self._play_async(filepath)

    def play_alert(self, filename):
        """播放提前提示音效

        Args:
            filename: 音效檔案名稱
        """
        if not filename:
            return

        filepath = os.path.join(self.sounds_dir, filename)
        if not os.path.exists(filepath):
            return

        self._play_async(filepath)

    def import_sound(self, source_path):
        """從外部路徑匯入音效檔案到 sounds/ 目錄

        Args:
            source_path: 來源音效檔案路徑

        Returns:
            str: 匯入後的檔案名稱，失敗時回傳 None
        """
        import shutil

        if not source_path:
            return None

        basename = os.path.basename(source_path)
        if not basename.lower().endswith(('.wav', '.mp3')):
            return None

        dest = os.path.join(self.sounds_dir, basename)

        # 若同名檔案已存在，加入數字後綴
        if os.path.exists(dest):
            name, ext = os.path.splitext(basename)
            counter = 1
            while os.path.exists(dest):
                dest = os.path.join(self.sounds_dir, f"{name}_{counter}{ext}")
                counter += 1
            basename = os.path.basename(dest)

        try:
            shutil.copy2(source_path, dest)
            return basename
        except Exception:
            return None

    def get_sound_options(self):
        """取得下拉式選單用的選項列表

        Returns:
            list[tuple[str, str]]: [(filename, label), ...] 包含空字串選項
        """
        options = []
        for filename in self.list_sounds():
            label = self.get_sound_label(filename)
            options.append((filename, label))
        return options

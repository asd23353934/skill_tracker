"""
TTS (文字轉語音) 模組
使用 Windows SAPI（System.Speech.Synthesis）經 PowerShell 子程序批次生成 WAV，
不依賴額外 Python 套件。生成的檔案可由 SoundManager 走 winsound 一律播放。

設計：
- 單一 PowerShell 進程處理一整批文字，避免多次啟動成本
- 透過環境變數傳遞 JSON payload，避開命令列長度 / 引號轉義
- 缺 powershell.exe / 無中文語音時 graceful degrade（無聲）
"""

import os
import json
import subprocess
import logging

logger = logging.getLogger(__name__)


# PowerShell 腳本：載入 SAPI → 挑中文語音 → 依 payload 逐筆生成 WAV
_PS_SCRIPT = r"""
Add-Type -AssemblyName System.Speech
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
try {
    $voices = $s.GetInstalledVoices() | Where-Object { $_.Enabled }
    $pick = $voices | Where-Object { $_.VoiceInfo.Culture.Name -eq 'zh-TW' } | Select-Object -First 1
    if (-not $pick) { $pick = $voices | Where-Object { $_.VoiceInfo.Culture.Name -eq 'zh-CN' } | Select-Object -First 1 }
    if (-not $pick) { $pick = $voices | Where-Object { $_.VoiceInfo.Culture.Name -like 'zh*' } | Select-Object -First 1 }
    if ($pick) { $s.SelectVoice($pick.VoiceInfo.Name) }
    $s.Rate = __RATE__
    $payload = $env:SKILL_TRACKER_TTS_PAYLOAD
    if (-not $payload) { Write-Output 0; exit 0 }
    $items = $payload | ConvertFrom-Json
    $ok = 0
    foreach ($item in $items) {
        try {
            $s.SetOutputToWaveFile($item.path)
            $s.Speak($item.text)
            $ok += 1
        } catch {
            Write-Error ("TTS fail: " + $item.text)
        }
    }
    Write-Output $ok
} finally {
    $s.Dispose()
}
"""


def generate_tts_batch(items, rate=0, timeout=60):
    """批次生成 TTS WAV（單一 PowerShell 進程處理整批）

    Args:
        items: [(text, output_path), ...]
        rate: 朗讀速度（-10 ~ 10），0 為正常
        timeout: PowerShell 進程逾時秒數

    Returns:
        實際成功生成的檔案數
    """
    pending = [(t, p) for (t, p) in items if t and p]
    if not pending:
        return 0

    payload = json.dumps(
        [{"text": t, "path": p} for (t, p) in pending],
        ensure_ascii=False,
    )

    script = _PS_SCRIPT.replace("__RATE__", str(int(rate)))

    env = os.environ.copy()
    env["SKILL_TRACKER_TTS_PAYLOAD"] = payload

    # CREATE_NO_WINDOW：避免 PyInstaller 打包後跳出 PowerShell 黑視窗
    kwargs = dict(
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if os.name == "nt":
        kwargs["creationflags"] = 0x08000000

    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
            **kwargs,
        )
    except FileNotFoundError:
        logger.warning("找不到 powershell.exe，TTS 功能無法使用")
        return 0
    except Exception:
        logger.exception("TTS PowerShell 啟動失敗")
        return 0

    if result.returncode != 0:
        logger.warning(
            "TTS exit=%d stderr=%r",
            result.returncode, (result.stderr or "")[:500],
        )

    try:
        return int((result.stdout or "0").strip().split()[0])
    except (ValueError, IndexError):
        return 0

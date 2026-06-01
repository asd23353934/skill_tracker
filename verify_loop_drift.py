"""
技能循環秒差（drift）回歸測試 — 真實 Qt 事件迴圈

直接跑「真實的」SkillWindow(is_loop=True) 循環邏輯（不 monkeypatch 計時行為，
只記錄歸零時刻 + 跑滿 N 輪後收尾），量測每次倒數歸零的 perf_counter 與「理想固定
排程」(global_start + n*total) 的偏差，斷言長時間循環不累積秒差。

對照修正前後（手動參考，非本腳本自動跑）：
  修正前：30 輪累積漂移 ≈ +10 秒（每輪 +336ms，30s 技能約 +40s/小時）
  修正後：應 < 0.5 秒且不隨輪數線性成長
"""

import os
import sys
import time

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

from src.ui.skill_window import SkillWindow

TOTAL = 1        # 冷卻秒數（1s 才能在合理時間內跑多輪）
N_LOOPS = 30     # 量測輪數
DRIFT_LIMIT_MS = 500     # 累積漂移上限
EXCESS_LIMIT_MS = 50     # 每輪平均超出量上限

app = QApplication.instance() or QApplication(sys.argv)


def run_real():
    """跑真實循環，回傳每輪歸零時刻與起始錨點"""
    zero_ts = []
    win = SkillWindow(
        skill={"name": "DriftTest", "cooldown": TOTAL},
        player="tester",
        position=(0, 0),
        skill_image=None,
        on_close=lambda w: None,
        enable_sound=False,
        skill_id="drift_test",
        is_loop=True,
        alert_enabled=False,
        window_size=64,
        skill_image_path=None,
        sound_manager=None,
    )
    global_start = win.start_time
    orig_finish = win._on_finish

    def patched_finish():
        # 只「記錄」歸零時刻；計時行為完全走真實程式碼
        if win.is_loop:
            zero_ts.append(time.perf_counter())
            if len(zero_ts) >= N_LOOPS:
                app.quit()
                return
        orig_finish()

    win._on_finish = patched_finish

    safety = QTimer()
    safety.setSingleShot(True)
    safety.timeout.connect(app.quit)
    safety.start(int((N_LOOPS * (TOTAL + 1) + 15) * 1000))

    app.exec()
    safety.stop()
    try:
        win.stop_countdown()
        win.close()
        app.processEvents()
    except Exception:
        pass
    return global_start, zero_ts


print("技能循環秒差回歸測試 — 真實 Qt 事件迴圈 (offscreen)")
print(f"Python {sys.version.split()[0]} | 平台 {os.environ.get('QT_QPA_PLATFORM')}\n")

gs, zero_ts = run_real()
n = len(zero_ts)
drifts = [zero_ts[i] - (gs + (i + 1) * TOTAL) for i in range(n)]
periods = [zero_ts[0] - gs] + [zero_ts[i] - zero_ts[i - 1] for i in range(1, n)]
excess = [p - TOTAL for p in periods]
mean_excess = sum(excess) / n
final_drift = drifts[-1]

print(f"  量測 {n} 輪 (total={TOTAL}s)")
print(f"  每輪週期：   平均 {sum(periods)/n:.4f}s | 最短 {min(periods):.4f}s | 最長 {max(periods):.4f}s")
print(f"  每輪超出量： 平均 {mean_excess*1000:+.1f} ms | 最小 {min(excess)*1000:+.1f} ms | 最大 {max(excess)*1000:+.1f} ms")
print(f"  累積漂移：   第 1 輪 {drifts[0]*1000:+.0f} ms  →  第 {n} 輪 {final_drift*1000:+.0f} ms")
cd = 30
loops_per_hour = 3600 / (cd + mean_excess)
print(f"  外推(30s技能)：1 小時(~{loops_per_hour:.0f}輪) 漂移 ≈ {loops_per_hour*mean_excess:+.2f}s\n")

ok_drift = abs(final_drift) * 1000 < DRIFT_LIMIT_MS
ok_excess = abs(mean_excess) * 1000 < EXCESS_LIMIT_MS
if ok_drift and ok_excess:
    print(f"  ✅ PASS — 累積漂移 {final_drift*1000:+.0f}ms (<{DRIFT_LIMIT_MS}ms)、"
          f"每輪 {mean_excess*1000:+.1f}ms (<{EXCESS_LIMIT_MS}ms)，長循環不漂移")
    sys.exit(0)
else:
    print(f"  ❌ FAIL — 漂移={final_drift*1000:+.0f}ms / 每輪={mean_excess*1000:+.1f}ms 超過門檻")
    sys.exit(1)

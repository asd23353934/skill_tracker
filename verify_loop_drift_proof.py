"""
循環秒差「獨立」驗證 — 零侵入觀察者 + 雙時鐘

回應質疑：「怎麼證明不是測試本身在配合？」
  1. 不 monkeypatch 視窗任何計時方法（_tick / _on_finish / _loop_restart 全跑真實程式碼）
  2. 另開一個獨立 QTimer 當「觀察者」，每 20ms 只『讀』win.start_time，偵測循環邊界，
     用觀察者自己的時鐘記錄時刻 —— 觀察者只讀不寫，無法影響被測物
  3. 同時用兩個獨立時鐘（perf_counter 單調鐘 + time.time 牆鐘）交叉比對
  4. 指標最直覺：固定牆鐘時間內，1s 冷卻技能「應該循環幾次」

用法：
  python verify_loop_drift_proof.py
  DRIFT_DURATION=120 python verify_loop_drift_proof.py   # 自訂測幾秒（預設 30）
"""

import os
import sys
import time

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

from src.ui.skill_window import SkillWindow

TOTAL = 1
DURATION = float(os.environ.get("DRIFT_DURATION", "30"))
app = QApplication.instance() or QApplication(sys.argv)


def observe(duration_s):
    """跑真實循環，用獨立觀察者（只讀）記錄每次循環邊界的雙時鐘時刻"""
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

    boundaries_perf = []   # 觀察者偵測到「新一輪開始」時的 perf_counter
    boundaries_wall = []   # 同一刻的 time.time（牆鐘）
    state = {"last_start": win.start_time, "samples": 0, "t0": time.perf_counter()}

    observer = QTimer()
    observer.setInterval(20)   # 每 20ms 取樣，純讀取

    def sample():
        state["samples"] += 1
        cur = win.start_time
        if cur != state["last_start"]:        # start_time 變了 → 新一輪開始
            state["last_start"] = cur
            boundaries_perf.append(time.perf_counter())
            boundaries_wall.append(time.time())
        if time.perf_counter() - state["t0"] >= duration_s:
            app.quit()

    observer.timeout.connect(sample)
    observer.start()

    app.exec()
    observer.stop()
    try:
        win.stop_countdown()
        win.close()
        app.processEvents()
    except Exception:
        pass
    return boundaries_perf, boundaries_wall, state["samples"]


def analyse(bp, bw, samples):
    k = len(bp)
    print(f"  觀察者取樣次數：{samples}（每 20ms 一次，純讀取 win.start_time）")
    print(f"  牆鐘測試時長：  {DURATION:.1f}s")
    print(f"  偵測到循環次數：{k}    （1s 冷卻技能理想值 ≈ {DURATION/TOTAL:.0f}）")
    if k < 2:
        print("  (循環次數不足，無法分析)")
        return
    # perf_counter 與 time.time 兩條獨立時鐘各自算
    for name, b in (("perf_counter 單調鐘", bp), ("time.time 牆鐘", bw)):
        ints = [b[i] - b[i - 1] for i in range(1, k)]
        span = b[-1] - b[0]
        ideal = (k - 1) * TOTAL
        drift = span - ideal
        print(f"    [{name}] 每輪間隔 平均 {sum(ints)/len(ints):.4f}s "
              f"(min {min(ints):.4f} / max {max(ints):.4f}) | "
              f"{k-1} 輪累積漂移 {drift*1000:+.0f} ms")
    # 兩鐘一致性
    span_p = bp[-1] - bp[0]
    span_w = bw[-1] - bw[0]
    print(f"    兩鐘量到的總時長差：{abs(span_p - span_w)*1000:.1f} ms（應 < 數十 ms，證明時鐘無異常）")


print("循環秒差『獨立』驗證 — 零侵入觀察者 + 雙時鐘 (offscreen)")
print(f"Python {sys.version.split()[0]}\n")
bp, bw, n = observe(DURATION)
analyse(bp, bw, n)

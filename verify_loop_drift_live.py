"""
循環秒差『真實視窗』即時示範

彈出 production 的 SkillWindow（你平常看到的倒數小窗）實際循環，旁邊一塊計分板
即時顯示：系統時鐘 + 已經過秒數 + 循環次數 + 對系統時鐘的累積誤差。
每隔一段自動截整個桌面（含 Windows 工作列時鐘）+ 截計分板，讓你自己對。

關鍵：用「零侵入觀察者」只讀 start_time 計次，不碰任何計時方法；誤差是對
datetime.now()（系統牆鐘）算的 —— 你可以拿截圖裡的工作列時鐘自己核。
"""

import os
import sys
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QFont

from src.ui.skill_window import SkillWindow

COOLDOWN = 3      # 循環冷卻秒數
DURATION = 90     # 示範總長（秒）
HERE = os.path.dirname(os.path.abspath(__file__))
ICON = os.path.join(HERE, "icon.png")


def make_app():
    """優先真實視窗；無桌面環境時退回 offscreen（仍能 widget.grab 出證據）"""
    inst = QApplication.instance()
    if inst:
        return inst, True
    try:
        return QApplication(sys.argv), True
    except Exception:
        os.environ["QT_QPA_PLATFORM"] = "offscreen"
        return QApplication(sys.argv), False


def hms(dt):
    return dt.strftime("%H:%M:%S.") + f"{dt.microsecond // 1000:03d}"


app, on_screen = make_app()

# 真實技能倒數窗（production class），循環模式
skillwin = SkillWindow(
    skill={"name": "循環測試", "cooldown": COOLDOWN},
    player="",
    position=(420, 470),
    skill_image=None,
    on_close=lambda w: None,
    enable_sound=False,
    skill_id="demo",
    is_loop=True,
    alert_enabled=False,
    window_size=96,
    skill_image_path=ICON if os.path.exists(ICON) else None,
    sound_manager=None,
    title="循環測試",
)

start_perf = time.perf_counter()
start_dt = datetime.now()
state = {"loops": 0, "last_start": skillwin.start_time, "err_ms": 0.0}


def observe():
    # 零侵入：只讀 start_time，變了就代表新一輪開始
    cur = skillwin.start_time
    if cur != state["last_start"]:
        state["last_start"] = cur
        state["loops"] += 1
        elapsed = time.perf_counter() - start_perf
        state["err_ms"] = (elapsed - state["loops"] * COOLDOWN) * 1000


obs = QTimer()
obs.setInterval(20)
obs.timeout.connect(observe)
obs.start()

# 計分板視窗
board = QWidget()
board.setWindowTitle("秒差即時驗證")
board.setWindowFlags(Qt.WindowStaysOnTopHint)
board.setStyleSheet("background:#1a1530;")
board.resize(760, 300)
board.move(380, 120)
lab = QLabel()
lab.setFont(QFont("Consolas", 15))
lab.setStyleSheet("color:#ffffff; padding:18px;")
lab.setTextFormat(Qt.PlainText)
lay = QVBoxLayout(board)
lay.addWidget(lab)


def refresh():
    now = datetime.now()
    elapsed = time.perf_counter() - start_perf
    lines = [
        "技能循環秒差 — 真實 SkillWindow 即時驗證",
        "──────────────────────────────",
        f"啟動系統時間 : {hms(start_dt)}",
        f"現在系統時間 : {hms(now)}   ← 可對你工作列時鐘",
        f"已經過       : {elapsed:6.1f} s",
        f"循環次數     : {state['loops']:3d}    (每輪 {COOLDOWN}s)",
        f"理想累積     : {state['loops'] * COOLDOWN:6.1f} s",
        f"累積誤差     : {state['err_ms']:+7.0f} ms   ← 應接近 0，不隨時間變大",
    ]
    lab.setText("\n".join(lines))


ui = QTimer()
ui.setInterval(100)
ui.timeout.connect(refresh)
ui.start()
refresh()
board.show()
board.raise_()


def snap(tag):
    try:
        QApplication.primaryScreen().grabWindow(0).save(f"_drift_demo_{tag}.png")
    except Exception as e:
        print(f"  (整桌面截圖失敗: {e})")
    board.grab().save(f"_drift_demo_{tag}_board.png")
    print(f"  [{tag}] loops={state['loops']} err={state['err_ms']:+.0f}ms "
          f"sysclock={hms(datetime.now())}")


QTimer.singleShot(2500, lambda: snap("start"))
QTimer.singleShot(int(DURATION * 1000 * 0.5), lambda: snap("mid"))


def finish():
    snap("end")
    print(f"\n結束：{state['loops']} 輪 / 經過 {time.perf_counter()-start_perf:.1f}s / "
          f"累積誤差 {state['err_ms']:+.0f} ms")
    app.quit()


QTimer.singleShot(int(DURATION * 1000), finish)

print(f"啟動真實視窗示範（on_screen={on_screen}）：{COOLDOWN}s 循環，跑 {DURATION}s")
print(f"系統起始時間 {hms(start_dt)}")
app.exec()

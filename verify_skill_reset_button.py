"""
技能小窗重置鈕 + 循環常駐顯示驗證

驗證兩件事：

1. 重置鈕（關閉鈕左側）
   - 位置：與關閉鈕同尺寸、緊鄰左側、不重疊、不超出小窗
   - hover：重置 / 關閉各自顯示 tooltip、滑出清掉 hover 高亮
   - 點擊：倒數直接歸零、停止計時、不播音效
   - 循環：歸零後停住不再跑下一輪
   - 常駐 / 怪物正數：歸零後停在 0 待機
   - 一般技能：歸零後比照自然結束自動關閉

2. 循環技能與常駐一樣常駐顯示
   - initialize_persistent_skills() 會為循環技能建立 0 待機小窗
   - 該小窗 is_loop=True、初始不計時，等待快捷鍵觸發

執行：python verify_skill_reset_button.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QPoint, QPointF, QEvent
from PySide6.QtGui import QMouseEvent

from src.ui.skill_window import SkillWindow
from src.ui.window_manager import WindowManager

HERE = os.path.dirname(os.path.abspath(__file__))
ICON = os.path.join(HERE, "icon.png")

_failures: list[str] = []


def check(label: str, got, expected):
    """比對實際值與期待值並記錄失敗項"""
    if got == expected:
        print(f"  OK   {label}")
    else:
        print(f"  FAIL {label}: got {got!r}, expected {expected!r}")
        _failures.append(label)


def check_true(label: str, cond):
    """斷言條件為真"""
    check(label, bool(cond), True)


def make_window(**kwargs) -> SkillWindow:
    """建立測試用小窗（預設 60 秒倒數、無音效）"""
    params = dict(
        skill={"name": "重置測試", "cooldown": 60},
        player="",
        position=(400, 300),
        skill_image=None,
        on_close=lambda w: None,
        enable_sound=False,
        skill_id="reset_demo",
        window_size=96,
        skill_image_path=ICON if os.path.exists(ICON) else None,
        sound_manager=None,
    )
    params.update(kwargs)
    return SkillWindow(**params)


def click(win: SkillWindow, point: QPoint):
    """對小窗指定座標送出一次左鍵按下事件"""
    ev = QMouseEvent(
        QEvent.Type.MouseButtonPress,
        QPointF(point),
        QPointF(win.mapToGlobal(point)),
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    win.mousePressEvent(ev)


def move_to(win: SkillWindow, point: QPoint):
    """對小窗指定座標送出一次滑鼠移動事件"""
    ev = QMouseEvent(
        QEvent.Type.MouseMove,
        QPointF(point),
        QPointF(win.mapToGlobal(point)),
        Qt.MouseButton.NoButton,
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
    )
    win.mouseMoveEvent(ev)


# --------------------------------------------------
# 1. 幾何
# --------------------------------------------------

def test_geometry(app):
    print("[test_geometry]")
    win = make_window()

    r, c = win._reset_rect, win._close_rect
    check("重置鈕與關閉鈕同尺寸", (r.width(), r.height()), (c.width(), c.height()))
    check("重置鈕與關閉鈕同一列", r.y(), c.y())
    check_true("重置鈕在關閉鈕左側", r.right() < c.left())
    check_true("兩鈕不重疊", not r.intersects(c))
    check_true("重置鈕未超出小窗左緣", r.left() >= 0)
    check_true("重置鈕在圖片區內", r.top() >= win._img_y0)
    check("重置鈕 tooltip", win.RESET_TOOLTIP, "重置")
    check("關閉鈕 tooltip", win.CLOSE_TOOLTIP, "關閉")

    win.close()


# --------------------------------------------------
# 2. hover / tooltip
# --------------------------------------------------

def test_hover(app):
    print("[test_hover]")
    win = make_window()

    move_to(win, win._reset_rect.center())
    check("hover 重置鈕", win._reset_hovered, True)
    check("hover 重置鈕時關閉鈕不亮", win._close_hovered, False)

    move_to(win, win._close_rect.center())
    check("hover 關閉鈕", win._close_hovered, True)
    check("hover 關閉鈕時重置鈕不亮", win._reset_hovered, False)

    win.leaveEvent(QEvent(QEvent.Type.Leave))
    check("滑鼠離開後 hover 全清", (win._close_hovered, win._reset_hovered), (False, False))

    win.close()


# --------------------------------------------------
# 3. 點擊分派
# --------------------------------------------------

def test_click_dispatch(app):
    print("[test_click_dispatch]")
    calls = {"reset": 0, "drag": 0}

    win = make_window(on_drag_start=lambda x, y: calls.__setitem__("drag", calls["drag"] + 1))
    win.reset_to_zero = lambda: calls.__setitem__("reset", calls["reset"] + 1)

    click(win, win._reset_rect.center())
    check("點重置鈕 → reset_to_zero", calls["reset"], 1)
    check("點重置鈕不啟動拖曳", calls["drag"], 0)

    click(win, QPoint(win._canvas_width // 2, win._img_y1 - 4))
    check("點圖片本體 → 開始拖曳", calls["drag"], 1)

    win.close()


# --------------------------------------------------
# 4. 歸零語意
# --------------------------------------------------

def test_reset_running_countdown(app):
    print("[test_reset_running_countdown]")
    played = []
    win = make_window(enable_sound=True)
    win._play_sound = lambda: played.append(1)

    check("初始計時中", win.running, True)
    win.reset_to_zero()

    check("歸零後停止計時", win.running, False)
    check("remaining 歸零", win.remaining, 0)
    check("顯示 0", win._current_display_text, "0")
    check("不播完成音", played, [])

    win.close()


def test_reset_loop_stops(app):
    print("[test_reset_loop_stops]")
    win = make_window(is_loop=True)
    restarts = []
    win._loop_restart = lambda: restarts.append(1)

    win.reset_to_zero()
    check("循環歸零後停止", win.running, False)
    check("循環不續跑下一輪", restarts, [])
    check("循環小窗留在畫面上", win._closed, False)

    app.processEvents()
    check("循環歸零後仍不計時", win.running, False)

    win.close()


def test_reset_permanent_idle(app):
    print("[test_reset_permanent_idle]")
    win = make_window(is_permanent=True, start_at_zero=True)
    win.restart_countdown()
    check("常駐按鍵後開始計時", win.running, True)

    win.reset_to_zero()
    check("常駐歸零後待機", (win.running, win.remaining), (False, 0))
    check("常駐小窗不關閉", win._closed, False)

    win.restart_countdown()
    check("待機後可再次觸發", win.running, True)

    win.close()


def test_reset_count_up_idle(app):
    print("[test_reset_count_up_idle]")
    win = make_window(
        skill={"name": "怪物", "respawn_time": 60},
        count_up=True,
        is_permanent=True,
    )
    win.reset_to_zero()
    check("怪物正數歸零後待機", (win.running, win.remaining), (False, 0))
    check("怪物小窗不關閉", win._closed, False)

    win.close()


def test_reset_normal_auto_close(app):
    print("[test_reset_normal_auto_close]")
    closed = []
    win = make_window(on_close=lambda w: closed.append(1))

    win.reset_to_zero()
    check("一般技能歸零瞬間尚未關閉", win._closed, False)

    # 自然結束同樣是 2 秒後關閉，這裡直接把排程的 singleShot 跑完
    from PySide6.QtCore import QEventLoop, QTimer
    loop = QEventLoop()
    QTimer.singleShot(2400, loop.quit)
    loop.exec()

    check("一般技能歸零 2 秒後自動關閉", win._closed, True)
    check("關閉有回呼 on_close", closed, [1])


# --------------------------------------------------
# 5. 循環常駐顯示
# --------------------------------------------------

class _FakeSkillManager:
    """最小 skill_manager 替身"""

    def __init__(self, skills):
        self._skills = skills
        self.skill_images = {}
        self.skill_image_paths = {
            sid: (ICON if os.path.exists(ICON) else None) for sid in skills
        }

    def get_skill(self, skill_id):
        return self._skills.get(skill_id)


class _FakeApp:
    """最小 app 替身，只提供 WindowManager 需要的欄位"""

    def __init__(self, skills, permanent, loop):
        self.skill_manager = _FakeSkillManager(skills)
        self.skill_permanent = permanent
        self.skill_loop = loop
        self.skill_alert_enabled = {sid: False for sid in skills}
        self.player_name = ""
        self.enable_sound = False
        self.enable_end_sound = False
        self.enable_alert_sound = False
        self.window_alpha = 0.95
        self.window_size = 96
        self.skill_start_x = 400
        self.skill_start_y = 300
        self.sound_manager = None

    def get_alert_seconds(self, skill_id):
        return 0

    def get_sound_for_skill(self, skill_id):
        return ""

    def get_alert_sound_for_skill(self, skill_id):
        return ""

    def get_all_monsters(self):
        return []


def test_loop_is_persistent(app):
    print("[test_loop_is_persistent]")
    skills = {
        "perm_skill": {"name": "常駐技", "cooldown": 30},
        "loop_skill": {"name": "循環技", "cooldown": 30},
        "plain_skill": {"name": "一般技", "cooldown": 30},
    }
    fake = _FakeApp(
        skills,
        permanent={"perm_skill": True, "loop_skill": False, "plain_skill": False},
        loop={"perm_skill": False, "loop_skill": True, "plain_skill": False},
    )
    wm = WindowManager(fake)
    wm.initialize_persistent_skills()

    check("常駐技能開機即顯示", "perm_skill" in wm.active_windows, True)
    check("循環技能開機即顯示", "loop_skill" in wm.active_windows, True)
    check("一般技能不顯示", "plain_skill" in wm.active_windows, False)

    lw = wm.active_windows["loop_skill"]
    check("循環小窗 is_loop", lw.is_loop, True)
    check("循環小窗非常駐", lw.is_permanent, False)
    check("循環小窗初始待機不計時", lw.running, False)
    check("循環小窗初始顯示 0", lw._current_display_text, "0")

    pw = wm.active_windows["perm_skill"]
    check("常駐小窗 is_permanent", pw.is_permanent, True)
    check("常駐小窗非循環", pw.is_loop, False)

    wm.trigger_skill("loop_skill")
    check("循環小窗按鍵後開始計時", wm.active_windows["loop_skill"].running, True)

    wm.close_all()


def main():
    app = QApplication.instance() or QApplication(sys.argv)

    test_geometry(app)
    test_hover(app)
    test_click_dispatch(app)
    test_reset_running_countdown(app)
    test_reset_loop_stops(app)
    test_reset_permanent_idle(app)
    test_reset_count_up_idle(app)
    test_reset_normal_auto_close(app)
    test_loop_is_persistent(app)

    print()
    if _failures:
        print(f"FAILED: {len(_failures)} check(s)")
        for f in _failures:
            print(f"  - {f}")
        return 1
    print("All checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

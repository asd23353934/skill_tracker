"""離屏渲染 V2 預覽 → PNG，供 Claude 自我檢查"""
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from main_v2 import PreviewWindow
from src.ui_v2.theme_v2 import V2Theme as T
from src.ui_v2.dialogs.skill_detail_dialog_v2 import SkillDetailDialogV2

app = QApplication(sys.argv)
app.setStyleSheet(T.global_qss())
win = PreviewWindow()
win.resize(1240, 760)
win.show()

def shoot_page():
    win.grab().save("_shot_page.png", "PNG")
    # 切到怪物頁
    win.sidebar._select("monster")
    QTimer.singleShot(200, shoot_monster)

def shoot_monster():
    win.grab().save("_shot_monster.png", "PNG")
    win.sidebar._select("overlay")
    QTimer.singleShot(200, shoot_overlay)

def shoot_overlay():
    win.grab().save("_shot_overlay.png", "PNG")
    win.sidebar._select("potion")
    QTimer.singleShot(200, shoot_potion)

def shoot_potion():
    win.grab().save("_shot_potion.png", "PNG")
    win.sidebar._select("mapleworld")
    QTimer.singleShot(200, shoot_mw)

def shoot_mw():
    win.grab().save("_shot_mapleworld.png", "PNG")
    dlg = SkillDetailDialogV2(win, "劍氣縱橫")
    dlg.show()
    QTimer.singleShot(300, lambda: shoot_dlg(dlg))

def shoot_dlg(dlg):
    dlg.grab().save("_shot_dialog.png", "PNG")
    app.quit()

QTimer.singleShot(400, shoot_page)
sys.exit(app.exec())

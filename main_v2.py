"""
V2 UI 預覽入口 — Soft Purple Gradient Dashboard
頁首無底線；唯一邊線在側邊欄右側
背景使用紫色漸層
執行：python main_v2.py
"""

import os
import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget,
)
from PySide6.QtCore import Qt, QTimer
from src.ui.dispatcher import Dispatcher

from src.ui_v2.theme_v2 import V2Theme as T
from src.ui_v2.header_v2 import HeaderV2
from src.ui_v2.sidebar_v2 import SidebarV2
from src.ui_v2.placeholder_page import PlaceholderPage
from src.ui_v2.pages.skill_page_v2 import SkillPageV2
from src.ui_v2.pages.monster_page_v2 import MonsterPageV2
from src.ui_v2.pages.overlay_page_v2 import OverlayPageV2
from src.ui_v2.pages.potion_page_v2 import PotionPageV2
from src.ui_v2.pages.mapleworld_page_v2 import MapleWorldPageV2

from src.infrastructure.config_manager import ConfigManager
from src.infrastructure.helpers import resource_path
from src.ui.app_core import AppCoreMixin


class V2AppContext(AppCoreMixin):
    """V2 預覽 app backing — 透過 AppCoreMixin 取得完整 domain 層。

    繼承 AppCoreMixin 後即可呼叫所有 V1/V2 共用方法（edit_cooldown / toggle_all
    / show_skill_detail / …），並擁有 SkillManager / HotkeyManager /
    WindowManager / SoundManager / OverlayManager 等 backing。

    額外提供：
        toast (NoopToast) / after / overlay_page slot
    """

    def __init__(self):
        # 跨執行緒安全 dispatcher（pynput daemon → 主執行緒）；
        # 必須在 _init_domain_backing 前建好，因 hotkey/window manager 之後會 capture self
        self._dispatcher = Dispatcher(QApplication.instance())
        self._init_domain_backing(ConfigManager(resource_path("config.json")))
        self.overlay_page = None
        self.toast = _NoopToast()
        # V1 UI 元件 stub —— HotkeyManager / WindowManager 會呼叫
        self.header = _NoopHeader()
        self.monster_page = _NoopMonsterPage()
        # V2 shell 預覽：啟動 hotkey + 還原常駐視窗，行為與 V1 等價
        self.hotkey_manager.start()
        self.window_manager.initialize_persistent_skills()

    def after(self, ms: int, fn):
        """執行緒安全：透過 _Dispatcher 排回主執行緒（V1 等價）"""
        self._dispatcher.schedule(ms, fn)


class _NoopToast:
    def show(self, msg, kind="info"):
        print(f"[toast/{kind}] {msg}")


class _NoopHeader:
    """V1 Header stub — HotkeyManager hint 接收後 print 到 console。"""
    def show_hotkey_hint(self, *args, **kwargs):
        print(f"[hotkey-hint] {args} {kwargs}")
    def clear_hotkey_hint(self):
        pass


class _NoopMonsterPage:
    """V1 MonsterPage stub — V2 monster page 接線後可移除。"""
    cards: dict = {}


PAGES = [
    ("skill",      "技能總覽"),
    ("monster",    "怪物總覽"),
    ("overlay",    "浮動圖片"),
    ("potion",     "費用分析"),
    ("mapleworld", "資源中心"),
]


class PreviewWindow(QMainWindow):
    """V2 預覽主視窗 — 無框 1240x760"""

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.resize(1240, 760)
        self.setMinimumSize(1000, 640)
        self.app_ctx = V2AppContext()
        self._build()

    def _build(self):
        # 主背景：紫色漸層
        root = QWidget()
        root.setObjectName("root_v2")
        root.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        root.setStyleSheet(
            f"QWidget#root_v2 {{ background: {T.bg_gradient()}; }}"
        )

        outer = QHBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── 側邊欄（左）──
        self.sidebar = SidebarV2(root, self._on_page_change)
        outer.addWidget(self.sidebar)

        # ── 右側：header + content ──
        right = QVBoxLayout()
        right.setContentsMargins(0, 0, 0, 0)
        right.setSpacing(0)

        self.header = HeaderV2(root, self)
        right.addWidget(self.header)

        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background: transparent;")
        self.pages = {}
        for key, title in PAGES:
            if key == "skill":
                page = SkillPageV2(self.stack, self.app_ctx)
            elif key == "monster":
                page = MonsterPageV2(self.stack, self.app_ctx)
            elif key == "overlay":
                page = OverlayPageV2(self.stack, self.app_ctx)
                self.app_ctx.overlay_page = page
            elif key == "potion":
                page = PotionPageV2(self.stack, self.app_ctx)
            elif key == "mapleworld":
                page = MapleWorldPageV2(self.stack, self.app_ctx)
            else:
                page = PlaceholderPage(self.stack, title)
            self.stack.addWidget(page)
            self.pages[key] = page
        right.addWidget(self.stack, 1)

        right_wrap = QWidget()
        right_wrap.setLayout(right)
        outer.addWidget(right_wrap, 1)

        self.setCentralWidget(root)
        self._on_page_change("skill")

    def _on_page_change(self, key):
        page = self.pages.get(key)
        if page:
            self.stack.setCurrentWidget(page)


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(T.global_qss())
    win = PreviewWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

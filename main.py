"""
技能追蹤器 - 主程式入口
Artale 楓之谷技能冷卻追蹤工具 — PySide6 版本
"""

import sys
import os

# 添加專案根目錄到路徑
sys.path.insert(0, os.path.dirname(__file__))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QSharedMemory
from src.ui.app import App
from src.ui.theme import AppTheme


_SINGLE_INSTANCE_KEY = "skill_tracker_artale_single_instance"


def _acquire_single_instance_lock() -> QSharedMemory | None:
    """佔用 shared memory key；若已被占用代表另一個實例已在執行，回 None。

    回傳的 QSharedMemory 必須由呼叫方持有到程式結束才不會釋放鎖。
    """
    shm = QSharedMemory(_SINGLE_INSTANCE_KEY)
    # 殘留鎖（前次崩潰未釋放）：先 attach 一次再丟掉，讓 OS 清理
    if shm.attach():
        shm.detach()
    if not shm.create(1):
        return None
    return shm


def main():
    """主程式

    用法：
        python main.py        # V2 正式 UI（預設）
        python main.py --v1   # V1 舊版 UI（保留 opt-in，未來移除）
    """
    qt_app = QApplication(sys.argv)
    # 防多開：V1 / V2 共用同一把鎖
    _lock = _acquire_single_instance_lock()
    if _lock is None:
        sys.exit(0)

    if "--v1" in sys.argv:
        qt_app.setStyleSheet(AppTheme.build_stylesheet())
        window = App()
        sys.exit(qt_app.exec())
        return

    from main_v2 import main as v2_main
    v2_main()


if __name__ == "__main__":
    main()

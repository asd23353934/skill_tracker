"""
技能追蹤器 - 主程式入口
Artale 楓之谷技能冷卻追蹤工具 — PySide6 版本
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QSharedMemory


_SINGLE_INSTANCE_KEY = "skill_tracker_artale_single_instance"


def _acquire_single_instance_lock() -> QSharedMemory | None:
    """佔用 shared memory key；若已被占用代表另一個實例已在執行，回 None。

    回傳的 QSharedMemory 必須由呼叫方持有到程式結束才不會釋放鎖。
    """
    shm = QSharedMemory(_SINGLE_INSTANCE_KEY)
    if shm.attach():
        shm.detach()
    if not shm.create(1):
        return None
    return shm


def main():
    """主程式 — 進入 V2 UI"""
    QApplication(sys.argv)
    _lock = _acquire_single_instance_lock()
    if _lock is None:
        sys.exit(0)

    from main_v2 import main as v2_main
    v2_main()


if __name__ == "__main__":
    main()

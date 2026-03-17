"""
技能追蹤器 - 主程式入口
Artale 楓之谷技能冷卻追蹤工具 — PySide6 版本
"""

import sys
import os

# 添加專案根目錄到路徑
sys.path.insert(0, os.path.dirname(__file__))

from PySide6.QtWidgets import QApplication
from src.ui.app import App
from src.ui.theme import AppTheme


def main():
    """主程式"""
    qt_app = QApplication(sys.argv)
    qt_app.setStyleSheet(AppTheme.build_stylesheet())

    window = App()
    sys.exit(qt_app.exec())


if __name__ == "__main__":
    main()

"""
技能追蹤器 - 主程式入口
Artale 楓之谷技能冷卻追蹤工具
"""

import sys
import os

# 添加專案根目錄到路徑
sys.path.insert(0, os.path.dirname(__file__))

from src.ui.main_window import MainWindow


def main():
    """主程式"""
    app = MainWindow()
    app.run()


if __name__ == "__main__":
    main()

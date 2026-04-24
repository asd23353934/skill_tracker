"""pytest 基礎設定：把專案根目錄加進 sys.path，讓 src.* import 可用"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

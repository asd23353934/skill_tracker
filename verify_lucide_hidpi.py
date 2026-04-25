"""
驗證 src/ui_v2/lucide.py 的 high-DPI 修復

執行：
    python verify_lucide_hidpi.py

涵蓋 4 個 case：
    A. DPR=1.0：pixmap 物理尺寸 = logical size，setDevicePixelRatio 設為 1.0
    B. DPR=1.5：pixmap 物理尺寸 = round(size*1.5)，dpr 設為 1.5
    C. DPR=2.0：pixmap 物理尺寸 = size*2，dpr 設為 2.0
    D. cache key 包含 dpr：不同 dpr 不會撞 cache
"""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication
_app = QApplication.instance() or QApplication(sys.argv)

from unittest.mock import patch
from src.ui_v2 import lucide


def _run_with_dpr(dpr: float, size: int = 16):
    lucide._cache.clear()
    with patch.object(lucide, "_device_pixel_ratio", return_value=dpr):
        pix = lucide.lucide_pixmap("settings", color="#ffffff", size=size)
    return pix


def case_a_dpr_1():
    pix = _run_with_dpr(1.0, size=16)
    assert pix.width() == 16, f"DPR=1.0 物理寬度應為 16, got {pix.width()}"
    assert pix.height() == 16, f"DPR=1.0 物理高度應為 16, got {pix.height()}"
    assert abs(pix.devicePixelRatio() - 1.0) < 1e-6, f"DPR=1.0 設定錯誤: {pix.devicePixelRatio()}"
    print(f"[A] PASS — DPR=1.0 → {pix.width()}x{pix.height()} px, dpr={pix.devicePixelRatio()}")


def case_b_dpr_1_5():
    pix = _run_with_dpr(1.5, size=16)
    assert pix.width() == 24, f"DPR=1.5 物理寬度應為 24, got {pix.width()}"
    assert pix.height() == 24, f"DPR=1.5 物理高度應為 24, got {pix.height()}"
    assert abs(pix.devicePixelRatio() - 1.5) < 1e-6, f"DPR=1.5 設定錯誤: {pix.devicePixelRatio()}"
    print(f"[B] PASS — DPR=1.5 → {pix.width()}x{pix.height()} px, dpr={pix.devicePixelRatio()}")


def case_c_dpr_2():
    pix = _run_with_dpr(2.0, size=16)
    assert pix.width() == 32, f"DPR=2.0 物理寬度應為 32, got {pix.width()}"
    assert pix.height() == 32, f"DPR=2.0 物理高度應為 32, got {pix.height()}"
    assert abs(pix.devicePixelRatio() - 2.0) < 1e-6, f"DPR=2.0 設定錯誤: {pix.devicePixelRatio()}"
    print(f"[C] PASS — DPR=2.0 → {pix.width()}x{pix.height()} px, dpr={pix.devicePixelRatio()}")


def case_d_cache_key_includes_dpr():
    """cache key 不包含 dpr 的話，不同 dpr 會誤撞 cache 拿到錯尺寸"""
    lucide._cache.clear()
    with patch.object(lucide, "_device_pixel_ratio", return_value=1.0):
        pix1 = lucide.lucide_pixmap("settings", color="#ffffff", size=16)
    with patch.object(lucide, "_device_pixel_ratio", return_value=2.0):
        pix2 = lucide.lucide_pixmap("settings", color="#ffffff", size=16)
    assert pix1.width() == 16, f"DPR=1.0 應回 16 px, got {pix1.width()}"
    assert pix2.width() == 32, f"DPR=2.0 應回 32 px, got {pix2.width()}"
    assert len(lucide._cache) == 2, f"應有 2 筆 cache, got {len(lucide._cache)}"
    print(f"[D] PASS — cache key 區分 dpr：{pix1.width()} vs {pix2.width()}, cache 筆數 {len(lucide._cache)}")


def main():
    cases = [case_a_dpr_1, case_b_dpr_1_5, case_c_dpr_2, case_d_cache_key_includes_dpr]
    failures = []
    for c in cases:
        try:
            c()
        except AssertionError as e:
            failures.append((c.__name__, str(e)))
            print(f"[{c.__name__}] FAIL — {e}")
        except Exception as e:
            failures.append((c.__name__, f"{type(e).__name__}: {e}"))
            print(f"[{c.__name__}] ERROR — {type(e).__name__}: {e}")

    print()
    if failures:
        print(f"FAILED: {len(failures)}/{len(cases)}")
        for name, msg in failures:
            print(f"  - {name}: {msg}")
        sys.exit(1)
    print(f"ALL PASSED: {len(cases)}/{len(cases)}")


if __name__ == "__main__":
    main()

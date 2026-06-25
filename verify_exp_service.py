"""exp_service / exp_table 單元驗證腳本（純邏輯層，無 Qt）

涵蓋 spec「exp-calculator」的計算需求與邊界：
- 經驗表錨點（Lv1=15 / Lv2=34 / Lv3=57 / Lv10=1716）與跨來源核對後的高段抽樣
- exp_remaining 範例（Lv10 @50% → Lv12 = 3218）與整級加總
- target<=level、Lv200 封頂、pct 邊界
- time_hours / 零速率 → None / format_duration（時分秒 HH:MM:SS）
- hourly_rate（由 10 / 30 / 60 分鐘區間經驗推每小時速率）
- domain 層不得載入 PySide6

直接執行：python verify_exp_service.py
"""

import sys

try:                                    # Windows cp950 console 無法輸出 ✓/✗，轉 utf-8
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def check(cond, msg):
    if not cond:
        print(f"  ✗ {msg}")
        raise AssertionError(msg)
    print(f"  ✓ {msg}")


def test_exp_table():
    from src.domain.exp_table import EXP_TO_NEXT, MAX_LEVEL
    check(MAX_LEVEL == 200, "MAX_LEVEL == 200")
    check(set(EXP_TO_NEXT) == set(range(1, 200)), "EXP_TO_NEXT 涵蓋 Lv1..199")
    check(EXP_TO_NEXT[1] == 15 and EXP_TO_NEXT[2] == 34 and EXP_TO_NEXT[3] == 57,
          "錨點 Lv1=15 / Lv2=34 / Lv3=57")
    check(EXP_TO_NEXT[10] == 1716, "錨點 Lv10=1716（canonical pre-BB）")
    # 跨來源核對後的高段抽樣
    for lv, v in {50: 709716, 70: 2062925, 100: 10223168,
                  120: 29715818, 150: 147262175, 199: 2011069705}.items():
        check(EXP_TO_NEXT[lv] == v, f"高段抽樣 Lv{lv}={v:,}")
    check(sum(EXP_TO_NEXT.values()) == 38703363662,
          "Lv1→200 累計總經驗 = 38,703,363,662")


def test_exp_remaining():
    from src.domain.exp_service import exp_remaining, exp_remaining_in_level
    # spec 範例：Lv10 @50% → Lv12
    check(exp_remaining_in_level(10, 50) == 858, "Lv10 @50% 距下一級 = round(1716×0.5)=858")
    check(exp_remaining(10, 50, 12) == 3218, "exp_remaining(10,50,12) = 858 + 2360 = 3218")
    # 整級：Lv10 @0% → Lv11 = 整個 Lv10
    check(exp_remaining(10, 0, 11) == 1716, "exp_remaining(10,0,11) = 1716")
    # target <= level → 0
    check(exp_remaining(50, 0, 50) == 0, "target == level → 0")
    check(exp_remaining(50, 30, 40) == 0, "target < level → 0")
    # pct 邊界夾值
    check(exp_remaining_in_level(10, -5) == 1716, "pct<0 夾為 0")
    check(exp_remaining_in_level(10, 150) == 0, "pct>100 夾為 100 → 0 剩餘")
    # Lv200 封頂不爆 key
    check(exp_remaining(200, 0, 200) == 0, "Lv200 封頂 → 0")
    check(exp_remaining_in_level(200, 0) == 0, "Lv200 無下一級 → 0")
    # 等級超界夾值（不丟例外）
    check(exp_remaining(0, 0, 5) == exp_remaining(1, 0, 5), "level<1 夾為 1")


def test_rate_and_time():
    from src.domain.exp_service import (
        time_hours, hourly_rate, format_duration,
    )
    # 由區間經驗推每小時速率
    check(hourly_rate(10000, 10) == 60000, "10分鐘10000 → 60000/hr")
    check(hourly_rate(30000, 30) == 60000, "30分鐘30000 → 60000/hr")
    check(hourly_rate(60000, 60) == 60000, "1小時60000 → 60000/hr")
    check(hourly_rate(0, 10) == 0, "經驗0 → 0/hr")
    check(time_hours(120000, 60000) == 2.0, "time_hours(120000,60000)=2.0")
    check(time_hours(1000, 0) is None, "每小時經驗 0 → time None")
    # 時分秒
    check(format_duration(2.0) == "02:00:00", "format_duration(2.0)=02:00:00")
    check(format_duration(1.5) == "01:30:00", "format_duration(1.5)=01:30:00")
    check(format_duration(1/3600) == "00:00:01", "format_duration(1秒)=00:00:01")
    check(format_duration(None) == "—", "format_duration(None)=—")


def test_no_qt():
    import src.domain.exp_service  # noqa: F401
    import src.domain.exp_table    # noqa: F401
    check("PySide6" not in sys.modules,
          "exp_service / exp_table 未載入 PySide6（domain 層零 Qt）")


def main():
    print("=== exp_table ===")
    test_exp_table()
    print("=== exp_remaining ===")
    test_exp_remaining()
    print("=== rate / time ===")
    test_rate_and_time()
    print("=== no-Qt ===")
    test_no_qt()
    print("\nALL PASS — exp_service / exp_table")


if __name__ == "__main__":
    main()

"""
PotionService 單元驗證腳本（專案無 tests/，先以獨立腳本涵蓋 spec example）
執行：`python verify_potion_service.py` —— 全部通過時 exit code = 0
"""

from __future__ import annotations

import sys

from src.domain.potion_service import PotionService


_failures: list[str] = []


def check(label: str, got, expected):
    if got == expected:
        print(f"  OK   {label}")
    else:
        print(f"  FAIL {label}: got {got!r}, expected {expected!r}")
        _failures.append(label)


def test_defaults_catalog():
    """PotionService provides default potion catalog"""
    print("[test_defaults_catalog]")
    check("keys are hp/mp/combined",
          sorted(PotionService.DEFAULTS.keys()),
          ["combined", "hp", "mp"])
    check("first hp entry",
          PotionService.DEFAULTS["hp"][0],
          {"name": "馴鹿奶", "price": 5600})


def test_calc_row_cost_edge_cases():
    """calc_row_cost edge cases from spec"""
    print("[test_calc_row_cost_edge_cases]")
    cases = [
        ({"price": 100, "before": 50, "after": 30}, 2000),
        ({"price": 100, "before": 30, "after": 50}, 0),
        ({"price": 0,   "before": 50, "after": 0},  0),
        ({},                                         0),
        ({"price": 5600, "before": 200, "after": 200}, 0),
    ]
    for row, expected in cases:
        check(f"row={row}", PotionService.calc_row_cost(row), expected)


def test_calc_section_subtotal():
    """calc_section_subtotal: empty + multi + cost-fast-path"""
    print("[test_calc_section_subtotal]")
    check("empty list", PotionService.calc_section_subtotal([]), 0)
    check("two rows sum",
          PotionService.calc_section_subtotal([
              {"price": 100, "before": 10, "after": 5},
              {"price": 200, "before": 3,  "after": 1},
          ]),
          900)
    # 優先讀 row["cost"] 的快路徑：即使 price/before/after 不一致也以 cost 為準
    check("cost fast-path",
          PotionService.calc_section_subtotal([
              {"price": 999, "before": 999, "after": 0, "cost": 123},
              {"price": 0,   "before": 0,   "after": 0, "cost": 77},
          ]),
          200)


def test_calc_summary_minutes_zero():
    """minutes=0 防 0，net_60 = int(net / 1 * 60)"""
    print("[test_calc_summary_minutes_zero]")
    form = {"duration_minutes": 0, "mesos_start": 0, "mesos_end": 6000}
    s = PotionService.calc_summary(form)
    check("net", s["net"], 6000)
    check("net_60", s["net_60"], 360000)


def test_calc_summary_30min_hunt():
    """spec example: 30 分鐘打怪"""
    print("[test_calc_summary_30min_hunt]")
    form = {
        "mesos_start": 10000, "mesos_end": 50000,
        "shop_before": 0, "shop_after": 20000,
        "exp_start": 1000, "exp_end": 4000,
        "duration_minutes": 30,
        "hp_potions": [{"price": 1000, "before": 10, "after": 5}],  # 5000 expense
    }
    s = PotionService.calc_summary(form)
    expected = {
        "income": 60000, "expense": 5000, "net": 55000, "exp_total": 3000,
        "net_10": 18333, "exp_10": 1000, "net_60": 110000, "exp_60": 6000,
    }
    for k, v in expected.items():
        check(k, s[k], v)


def test_serialize_roundtrip():
    """deserialize(serialize(form)) 對 user-entered 欄位 fully-preserve"""
    print("[test_serialize_roundtrip]")
    form = {
        "duration_minutes": 45,
        "hp_potions": [
            {"name": "馴鹿奶", "price": 5600, "before": 200, "after": 150,
             "consumed": 50, "cost": 280000},
        ],
        "mp_potions": [],
        "combined_potions": [
            {"name": "超級藥水", "price": 35000, "before": 10, "after": 5,
             "consumed": 5, "cost": 175000},
        ],
        "mesos_start": 10000, "mesos_end": 50000,
        "shop_before": 0, "shop_after": 20000,
        "exp_start": 1000, "exp_end": 4000,
    }
    ser = PotionService.serialize(form)
    check("saved_at present by default", "saved_at" in ser, True)
    check("summary has 8 keys", sorted(ser["summary"].keys()),
          ["exp_10", "exp_60", "exp_total", "expense",
           "income", "net", "net_10", "net_60"])
    des = PotionService.deserialize(ser)
    for k, v in form.items():
        check(f"round-trip {k}", des[k], v)

    ser2 = PotionService.serialize(form, with_timestamp=False)
    check("with_timestamp=False omits saved_at", "saved_at" not in ser2, True)


def main():
    test_defaults_catalog()
    test_calc_row_cost_edge_cases()
    test_calc_section_subtotal()
    test_calc_summary_minutes_zero()
    test_calc_summary_30min_hunt()
    test_serialize_roundtrip()

    print()
    if _failures:
        print(f"FAILURES: {len(_failures)}")
        for f in _failures:
            print(f"  - {f}")
        sys.exit(1)
    print("All checks passed.")
    sys.exit(0)


if __name__ == "__main__":
    main()

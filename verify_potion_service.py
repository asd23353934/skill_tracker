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


def test_calc_items_total():
    """calc_items_total: 物品取得收入合計（spec example + guards）"""
    print("[test_calc_items_total]")
    check("two rows",
          PotionService.calc_items_total(
              [{"qty": 3, "unit_price": 1000}, {"qty": 5, "unit_price": 200}]),
          4000)
    check("empty", PotionService.calc_items_total([]), 0)
    check("negative price clamped",
          PotionService.calc_items_total([{"qty": 2, "unit_price": -50}]), 0)
    check("zero qty",
          PotionService.calc_items_total([{"qty": 0, "unit_price": 999}]), 0)
    check("name ignored in math",
          PotionService.calc_items_total([{"name": "緞帶", "qty": 4, "unit_price": 25}]), 100)
    # value 快路徑：含已算好的 value 直接採用
    check("value fast-path",
          PotionService.calc_items_total([{"value": 777, "qty": 1, "unit_price": 1}]), 777)


def test_calc_summary_income_expense_net():
    """收支摘要：收入＝楓幣差＋商店差＋物品；支出＝藥水；net＝收入−支出（無經驗/速率）"""
    print("[test_calc_summary_income_expense_net]")
    form = {
        "mesos_start": 10000, "mesos_end": 50000,        # +40000
        "shop_before": 0, "shop_after": 20000,           # +20000
        "item_rows": [{"qty": 63, "unit_price": 1000}],  # +63000
        "hp_potions": [{"price": 1000, "before": 10, "after": 5}],  # 5000 支出
    }
    s = PotionService.calc_summary(form)
    check("income", s["income"], 123000)               # 40000+20000+63000
    check("expense", s["expense"], 5000)
    check("net", s["net"], 118000)
    check("summary has exactly 3 keys", sorted(s.keys()),
          ["expense", "income", "net"])
    # 後<前 不為負（max(0, 後−前)）
    neg = PotionService.calc_summary({"mesos_start": 5000, "mesos_end": 3000})
    check("negative mesos diff clamped to 0 income", neg["income"], 0)


def test_serialize_roundtrip():
    """deserialize(serialize(form)) 對 user-entered 欄位 fully-preserve（含 item_rows、無 exp）"""
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
        "item_rows": [{"name": "綠水靈的水滴", "qty": 12, "stack_size": 9900, "unit_price": 50}],
    }
    ser = PotionService.serialize(form)
    check("saved_at present by default", "saved_at" in ser, True)
    check("item_rows serialized", ser["item_rows"], form["item_rows"])
    check("mesos/shop serialized", (ser["mesos_end"], ser["shop_after"]), (50000, 20000))
    check("no exp in output",
          "exp_start" not in ser and "exp_end" not in ser, True)
    check("summary has 3 keys", sorted(ser["summary"].keys()),
          ["expense", "income", "net"])
    des = PotionService.deserialize(ser)
    for k, v in form.items():
        check(f"round-trip {k}", des[k], v)

    ser2 = PotionService.serialize(form, with_timestamp=False)
    check("with_timestamp=False omits saved_at", "saved_at" not in ser2, True)


def test_deserialize_legacy_fields():
    """legacy 存檔含 exp（已廢）、mesos/shop（保留）、無 item_rows → 忽略 exp、補空 item_rows"""
    print("[test_deserialize_legacy_fields]")
    legacy = {
        "duration_minutes": 30,
        "mesos_start": 1000, "mesos_end": 5000,
        "shop_before": 0, "shop_after": 2000,
        "exp_start": 1000, "exp_end": 4000,   # 廢棄欄位
        "hp_potions": [{"price": 100, "before": 10, "after": 5}],
    }
    des = PotionService.deserialize(legacy)
    check("legacy exp dropped",
          "exp_start" not in des and "exp_end" not in des, True)
    check("mesos/shop preserved", (des["mesos_end"], des["shop_after"]), (5000, 2000))
    check("item_rows defaulted to []", des["item_rows"], [])
    check("potion rows preserved", len(des["hp_potions"]), 1)


def main():
    test_defaults_catalog()
    test_calc_row_cost_edge_cases()
    test_calc_section_subtotal()
    test_calc_items_total()
    test_calc_summary_income_expense_net()
    test_serialize_roundtrip()
    test_deserialize_legacy_fields()

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

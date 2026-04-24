"""domain.potion_service 測試 — 純計算 / serialize round-trip / autosave 注入"""

import pytest

from src.domain.potion_service import PotionService, _as_nonneg_int


# ── _as_nonneg_int helper ───────────────────────────────────

@pytest.mark.parametrize("src,expected", [
    (0, 0),
    (5, 5),
    (-3, 0),
    ("12", 12),
    ("-7", 0),
    ("abc", 0),
    (None, 0),
    (1.9, 1),
    ([], 0),
])
def test_as_nonneg_int(src, expected):
    assert _as_nonneg_int(src) == expected


# ── calc_row_cost ────────────────────────────────────────────

def test_calc_row_cost_basic():
    assert PotionService.calc_row_cost({"price": 100, "before": 50, "after": 30}) == 2000


def test_calc_row_cost_negative_consumed_clamped_zero():
    # after > before 不扣錢
    assert PotionService.calc_row_cost({"price": 100, "before": 30, "after": 50}) == 0


def test_calc_row_cost_missing_keys_all_zero():
    assert PotionService.calc_row_cost({}) == 0


def test_calc_row_cost_invalid_types_treated_as_zero():
    assert PotionService.calc_row_cost({"price": "abc", "before": None, "after": []}) == 0


# ── calc_section_subtotal ───────────────────────────────────

def test_section_subtotal_empty():
    assert PotionService.calc_section_subtotal([]) == 0
    assert PotionService.calc_section_subtotal(None) == 0  # type: ignore[arg-type]


def test_section_subtotal_uses_cached_cost_when_present():
    rows = [
        {"price": 999, "before": 10, "after": 0, "cost": 42},  # 用 cost 不重算
        {"price": 10,  "before": 5,  "after": 2},              # 計算 = 30
    ]
    assert PotionService.calc_section_subtotal(rows) == 42 + 30


def test_section_subtotal_sum():
    rows = [
        {"price": 100, "before": 5,  "after": 3},   # 200
        {"price": 50,  "before": 10, "after": 0},   # 500
    ]
    assert PotionService.calc_section_subtotal(rows) == 700


# ── calc_summary ─────────────────────────────────────────────

def test_calc_summary_basic():
    form = {
        "duration_minutes": 30,
        "hp_potions":       [{"price": 100, "before": 10, "after": 0}],  # 1000
        "mp_potions":       [{"price": 50,  "before": 20, "after": 0}],  # 1000
        "combined_potions": [],
        "mesos_start": 1000,
        "mesos_end":   5000,                          # +4000
        "shop_before": 0,
        "shop_after":  500,                           # +500
        "exp_start": 100,
        "exp_end":   1300,                            # +1200
    }
    s = PotionService.calc_summary(form)
    assert s["income"]    == 4500
    assert s["expense"]   == 2000
    assert s["net"]       == 2500
    assert s["exp_total"] == 1200
    # 30min → 60min 速率應為 ×2
    assert s["net_60"] == 5000
    assert s["exp_60"] == 2400
    # 10min 速率 = net / 30 * 10
    assert s["net_10"] == int(2500 / 30 * 10)


def test_calc_summary_zero_duration_no_divide_by_zero():
    form = {"duration_minutes": 0, "mesos_start": 0, "mesos_end": 100}
    s = PotionService.calc_summary(form)
    # denom = max(1, 0) = 1；不炸
    assert s["net_10"] == 1000
    assert s["net_60"] == 6000


def test_calc_summary_missing_fields_zero():
    s = PotionService.calc_summary({})
    assert s["income"] == 0
    assert s["expense"] == 0
    assert s["net"] == 0


def test_calc_summary_negative_mesos_diff_clamped():
    # 結束少於開始（例如死掉掉錢）→ income = 0
    form = {"mesos_start": 5000, "mesos_end": 3000, "duration_minutes": 10}
    s = PotionService.calc_summary(form)
    assert s["income"] == 0


# ── serialize / deserialize round-trip ──────────────────────

def test_serialize_includes_summary_and_timestamp():
    form = {
        "duration_minutes": 10,
        "hp_potions": [{"price": 100, "before": 5, "after": 2}],  # 300
    }
    out = PotionService.serialize(form)
    assert "saved_at" in out
    assert out["duration_minutes"] == 10
    assert out["summary"]["expense"] == 300


def test_serialize_without_timestamp():
    out = PotionService.serialize({}, with_timestamp=False)
    assert "saved_at" not in out


def test_deserialize_fills_missing_with_zero():
    form = PotionService.deserialize({"duration_minutes": 15})
    assert form["duration_minutes"] == 15
    assert form["mesos_start"] == 0
    assert form["hp_potions"] == []


def test_deserialize_drops_summary_and_saved_at():
    data = {"duration_minutes": 5, "saved_at": "2026-01-01", "summary": {"net": 999}}
    form = PotionService.deserialize(data)
    assert "summary" not in form
    assert "saved_at" not in form


def test_deserialize_none_returns_zero_filled():
    form = PotionService.deserialize(None)  # type: ignore[arg-type]
    assert form["duration_minutes"] == 0


def test_serialize_deserialize_roundtrip_numeric_fields_stable():
    original = {
        "duration_minutes": 42,
        "mesos_start": 100, "mesos_end": 200,
        "shop_before": 5, "shop_after": 50,
        "exp_start": 0, "exp_end": 500,
        "hp_potions": [], "mp_potions": [], "combined_potions": [],
    }
    serialized = PotionService.serialize(original, with_timestamp=False)
    restored = PotionService.deserialize(serialized)
    for k in ("duration_minutes", "mesos_start", "mesos_end",
              "shop_before", "shop_after", "exp_start", "exp_end"):
        assert restored[k] == original[k]


# ── Autosave 無 ConfigManager 時的行為 ──────────────────────

def test_autosave_without_config_manager_is_noop():
    svc = PotionService(config_manager=None)
    assert svc.save_autosave({}) is False
    assert svc.load_autosave() is None
    assert svc.clear_autosave() is False


def test_autosave_with_config_manager_delegates():
    class _FakeCM:
        def __init__(self):
            self.saved = None
        def save_potion_autosave(self, payload):
            self.saved = payload
            return True
        def load_potion_autosave(self):
            return {"duration_minutes": 7}
        def delete_potion_autosave(self):
            return True

    cm = _FakeCM()
    svc = PotionService(config_manager=cm)
    assert svc.save_autosave({"duration_minutes": 3}, timer_elapsed=45) is True
    assert cm.saved == {"duration_minutes": 3, "_timer_elapsed": 45}
    assert svc.load_autosave() == {"duration_minutes": 7}
    assert svc.clear_autosave() is True


def test_autosave_negative_timer_elapsed_clamped_zero():
    class _CM:
        def __init__(self):
            self.saved = None
        def save_potion_autosave(self, payload):
            self.saved = payload
            return True

    cm = _CM()
    PotionService(cm).save_autosave({}, timer_elapsed=-99)
    assert cm.saved["_timer_elapsed"] == 0

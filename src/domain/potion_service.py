"""
藥水費用計算服務
集中練功水錢的純邏輯：單列成本、分區小計、全局摘要、autosave 讀寫、紀錄序列化。
零 Qt 依賴。
"""

from __future__ import annotations

import datetime
from types import MappingProxyType
from typing import Mapping, TypedDict


class PotionRowData(TypedDict, total=False):
    """單一藥水列資料形狀"""
    name: str
    price: int
    before: int
    after: int
    consumed: int
    cost: int


class PotionSectionData(TypedDict, total=False):
    """一類藥水區塊資料形狀（目前單純為 row list 的別名，保留擴充點）"""
    rows: list[PotionRowData]


class ItemRowData(TypedDict, total=False):
    """單一物品取得列資料形狀（收入側）：收入 = qty × unit_price"""
    name: str
    qty: int
    unit_price: int
    value: int


class PotionFormData(TypedDict, total=False):
    """完整表單資料形狀（收支：藥水支出 + 撿取楓幣/商店/物品取得收入）"""
    saved_at: str
    duration_minutes: int
    hp_potions: list[PotionRowData]
    mp_potions: list[PotionRowData]
    combined_potions: list[PotionRowData]
    mesos_start: int
    mesos_end: int
    shop_before: int
    shop_after: int
    item_rows: list[ItemRowData]
    summary: dict


def _as_nonneg_int(value) -> int:
    """把任意值解成非負整數；無法解析或負值均回 0"""
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return 0


class PotionService:
    """藥水費用計算服務 — 純 Python 邏輯，無 Qt 依賴

    Args:
        config_manager: ConfigManager 實例，提供 potion autosave IO。
                        可為 None（僅用於純計算/序列化的使用情境）
    """

    DEFAULTS: Mapping[str, tuple[dict, ...]] = MappingProxyType({
        "hp": (
            {"name": "馴鹿奶",   "price": 5600},
            {"name": "乳酪",     "price": 4500},
            {"name": "棒冰棒",   "price": 2185},
            {"name": "中華拉麵", "price": 1600},
            {"name": "烤鰻魚",   "price": 1045},
            {"name": "熱狗堡",   "price": 503},
            {"name": "白色藥水", "price": 304},
            {"name": "蘋果",     "price": 28},
        ),
        "mp": (
            {"name": "黃昏之露", "price": 9690},
            {"name": "清晨之露", "price": 7695},
            {"name": "紅豆刨冰", "price": 3800},
            {"name": "礦泉水",   "price": 1567},
            {"name": "活力藥水", "price": 589},
            {"name": "藍水",     "price": 190},
        ),
        "combined": (
            {"name": "超級藥水", "price": 35000},
            {"name": "特殊藥水", "price": 24000},
            {"name": "櫻桃派",   "price": 3000},
            {"name": "西瓜",     "price": 3034},
            {"name": "蛋糕",     "price": 304},
            {"name": "巧克力",   "price": 2850},
        ),
    })

    def __init__(self, config_manager=None):
        self._config_manager = config_manager

    @staticmethod
    def calc_row_cost(row: PotionRowData) -> int:
        """計算單一列水錢

        Args:
            row: 藥水列 dict，至少可能含 `price / before / after`

        Returns:
            `max(0, before - after) * price`；缺 key 視為 0
        """
        price  = _as_nonneg_int(row.get("price"))
        before = _as_nonneg_int(row.get("before"))
        after  = _as_nonneg_int(row.get("after"))
        return max(0, before - after) * price

    @staticmethod
    def calc_section_subtotal(rows: list[PotionRowData]) -> int:
        """計算一個藥水區塊的小計（各列水錢總和）

        若 row dict 含已算好的 `"cost"` 欄位則直接採用，避免熱路徑重算。

        Args:
            rows: 藥水列 dict 清單；空 list 回 0
        """
        total = 0
        for r in rows or []:
            cost = r.get("cost")
            total += _as_nonneg_int(cost) if cost is not None else PotionService.calc_row_cost(r)
        return total

    @staticmethod
    def calc_items_total(rows: list[ItemRowData]) -> int:
        """計算物品取得收入合計（各列 qty × unit_price 之和）

        若 row dict 含已算好的 `"value"` 欄位則直接採用，避免熱路徑重算；
        qty / unit_price 缺值或負值一律視為 0。

        Args:
            rows: 物品列 dict 清單；空 / None 回 0
        """
        total = 0
        for r in rows or []:
            value = r.get("value")
            if value is not None:
                total += _as_nonneg_int(value)
            else:
                total += _as_nonneg_int(r.get("qty")) * _as_nonneg_int(r.get("unit_price"))
        return total

    @staticmethod
    def calc_summary(form: PotionFormData) -> dict:
        """計算收支摘要（收入 / 支出 / 淨收支；不含經驗、不含時間速率）

        Args:
            form: 完整表單 dict；缺 key 視為 0

        Returns:
            dict with keys: income, expense, net
            收入 = 撿取楓幣差 + 商店收益差 + 物品取得合計（差值以 max(0, 後−前) 計，不為負）
        """
        mesos_start = _as_nonneg_int(form.get("mesos_start"))
        mesos_end   = _as_nonneg_int(form.get("mesos_end"))
        shop_before = _as_nonneg_int(form.get("shop_before"))
        shop_after  = _as_nonneg_int(form.get("shop_after"))
        income = (
            max(0, mesos_end - mesos_start)
            + max(0, shop_after - shop_before)
            + PotionService.calc_items_total(form.get("item_rows") or [])
        )
        expense = (
            PotionService.calc_section_subtotal(form.get("hp_potions") or [])
            + PotionService.calc_section_subtotal(form.get("mp_potions") or [])
            + PotionService.calc_section_subtotal(form.get("combined_potions") or [])
        )
        return {
            "income":  income,
            "expense": expense,
            "net":     income - expense,
        }

    # Autosave（節流 / dirty tracking 由 caller 負責）

    def save_autosave(self, form: PotionFormData, *, timer_elapsed: int = 0) -> bool:
        """寫入 autosave 檔

        Args:
            form:          表單資料；不會被修改（timer_elapsed 另存在新 dict）
            timer_elapsed: UI 計時器已累積秒數；透過顯式 keyword 傳入，避免污染 form

        Returns:
            ConfigManager 的寫入結果；未注入 ConfigManager 時回 False
        """
        if self._config_manager is None:
            return False
        payload = {**form, "_timer_elapsed": _as_nonneg_int(timer_elapsed)}
        return bool(self._config_manager.save_potion_autosave(payload))

    def load_autosave(self) -> PotionFormData | None:
        """讀取 autosave 檔，無檔案回 None"""
        if self._config_manager is None:
            return None
        return self._config_manager.load_potion_autosave()

    def clear_autosave(self) -> bool:
        """刪除 autosave 檔；未注入 ConfigManager 時回 False"""
        if self._config_manager is None:
            return False
        return bool(self._config_manager.delete_potion_autosave())

    @staticmethod
    def serialize(form: PotionFormData, *, with_timestamp: bool = True) -> dict:
        """將表單資料序列化為存檔 dict

        Args:
            form:           表單資料
            with_timestamp: 是否加入 `saved_at` ISO-8601 時間戳（autosave 可傳 False）

        Returns:
            可直接 json.dump 的 dict；summary 區塊由 `calc_summary` 計算
        """
        out: dict = {}
        if with_timestamp:
            out["saved_at"] = datetime.datetime.now().isoformat(timespec="seconds")
        out["duration_minutes"] = _as_nonneg_int(form.get("duration_minutes"))
        out["hp_potions"]       = list(form.get("hp_potions") or [])
        out["mp_potions"]       = list(form.get("mp_potions") or [])
        out["combined_potions"] = list(form.get("combined_potions") or [])
        out["mesos_start"] = _as_nonneg_int(form.get("mesos_start"))
        out["mesos_end"]   = _as_nonneg_int(form.get("mesos_end"))
        out["shop_before"] = _as_nonneg_int(form.get("shop_before"))
        out["shop_after"]  = _as_nonneg_int(form.get("shop_after"))
        out["item_rows"]   = list(form.get("item_rows") or [])
        out["summary"]     = PotionService.calc_summary(form)
        return out

    @staticmethod
    def deserialize(data: dict) -> PotionFormData:
        """將存檔 dict 還原為表單資料

        未知/缺失欄位會以零值 / 空 list 補齊；`summary` / `saved_at` 不參與還原。
        相容 legacy：忽略舊存檔的 `exp_start` / `exp_end`，缺 `item_rows` 補空 list。
        """
        data = data or {}
        return {
            "duration_minutes": _as_nonneg_int(data.get("duration_minutes")),
            "hp_potions":       list(data.get("hp_potions") or []),
            "mp_potions":       list(data.get("mp_potions") or []),
            "combined_potions": list(data.get("combined_potions") or []),
            "mesos_start": _as_nonneg_int(data.get("mesos_start")),
            "mesos_end":   _as_nonneg_int(data.get("mesos_end")),
            "shop_before": _as_nonneg_int(data.get("shop_before")),
            "shop_after":  _as_nonneg_int(data.get("shop_after")),
            "item_rows":   list(data.get("item_rows") or []),
        }

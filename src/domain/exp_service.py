"""經驗值計算服務 — 升級時間估算（零 Qt 依賴）

由「目前等級＋目前經驗 %、目標等級、練功效率（在 N 分鐘內獲得的經驗）」計算：
- 升級到目標還需多少經驗（exp_remaining）
- 距目前等級下一級還需多少（exp_remaining_in_level）
- 由區間經驗推每小時速率（hourly_rate）
- 預估時間（time_hours / format_duration，時分秒）

經驗表見 src/domain/exp_table.py。純 Python 邏輯，無 Qt 依賴，可被 verify 腳本涵蓋。
"""

from __future__ import annotations

from src.domain.exp_table import EXP_TO_NEXT, MAX_LEVEL


def _clamp_level(level) -> int:
    """把等級夾到 [1, MAX_LEVEL]；非法輸入回 1"""
    try:
        level = int(level)
    except (TypeError, ValueError):
        return 1
    return max(1, min(MAX_LEVEL, level))


def _clamp_pct(pct) -> float:
    """把經驗百分比夾到 [0, 100]（pct 為 0–100 的百分數，非 0–1 比例）；非法輸入回 0"""
    try:
        pct = float(pct)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(100.0, pct))


def exp_remaining_in_level(level, pct) -> int:
    """距目前等級下一級還需的經驗 ＝ round(EXP_TO_NEXT[level] × (1 − pct/100))

    Lv200（封頂）或無下一級資料時回 0。
    """
    level = _clamp_level(level)
    pct = _clamp_pct(pct)
    tnl = EXP_TO_NEXT.get(level)
    if not tnl:
        return 0
    return round(tnl * (1 - pct / 100.0))


def exp_remaining(level, pct, target) -> int:
    """升級到 target 還需的總經驗（從 level 的 pct% 起算）

    target <= level 回 0；否則 ＝ 目前等級剩餘 ＋ Σ(level+1 .. target-1) 的整級經驗。
    level / target 夾在 [1, MAX_LEVEL]，pct 夾在 [0, 100]。

    Args:
        level:  目前等級（1–200）
        pct:    目前等級已獲得的經驗百分比（0–100）
        target: 目標等級（1–200）
    """
    level = _clamp_level(level)
    target = _clamp_level(target)
    if target <= level:
        return 0
    full = sum(EXP_TO_NEXT[lv] for lv in range(level + 1, target))
    return exp_remaining_in_level(level, pct) + full


def hourly_rate(exp_per_interval, minutes) -> float:
    """由「在 N 分鐘內獲得的經驗」推得每小時經驗 ＝ exp × 60 / N；非正輸入回 0"""
    try:
        exp = float(exp_per_interval)
        mins = float(minutes)
    except (TypeError, ValueError):
        return 0.0
    if exp <= 0 or mins <= 0:
        return 0.0
    return exp * 60.0 / mins


def time_hours(total_exp, exp_per_hour) -> float | None:
    """預估時間（小時）＝ total / 每小時經驗；每小時經驗 <= 0 回 None"""
    try:
        total = max(0, int(total_exp))
        eph = float(exp_per_hour)
    except (TypeError, ValueError):
        return None
    if eph <= 0:
        return None
    return total / eph


def format_duration(hours: float | None) -> str:
    """把小時數格式化為 HH:MM:SS（時分秒）；None 回 "—"（零速率/無法估算）"""
    if hours is None:
        return "—"
    hours = max(0.0, float(hours))
    total_seconds = int(round(hours * 3600))
    h, rem = divmod(total_seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"

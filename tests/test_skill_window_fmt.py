"""測 SkillWindow._fmt_seconds — 分鐘顯示邊界邏輯（>600s）"""
import os
import sys

# 確保 import skill_window 不會誤觸 Qt（_fmt_seconds 是純 staticmethod）
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

# 讓 import 在沒實例化 SkillWindow 的情況下也能取得 _fmt_seconds
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def test_fmt_seconds_below_threshold():
    from src.ui.skill_window import SkillWindow
    assert SkillWindow._fmt_seconds(0) == "0"
    assert SkillWindow._fmt_seconds(1) == "1"
    assert SkillWindow._fmt_seconds(60) == "60"
    assert SkillWindow._fmt_seconds(599) == "599"


def test_fmt_seconds_at_boundary():
    """剛好 600 秒仍以秒顯示（嚴格大於才轉分鐘）"""
    from src.ui.skill_window import SkillWindow
    assert SkillWindow._fmt_seconds(600) == "600"


def test_fmt_seconds_above_threshold():
    from src.ui.skill_window import SkillWindow
    assert SkillWindow._fmt_seconds(601) == "11m"  # ceil(601/60) = 11
    assert SkillWindow._fmt_seconds(660) == "11m"  # 剛好 11 分鐘
    assert SkillWindow._fmt_seconds(661) == "12m"
    assert SkillWindow._fmt_seconds(720) == "12m"


def test_fmt_seconds_buff_durations():
    """v4.3.6 三個新 buff 道具的 cooldown 全程顯示"""
    from src.ui.skill_window import SkillWindow
    assert SkillWindow._fmt_seconds(1800) == "30m"  # 30 分鐘 (exp / drop)
    assert SkillWindow._fmt_seconds(3600) == "60m"  # 60 分鐘 (HT)


def test_fmt_seconds_extreme_values():
    """極端值：負數會原樣 str（呼叫端有 remaining<=0 防守，不會傳到這）"""
    from src.ui.skill_window import SkillWindow
    assert SkillWindow._fmt_seconds(-1) == "-1"
    assert SkillWindow._fmt_seconds(86400) == "1440m"  # 24 小時

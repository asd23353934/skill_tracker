"""
頁面套件
提供各頁面元件供側邊欄切換使用
"""

from src.ui.pages.skill_page import SkillPage
from src.ui.pages.skill_page_v2 import SkillPageV2
from src.ui.pages.monster_page import MonsterPage
from src.ui.pages.overlay_page import OverlayPage
from src.ui.pages.potion_cost_page import PotionCostPage
from src.ui.pages.mapleworld_page import MapleWorldPage
__all__ = [
    "SkillPage", "SkillPageV2", "MonsterPage", "OverlayPage",
    "PotionCostPage", "MapleWorldPage",
]

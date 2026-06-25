"""
V2 頁面註冊表 — 頁面導覽的單一來源（single source of truth）

`main_v2.py`（建立 QStackedWidget 內各頁）與 `src/ui_v2/sidebar_v2.py`（左側導覽
按鈕）皆從此處的 `PAGE_REGISTRY` 讀取，確保「key／順序／導覽標題／lucide icon／
tooltip／建構方式」只維護一份。新增或移除頁面只需改這份清單，兩處導覽自動同步。
"""

from collections.abc import Callable
from dataclasses import dataclass

from PySide6.QtWidgets import QWidget

from src.ui_v2.pages.skill_page_v2 import SkillPageV2
from src.ui_v2.pages.monster_page_v2 import MonsterPageV2
from src.ui_v2.pages.overlay_page_v2 import OverlayPageV2
from src.ui_v2.pages.potion_page_v2 import PotionPageV2
from src.ui_v2.pages.exp_calculator_page_v2 import ExpCalculatorPageV2
from src.ui_v2.pages.mapleworld_page_v2 import MapleWorldPageV2
from src.ui_v2.pages.command_page_v2 import CommandPageV2


@dataclass(frozen=True)
class PageSpec:
    """單一頁面的導覽與建構定義

    Attributes:
        key: 唯一識別碼，main_v2 stack 與 sidebar 切換共用
        title: 導覽標題（頁面標題用）
        icon: lucide icon 檔名（對應 src/ui_v2/icons/{icon}.svg）
        tooltip: sidebar 導覽按鈕 tooltip
        factory: 建頁工廠，簽名為 (parent, app_ctx) -> QWidget；
            page class 本身即符合此簽名，需額外副作用者另包一層函數
    """

    key: str
    title: str
    icon: str
    tooltip: str
    factory: Callable[..., QWidget]


def _build_overlay(parent: QWidget, app_ctx) -> QWidget:
    """建立浮動圖片頁，並把 page 反向掛到 app_ctx 供主視窗 overlay 操作存取"""
    page = OverlayPageV2(parent, app_ctx)
    app_ctx.overlay_page = page
    return page


# 頁面註冊表（清單順序即導覽顯示順序）— 新增/移除頁面只改這裡
PAGE_REGISTRY: list[PageSpec] = [
    PageSpec("skill",      "技能總覽", "swords",     "技能倒數",   SkillPageV2),
    PageSpec("monster",    "怪物總覽", "skull",      "怪物重生",   MonsterPageV2),
    PageSpec("overlay",    "浮動圖片", "image",      "浮動圖片",   _build_overlay),
    PageSpec("potion",     "收支分析", "coins",      "練功收支",   PotionPageV2),
    PageSpec("exp",        "經驗計算", "calculator", "經驗計算器", ExpCalculatorPageV2),
    PageSpec("mapleworld", "資源中心", "globe",      "MapleWorld", MapleWorldPageV2),
    PageSpec("command",    "快速指令", "keyboard",   "指令",       CommandPageV2),
]

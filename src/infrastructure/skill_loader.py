"""
技能資料載入模組
提供純 Python 的技能資料載入與查詢功能，不依賴 PySide6 或 PIL
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.infrastructure.config_manager import ConfigManager


class SkillLoader:
    """技能資料載入器 — 純 Python 版本，不含圖片快取"""

    def __init__(self, config_manager: ConfigManager) -> None:
        """初始化技能資料載入器

        Args:
            config_manager: 配置管理器實例
        """
        self.config_manager = config_manager
        self.skills: dict[str, dict] = {}
        self.skill_categories: dict[str, dict[str, list[str]]] = {}
        self._load_skills()

    def _load_skills(self) -> None:
        """載入所有技能和道具"""
        # 載入技能
        for skill_data in self.config_manager.initial_skills:
            skill_id = skill_data["id"]
            category = skill_data.get("category", "player")
            subcategory = skill_data.get("subcategory", "未分類")

            self.skills[skill_id] = skill_data.copy()

            if category not in self.skill_categories:
                self.skill_categories[category] = {}
            if subcategory not in self.skill_categories[category]:
                self.skill_categories[category][subcategory] = []
            self.skill_categories[category][subcategory].append(skill_id)

        # 載入道具
        for item_data in self.config_manager.initial_items:
            item_id = item_data["id"]
            category = item_data.get("category", "item")
            subcategory = item_data.get("subcategory", "道具")

            self.skills[item_id] = item_data.copy()

            if category not in self.skill_categories:
                self.skill_categories[category] = {}
            if subcategory not in self.skill_categories[category]:
                self.skill_categories[category][subcategory] = []
            self.skill_categories[category][subcategory].append(item_id)

    # --------------------------------------------------
    # 查詢 API
    # --------------------------------------------------

    def get_skill(self, skill_id: str) -> dict | None:
        """取得技能資料

        Args:
            skill_id: 技能 ID

        Returns:
            技能資料字典或 None
        """
        return self.skills.get(skill_id)

    def get_all_skills(self) -> dict[str, dict]:
        """取得所有技能字典"""
        return self.skills

    def get_categories(self, category_type: str = None) -> dict:
        """取得技能分類

        Args:
            category_type: 'player' / 'boss' / 'item'，None 則回傳全部

        Returns:
            分類字典
        """
        if category_type:
            return self.skill_categories.get(category_type, {})
        return self.skill_categories

    def update_hotkey(self, skill_id: str, hotkey: str) -> bool:
        """更新技能快捷鍵（僅更新記憶體內狀態，不寫入靜態區）

        持久化由呼叫端透過 auto_save_current_profile() 負責。

        Args:
            skill_id: 技能 ID
            hotkey:   新快捷鍵

        Returns:
            成功回傳 True，失敗回傳 False
        """
        if skill_id not in self.skills:
            return False
        self.skills[skill_id]["hotkey"] = hotkey
        return True

    def clear_all_hotkeys(self) -> None:
        """清空所有快捷鍵"""
        for skill_id in self.skills:
            self.update_hotkey(skill_id, "")

    def get_skill_by_hotkey(self, hotkey: str) -> str | None:
        """根據快捷鍵查找技能 ID

        Args:
            hotkey: 快捷鍵字串

        Returns:
            技能 ID 或 None
        """
        for skill_id, skill in self.skills.items():
            if skill.get("hotkey", "").lower() == hotkey.lower():
                return skill_id
        return None

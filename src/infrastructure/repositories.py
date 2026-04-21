"""
資料存取層模組
提供 Repository 類別，包裝 ConfigManager 提供型別化的資料存取介面。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.domain.models import SkillMetadata

if TYPE_CHECKING:
    from src.infrastructure.config_manager import ConfigManager


class SkillRepository:
    """唯讀技能元資料查詢，合併 skills 和 items"""

    def __init__(self, config_manager: ConfigManager) -> None:
        self._cm = config_manager
        self._cache: dict[str, SkillMetadata] = {}
        self._build_cache()

    def _build_cache(self) -> None:
        """從 ConfigManager 的 initial_skills 和 initial_items 建立快取"""
        for entry in self._cm.initial_skills + self._cm.initial_items:
            skill = SkillMetadata(
                id=entry["id"],
                name=entry["name"],
                icon=entry["icon"],
                cooldown=entry["cooldown"],
                category=entry["category"],
                subcategory=entry.get("subcategory", ""),
            )
            self._cache[skill.id] = skill

    def get_all(self) -> dict[str, SkillMetadata]:
        """取得所有技能與道具元資料"""
        return dict(self._cache)

    def get(self, skill_id: str) -> SkillMetadata | None:
        """取得指定 id 的技能元資料"""
        return self._cache.get(skill_id)

    def get_by_category(self, category: str) -> list[SkillMetadata]:
        """取得指定類別的技能列表"""
        return [s for s in self._cache.values() if s.category == category]


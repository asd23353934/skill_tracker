"""
技能圖片快取模組
處理技能圖片的載入與多尺寸 QPixmap 快取
PySide6 版本：圖片使用 QPixmap 快取
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PIL import Image
from PySide6.QtGui import QImage, QPixmap

from src.infrastructure.helpers import resource_path

if TYPE_CHECKING:
    from src.infrastructure.skill_loader import SkillLoader


def _pil_to_qpixmap(pil_img: Image.Image) -> QPixmap:
    """PIL RGBA Image → QPixmap（一次轉換）

    Args:
        pil_img: PIL Image（自動轉 RGBA）

    Returns:
        QPixmap 物件
    """
    pil_img = pil_img.convert("RGBA")
    data = pil_img.tobytes("raw", "RGBA")
    qimg = QImage(data, pil_img.width, pil_img.height,
                  QImage.Format.Format_RGBA8888)
    return QPixmap.fromImage(qimg)


class SkillPixmapCache:
    """技能圖片快取 — 包裝 SkillLoader 提供 QPixmap 快取"""

    def __init__(self, skill_loader: SkillLoader) -> None:
        """初始化圖片快取

        Args:
            skill_loader: 技能資料載入器實例
        """
        self.skill_loader = skill_loader
        self.skill_image_paths: dict[str, str] = {}

        # QPixmap 快取（多種尺寸）
        self.qpixmaps: dict[str, QPixmap | None] = {}        # 50×50 主 UI
        self.qpixmaps_small: dict[str, QPixmap | None] = {}   # 28×28 小圖示
        self.qpixmaps_medium: dict[str, QPixmap | None] = {}  # 64×64 倒數視窗
        self.qpixmaps_card: dict[str, QPixmap | None] = {}    # 36×36 技能卡片

        self._load_all_images()

    def _load_all_images(self) -> None:
        """從 SkillLoader 的技能列表載入所有圖片"""
        for skill_id, skill_data in self.skill_loader.get_all_skills().items():
            self._load_skill_image(skill_id, skill_data["icon"])

    def _load_skill_image(self, skill_id: str, icon_filename: str) -> None:
        """載入技能圖片並產生多尺寸 QPixmap 快取

        Args:
            skill_id:      技能 ID
            icon_filename: 圖示檔名
        """
        icon_path = resource_path(f"images/{icon_filename}")
        self.skill_image_paths[skill_id] = icon_path
        try:
            img = Image.open(icon_path).convert("RGBA")

            self.qpixmaps[skill_id] = _pil_to_qpixmap(
                img.resize((50, 50), Image.Resampling.LANCZOS))
            self.qpixmaps_small[skill_id] = _pil_to_qpixmap(
                img.resize((28, 28), Image.Resampling.LANCZOS))
            self.qpixmaps_medium[skill_id] = _pil_to_qpixmap(
                img.resize((64, 64), Image.Resampling.LANCZOS))
            self.qpixmaps_card[skill_id] = _pil_to_qpixmap(
                img.resize((36, 36), Image.Resampling.LANCZOS))
        except Exception:
            self.qpixmaps[skill_id] = None
            self.qpixmaps_small[skill_id] = None
            self.qpixmaps_medium[skill_id] = None
            self.qpixmaps_card[skill_id] = None

    # --------------------------------------------------
    # SkillLoader 委派 API（向後相容）
    # 讓現有 self.app.skill_manager.get_skill() 等呼叫繼續運作
    # --------------------------------------------------

    @property
    def config_manager(self):
        """委派至 SkillLoader.config_manager"""
        return self.skill_loader.config_manager

    @property
    def skills(self) -> dict[str, dict]:
        """委派至 SkillLoader.skills"""
        return self.skill_loader.skills

    @property
    def skill_categories(self) -> dict:
        """委派至 SkillLoader.skill_categories"""
        return self.skill_loader.skill_categories

    def get_skill(self, skill_id: str) -> dict | None:
        """委派至 SkillLoader.get_skill"""
        return self.skill_loader.get_skill(skill_id)

    def get_all_skills(self) -> dict[str, dict]:
        """委派至 SkillLoader.get_all_skills"""
        return self.skill_loader.get_all_skills()

    def get_categories(self, category_type: str = None) -> dict:
        """委派至 SkillLoader.get_categories"""
        return self.skill_loader.get_categories(category_type)

    def update_hotkey(self, skill_id: str, hotkey: str) -> bool:
        """委派至 SkillLoader.update_hotkey"""
        return self.skill_loader.update_hotkey(skill_id, hotkey)

    def clear_all_hotkeys(self) -> None:
        """委派至 SkillLoader.clear_all_hotkeys"""
        self.skill_loader.clear_all_hotkeys()

    def get_skill_by_hotkey(self, hotkey: str) -> str | None:
        """委派至 SkillLoader.get_skill_by_hotkey"""
        return self.skill_loader.get_skill_by_hotkey(hotkey)

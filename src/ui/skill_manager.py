"""
技能管理模組
處理技能的載入、分類、圖片載入等核心邏輯
PySide6 版本：圖片改用 QPixmap 快取
"""

from PIL import Image
from PySide6.QtGui import QImage, QPixmap
from src.ui.helpers import resource_path


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


class SkillManager:
    """技能管理器 — PySide6 版本"""

    def __init__(self, config_manager):
        """初始化技能管理器

        Args:
            config_manager: 配置管理器實例
        """
        self.config_manager = config_manager
        self.skills = {}
        self.skill_categories = {}
        self.skill_image_paths = {}

        # QPixmap 快取（多種尺寸）
        self.qpixmaps        = {}   # 50×50 主 UI
        self.qpixmaps_small  = {}   # 28×28 小圖示
        self.qpixmaps_medium = {}   # 64×64 倒數視窗
        self.qpixmaps_card   = {}   # 36×36 技能卡片

        self._load_skills()

    def _load_skills(self):
        """載入所有技能和道具"""
        # 載入技能
        for skill_data in self.config_manager.initial_skills:
            skill_id    = skill_data["id"]
            category    = skill_data.get("category", "player")
            subcategory = skill_data.get("subcategory", "未分類")

            self.skills[skill_id] = skill_data.copy()

            if category not in self.skill_categories:
                self.skill_categories[category] = {}
            if subcategory not in self.skill_categories[category]:
                self.skill_categories[category][subcategory] = []
            self.skill_categories[category][subcategory].append(skill_id)

            self._load_skill_image(skill_id, skill_data["icon"])

        # 載入道具
        for item_data in self.config_manager.initial_items:
            item_id     = item_data["id"]
            category    = item_data.get("category", "item")
            subcategory = item_data.get("subcategory", "道具")

            self.skills[item_id] = item_data.copy()

            if category not in self.skill_categories:
                self.skill_categories[category] = {}
            if subcategory not in self.skill_categories[category]:
                self.skill_categories[category][subcategory] = []
            self.skill_categories[category][subcategory].append(item_id)

            self._load_skill_image(item_id, item_data["icon"])

    def _load_skill_image(self, skill_id: str, icon_filename: str):
        """載入技能圖片並產生多尺寸 QPixmap 快取

        Args:
            skill_id:      技能 ID
            icon_filename: 圖示檔名
        """
        icon_path = resource_path(f"images/{icon_filename}")
        self.skill_image_paths[skill_id] = icon_path
        try:
            img = Image.open(icon_path).convert("RGBA")

            self.qpixmaps[skill_id]        = _pil_to_qpixmap(
                img.resize((50, 50), Image.Resampling.LANCZOS))
            self.qpixmaps_small[skill_id]  = _pil_to_qpixmap(
                img.resize((28, 28), Image.Resampling.LANCZOS))
            self.qpixmaps_medium[skill_id] = _pil_to_qpixmap(
                img.resize((64, 64), Image.Resampling.LANCZOS))
            self.qpixmaps_card[skill_id]   = _pil_to_qpixmap(
                img.resize((36, 36), Image.Resampling.LANCZOS))
        except Exception:
            self.qpixmaps[skill_id]        = None
            self.qpixmaps_small[skill_id]  = None
            self.qpixmaps_medium[skill_id] = None
            self.qpixmaps_card[skill_id]   = None

    # --------------------------------------------------
    # 查詢 API（邏輯與原版完全相同）
    # --------------------------------------------------

    def get_skill(self, skill_id: str):
        """取得技能資料

        Args:
            skill_id: 技能 ID

        Returns:
            技能資料字典或 None
        """
        return self.skills.get(skill_id)

    def get_all_skills(self) -> dict:
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
        """更新技能快捷鍵

        Args:
            skill_id: 技能 ID
            hotkey:   新快捷鍵

        Returns:
            成功回傳 True，失敗回傳 False
        """
        if skill_id not in self.skills:
            return False
        self.skills[skill_id]["hotkey"] = hotkey
        for i, skill_data in enumerate(self.config_manager.config["skills"]):
            if skill_data["id"] == skill_id:
                self.config_manager.config["skills"][i]["hotkey"] = hotkey
                break
        return True

    def clear_all_hotkeys(self):
        """清空所有快捷鍵"""
        for skill_id in self.skills:
            self.update_hotkey(skill_id, "")

    def get_skill_by_hotkey(self, hotkey: str):
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

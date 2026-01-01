"""
技能管理模組
處理技能的載入、分類、圖片載入等核心邏輯
"""

from PIL import Image, ImageTk
from src.utils.helpers import resource_path


class SkillManager:
    """技能管理器"""
    
    def __init__(self, config_manager):
        """初始化技能管理器
        
        Args:
            config_manager: 配置管理器實例
        """
        self.config_manager = config_manager
        self.skills = {}
        self.skill_categories = {}
        self.skill_images = {}
        self.skill_images_small = {}
        
        self._load_skills()
    
    def _load_skills(self):
        """載入所有技能和道具"""
        # 載入技能（使用原始值）
        for skill_data in self.config_manager.initial_skills:
            skill_id = skill_data['id']
            category = skill_data.get('category', 'player')
            subcategory = skill_data.get('subcategory', '未分類')
            
            # 儲存技能資料（創建副本，避免修改原始數據）
            self.skills[skill_id] = skill_data.copy()
            
            # 分類整理
            if category not in self.skill_categories:
                self.skill_categories[category] = {}
            if subcategory not in self.skill_categories[category]:
                self.skill_categories[category][subcategory] = []
            self.skill_categories[category][subcategory].append(skill_id)
            
            # 載入圖片
            self._load_skill_image(skill_id, skill_data['icon'])
        
        # 載入道具（使用原始值）
        for item_data in self.config_manager.initial_items:
            item_id = item_data['id']
            category = item_data.get('category', 'item')
            subcategory = item_data.get('subcategory', '道具')
            
            # 儲存道具資料（創建副本，避免修改原始數據）
            self.skills[item_id] = item_data.copy()
            
            # 分類整理
            if category not in self.skill_categories:
                self.skill_categories[category] = {}
            if subcategory not in self.skill_categories[category]:
                self.skill_categories[category][subcategory] = []
            self.skill_categories[category][subcategory].append(item_id)
            
            # 載入圖片
            self._load_skill_image(item_id, item_data['icon'])
    
    def _load_skill_image(self, skill_id, icon_filename):
        """載入技能圖片
        
        Args:
            skill_id: 技能 ID
            icon_filename: 圖片檔名
        """
        icon_path = resource_path(f"images/{icon_filename}")
        try:
            img = Image.open(icon_path)
            img_large = img.resize((50, 50), Image.Resampling.LANCZOS)
            img_small = img.resize((28, 28), Image.Resampling.LANCZOS)
            self.skill_images[skill_id] = ImageTk.PhotoImage(img_large)
            self.skill_images_small[skill_id] = ImageTk.PhotoImage(img_small)
        except:
            self.skill_images[skill_id] = None
            self.skill_images_small[skill_id] = None
    
    def get_skill(self, skill_id):
        """獲取技能資料
        
        Args:
            skill_id: 技能 ID
        
        Returns:
            技能資料字典或 None
        """
        return self.skills.get(skill_id)
    
    def get_all_skills(self):
        """獲取所有技能"""
        return self.skills
    
    def get_categories(self, category_type=None):
        """獲取技能分類
        
        Args:
            category_type: 分類類型 ('player' 或 'boss')，None 則返回所有
        
        Returns:
            分類字典
        """
        if category_type:
            return self.skill_categories.get(category_type, {})
        return self.skill_categories
    
    def update_hotkey(self, skill_id, hotkey):
        """更新技能快捷鍵
        
        Args:
            skill_id: 技能 ID
            hotkey: 新快捷鍵
        
        Returns:
            成功返回 True，失敗返回 False
        """
        if skill_id not in self.skills:
            return False
        
        # 更新內存中的技能資料
        self.skills[skill_id]['hotkey'] = hotkey
        
        # 更新配置文件中的技能資料
        for i, skill_data in enumerate(self.config_manager.config['skills']):
            if skill_data['id'] == skill_id:
                self.config_manager.config['skills'][i]['hotkey'] = hotkey
                break
        
        return True
    
    def clear_all_hotkeys(self):
        """清空所有快捷鍵"""
        for skill_id in self.skills:
            self.update_hotkey(skill_id, '')
    
    def get_skill_by_hotkey(self, hotkey):
        """根據快捷鍵查找技能
        
        Args:
            hotkey: 快捷鍵
        
        Returns:
            技能 ID 或 None
        """
        for skill_id, skill in self.skills.items():
            if skill.get('hotkey', '').lower() == hotkey.lower():
                return skill_id
        return None

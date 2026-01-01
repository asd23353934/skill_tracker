"""
配置管理模組
處理配置文件的讀寫、配置檔案的管理
"""

import json
import os


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_path):
        self.config_path = config_path
        self.config = self._load_config()
        
        # 分離出 skills 和 items（只讀，不會被保存）
        self.initial_skills = self.config.get('skills', [])
        self.initial_items = self.config.get('items', [])
        
        self.profiles_dir = os.path.join(os.path.dirname(config_path), 'profiles')
        self._ensure_profiles_dir()
    
    def _load_config(self):
        """載入配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"無法載入 config.json: {e}")
            raise
    
    def _ensure_profiles_dir(self):
        """確保配置檔案目錄存在"""
        if not os.path.exists(self.profiles_dir):
            os.makedirs(self.profiles_dir)
    
    def save(self):
        """儲存配置文件（只保存 settings，不保存 skills 和 items）"""
        try:
            # 創建要保存的配置（不包含 skills 和 items 的當前狀態）
            save_config = {
                'skills': self.initial_skills,  # 使用原始值
                'items': self.initial_items,    # 使用原始值
                'settings': self.config.get('settings', {})
            }
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(save_config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存配置失敗: {e}")
            return False
    
    def get(self, key, default=None):
        """獲取配置值"""
        return self.config.get(key, default)
    
    def get_settings(self, key, default=None):
        """獲取設定值"""
        return self.config.get('settings', {}).get(key, default)
    
    def set_settings(self, key, value):
        """設定設定值"""
        if 'settings' not in self.config:
            self.config['settings'] = {}
        self.config['settings'][key] = value
    
    # ==================== 配置檔案管理 ====================
    
    def list_profiles(self):
        """列出所有配置檔案"""
        if not os.path.exists(self.profiles_dir):
            return []
        profiles = []
        for filename in os.listdir(self.profiles_dir):
            if filename.endswith('.json'):
                profiles.append(filename[:-5])
        return sorted(profiles)
    
    def save_profile(self, profile_name, skill_settings):
        """儲存配置檔案
        
        Args:
            profile_name: 配置名稱
            skill_settings: 技能設定字典
        
        Returns:
            成功返回 True，失敗返回 False
        """
        profile_path = os.path.join(self.profiles_dir, f"{profile_name}.json")
        try:
            with open(profile_path, 'w', encoding='utf-8') as f:
                json.dump(skill_settings, f, ensure_ascii=False, indent=2)
            return True
        except:
            return False
    
    def load_profile(self, profile_name):
        """載入配置檔案
        
        Args:
            profile_name: 配置名稱
        
        Returns:
            成功返回設定字典，失敗返回 None
        """
        profile_path = os.path.join(self.profiles_dir, f"{profile_name}.json")
        try:
            with open(profile_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return None
    
    def delete_profile(self, profile_name):
        """刪除配置檔案
        
        Args:
            profile_name: 配置名稱
        
        Returns:
            成功返回 True，失敗返回 False
        """
        profile_path = os.path.join(self.profiles_dir, f"{profile_name}.json")
        try:
            os.remove(profile_path)
            return True
        except:
            return False
    
    def rename_profile(self, old_name, new_name):
        """重命名配置檔案
        
        Args:
            old_name: 舊名稱
            new_name: 新名稱
        
        Returns:
            成功返回 True，失敗返回 False
        """
        old_path = os.path.join(self.profiles_dir, f"{old_name}.json")
        new_path = os.path.join(self.profiles_dir, f"{new_name}.json")
        try:
            os.rename(old_path, new_path)
            return True
        except:
            return False
    
    def get_current_profile(self):
        """獲取當前配置名稱"""
        return self.get_settings('current_profile', '預設配置')
    
    def set_current_profile(self, profile_name):
        """設定當前配置名稱"""
        self.set_settings('current_profile', profile_name)
        self.save()
    
    def ensure_default_profile(self):
        """確保預設配置存在，並檢查當前配置是否有效"""
        default_name = '預設配置'
        
        # 1. 確保預設配置存在
        if default_name not in self.list_profiles():
            # 創建預設配置（所有技能都是初始狀態）
            default_settings = {
                'hotkeys': {},
                'send': {},
                'receive': {},
                'permanent': {},
                'cooldown_overrides': {}  # 使用 config.json 中的原始秒數
            }
            self.save_profile(default_name, default_settings)
            print(f"✅ 已創建預設配置")
        
        # 2. 檢查當前配置是否有效
        current = self.get_current_profile()
        
        # 如果當前配置不存在，切換到預設配置
        if current not in self.list_profiles():
            print(f"⚠️ 當前配置 '{current}' 不存在，自動切換到 '{default_name}'")
            self.set_current_profile(default_name)
        
        # 3. 如果沒有設定當前配置，設為預設配置
        if not current:
            print(f"ℹ️ 未設定當前配置，使用 '{default_name}'")
            self.set_current_profile(default_name)


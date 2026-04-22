"""
配置管理模組
處理配置文件的讀寫、配置檔案的管理
"""

import json
import logging
import os

logger = logging.getLogger(__name__)

# Windows 保留檔名（含副檔名也視為保留；含 COM0 / LPT0）
_RESERVED_WINDOWS_NAMES = frozenset({
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{i}" for i in range(10)),
    *(f"LPT{i}" for i in range(10)),
})


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_path):
        self.config_path = config_path
        self.config = self._load_config()
        
        # 分離出 skills 和 items（只讀，不會被保存）
        self.initial_skills = self.config.get('skills', [])
        self.initial_items = self.config.get('items', [])

        # 記錄怪物原始重生時間（供重置用）
        self.initial_monsters = {
            m["id"]: m.get("respawn_time", 0)
            for m in self.config.get("monsters", [])
        }
        
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
        """儲存配置文件（保存 settings 和 monsters，skills/items 使用原始值）"""
        try:
            save_config = {
                'skills': self.initial_skills,  # 使用原始值
                'items': self.initial_items,    # 使用原始值
                'settings': self.config.get('settings', {}),
            }

            # 保存怪物資料（含快捷鍵等可變動欄位）
            if 'monsters' in self.config:
                save_config['monsters'] = self.config['monsters']

            # 保存覆蓋圖片資料（位置、尺寸、透明度等）
            if 'overlays' in self.config:
                save_config['overlays'] = self.config['overlays']

            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(save_config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存配置失敗: {e}")
            return False
    
    def get_original_respawn_time(self, monster_id):
        """取得怪物原始重生時間"""
        return self.initial_monsters.get(monster_id)

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
    
    # ==================== 內部工具 ====================

    @staticmethod
    def _validate_filename(name: str) -> bool:
        """驗證存檔名稱安全性，防止 Path Traversal 攻擊

        Args:
            name: 待驗證的名稱（不含副檔名）

        Returns:
            合法回傳 True，否則回傳 False
        """
        if not name:
            return False
        if any(c in name for c in ("/", "\\", "..")):
            return False
        if name[-1] in (" ", "."):
            return False
        stem = name.split(".", 1)[0].upper()
        if stem in _RESERVED_WINDOWS_NAMES:
            return False
        return True

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
            profile_name:   配置名稱
            skill_settings: 技能設定字典

        Returns:
            成功返回 True，失敗返回 False
        """
        if not self._validate_filename(profile_name):
            logger.warning("save_profile: 非法配置名稱 %r", profile_name)
            return False
        profile_path = os.path.join(self.profiles_dir, f"{profile_name}.json")
        try:
            with open(profile_path, 'w', encoding='utf-8') as f:
                json.dump(skill_settings, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            logger.exception("save_profile: 儲存失敗 name=%r", profile_name)
            return False

    def load_profile(self, profile_name):
        """載入配置檔案，並補足缺少的結構欄位

        Args:
            profile_name: 配置名稱

        Returns:
            成功返回設定字典，失敗返回 None
        """
        if not self._validate_filename(profile_name):
            logger.warning("load_profile: 非法配置名稱 %r", profile_name)
            return None
        profile_path = os.path.join(self.profiles_dir, f"{profile_name}.json")
        try:
            with open(profile_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # 結構驗證：確保必要欄位存在（填入空字典預設值）
            for key in ("hotkeys", "permanent", "loop", "alert_enabled", "cooldown_overrides"):
                if key not in data:
                    logger.debug("load_profile: 補足缺少欄位 %r in %r", key, profile_name)
                    data[key] = {}
            return data
        except Exception:
            logger.exception("load_profile: 載入失敗 name=%r", profile_name)
            return None

    def delete_profile(self, profile_name):
        """刪除配置檔案

        Args:
            profile_name: 配置名稱

        Returns:
            成功返回 True，失敗返回 False
        """
        if not self._validate_filename(profile_name):
            logger.warning("delete_profile: 非法配置名稱 %r", profile_name)
            return False
        profile_path = os.path.join(self.profiles_dir, f"{profile_name}.json")
        try:
            os.remove(profile_path)
            return True
        except Exception:
            logger.exception("delete_profile: 刪除失敗 name=%r", profile_name)
            return False

    def rename_profile(self, old_name, new_name):
        """重命名配置檔案

        Args:
            old_name: 舊名稱
            new_name: 新名稱

        Returns:
            成功返回 True，失敗返回 False
        """
        if not self._validate_filename(old_name) or not self._validate_filename(new_name):
            logger.warning("rename_profile: 非法名稱 %r → %r", old_name, new_name)
            return False
        old_path = os.path.join(self.profiles_dir, f"{old_name}.json")
        new_path = os.path.join(self.profiles_dir, f"{new_name}.json")
        try:
            os.rename(old_path, new_path)
            return True
        except Exception:
            logger.exception("rename_profile: 重命名失敗 %r → %r", old_name, new_name)
            return False
    
    def get_current_profile(self):
        """獲取當前配置名稱"""
        return self.get_settings('current_profile', '預設配置')
    
    def set_current_profile(self, profile_name):
        """設定當前配置名稱"""
        self.set_settings('current_profile', profile_name)
        self.save()
    
    def ensure_default_profile(self):
        """確保預設配置存在"""
        default_name = '預設配置'
        if default_name not in self.list_profiles():
            # 創建預設配置（所有技能都是初始狀態）
            default_settings = {
                'hotkeys': {},
                'permanent': {},
                'loop': {},
                'alert_enabled': {},
                'cooldown_overrides': {},
                'alert_seconds_overrides': {},
                'sound_overrides': {},
                'alert_sound_overrides': {},
            }
            self.save_profile(default_name, default_settings)

        # 如果沒有當前配置，設定為預設配置
        if not self.get_current_profile():
            self.set_current_profile(default_name)

    # ==================== 練功水錢存檔管理 ====================

    def _potion_saves_dir(self) -> str:
        """建立並回傳練功水錢存檔目錄的絕對路徑"""
        path = os.path.join(os.path.dirname(self.config_path), "potion_saves")
        if not os.path.exists(path):
            os.makedirs(path)
        return path

    def list_potion_saves(self) -> list:
        """列出所有練功水錢存檔名稱，按修改時間倒序排列

        Returns:
            名稱列表（不含 .json，最新在前）
        """
        saves_dir = self._potion_saves_dir()
        entries = []
        for filename in os.listdir(saves_dir):
            if filename.endswith(".json"):
                full_path = os.path.join(saves_dir, filename)
                mtime = os.path.getmtime(full_path)
                entries.append((filename[:-5], mtime))
        entries.sort(key=lambda x: x[1], reverse=True)
        return [name for name, _ in entries]

    def save_potion_record(self, name: str, data: dict) -> bool:
        """儲存練功水錢紀錄

        Args:
            name: 存檔名稱（不含 .json）
            data: 完整表單資料字典

        Returns:
            成功返回 True，失敗返回 False
        """
        if not self._validate_filename(name):
            logger.warning("save_potion_record: 非法名稱 %r", name)
            return False
        path = os.path.join(self._potion_saves_dir(), f"{name}.json")
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            logger.exception("save_potion_record: 儲存失敗 name=%r", name)
            return False

    def load_potion_record(self, name: str):
        """載入練功水錢紀錄

        Args:
            name: 存檔名稱

        Returns:
            資料字典，載入失敗返回 None
        """
        if not self._validate_filename(name):
            logger.warning("load_potion_record: 非法名稱 %r", name)
            return None
        path = os.path.join(self._potion_saves_dir(), f"{name}.json")
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            logger.exception("load_potion_record: 載入失敗 name=%r", name)
            return None

    def delete_potion_record(self, name: str) -> bool:
        """刪除練功水錢紀錄

        Args:
            name: 存檔名稱

        Returns:
            成功返回 True，失敗返回 False
        """
        if not self._validate_filename(name):
            logger.warning("delete_potion_record: 非法名稱 %r", name)
            return False
        path = os.path.join(self._potion_saves_dir(), f"{name}.json")
        try:
            os.remove(path)
            return True
        except Exception:
            logger.exception("delete_potion_record: 刪除失敗 name=%r", name)
            return False

    # ==================== 練功水錢自動保存 ====================

    def _potion_autosave_path(self) -> str:
        """練功水錢自動保存檔案路徑（與 config.json 同層）"""
        return os.path.join(os.path.dirname(self.config_path), "potion_autosave.json")

    def save_potion_autosave(self, data: dict) -> bool:
        """寫入練功水錢自動保存"""
        try:
            with open(self._potion_autosave_path(), "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            logger.exception("save_potion_autosave: 寫入失敗")
            return False

    def load_potion_autosave(self):
        """讀取練功水錢自動保存，無檔或錯誤回傳 None"""
        path = self._potion_autosave_path()
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            logger.exception("load_potion_autosave: 讀取失敗")
            return None

    def delete_potion_autosave(self) -> bool:
        """刪除練功水錢自動保存"""
        path = self._potion_autosave_path()
        if not os.path.exists(path):
            return True
        try:
            os.remove(path)
            return True
        except Exception:
            logger.exception("delete_potion_autosave: 刪除失敗")
            return False

    def rename_potion_record(self, old_name: str, new_name: str) -> bool:
        """重命名練功水錢紀錄

        Args:
            old_name: 舊名稱
            new_name: 新名稱

        Returns:
            成功返回 True，失敗返回 False
        """
        if not self._validate_filename(old_name) or not self._validate_filename(new_name):
            logger.warning("rename_potion_record: 非法名稱 %r → %r", old_name, new_name)
            return False
        saves_dir = self._potion_saves_dir()
        old_path = os.path.join(saves_dir, f"{old_name}.json")
        new_path = os.path.join(saves_dir, f"{new_name}.json")
        try:
            os.rename(old_path, new_path)
            return True
        except Exception:
            logger.exception("rename_potion_record: 重命名失敗 %r → %r", old_name, new_name)
            return False


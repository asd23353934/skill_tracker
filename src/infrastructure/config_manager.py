"""
配置管理模組
處理配置文件的讀寫、配置檔案的管理
"""

import json
import logging
import os

from src.infrastructure.helpers import atomic_write_json

logger = logging.getLogger(__name__)


# Windows 保留檔名（含副檔名也視為保留；含 COM0 / LPT0）
_RESERVED_WINDOWS_NAMES = frozenset({
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{i}" for i in range(10)),
    *(f"LPT{i}" for i in range(10)),
})

# Windows 不允許作為檔名一部分的字元（除了 / \ 已在 path traversal 檢查擋掉）
_BAD_FILENAME_CHARS = frozenset('<>:"|?*')

# 檔名長度上限（NTFS 單一 component 限 255；保留 .json 副檔名 + 安全 buffer）
_MAX_FILENAME_LEN = 200

# 指令頁「最近使用的玩家名稱」清單上限
_MAX_RECENT_COMMAND_NAMES = 20


def promote_recent(names: list[str], name: str,
                   cap: int = _MAX_RECENT_COMMAND_NAMES) -> list[str]:
    """把 name 提到清單最前、去重、截斷到 cap（純函式，供指令頁名稱記憶用）

    Args:
        names: 既有清單（最近在前）
        name: 要加入 / 提前的名稱（呼叫端應已去前後空白）
        cap: 清單長度上限

    Returns:
        新清單（最近在前、無重複、長度 ≤ cap）；name 為空字串時不新增、僅回傳去重後的既有清單
    """
    result = [name] if name else []
    for n in names:
        if n and n != name and n not in result:
            result.append(n)
    return result[:cap]


class ConfigManager:
    """配置管理器"""
    
    # ── user 可變區預設值（_load_or_migrate_user_config + strip script 共用） ──
    DEFAULT_USER_SETTINGS = {
        "player_name":          "玩家1",
        "skill_start_x":        200,
        "skill_start_y":        200,
        "enable_sound":         True,                  # 舊版相容（= 完成或提前任一開啟）
        "enable_end_sound":     True,                  # 完成提示音開關
        "enable_alert_sound":   True,                  # 提前提示音開關
        "sound_volume":         100,
        "window_size":          96,                    # 大
        "alert_before_seconds": 10,
        "hint_position_x":      0,
        "hint_position_y":      0,
        "global_sound":         "alert_urgent.wav",    # 緊急提示
        "global_alert_sound":   "alert_urgent.wav",
        "hotkey_app_filter_enabled": False,            # 快捷鍵僅在指定視窗前景時觸發
        "hotkey_app_target_exe":     "",               # 目標程式 exe（小寫 basename）
        "hotkey_app_target_label":   "",               # 目標視窗顯示標題
        "command_hotkeys_enabled":  True,              # 指令頁快捷鍵觸發總開關
        "current_profile":      "預設配置",
    }

    def __init__(self, config_path):
        self.config_path = config_path
        self.user_config_path = os.path.join(
            os.path.dirname(config_path), 'config_user.json'
        )
        self.config = self._load_config()
        # 載入 user 可變區（settings / monsters / overlays），覆蓋 in-memory config
        self._load_or_migrate_user_config()

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

    def _load_or_migrate_user_config(self):
        """user 可變區（settings / monsters / overlays）分檔載入。

        三種情境：
        1. config_user.json 已存在 → 讀入後覆蓋 self.config 對應欄位
        2. config_user.json 不存在 + config.json 已被 strip（含 _user_data_stripped）
           → 建空白 user 檔（settings 用 DEFAULT_USER_SETTINGS）
        3. config_user.json 不存在 + config.json 仍含 user data（migration from
           pre-split 版本） → 從現有 self.config 抽出 settings/monsters/overlays
           寫成 user 檔
        """
        if os.path.exists(self.user_config_path):
            try:
                with open(self.user_config_path, 'r', encoding='utf-8') as f:
                    user = json.load(f)
                if isinstance(user.get('settings'), dict):
                    self.config['settings'] = user['settings']
                if isinstance(user.get('monsters'), list):
                    self.config['monsters'] = user['monsters']
                if isinstance(user.get('overlays'), list):
                    self.config['overlays'] = user['overlays']
                return
            except Exception as e:
                print(f"無法載入 config_user.json: {e}")
                # 故障時退回 fresh 邏輯（下面）

        # 第一次跑：判斷 config.json 來源
        if self.config.get('_user_data_stripped') is True:
            # fresh install：settings 的個人欄位不可信，改用 default；
            # 但 monsters / overlays 是 ship 預設內容（boss 列表 / 預設浮動圖），
            # 直接沿用 config.json 內的值作為新 user 檔初值
            self.config['settings'] = dict(self.DEFAULT_USER_SETTINGS)
            # monsters / overlays 維持 config.json 帶進來的內容
        # else: pre-split 版本升上來，self.config 內 settings/monsters/overlays
        # 即為 user data，直接持有；接著寫成 user 檔保留下來
        self._write_user_config()

    def _write_user_config(self):
        """把 self.config 的 settings/monsters/overlays 寫成 config_user.json。"""
        user = {
            'settings': self.config.get('settings', {}),
            'monsters': self.config.get('monsters', []),
            'overlays': self.config.get('overlays', []),
        }
        try:
            atomic_write_json(self.user_config_path, user)
            return True
        except Exception:
            logger.exception("保存 config_user.json 失敗")
            return False

    def _ensure_profiles_dir(self):
        """確保配置檔案目錄存在"""
        if not os.path.exists(self.profiles_dir):
            os.makedirs(self.profiles_dir)

    def save(self):
        """儲存設定（只寫 config_user.json；config.json 保持磁碟原樣）"""
        return self._write_user_config()
    
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

    def get_recent_command_names(self) -> list[str]:
        """取得舊版共用「最近使用玩家名稱」清單（legacy）

        自 command-name-chips 起，名稱改為 per-command 儲存（見 get_command_names）；
        本方法保留為「整個 command_names map 不存在」時的唯讀 fallback 來源。
        缺鍵時回空清單（向後相容舊 config_user.json）；防禦性過濾非字串元素。
        """
        names = self.get_settings('command_recent_names', [])
        if not isinstance(names, list):
            return []
        return [n for n in names if isinstance(n, str) and n]

    # ── 指令頁 per-command 名稱（settings.command_names: {key: [name, ...]}）──

    def get_command_names(self, key: str) -> list[str]:
        """取得某指令的名稱清單（最近在前）

        升級相容（per-key fallback）：未曾寫入過的 key（不在 command_names map 中）
        以舊版共用 command_recent_names 作為唯讀初始來源；一旦該 key 被寫入（含被刪到空），
        即以 map 內的值為準、不再回填舊清單。fallback 判斷以「key 是否在 map 中」為準，
        而非「map 是否存在」——否則對任一指令的首次刪除會連帶清空其他尚未操作指令的繼承名單。
        非字串元素一律過濾。

        Args:
            key: 指令 key（_Command.key）

        Returns:
            該指令的名稱清單；key 非法回空清單
        """
        if not isinstance(key, str) or not key:
            return []
        m = self.get_settings('command_names')
        if not isinstance(m, dict) or key not in m:
            # 此 key 從未寫入 → 舊共用清單作為該指令的初始來源（read-only）
            return self.get_recent_command_names()
        names = m.get(key)
        if not isinstance(names, list):
            return []
        return [n for n in names if isinstance(n, str) and n]

    def _set_command_names(self, key: str, names: list[str]):
        """寫入某指令的名稱清單到 settings.command_names 並持久化"""
        m = self.get_settings('command_names')
        if not isinstance(m, dict):
            m = {}
        m[key] = names
        self.set_settings('command_names', m)
        self.save()

    def add_command_name(self, key: str, name: str) -> list[str]:
        """為某指令記住一個名稱：去空白、提到最前、去重、截斷上限，持久化

        名稱含「#代碼」原樣保存。名稱為空白或 key 非法則不動作。

        Returns:
            更新後清單（供 UI 直接刷新）
        """
        if not isinstance(key, str) or not key:
            return []
        name = (name or "").strip()
        if not name:
            return self.get_command_names(key)
        new_list = promote_recent(self.get_command_names(key), name)
        self._set_command_names(key, new_list)
        return new_list

    def remove_command_name(self, key: str, name: str) -> list[str]:
        """從某指令的名稱清單移除一個名稱，持久化

        連帶清除該名稱專屬的快捷鍵（避免孤兒綁定佔用按鍵卻永遠觸發不到）。

        Returns:
            更新後清單
        """
        if not isinstance(key, str) or not key:
            return []
        new_list = [n for n in self.get_command_names(key) if n != name]
        self._set_command_names(key, new_list)
        if self.get_command_name_hotkey(key, name):
            self.set_command_name_hotkey(key, name, "")
        return new_list

    def rename_command_name(self, key: str, old: str, new: str) -> list[str]:
        """就地把某指令清單中的 old 改名為 new（去空白），持久化

        new 為空白 → 視為刪除 old；new 與既有重複 → 去重（保留最前出現）；
        old 不在清單時，new 非空則當作新增。old 的專屬快捷鍵會跟著遷移到 new
        （new 本身已有快捷鍵則保留 new 的，old 的直接捨棄，避免覆蓋使用者剛設定的）。

        Returns:
            更新後清單
        """
        if not isinstance(key, str) or not key:
            return []
        new = (new or "").strip()
        current = self.get_command_names(key)
        if old not in current:
            return self.add_command_name(key, new) if new else current
        if not new:
            return self.remove_command_name(key, old)
        # 以 new 取代 old 的位置，再去重（dict.fromkeys 保序）並濾空、截斷上限
        replaced = [new if n == old else n for n in current]
        new_list = [n for n in dict.fromkeys(replaced) if n][:_MAX_RECENT_COMMAND_NAMES]
        self._set_command_names(key, new_list)
        old_hotkey = self.get_command_name_hotkey(key, old)
        if old_hotkey and old != new:
            if not self.get_command_name_hotkey(key, new):
                self.set_command_name_hotkey(key, new, old_hotkey)
            self.set_command_name_hotkey(key, old, "")
        return new_list

    # ── 指令頁快捷鍵（獨立命名空間，僅指令彼此之間去重，不與技能／怪物比對衝突）──
    # 同一按鍵若同時綁在技能／怪物上，HotkeyManager 依「技能→怪物→指令」順序比對，
    # 該按鍵會被技能／怪物攔截，指令快捷鍵不會觸發。
    #
    # 兩層儲存：
    #   settings.command_hotkeys      = {cmd_key: KEY}             指令層級（無名稱／MRU 觸發）
    #   settings.command_name_hotkeys = {cmd_key: {name: KEY}}     特定名稱專屬（needs_name 指令）
    # 兩層共用同一份按鍵去重池：設定其中一筆時，會清掉另一層裡值相同的按鍵，
    # 確保同一實體按鍵在指令命名空間裡只對應唯一一個觸發目標。

    def get_command_hotkeys_enabled(self) -> bool:
        """指令快捷鍵總開關（settings.command_hotkeys_enabled）；預設啟用

        關閉時只影響「觸發」（HotkeyManager 按鍵比對階段直接跳過指令命名空間），
        不影響設定／清除快捷鍵本身 —— 關閉狀態下一樣能綁鍵，重新啟用立刻生效。
        """
        return bool(self.get_settings('command_hotkeys_enabled', True))

    def set_command_hotkeys_enabled(self, enabled: bool) -> None:
        self.set_settings('command_hotkeys_enabled', bool(enabled))
        self.save()

    def get_command_hotkeys(self) -> dict[str, str]:
        """取得指令層級快捷鍵 map（{cmd_key: KEY}）；過濾非法型別"""
        m = self.get_settings('command_hotkeys')
        if not isinstance(m, dict):
            return {}
        return {k: v for k, v in m.items()
                if isinstance(k, str) and isinstance(v, str) and v}

    def get_command_hotkey(self, key: str) -> str:
        """取得某指令目前綁定的指令層級按鍵，未綁定回空字串"""
        return self.get_command_hotkeys().get(key, "")

    def get_all_command_name_hotkeys(self) -> dict[str, dict[str, str]]:
        """取得所有指令的「特定名稱」快捷鍵 map（{cmd_key: {name: KEY}}）；過濾非法型別與空 map"""
        m = self.get_settings('command_name_hotkeys')
        if not isinstance(m, dict):
            return {}
        result: dict[str, dict[str, str]] = {}
        for cmd_key, names_map in m.items():
            if not isinstance(cmd_key, str) or not isinstance(names_map, dict):
                continue
            clean = {n: v for n, v in names_map.items()
                     if isinstance(n, str) and isinstance(v, str) and v}
            if clean:
                result[cmd_key] = clean
        return result

    def get_command_name_hotkeys(self, cmd_key: str) -> dict[str, str]:
        """取得某指令下所有「特定名稱」快捷鍵（{name: KEY}）"""
        return self.get_all_command_name_hotkeys().get(cmd_key, {})

    def get_command_name_hotkey(self, cmd_key: str, name: str) -> str:
        """取得某指令下特定名稱目前綁定的按鍵，未綁定回空字串"""
        return self.get_command_name_hotkeys(cmd_key).get(name, "")

    def _iter_command_bindings(self):
        """走訪指令命名空間目前所有綁定，yield (cmd_key, name, hotkey)；name="" 為指令層級

        供 get_command_hotkey_target 等只需要「找」的呼叫端共用同一份走訪邏輯。
        """
        for cmd_key, hk in self.get_command_hotkeys().items():
            yield cmd_key, "", hk
        for cmd_key, names_map in self.get_all_command_name_hotkeys().items():
            for name, hk in names_map.items():
                yield cmd_key, name, hk

    def get_command_hotkey_target(self, key_name: str) -> tuple[str, str] | None:
        """按鍵名稱反查指令命名空間目前綁定的觸發目標。

        Returns:
            (cmd_key, name)：name 為空字串表示指令層級（MRU 觸發）；
            非空字串表示綁在該指令下的特定名稱。查無回 None。
        """
        key_name = (key_name or "").upper()
        if not key_name:
            return None
        for cmd_key, name, hk in self._iter_command_bindings():
            if hk == key_name:
                return cmd_key, name
        return None

    def _clear_command_hotkey(self, hotkey: str) -> tuple[dict, dict]:
        """從指令層級與所有「特定名稱」層級移除等於 hotkey 的綁定（尚未寫入）

        Returns:
            (cmd_map, name_map_all)：清過重複值、可直接疊加新綁定後寫入的兩份 map
        """
        cmd_map = {k: v for k, v in self.get_command_hotkeys().items() if v != hotkey}
        name_map_all: dict[str, dict[str, str]] = {}
        for cmd_key, names_map in self.get_all_command_name_hotkeys().items():
            cleaned = {n: v for n, v in names_map.items() if v != hotkey}
            if cleaned:
                name_map_all[cmd_key] = cleaned
        return cmd_map, name_map_all

    def _save_command_hotkey_maps(self, cmd_map: dict, name_map_all: dict) -> None:
        self.set_settings('command_hotkeys', cmd_map)
        self.set_settings('command_name_hotkeys', name_map_all)
        self.save()

    def set_command_hotkey(self, key: str, hotkey: str) -> None:
        """設定（或以空字串清除）某指令的指令層級快捷鍵，持久化。

        指令命名空間內部去重（含「特定名稱」層級）：新按鍵原本綁在其他指令或
        其他名稱上會自動清除。
        """
        if not isinstance(key, str) or not key:
            return
        hk = (hotkey or "").upper()
        if hk:
            cmd_map, name_map_all = self._clear_command_hotkey(hk)
            cmd_map[key] = hk
        else:
            cmd_map = dict(self.get_command_hotkeys())
            cmd_map.pop(key, None)
            name_map_all = self.get_all_command_name_hotkeys()
        self._save_command_hotkey_maps(cmd_map, name_map_all)

    def set_command_name_hotkey(self, cmd_key: str, name: str, hotkey: str) -> None:
        """設定（或以空字串清除）某指令下特定名稱的快捷鍵，持久化。

        指令命名空間內部去重（含指令層級）：新按鍵原本綁在其他指令／名稱上會自動清除。
        """
        if not isinstance(cmd_key, str) or not cmd_key:
            return
        if not isinstance(name, str) or not name:
            return
        hk = (hotkey or "").upper()
        if hk:
            cmd_map, name_map_all = self._clear_command_hotkey(hk)
            names_map = dict(name_map_all.get(cmd_key, {}))
            names_map[name] = hk
            name_map_all[cmd_key] = names_map
        else:
            cmd_map = dict(self.get_command_hotkeys())
            name_map_all = self.get_all_command_name_hotkeys()
            names_map = dict(name_map_all.get(cmd_key, {}))
            names_map.pop(name, None)
            if names_map:
                name_map_all[cmd_key] = names_map
            else:
                name_map_all.pop(cmd_key, None)
        self._save_command_hotkey_maps(cmd_map, name_map_all)

    # ==================== 內部工具 ====================

    @staticmethod
    def _validate_filename(name: str) -> bool:
        """驗證存檔名稱安全性，防止 Path Traversal 攻擊與 Windows 寫檔失敗

        擋住：
            - 空 / 過長（> 200 char）
            - path traversal：`/` / `\\` / `..`
            - 結尾 `.` 或空白（Windows trim 規則導致歧義）
            - 開頭空白（Windows 視為非法）
            - Windows 不允許字元：`< > : " | ? *`
            - 控制字元（含 NUL 與 RTL override）
            - Windows 保留名：CON / PRN / AUX / NUL / COM0-9 / LPT0-9

        Args:
            name: 待驗證的名稱（不含副檔名）

        Returns:
            合法回傳 True，否則回傳 False
        """
        if not name:
            return False
        if len(name) > _MAX_FILENAME_LEN:
            return False
        if name.startswith(" "):
            return False
        if any(c in name for c in ("/", "\\", "..")):
            return False
        if name[-1] in (" ", "."):
            return False
        if any(c in _BAD_FILENAME_CHARS for c in name):
            return False
        if any(ord(c) < 0x20 for c in name):
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
            atomic_write_json(profile_path, skill_settings)
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
            atomic_write_json(path, data)
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
            atomic_write_json(self._potion_autosave_path(), data)
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


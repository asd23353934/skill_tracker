"""
技能視窗管理模組
處理技能視窗的生命週期、定位、群組拖曳
Phase 4 將完整重寫為 PySide6 SkillWindow
"""

import logging
import os

from src.infrastructure.helpers import resource_path

logger = logging.getLogger(__name__)


def _get_skill_window_cls():
    """延遲匯入 SkillWindow（Phase 4 前使用 tkinter 版本，失敗傳回 None）"""
    try:
        from src.ui.skill_window import SkillWindow as _SW
        return _SW
    except Exception:
        return None


class WindowManager:
    """技能視窗管理器"""

    def __init__(self, app):
        self.app = app
        self.active_windows = {}
        self.window_order = []

        # 佈局常數
        self.H_GAP = 6
        self.V_GAP = 6
        self.MAX_PER_ROW = 10

        # 群組拖曳數據
        self.drag_data = {
            "x": 0, "y": 0,
            "dragging": False,
            "start_x": 0, "start_y": 0,
            "screen_x": 0, "screen_y": 0,
        }

    # ==================== 技能視窗管理 ====================

    def trigger_skill(self, skill_id, player_name=None):
        """觸發技能"""
        skill = self.app.skill_manager.get_skill(skill_id)
        if not skill:
            return

        player = player_name or self.app.player_name

        if skill_id in self.active_windows:
            is_permanent = self.app.skill_permanent.get(skill_id, False)
            is_loop = self.app.skill_loop.get(skill_id, False)
            if is_permanent or is_loop:
                self.active_windows[skill_id].restart_countdown()
            else:
                self.active_windows[skill_id].close()
            return

        if skill_id not in self.window_order:
            self.window_order.append(skill_id)

        position = self._calculate_position(skill_id)
        is_permanent = self.app.skill_permanent.get(skill_id, False)
        is_loop = self.app.skill_loop.get(skill_id, False)
        # Phase 4: qpixmaps 取代舊的 skill_images
        skill_image      = getattr(self.app.skill_manager, "skill_images", {}).get(skill_id)
        skill_image_path = self.app.skill_manager.skill_image_paths.get(skill_id)
        alert_enabled    = self.app.skill_alert_enabled.get(skill_id, False)

        SkillWindow = _get_skill_window_cls()
        if SkillWindow is None:
            return

        try:
            skill_window = SkillWindow(
                skill, player, position, skill_image,
                lambda w: self._on_window_close(w, skill_id),
                self.app.enable_sound, skill_id,
                is_permanent=is_permanent,
                is_loop=is_loop,
                window_alpha=self.app.window_alpha,
                alert_enabled=alert_enabled,
                alert_before_seconds=self.app.get_alert_seconds(skill_id),
                on_drag_start=self.on_drag_start,
                on_drag_motion=self.on_drag_motion,
                on_drag_end=self.on_drag_end,
                window_size=self.app.window_size,
                skill_image_path=skill_image_path,
                sound_manager=self.app.sound_manager,
                sound_filename=self.app.get_sound_for_skill(skill_id),
                alert_sound_filename=self.app.get_alert_sound_for_skill(skill_id),
            )
            self.active_windows[skill_id] = skill_window
        except Exception:
            pass

    def trigger_monster(self, monster_id):
        """觸發怪物重生計時（正數模式：從 0 數到目標秒數）"""
        if monster_id in self.active_windows:
            # 已有視窗：重新開始計時
            self.active_windows[monster_id].restart_countdown()
            return

        monster = self.app.get_monster(monster_id)
        if not monster:
            return

        is_permanent = monster.get("permanent", False)
        self._create_monster_window(monster_id, is_permanent=is_permanent)

    def create_permanent_monster_window(self, monster_id):
        """建立常駐怪物視窗（idle 狀態，等待按鍵觸發計時）"""
        self._create_monster_window(monster_id, is_permanent=True, idle_start=True)

    def _create_monster_window(self, monster_id, *, is_permanent: bool, idle_start: bool = False):
        """建立怪物視窗的共用邏輯（供 trigger_monster / create_permanent_monster_window 呼叫）

        Args:
            monster_id: 怪物 ID
            is_permanent: 是否常駐（視窗結束後自動重置為 idle）
            idle_start: 是否以 idle 狀態啟動（常駐視窗啟動時使用）
        """
        monster = self.app.get_monster(monster_id)
        if not monster:
            return

        if monster_id not in self.window_order:
            self.window_order.append(monster_id)

        position = self._calculate_position(monster_id)
        img_path = self._resolve_monster_image_path(monster)

        alert_before = monster.get("alert_before", 10)
        monster_alert_sound   = monster.get("alert_sound", "")
        effective_alert_sound = monster_alert_sound or self.app.global_alert_sound
        monster_end_sound     = monster.get("sound", "")
        effective_end_sound   = monster_end_sound or self.app.global_sound
        is_loop = monster.get("loop", True)

        SkillWindow = _get_skill_window_cls()
        if SkillWindow is None:
            return

        try:
            skill_window = SkillWindow(
                monster, self.app.player_name, position, None,
                lambda w: self._on_window_close(w, monster_id),
                self.app.enable_sound, monster_id,
                is_permanent=is_permanent,
                is_loop=is_loop,
                window_alpha=self.app.window_alpha,
                alert_enabled=(alert_before > 0),
                alert_before_seconds=alert_before,
                on_drag_start=self.on_drag_start,
                on_drag_motion=self.on_drag_motion,
                on_drag_end=self.on_drag_end,
                window_size=self.app.window_size,
                skill_image_path=img_path,
                sound_manager=self.app.sound_manager,
                sound_filename=effective_end_sound,
                alert_sound_filename=effective_alert_sound,
                count_up=True,
                idle_start=idle_start,
            )
            self.active_windows[monster_id] = skill_window
        except Exception:
            pass

    def _resolve_monster_image_path(self, monster: dict) -> str | None:
        """解析怪物圖片的完整路徑，若檔案不存在則回傳 None

        Args:
            monster: 怪物資料字典

        Returns:
            存在的圖片路徑，或 None
        """
        icon_file = monster.get("icon", "")
        if not icon_file:
            return None
        candidate = resource_path(f"images/{icon_file}")
        return candidate if os.path.exists(candidate) else None

    def create_permanent_window(self, skill_id):
        """建立技能常駐視窗"""
        skill = self.app.skill_manager.get_skill(skill_id)
        if not skill:
            return

        if skill_id not in self.window_order:
            self.window_order.append(skill_id)

        position = self._calculate_position(skill_id)
        # Phase 4: qpixmaps 取代舊的 skill_images
        skill_image      = getattr(self.app.skill_manager, "skill_images", {}).get(skill_id)
        skill_image_path = self.app.skill_manager.skill_image_paths.get(skill_id)
        alert_enabled    = self.app.skill_alert_enabled.get(skill_id, False)

        SkillWindow = _get_skill_window_cls()
        if SkillWindow is None:
            return

        try:
            skill_window = SkillWindow(
                skill, self.app.player_name, position, skill_image,
                lambda w: self._on_window_close(w, skill_id),
                self.app.enable_sound, skill_id,
                is_permanent=True, is_loop=False,
                start_at_zero=True,
                window_alpha=self.app.window_alpha,
                alert_enabled=alert_enabled,
                alert_before_seconds=self.app.get_alert_seconds(skill_id),
                on_drag_start=self.on_drag_start,
                on_drag_motion=self.on_drag_motion,
                on_drag_end=self.on_drag_end,
                window_size=self.app.window_size,
                skill_image_path=skill_image_path,
                sound_manager=self.app.sound_manager,
                sound_filename=self.app.get_sound_for_skill(skill_id),
                alert_sound_filename=self.app.get_alert_sound_for_skill(skill_id),
            )
            self.active_windows[skill_id] = skill_window
        except Exception:
            pass

    def initialize_persistent_skills(self):
        """初始化常駐技能與常駐怪物（循環技能不初始化，等待按鍵觸發）"""
        for skill_id, is_permanent in self.app.skill_permanent.items():
            if is_permanent and skill_id not in self.active_windows:
                self.create_permanent_window(skill_id)

        for monster in self.app.get_all_monsters():
            if monster.get("permanent", False) and monster["id"] not in self.active_windows:
                self.create_permanent_monster_window(monster["id"])

    def _calculate_position(self, skill_id):
        """計算技能視窗位置（從右往左、從上往下）"""
        index = self.window_order.index(skill_id)
        col = index % self.MAX_PER_ROW
        row = index // self.MAX_PER_ROW

        x = self.app.skill_start_x - col * (self.app.window_size + self.H_GAP)
        y = self.app.skill_start_y - row * (self.app.window_size + self.V_GAP)
        return (x, y)

    def reposition_all(self):
        """重新定位所有技能視窗"""
        for skill_id in self.window_order:
            if skill_id in self.active_windows:
                x, y = self._calculate_position(skill_id)
                self.active_windows[skill_id].update_position(x, y)

    def close_all(self):
        """關閉所有技能/怪物視窗（切換配置、套用新設定時使用）"""
        for sid in list(self.active_windows.keys()):
            try:
                self.active_windows[sid].close()
            except Exception:
                logger.exception("close_all: 關閉視窗失敗 sid=%r", sid)
        self.active_windows.clear()
        self.window_order.clear()

    def refresh_window_sound_params(self, skill_id):
        """同步技能的音效與提前秒數至活躍視窗（細節設定/全域設定變更後呼叫）"""
        win = self.active_windows.get(skill_id)
        if win is None:
            return
        win.alert_before_seconds = self.app.get_alert_seconds(skill_id)
        win.sound_filename       = self.app.get_sound_for_skill(skill_id)
        win.alert_sound_filename = self.app.get_alert_sound_for_skill(skill_id)

    def _on_window_close(self, window, skill_id):
        """技能視窗關閉回調"""
        if skill_id in self.active_windows:
            del self.active_windows[skill_id]
        if skill_id in self.window_order:
            self.window_order.remove(skill_id)
        self.reposition_all()

    # ==================== 群組拖曳 ====================

    def on_drag_start(self, global_x: int, global_y: int):
        """開始拖曳技能（整組）

        Args:
            global_x: 滑鼠螢幕 X 座標（由 SkillWindow.mousePressEvent 提供）
            global_y: 滑鼠螢幕 Y 座標
        """
        self.drag_data["screen_x"] = global_x
        self.drag_data["screen_y"] = global_y
        self.drag_data["dragging"] = True
        self.drag_data["start_x"] = self.app.skill_start_x
        self.drag_data["start_y"] = self.app.skill_start_y

    def on_drag_motion(self, global_x: int, global_y: int):
        """拖曳技能中（整組移動）

        Args:
            global_x: 滑鼠螢幕 X 座標
            global_y: 滑鼠螢幕 Y 座標
        """
        if not self.drag_data["dragging"]:
            return

        delta_x = global_x - self.drag_data["screen_x"]
        delta_y = global_y - self.drag_data["screen_y"]

        self.app.skill_start_x = self.drag_data["start_x"] + delta_x
        self.app.skill_start_y = self.drag_data["start_y"] + delta_y

        self.reposition_all()

    def on_drag_end(self, global_x: int, global_y: int):
        """結束拖曳技能

        Args:
            global_x: 滑鼠螢幕 X 座標
            global_y: 滑鼠螢幕 Y 座標
        """
        if self.drag_data["dragging"]:
            self.drag_data["dragging"] = False

            self.app.config_manager.set_settings("skill_start_x", self.app.skill_start_x)
            self.app.config_manager.set_settings("skill_start_y", self.app.skill_start_y)
            self.app.config_manager.save()

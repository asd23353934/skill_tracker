"""
技能視窗管理模組
處理技能視窗的生命週期、定位、群組拖曳
"""

from src.ui.skill_window import SkillWindow


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
        skill_image = self.app.skill_manager.skill_images.get(skill_id)
        skill_image_path = self.app.skill_manager.skill_image_paths.get(skill_id)
        alert_enabled = self.app.skill_alert_enabled.get(skill_id, False)

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

    def trigger_monster(self, monster_id):
        """觸發怪物重生計時（正數模式：從 0 數到目標秒數）"""
        monster = self.app.get_monster(monster_id)
        if not monster:
            return

        # 若已有視窗，重新開始
        if monster_id in self.active_windows:
            self.active_windows[monster_id].restart_countdown()
            return

        if monster_id not in self.window_order:
            self.window_order.append(monster_id)

        position = self._calculate_position(monster_id)

        # 取得怪物圖片路徑
        icon_file = monster.get("icon", "")
        img_path = None
        if icon_file:
            from src.ui.helpers import resource_path
            import os
            candidate = resource_path(f"images/{icon_file}")
            if os.path.exists(candidate):
                img_path = candidate

        alert_before = monster.get("alert_before", 10)

        # 怪物提示聲音：若卡牌有設定則用卡牌的，否則用全域
        monster_alert_sound = monster.get("alert_sound", "")
        effective_alert_sound = monster_alert_sound or self.app.global_alert_sound
        effective_sound = self.app.global_sound

        skill_window = SkillWindow(
            monster, self.app.player_name, position, None,
            lambda w: self._on_window_close(w, monster_id),
            self.app.enable_sound, monster_id,
            is_permanent=False, is_loop=False,
            window_alpha=self.app.window_alpha,
            alert_enabled=(alert_before > 0),
            alert_before_seconds=alert_before,
            on_drag_start=self.on_drag_start,
            on_drag_motion=self.on_drag_motion,
            on_drag_end=self.on_drag_end,
            window_size=self.app.window_size,
            skill_image_path=img_path,
            sound_manager=self.app.sound_manager,
            sound_filename=effective_sound,
            alert_sound_filename=effective_alert_sound,
            count_up=True,
        )
        self.active_windows[monster_id] = skill_window

    def create_permanent_window(self, skill_id):
        """創建常駐視窗"""
        skill = self.app.skill_manager.get_skill(skill_id)
        if not skill:
            return

        if skill_id not in self.window_order:
            self.window_order.append(skill_id)

        position = self._calculate_position(skill_id)
        skill_image = self.app.skill_manager.skill_images.get(skill_id)
        skill_image_path = self.app.skill_manager.skill_image_paths.get(skill_id)
        alert_enabled = self.app.skill_alert_enabled.get(skill_id, False)

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

    def initialize_persistent_skills(self):
        """初始化常駐技能（循環技能不初始化，等待按鍵觸發）"""
        for skill_id, is_permanent in self.app.skill_permanent.items():
            if is_permanent and skill_id not in self.active_windows:
                self.create_permanent_window(skill_id)

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

    def _on_window_close(self, window, skill_id):
        """技能視窗關閉回調"""
        if skill_id in self.active_windows:
            del self.active_windows[skill_id]
        if skill_id in self.window_order:
            self.window_order.remove(skill_id)
        self.reposition_all()

    # ==================== 群組拖曳 ====================

    def on_drag_start(self, event):
        """開始拖曳技能（整組）"""
        widget = event.widget
        toplevel = widget.winfo_toplevel() if hasattr(widget, "winfo_toplevel") else widget

        self.drag_data["screen_x"] = toplevel.winfo_pointerx()
        self.drag_data["screen_y"] = toplevel.winfo_pointery()
        self.drag_data["dragging"] = True
        self.drag_data["start_x"] = self.app.skill_start_x
        self.drag_data["start_y"] = self.app.skill_start_y

    def on_drag_motion(self, event):
        """拖曳技能中（整組移動）"""
        if not self.drag_data["dragging"]:
            return

        widget = event.widget
        toplevel = widget.winfo_toplevel() if hasattr(widget, "winfo_toplevel") else widget

        current_screen_x = toplevel.winfo_pointerx()
        current_screen_y = toplevel.winfo_pointery()

        delta_x = current_screen_x - self.drag_data["screen_x"]
        delta_y = current_screen_y - self.drag_data["screen_y"]

        self.app.skill_start_x = self.drag_data["start_x"] + delta_x
        self.app.skill_start_y = self.drag_data["start_y"] + delta_y

        self.reposition_all()

    def on_drag_end(self, event):
        """結束拖曳技能"""
        if self.drag_data["dragging"]:
            self.drag_data["dragging"] = False

            self.app.config_manager.set_settings("skill_start_x", self.app.skill_start_x)
            self.app.config_manager.set_settings("skill_start_y", self.app.skill_start_y)
            self.app.config_manager.save()

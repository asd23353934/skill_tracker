"""
主視窗模組 - 單機版
技能追蹤與管理
"""

import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
from pynput import keyboard
import time

from src.ui.components import RoundedButton, SectionFrame, ScrollableFrame
from src.ui.dialogs import ProfileManagerDialog, SettingsDialog
from src.ui.skill_window import SkillWindow
from src.ui.config_manager import ConfigManager
from src.ui.skill_manager import SkillManager
from src.ui.styles import Colors, Fonts, Sizes
from src.ui.helpers import resource_path


class MainWindow:
    """主視窗類別"""
    
    def __init__(self):
        """初始化主視窗"""
        # 獲取版本號
        try:
            from version import get_version
            version_str = f" v{get_version()}"
        except:
            version_str = ""
        
        # 創建根視窗
        self.root = tk.Tk()
        self.root.title(f"🎮 技能追蹤器 - Artale 楓之谷{version_str}")
        self.root.attributes('-topmost', True)
        self.root.attributes('-alpha', 0.96)
        self.root.configure(bg=Colors.BG_DARK)
        self.root.geometry("1600x900+100+50")
        
        # 初始化管理器
        try:
            self.config_manager = ConfigManager(resource_path('config.json'))
            self.skill_manager = SkillManager(self.config_manager)
        except Exception as e:
            messagebox.showerror("錯誤", f"初始化失敗: {e}")
            self.root.destroy()
            return
        
        # 初始化變數
        self._init_variables()
        
        # 創建 UI
        self._create_ui()
        
        # 啟動鍵盤監聽
        self._start_keyboard_listener()
        
        # 初始化駐留技能
        self._initialize_permanent_skills()
        
        # 檢查更新（非阻塞）
        self.root.after(1000, self._check_for_updates)
    
    def _init_variables(self):
        """初始化變數"""
        # 確保預設配置存在
        self.config_manager.ensure_default_profile()
        
        # 獲取當前配置名稱
        self.current_profile_name = self.config_manager.get_current_profile()
        
        # 載入當前配置
        profile_data = self.config_manager.load_profile(self.current_profile_name)
        
        settings = self.config_manager.config.get('settings', {})
        
        # 技能視窗管理
        self.active_windows = {}
        self.window_order = []
        
        # 🆕 獲取螢幕尺寸並計算中央位置
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        default_x = screen_width // 2
        default_y = screen_height // 2
        
        # 設定
        self.player_name = settings.get('player_name', '玩家1')
        self.skill_start_x = settings.get('skill_start_x', default_x)  # 🆕 預設中央
        self.skill_start_y = settings.get('skill_start_y', default_y)  # 🆕 預設中央
        self.enable_sound = settings.get('enable_sound', True)
        self.window_alpha = 0.95  # 固定透明度
        self.window_size = settings.get('window_size', 64)  # 🆕 視窗大小設定
        
        # 🆕 提前提示音設定
        self.alert_before_seconds = settings.get('alert_before_seconds', 0)
        
        # 技能設定 - 從配置檔案載入
        if profile_data:
            self.skill_permanent = profile_data.get('permanent', {})
            self.skill_loop = profile_data.get('loop', {})
            self.skill_alert_enabled = profile_data.get('alert_enabled', {})
            
            # 載入快捷鍵到技能管理器
            hotkeys = profile_data.get('hotkeys', {})
            for skill_id, hotkey in hotkeys.items():
                skill = self.skill_manager.get_skill(skill_id)
                if skill:
                    skill['hotkey'] = hotkey
            
            # 載入秒數覆寫
            cooldown_overrides = profile_data.get('cooldown_overrides', {})
            for skill_id, cooldown in cooldown_overrides.items():
                skill = self.skill_manager.get_skill(skill_id)
                if skill:
                    skill['cooldown'] = cooldown
        else:
            self.skill_permanent = {}
            self.skill_loop = {}
            self.skill_alert_enabled = {}
        
        # 初始化所有技能的預設值
        for skill_id in self.skill_manager.get_all_skills():
            self.skill_permanent.setdefault(skill_id, False)
            self.skill_loop.setdefault(skill_id, False)
            self.skill_alert_enabled.setdefault(skill_id, False)
        
        # UI 控制
        self.keyboard_enabled = True
        self.waiting_for_hotkey = None
        self.waiting_skill_name = None
        
        # UI 元件字典
        self.permanent_vars = {}
        self.loop_vars = {}
        self.alert_enabled_vars = {}
        self.hotkey_buttons = {}
        self.cooldown_buttons = {}
        
        # 🔧 技能視窗常數（使用動態大小）
        self.H_GAP = 6
        self.V_GAP = 6
        self.MAX_PER_ROW = 10
        
        # 🔧 技能組拖曳數據
        self.group_drag_data = {'x': 0, 'y': 0, 'dragging': False, 'start_x': 0, 'start_y': 0}
    
    # ==================== UI 創建 ====================
    
    def _create_ui(self):
        """創建主要 UI"""
        # 頂部標題列
        self._create_header()
        
        # 主內容區 - 四欄佈局
        main_container = tk.Frame(self.root, bg=Colors.BG_DARK)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 第一欄：玩家技能
        col1 = tk.Frame(main_container, bg=Colors.BG_DARK)
        col1.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        self._create_player_skills_column(col1)
        
        # 第二欄：BOSS 技能
        col2 = tk.Frame(main_container, bg=Colors.BG_DARK)
        col2.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        self._create_boss_skills_column(col2)
        
        # 第三欄：道具
        col3 = tk.Frame(main_container, bg=Colors.BG_DARK)
        col3.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        self._create_items_column(col3)
    
    def _create_header(self):
        """創建頂部標題列"""
        from src.ui.components import RoundedFrame
        
        header_frame = RoundedFrame(
            self.root, radius=12, bg=Colors.BG_MEDIUM,
            border_color=Colors.ACCENT_YELLOW, border_width=3,
            fixed_height=True
        )
        header_frame.pack(fill=tk.X, side=tk.TOP, padx=10, pady=(10, 5))
        header_frame.configure(height=70)
        
        header = header_frame.get_content()
        
        # 左側標題
        tk.Label(
            header, text="🎮 技能追蹤器", 
            bg=Colors.BG_MEDIUM, fg=Colors.ACCENT_YELLOW,
            font=Fonts.TITLE_LARGE
        ).pack(side=tk.LEFT, padx=20, pady=15)
        
        tk.Label(
            header, text="Artale 楓之谷", 
            bg=Colors.BG_MEDIUM, fg=Colors.TEXT_SECONDARY,
            font=Fonts.BODY_MEDIUM
        ).pack(side=tk.LEFT, pady=15)
        
        # 當前配置顯示
        tk.Label(
            header, text="|", 
            bg=Colors.BG_MEDIUM, fg=Colors.TEXT_SECONDARY,
            font=Fonts.BODY_MEDIUM
        ).pack(side=tk.LEFT, padx=10)
        
        tk.Label(
            header, text="📋", 
            bg=Colors.BG_MEDIUM, fg=Colors.ACCENT_BLUE,
            font=Fonts.BODY_MEDIUM
        ).pack(side=tk.LEFT)
        
        self.current_profile_label = tk.Label(
            header, text=self.current_profile_name, 
            bg=Colors.BG_MEDIUM, fg=Colors.ACCENT_BLUE,
            font=Fonts.BODY_MEDIUM_BOLD
        )
        self.current_profile_label.pack(side=tk.LEFT, padx=5)
        
        # 右側按鈕組
        right_buttons = tk.Frame(header, bg=Colors.BG_MEDIUM)
        right_buttons.pack(side=tk.RIGHT, padx=20, pady=15)
        
        # 更新按鈕（初始隱藏）
        self.update_button = RoundedButton(
            right_buttons, "⬆️ 有新版本", self._show_update_dialog,
            Colors.ACCENT_GREEN, width=100, height=30
        )
        
        # 清空按鍵按鈕
        RoundedButton(
            right_buttons, "清空按鍵", self._clear_all_hotkeys,
            Colors.ACCENT_RED, width=100, height=30
        ).pack(side=tk.LEFT, padx=3)
        
        # 配置管理按鈕
        RoundedButton(
            right_buttons, "💾 配置管理", self._show_profile_manager,
            Colors.ACCENT_PURPLE, width=100, height=30
        ).pack(side=tk.LEFT, padx=3)
        
        # 全選按鈕組
        quick_btns = tk.Frame(right_buttons, bg=Colors.BG_MEDIUM)
        quick_btns.pack(side=tk.LEFT, padx=5)
        
        tk.Label(
            quick_btns, text="全選:", 
            bg=Colors.BG_MEDIUM, fg=Colors.TEXT_SECONDARY,
            font=Fonts.BODY_SMALL
        ).pack(side=tk.LEFT, padx=3)
        
        RoundedButton(
            quick_btns, "常駐", lambda: self._toggle_all('permanent'),
            Colors.ACCENT_YELLOW, width=50, height=25
        ).pack(side=tk.LEFT, padx=1)
        
        RoundedButton(
            quick_btns, "循環", lambda: self._toggle_all('loop'),
            Colors.ACCENT_GREEN, width=50, height=25
        ).pack(side=tk.LEFT, padx=1)
        
        # 🔧 提前提示全選按鈕
        RoundedButton(
            quick_btns, "提前提示", lambda: self._toggle_all('alert'),
            Colors.ACCENT_ORANGE, width=65, height=25
        ).pack(side=tk.LEFT, padx=1)
        
        # 設定按鈕
        RoundedButton(
            right_buttons, "⚙️ 設定", self._show_settings,
            Colors.BG_LIGHT, width=80, height=30
        ).pack(side=tk.LEFT, padx=3)
        
        # 按鍵設定提示標籤
        self.hotkey_hint_label = tk.Label(
            header, text="", 
            bg=Colors.BG_MEDIUM, fg=Colors.ACCENT_GREEN,
            font=Fonts.BODY_LARGE_BOLD
        )
        self.hotkey_hint_label.pack(side=tk.RIGHT, padx=20, pady=15)
    
    def _create_player_skills_column(self, parent):
        """創建玩家技能欄"""
        self._create_column_title(parent, "⚔️ 玩家技能")
        
        self.player_scroll_frame = ScrollableFrame(parent)
        self.player_scroll_frame.pack(fill=tk.BOTH, expand=True)
        
        content = self.player_scroll_frame.get_content()
        
        if 'player' in self.skill_manager.skill_categories:
            for subcategory, skill_ids in sorted(self.skill_manager.get_categories('player').items()):
                group = self._create_skill_group(content, subcategory, skill_ids)
                if group:
                    self.player_scroll_frame.bind_widget_to_scroll(group)
    
    def _create_boss_skills_column(self, parent):
        """創建 BOSS 技能欄"""
        self._create_column_title(parent, "👹 BOSS 技能")
        
        self.boss_scroll_frame = ScrollableFrame(parent)
        self.boss_scroll_frame.pack(fill=tk.BOTH, expand=True)
        
        content = self.boss_scroll_frame.get_content()
        
        if 'boss' in self.skill_manager.skill_categories:
            for subcategory, skill_ids in sorted(self.skill_manager.get_categories('boss').items()):
                group = self._create_skill_group(content, subcategory, skill_ids)
                if group:
                    self.boss_scroll_frame.bind_widget_to_scroll(group)
    
    def _create_items_column(self, parent):
        """創建道具欄"""
        self._create_column_title(parent, "🎁 道具")
        
        self.items_scroll_frame = ScrollableFrame(parent)
        self.items_scroll_frame.pack(fill=tk.BOTH, expand=True)
        
        content = self.items_scroll_frame.get_content()
        
        if 'item' in self.skill_manager.skill_categories:
            for subcategory, item_ids in sorted(self.skill_manager.get_categories('item').items()):
                group = self._create_skill_group(content, subcategory, item_ids)
                if group:
                    self.items_scroll_frame.bind_widget_to_scroll(group)
    
    def _create_column_title(self, parent, text):
        """創建欄位標題"""
        from src.ui.components import RoundedFrame
        
        title_frame_wrapper = RoundedFrame(
            parent, radius=10, bg=Colors.BG_MEDIUM,
            border_color=Colors.ACCENT_BLUE, border_width=2
        )
        title_frame_wrapper.pack(fill=tk.X, pady=(0, 5))
        
        title_frame = title_frame_wrapper.get_content()
        
        tk.Label(
            title_frame, text=text,
            bg=Colors.BG_MEDIUM, fg=Colors.TEXT_PRIMARY,
            font=Fonts.TITLE_MEDIUM
        ).pack(side=tk.LEFT, padx=15, pady=15)
    
    def _create_skill_group(self, parent, subcategory, skill_ids):
        """創建技能分組"""
        from src.ui.components import RoundedFrame
        
        group_wrapper = RoundedFrame(
            parent, radius=8, bg=Colors.BG_MEDIUM,
            border_color=Colors.BG_LIGHT, border_width=1
        )
        group_wrapper.pack(fill=tk.X, pady=5, padx=5)
        
        group_frame = group_wrapper.get_content()
        
        # 分組標題
        title_frame = tk.Frame(group_frame, bg=Colors.BG_MEDIUM)
        title_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(
            title_frame, text=f"📂 {subcategory}",
            bg=Colors.BG_MEDIUM, fg=Colors.ACCENT_YELLOW,
            font=Fonts.BODY_LARGE_BOLD
        ).pack(anchor='w', padx=5)
        
        # 技能列表
        for skill_id in skill_ids:
            skill = self.skill_manager.get_skill(skill_id)
            if skill:
                self._create_skill_item(group_frame, skill_id, skill)
        
        return group_wrapper
    
    def _create_skill_item(self, parent, skill_id, skill):
        """創建技能項目"""
        from src.ui.components import RoundedFrame
        
        item_wrapper = RoundedFrame(
            parent, radius=6, bg=Colors.BG_DARK,
            border_color=Colors.BG_LIGHT, border_width=1
        )
        item_wrapper.pack(fill=tk.X, padx=8, pady=3)
        
        item_frame = item_wrapper.get_content()
        
        # 左側：圖示 + 資訊
        left_frame = tk.Frame(item_frame, bg=Colors.BG_DARK)
        left_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 顯示圖示
        if self.skill_manager.skill_images_small.get(skill_id):
            img_label = tk.Label(
                left_frame,
                image=self.skill_manager.skill_images_small[skill_id],
                bg=Colors.BG_DARK
            )
            img_label.image = self.skill_manager.skill_images_small[skill_id]
            img_label.pack(side=tk.LEFT, padx=5, pady=3)
        
        # 技能資訊
        info_frame = tk.Frame(left_frame, bg=Colors.BG_DARK)
        info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # 技能名稱
        tk.Label(
            info_frame, text=skill['name'],
            bg=Colors.BG_DARK, fg=Colors.TEXT_PRIMARY,
            font=Fonts.BODY_MEDIUM
        ).pack(anchor='w')
        
        # 冷卻時間 + 快捷鍵
        bottom_info = tk.Frame(info_frame, bg=Colors.BG_DARK)
        bottom_info.pack(anchor='w', pady=2)
        
        # 秒數按鈕
        original_cooldown = self._get_original_cooldown(skill_id)
        is_modified = original_cooldown and skill['cooldown'] != original_cooldown
        
        cooldown_btn = RoundedButton(
            bottom_info, f"{skill['cooldown']}秒",
            lambda sid=skill_id: self._edit_cooldown(sid),
            Colors.ACCENT_BLUE if is_modified else Colors.BG_MEDIUM,
            fg_color='#FFFFFF' if is_modified else Colors.TEXT_PRIMARY,
            width=60, height=20
        )
        cooldown_btn.pack(side=tk.LEFT, padx=(0, 2))
        
        # 重置秒數按鈕
        reset_cooldown_btn = RoundedButton(
            bottom_info, "🔄",
            lambda sid=skill_id: self._reset_cooldown(sid),
            Colors.BG_MEDIUM,
            fg_color=Colors.TEXT_SECONDARY,
            width=20, height=20
        )
        reset_cooldown_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        if not hasattr(self, 'cooldown_buttons'):
            self.cooldown_buttons = {}
        self.cooldown_buttons[skill_id] = cooldown_btn
        
        # 快捷鍵按鈕
        hotkey_text = skill.get('hotkey', '') or '未設定'
        has_hotkey = bool(skill.get('hotkey'))
        hotkey_btn = RoundedButton(
            bottom_info, hotkey_text,
            lambda sid=skill_id: self._start_hotkey_capture(sid),
            Colors.ACCENT_YELLOW if has_hotkey else Colors.BG_MEDIUM,
            fg_color='#000000' if has_hotkey else Colors.TEXT_SECONDARY,
            width=60, height=20
        )
        hotkey_btn.pack(side=tk.LEFT, padx=(0, 2))
        self.hotkey_buttons[skill_id] = hotkey_btn
        
        # 重置按鍵按鈕
        reset_hotkey_btn = RoundedButton(
            bottom_info, "🔄",
            lambda sid=skill_id: self._reset_hotkey(sid),
            Colors.BG_MEDIUM,
            fg_color=Colors.TEXT_SECONDARY,
            width=20, height=20
        )
        reset_hotkey_btn.pack(side=tk.LEFT)
        
        # 右側：選項
        options_frame = tk.Frame(item_frame, bg=Colors.BG_DARK)
        options_frame.pack(side=tk.RIGHT, padx=5)
        
        self._create_skill_checkboxes(options_frame, skill_id)
    
    def _create_skill_checkboxes(self, parent, skill_id):
        """創建技能選項"""
        # 常駐 checkbox
        permanent_var = tk.BooleanVar(value=self.skill_permanent.get(skill_id, False))
        self.permanent_vars[skill_id] = permanent_var
        
        permanent_cb = tk.Checkbutton(
            parent, text='常駐', variable=permanent_var,
            command=lambda sid=skill_id, v=permanent_var:
                self._update_skill_setting_exclusive(sid, 'permanent', v),
            bg=Colors.BG_DARK, fg=Colors.ACCENT_YELLOW,
            font=Fonts.BODY_SMALL,
            selectcolor=Colors.BG_MEDIUM,
            activebackground=Colors.BG_DARK
        )
        permanent_cb.pack(side=tk.LEFT, padx=2)
        
        # 循環 checkbox
        loop_var = tk.BooleanVar(value=self.skill_loop.get(skill_id, False))
        self.loop_vars[skill_id] = loop_var
        
        loop_cb = tk.Checkbutton(
            parent, text='循環', variable=loop_var,
            command=lambda sid=skill_id, v=loop_var:
                self._update_skill_setting_exclusive(sid, 'loop', v),
            bg=Colors.BG_DARK, fg=Colors.ACCENT_GREEN,
            font=Fonts.BODY_SMALL,
            selectcolor=Colors.BG_MEDIUM,
            activebackground=Colors.BG_DARK
        )
        loop_cb.pack(side=tk.LEFT, padx=2)
        
        # 提前提示 checkbox
        alert_var = tk.BooleanVar(value=self.skill_alert_enabled.get(skill_id, False))
        self.alert_enabled_vars[skill_id] = alert_var
        
        alert_cb = tk.Checkbutton(
            parent, text='提前提示', variable=alert_var,
            command=lambda sid=skill_id, v=alert_var:
                self._update_alert_setting(sid, v),
            bg=Colors.BG_DARK, fg=Colors.ACCENT_ORANGE,
            font=Fonts.BODY_SMALL,
            selectcolor=Colors.BG_MEDIUM,
            activebackground=Colors.BG_DARK
        )
        alert_cb.pack(side=tk.LEFT, padx=2)
    
    # 🔧 ==================== 技能組拖曳 ====================
    
    def _on_skill_drag_start(self, event):
        """開始拖曳技能（整組）"""
        # 🔧 使用螢幕絕對座標
        widget = event.widget
        if hasattr(widget, 'winfo_toplevel'):
            toplevel = widget.winfo_toplevel()
        else:
            toplevel = widget
        
        # 記錄滑鼠的螢幕絕對座標
        self.group_drag_data['screen_x'] = toplevel.winfo_pointerx()
        self.group_drag_data['screen_y'] = toplevel.winfo_pointery()
        self.group_drag_data['dragging'] = True
        self.group_drag_data['start_x'] = self.skill_start_x
        self.group_drag_data['start_y'] = self.skill_start_y
    
    def _on_skill_drag_motion(self, event):
        """拖曳技能中（整組移動）"""
        if not self.group_drag_data['dragging']:
            return
        
        # 🔧 使用螢幕絕對座標計算位移
        widget = event.widget
        if hasattr(widget, 'winfo_toplevel'):
            toplevel = widget.winfo_toplevel()
        else:
            toplevel = widget
        
        current_screen_x = toplevel.winfo_pointerx()
        current_screen_y = toplevel.winfo_pointery()
        
        delta_x = current_screen_x - self.group_drag_data['screen_x']
        delta_y = current_screen_y - self.group_drag_data['screen_y']
        
        # 更新技能起始座標
        self.skill_start_x = self.group_drag_data['start_x'] + delta_x
        self.skill_start_y = self.group_drag_data['start_y'] + delta_y
        
        # 即時更新所有技能位置
        self._reposition_windows()
    
    def _on_skill_drag_end(self, event):
        """結束拖曳技能"""
        if self.group_drag_data['dragging']:
            self.group_drag_data['dragging'] = False
            
            # 保存新位置
            self.config_manager.set_settings('skill_start_x', self.skill_start_x)
            self.config_manager.set_settings('skill_start_y', self.skill_start_y)
            self.config_manager.save()
            
            print(f"💾 技能位置已保存: ({self.skill_start_x}, {self.skill_start_y})")
    
    # ==================== 配置管理 ====================
    
    def _auto_save_current_profile(self):
        """自動保存當前配置"""
        current_settings = self._get_current_settings()
        self.config_manager.save_profile(self.current_profile_name, current_settings)
        print(f"💾 自動保存配置: {self.current_profile_name}")
    
    def _show_profile_manager(self):
        """顯示配置管理視窗"""
        self.keyboard_enabled = False
        
        dialog = ProfileManagerDialog(
            self.root,
            self.config_manager,
            self._get_current_settings(),
            self
        )
        
        result = dialog.show()
        
        if result:
            self._apply_profile(result)
        
        self.keyboard_enabled = True
    
    def _get_current_settings(self):
        """獲取當前設定"""
        cooldown_overrides = {}
        for skill_id, skill in self.skill_manager.get_all_skills().items():
            original_cooldown = self._get_original_cooldown(skill_id)
            current_cooldown = skill.get('cooldown')
            if original_cooldown and current_cooldown != original_cooldown:
                cooldown_overrides[skill_id] = current_cooldown
        
        return {
            'hotkeys': {
                sid: skill.get('hotkey', '')
                for sid, skill in self.skill_manager.get_all_skills().items()
            },
            'permanent': self.skill_permanent.copy(),
            'loop': self.skill_loop.copy(),
            'alert_enabled': self.skill_alert_enabled.copy(),
            'cooldown_overrides': cooldown_overrides
        }
    
    def _get_original_cooldown(self, skill_id):
        """獲取技能的原始秒數"""
        for skill_data in self.config_manager.initial_skills:
            if skill_data['id'] == skill_id:
                return skill_data.get('cooldown')
        
        for item_data in self.config_manager.initial_items:
            if item_data['id'] == skill_id:
                return item_data.get('cooldown')
        
        return None
    
    def _apply_profile(self, profile_data):
        """套用配置"""
        self.current_profile_name = self.config_manager.get_current_profile()
        
        for skill_id, skill in self.skill_manager.get_all_skills().items():
            original_cooldown = self._get_original_cooldown(skill_id)
            if original_cooldown:
                skill['cooldown'] = original_cooldown
            skill['hotkey'] = ''
        
        hotkeys = profile_data.get('hotkeys', {})
        for skill_id, hotkey in hotkeys.items():
            skill = self.skill_manager.get_skill(skill_id)
            if skill:
                skill['hotkey'] = hotkey
        
        cooldown_overrides = profile_data.get('cooldown_overrides', {})
        for skill_id, cooldown in cooldown_overrides.items():
            skill = self.skill_manager.get_skill(skill_id)
            if skill:
                skill['cooldown'] = cooldown
        
        self.skill_permanent = profile_data.get('permanent', {}).copy()
        self.skill_loop = profile_data.get('loop', {}).copy()
        self.skill_alert_enabled = profile_data.get('alert_enabled', {}).copy()
        
        for skill_id in self.skill_manager.get_all_skills():
            self.skill_permanent.setdefault(skill_id, False)
            self.skill_loop.setdefault(skill_id, False)
            self.skill_alert_enabled.setdefault(skill_id, False)
        
        self._save_config()
        self._reload_main_ui()
    
    def _reload_main_ui(self):
        """重新載入主 UI"""
        for widget in self.root.winfo_children():
            widget.destroy()
        
        self.permanent_vars = {}
        self.loop_vars = {}
        self.alert_enabled_vars = {}
        self.hotkey_buttons = {}
        self.cooldown_buttons = {}
        
        self._create_ui()
        self._initialize_permanent_skills()
    
    # ==================== 快捷鍵操作 ====================
    
    def _clear_all_hotkeys(self):
        """清空所有快捷鍵和秒數覆寫"""
        if messagebox.askyesno("確認", "確定要清空所有技能的快捷鍵和自訂秒數嗎?\n（會恢復預設秒數）", parent=self.root):
            for skill_id, skill in self.skill_manager.get_all_skills().items():
                skill['hotkey'] = ''
                
                original_cooldown = self._get_original_cooldown(skill_id)
                if original_cooldown:
                    skill['cooldown'] = original_cooldown
                
                if skill_id in self.hotkey_buttons:
                    btn = self.hotkey_buttons[skill_id]
                    btn.update_text('未設定')
                    btn.update_color(Colors.BG_MEDIUM, Colors.TEXT_SECONDARY)
                
                if skill_id in self.cooldown_buttons:
                    btn = self.cooldown_buttons[skill_id]
                    btn.update_text(f'{original_cooldown}秒')
                    btn.update_color(Colors.BG_MEDIUM, Colors.TEXT_PRIMARY)
            
            self._auto_save_current_profile()
            messagebox.showinfo("完成", "已清空所有快捷鍵並恢復預設秒數!", parent=self.root)
    
    def _start_hotkey_capture(self, skill_id):
        """開始捕捉快捷鍵"""
        skill = self.skill_manager.get_skill(skill_id)
        if not skill:
            return
        
        self.waiting_for_hotkey = skill_id
        self.waiting_skill_name = skill['name']
        self.keyboard_enabled = False
        
        self.hotkey_hint_label.config(
            text=f"⌨️ 請按下 '{self.waiting_skill_name}' 的快捷鍵...",
            fg=Colors.ACCENT_YELLOW
        )
    
    def _capture_hotkey(self, key):
        """捕捉按鍵並設定"""
        if self.waiting_for_hotkey is None:
            return
        
        try:
            key_name = key.name if hasattr(key, 'name') else str(key.char)
            key_str = key_name.upper()
            
            for sid, skill in self.skill_manager.get_all_skills().items():
                if skill.get('hotkey') == key_str and sid != self.waiting_for_hotkey:
                    skill['hotkey'] = ''
                    if sid in self.hotkey_buttons:
                        btn = self.hotkey_buttons[sid]
                        btn.update_text('未設定')
                        btn.update_color(Colors.BG_MEDIUM, Colors.TEXT_SECONDARY)
            
            skill = self.skill_manager.get_skill(self.waiting_for_hotkey)
            skill['hotkey'] = key_str
            
            if self.waiting_for_hotkey in self.hotkey_buttons:
                btn = self.hotkey_buttons[self.waiting_for_hotkey]
                btn.update_text(key_str)
                btn.update_color(Colors.ACCENT_YELLOW, '#000000')
            
            self._auto_save_current_profile()
            
            self.hotkey_hint_label.config(
                text=f"✓ '{self.waiting_skill_name}' 設定為 {key_str}",
                fg=Colors.ACCENT_GREEN
            )
            
            self.root.after(2000, self._clear_hotkey_hint)
            
            self.waiting_for_hotkey = None
            self.waiting_skill_name = None
            self.keyboard_enabled = True
            
        except Exception as e:
            self.hotkey_hint_label.config(
                text=f"✗ 設定失敗: {e}",
                fg=Colors.ACCENT_RED
            )
            self.root.after(3000, self._clear_hotkey_hint)
            self.waiting_for_hotkey = None
            self.waiting_skill_name = None
            self.keyboard_enabled = True
    
    def _clear_hotkey_hint(self):
        """清除快捷鍵提示"""
        self.hotkey_hint_label.config(text="")
    
    # ==================== 技能設定 ====================
    
    def _toggle_all(self, setting_type):
        """切換所有技能的設定"""
        if setting_type == 'permanent':
            all_checked = all(self.skill_permanent.get(sid, False) 
                             for sid in self.skill_manager.get_all_skills().keys())
            new_value = not all_checked
            
            # 🔧 如果要全選常駐，先取消所有循環
            if new_value:
                for skill_id in self.skill_manager.get_all_skills().keys():
                    if self.skill_loop.get(skill_id, False):
                        self._update_loop_skill(skill_id, False)
                        self.skill_loop[skill_id] = False
                        if skill_id in self.loop_vars:
                            self.loop_vars[skill_id].set(False)
            
            for skill_id in self.skill_manager.get_all_skills().keys():
                self._update_permanent_skill(skill_id, new_value)
                self.skill_permanent[skill_id] = new_value
                if skill_id in self.permanent_vars:
                    self.permanent_vars[skill_id].set(new_value)
        
        elif setting_type == 'loop':
            all_checked = all(self.skill_loop.get(sid, False) 
                             for sid in self.skill_manager.get_all_skills().keys())
            new_value = not all_checked
            
            # 🔧 如果要全選循環，先取消所有常駐
            if new_value:
                for skill_id in self.skill_manager.get_all_skills().keys():
                    if self.skill_permanent.get(skill_id, False):
                        self._update_permanent_skill(skill_id, False)
                        self.skill_permanent[skill_id] = False
                        if skill_id in self.permanent_vars:
                            self.permanent_vars[skill_id].set(False)
            
            for skill_id in self.skill_manager.get_all_skills().keys():
                self._update_loop_skill(skill_id, new_value)
                self.skill_loop[skill_id] = new_value
                if skill_id in self.loop_vars:
                    self.loop_vars[skill_id].set(new_value)
        
        elif setting_type == 'alert':
            all_checked = all(self.skill_alert_enabled.get(sid, False) 
                             for sid in self.skill_manager.get_all_skills().keys())
            new_value = not all_checked
            
            for skill_id in self.skill_manager.get_all_skills().keys():
                self.skill_alert_enabled[skill_id] = new_value
                if skill_id in self.alert_enabled_vars:
                    self.alert_enabled_vars[skill_id].set(new_value)
        
        self._save_config()
        self._auto_save_current_profile()
    
    def _update_skill_setting_exclusive(self, skill_id, setting_type, var):
        new_value = var.get()
    
        if new_value:
            if setting_type == 'permanent':
                if self.skill_loop.get(skill_id, False):
                    self.skill_loop[skill_id] = False
                    if skill_id in self.loop_vars:
                        self.loop_vars[skill_id].set(False)
                    if skill_id in self.active_windows:
                        self.active_windows[skill_id].close()
    
                self.skill_permanent[skill_id] = True
    
                if skill_id not in self.active_windows:
                    self._create_permanent_window(skill_id)
    
            elif setting_type == 'loop':
                if self.skill_permanent.get(skill_id, False):
                    self.skill_permanent[skill_id] = False
                    if skill_id in self.permanent_vars:
                        self.permanent_vars[skill_id].set(False)
                    if skill_id in self.active_windows:
                        self.active_windows[skill_id].close()
    
                self.skill_loop[skill_id] = True
    
                if skill_id not in self.active_windows:
                    self._create_loop_window(skill_id)
    
        else:
            if skill_id in self.active_windows:
                self.active_windows[skill_id].close()
    
            if setting_type == 'permanent':
                self.skill_permanent[skill_id] = False
            elif setting_type == 'loop':
                self.skill_loop[skill_id] = False
        
        # 🆕 更新預覽框大小
        
        self._save_config()
        self._auto_save_current_profile()
    
    def _update_alert_setting(self, skill_id, var):
        """更新提前提示設定"""
        new_value = var.get()
        self.skill_alert_enabled[skill_id] = new_value
        
        if skill_id in self.active_windows:
            self.active_windows[skill_id].alert_enabled = new_value
            self.active_windows[skill_id].alert_before_seconds = self.alert_before_seconds
        
        self._save_config()
        self._auto_save_current_profile()
    
    def _update_permanent_skill(self, skill_id, is_permanent):
        """更新駐留技能"""
        was_permanent = self.skill_permanent.get(skill_id, False)
        if is_permanent and not was_permanent:
            if skill_id not in self.active_windows:
                self._create_permanent_window(skill_id)
        elif not is_permanent and was_permanent:
            if skill_id in self.active_windows:
                self.active_windows[skill_id].close()
    
    def _update_loop_skill(self, skill_id, is_loop):
        """更新循環技能"""
        was_loop = self.skill_loop.get(skill_id, False)
        if is_loop and not was_loop:
            if skill_id not in self.active_windows:
                self._create_loop_window(skill_id)
        elif not is_loop and was_loop:
            if skill_id in self.active_windows:
                self.active_windows[skill_id].close()
    
    def _initialize_permanent_skills(self):
        """初始化駐留技能和循環技能"""
        for skill_id, is_permanent in self.skill_permanent.items():
            if is_permanent and skill_id not in self.active_windows:
                self._create_permanent_window(skill_id)
        
        for skill_id, is_loop in self.skill_loop.items():
            if is_loop and skill_id not in self.active_windows:
                self._create_loop_window(skill_id)
        
        # 🆕 初始化後更新預覽框大小
    
    def _create_permanent_window(self, skill_id):
        """創建駐留視窗"""
        skill = self.skill_manager.get_skill(skill_id)
        if not skill:
            return
        
        if skill_id not in self.window_order:
            self.window_order.append(skill_id)
        
        position = self._calculate_position(skill_id)
        skill_image = self.skill_manager.skill_images.get(skill_id)
        skill_image_path = self.skill_manager.skill_image_paths.get(skill_id)  # 🆕 獲取圖片路徑
        alert_enabled = self.skill_alert_enabled.get(skill_id, False)
        
        skill_window = SkillWindow(
            skill, self.player_name, position, skill_image,
            lambda w: self._on_window_close(w, skill_id),
            self.enable_sound, skill_id, is_permanent=True, is_loop=False,
            start_at_zero=True,
            window_alpha=self.window_alpha,
            alert_enabled=alert_enabled,
            alert_before_seconds=self.alert_before_seconds,
            on_drag_start=self._on_skill_drag_start,
            on_drag_motion=self._on_skill_drag_motion,
            on_drag_end=self._on_skill_drag_end,
            window_size=self.window_size,  # 🆕 傳遞視窗大小
            skill_image_path=skill_image_path  # 🆕 傳遞圖片路徑
        )
        self.active_windows[skill_id] = skill_window
    
    def _create_loop_window(self, skill_id):
        """創建循環視窗"""
        skill = self.skill_manager.get_skill(skill_id)
        if not skill:
            return
        
        if skill_id not in self.window_order:
            self.window_order.append(skill_id)
        
        position = self._calculate_position(skill_id)
        skill_image = self.skill_manager.skill_images.get(skill_id)
        skill_image_path = self.skill_manager.skill_image_paths.get(skill_id)  # 🆕 獲取圖片路徑
        alert_enabled = self.skill_alert_enabled.get(skill_id, False)
        
        skill_window = SkillWindow(
            skill, self.player_name, position, skill_image,
            lambda w: self._on_window_close(w, skill_id),
            self.enable_sound, skill_id, is_permanent=False, is_loop=True,
            start_at_zero=False,
            window_alpha=self.window_alpha,
            alert_enabled=alert_enabled,
            alert_before_seconds=self.alert_before_seconds,
            on_drag_start=self._on_skill_drag_start,
            on_drag_motion=self._on_skill_drag_motion,
            on_drag_end=self._on_skill_drag_end,
            window_size=self.window_size,  # 🆕 傳遞視窗大小
            skill_image_path=skill_image_path  # 🆕 傳遞圖片路徑
        )
        self.active_windows[skill_id] = skill_window
    
    # ==================== 其他功能 ====================
    
    def _check_for_updates(self):
        """檢查更新（非阻塞）"""
        from src.ui.updater import Updater
        
        try:
            updater = Updater()
            update_info = updater.check_for_updates()
            
            if update_info.get('available'):
                self.update_button.pack(side=tk.LEFT, padx=3)
                self.update_info = update_info
                print(f"🎉 發現新版本: {update_info['latest']} (當前: {update_info['current']})")
            else:
                print(f"✅ 已是最新版本: {update_info['current']}")
        except Exception as e:
            print(f"⚠️ 檢查更新時發生錯誤: {e}")
    
    def _show_update_dialog(self):
        """顯示更新對話框"""
        if not hasattr(self, 'update_info'):
            return
        
        from tkinter import messagebox
        import webbrowser
        
        message = f"""發現新版本！

當前版本: {self.update_info['current']}
最新版本: {self.update_info['latest']}

是否前往下載頁面？"""
        
        if messagebox.askyesno("更新可用", message, parent=self.root):
            download_url = self.update_info.get('download_url')
            if download_url:
                webbrowser.open(download_url)
            else:
                webbrowser.open("https://github.com/asd23353934/skill_tracker/releases/latest")
    
    def _edit_cooldown(self, skill_id):
        """編輯技能冷卻時間"""
        skill = self.skill_manager.get_skill(skill_id)
        if not skill:
            return
        
        self.keyboard_enabled = False
        
        original_cooldown = self._get_original_cooldown(skill_id)
        
        new_cooldown = simpledialog.askinteger(
            "修改冷卻時間",
            f"請輸入 {skill['name']} 的新冷卻時間（秒）:\n(原始值: {original_cooldown}秒)",
            initialvalue=skill['cooldown'],
            minvalue=1,
            maxvalue=999,
            parent=self.root
        )
        
        self.keyboard_enabled = True
        
        if new_cooldown is not None and new_cooldown != skill['cooldown']:
            skill['cooldown'] = new_cooldown
            
            if skill_id in self.cooldown_buttons:
                btn = self.cooldown_buttons[skill_id]
                btn.update_text(f"{new_cooldown}秒")
                
                is_modified = original_cooldown and new_cooldown != original_cooldown
                if is_modified:
                    btn.update_color(Colors.ACCENT_BLUE, '#FFFFFF')
                else:
                    btn.update_color(Colors.BG_MEDIUM, Colors.TEXT_SECONDARY)
            
            self._auto_save_current_profile()
            
            status = "修改" if original_cooldown != new_cooldown else "恢復預設"
            print(f"✅ 已將 {skill['name']} 的冷卻時間{status}為 {new_cooldown}秒")
    
    def _reset_cooldown(self, skill_id):
        """重置技能冷卻時間為預設值"""
        skill = self.skill_manager.get_skill(skill_id)
        if not skill:
            return
        
        original_cooldown = self._get_original_cooldown(skill_id)
        if not original_cooldown:
            return
        
        if skill['cooldown'] == original_cooldown:
            print(f"ℹ️ {skill['name']} 已經是預設秒數")
            return
        
        skill['cooldown'] = original_cooldown
        
        if skill_id in self.cooldown_buttons:
            btn = self.cooldown_buttons[skill_id]
            btn.update_text(f"{original_cooldown}秒")
            btn.update_color(Colors.BG_MEDIUM, Colors.TEXT_PRIMARY)
        
        self._auto_save_current_profile()
        
        print(f"✅ 已將 {skill['name']} 的冷卻時間重置為預設值 {original_cooldown}秒")
    
    def _reset_hotkey(self, skill_id):
        """重置技能快捷鍵"""
        skill = self.skill_manager.get_skill(skill_id)
        if not skill:
            return
        
        if not skill.get('hotkey'):
            print(f"ℹ️ {skill['name']} 沒有設定快捷鍵")
            return
        
        skill['hotkey'] = ''
        
        if skill_id in self.hotkey_buttons:
            btn = self.hotkey_buttons[skill_id]
            btn.update_text('未設定')
            btn.update_color(Colors.BG_MEDIUM, Colors.TEXT_SECONDARY)
        
        self._auto_save_current_profile()
        
        print(f"✅ 已清空 {skill['name']} 的快捷鍵")
    
    def _show_settings(self):
        """顯示設定對話框"""
        self.keyboard_enabled = False
        
        dialog = SettingsDialog(self.root, {
            'x': self.skill_start_x,
            'y': self.skill_start_y,
            'sound': self.enable_sound,
            'alert_before_seconds': self.alert_before_seconds,
            'window_size': self.window_size  # 🆕 傳遞視窗大小
        })
        
        result = dialog.show()
        
        if result:
            old_x = self.skill_start_x
            old_y = self.skill_start_y
            old_alert_seconds = self.alert_before_seconds
            old_window_size = self.window_size  # 🆕
            
            self.skill_start_x = result['x']
            self.skill_start_y = result['y']
            self.enable_sound = result['sound']
            self.alert_before_seconds = result['alert_before_seconds']
            self.window_size = result['window_size']  # 🆕
            
            self.config_manager.set_settings('skill_start_x', self.skill_start_x)
            self.config_manager.set_settings('skill_start_y', self.skill_start_y)
            self.config_manager.set_settings('enable_sound', self.enable_sound)
            self.config_manager.set_settings('alert_before_seconds', self.alert_before_seconds)
            self.config_manager.set_settings('window_size', self.window_size)  # 🆕
            self.config_manager.save()
            
            for window in self.active_windows.values():
                window.enable_sound = self.enable_sound
                window.alert_before_seconds = self.alert_before_seconds
            
            if old_x != self.skill_start_x or old_y != self.skill_start_y:
                self._reposition_windows()
                print(f"✅ 位置已更新：({old_x}, {old_y}) → ({self.skill_start_x}, {self.skill_start_y})")
            
            if old_alert_seconds != self.alert_before_seconds:
                print(f"✅ 提前提示秒數已更新：{old_alert_seconds} → {self.alert_before_seconds}秒")
            
            if old_window_size != self.window_size:  # 🆕
                print(f"✅ 視窗大小已更新：{old_window_size}px → {self.window_size}px")
                print("⚠️ 視窗大小變更將在下次觸發技能時生效")
            
            print(f"✅ 設定已套用")
            messagebox.showinfo("設定已套用", "設定已成功保存並套用！\n視窗大小將在下次觸發技能時生效。", parent=self.root)
        
        self.keyboard_enabled = True
    
    def _trigger_skill(self, skill_id, player_name=None):
        """觸發技能"""
        skill = self.skill_manager.get_skill(skill_id)
        if not skill:
            return
        
        player = player_name or self.player_name
        
        if skill_id in self.active_windows:
            is_permanent = self.skill_permanent.get(skill_id, False)
            is_loop = self.skill_loop.get(skill_id, False)
            if is_permanent or is_loop:
                self.active_windows[skill_id].restart_countdown()
            else:
                self.active_windows[skill_id].close()
            return
        
        if skill_id not in self.window_order:
            self.window_order.append(skill_id)
        
        position = self._calculate_position(skill_id)
        is_permanent = self.skill_permanent.get(skill_id, False)
        is_loop = self.skill_loop.get(skill_id, False)
        skill_image = self.skill_manager.skill_images.get(skill_id)
        skill_image_path = self.skill_manager.skill_image_paths.get(skill_id)  # 🆕 獲取圖片路徑
        alert_enabled = self.skill_alert_enabled.get(skill_id, False)
        
        skill_window = SkillWindow(
            skill, player, position, skill_image,
            lambda w: self._on_window_close(w, skill_id),
            self.enable_sound, skill_id, 
            is_permanent=is_permanent,
            is_loop=is_loop,
            window_alpha=self.window_alpha,
            alert_enabled=alert_enabled,
            alert_before_seconds=self.alert_before_seconds,
            on_drag_start=self._on_skill_drag_start,
            on_drag_motion=self._on_skill_drag_motion,
            on_drag_end=self._on_skill_drag_end,
            window_size=self.window_size,  # 🆕 傳遞視窗大小
            skill_image_path=skill_image_path  # 🆕 傳遞圖片路徑
        )
        self.active_windows[skill_id] = skill_window
    
    def _calculate_position(self, skill_id):
        """計算技能視窗位置（從右往左、從上往下）"""
        index = self.window_order.index(skill_id)

        col = index % self.MAX_PER_ROW
        row = index // self.MAX_PER_ROW

        # 🆕 使用動態視窗大小計算位置
        # 從 skill_start_x, skill_start_y 開始，向左和向下排列
        x = self.skill_start_x - col * (self.window_size + self.H_GAP)
        y = self.skill_start_y - row * (self.window_size + self.V_GAP)

        return (x, y)

    def _reposition_windows(self):
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
    
        self._reposition_windows()
        
        # 🆕 更新預覽框大小
    
    def _on_key_press(self, key):
        """按鍵處理"""
        if self.waiting_for_hotkey is not None:
            self._capture_hotkey(key)
            return
        
        if not self.keyboard_enabled:
            return
        
        try:
            key_name = key.name if hasattr(key, 'name') else str(key.char)
            skill_id = self.skill_manager.get_skill_by_hotkey(key_name)
            if skill_id:
                self.root.after(0, self._trigger_skill, skill_id)
        except:
            pass
    
    def _start_keyboard_listener(self):
        """啟動鍵盤監聽"""
        listener = keyboard.Listener(on_press=self._on_key_press)
        listener.daemon = True
        listener.start()
    
    def _save_config(self):
        """保存配置"""
        self.config_manager.set_settings('skill_permanent', self.skill_permanent)
        self.config_manager.save()
    
    def run(self):
        """運行應用程式"""
        self.root.mainloop()
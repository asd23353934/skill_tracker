"""
主視窗模組 - 完整正式版
三欄佈局：房間管理 | 玩家技能 | BOSS 技能
"""

import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
from pynput import keyboard
import time

from src.ui.components import RoundedButton, SectionFrame, ScrollableFrame
from src.ui.dialogs import ProfileManagerDialog, SettingsDialog, JoinRoomDialog
from src.ui.skill_window import SkillWindow
from src.core.config_manager import ConfigManager
from src.core.network_manager import NetworkManager
from src.core.skill_manager import SkillManager
from src.utils.styles import Colors, Fonts, Sizes
from src.utils.helpers import resource_path


class MainWindow:
    """主視窗類別"""
    
    def __init__(self):
        """初始化主視窗"""
        # 獲取版本號
        try:
            from version import VERSION
            version_str = f" v{VERSION}"
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
            self.network = NetworkManager(
                self._on_network_skill, 
                self._on_members_update
            )
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
        
        # 設定
        self.player_name = settings.get('player_name', '玩家1')
        self.skill_start_x = settings.get('skill_start_x', 1700)
        self.skill_start_y = settings.get('skill_start_y', 850)
        self.enable_sound = settings.get('enable_sound', True)
        
        # 技能設定 - 從配置檔案載入
        if profile_data:
            self.skill_send = profile_data.get('send', {})
            self.skill_receive = profile_data.get('receive', {})
            self.skill_permanent = profile_data.get('permanent', {})
            
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
            self.skill_send = {}
            self.skill_receive = {}
            self.skill_permanent = {}
        
        # 初始化所有技能的預設值
        for skill_id in self.skill_manager.get_all_skills():
            self.skill_send.setdefault(skill_id, True)
            self.skill_receive.setdefault(skill_id, True)
            self.skill_permanent.setdefault(skill_id, False)
        
        # UI 控制
        self.keyboard_enabled = True
        self.waiting_for_hotkey = None
        self.waiting_skill_name = None
        
        # UI 元件字典
        self.send_vars = {}
        self.receive_vars = {}
        self.permanent_vars = {}
        self.hotkey_buttons = {}
        self.cooldown_buttons = {}  # 秒數按鈕字典
    
    # ==================== UI 創建 ====================
    
    def _create_ui(self):
        """創建主要 UI"""
        # 頂部標題列
        self._create_header()
        
        # 主內容區 - 四欄佈局
        main_container = tk.Frame(self.root, bg=Colors.BG_DARK)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 第一欄：房間管理
        col1 = tk.Frame(main_container, bg=Colors.BG_DARK)
        col1.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        self._create_room_column(col1)
        
        # 第二欄：玩家技能
        col2 = tk.Frame(main_container, bg=Colors.BG_DARK)
        col2.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        self._create_player_skills_column(col2)
        
        # 第三欄：BOSS 技能
        col3 = tk.Frame(main_container, bg=Colors.BG_DARK)
        col3.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        self._create_boss_skills_column(col3)
        
        # 第四欄：道具
        col4 = tk.Frame(main_container, bg=Colors.BG_DARK)
        col4.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        self._create_items_column(col4)
    
    def _create_header(self):
        """創建頂部標題列"""
        # 使用圓角框架
        from src.ui.components import RoundedFrame
        
        header_frame = RoundedFrame(
            self.root, radius=12, bg=Colors.BG_MEDIUM,
            border_color=Colors.ACCENT_YELLOW, border_width=3,
            fixed_height=True  # 只有 header 需要固定高度
        )
        header_frame.pack(fill=tk.X, side=tk.TOP, padx=10, pady=(10, 5))
        header_frame.configure(height=70)
        
        header = header_frame.get_content()
        
        # 左側標題 - 恢復原始大小
        tk.Label(
            header, text="🎮 技能追蹤器", 
            bg=Colors.BG_MEDIUM, fg=Colors.ACCENT_YELLOW,
            font=Fonts.TITLE_LARGE  # 恢復原始字體
        ).pack(side=tk.LEFT, padx=20, pady=15)
        
        tk.Label(
            header, text="Artale 楓之谷", 
            bg=Colors.BG_MEDIUM, fg=Colors.TEXT_SECONDARY,
            font=Fonts.BODY_MEDIUM  # 恢復原始字體
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
        # 初始不顯示
        
        # 清空按鍵按鈕
        RoundedButton(
            right_buttons, "🗑️ 清空按鍵", self._clear_all_hotkeys,
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
            quick_btns, "發", lambda: self._toggle_all('send'),
            Colors.ACCENT_GREEN, width=40, height=25
        ).pack(side=tk.LEFT, padx=1)
        
        RoundedButton(
            quick_btns, "收", lambda: self._toggle_all('receive'),
            Colors.ACCENT_BLUE, width=40, height=25
        ).pack(side=tk.LEFT, padx=1)
        
        RoundedButton(
            quick_btns, "駐", lambda: self._toggle_all('permanent'),
            Colors.ACCENT_YELLOW, width=40, height=25
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
    
    def _create_room_column(self, parent):
        """創建房間管理欄"""
        # 標題
        self._create_column_title(parent, "🏠 房間管理")
        
        content = tk.Frame(parent, bg=Colors.BG_DARK)
        content.pack(fill=tk.BOTH, expand=True)
        
        # 房間狀態
        status_frame = SectionFrame(content, "房間狀態")
        status_frame.pack(fill=tk.X, pady=5)
        
        status_content = status_frame.get_content()
        
        self.room_info_label = tk.Label(
            status_content, text="● 未連線",
            bg=Colors.BG_LIGHT, fg=Colors.TEXT_SECONDARY,
            font=Fonts.BODY_MEDIUM
        )
        self.room_info_label.pack(pady=15)
        
        # 按鈕組
        btn_frame = tk.Frame(status_content, bg=Colors.BG_LIGHT)
        btn_frame.pack(pady=10, padx=10, fill=tk.X)
        
        self.create_btn = tk.Button(
            btn_frame, text="創建房間", command=self._create_room,
            bg=Colors.ACCENT_BLUE, fg='white',
            font=Fonts.BUTTON, relief=tk.FLAT, cursor='hand2',
            activebackground=Colors.BG_DARK
        )
        self.create_btn.pack(fill=tk.X, pady=3)
        
        self.join_btn = tk.Button(
            btn_frame, text="加入房間", command=self._join_room,
            bg=Colors.ACCENT_PURPLE, fg='white',
            font=Fonts.BUTTON, relief=tk.FLAT, cursor='hand2',
            activebackground=Colors.BG_DARK
        )
        self.join_btn.pack(fill=tk.X, pady=3)
        
        self.leave_btn = tk.Button(
            btn_frame, text="退出房間", command=self._leave_room,
            bg=Colors.ACCENT_RED, fg='white',
            font=Fonts.BUTTON, relief=tk.FLAT, cursor='hand2',
            state=tk.DISABLED, activebackground=Colors.BG_DARK
        )
        self.leave_btn.pack(fill=tk.X, pady=3)
        
        # 玩家資訊
        player_frame = tk.Frame(status_content, bg=Colors.BG_LIGHT)
        player_frame.pack(pady=10, fill=tk.X)
        
        self.player_label = tk.Label(
            player_frame, text=f"👤 玩家: {self.player_name}",
            bg=Colors.BG_LIGHT, fg=Colors.ACCENT_GREEN,
            font=Fonts.BODY_MEDIUM_BOLD
        )
        self.player_label.pack(side=tk.LEFT, padx=15)
        
        tk.Button(
            player_frame, text="✏️ 修改", command=self._change_player_name,
            bg=Colors.BG_MEDIUM, fg=Colors.TEXT_PRIMARY,
            font=Fonts.BODY_SMALL, relief=tk.FLAT, cursor='hand2',
            activebackground=Colors.BG_DARK
        ).pack(side=tk.RIGHT, padx=15)
        
        # 成員列表
        members_frame = SectionFrame(content, "房間成員")
        members_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        members_content = members_frame.get_content()
        
        self.members_list = tk.Listbox(
            members_content, bg=Colors.BG_DARK,
            fg=Colors.TEXT_PRIMARY,
            font=Fonts.BODY_SMALL, height=8,
            selectbackground=Colors.ACCENT_BLUE,
            relief=tk.FLAT, bd=0
        )
        self.members_list.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 提示
        from src.ui.components import RoundedFrame
        
        tip_wrapper = RoundedFrame(
            content, radius=8, bg=Colors.BG_MEDIUM,
            border_color=Colors.ACCENT_GREEN, border_width=2
        )
        tip_wrapper.pack(fill=tk.X, pady=10, padx=5)
        
        tip_frame = tip_wrapper.get_content()
        
        tk.Label(
            tip_frame,
            text="💡 提示:\n• 再次按快捷鍵可關閉倒數\n• 點擊快捷鍵按鈕可重新設定\n• 配置管理可儲存多種場景",
            bg=Colors.BG_MEDIUM, fg=Colors.TEXT_SECONDARY,
            font=Fonts.BODY_SMALL, justify=tk.LEFT
        ).pack(padx=15, pady=10)
    
    def _create_player_skills_column(self, parent):
        """創建玩家技能欄"""
        # 標題
        self._create_column_title(parent, "⚔️ 玩家技能")
        
        # 滾動區域
        self.player_scroll_frame = ScrollableFrame(parent)
        self.player_scroll_frame.pack(fill=tk.BOTH, expand=True)
        
        content = self.player_scroll_frame.get_content()
        
        # 顯示玩家技能
        if 'player' in self.skill_manager.skill_categories:
            for subcategory, skill_ids in sorted(self.skill_manager.get_categories('player').items()):
                group = self._create_skill_group(content, subcategory, skill_ids)
                # 綁定新創建的組件到滾輪
                if group:
                    self.player_scroll_frame.bind_widget_to_scroll(group)
    
    def _create_boss_skills_column(self, parent):
        """創建 BOSS 技能欄"""
        # 標題
        self._create_column_title(parent, "👹 BOSS 技能")
        
        # 滾動區域
        self.boss_scroll_frame = ScrollableFrame(parent)
        self.boss_scroll_frame.pack(fill=tk.BOTH, expand=True)
        
        content = self.boss_scroll_frame.get_content()
        
        # 顯示 BOSS 技能
        if 'boss' in self.skill_manager.skill_categories:
            for subcategory, skill_ids in sorted(self.skill_manager.get_categories('boss').items()):
                group = self._create_skill_group(content, subcategory, skill_ids)
                # 綁定新創建的組件到滾輪
                if group:
                    self.boss_scroll_frame.bind_widget_to_scroll(group)
                # 綁定新創建的組件到滾輪
                if group:
                    self.boss_scroll_frame.bind_widget_to_scroll(group)
    
    def _create_items_column(self, parent):
        """創建道具欄"""
        # 標題
        self._create_column_title(parent, "🎁 道具")
        
        # 滾動區域
        self.items_scroll_frame = ScrollableFrame(parent)
        self.items_scroll_frame.pack(fill=tk.BOTH, expand=True)
        
        content = self.items_scroll_frame.get_content()
        
        # 顯示道具
        if 'item' in self.skill_manager.skill_categories:
            for subcategory, item_ids in sorted(self.skill_manager.get_categories('item').items()):
                group = self._create_skill_group(content, subcategory, item_ids)
                # 綁定新創建的組件到滾輪
                if group:
                    self.items_scroll_frame.bind_widget_to_scroll(group)
        
        # 提示
        from src.ui.components import RoundedFrame
        
        tip_wrapper = RoundedFrame(
            content, radius=8, bg=Colors.BG_MEDIUM,
            border_color=Colors.ACCENT_GREEN, border_width=2
        )
    
    def _create_column_title(self, parent, text):
        """創建欄位標題"""
        from src.ui.components import RoundedFrame
        
        title_frame_wrapper = RoundedFrame(
            parent, radius=10, bg=Colors.BG_MEDIUM,
            border_color=Colors.ACCENT_BLUE, border_width=2
        )
        title_frame_wrapper.pack(fill=tk.X, pady=(0, 5))
        # 移除固定高度，讓它自動調整
        
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
        
        # 秒數按鈕 - 可點擊編輯
        original_cooldown = self._get_original_cooldown(skill_id)
        is_modified = original_cooldown and skill['cooldown'] != original_cooldown
        
        cooldown_btn = RoundedButton(
            bottom_info, f"{skill['cooldown']}秒",
            lambda sid=skill_id: self._edit_cooldown(sid),
            Colors.ACCENT_BLUE if is_modified else Colors.BG_MEDIUM,
            fg_color='#FFFFFF' if is_modified else Colors.TEXT_SECONDARY,
            width=60, height=20
        )
        cooldown_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # 記錄秒數按鈕（用於更新顯示）
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
        hotkey_btn.pack(side=tk.LEFT)
        self.hotkey_buttons[skill_id] = hotkey_btn
        
        # 右側：選項
        options_frame = tk.Frame(item_frame, bg=Colors.BG_DARK)
        options_frame.pack(side=tk.RIGHT, padx=5)
        
        self._create_skill_checkboxes(options_frame, skill_id)
    
    def _create_skill_checkboxes(self, parent, skill_id):
        """創建技能選項"""
        checkboxes = [
            ('send', '發', Colors.ACCENT_GREEN, self.skill_send, self.send_vars),
            ('receive', '收', Colors.ACCENT_BLUE, self.skill_receive, self.receive_vars),
            ('permanent', '駐', Colors.ACCENT_YELLOW, self.skill_permanent, self.permanent_vars)
        ]
        
        for setting_type, text, color, settings_dict, vars_dict in checkboxes:
            var = tk.BooleanVar(value=settings_dict.get(skill_id, True))
            vars_dict[skill_id] = var
            
            cb = tk.Checkbutton(
                parent, text=text, variable=var,
                command=lambda sid=skill_id, t=setting_type, v=var:
                    self._update_skill_setting(sid, t, v),
                bg=Colors.BG_DARK, fg=color,
                font=Fonts.BODY_SMALL,
                selectcolor=Colors.BG_MEDIUM,
                activebackground=Colors.BG_DARK
            )
            cb.pack(side=tk.LEFT, padx=2)
    
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
            self  # 傳遞主視窗實例
        )
        
        result = dialog.show()
        
        if result:
            # 套用配置
            self._apply_profile(result)
        
        self.keyboard_enabled = True
    
    def _get_current_settings(self):
        """獲取當前設定"""
        # 獲取秒數覆寫（只保存修改過的）
        cooldown_overrides = {}
        for skill_id, skill in self.skill_manager.get_all_skills().items():
            # 獲取原始秒數
            original_cooldown = self._get_original_cooldown(skill_id)
            
            # 如果當前秒數與原始秒數不同，記錄覆寫
            current_cooldown = skill.get('cooldown')
            if original_cooldown and current_cooldown != original_cooldown:
                cooldown_overrides[skill_id] = current_cooldown
        
        return {
            'hotkeys': {
                sid: skill.get('hotkey', '')
                for sid, skill in self.skill_manager.get_all_skills().items()
            },
            'send': self.skill_send.copy(),
            'receive': self.skill_receive.copy(),
            'permanent': self.skill_permanent.copy(),
            'cooldown_overrides': cooldown_overrides
        }
    
    def _get_original_cooldown(self, skill_id):
        """獲取技能的原始秒數
        
        Args:
            skill_id: 技能ID
            
        Returns:
            int: 原始秒數，如果找不到返回 None
        """
        # 從 initial_skills 中查找
        for skill_data in self.config_manager.initial_skills:
            if skill_data['id'] == skill_id:
                return skill_data.get('cooldown')
        
        # 從 initial_items 中查找
        for item_data in self.config_manager.initial_items:
            if item_data['id'] == skill_id:
                return item_data.get('cooldown')
        
        return None
    
    def _apply_profile(self, profile_data):
        """套用配置"""
        # 更新當前配置名稱
        self.current_profile_name = self.config_manager.get_current_profile()
        
        # 先恢復所有技能的原始秒數和清空快捷鍵
        for skill_id, skill in self.skill_manager.get_all_skills().items():
            # 恢復原始秒數
            original_cooldown = self._get_original_cooldown(skill_id)
            if original_cooldown:
                skill['cooldown'] = original_cooldown
            skill['hotkey'] = ''
        
        # 更新快捷鍵（只更新記憶體）
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
        
        # 更新設定
        self.skill_send = profile_data.get('send', {}).copy()
        self.skill_receive = profile_data.get('receive', {}).copy()
        self.skill_permanent = profile_data.get('permanent', {}).copy()
        
        # 確保所有技能都有預設值
        for skill_id in self.skill_manager.get_all_skills():
            self.skill_send.setdefault(skill_id, True)
            self.skill_receive.setdefault(skill_id, True)
            self.skill_permanent.setdefault(skill_id, False)
        
        self._save_config()
        
        # 重新載入 UI
        self._reload_main_ui()
    
    def _reload_main_ui(self):
        """重新載入主 UI"""
        # 銷毀主視窗內容並重建
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # 重新初始化變數
        self.send_vars = {}
        self.receive_vars = {}
        self.permanent_vars = {}
        self.hotkey_buttons = {}
        self.cooldown_buttons = {}  # 重置秒數按鈕
        
        # 重建 UI
        self._create_ui()
        self._initialize_permanent_skills()
    
    # ==================== 快捷鍵操作 ====================
    
    def _clear_all_hotkeys(self):
        """清空所有快捷鍵"""
        if messagebox.askyesno("確認", "確定要清空所有技能的快捷鍵設定嗎?", parent=self.root):
            for skill_id, skill in self.skill_manager.get_all_skills().items():
                # 只清空記憶體中的快捷鍵
                skill['hotkey'] = ''
                
                # 更新按鈕顯示
                if skill_id in self.hotkey_buttons:
                    btn = self.hotkey_buttons[skill_id]
                    btn.update_text('未設定')
                    btn.update_color(Colors.BG_MEDIUM, Colors.TEXT_SECONDARY)
            
            # 自動保存當前配置（會清空 hotkeys）
            self._auto_save_current_profile()
            messagebox.showinfo("完成", "已清空所有快捷鍵!", parent=self.root)
    
    def _start_hotkey_capture(self, skill_id):
        """開始捕捉快捷鍵"""
        skill = self.skill_manager.get_skill(skill_id)
        if not skill:
            return
        
        self.waiting_for_hotkey = skill_id
        self.waiting_skill_name = skill['name']
        self.keyboard_enabled = False
        
        # 顯示提示
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
            
            # 檢查並清除其他技能的相同按鍵（只修改記憶體）
            for sid, skill in self.skill_manager.get_all_skills().items():
                if skill.get('hotkey') == key_str and sid != self.waiting_for_hotkey:
                    skill['hotkey'] = ''
                    # 更新按鈕顯示
                    if sid in self.hotkey_buttons:
                        btn = self.hotkey_buttons[sid]
                        btn.update_text('未設定')
                        btn.update_color(Colors.BG_MEDIUM, Colors.TEXT_SECONDARY)
            
            # 設定新快捷鍵（只修改記憶體）
            skill = self.skill_manager.get_skill(self.waiting_for_hotkey)
            skill['hotkey'] = key_str
            
            # 更新按鈕顯示
            if self.waiting_for_hotkey in self.hotkey_buttons:
                btn = self.hotkey_buttons[self.waiting_for_hotkey]
                btn.update_text(key_str)
                btn.update_color(Colors.ACCENT_YELLOW, '#000000')  # 黃底黑字
            
            # 自動保存當前配置
            self._auto_save_current_profile()
            
            # 顯示成功訊息
            self.hotkey_hint_label.config(
                text=f"✓ '{self.waiting_skill_name}' 設定為 {key_str}",
                fg=Colors.ACCENT_GREEN
            )
            
            # 2秒後清除提示
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
        settings_map = {
            'send': (self.skill_send, self.send_vars),
            'receive': (self.skill_receive, self.receive_vars),
            'permanent': (self.skill_permanent, self.permanent_vars)
        }
        
        settings_dict, vars_dict = settings_map[setting_type]
        all_checked = all(settings_dict.get(sid, True) for sid in self.skill_manager.get_all_skills().keys())
        new_value = not all_checked
        
        for skill_id in self.skill_manager.get_all_skills().keys():
            if setting_type == 'permanent':
                self._update_permanent_skill(skill_id, new_value)
            settings_dict[skill_id] = new_value
            if skill_id in vars_dict:
                vars_dict[skill_id].set(new_value)
        
        self._save_config()
    
    def _update_skill_setting(self, skill_id, setting_type, var):
        """更新技能設定"""
        new_value = var.get()
        if setting_type == 'send':
            self.skill_send[skill_id] = new_value
        elif setting_type == 'receive':
            self.skill_receive[skill_id] = new_value
        elif setting_type == 'permanent':
            self._update_permanent_skill(skill_id, new_value)
            self.skill_permanent[skill_id] = new_value
        self._save_config()
        
        # 自動保存當前配置
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
    
    def _initialize_permanent_skills(self):
        """初始化駐留技能"""
        for skill_id, is_permanent in self.skill_permanent.items():
            if is_permanent and skill_id not in self.active_windows:
                self._create_permanent_window(skill_id)
    
    def _create_permanent_window(self, skill_id):
        """創建駐留視窗"""
        skill = self.skill_manager.get_skill(skill_id)
        if not skill:
            return
        
        if skill_id not in self.window_order:
            self.window_order.append(skill_id)
        
        position = self._calculate_position(skill_id)
        skill_image = self.skill_manager.skill_images.get(skill_id)
        
        skill_window = SkillWindow(
            skill, self.player_name, position, skill_image,
            lambda w: self._on_window_close(w, skill_id),
            self.enable_sound, skill_id, True, start_at_zero=True
        )
        self.active_windows[skill_id] = skill_window
    
    # ==================== 其他功能 ====================
    
    def _check_for_updates(self):
        """檢查更新（非阻塞）"""
        from src.core.updater import Updater
        
        try:
            updater = Updater()
            update_info = updater.check_for_updates()
            
            if update_info.get('available'):
                # 顯示更新按鈕
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
            # 打開下載頁面
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
        
        # 暫時禁用鍵盤輸入
        self.keyboard_enabled = False
        
        # 獲取原始秒數
        original_cooldown = self._get_original_cooldown(skill_id)
        
        # 顯示輸入對話框
        new_cooldown = simpledialog.askinteger(
            "修改冷卻時間",
            f"請輸入 {skill['name']} 的新冷卻時間（秒）:\n(原始值: {original_cooldown}秒)",
            initialvalue=skill['cooldown'],
            minvalue=1,
            maxvalue=999,
            parent=self.root
        )
        
        # 恢復鍵盤輸入
        self.keyboard_enabled = True
        
        # 如果用戶輸入了新值
        if new_cooldown is not None and new_cooldown != skill['cooldown']:
            # 只更新技能管理器中的數據（記憶體）
            skill['cooldown'] = new_cooldown
            
            # 更新按鈕顯示和顏色
            if skill_id in self.cooldown_buttons:
                btn = self.cooldown_buttons[skill_id]
                btn.update_text(f"{new_cooldown}秒")
                
                # 判斷是否被修改（與原始值比較）
                is_modified = original_cooldown and new_cooldown != original_cooldown
                if is_modified:
                    btn.update_color(Colors.ACCENT_BLUE, '#FFFFFF')  # 藍底白字
                else:
                    btn.update_color(Colors.BG_MEDIUM, Colors.TEXT_SECONDARY)  # 灰底灰字
            
            # 自動保存當前配置（會包含 cooldown_overrides）
            self._auto_save_current_profile()
            
            status = "修改" if original_cooldown != new_cooldown else "恢復預設"
            print(f"✅ 已將 {skill['name']} 的冷卻時間{status}為 {new_cooldown}秒")
    
    def _change_player_name(self):
        """修改玩家名稱"""
        self.keyboard_enabled = False
        new_name = simpledialog.askstring(
            "修改名稱", "輸入新的玩家名稱:",
            initialvalue=self.player_name, parent=self.root
        )
        self.keyboard_enabled = True
        
        if new_name:
            self.player_name = new_name
            self.player_label.config(text=f"👤 玩家: {self.player_name}")
            self.config_manager.set_settings('player_name', self.player_name)
            self.config_manager.save()
    
    def _show_settings(self):
        """顯示設定對話框"""
        self.keyboard_enabled = False
        
        dialog = SettingsDialog(self.root, {
            'x': self.skill_start_x,
            'y': self.skill_start_y,
            'sound': self.enable_sound
        })
        
        result = dialog.show()
        
        if result:
            self.skill_start_x = result['x']
            self.skill_start_y = result['y']
            self.enable_sound = result['sound']
            
            self.config_manager.set_settings('skill_start_x', self.skill_start_x)
            self.config_manager.set_settings('skill_start_y', self.skill_start_y)
            self.config_manager.set_settings('enable_sound', self.enable_sound)
            self.config_manager.save()
        
        self.keyboard_enabled = True
    
    def _create_room(self):
        """創建房間"""
        room_code = self.network.create_room()
        if room_code:
            self.room_info_label.config(text=f"● 房間: {room_code} (主機)", fg=Colors.ACCENT_GREEN)
            self.create_btn.configure(state=tk.DISABLED)
            self.join_btn.configure(state=tk.DISABLED)
            self.leave_btn.configure(state=tk.NORMAL)
            self._on_members_update([])
            messagebox.showinfo("房間已創建", f"房間代碼: {room_code}\n分享給隊友!", parent=self.root)
        else:
            messagebox.showerror("錯誤", "創建房間失敗", parent=self.root)
    
    def _join_room(self):
        """加入房間"""
        self.keyboard_enabled = False
        
        dialog = JoinRoomDialog(self.root)
        result = dialog.show()
        
        if result:
            # result 是字符串（房間代碼），不是字典
            room_code = result
            if self.network.join_room(room_code, self.player_name):
                self.room_info_label.config(text=f"● 房間: {room_code} (已連線)", fg=Colors.ACCENT_GREEN)
                self.create_btn.configure(state=tk.DISABLED)
                self.join_btn.configure(state=tk.DISABLED)
                self.leave_btn.configure(state=tk.NORMAL)
                messagebox.showinfo("成功", "已加入房間!", parent=self.root)
            else:
                messagebox.showerror("錯誤", "加入房間失敗\n請確認房間代碼正確或主機是否在線", parent=self.root)
        
        self.keyboard_enabled = True
    
    def _leave_room(self):
        """離開房間"""
        if messagebox.askyesno("確認", "確定要退出房間嗎?", parent=self.root):
            self.network.leave_room()
            self.room_info_label.config(text="● 未連線", fg=Colors.TEXT_SECONDARY)
            self.create_btn.configure(state=tk.NORMAL)
            self.join_btn.configure(state=tk.NORMAL)
            self.leave_btn.configure(state=tk.DISABLED)
            self.members_list.delete(0, tk.END)
    
    def _on_members_update(self, members):
        """成員更新回調"""
        self.members_list.delete(0, tk.END)
        if self.network.is_host:
            self.members_list.insert(tk.END, f"👑 {self.player_name} (主機)")
        for member in members:
            self.members_list.insert(tk.END, f"👤 {member}")
    
    def _on_network_skill(self, skill_data):
        """網路技能回調"""
        if skill_data.get('type') == 'skill':
            self.root.after(0, self._trigger_skill, skill_data['skill_id'], skill_data['player'])
    
    def _trigger_skill(self, skill_id, player_name=None):
        """觸發技能"""
        skill = self.skill_manager.get_skill(skill_id)
        if not skill:
            return
        
        player = player_name or self.player_name
        if player != self.player_name and not self.skill_receive.get(skill_id, True):
            return
        
        if skill_id in self.active_windows:
            is_permanent = self.skill_permanent.get(skill_id, False)
            if is_permanent:
                self.active_windows[skill_id].restart_countdown()
            else:
                self.active_windows[skill_id].close()
            return
        
        if skill_id not in self.window_order:
            self.window_order.append(skill_id)
        
        position = self._calculate_position(skill_id)
        is_permanent = self.skill_permanent.get(skill_id, False)
        skill_image = self.skill_manager.skill_images.get(skill_id)
        
        skill_window = SkillWindow(
            skill, player, position, skill_image,
            lambda w: self._on_window_close(w, skill_id),
            self.enable_sound, skill_id, is_permanent
        )
        self.active_windows[skill_id] = skill_window
        
        if player == self.player_name and self.skill_send.get(skill_id, True):
            self.network.broadcast_skill({
                'type': 'skill',
                'skill_id': skill_id,
                'player': player,
                'timestamp': time.time()
            })
    
    def _calculate_position(self, skill_id):
        """計算視窗位置"""
        index = self.window_order.index(skill_id) if skill_id in self.window_order else len(self.window_order)
        x = self.skill_start_x - (index * 110)
        y = self.skill_start_y
        return (x, y)
    
    def _reposition_windows(self):
        """重新排列視窗"""
        for skill_id in self.window_order:
            if skill_id in self.active_windows:
                index = self.window_order.index(skill_id)
                x = self.skill_start_x - (index * 110)
                y = self.skill_start_y
                self.active_windows[skill_id].update_position(x, y)
    
    def _on_window_close(self, window, skill_id):
        """視窗關閉回調"""
        if skill_id in self.active_windows:
            del self.active_windows[skill_id]
        if skill_id in self.window_order:
            self.window_order.remove(skill_id)
        self._reposition_windows()
    
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
        self.config_manager.set_settings('skill_send', self.skill_send)
        self.config_manager.set_settings('skill_receive', self.skill_receive)
        self.config_manager.set_settings('skill_permanent', self.skill_permanent)
        self.config_manager.save()
    
    def run(self):
        """運行應用程式"""
        self.root.mainloop()

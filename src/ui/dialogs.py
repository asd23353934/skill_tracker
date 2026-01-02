"""
對話框模組
提供各種對話框的創建和管理
"""

import tkinter as tk
from tkinter import simpledialog, messagebox
from src.ui.components import RoundedButton, BorderedFrame
from src.ui.styles import Colors, Fonts


class BaseDialog:
    """基礎對話框（圓角）"""
    
    def __init__(self, parent, title, width=400, height=300):
        """初始化對話框
        
        Args:
            parent: 父視窗
            title: 對話框標題
            width: 寬度
            height: 高度
        """
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.attributes('-topmost', True)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.overrideredirect(True)  # 移除邊框以便自訂
        self.dialog.configure(bg=Colors.BG_DARK)
        
        # 計算置中位置
        screen_width = parent.winfo_screenwidth()
        screen_height = parent.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.dialog.geometry(f"{width}x{height}+{x}+{y}")
        
        self.dialog.lift()
        self.dialog.focus_force()
        
        # 使用圓角框架作為容器
        from src.ui.components import RoundedFrame
        
        self.container = RoundedFrame(
            self.dialog,
            radius=15,
            bg=Colors.BG_MEDIUM,
            border_color=Colors.ACCENT_YELLOW,
            border_width=2
        )
        self.container.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # 標題列（可拖動）
        self.title_bar = tk.Frame(self.container.get_content(), bg=Colors.BG_MEDIUM, cursor='hand2')
        self.title_bar.pack(fill=tk.X, pady=(10, 5))
        
        tk.Label(
            self.title_bar, text=title,
            bg=Colors.BG_MEDIUM, fg=Colors.ACCENT_YELLOW,
            font=Fonts.TITLE_SMALL
        ).pack(side=tk.LEFT, padx=15)
        
        # 關閉按鈕
        close_btn = tk.Label(
            self.title_bar, text="✕",
            bg=Colors.BG_MEDIUM, fg=Colors.TEXT_SECONDARY,
            font=('Arial', 14, 'bold'),
            cursor='hand2'
        )
        close_btn.pack(side=tk.RIGHT, padx=15)
        close_btn.bind('<Button-1>', lambda e: self.close())
        
        # 啟用拖動
        self._enable_drag()
        
        # 內容區域（子類使用）
        self.content = self.container.get_content()
        
        self.result = None
    
    def _enable_drag(self):
        """啟用對話框拖動"""
        self.title_bar.bind('<Button-1>', self._start_drag)
        self.title_bar.bind('<B1-Motion>', self._on_drag)
        
        self._drag_x = 0
        self._drag_y = 0
    
    def _start_drag(self, event):
        """開始拖動"""
        self._drag_x = event.x
        self._drag_y = event.y
    
    def _on_drag(self, event):
        """拖動中"""
        x = self.dialog.winfo_x() + event.x - self._drag_x
        y = self.dialog.winfo_y() + event.y - self._drag_y
        self.dialog.geometry(f"+{x}+{y}")
    
    def show(self):
        """顯示對話框"""
        self.dialog.wait_window()
        return self.result
    
    def close(self):
        """關閉對話框"""
        self.dialog.destroy()


class ProfileManagerDialog(BaseDialog):
    """配置管理對話框 - 完整版"""
    
    def __init__(self, parent, config_manager, current_settings, main_window):
        """初始化配置管理對話框
        
        Args:
            parent: 父視窗
            config_manager: 配置管理器
            current_settings: 當前配置數據
            main_window: 主視窗實例（用於更新UI）
        """
        super().__init__(parent, "配置管理", 600, 500)
        self.config_manager = config_manager
        self.current_settings = current_settings
        self.main_window = main_window
        self.current_profile = self.config_manager.get_current_profile()
        
        self._create_ui()
    
    def _create_ui(self):
        """創建 UI"""
        # 標題
        title_frame = tk.Frame(self.content, bg=Colors.BG_MEDIUM)
        title_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(
            title_frame, text="💾 配置管理", 
            bg=Colors.BG_MEDIUM, fg=Colors.ACCENT_YELLOW,
            font=Fonts.TITLE_MEDIUM
        ).pack(side=tk.LEFT, padx=20)
        
        # 當前配置顯示
        tk.Label(
            title_frame, text="當前:", 
            bg=Colors.BG_MEDIUM, fg=Colors.TEXT_SECONDARY,
            font=Fonts.BODY_MEDIUM
        ).pack(side=tk.LEFT, padx=(20, 5))
        
        self.current_label = tk.Label(
            title_frame, text=self.current_profile, 
            bg=Colors.BG_MEDIUM, fg=Colors.ACCENT_BLUE,
            font=Fonts.BODY_MEDIUM_BOLD
        )
        self.current_label.pack(side=tk.LEFT)
        
        # 配置列表
        list_frame = BorderedFrame(self.content, bg=Colors.BG_DARK)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.profile_listbox = tk.Listbox(
            list_frame, bg=Colors.BG_DARK, fg=Colors.TEXT_PRIMARY,
            font=Fonts.BODY_LARGE,
            selectbackground=Colors.ACCENT_BLUE,
            yscrollcommand=scrollbar.set, height=12
        )
        self.profile_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.profile_listbox.yview)
        
        # 雙擊載入
        self.profile_listbox.bind('<Double-Button-1>', lambda e: self._switch_profile())
        
        self._refresh_list()
        
        # 按鈕組
        btn_frame = tk.Frame(self.content, bg=Colors.BG_MEDIUM)
        btn_frame.pack(pady=10)
        
        RoundedButton(
            btn_frame, "➕ 新增", self._create_new_profile, 
            Colors.ACCENT_GREEN, width=100, height=32
        ).pack(side=tk.LEFT, padx=3)
        
        RoundedButton(
            btn_frame, "📋 複製", self._copy_profile, 
            Colors.ACCENT_BLUE, width=100, height=32
        ).pack(side=tk.LEFT, padx=3)
        
        RoundedButton(
            btn_frame, "✏️ 重命名", self._rename_profile, 
            Colors.ACCENT_YELLOW, width=100, height=32
        ).pack(side=tk.LEFT, padx=3)
        
        RoundedButton(
            btn_frame, "🔄 切換", self._switch_profile, 
            Colors.ACCENT_PURPLE, width=100, height=32
        ).pack(side=tk.LEFT, padx=3)
        
        RoundedButton(
            btn_frame, "🗑️ 刪除", self._delete_profile, 
            Colors.ACCENT_RED, width=100, height=32
        ).pack(side=tk.LEFT, padx=3)
        
        # 提示
        tk.Label(
            self.content, 
            text="💡 雙擊配置名稱可快速切換 | 所有修改會自動保存到當前配置", 
            bg=Colors.BG_MEDIUM, fg=Colors.TEXT_SECONDARY,
            font=Fonts.BODY_SMALL
        ).pack(pady=10)
    
    def _refresh_list(self):
        """刷新配置列表"""
        self.profile_listbox.delete(0, tk.END)
        profiles = self.config_manager.list_profiles()
        
        for profile in profiles:
            display_text = f"{'★ ' if profile == self.current_profile else '   '}{profile}"
            self.profile_listbox.insert(tk.END, display_text)
    
    def _get_selected_profile_name(self):
        """獲取選中的配置名稱"""
        selection = self.profile_listbox.curselection()
        if not selection:
            return None
        
        display_text = self.profile_listbox.get(selection[0])
        # 移除星號標記
        return display_text.replace('★ ', '').strip()
    
    def _create_new_profile(self):
        """新增配置"""
        name = simpledialog.askstring("新增配置", "輸入新配置名稱:", parent=self.dialog)
        if name and name.strip():
            name = name.strip()
            
            # 檢查是否已存在
            if name in self.config_manager.list_profiles():
                messagebox.showerror("錯誤", f"配置 '{name}' 已存在!", parent=self.dialog)
                return
            
            # 創建初始配置 - 包含所有技能的預設值
            from src.ui.skill_manager import SkillManager
            all_skills = self.main_window.skill_manager.get_all_skills().keys()
            
            initial_settings = {
                'hotkeys': {},  # 所有技能無快捷鍵
                'send': {skill_id: True for skill_id in all_skills},  # 預設勾選
                'receive': {skill_id: True for skill_id in all_skills},  # 預設勾選
                'permanent': {skill_id: False for skill_id in all_skills},  # 預設不駐留
                'cooldown_overrides': {}  # 使用 config.json 中的原始秒數
            }
            
            if self.config_manager.save_profile(name, initial_settings):
                self._refresh_list()
                print(f"✅ 已新增配置 '{name}'")
            else:
                messagebox.showerror("錯誤", f"新增配置失敗!", parent=self.dialog)
    
    def _copy_profile(self):
        """複製選中的配置"""
        source_name = self._get_selected_profile_name()
        if not source_name:
            messagebox.showwarning("提示", "請先選擇要複製的配置!", parent=self.dialog)
            return
        
        new_name = simpledialog.askstring(
            "複製配置", 
            f"輸入新配置名稱:\n(將複製自 '{source_name}')", 
            parent=self.dialog
        )
        
        if new_name and new_name.strip():
            new_name = new_name.strip()
            
            # 檢查是否已存在
            if new_name in self.config_manager.list_profiles():
                messagebox.showerror("錯誤", f"配置 '{new_name}' 已存在!", parent=self.dialog)
                return
            
            # 載入源配置
            source_data = self.config_manager.load_profile(source_name)
            if source_data:
                # 保存為新配置
                if self.config_manager.save_profile(new_name, source_data):
                    self._refresh_list()
                    print(f"✅ 已複製配置 '{source_name}' → '{new_name}'")
                else:
                    messagebox.showerror("錯誤", "複製配置失敗!", parent=self.dialog)
            else:
                messagebox.showerror("錯誤", f"無法讀取配置 '{source_name}'!", parent=self.dialog)
    
    def _rename_profile(self):
        """重命名選中的配置"""
        old_name = self._get_selected_profile_name()
        if not old_name:
            messagebox.showwarning("提示", "請先選擇要重命名的配置!", parent=self.dialog)
            return
        
        new_name = simpledialog.askstring(
            "重命名配置", 
            f"輸入新名稱:\n(當前: '{old_name}')", 
            initialvalue=old_name,
            parent=self.dialog
        )
        
        if new_name and new_name.strip() and new_name.strip() != old_name:
            new_name = new_name.strip()
            
            # 檢查是否已存在
            if new_name in self.config_manager.list_profiles():
                messagebox.showerror("錯誤", f"配置 '{new_name}' 已存在!", parent=self.dialog)
                return
            
            # 重命名
            if self.config_manager.rename_profile(old_name, new_name):
                # 如果重命名的是當前配置，更新當前配置名稱
                if old_name == self.current_profile:
                    self.current_profile = new_name
                    self.config_manager.set_current_profile(new_name)
                    self.current_label.config(text=new_name)
                    # 更新主視窗的標籤
                    if hasattr(self.main_window, 'current_profile_label'):
                        self.main_window.current_profile_label.config(text=new_name)
                        self.main_window.current_profile_name = new_name
                
                self._refresh_list()
                print(f"✅ 已重命名配置 '{old_name}' → '{new_name}'")
            else:
                messagebox.showerror("錯誤", "重命名失敗!", parent=self.dialog)
    
    def _switch_profile(self):
        """切換到選中的配置"""
        profile_name = self._get_selected_profile_name()
        if not profile_name:
            messagebox.showwarning("提示", "請先選擇要切換的配置!", parent=self.dialog)
            return
        
        if profile_name == self.current_profile:
            messagebox.showinfo("提示", "已經是當前配置了!", parent=self.dialog)
            return
        
        # 載入配置數據
        profile_data = self.config_manager.load_profile(profile_name)
        if profile_data:
            # 設定為當前配置
            self.config_manager.set_current_profile(profile_name)
            self.current_profile = profile_name
            self.current_label.config(text=profile_name)
            
            # 返回配置數據給主視窗
            self.result = profile_data
            self.close()
            
            print(f"✅ 已切換到配置 '{profile_name}'")
        else:
            messagebox.showerror("錯誤", f"無法載入配置 '{profile_name}'!", parent=self.dialog)
    
    def _delete_profile(self):
        """刪除選中的配置"""
        profile_name = self._get_selected_profile_name()
        if not profile_name:
            messagebox.showwarning("提示", "請先選擇要刪除的配置!", parent=self.dialog)
            return
        
        # 不能刪除當前配置
        if profile_name == self.current_profile:
            messagebox.showerror("錯誤", "無法刪除當前正在使用的配置!", parent=self.dialog)
            return
        
        # 確認刪除
        if messagebox.askyesno("確認刪除", f"確定要刪除配置 '{profile_name}' 嗎？", parent=self.dialog):
            if self.config_manager.delete_profile(profile_name):
                self._refresh_list()
                print(f"✅ 配置 '{profile_name}' 已刪除")
            else:
                messagebox.showerror("錯誤", "刪除失敗!", parent=self.dialog)


class SettingsDialog(BaseDialog):
    """設定對話框"""
    
    def __init__(self, parent, current_settings):
        """初始化設定對話框
        
        Args:
            parent: 父視窗
            current_settings: 當前設定字典
        """
        super().__init__(parent, "設定", 450, 320)  # 減少高度（移除尺寸設定）
        self.current_settings = current_settings
        
        self._create_ui()
    
    def _create_ui(self):
        """創建 UI"""
        # 位置設定
        pos_label = tk.Label(
            self.content, text="技能視窗起始位置", 
            bg=Colors.BG_MEDIUM, fg=Colors.ACCENT_YELLOW,
            font=Fonts.BODY_LARGE
        )
        pos_label.pack(anchor='w', padx=20, pady=(15, 5))
        
        pos_frame = tk.Frame(self.content, bg=Colors.BG_MEDIUM)
        pos_frame.pack(pady=5, padx=20, fill='x')
        
        tk.Label(
            pos_frame, text="X:", 
            bg=Colors.BG_MEDIUM, fg=Colors.TEXT_PRIMARY,
            font=Fonts.BODY_LARGE
        ).grid(row=0, column=0, padx=8)
        
        self.x_entry = tk.Entry(
            pos_frame, font=('Arial', 11), width=10, 
            bg=Colors.BG_DARK, fg=Colors.TEXT_PRIMARY, relief=tk.FLAT
        )
        self.x_entry.insert(0, str(self.current_settings.get('x', 1700)))
        self.x_entry.grid(row=0, column=1, padx=8)
        
        tk.Label(
            pos_frame, text="Y:", 
            bg=Colors.BG_MEDIUM, fg=Colors.TEXT_PRIMARY,
            font=Fonts.BODY_LARGE
        ).grid(row=0, column=2, padx=8)
        
        self.y_entry = tk.Entry(
            pos_frame, font=('Arial', 11), width=10,
            bg=Colors.BG_DARK, fg=Colors.TEXT_PRIMARY, relief=tk.FLAT
        )
        self.y_entry.insert(0, str(self.current_settings.get('y', 850)))
        self.y_entry.grid(row=0, column=3, padx=8)
        
        # 音效設定
        self.sound_var = tk.BooleanVar(value=self.current_settings.get('sound', True))
        tk.Checkbutton(
            self.content, text="🔊 啟用音效", variable=self.sound_var,
            bg=Colors.BG_MEDIUM, fg=Colors.TEXT_PRIMARY, 
            font=Fonts.BODY_LARGE,
            selectcolor=Colors.BG_DARK, activebackground=Colors.BG_MEDIUM
        ).pack(pady=15)
        
        # 提示
        tk.Label(
            self.content, text="💡 視窗尺寸自動適應技能圖片大小", 
            bg=Colors.BG_MEDIUM, fg=Colors.TEXT_SECONDARY,
            font=Fonts.BODY_SMALL
        ).pack(pady=5)
        
        # 儲存按鈕
        RoundedButton(
            self.content, "✓ 儲存設定", self._save, 
            Colors.ACCENT_GREEN, width=150, height=35
        ).pack(pady=20)
    
    def _save(self):
        """儲存設定"""
        try:
            self.result = {
                'x': int(self.x_entry.get()),
                'y': int(self.y_entry.get()),
                'alpha': float(self.alpha_entry.get()),
                'sound': self.sound_var.get()
            }
            self.close()
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("錯誤", f"設定格式錯誤：{e}", parent=self.dialog)


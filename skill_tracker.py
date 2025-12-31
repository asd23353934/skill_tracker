import tkinter as tk
from tkinter import messagebox, simpledialog
from PIL import Image, ImageTk
import json
import os
import sys
import threading
import time
from pynput import keyboard
import winsound
import socket
import socketserver
import hashlib

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class NetworkManager:
    def __init__(self, callback):
        self.callback = callback
        self.server = None
        self.client = None
        self.room_code = None
        self.is_host = False
        
    def create_room(self):
        try:
            self.room_code = hashlib.md5(str(time.time()).encode()).hexdigest()[:6].upper()
            self.is_host = True
            self.server = SkillServer(self.callback)
            threading.Thread(target=self.server.serve_forever, daemon=True).start()
            return self.room_code
        except:
            return None
    
    def join_room(self, room_code, server_ip='127.0.0.1'):
        try:
            self.room_code = room_code
            self.is_host = False
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client.connect((server_ip, 9999))
            threading.Thread(target=self._receive_messages, daemon=True).start()
            return True
        except:
            return False
    
    def broadcast_skill(self, skill_data):
        if self.is_host and self.server:
            self.server.broadcast(json.dumps(skill_data))
        elif self.client:
            try:
                self.client.send(json.dumps(skill_data).encode())
            except:
                pass
    
    def _receive_messages(self):
        while True:
            try:
                data = self.client.recv(1024).decode()
                if data:
                    self.callback(json.loads(data))
            except:
                break

class SkillServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    
    def __init__(self, callback):
        self.callback = callback
        self.clients = []
        super().__init__(('0.0.0.0', 9999), SkillHandler)
        self.skill_handler_callback = callback
    
    def broadcast(self, message):
        for client in self.clients[:]:
            try:
                client.send(message.encode())
            except:
                self.clients.remove(client)

class SkillHandler(socketserver.BaseRequestHandler):
    def handle(self):
        self.server.clients.append(self.request)
        while True:
            try:
                data = self.request.recv(1024).decode()
                if not data:
                    break
                self.server.broadcast(data)
                self.server.skill_handler_callback(json.loads(data))
            except:
                break
        self.server.clients.remove(self.request)

class SkillWindow:
    def __init__(self, skill, player, position, skill_image, on_close, enable_sound):
        self.skill = skill
        self.player = player
        self.on_close = on_close
        self.enable_sound = enable_sound
        self.remaining = skill['cooldown']
        self.total = skill['cooldown']
        
        self.window = tk.Toplevel()
        self.window.title("")
        self.window.attributes('-topmost', True)
        self.window.attributes('-alpha', 0.95)
        self.window.overrideredirect(True)
        self.window.configure(bg='#1a1a1a')
        
        container = tk.Frame(self.window, bg='#2a2a2a', highlightbackground='#667eea', highlightthickness=3)
        container.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        tk.Label(container, text=skill['name'], bg='#2a2a2a', fg='#fbbf24',
                font=('Microsoft JhengHei', 9, 'bold')).pack(pady=(3, 2))
        
        if skill_image:
            img_label = tk.Label(container, image=skill_image, bg='#2a2a2a')
            img_label.image = skill_image
            img_label.pack(pady=3)
        
        self.timer_label = tk.Label(container, text=f"{self.remaining}秒", bg='#2a2a2a', fg='#ffffff',
                                    font=('Microsoft JhengHei', 20, 'bold'))
        self.timer_label.pack(pady=3)
        
        tk.Label(container, text=f"玩家: {player}", bg='#2a2a2a', fg='#94a3b8',
                font=('Microsoft JhengHei', 7)).pack(pady=(0, 3))
        
        self.window.geometry(f"110x140+{position[0]}+{position[1]}")
        
        self.running = True
        threading.Thread(target=self.countdown, daemon=True).start()
    
    def countdown(self):
        while self.running and self.remaining > 0:
            time.sleep(1)
            self.remaining -= 1
            if self.running:
                self.update_display()
        
        if self.running:
            if self.enable_sound:
                self.play_sound()
            time.sleep(2)
            self.close()
    
    def update_display(self):
        if self.remaining > 0:
            self.timer_label.config(text=f"{self.remaining}秒")
        else:
            self.timer_label.config(text="完成!", fg='#4ade80')
    
    def play_sound(self):
        try:
            winsound.Beep(800, 300)
        except:
            pass
    
    def close(self):
        self.running = False
        self.window.destroy()
        self.on_close(self)

class SkillTracker:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("技能追蹤器")
        
        self.config = self.load_config()
        settings = self.config.get('settings', {})
        
        self.root.attributes('-topmost', True)
        self.root.attributes('-alpha', 0.95)
        self.root.configure(bg='#1a1a1a')
        
        self.skills = {}
        self.skill_images = {}
        self.skill_images_small = {}
        self.active_windows = {}
        self.player_name = settings.get('player_name', '玩家1')
        self.network = NetworkManager(self.on_network_skill)
        
        self.skill_start_x = settings.get('skill_start_x', 1700)
        self.skill_start_y = settings.get('skill_start_y', 850)
        self.enable_sound = settings.get('enable_sound', True)
        
        self.load_skills()
        self.create_ui()
        self.start_keyboard_listener()
        
        self.root.geometry("350x500+50+50")
    
    def load_config(self):
        config_file = resource_path('config.json')
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            messagebox.showerror("錯誤", f"無法載入 config.json\n{e}")
            sys.exit(1)
    
    def save_config(self):
        try:
            with open(resource_path('config.json'), 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except:
            pass
    
    def load_skills(self):
        for skill_data in self.config.get('skills', []):
            skill_id = skill_data['id']
            self.skills[skill_id] = skill_data
            
            icon_path = resource_path(f"images/{skill_data['icon']}")
            try:
                img = Image.open(icon_path)
                img_large = img.resize((60, 60), Image.Resampling.LANCZOS)
                img_small = img.resize((30, 30), Image.Resampling.LANCZOS)
                self.skill_images[skill_id] = ImageTk.PhotoImage(img_large)
                self.skill_images_small[skill_id] = ImageTk.PhotoImage(img_small)
            except:
                self.skill_images[skill_id] = None
                self.skill_images_small[skill_id] = None
    
    def create_ui(self):
        main_frame = tk.Frame(self.root, bg='#1a1a1a')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        tk.Label(main_frame, text="🎯 技能追蹤器", 
                bg='#1a1a1a', fg='#fbbf24', font=('Microsoft JhengHei', 14, 'bold')).pack(pady=(0, 10))
        
        room_frame = tk.Frame(main_frame, bg='#2a2a2a', relief=tk.RIDGE, bd=2)
        room_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(room_frame, text="房間狀態", 
                bg='#2a2a2a', fg='#cbd5e1', font=('Microsoft JhengHei', 10, 'bold')).pack(pady=5)
        
        self.room_info_label = tk.Label(room_frame, text="未連線", 
                                        bg='#2a2a2a', fg='#94a3b8', font=('Microsoft JhengHei', 9))
        self.room_info_label.pack(pady=5)
        
        btn_frame = tk.Frame(room_frame, bg='#2a2a2a')
        btn_frame.pack(pady=5)
        
        tk.Button(btn_frame, text="創建房間", command=self.create_room,
                 bg='#667eea', fg='white', font=('Microsoft JhengHei', 9, 'bold'),
                 relief=tk.FLAT, padx=12, pady=4, cursor='hand2').pack(side=tk.LEFT, padx=3)
        
        tk.Button(btn_frame, text="加入房間", command=self.join_room,
                 bg='#764ba2', fg='white', font=('Microsoft JhengHei', 9, 'bold'),
                 relief=tk.FLAT, padx=12, pady=4, cursor='hand2').pack(side=tk.LEFT, padx=3)
        
        player_frame = tk.Frame(room_frame, bg='#2a2a2a')
        player_frame.pack(pady=(0, 5))
        
        self.player_label = tk.Label(player_frame, text=f"玩家: {self.player_name}", 
                bg='#2a2a2a', fg='#4ade80', font=('Microsoft JhengHei', 8))
        self.player_label.pack(side=tk.LEFT, padx=5)
        
        tk.Button(player_frame, text="修改", command=self.change_player_name,
                 bg='#444', fg='white', font=('Microsoft JhengHei', 7),
                 relief=tk.FLAT, padx=5, pady=2, cursor='hand2').pack(side=tk.LEFT)
        
        skills_frame = tk.Frame(main_frame, bg='#2a2a2a', relief=tk.RIDGE, bd=2)
        skills_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        tk.Label(skills_frame, text="可用技能", 
                bg='#2a2a2a', fg='#cbd5e1', font=('Microsoft JhengHei', 10, 'bold')).pack(pady=5)
        
        for skill_id, skill in self.skills.items():
            skill_item = tk.Frame(skills_frame, bg='#1a1a1a', relief=tk.RAISED, bd=1)
            skill_item.pack(fill=tk.X, padx=5, pady=2)
            
            if self.skill_images_small.get(skill_id):
                img_label = tk.Label(skill_item, image=self.skill_images_small[skill_id], bg='#1a1a1a')
                img_label.image = self.skill_images_small[skill_id]
                img_label.pack(side=tk.LEFT, padx=5, pady=2)
            
            tk.Label(skill_item, text=f"{skill['name']} ({skill['cooldown']}秒)", 
                    bg='#1a1a1a', fg='#ffffff', font=('Microsoft JhengHei', 9)).pack(side=tk.LEFT, padx=5, pady=3)
            
            tk.Label(skill_item, text=f"{skill['hotkey']}", 
                    bg='#fbbf24', fg='#000000', font=('Microsoft JhengHei', 8, 'bold'),
                    padx=5, pady=2).pack(side=tk.RIGHT, padx=5)
        
        settings_btn = tk.Button(main_frame, text="⚙️ 設定", command=self.show_settings,
                                bg='#444', fg='white', font=('Microsoft JhengHei', 9, 'bold'),
                                relief=tk.FLAT, pady=4, cursor='hand2')
        settings_btn.pack(fill=tk.X, pady=5)
        
        tk.Label(main_frame, text="提示: 再次按快捷鍵可關閉技能倒數", 
                bg='#1a1a1a', fg='#94a3b8', font=('Microsoft JhengHei', 7)).pack(pady=2)
    
    def change_player_name(self):
        new_name = simpledialog.askstring("修改名稱", "輸入新的玩家名稱:", initialvalue=self.player_name)
        if new_name:
            self.player_name = new_name
            self.player_label.config(text=f"玩家: {self.player_name}")
            self.config['settings']['player_name'] = self.player_name
            self.save_config()
    
    def show_settings(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("設定")
        dialog.attributes('-topmost', True)
        dialog.configure(bg='#2a2a2a')
        dialog.geometry("350x250")
        
        tk.Label(dialog, text="技能視窗起始位置", bg='#2a2a2a', fg='#fbbf24',
                font=('Microsoft JhengHei', 11, 'bold')).pack(pady=10)
        
        pos_frame = tk.Frame(dialog, bg='#2a2a2a')
        pos_frame.pack(pady=5)
        
        tk.Label(pos_frame, text="X:", bg='#2a2a2a', fg='white',
                font=('Microsoft JhengHei', 9)).grid(row=0, column=0, padx=5)
        x_entry = tk.Entry(pos_frame, font=('Arial', 10), width=8)
        x_entry.insert(0, str(self.skill_start_x))
        x_entry.grid(row=0, column=1, padx=5)
        
        tk.Label(pos_frame, text="Y:", bg='#2a2a2a', fg='white',
                font=('Microsoft JhengHei', 9)).grid(row=0, column=2, padx=5)
        y_entry = tk.Entry(pos_frame, font=('Arial', 10), width=8)
        y_entry.insert(0, str(self.skill_start_y))
        y_entry.grid(row=0, column=3, padx=5)
        
        sound_var = tk.BooleanVar(value=self.enable_sound)
        sound_check = tk.Checkbutton(dialog, text="啟用音效", variable=sound_var,
                                     bg='#2a2a2a', fg='white', font=('Microsoft JhengHei', 10),
                                     selectcolor='#1a1a1a', activebackground='#2a2a2a',
                                     activeforeground='white')
        sound_check.pack(pady=10)
        
        tk.Label(dialog, text="提示: 從右下往左排列", bg='#2a2a2a', fg='#94a3b8',
                font=('Microsoft JhengHei', 8)).pack(pady=5)
        
        def save():
            try:
                self.skill_start_x = int(x_entry.get())
                self.skill_start_y = int(y_entry.get())
                self.enable_sound = sound_var.get()
                
                self.config['settings']['skill_start_x'] = self.skill_start_x
                self.config['settings']['skill_start_y'] = self.skill_start_y
                self.config['settings']['enable_sound'] = self.enable_sound
                
                self.save_config()
                messagebox.showinfo("成功", "設定已儲存!")
                dialog.destroy()
            except:
                messagebox.showerror("錯誤", "請輸入有效的數字")
        
        tk.Button(dialog, text="✓ 儲存", command=save,
                 bg='#667eea', fg='white', font=('Microsoft JhengHei', 10, 'bold'),
                 relief=tk.FLAT, padx=20, pady=8, cursor='hand2').pack(pady=20)
    
    def create_room(self):
        room_code = self.network.create_room()
        if room_code:
            self.room_info_label.config(text=f"房間: {room_code} (主機)", fg='#4ade80')
            messagebox.showinfo("房間已創建", f"房間代碼: {room_code}\n分享給隊友!")
        else:
            messagebox.showerror("錯誤", "創建房間失敗")
    
    def join_room(self):
        room_code = simpledialog.askstring("加入房間", "輸入房間代碼:")
        if not room_code:
            return
        
        server_ip = simpledialog.askstring("伺服器 IP", "輸入主機 IP:", initialvalue="127.0.0.1")
        if not server_ip:
            server_ip = "127.0.0.1"
        
        if self.network.join_room(room_code, server_ip):
            self.room_info_label.config(text=f"房間: {room_code} (已連線)", fg='#4ade80')
            messagebox.showinfo("成功", "已加入房間!")
        else:
            messagebox.showerror("錯誤", "加入房間失敗")
    
    def trigger_skill(self, skill_id, player_name=None):
        if skill_id not in self.skills:
            return
        
        if skill_id in self.active_windows:
            self.active_windows[skill_id].close()
            return
        
        skill = self.skills[skill_id]
        player = player_name or self.player_name
        
        position = self.calculate_position()
        
        skill_window = SkillWindow(skill, player, position, self.skill_images.get(skill_id), 
                                   lambda w: self.on_window_close(w, skill_id), self.enable_sound)
        self.active_windows[skill_id] = skill_window
        
        if player == self.player_name:
            self.network.broadcast_skill({
                'skill_id': skill_id,
                'player': player,
                'timestamp': time.time()
            })
    
    def calculate_position(self):
        x = self.skill_start_x - (len(self.active_windows) * 120)
        y = self.skill_start_y
        return (x, y)
    
    def on_window_close(self, window, skill_id):
        if skill_id in self.active_windows:
            del self.active_windows[skill_id]
    
    def on_network_skill(self, skill_data):
        self.root.after(0, self.trigger_skill, skill_data['skill_id'], skill_data['player'])
    
    def on_key_press(self, key):
        try:
            key_name = key.name if hasattr(key, 'name') else str(key.char)
            for skill_id, skill in self.skills.items():
                if skill['hotkey'].lower() == key_name.lower():
                    self.root.after(0, self.trigger_skill, skill_id)
                    break
        except:
            pass
    
    def start_keyboard_listener(self):
        listener = keyboard.Listener(on_press=self.on_key_press)
        listener.daemon = True
        listener.start()
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = SkillTracker()
    app.run()

import os
import sys
import subprocess
import customtkinter as ctk
from tkinter import messagebox

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class SetupApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("きりぬきつーる - セットアップウィザード")
        self.geometry("460x360")
        self.resizable(False, False)
        
        # Center window
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
        
        # Root path determination
        if getattr(sys, 'frozen', False):
            self.base_dir = os.path.dirname(sys.executable)
        else:
            self.base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

        # GUI Layout
        self.main_frame = ctk.CTkFrame(self, corner_radius=12)
        self.main_frame.pack(padx=20, pady=20, fill="both", expand=True)
        
        self.title_label = ctk.CTkLabel(
            self.main_frame, 
            text="🎨 きりぬきつーる セットアップ", 
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.title_label.pack(pady=(20, 5))
        
        self.desc_label = ctk.CTkLabel(
            self.main_frame, 
            text="ワンクリックで必須フォルダの作成と\nデスクトップへのショートカット配置を行います。",
            font=ctk.CTkFont(size=12),
            text_color="gray70"
        )
        self.desc_label.pack(pady=(0, 15))
        
        # Log box
        self.log_textbox = ctk.CTkTextbox(self.main_frame, height=100, width=400, font=ctk.CTkFont(size=11))
        self.log_textbox.pack(pady=(0, 15))
        self.log_textbox.insert("end", "準備完了。下の「セットアップ実行」を押してください。\n")
        self.log_textbox.configure(state="disabled")
        
        # Action Buttons
        self.btn_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.btn_frame.pack(fill="x", padx=20)
        
        self.setup_btn = ctk.CTkButton(
            self.btn_frame, 
            text="🚀 セットアップ実行", 
            font=ctk.CTkFont(size=14, weight="bold"),
            height=36,
            command=self.run_setup
        )
        self.setup_btn.pack(side="left", expand=True, fill="x", padx=(0, 5))
        
        self.launch_btn = ctk.CTkButton(
            self.btn_frame, 
            text="▶ ツールを起動", 
            font=ctk.CTkFont(size=14, weight="bold"),
            height=36,
            fg_color="gray30",
            hover_color="gray40",
            command=self.launch_main_app
        )
        self.launch_btn.pack(side="right", expand=True, fill="x", padx=(5, 0))

    def log(self, msg):
        self.log_textbox.configure(state="normal")
        self.log_textbox.insert("end", f"{msg}\n")
        self.log_textbox.see("end")
        self.log_textbox.configure(state="disabled")

    def create_shortcut(self, target_exe, shortcut_path):
        ps_script = f'''
        $WshShell = New-Object -ComObject WScript.Shell
        $Shortcut = $WshShell.CreateShortcut("{shortcut_path}")
        $Shortcut.TargetPath = "{target_exe}"
        $Shortcut.WorkingDirectory = "{os.path.dirname(target_exe)}"
        $Shortcut.Save()
        '''
        cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script]
        res = subprocess.run(cmd, capture_output=True, text=True)
        return res.returncode == 0

    def run_setup(self):
        self.log("--- セットアップを開始します ---")
        
        # 1. Folders creation
        required_dirs = ["動画", "画像", "ショート", "temp"]
        for d in required_dirs:
            full_p = os.path.join(self.base_dir, d)
            if not os.path.exists(full_p):
                os.makedirs(full_p, exist_ok=True)
                self.log(f"📁 フォルダ作成: {d}")
            else:
                self.log(f"✅ フォルダ確認: {d}")
                
        # 2. Shortcut creation
        exe_path = os.path.join(self.base_dir, "きりぬきつーる.exe")
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        shortcut_p = os.path.join(desktop_path, "きりぬきつーる.lnk")
        
        if os.path.exists(exe_path):
            if self.create_shortcut(os.path.abspath(exe_path), os.path.abspath(shortcut_p)):
                self.log(f"🔗 ショートカット作成成功: デスクトップ")
            else:
                self.log(f"⚠️ ショートカット作成失敗")
        else:
            self.log(f"⚠️ きりぬきつーる.exe が見つかりませんでした")
            
        self.log("🎉 セットアップが完了しました！")
        self.setup_btn.configure(text="✅ セットアップ完了", fg_color="forestgreen", state="disabled")
        self.launch_btn.configure(fg_color="#1a73e8", hover_color="#155cb4")

    def launch_main_app(self):
        exe_path = os.path.join(self.base_dir, "きりぬきつーる.exe")
        if os.path.exists(exe_path):
            try:
                os.startfile(exe_path)
                self.destroy()
            except Exception as e:
                messagebox.showerror("エラー", f"起動に失敗しました: {e}")
        else:
            messagebox.showerror("エラー", "きりぬきつーる.exe が見つかりません。")

if __name__ == "__main__":
    app = SetupApp()
    app.mainloop()

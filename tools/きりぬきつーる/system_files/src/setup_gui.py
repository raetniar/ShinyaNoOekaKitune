import os
import sys
import shutil
import subprocess
import customtkinter as ctk
from tkinter import filedialog, messagebox

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class SetupApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("きりぬきつーる - インストーラー")
        self.geometry("520x460")
        self.resizable(False, False)
        
        # Center window
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
        
        # Source base dir
        if getattr(sys, 'frozen', False):
            self.source_dir = os.path.dirname(sys.executable)
            self.bundled_dir = getattr(sys, '_MEIPASS', self.source_dir)
        else:
            self.source_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
            self.bundled_dir = self.source_dir

        # Default install dir: User's Documents\きりぬきつーる
        docs_dir = os.path.join(os.path.expanduser("~"), "Documents")
        default_target = os.path.join(docs_dir, "きりぬきつーる")
        self.target_dir_var = ctk.StringVar(value=default_target)

        # GUI Layout
        self.main_frame = ctk.CTkFrame(self, corner_radius=12)
        self.main_frame.pack(padx=20, pady=20, fill="both", expand=True)
        
        self.title_label = ctk.CTkLabel(
            self.main_frame, 
            text="🎨 きりぬきつーる インストーラー", 
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.title_label.pack(pady=(15, 5))
        
        self.desc_label = ctk.CTkLabel(
            self.main_frame, 
            text="インストール先を確認・変更し、「インストール実行」を押してください。\n必須ファイル・フォルダの構築とショートカット作成を自動で行います。",
            font=ctk.CTkFont(size=12),
            text_color="gray70"
        )
        self.desc_label.pack(pady=(0, 10))
        
        # Folder selection frame
        self.folder_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.folder_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        self.folder_lbl = ctk.CTkLabel(self.folder_frame, text="インストール先フォルダ:", font=ctk.CTkFont(size=12, weight="bold"))
        self.folder_lbl.pack(anchor="w", pady=(0, 3))
        
        self.path_entry = ctk.CTkEntry(self.folder_frame, textvariable=self.target_dir_var, font=ctk.CTkFont(size=11))
        self.path_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        self.browse_btn = ctk.CTkButton(self.folder_frame, text="参照...", width=70, command=self.browse_folder)
        self.browse_btn.pack(side="right")
        
        # Log box
        self.log_textbox = ctk.CTkTextbox(self.main_frame, height=120, width=460, font=ctk.CTkFont(size=11))
        self.log_textbox.pack(pady=(0, 15), padx=15)
        self.log_textbox.insert("end", "準備完了。インストール先を確認の上「インストール実行」を押してください。\n")
        self.log_textbox.configure(state="disabled")
        
        # Action Buttons
        self.btn_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.btn_frame.pack(fill="x", padx=15)
        
        self.setup_btn = ctk.CTkButton(
            self.btn_frame, 
            text="🚀 インストール実行", 
            font=ctk.CTkFont(size=14, weight="bold"),
            height=38,
            command=self.run_setup
        )
        self.setup_btn.pack(side="left", expand=True, fill="x", padx=(0, 5))
        
        self.launch_btn = ctk.CTkButton(
            self.btn_frame, 
            text="▶ ツールを起動", 
            font=ctk.CTkFont(size=14, weight="bold"),
            height=38,
            fg_color="gray30",
            hover_color="gray40",
            command=self.launch_main_app
        )
        self.launch_btn.pack(side="right", expand=True, fill="x", padx=(5, 0))

    def browse_folder(self):
        chosen = filedialog.askdirectory(title="インストール先フォルダの選択", initialdir=self.target_dir_var.get())
        if chosen:
            self.target_dir_var.set(os.path.normpath(chosen))

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
        target_dir = os.path.abspath(self.target_dir_var.get().strip())
        self.log(f"--- インストールを開始します: {target_dir} ---")
        
        try:
            os.makedirs(target_dir, exist_ok=True)
        except Exception as e:
            messagebox.showerror("エラー", f"インストール先フォルダを作成できませんでした: {e}")
            return
            
        # 1. Copy main executable & system_files if installing to a new folder
        src_exe = os.path.join(self.source_dir, "きりぬきつーる.exe")
        if not os.path.exists(src_exe):
            src_exe = os.path.join(self.bundled_dir, "きりぬきつーる.exe")
            
        target_exe = os.path.join(target_dir, "きりぬきつーる.exe")
        
        if os.path.exists(src_exe) and os.path.abspath(src_exe) != os.path.abspath(target_exe):
            self.log("📦 アプリ本体 (きりぬきつーる.exe) をコピー中...")
            try:
                shutil.copy2(src_exe, target_exe)
                self.log("✅ 本体ファイルのデプロイ完了")
            except Exception as e:
                self.log(f"⚠️ コピー警告: {e}")

        # 2. Copy system_files directory if exists
        src_sys = os.path.join(self.source_dir, "system_files")
        target_sys = os.path.join(target_dir, "system_files")
        if os.path.exists(src_sys) and os.path.abspath(src_sys) != os.path.abspath(target_sys):
            self.log("📦 システムライブラリ (system_files) を複製中...")
            try:
                if os.path.exists(target_sys):
                    shutil.rmtree(target_sys, ignore_errors=True)
                shutil.copytree(src_sys, target_sys)
                self.log("✅ システムライブラリのデプロイ完了")
            except Exception as e:
                self.log(f"⚠️ ライブラリ複製警告: {e}")

        # 3. Create required working folders
        required_dirs = ["動画", "画像", "ショート", "temp"]
        for d in required_dirs:
            full_p = os.path.join(target_dir, d)
            if not os.path.exists(full_p):
                os.makedirs(full_p, exist_ok=True)
                self.log(f"📁 フォルダ作成: {d}")
            else:
                self.log(f"✅ フォルダ確認: {d}")

        # 4. Create Desktop & Start Menu Shortcuts
        if os.path.exists(target_exe):
            # Desktop Shortcut
            desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
            desktop_shortcut = os.path.join(desktop_path, "きりぬきつーる.lnk")
            if self.create_shortcut(target_exe, desktop_shortcut):
                self.log("🔗 デスクトップショートカット作成成功")
            
            # Start Menu Shortcut
            start_menu_path = os.path.join(os.path.expanduser("~"), "AppData", "Roaming", "Microsoft", "Windows", "Start Menu", "Programs")
            start_shortcut = os.path.join(start_menu_path, "きりぬきつーる.lnk")
            if self.create_shortcut(target_exe, start_shortcut):
                self.log("🔗 スタートメニューへの追加成功")
        else:
            self.log("⚠️ きりぬきつーる.exe が見つかりませんでした")
            
        self.log("🎉 インストールが完了しました！")
        self.setup_btn.configure(text="✅ インストール完了", fg_color="forestgreen", state="disabled")
        self.launch_btn.configure(fg_color="#1a73e8", hover_color="#155cb4")

    def launch_main_app(self):
        target_dir = os.path.abspath(self.target_dir_var.get().strip())
        exe_path = os.path.join(target_dir, "きりぬきつーる.exe")
        if not os.path.exists(exe_path):
            exe_path = os.path.join(self.source_dir, "きりぬきつーる.exe")
            
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

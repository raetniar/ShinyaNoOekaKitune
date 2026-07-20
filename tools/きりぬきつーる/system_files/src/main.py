import os
import sys
import tkinter as tk
from tkinter import ttk
import customtkinter as ctk

class DummyWriter:
    def write(self, s): pass
    def flush(self): pass

if sys.stdout is None:
    sys.stdout = DummyWriter()
if sys.stderr is None:
    sys.stderr = DummyWriter()

# アプリ用ディレクトリ
config_dir = os.path.join(os.getenv('APPDATA'), 'KirinukiTool')
config_path = os.path.join(config_dir, 'config.json')

# スプラッシュ画面の設定と起動
splash = tk.Tk()
splash.title("起動中...")
splash.overrideredirect(True)
splash.configure(bg="#1a1a1a")

w, h = 450, 180
sw = splash.winfo_screenwidth()
sh = splash.winfo_screenheight()
x = (sw - w) // 2
y = (sh - h) // 2
splash.geometry(f"{w}x{h}+{x}+{y}")

lbl = tk.Label(splash, text="きりぬき箇所判定・一括編集ツール", font=("Segoe UI", 16, "bold"), fg="#1a73e8", bg="#1a1a1a")
lbl.pack(pady=(35, 5))

status_lbl = tk.Label(splash, text="ライブラリをロードしています...", font=("Segoe UI", 10), fg="#aaaaaa", bg="#1a1a1a")
status_lbl.pack(pady=5)

style = ttk.Style()
style.theme_use('default')
style.configure("blue.Horizontal.TProgressbar", foreground='#1a73e8', background='#1a73e8', thickness=10)

progress = ttk.Progressbar(splash, style="blue.Horizontal.TProgressbar", length=350, mode="determinate")
progress.pack(pady=15)
progress['value'] = 0
splash.update()

try:
    status_lbl.configure(text="音声・動画ライブラリの準備中...")
    progress['value'] = 30
    splash.update()
    
    # 共通モジュールのインポート
    import audio as audio_mod
    import video as video_mod
    
    status_lbl.configure(text="動画編集システムをロード中...")
    progress['value'] = 60
    splash.update()
    video_mod.init_video_libs()
    
    status_lbl.configure(text="AI音声認識エンジンをロード中...")
    progress['value'] = 90
    splash.update()
    audio_mod.init_whisper()
    
    status_lbl.configure(text="完了しました。起動中...")
    progress['value'] = 100
    splash.update()
except Exception as e:
    import traceback
    print(f"モジュールロード中にエラーが発生しました: {e}")
    traceback.print_exc()

splash.destroy()

# アプリ本体のインポートと起動
from config import ConfigManager
from app import App

config_manager = ConfigManager(config_dir, config_path)
config_data = config_manager.load_config()

# UIフォントの設定をグローバルテーマに適用
ui_font = config_data.get("ui_font_family", "Yu Gothic UI")
ui_font_size = int(config_data.get("ui_font_size", 12))
try:
    ctk.ThemeManager.theme['CTkFont']['family'] = ui_font
    ctk.ThemeManager.theme['CTkFont']['size'] = ui_font_size
except Exception:
    pass

# テンポラリフォルダの自動作成
os.makedirs("temp", exist_ok=True)

app = App(config_manager)
app.load_prompt_template()
app.mainloop()

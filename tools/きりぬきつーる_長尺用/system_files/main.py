import os
import sys

# CPUスレッドの占有を防ぎPCが固まらないようにするための環境変数設定
os.environ["OMP_NUM_THREADS"] = "4"
os.environ["MKL_NUM_THREADS"] = "4"
os.environ["OPENBLAS_NUM_THREADS"] = "4"
os.environ["VECLIB_MAXIMUM_THREADS"] = "4"
os.environ["NUMEXPR_NUM_THREADS"] = "4" 
import subprocess
import re
import threading
import time
import math
import bisect
import tempfile

# PyInstallerで --noconsole を使用したときに stdout/stderr が None になり
# whisper や tqdm の書き出しで 'NoneType' object has no attribute 'write' が発生するのを防止
class DummyStream:
    def write(self, x):
        pass
    def flush(self):
        pass

if sys.stdout is None:
    sys.stdout = DummyStream()
if sys.stderr is None:
    sys.stderr = DummyStream()

import customtkinter as ctk
from tkinter import filedialog, messagebox
import tkinter as tk
import colorsys
import PIL.Image
import PIL.ImageTk

# カスタム例外クラスの定義
class AudioProcessingError(RuntimeError): pass
class FFmpegError(RuntimeError): pass
class SRTWriteError(RuntimeError): pass
class UserCancelledError(RuntimeError): pass

try:
    import torch
    torch.set_num_threads(4)
except Exception:
    pass

def parse_color_to_rgb(color_str: str) -> tuple:
    color_str = color_str.strip().lower()
    names = {
        "white": (255, 255, 255),
        "yellow": (255, 255, 0),
        "red": (255, 0, 0),
        "green": (0, 255, 0),
        "black": (0, 0, 0),
        "blue": (0, 0, 255),
        "白 (white)": (255, 255, 255),
        "黄 (yellow)": (255, 255, 0),
        "赤 (red)": (255, 0, 0),
        "緑 (green)": (0, 255, 0),
        "黒 (black)": (0, 0, 0),
        "青 (blue)": (0, 0, 255)
    }
    if color_str in names:
        return names[color_str]
    if "," in color_str:
        parts = color_str.split(",")
        if len(parts) == 3:
            try:
                r = min(255, max(0, int(parts[0].strip())))
                g = min(255, max(0, int(parts[1].strip())))
                b = min(255, max(0, int(parts[2].strip())))
                return (r, g, b)
            except ValueError: pass
    clean_hex = color_str.lstrip("#")
    if len(clean_hex) == 3:
        clean_hex = "".join([c*2 for c in clean_hex])
    if len(clean_hex) == 6:
        try:
            r = int(clean_hex[0:2], 16)
            g = int(clean_hex[2:4], 16)
            b = int(clean_hex[4:6], 16)
            return (r, g, b)
        except ValueError: pass
    return (255, 255, 255)

def rgb_to_hsb(r, g, b):
    h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
    return int(h * 360), int(s * 100), int(v * 100)

def hsb_to_rgb(h, s, b):
    r, g, bl = colorsys.hsv_to_rgb(h / 360.0, s / 100.0, b / 100.0)
    return int(r * 255), int(g * 255), int(bl * 255)

def generate_sb_gradient_pure_pil(hue):
    img = PIL.Image.new("RGB", (90, 90))
    pixels = img.load()
    h_val = hue / 360.0
    for y in range(90):
        v = 1.0 - (y / 89.0)
        for x in range(90):
            s = x / 89.0
            r, g, b = colorsys.hsv_to_rgb(h_val, s, v)
            pixels[x, y] = (int(r * 255), int(g * 255), int(b * 255))
    return img.resize((180, 180), PIL.Image.Resampling.BILINEAR)

def generate_hue_gradient():
    img = PIL.Image.new("RGB", (20, 180))
    pixels = img.load()
    for y in range(180):
        h = y / 179.0
        r, g, b = colorsys.hsv_to_rgb(h, 1.0, 1.0)
        color = (int(r * 255), int(g * 255), int(b * 255))
        for x in range(20):
            pixels[x, y] = color
    return img

def rgb_to_ass_hex(rgb: tuple) -> str:
    r, g, b = rgb
    return f"&H{b:02X}{g:02X}{r:02X}"

def format_srt_time(t):
    h, m = divmod(t, 3600)
    m, s = divmod(m, 60)
    sec, ms = divmod(s, 1)
    return f"{int(h):02d}:{int(m):02d}:{int(sec):02d},{int(ms*1000):03d}"

class ColorPickerDialog(ctk.CTkToplevel):
    def __init__(self, parent, title="色を選択", initial_color="#FFFF00"):
        super().__init__(parent)
        self.title(title)
        self.geometry("630x390")
        self.resizable(False, False)
        
        self.parent = parent
        self.result = None
        self.initial_color = initial_color.upper()
        
        # Parse initial color
        rgb = parse_color_to_rgb(initial_color)
        self.r_var = tk.IntVar(value=rgb[0])
        self.g_var = tk.IntVar(value=rgb[1])
        self.b_var = tk.IntVar(value=rgb[2])
        self.hex_var = tk.StringVar(value=initial_color.upper())
        
        # HSB variables
        h, s, b = rgb_to_hsb(rgb[0], rgb[1], rgb[2])
        self.h_var = tk.IntVar(value=h)
        self.s_var = tk.IntVar(value=s)
        self.v_var = tk.IntVar(value=b)
        
        # Center window
        self.grab_set()
        x = parent.winfo_x() + (parent.winfo_width() - 630) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 390) // 2
        self.geometry(f"630x390+{x}+{y}")
        
        # Main layout
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)
        main_frame.grid_columnconfigure(0, weight=0)
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_columnconfigure(2, weight=0)
        main_frame.grid_rowconfigure(0, weight=1)
        
        # Column 0: Canvases (SB Canvas + Hue Canvas)
        left_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(5, 10), pady=5)
        
        canvas_container = ctk.CTkFrame(left_frame, fg_color="transparent")
        canvas_container.pack(fill="x")
        
        self.sb_canvas = tk.Canvas(canvas_container, width=180, height=180, highlightthickness=1, highlightbackground="gray40", bd=0, cursor="crosshair")
        self.sb_canvas.pack(side="left")
        self.sb_canvas.bind("<Button-1>", self.on_sb_click)
        self.sb_canvas.bind("<B1-Motion>", self.on_sb_drag)
        
        self.hue_canvas = tk.Canvas(canvas_container, width=20, height=180, highlightthickness=1, highlightbackground="gray40", bd=0, cursor="sb_v_double_arrow")
        self.hue_canvas.pack(side="left", padx=(10, 0))
        self.hue_canvas.bind("<Button-1>", self.on_hue_click)
        self.hue_canvas.bind("<B1-Motion>", self.on_hue_drag)
        
        # HEX input below canvases
        hex_row = ctk.CTkFrame(left_frame, fg_color="transparent")
        hex_row.pack(fill="x", pady=(15, 0))
        ctk.CTkLabel(hex_row, text="#", font=ctk.CTkFont(size=14, weight="bold")).pack(side="left")
        self.hex_entry = ctk.CTkEntry(hex_row, textvariable=self.hex_var, width=120, font=("Consolas", 12))
        self.hex_entry.pack(side="left", padx=5)
        self.hex_entry.bind("<KeyRelease>", self.on_hex_edit)
        
        # Column 1: Sliders
        mid_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        mid_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 10), pady=5)
        
        ctk.CTkLabel(mid_frame, text="RGB カラー調整:", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w", pady=(0, 2))
        
        # Red
        r_f = ctk.CTkFrame(mid_frame, fg_color="transparent")
        r_f.pack(fill="x", pady=2)
        ctk.CTkLabel(r_f, text="R:", width=15).pack(side="left")
        self.r_slider = ctk.CTkSlider(r_f, from_=0, to=255, variable=self.r_var, command=self.on_rgb_slider_edit)
        self.r_slider.pack(side="left", fill="x", expand=True, padx=5)
        self.r_lbl = ctk.CTkLabel(r_f, text=str(self.r_var.get()), width=25)
        self.r_lbl.pack(side="right")
        
        # Green
        g_f = ctk.CTkFrame(mid_frame, fg_color="transparent")
        g_f.pack(fill="x", pady=2)
        ctk.CTkLabel(g_f, text="G:", width=15).pack(side="left")
        self.g_slider = ctk.CTkSlider(g_f, from_=0, to=255, variable=self.g_var, command=self.on_rgb_slider_edit)
        self.g_slider.pack(side="left", fill="x", expand=True, padx=5)
        self.g_lbl = ctk.CTkLabel(g_f, text=str(self.g_var.get()), width=25)
        self.g_lbl.pack(side="right")
        
        # Blue
        b_f = ctk.CTkFrame(mid_frame, fg_color="transparent")
        b_f.pack(fill="x", pady=2)
        ctk.CTkLabel(b_f, text="B:", width=15).pack(side="left")
        self.b_slider = ctk.CTkSlider(b_f, from_=0, to=255, variable=self.b_var, command=self.on_rgb_slider_edit)
        self.b_slider.pack(side="left", fill="x", expand=True, padx=5)
        self.b_lbl = ctk.CTkLabel(b_f, text=str(self.b_var.get()), width=25)
        self.b_lbl.pack(side="right")
        
        ctk.CTkLabel(mid_frame, text="HSB カラー調整:", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w", pady=(10, 2))
        
        # Hue slider
        h_f = ctk.CTkFrame(mid_frame, fg_color="transparent")
        h_f.pack(fill="x", pady=2)
        ctk.CTkLabel(h_f, text="H:", width=15).pack(side="left")
        self.h_slider = ctk.CTkSlider(h_f, from_=0, to=360, variable=self.h_var, command=self.on_hsb_slider_edit)
        self.h_slider.pack(side="left", fill="x", expand=True, padx=5)
        self.h_lbl = ctk.CTkLabel(h_f, text=f"{self.h_var.get()}°", width=30)
        self.h_lbl.pack(side="right")
        
        # Saturation slider
        s_f = ctk.CTkFrame(mid_frame, fg_color="transparent")
        s_f.pack(fill="x", pady=2)
        ctk.CTkLabel(s_f, text="S:", width=15).pack(side="left")
        self.s_slider = ctk.CTkSlider(s_f, from_=0, to=100, variable=self.s_var, command=self.on_hsb_slider_edit)
        self.s_slider.pack(side="left", fill="x", expand=True, padx=5)
        self.s_lbl = ctk.CTkLabel(s_f, text=f"{self.s_var.get()}%", width=30)
        self.s_lbl.pack(side="right")
        
        # Brightness slider
        v_f = ctk.CTkFrame(mid_frame, fg_color="transparent")
        v_f.pack(fill="x", pady=2)
        ctk.CTkLabel(v_f, text="B:", width=15).pack(side="left")
        self.v_slider = ctk.CTkSlider(v_f, from_=0, to=100, variable=self.v_var, command=self.on_hsb_slider_edit)
        self.v_slider.pack(side="left", fill="x", expand=True, padx=5)
        self.v_lbl = ctk.CTkLabel(v_f, text=f"{self.v_var.get()}%", width=30)
        self.v_lbl.pack(side="right")
        
        # Column 2: Right side (OK, Cancel, Swatches)
        right_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        right_frame.grid(row=0, column=2, sticky="nsew", padx=(10, 5), pady=5)
        
        comp_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        comp_frame.pack(fill="x", pady=(0, 10))
        
        preview_container = ctk.CTkFrame(comp_frame, width=80, height=60, border_width=1, border_color="gray40")
        preview_container.pack(side="left", padx=(0, 10))
        preview_container.pack_propagate(False)
        
        self.new_preview = ctk.CTkLabel(preview_container, text="", fg_color=initial_color, height=30)
        self.new_preview.pack(fill="x")
        self.curr_preview = ctk.CTkLabel(preview_container, text="", fg_color=initial_color, height=30)
        self.curr_preview.pack(fill="x")
        
        labels_container = ctk.CTkFrame(comp_frame, fg_color="transparent")
        labels_container.pack(side="left", fill="both", expand=True)
        ctk.CTkLabel(labels_container, text="新しい色", font=ctk.CTkFont(size=11), anchor="w").pack(fill="x", pady=(2, 2))
        ctk.CTkLabel(labels_container, text="現在の色", font=ctk.CTkFont(size=11), anchor="w").pack(fill="x")
        
        p_color = "#1a73e8"
        h_color = "#155cb4"
        
        self.ok_btn = ctk.CTkButton(right_frame, text="OK", fg_color=p_color, hover_color=h_color, height=32, command=self.ok)
        self.ok_btn.pack(fill="x", pady=2)
        
        self.cancel_btn = ctk.CTkButton(right_frame, text="キャンセル", fg_color="transparent", border_width=1, height=32, command=self.cancel)
        self.cancel_btn.pack(fill="x", pady=2)
        
        self.add_swatch_btn = ctk.CTkButton(right_frame, text="スウォッチに追加", fg_color="gray30", hover_color="gray40", height=32, command=self.add_to_swatches)
        self.add_swatch_btn.pack(fill="x", pady=(2, 10))
        
        ctk.CTkLabel(right_frame, text="カラースウォッチ:", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w")
        self.swatches_container = ctk.CTkFrame(right_frame, fg_color="transparent")
        self.swatches_container.pack(fill="both", expand=True, pady=2)
        
        self.draw_swatches()
        
        # Render canvas images and indicators
        self.update_idletasks()
        self.draw_hue_canvas()
        self.update_sb_canvas()
        
        self.protocol("WM_DELETE_WINDOW", self.cancel)
        
    def draw_hue_canvas(self):
        self.hue_img = generate_hue_gradient()
        self.hue_photo = PIL.ImageTk.PhotoImage(self.hue_img)
        self.hue_canvas.create_image(0, 0, anchor="nw", image=self.hue_photo)
        self.update_hue_indicator()
        
    def update_hue_indicator(self):
        self.hue_canvas.delete("indicator")
        h = self.h_var.get()
        y = int((h / 360.0) * 179)
        self.hue_canvas.create_line(0, y, 20, y, fill="white", width=2, tags="indicator")
        self.hue_canvas.create_line(0, y-1, 20, y-1, fill="black", width=1, tags="indicator")
        self.hue_canvas.create_line(0, y+1, 20, y+1, fill="black", width=1, tags="indicator")

    def update_sb_canvas(self):
        h = self.h_var.get()
        self.sb_img = generate_sb_gradient_pure_pil(h)
        self.sb_photo = PIL.ImageTk.PhotoImage(self.sb_img)
        self.sb_canvas.create_image(0, 0, anchor="nw", image=self.sb_photo)
        self.update_sb_indicator()
        
    def update_sb_indicator(self):
        self.sb_canvas.delete("indicator")
        s = self.s_var.get()
        v = self.v_var.get()
        x = int((s / 100.0) * 179)
        y = int((1.0 - (v / 100.0)) * 179)
        color = "white" if v < 50 else "black"
        self.sb_canvas.create_oval(x-4, y-4, x+4, y+4, outline=color, width=2, tags="indicator")

    def on_hue_click(self, event):
        self.handle_hue_event(event.y)
        
    def on_hue_drag(self, event):
        self.handle_hue_event(event.y)
        
    def handle_hue_event(self, y):
        y = max(0, min(179, y))
        hue = int((y / 179.0) * 360)
        self.h_var.set(hue)
        self.update_from_hsb()

    def on_sb_click(self, event):
        self.handle_sb_event(event.x, event.y)
        
    def on_sb_drag(self, event):
        self.handle_sb_event(event.x, event.y)
        
    def handle_sb_event(self, x, y):
        x = max(0, min(179, x))
        y = max(0, min(179, y))
        s = int((x / 179.0) * 100)
        v = int((1.0 - (y / 179.0)) * 100)
        self.s_var.set(s)
        self.v_var.set(v)
        self.update_from_hsb()
        
    def draw_swatches(self):
        for widget in self.swatches_container.winfo_children():
            widget.destroy()
            
        history = self.parent.config_data.get("color_history", [])
        while len(history) < 16:
            default_colors = ["#FFFFFF", "#000000", "#FFFF00", "#FF0000", "#00FF00", "#0000FF", "#00FFFF", "#FF00FF",
                              "#FFA500", "#800080", "#A52A2A", "#808080", "#C0C0C0", "#008000", "#008080", "#000080"]
            history.append(default_colors[len(history)])
            
        for i in range(16):
            row = i // 8
            col = i % 8
            color_hex = history[i]
            btn = ctk.CTkButton(
                self.swatches_container, text="", fg_color=color_hex, hover_color=color_hex,
                width=18, height=18, corner_radius=1, border_width=1, border_color="gray50",
                command=lambda c=color_hex: self.select_preset(c)
            )
            btn.grid(row=row, column=col, padx=2, pady=2)
            
    def add_to_swatches(self):
        color_hex = self.hex_var.get().strip().upper()
        if not color_hex.startswith("#"):
            color_hex = f"#{color_hex}"
        if len(color_hex) != 7:
            return
            
        history = self.parent.config_data.get("color_history", [])
        if color_hex in history:
            history.remove(color_hex)
        history.insert(0, color_hex)
        self.parent.config_data["color_history"] = history[:16]
        
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.json")
        try:
            import json
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(self.parent.config_data, f, indent=4, ensure_ascii=False)
        except Exception: pass
        self.draw_swatches()
        
    def select_preset(self, color_hex):
        rgb = parse_color_to_rgb(color_hex)
        self.r_var.set(rgb[0])
        self.g_var.set(rgb[1])
        self.b_var.set(rgb[2])
        self.update_from_rgb()
        
    def update_from_rgb(self):
        r = int(self.r_var.get())
        g = int(self.g_var.get())
        b = int(self.b_var.get())
        
        self.r_lbl.configure(text=str(r))
        self.g_lbl.configure(text=str(g))
        self.b_lbl.configure(text=str(b))
        
        h, s, val = rgb_to_hsb(r, g, b)
        self.h_var.set(h)
        self.s_var.set(s)
        self.v_var.set(val)
        self.h_lbl.configure(text=f"{h}°")
        self.s_lbl.configure(text=f"{s}%")
        self.v_lbl.configure(text=f"{val}%")
        
        hex_str = f"#{r:02X}{g:02X}{b:02X}"
        self.hex_var.set(hex_str)
        self.new_preview.configure(fg_color=hex_str)
        
        if hasattr(self, "hue_canvas"):
            self.update_hue_indicator()
        if hasattr(self, "sb_canvas"):
            self.update_sb_canvas()
        
    def update_from_hsb(self):
        h = int(self.h_var.get())
        s = int(self.s_var.get())
        val = int(self.v_var.get())
        
        self.h_lbl.configure(text=f"{h}°")
        self.s_lbl.configure(text=f"{s}%")
        self.v_lbl.configure(text=f"{val}%")
        
        r, g, b = hsb_to_rgb(h, s, val)
        self.r_var.set(r)
        self.g_var.set(g)
        self.b_var.set(b)
        self.r_lbl.configure(text=str(r))
        self.g_lbl.configure(text=str(g))
        self.b_lbl.configure(text=str(b))
        
        hex_str = f"#{r:02X}{g:02X}{b:02X}"
        self.hex_var.set(hex_str)
        self.new_preview.configure(fg_color=hex_str)
        
        if hasattr(self, "hue_canvas"):
            self.update_hue_indicator()
        if hasattr(self, "sb_canvas"):
            self.update_sb_canvas()
        
    def on_rgb_slider_edit(self, _):
        self.update_from_rgb()
        
    def on_hsb_slider_edit(self, _):
        self.update_from_hsb()
        
    def on_hex_edit(self, _):
        hex_str = self.hex_var.get().strip().lstrip("#")
        if len(hex_str) == 6:
            try:
                r = int(hex_str[0:2], 16)
                g = int(hex_str[2:4], 16)
                b = int(hex_str[4:6], 16)
                self.r_var.set(r)
                self.g_var.set(g)
                self.b_var.set(b)
                self.update_from_rgb()
            except ValueError: pass

    def ok(self):
        self.result = self.hex_var.get()
        self.destroy()
        
    def cancel(self):
        self.destroy()

class ProgressDialog(ctk.CTkToplevel):
    def __init__(self, parent, title="処理進行状況"):
        super().__init__(parent)
        self.title(title)
        self.geometry("500x200")
        self.resizable(False, False)
        self.parent = parent
        
        # モーダル化
        self.grab_set()
        
        # メインウィンドウの中央に配置
        x = parent.winfo_x() + (parent.winfo_width() - 500) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 200) // 2
        self.geometry(f"500x200+{x}+{y}")
        
        frame = ctk.CTkFrame(self)
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.label_status = ctk.CTkLabel(frame, text="初期化中...", font=ctk.CTkFont(size=14, weight="bold"))
        self.label_status.pack(anchor="w", pady=(0, 10))
        
        self.progress_bar = ctk.CTkProgressBar(frame, width=460)
        self.progress_bar.pack(fill="x", pady=10)
        self.progress_bar.set(0.0)
        
        self.label_percent = ctk.CTkLabel(frame, text="0%", font=ctk.CTkFont(size=12))
        self.label_percent.pack(anchor="e", pady=(0, 15))
        
        self.cancel_btn = ctk.CTkButton(frame, text="キャンセル", fg_color="red", hover_color="darkred", width=120, command=self.on_cancel)
        self.cancel_btn.pack()
        
        self.protocol("WM_DELETE_WINDOW", self.on_cancel)
        
    def update_progress(self, value, text):
        self.label_status.configure(text=text)
        self.progress_bar.set(value)
        self.label_percent.configure(text=f"{int(value * 100)}%")
        
    def on_cancel(self):
        if messagebox.askyesno("確認", "本当に処理をキャンセルしますか？"):
            self.parent.cancel_processing()
            self.destroy()

# CustomTkinterの設定
ctk.set_appearance_mode("System")  # 開発環境のシステム設定に追従
ctk.set_default_color_theme("blue")

class LongVideoClipperApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("長尺動画切り抜きツール (無音カット＆挨拶カット)")
        self.geometry("750x850")
        self.load_config()
        
        # UI更新スロットリング用
        self._last_ui_update = 0.0
        
        # 処理中フラグ
        self.is_processing = False
        self.is_cancelled = False
        self.current_process = None
        self.progress_dialog = None
        
        # UIレイアウトの作成
        self.create_widgets()
        
        # FFmpegの存在確認
        self.ffmpeg_path = self.get_ffmpeg_path()
        self.ffprobe_path = self.get_ffprobe_path()
        
        if not self.ffmpeg_path:
            self.log("【警告】FFmpeg が見つかりません。")
            self.log("システム環境変数 PATH に追加するか、本ツールの _internal フォルダに ffmpeg.exe を配置してください。")
            messagebox.showwarning("警告", "FFmpeg が見つかりません。動画処理を実行する前に配置してください。")
        else:
            self.log(f"FFmpeg パス: {self.ffmpeg_path}")
            if self.ffprobe_path:
                self.log(f"FFprobe パス: {self.ffprobe_path}")
            else:
                self.log("【情報】FFprobe がありません。動画の長さ取得には FFmpeg を使用します。")

    def get_ffmpeg_path(self):
        # 1. PATHの確認
        try:
            subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return "ffmpeg"
        except FileNotFoundError:
            pass
        
        # 2. カレントディレクトリの確認
        if os.path.exists("ffmpeg.exe"):
            return os.path.abspath("ffmpeg.exe")
            
        # 3. _internal フォルダの確認 (PyInstallerビルド環境)
        if getattr(sys, 'frozen', False):
            exe_dir = os.path.dirname(sys.executable)
            ffmpeg_exe = os.path.join(exe_dir, "_internal", "ffmpeg.exe")
            if os.path.exists(ffmpeg_exe):
                return ffmpeg_exe
        return None

    def get_ffprobe_path(self):
        # 1. PATHの確認
        try:
            subprocess.run(["ffprobe", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return "ffprobe"
        except FileNotFoundError:
            pass
        
        # 2. カレントディレクトリの確認
        if os.path.exists("ffprobe.exe"):
            return os.path.abspath("ffprobe.exe")
            
        # 3. _internal フォルダの確認
        if getattr(sys, 'frozen', False):
            exe_dir = os.path.dirname(sys.executable)
            ffprobe_exe = os.path.join(exe_dir, "_internal", "ffprobe.exe")
            if os.path.exists(ffprobe_exe):
                return ffprobe_exe
        return None

    def get_gpu_encoder(self):
        if not self.ffmpeg_path:
            return "libx264"
        try:
            result = subprocess.run([self.ffmpeg_path, "-encoders"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors='ignore')
            encoders_text = result.stdout
            
            if "h264_nvenc" in encoders_text:
                self.safe_log("【GPU検出】NVIDIA NVENC エンコーダーを使用します。")
                return "h264_nvenc"
            elif "h264_qsv" in encoders_text:
                self.safe_log("【GPU検出】Intel QSV エンコーダーを使用します。")
                return "h264_qsv"
            elif "h264_amf" in encoders_text:
                self.safe_log("【GPU検出】AMD AMF エンコーダーを使用します。")
                return "h264_amf"
        except Exception as e:
            self.safe_log(f"【GPU検出エラー】GPU検出に失敗しました（CPUを使用します）: {e}")
        return "libx264"

    def create_widgets(self):
        # グリッド配置の設定
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(5, weight=1) # ログ表示部分を伸縮可能に
        
        # ----------------------------------------------------
        # 1. ファイル選択エリア
        # ----------------------------------------------------
        file_frame = ctk.CTkFrame(self)
        file_frame.grid(row=0, column=0, padx=20, pady=10, sticky="ew")
        file_frame.grid_columnconfigure(1, weight=1)
        
        self.input_label = ctk.CTkLabel(file_frame, text="入力動画:")
        self.input_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        
        self.input_entry = ctk.CTkEntry(file_frame, placeholder_text="動画ファイルを選択してください...")
        self.input_entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        
        self.input_btn = ctk.CTkButton(file_frame, text="参照", width=80, command=self.select_input_file)
        self.input_btn.grid(row=0, column=2, padx=10, pady=5)
        
        self.output_label = ctk.CTkLabel(file_frame, text="出力動画:")
        self.output_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        
        self.output_entry = ctk.CTkEntry(file_frame, placeholder_text="保存先を指定してください...")
        self.output_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        
        self.output_btn = ctk.CTkButton(file_frame, text="参照", width=80, command=self.select_output_file)
        self.output_btn.grid(row=1, column=2, padx=10, pady=5)

        # ----------------------------------------------------
        # 2. 無音検出設定エリア
        # ----------------------------------------------------
        silence_frame = ctk.CTkFrame(self)
        silence_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        silence_frame.grid_columnconfigure((1, 3), weight=1)
        
        # タイトルラベル
        silence_title = ctk.CTkLabel(silence_frame, text="■ 無音検出の設定", font=ctk.CTkFont(weight="bold"))
        silence_title.grid(row=0, column=0, columnspan=4, padx=10, pady=5, sticky="w")
        
        # 音量閾値 (dB)
        self.db_label = ctk.CTkLabel(silence_frame, text="音量閾値 (dB):")
        self.db_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        
        self.db_slider = ctk.CTkSlider(silence_frame, from_=-60, to=-10, number_of_steps=50, command=self.update_db_label)
        self.db_slider.set(self.config_data.get("db_threshold", -30))
        self.db_slider.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        
        self.db_val_label = ctk.CTkLabel(silence_frame, text="-30 dB", width=60)
        self.db_val_label.grid(row=1, column=2, padx=10, pady=5, sticky="w")
        
        # 最小無音時間 (秒)
        self.duration_label = ctk.CTkLabel(silence_frame, text="最小無音時間 (秒):")
        self.duration_label.grid(row=2, column=0, padx=10, pady=5, sticky="w")
        
        self.duration_slider = ctk.CTkSlider(silence_frame, from_=0.1, to=5.0, number_of_steps=49, command=self.update_duration_label)
        self.duration_slider.set(self.config_data.get("min_silence_duration", 0.5))
        self.duration_slider.grid(row=2, column=1, padx=10, pady=5, sticky="ew")
        
        self.duration_val_label = ctk.CTkLabel(silence_frame, text="0.50 秒", width=60)
        self.duration_val_label.grid(row=2, column=2, padx=10, pady=5, sticky="w")
        
        # マージン（カットする前後の余裕秒数）
        self.margin_label = ctk.CTkLabel(silence_frame, text="カット余白 (秒):")
        self.margin_label.grid(row=1, column=3, padx=10, pady=5, sticky="w")
        
        self.margin_entry = ctk.CTkEntry(silence_frame, width=70)
        self.margin_entry.insert(0, self.config_data.get("margin", "0.1"))
        self.margin_entry.grid(row=1, column=4, padx=10, pady=5, sticky="w")
        
        # 最小有音キープ時間（これより短い有音区間はノイズとしてカット）
        self.keep_label = ctk.CTkLabel(silence_frame, text="最小有音キープ (秒):")
        self.keep_label.grid(row=2, column=3, padx=10, pady=5, sticky="w")
        
        self.keep_entry = ctk.CTkEntry(silence_frame, width=70)
        self.keep_entry.insert(0, self.config_data.get("min_keep", "0.2"))
        self.keep_entry.grid(row=2, column=4, padx=10, pady=5, sticky="w")
        
        # 音量最適化のチェックボックス (row 3)
        self.audio_norm_enable = ctk.CTkCheckBox(silence_frame, text="音量を均一化しYouTube基準に適正化する")
        if self.config_data.get("audio_norm", True): self.audio_norm_enable.select()
        else: self.audio_norm_enable.deselect()
        self.audio_norm_enable.grid(row=3, column=0, columnspan=3, padx=10, pady=5, sticky="w")
        
        # フィラー言葉自動カット (row 3, column 3)
        self.filler_cut_enable = ctk.CTkCheckBox(silence_frame, text="フィラー言葉(えーっと等)を自動カット", command=self.toggle_greeting_widgets)
        self.filler_cut_enable.grid(row=3, column=3, columnspan=2, padx=10, pady=5, sticky="w")
        if self.config_data.get("filler_cut", False): self.filler_cut_enable.select()
        
        # 大声自動ズーム (row 4)
        self.loud_zoom_enable = ctk.CTkCheckBox(silence_frame, text="大声の瞬間に画面を自動ズームする")
        self.loud_zoom_enable.grid(row=4, column=0, columnspan=3, padx=10, pady=5, sticky="w")
        if self.config_data.get("loud_zoom", False): self.loud_zoom_enable.select()
        
        # SRT & JSX 出力 (row 4, column 3)
        self.sub_export_enable = ctk.CTkCheckBox(silence_frame, text="SRT字幕＆AE用スクリプト(.jsx)を出力", command=self.toggle_greeting_widgets)
        if self.config_data.get("sub_export", True): self.sub_export_enable.select()
        else: self.sub_export_enable.deselect()
        self.sub_export_enable.grid(row=4, column=3, columnspan=2, padx=10, pady=5, sticky="w")

        # ----------------------------------------------------
        # 3. 挨拶カット設定エリア
        # ----------------------------------------------------
        greeting_frame = ctk.CTkFrame(self)
        greeting_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        greeting_frame.grid_columnconfigure((1, 2), weight=1)
        
        self.greeting_title = ctk.CTkLabel(greeting_frame, text="■ 挨拶カットの設定", font=ctk.CTkFont(weight="bold"))
        self.greeting_title.grid(row=0, column=0, columnspan=3, padx=10, pady=5, sticky="w")
        
        self.greeting_enable = ctk.CTkCheckBox(greeting_frame, text="挨拶カットを有効にする", command=self.toggle_greeting_widgets)
        self.greeting_enable.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        if self.config_data.get("greeting_enable", False): self.greeting_enable.select()
        
        # カット方法のラジオボタン
        self.greeting_mode = ctk.StringVar(value="manual")
        
        self.radio_manual = ctk.CTkRadioButton(greeting_frame, text="手動で秒数指定 (冒頭カット)", variable=self.greeting_mode, value="manual", command=self.toggle_greeting_widgets)
        self.radio_manual.grid(row=1, column=1, padx=10, pady=5, sticky="w")
        
        self.radio_whisper = ctk.CTkRadioButton(greeting_frame, text="Whisper音声認識で自動検出", variable=self.greeting_mode, value="whisper", command=self.toggle_greeting_widgets)
        self.radio_whisper.grid(row=1, column=2, padx=10, pady=5, sticky="w")
        
        # 手動カット秒数入力
        self.sec_label = ctk.CTkLabel(greeting_frame, text="冒頭カット秒数:")
        self.sec_label.grid(row=2, column=0, padx=10, pady=5, sticky="w")
        
        self.sec_entry = ctk.CTkEntry(greeting_frame, width=80)
        self.sec_entry.insert(0, self.config_data.get("greeting_sec", "5.0"))
        self.sec_entry.grid(row=2, column=1, padx=10, pady=5, sticky="w")
        
        # Whisper設定 (モデル選択)
        self.model_label = ctk.CTkLabel(greeting_frame, text="Whisperモデル:")
        self.model_label.grid(row=2, column=2, padx=10, pady=5, sticky="w")
        
        self.model_combo = ctk.CTkComboBox(greeting_frame, values=["tiny", "base", "small"], width=100)
        self.model_combo.set(self.config_data.get("whisper_model", "base"))
        self.model_combo.grid(row=2, column=2, padx=110, pady=5, sticky="w")
        
        # 初期状態でウィジェットの有効・無効化を適用
        self.toggle_greeting_widgets()

        # ----------------------------------------------------
        # 字幕のスタイル設定
        # ----------------------------------------------------
        style_frame = ctk.CTkFrame(self)
        style_frame.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        style_frame.grid_columnconfigure((1, 3, 5), weight=1)
        
        style_title = ctk.CTkLabel(style_frame, text="■ 字幕・文字のスタイル設定", font=ctk.CTkFont(weight="bold"))
        style_title.grid(row=0, column=0, columnspan=6, padx=10, pady=5, sticky="w")
        
        # Row 1: Burn Subtitles Checkbox & Font Name
        self.sub_burn_enable = ctk.CTkCheckBox(style_frame, text="動画に字幕を焼き付ける")
        if self.config_data.get("sub_burn_enable", True):
            self.sub_burn_enable.select()
        else:
            self.sub_burn_enable.deselect()
        self.sub_burn_enable.grid(row=1, column=0, columnspan=2, padx=10, pady=5, sticky="w")
        
        ctk.CTkLabel(style_frame, text="フォント:").grid(row=1, column=2, padx=10, pady=5, sticky="w")
        
        import tkinter.font as tkfont
        try: all_families = set(tkfont.families(self))
        except Exception: all_families = set()
        preferred_fonts = [
            "MS Gothic", "ＭＳ ゴシック", "MS PGothic", "ＭＳ Ｐゴシック",
            "Meiryo", "メイリオ", "Yu Gothic", "游ゴシック", "Segoe UI", "Arial"
        ]
        font_list = [f for f in preferred_fonts if f in all_families]
        other_fonts = sorted([f for f in all_families if not f.startswith("@") and f not in font_list])
        font_list.extend(other_fonts)
        if not font_list:
            font_list = ["MS Gothic", "Meiryo", "Yu Gothic"]
        font_list = font_list[:30]
        
        self.sub_font_name_var = ctk.StringVar(value=self.config_data.get("sub_font_name", "Meiryo" if "Meiryo" in font_list else font_list[0]))
        self.sub_font_combo = ctk.CTkComboBox(style_frame, values=font_list, variable=self.sub_font_name_var, width=150)
        self.sub_font_combo.grid(row=1, column=3, padx=10, pady=5, sticky="w")
        
        # Size
        ctk.CTkLabel(style_frame, text="サイズ:").grid(row=1, column=4, padx=10, pady=5, sticky="w")
        self.sub_font_size_var = ctk.StringVar(value=self.config_data.get("sub_font_size", "48"))
        self.sub_font_size_menu = ctk.CTkOptionMenu(style_frame, values=["24", "32", "36", "40", "48", "64", "72", "96"], variable=self.sub_font_size_var, width=80)
        self.sub_font_size_menu.grid(row=1, column=5, padx=10, pady=5, sticky="w")
        
        # Row 2: Text Color & Outline Color
        ctk.CTkLabel(style_frame, text="文字色:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        color_sub_row = ctk.CTkFrame(style_frame, fg_color="transparent")
        color_sub_row.grid(row=2, column=1, padx=10, pady=5, sticky="w")
        self.sub_color_var = ctk.StringVar(value=self.config_data.get("sub_color", "#FFFF00"))
        self.sub_color_entry = ctk.CTkEntry(color_sub_row, textvariable=self.sub_color_var, width=80)
        self.sub_color_entry.pack(side="left")
        self.sub_color_preview = ctk.CTkLabel(color_sub_row, text="", width=24, height=24, fg_color=self.sub_color_var.get(), corner_radius=4, cursor="hand2")
        self.sub_color_preview.pack(side="left", padx=(5, 0))
        self.sub_color_preview.bind("<Button-1>", lambda _: self.open_color_picker("color"))
        
        # Outline Color
        ctk.CTkLabel(style_frame, text="フチ色:").grid(row=2, column=2, padx=10, pady=5, sticky="w")
        outline_sub_row = ctk.CTkFrame(style_frame, fg_color="transparent")
        outline_sub_row.grid(row=2, column=3, padx=10, pady=5, sticky="w")
        self.sub_outline_color_var = ctk.StringVar(value=self.config_data.get("sub_outline_color", "#000000"))
        self.sub_outline_color_entry = ctk.CTkEntry(outline_sub_row, textvariable=self.sub_outline_color_var, width=80)
        self.sub_outline_color_entry.pack(side="left")
        self.sub_outline_color_preview = ctk.CTkLabel(outline_sub_row, text="", width=24, height=24, fg_color=self.sub_outline_color_var.get(), corner_radius=4, cursor="hand2")
        self.sub_outline_color_preview.pack(side="left", padx=(5, 0))
        self.sub_outline_color_preview.bind("<Button-1>", lambda _: self.open_color_picker("outline"))
        
        # Outline Width
        ctk.CTkLabel(style_frame, text="フチ太さ:").grid(row=2, column=4, padx=10, pady=5, sticky="w")
        self.sub_outline_width_var = ctk.StringVar(value=self.config_data.get("sub_outline_width", "3.0"))
        self.sub_outline_width_menu = ctk.CTkOptionMenu(style_frame, values=["0.0", "1.0", "2.0", "3.0", "4.0", "5.0", "6.0", "8.0", "10.0"], variable=self.sub_outline_width_var, width=80)
        self.sub_outline_width_menu.grid(row=2, column=5, padx=10, pady=5, sticky="w")
        
        # Row 3: Shadow Depth, Shadow Alpha & Vertical Margin
        ctk.CTkLabel(style_frame, text="影の深さ:").grid(row=3, column=0, padx=10, pady=5, sticky="w")
        self.sub_shadow_depth_var = ctk.StringVar(value=self.config_data.get("sub_shadow_depth", "2.0"))
        self.sub_shadow_depth_menu = ctk.CTkOptionMenu(style_frame, values=["0.0", "1.0", "2.0", "3.0", "4.0", "5.0", "8.0", "10.0"], variable=self.sub_shadow_depth_var, width=80)
        self.sub_shadow_depth_menu.grid(row=3, column=1, padx=10, pady=5, sticky="w")
        
        ctk.CTkLabel(style_frame, text="影透明度:").grid(row=3, column=2, padx=10, pady=5, sticky="w")
        self.sub_shadow_alpha_var = ctk.DoubleVar(value=self.config_data.get("sub_shadow_alpha", 0.8))
        self.sub_shadow_alpha_slider = ctk.CTkSlider(style_frame, from_=0.0, to=1.0, number_of_steps=100, variable=self.sub_shadow_alpha_var, width=120)
        self.sub_shadow_alpha_slider.grid(row=3, column=3, padx=10, pady=5, sticky="w")
        
        # Position Y
        ctk.CTkLabel(style_frame, text="位置 Y (px):").grid(row=3, column=4, padx=10, pady=5, sticky="w")
        self.sub_margin_v_var = ctk.StringVar(value=self.config_data.get("sub_margin_v", "80"))
        self.sub_margin_v_entry = ctk.CTkEntry(style_frame, textvariable=self.sub_margin_v_var, width=80)
        self.sub_margin_v_entry.grid(row=3, column=5, padx=10, pady=5, sticky="w")
        
        # Row 4: Bold, Italic Checkboxes & Alignment
        self.sub_bold_var = ctk.BooleanVar(value=self.config_data.get("sub_bold", True))
        self.sub_bold_checkbox = ctk.CTkCheckBox(style_frame, text="太字 (Bold)", variable=self.sub_bold_var)
        self.sub_bold_checkbox.grid(row=4, column=0, columnspan=2, padx=10, pady=5, sticky="w")
        
        self.sub_italic_var = ctk.BooleanVar(value=self.config_data.get("sub_italic", False))
        self.sub_italic_checkbox = ctk.CTkCheckBox(style_frame, text="斜体 (Italic)", variable=self.sub_italic_var)
        self.sub_italic_checkbox.grid(row=4, column=2, padx=10, pady=5, sticky="w")
        
        ctk.CTkLabel(style_frame, text="配置:").grid(row=4, column=3, padx=10, pady=5, sticky="w")
        self.sub_alignment_var = ctk.StringVar(value=self.config_data.get("sub_alignment", "中央寄せ"))
        self.sub_alignment_btn = ctk.CTkSegmentedButton(style_frame, values=["左寄せ", "中央寄せ", "右寄せ"], variable=self.sub_alignment_var, width=180)
        self.sub_alignment_btn.grid(row=4, column=4, columnspan=2, padx=10, pady=5, sticky="w")

        # ----------------------------------------------------
        # 4. 実行＆進捗エリア
        # ----------------------------------------------------
        action_frame = ctk.CTkFrame(self)
        action_frame.grid(row=4, column=0, padx=20, pady=10, sticky="ew")
        action_frame.grid_columnconfigure(0, weight=1)
        
        self.run_btn = ctk.CTkButton(action_frame, text="切り抜き処理を開始する", font=ctk.CTkFont(size=16, weight="bold"), height=40, command=self.start_processing)
        self.run_btn.grid(row=0, column=0, padx=20, pady=10, sticky="ew")
        
        self.progress_label = ctk.CTkLabel(action_frame, text="待機中...")
        self.progress_label.grid(row=1, column=0, padx=20, pady=2, sticky="w")
        
        self.progress_bar = ctk.CTkProgressBar(action_frame)
        self.progress_bar.set(0)
        self.progress_bar.grid(row=2, column=0, padx=20, pady=10, sticky="ew")

        # ----------------------------------------------------
        # 5. ログコンソールエリア
        # ----------------------------------------------------
        log_frame = ctk.CTkFrame(self)
        log_frame.grid(row=5, column=0, padx=20, pady=10, sticky="nsew")
        log_frame.grid_rowconfigure(1, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)
        
        log_title = ctk.CTkLabel(log_frame, text="ログ出力:")
        log_title.grid(row=0, column=0, padx=10, pady=2, sticky="w")
        
        self.log_textbox = ctk.CTkTextbox(log_frame, activate_scrollbars=True)
        self.log_textbox.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")

    # ----------------------------------------------------
    # UIコントロール関数
    # ----------------------------------------------------
    def update_db_label(self, value):
        self.db_val_label.configure(text=f"{int(value)} dB")
        
    def update_duration_label(self, value):
        self.duration_val_label.configure(text=f"{value:.2f} 秒")

    def toggle_greeting_widgets(self):
        enabled = self.greeting_enable.get()
        mode = self.greeting_mode.get()
        
        # フィラーカットやSRT出力が有効な場合もWhisperが必要になる
        whisper_needed = False
        try:
            whisper_needed = (
                (enabled and mode == "whisper") or
                self.filler_cut_enable.get() or
                self.sub_export_enable.get()
            )
        except AttributeError:
            # ウィジェット初期化中の例外を回避
            if enabled and mode == "whisper":
                whisper_needed = True
        
        if not enabled:
            self.radio_manual.configure(state="disabled")
            self.radio_whisper.configure(state="disabled")
            self.sec_label.configure(state="disabled")
            self.sec_entry.configure(state="disabled")
        else:
            self.radio_manual.configure(state="normal")
            self.radio_whisper.configure(state="normal")
            
            if mode == "manual":
                self.sec_label.configure(state="normal")
                self.sec_entry.configure(state="normal")
            else:
                self.sec_label.configure(state="disabled")
                self.sec_entry.configure(state="disabled")
                
        # いずれかでWhisperが必要な場合にコンボボックスを活性化
        if whisper_needed:
            self.model_label.configure(state="normal")
            self.model_combo.configure(state="normal")
        else:
            self.model_label.configure(state="disabled")
            self.model_combo.configure(state="disabled")

    def select_input_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("動画ファイル", "*.mp4 *.avi *.mkv *.mov"), ("すべてのファイル", "*.*")]
        )
        if file_path:
            self.input_entry.delete(0, "end")
            self.input_entry.insert(0, os.path.normpath(file_path))
            
            # デフォルトの出力ファイル名を自動生成
            dir_name = os.path.dirname(file_path)
            base_name = os.path.basename(file_path)
            name, ext = os.path.splitext(base_name)
            output_name = os.path.join(dir_name, f"{name}_clipped{ext}")
            self.output_entry.delete(0, "end")
            self.output_entry.insert(0, os.path.normpath(output_name))
    def process_video(self, input_path, output_path):

        import shutil
        # 一時作業フォルダの作成
        temp_dir = os.path.join(os.path.dirname(output_path), "kirinuki_temp")
        if os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
            except Exception:
                pass
        try:
            os.makedirs(temp_dir, exist_ok=True)
        except Exception as e:
            self.safe_log(f"【エラー】一時作業フォルダの作成に失敗しました: {e}")
            self.finish_processing(False, "一時フォルダ作成失敗")
            return

        try:
            # 各種設定値の取得
            db_threshold = int(self.db_slider.get())
            min_silence_duration = self.duration_slider.get()
            
            try:
                margin = float(self.margin_entry.get())
            except ValueError:
                margin = 0.1
                
            try:
                min_keep_duration = float(self.keep_entry.get())
            except ValueError:
                min_keep_duration = 0.2
                
            greeting_enabled = self.greeting_enable.get()
            greeting_mode = self.greeting_mode.get()
            
            self.safe_log("動画解析処理を開始します。")
            self.safe_update_ui(0.02, "動画情報を取得中...")
            
            # 1. 動画の長さを取得する
            total_duration = self.get_video_duration(input_path)
            if total_duration <= 0:
                self.safe_log("【エラー】動画の長さを取得できませんでした。")
                self.finish_processing(False, "動画解析失敗")
                return
            
            self.safe_log(f"動画の総長さ: {total_duration:.2f} 秒")
            self.safe_update_ui(0.05, "無音部分を検出中...")
            
            # 2. 全体無音検出の実行
            silence_ranges = self.detect_silence_ranges(input_path, db_threshold, min_silence_duration, total_duration)
            self.safe_log(f"検出された無音区間の数: {len(silence_ranges)}")
            
            # 3. 全体有音区間の算出
            keep_ranges = self.calculate_keep_ranges(silence_ranges, total_duration, margin, min_keep_duration)
            self.safe_log(f"カット前の有音区間の数: {len(keep_ranges)}")
            
            # 4. 挨拶カットの適用
            start_offset = 0.0
            if greeting_enabled:
                self.safe_update_ui(0.08, "挨拶部分を解析中...")
                if greeting_mode == "manual":
                    try:
                        start_offset = float(self.sec_entry.get())
                    except ValueError:
                        start_offset = 5.0
                    self.safe_log(f"挨拶カット(手動): 冒頭 {start_offset:.2f} 秒をカットします。")
                else:
                    whisper_model = self.model_combo.get()
                    self.safe_log("挨拶カット(Whisper): 冒頭の音声から挨拶位置を解析しています...")
                    start_offset = self.detect_greeting_by_whisper(input_path, whisper_model)
                    self.safe_log(f"挨拶カット(Whisper): 検出された挨拶の終了位置は {start_offset:.2f} 秒です。")
                
                # 有音区間の補正
                keep_ranges = self.apply_start_offset(keep_ranges, start_offset)
                self.safe_log(f"挨拶カット適用後の有音区間の数: {len(keep_ranges)}")

            if not keep_ranges:
                self.safe_log("【エラー】出力可能な有音区間がありませんでした。")
                self.finish_processing(False, "有音区間なし")
                return

            # GPUエンコーダーの自動検出
            gpu_encoder = self.get_gpu_encoder()

            # 5. 分割点（Split Points）の算出
            # 30分（1800秒）を目安とし、その付近で最も近い「無音区間」の開始秒数を分割点とする
            split_times = [0.0]
            target_interval = 1800.0  # 30分
            num_parts = int(total_duration // target_interval)
            
            for k in range(1, num_parts + 1):
                target_t = k * target_interval
                # ターゲット時刻から最も近い無音区間を探す（前後5分以内）
                best_split = None
                best_diff = 300.0  # 最大5分
                
                for s_start, s_end in silence_ranges:
                    diff = abs(s_start - target_t)
                    if diff < best_diff:
                        best_diff = diff
                        best_split = s_start
                
                if best_split is not None and best_split not in split_times:
                    split_times.append(best_split)
                else:
                    # 無音が見つからない場合はそのまま分割
                    split_times.append(target_t)
            
            if split_times[-1] < total_duration:
                split_times.append(total_duration)
                
            self.safe_log(f"動画を {len(split_times)-1} 個 of パートに分割して処理します。分割点: {split_times}")

            # 各パートの処理結果を格納するリスト
            part_videos = []
            combined_segments = []
            combined_loud_peaks = []
            output_accumulated_duration = 0.0  # タイムスタンプ結合用のオフセット

            # Whisper設定
            whisper_model = self.model_combo.get()
            need_whisper = self.filler_cut_enable.get() or self.sub_export_enable.get()
            loaded_model = None

            # 6. 各パートの処理ループ
            for i in range(len(split_times) - 1):
                if self.is_cancelled:
                    raise UserCancelledError("処理がキャンセルされました。")
                    
                p_start = split_times[i]
                p_end = split_times[i+1]
                p_len = p_end - p_start
                
                self.safe_log(f"\n--- パート {i+1} / {len(split_times)-1} の処理を開始します ({p_start:.2f}秒 〜 {p_end:.2f}秒) ---")
                
                # A. パート動画の一時無劣化切り出し
                part_video_path = os.path.join(temp_dir, f"part_{i}.mp4")
                cmd = [
                    self.ffmpeg_path, "-y", "-ss", f"{p_start:.3f}", "-to", f"{p_end:.3f}",
                    "-i", input_path, "-c", "copy", "-avoid_negative_ts", "make_zero",
                    part_video_path
                ]
                
                process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                self.current_process = process
                process.wait()
                self.current_process = None

                # B. このパートに含まれるローカル有音区間の抽出
                part_keep_ranges = []
                for k_start, k_end in keep_ranges:
                    if k_end > p_start and k_start < p_end:
                        local_start = max(0.0, k_start - p_start)
                        local_end = min(p_len, k_end - p_start)
                        if (local_end - local_start) >= min_keep_duration:
                            part_keep_ranges.append((local_start, local_end))
                
                if not part_keep_ranges:
                    self.safe_log(f"パート {i+1} には有音区間がないためスキップします。")
                    if os.path.exists(part_video_path):
                        try: os.remove(part_video_path)
                        except Exception: pass
                    continue

                # C. 有音区間のみの音声（WAV）を一時抽出 (Windowsコマンドライン長制限を回避)
                part_audio_path = os.path.join(temp_dir, f"part_{i}_keep.wav")
                select_a_parts = [f"between(t,{start:.3f},{end:.3f})" for start, end in part_keep_ranges]
                a_filter = "+".join(select_a_parts)
                
                audio_filter_script = os.path.join(temp_dir, f"part_{i}_audio_filter.txt")
                with open(audio_filter_script, "w", encoding="utf-8") as afs:
                    afs.write(f"[0:a]aselect='{a_filter}',asetpts=N/SR/TB[outa]")
                    
                cmd = [
                    self.ffmpeg_path, "-y", "-i", part_video_path,
                    "-filter_complex_script", audio_filter_script,
                    "-map", "[outa]", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
                    part_audio_path
                ]
                
                process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                self.current_process = process
                process.wait()
                self.current_process = None
                
                if os.path.exists(audio_filter_script):
                    try: os.remove(audio_filter_script)
                    except Exception: pass

                if self.is_cancelled:
                    raise UserCancelledError("処理がキャンセルされました。")
                    
                # D. Whisperによる文字起こし（有音区間のみ）
                part_whisper_result = None
                if need_whisper and os.path.exists(part_audio_path):
                    self.safe_update_ui(0.10 + (i / (len(split_times)-1)) * 0.45, f"パート {i+1} 文字起こし中...")
                    try:
                        if loaded_model is None:
                            self.safe_log(f"Whisperモデル '{whisper_model}' をロード中...")
                            import whisper
                            loaded_model = whisper.load_model(whisper_model)
                        
                        self.safe_log(f"パート {i+1} の文字起こしを実行中...")
                        part_whisper_result = loaded_model.transcribe(part_audio_path, language="ja")
                    except Exception as e:
                        self.safe_log(f"【警告】パート {i+1} の音声解析に失敗しました: {str(e)}")

                if self.is_cancelled:
                    raise UserCancelledError("処理がキャンセルされました。")

                # E. フィラー言葉の検出とローカルキープ区間の再カット
                local_keep_ranges = list(part_keep_ranges)
                local_time_map = self.build_time_map(part_keep_ranges)
                filler_words = ["えーっと", "えーと", "あのー", "あのア", "ええと", "うーん", "うーんと", "あのっ", "えっと", "えー"]
                
                if self.filler_cut_enable.get() and part_whisper_result is not None:
                    filler_ranges = []
                    for seg in part_whisper_result.get("segments", []):
                        text = seg.get("text", "").strip()
                        if text in filler_words or (len(text) < 6 and any(text.startswith(fw) for fw in filler_words)):
                            # 有音のみ文字起こしの秒数軸から、元のパート動画の時間軸に逆マッピング
                            seg_start = seg.get("start", 0.0)
                            seg_end = seg.get("end", 0.0)
                            orig_start = self.map_cut_timeline_to_orig(seg_start, local_time_map)
                            orig_end = self.map_cut_timeline_to_orig(seg_end, local_time_map)
                            
                            if orig_start is not None and orig_end is not None:
                                filler_ranges.append((orig_start, orig_end))
                                
                    if filler_ranges:
                        local_keep_ranges = self.subtract_ranges(part_keep_ranges, filler_ranges)
                        self.safe_log(f"パート {i+1}: フィラー言葉 {len(filler_ranges)} 個を検出してカットしました。")

                if not local_keep_ranges:
                    self.safe_log(f"パート {i+1}: フィラーカット後にキープする動画区間が無くなりました。")
                    if os.path.exists(part_video_path):
                        try: os.remove(part_video_path)
                        except Exception: pass
                    if os.path.exists(part_audio_path):
                        try: os.remove(part_audio_path)
                        except Exception: pass
                    continue

                # F. 大声ピーク（ツッコミ）の検出（元のパート動画全体から抽出）
                part_loud_peaks = []
                if self.loud_zoom_enable.get() or self.sub_export_enable.get():
                    if self.is_cancelled:
                        raise UserCancelledError("処理がキャンセルされました。")
                    part_full_audio_path = os.path.join(temp_dir, f"part_{i}_full.wav")
                    cmd = [
                        self.ffmpeg_path, "-y", "-i", part_video_path,
                        "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
                        part_full_audio_path
                    ]
                    process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    self.current_process = process
                    process.wait()
                    self.current_process = None
                    
                    if os.path.exists(part_full_audio_path):
                        part_loud_peaks = self.detect_audio_peaks(part_full_audio_path)
                        self.safe_log(f"パート {i+1}: 検出された大声ピーク数: {len(part_loud_peaks)}")

                # G. タイムスタンプの最終統合と字幕（SRT/JSX）の構築
                final_time_map = self.build_time_map(local_keep_ranges)
                
                # 字幕セグメントのマッピング
                if part_whisper_result is not None:
                    for seg in part_whisper_result.get("segments", []):
                        s_start = seg.get("start", 0.0)
                        s_end = seg.get("end", 0.0)
                        txt = seg.get("text", "").strip()
                        
                        if self.filler_cut_enable.get() and txt in filler_words:
                            continue
                            
                        # 1. 無音カット前（元のパート動画軸）に逆マッピング
                        orig_start = self.map_cut_timeline_to_orig(s_start, local_time_map)
                        orig_end = self.map_cut_timeline_to_orig(s_end, local_time_map)
                        
                        if orig_start is not None and orig_end is not None:
                            # 2. 最終カット後の時間軸にマッピング
                            new_start = self.map_time_to_cut_timeline(orig_start, final_time_map)
                            new_end = self.map_time_to_cut_timeline(orig_end, final_time_map)
                            
                            if new_start is not None and new_end is not None:
                                # 3. 全体のオフセットを加算
                                combined_segments.append({
                                    "start": output_accumulated_duration + new_start,
                                    "end": output_accumulated_duration + new_end,
                                    "text": txt
                                })
                
                # 大声ピークのマッピング
                for p in part_loud_peaks:
                    new_p = self.map_time_to_cut_timeline(p, final_time_map)
                    if new_p is not None:
                        combined_loud_peaks.append(output_accumulated_duration + new_p)

                # H. パート動画のエクスポート（GPUエンコーダー適用）
                output_part_video_path = os.path.join(temp_dir, f"out_part_{i}.mp4")
                self.safe_update_ui(0.10 + (i / (len(split_times)-1)) * 0.45, f"パート {i+1} 動画出力中...")
                
                part_srt_path = None
                if self.sub_burn_enable.get() and part_whisper_result is not None:
                    part_srt_path = os.path.join(temp_dir, f"part_{i}_sub.srt")
                    try:
                        with open(part_srt_path, "w", encoding="utf-8") as pf:
                            s_idx = 1
                            for seg in part_whisper_result.get("segments", []):
                                s_start = seg.get("start", 0.0)
                                s_end = seg.get("end", 0.0)
                                s_text = seg.get("text", "").strip()
                                
                                if self.filler_cut_enable.get():
                                    filler_words = ["あのー", "そのー", "えーと", "えー", "まー", "なんか", "えっと", "うーん", "こう", "ね"]
                                    if s_text in filler_words:
                                        continue
                                        
                                s_start_str = format_srt_time(s_start)
                                s_end_str = format_srt_time(s_end)
                                pf.write(f"{s_idx}\n{s_start_str} --> {s_end_str}\n{s_text}\n\n")
                                s_idx += 1
                    except Exception as e:
                        self.safe_log(f"警告 (一時字幕出力失敗): {str(e)}")

                success = self.export_sliced_video(
                    part_video_path, output_part_video_path,
                    local_keep_ranges, p_len, part_loud_peaks, srt_path=part_srt_path, gpu_encoder=gpu_encoder
                )
                if not success:
                    raise FFmpegError(f"パート {i+1} の動画出力に失敗しました。")
                
                part_videos.append(output_part_video_path)
                
                # 不要になったこのパートの入力動画や中間ファイルを削除してディスク容量を節約
                if os.path.exists(part_video_path):
                    try: os.remove(part_video_path)
                    except Exception: pass
                if os.path.exists(part_audio_path):
                    try: os.remove(part_audio_path)
                    except Exception: pass
                if 'part_full_audio_path' in locals() and os.path.exists(part_full_audio_path):
                    try: os.remove(part_full_audio_path)
                    except Exception: pass
                if part_srt_path and os.path.exists(part_srt_path):
                    try: os.remove(part_srt_path)
                    except Exception: pass
                
                # 出力動画の累積長を更新
                part_output_duration = sum(end - start for start, end in local_keep_ranges)
                output_accumulated_duration += part_output_duration
                
                # メモリとキャッシュの強制解放
                import gc
                gc.collect()
                try:
                    import torch
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()
                except Exception:
                    pass

            # 7. 全パート動画のロスレス結合
            if part_videos:
                if self.is_cancelled:
                    raise UserCancelledError("処理がキャンセルされました。")
                    
                self.safe_update_ui(0.95, "各パート動画を結合中...")
                concat_list_path = os.path.join(temp_dir, "concat.txt")
                with open(concat_list_path, "w", encoding="utf-8") as f:
                    for pv in part_videos:
                        safe_pv = pv.replace("\\", "/")
                        f.write(f"file '{safe_pv}'\n")
                
                cmd = [
                    self.ffmpeg_path, "-y", "-f", "concat", "-safe", "0",
                    "-i", concat_list_path, "-c", "copy",
                    output_path
                ]
                
                self.safe_log("最終動画のロスレス結合処理を実行中...")
                process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='ignore')
                self.current_process = process
                
                stderr_buffer = []
                while True:
                    if self.is_cancelled:
                        process.terminate()
                        raise UserCancelledError("処理がキャンセルされました。")
                    line = process.stderr.readline()
                    if not line:
                        break
                    stderr_buffer.append(line.strip())
                    if len(stderr_buffer) > 20:
                        stderr_buffer.pop(0)
                        
                process.wait()
                self.current_process = None
                
                if process.returncode != 0:
                    self.safe_log("最終動画の結合処理に失敗しました。")
                    for err_line in stderr_buffer:
                        self.safe_log(f"  FFmpeg Concat: {err_line}")
                    raise FFmpegError("Final video concat failed")
                
                if result.returncode != 0:
                    self.safe_log("【エラー】最終動画の結合に失敗しました。以下はエラーログの末尾です：")
                    self.safe_log(result.stderr)
                    raise FFmpegError("Final video concat failed")
                    
                # 8. 字幕ファイル (SRT) ＆ After Effects用スクリプト (JSX) の書き出し
                if self.sub_export_enable.get():
                    self.write_srt_and_jsx(output_path, combined_segments, combined_loud_peaks)
                
                self.safe_log("切り抜き処理が正常に完了しました！")
                self.finish_processing(True, "完了！")
            else:
                self.safe_log("【エラー】出力された動画パートがありません。")
                self.finish_processing(False, "書き出し失敗")

        except UserCancelledError as e:
            self.safe_log("ユーザーによって処理がキャンセルされました。")
            self.finish_processing(False, "キャンセルされました")
        except Exception as e:
            self.safe_log(f"予期しないエラーが発生しました: {str(e)}")
            self.finish_processing(False, "エラー終了")
        finally:
            # 一時作業フォルダの完全なクリーンアップ
            if os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                except Exception:
                    pass
    def get_video_duration(self, file_path):
        # 1. まず ffprobe の使用を試みる
        if self.ffprobe_path:
            try:
                cmd = [
                    self.ffprobe_path, "-v", "error", 
                    "-show_entries", "format=duration", 
                    "-of", "default=noprint_wrappers=1:nokey=1", 
                    file_path
                ]
                result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
                return float(result.stdout.strip())
            except Exception:
                pass
                
        # 2. ffprobe がない、または失敗した場合は ffmpeg の情報から Duration をパースする
        try:
            cmd = [self.ffmpeg_path, "-i", file_path]
            # ffmpeg -i は出力ファイルを指定しないため、必ずエラーで終了します。その stderr を取得します。
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='ignore')
            log = result.stderr
            
            # Duration: 00:01:23.45 のようなパターンを探す
            m = re.search(r"Duration:\s*(\d{2}):(\d{2}):(\d{2})\.(\d{2})", log)
            if m:
                h, m, s, cs = map(int, m.groups())
                return h * 3600 + m * 60 + s + cs / 100.0
            else:
                self.safe_log("FFmpeg の出力ログから Duration (動画時間) を取得できませんでした。")
        except Exception as e:
            self.safe_log(f"動画長取得エラー: {str(e)}")
            
        return -1.0

    def detect_silence_ranges(self, file_path, db_threshold, min_duration, total_duration):
        silence_ranges = []
        
        if self.is_cancelled:
            raise UserCancelledError("処理がキャンセルされました。")
            
        # silencedetect フィルタをかけて標準エラー出力を解析
        cmd = [
            self.ffmpeg_path, "-i", file_path,
            "-af", f"silencedetect=noise={db_threshold}dB:d={min_duration}",
            "-f", "null", "-"
        ]
        
        # 処理状況を読み取るため stderr をパイプ
        process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='ignore')
        self.current_process = process
        
        start_time = None
        
        # 進捗パース用
        time_regex = re.compile(r"time=(\d{2}):(\d{2}):(\d{2})\.(\d{2})")
        
        while True:
            if self.is_cancelled:
                process.terminate()
                raise UserCancelledError("処理がキャンセルされました。")
            line = process.stderr.readline()
            if not line:
                break
                
            # 無音開始
            if "silence_start:" in line:
                m = re.search(r"silence_start: (-?\d+\.?\d*)", line)
                if m:
                    # 開始秒数をパース (負の値は0に補正)
                    val = float(m.group(1))
                    start_time = max(0.0, val)
            
            # 無音終了
            elif "silence_end:" in line:
                m = re.search(r"silence_end: (\d+\.?\d*)", line)
                if m and start_time is not None:
                    end_time = float(m.group(1))
                    silence_ranges.append((start_time, end_time))
                    start_time = None
                    
            # 進捗のアップデート
            m_time = time_regex.search(line)
            if m_time:
                h, m, s, _ = map(int, m_time.groups())
                current_secs = h * 3600 + m * 60 + s
                # 進捗の0.05〜0.45の範囲にスケーリング
                prog = 0.05 + (current_secs / total_duration) * 0.40
                self.safe_update_ui(min(prog, 0.49), f"無音部分を検出中... {current_secs:.0f}秒/{total_duration:.0f}秒")
                
        process.wait()
        self.current_process = None
        
        # 最後に無音区間が閉じられていない（最後まで無音）場合の処理
        if start_time is not None:
            silence_ranges.append((start_time, total_duration))
            
        return silence_ranges

    def calculate_keep_ranges(self, silence_ranges, total_duration, margin, min_keep_duration):
        keep_ranges = []
        
        if not silence_ranges:
            return [(0.0, total_duration)]
            
        # 1. 最初の有音区間
        first_silence_start = silence_ranges[0][0]
        if first_silence_start > min_keep_duration:
            # 最初の有音区間は [0, 最初無音の開始 + マージン]
            end = min(total_duration, first_silence_start + margin)
            keep_ranges.append((0.0, end))
            
        # 2. 中間の有音区間
        for i in range(len(silence_ranges) - 1):
            # 無音の終了時間
            current_silence_end = silence_ranges[i][1]
            # 次の無音の開始時間
            next_silence_start = silence_ranges[i+1][0]
            
            # 有音区間の境界をマージン分補正
            start = max(0.0, current_silence_end - margin)
            end = min(total_duration, next_silence_start + margin)
            
            if (end - start) >= min_keep_duration:
                keep_ranges.append((start, end))
                
        # 3. 最後の有音区間
        last_silence_end = silence_ranges[-1][1]
        if (total_duration - last_silence_end) > min_keep_duration:
            start = max(0.0, last_silence_end - margin)
            keep_ranges.append((start, total_duration))
            
        # 重なり合う区間の結合・マージ処理
        merged_ranges = []
        if keep_ranges:
            curr_start, curr_end = keep_ranges[0]
            for next_start, next_end in keep_ranges[1:]:
                # 重なっている、または極端に近い場合は結合
                if next_start <= curr_end:
                    curr_end = max(curr_end, next_end)
                else:
                    merged_ranges.append((curr_start, curr_end))
                    curr_start, curr_end = next_start, next_end
            merged_ranges.append((curr_start, curr_end))
            
        return merged_ranges

    def export_sliced_video(self, input_path, output_path, keep_ranges, total_duration, loud_peaks=None, srt_path=None, gpu_encoder="libx264"):
        # ffmpeg フィルターグラフの構築
        select_v_parts = []
        select_a_parts = []
        
        for start, end in keep_ranges:
            select_v_parts.append(f"between(t,{start:.3f},{end:.3f})")
            select_a_parts.append(f"between(t,{start:.3f},{end:.3f})")
            
        v_filter = "+".join(select_v_parts)
        a_filter = "+".join(select_a_parts)
        
        # 音量ノーマライズの有無を取得
        audio_norm = self.audio_norm_enable.get()
        
        # フィルター文字列の定義
        v_filter_str = f"select='{v_filter}',setpts=N/FRAME_RATE/TB"
        
        # 字幕の焼き付け
        if self.sub_burn_enable.get() and srt_path and os.path.exists(srt_path):
            color_hex = rgb_to_ass_hex(parse_color_to_rgb(self.sub_color_var.get()))
            outline_color_hex = rgb_to_ass_hex(parse_color_to_rgb(self.sub_outline_color_var.get()))
            alpha_val = int((1.0 - max(0.0, min(1.0, self.sub_shadow_alpha_var.get()))) * 255)
            bbggrr = outline_color_hex.replace("&H", "")
            back_color_hex = f"&H{alpha_val:02X}{bbggrr}"
            
            ass_bold = -1 if self.sub_bold_var.get() else 0
            ass_italic = -1 if self.sub_italic_var.get() else 0
            
            alignment_map = {"左寄せ": 1, "中央寄せ": 2, "右寄せ": 3}
            alignment = alignment_map.get(self.sub_alignment_var.get(), 2)
            
            # Detect resolution/aspect ratio
            pr_x, pr_y = 1920, 1080
            if self.ffprobe_path:
                try:
                    res_cmd = [
                        self.ffprobe_path, "-v", "error",
                        "-select_streams", "v:0",
                        "-show_entries", "stream=width,height",
                        "-of", "csv=p=0:s=x",
                        input_path
                    ]
                    res_out = subprocess.run(res_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
                    w_h = res_out.stdout.strip().split('x')
                    if len(w_h) == 2:
                        w, h = int(w_h[0]), int(w_h[1])
                        if h > w:
                            pr_x, pr_y = 1080, 1920
                except Exception:
                    pass
            else:
                if self.ffmpeg_path:
                    try:
                        res_cmd = [self.ffmpeg_path, "-i", input_path]
                        res_out = subprocess.run(res_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                        for line in res_out.stderr.splitlines():
                            if "Video:" in line:
                                import re
                                m_dim = re.search(r"(\d+)x(\d+)", line)
                                if m_dim:
                                    w, h = int(m_dim.group(1)), int(m_dim.group(2))
                                    if h > w:
                                        pr_x, pr_y = 1080, 1920
                                    break
                    except Exception:
                        pass
            
            style = (
                f"Fontname={self.sub_font_name_var.get()},"
                f"Fontsize={self.sub_font_size_var.get()},"
                f"PrimaryColour={color_hex},"
                f"OutlineColour={outline_color_hex},"
                f"BackColour={back_color_hex},"
                f"BorderStyle=1,"
                f"Outline={self.sub_outline_width_var.get()},"
                f"Shadow={self.sub_shadow_depth_var.get()},"
                f"Alignment={alignment},"
                f"MarginV={self.sub_margin_v_var.get()},"
                f"PlayResX={pr_x},PlayResY={pr_y},"
                f"Bold={ass_bold},Italic={ass_italic}"
            )
            
            srt_ffmpeg = srt_path.replace("\\", "/")
            if ":" in srt_ffmpeg:
                srt_ffmpeg = srt_ffmpeg.replace(":", "\\:")
            srt_ffmpeg = srt_ffmpeg.replace("'", "'\\\\\''")
            
            v_filter_str += f",subtitles='{srt_ffmpeg}':force_style='{style}'"
        a_filter_str = f"aselect='{a_filter}',asetpts=N/SR/TB"
        
        # 大声自動ズームを動画に直接焼き付ける場合
        if self.loud_zoom_enable.get() and loud_peaks:
            zoom_conds = []
            for peak in loud_peaks:
                # ピークから1.5秒間ズームする
                zoom_conds.append(f"between(t,{peak:.3f},{peak+1.5:.3f})")
            
            if zoom_conds:
                zoom_expr = "+".join(zoom_conds)
                # 中央基準で1.2倍ズーム（crop & scaleで元の解像度を保持）
                v_filter_str += f",crop=w='if({zoom_expr},iw/1.2,iw)':h='if({zoom_expr},ih/1.2,ih)':x='(iw-ow)/2':y='(ih-oh)/2',scale=iw:ih"
                self.safe_log("動画自体への大声自動ズーム（焼き付け）を適用します。")
        
        # 音量ノーマライズを適用する場合
        if audio_norm:
            # dynaudnorm（音量の均一化）＋ loudnorm（YouTube推奨のラウドネス -14 LUFS / peak -1.0dB に調整）
            a_filter_str += ",dynaudnorm=f=75:g=15:p=0.9,loudnorm=I=-14:TP=-1.0:LRA=11"
            
        filter_complex = (
            f"[0:v]{v_filter_str}[outv];\n"
            f"[0:a]{a_filter_str}[outa]"
        )
        
        # WinError 206 (コマンドライン引数が長すぎる) を防ぐため、フィルターグラフを一時ファイルに書き出す
        filter_script_path = None
        try:
            with tempfile.NamedTemporaryFile('w', delete=False, suffix='.txt', encoding='utf-8') as tf:
                tf.write(filter_complex)
                filter_script_path = tf.name
        except Exception as e:
            self.safe_log(f"一時フィルターファイルの作成に失敗しました: {str(e)}")
            return False
            
        try:
            encoder_opts = []
            if gpu_encoder == "h264_nvenc":
                encoder_opts = ["-c:v", "h264_nvenc", "-preset", "fast", "-cq", "23", "-rc", "constqp", "-pix_fmt", "yuv420p"]
            elif gpu_encoder == "h264_qsv":
                encoder_opts = ["-c:v", "h264_qsv", "-preset", "fast", "-global_quality", "23", "-pix_fmt", "yuv420p"]
            elif gpu_encoder == "h264_amf":
                encoder_opts = ["-c:v", "h264_amf", "-quality", "speed", "-pix_fmt", "yuv420p"]
            else:
                encoder_opts = ["-c:v", "libx264", "-crf", "23", "-preset", "veryfast", "-pix_fmt", "yuv420p"]

            if self.is_cancelled:
                raise UserCancelledError("処理がキャンセルされました。")
                
            cmd = [
                self.ffmpeg_path, "-y", "-i", input_path,
                "-filter_complex_script", filter_script_path,
                "-map", "[outv]", "-map", "[outa]"
            ] + ["-threads", "4"] + encoder_opts + [
                "-c:a", "aac", "-b:a", "128k",
                output_path
            ]
            
            self.safe_log(f"実行するFFmpegコマンドを生成しました（エンコーダー: {gpu_encoder}、スレッド数: 4）。")
            if audio_norm:
                self.safe_log("音量の自動最適化（音量均一化＆YouTube適正化 -14 LUFS）を適用しています。")
            self.safe_log("書き出しを開始します。しばらくお待ちください...")
            
            process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='ignore')
            self.current_process = process
            
            # 進捗読み取り用
            time_regex = re.compile(r"time=(\d{2}):(\d{2}):(\d{2})\.(\d{2})")
            
            # キープする総時間（出力動画の想定長）の算出
            target_duration = sum(end - start for start, end in keep_ranges)
            self.safe_log(f"出力予定の動画長さ: {target_duration:.2f} 秒")
            
            # エラー診断用にFFmpegのstderrの末尾を記録しておく
            stderr_buffer = []
            
            while True:
                if self.is_cancelled:
                    process.terminate()
                    raise UserCancelledError("処理がキャンセルされました。")
                line = process.stderr.readline()
                if not line:
                    break
                
                line_str = line.strip()
                if line_str:
                    stderr_buffer.append(line_str)
                    if len(stderr_buffer) > 30:
                        stderr_buffer.pop(0)
                    
                m_time = time_regex.search(line)
                if m_time:
                    h, m, s, _ = map(int, m_time.groups())
                    current_secs = h * 3600 + m * 60 + s
                    prog = 0.60 + (current_secs / target_duration) * 0.39
                    self.safe_update_ui(min(prog, 0.99), f"動画結合中... {current_secs:.0f}秒/{target_duration:.0f}秒")
                    
            process.wait()
            self.current_process = None
            
            if process.returncode != 0:
                self.safe_log("【エラー】FFmpegが異常終了しました。以下はエラーログの末尾です：")
                for err_line in stderr_buffer:
                    self.safe_log(f"  FFmpeg: {err_line}")
                raise FFmpegError("FFmpeg execution failed")
                
            return True
        except Exception as e:
            self.safe_log(f"動画結合処理中にエラーが発生しました: {str(e)}")
            return False
        finally:
            if filter_script_path and os.path.exists(filter_script_path):
                try:
                    os.remove(filter_script_path)
                except Exception:
                    pass

    def detect_greeting_by_whisper(self, video_path, model_name):
        temp_audio = "temp_greeting_audio.wav"
        
        try:
            self.safe_log("音声認識用に冒頭30秒の音声を抽出中...")
            cmd = [
                self.ffmpeg_path, "-y", "-i", video_path,
                "-to", "30", "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
                temp_audio
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            
            self.safe_log(f"Whisperモデル '{model_name}' をロード中 (初回はダウンロードが発生するため数分かかる場合があります)...")
            import whisper
            model = whisper.load_model(model_name)
            
            self.safe_log("文字起こし処理を実行中...")
            result = model.transcribe(temp_audio, language="ja")
            
            self.safe_log("文字起こし結果:")
            greeting_end_time = 0.0
            
            greeting_keywords = [
                "こんにちは", "こんにちわ", "どうも", "はじめまして", 
                "はろー", "ハロー", "おはよう", "こんばんわ", "こんばんは",
                "です", "ます", "配信", "放送", "スタート", "開始", "ようこそ"
            ]
            
            for segment in result.get("segments", []):
                text = segment.get("text", "")
                start = segment.get("start", 0.0)
                end = segment.get("end", 0.0)
                self.safe_log(f"  [{start:.2f}s -> {end:.2f}s]: {text}")
                
                if any(kw in text for kw in greeting_keywords):
                    greeting_end_time = max(greeting_end_time, end)
            
            if os.path.exists(temp_audio):
                os.remove(temp_audio)
                
            return min(greeting_end_time, 15.0)
            
        except Exception as e:
            self.safe_log(f"Whisperでの挨拶自動検出に失敗しました（手動5秒カットにフォールバックします）: {str(e)}")
            if os.path.exists(temp_audio):
                os.remove(temp_audio)
            return 5.0

    def apply_start_offset(self, keep_ranges, offset):
        adjusted_ranges = []
        for start, end in keep_ranges:
            if end > offset:
                new_start = max(start, offset)
                adjusted_ranges.append((new_start, end))
        return adjusted_ranges

    def subtract_ranges(self, keep_ranges, subtract_ranges):
        result = []
        for k_start, k_end in keep_ranges:
            temp = [(k_start, k_end)]
            for s_start, s_end in subtract_ranges:
                next_temp = []
                for t_start, t_end in temp:
                    if s_end <= t_start or s_start >= t_end:
                        next_temp.append((t_start, t_end))
                    else:
                        if s_start > t_start:
                            next_temp.append((t_start, s_start))
                        if s_end < t_end:
                            next_temp.append((s_end, t_end))
                temp = next_temp
            result.extend(temp)
        return [r for r in result if (r[1] - r[0]) >= 0.05]

    def build_time_map(self, keep_ranges):
        time_map = []
        accumulated_time = 0.0
        for start, end in keep_ranges:
            time_map.append((start, end, accumulated_time))
            accumulated_time += (end - start)
        return time_map

    def map_time_to_cut_timeline(self, t, time_map):
        if not time_map:
            return None
        if len(time_map[0]) == 2:
            time_map = self.build_time_map(time_map)
            
        starts = [item[0] for item in time_map]
        idx = bisect.bisect_right(starts, t) - 1
        
        if idx < 0:
            return None
            
        orig_start, orig_end, new_start = time_map[idx]
        if t > orig_end:
            return None
            
        return new_start + (t - orig_start)

    def map_cut_timeline_to_orig(self, new_t, time_map):
        if not time_map:
            return None
        if len(time_map[0]) == 2:
            time_map = self.build_time_map(time_map)
            
        new_starts = [item[2] for item in time_map]
        idx = bisect.bisect_right(new_starts, new_t) - 1
        
        if idx < 0:
            return None
            
        orig_start, orig_end, new_start = time_map[idx]
        duration = orig_end - orig_start
        if new_t > (new_start + duration):
            return None
            
        return orig_start + (new_t - new_start)

    def detect_audio_peaks(self, wav_path):
        import wave
        import struct
        import math
        try:
            with wave.open(wav_path, 'rb') as wf:
                params = wf.getparams()
                sample_rate = params.framerate
                
                # 0.1秒ごとのチャンクで解析
                chunk_size = int(sample_rate * 0.1)
                rms_list = []
                fmt = f"{chunk_size}h"
                
                while True:
                    data = wf.readframes(chunk_size)
                    if not data:
                        break
                    n_samples = len(data) // 2
                    if n_samples == 0:
                        continue
                    
                    chunk_fmt = fmt if n_samples == chunk_size else f"{n_samples}h"
                    samples = struct.unpack(chunk_fmt, data)
                    sum_sq = sum(s * s for s in samples)
                    rms = math.sqrt(sum_sq / n_samples)
                    rms_list.append(rms)
                    
            if not rms_list:
                return []
                
            max_rms = max(rms_list)
            loud_times = []
            
            # 判定閾値：最大音量の45%以上、かつ周辺（前後1秒）平均の2.0倍以上
            # かつ最低限の音量閾値（ノイズ判定防止）
            for i, rms in enumerate(rms_list):
                t = i * 0.1
                if rms > max_rms * 0.45 and rms > 800:
                    start_idx = max(0, i - 10)
                    end_idx = min(len(rms_list), i + 10)
                    local_avg = sum(rms_list[start_idx:end_idx]) / (end_idx - start_idx)
                    
                    if rms > local_avg * 2.0:
                        loud_times.append(t)
                        
            # 近すぎるピーク（3秒以内）を結合
            merged_peaks = []
            for t in loud_times:
                if not merged_peaks or t - merged_peaks[-1] > 3.0:
                    merged_peaks.append(t)
                    
            return merged_peaks
            
        except Exception as e:
            self.safe_log(f"音声ピーク検出エラー: {str(e)}")
            return []

    def write_srt_and_jsx(self, output_path, segments, loud_peaks):
        base_path, _ = os.path.splitext(output_path)
        srt_path = base_path + ".srt"
        jsx_path = base_path + ".jsx"
        
        # 1. SRTの書き込み
        try:
            with open(srt_path, "w", encoding="utf-8") as f:
                for idx, seg in enumerate(segments, 1):
                    start = seg["start"]
                    end = seg["end"]
                    text = seg["text"]
                    
                    # タイムスタンプフォーマット HH:MM:SS,mmm
                    s_h, s_m = divmod(start, 3600)
                    s_m, s_s = divmod(s_m, 60)
                    s_sec, s_ms = divmod(s_s, 1)
                    
                    e_h, e_m = divmod(end, 3600)
                    e_m, e_s = divmod(e_m, 60)
                    e_sec, e_ms = divmod(e_s, 1)
                    
                    start_str = f"{int(s_h):02d}:{int(s_m):02d}:{int(s_sec):02d},{int(s_ms*1000):03d}"
                    end_str = f"{int(e_h):02d}:{int(e_m):02d}:{int(e_sec):02d},{int(e_ms*1000):03d}"
                    
                    f.write(f"{idx}\n{start_str} --> {end_str}\n{text}\n\n")
            self.safe_log(f"SRT字幕ファイルを保存しました: {os.path.basename(srt_path)}")
        except Exception as e:
            self.safe_log(f"SRT字幕ファイルの保存に失敗しました: {str(e)}")
            
        # 2. After Effects用JSXの書き込み
        try:
            import json
            subs_json = json.dumps(segments, ensure_ascii=False)
            peaks_json = json.dumps(loud_peaks)
            
            jsx_content = f"""(function() {{
    app.beginUndoGroup("Import Subtitles and Zoom Control");
    var comp = app.project.activeItem;
    if (!comp || !(comp instanceof CompItem)) {{
        alert("アクティブなコンポジションを選択してください。");
        return;
    }}

    var subs = {subs_json};
    var loudPeaks = {peaks_json};

    // 1. 大声ピーク位置へのマーカー追加とズームヌルの作成
    if (loudPeaks.length > 0) {{
        var zoomNull = comp.layers.addNull();
        zoomNull.name = "Zoom_Controller";
        var scaleProp = zoomNull.property("ADBE Transform Group").property("ADBE Scale");
        var compMarkerGroup = comp.markerProperty;

        for (var p = 0; p < loudPeaks.length; p++) {{
            var t = loudPeaks[p];
            // スケールのアニメーションキーフレーム (100% -> 120% -> 120% -> 100%)
            scaleProp.setValueAtTime(t - 0.1, [100, 100, 100]);
            scaleProp.setValueAtTime(t, [120, 120, 100]);
            scaleProp.setValueAtTime(t + 1.0, [120, 120, 100]);
            scaleProp.setValueAtTime(t + 1.2, [100, 100, 100]);

            // コンポジションマーカーの追加
            var markerVal = new MarkerValue("大声ピーク");
            markerVal.comment = "Loud Peak " + (p + 1);
            markerVal.duration = 1.2;
            compMarkerGroup.setValueAtTime(t, markerVal);
        }}
    }}

    // 2. 字幕テキストレイヤーの作成
    for (var i = 0; i < subs.length; i++) {{
        var s = subs[i];
        var textLayer = comp.layers.addText(s.text);
        textLayer.startTime = s.start;
        textLayer.outPoint = s.end;

        var textProp = textLayer.property("Source Text");
        var textDocument = textProp.value;
        textDocument.fontSize = {self.sub_font_size_var.get()};
        textDocument.font = "{self.sub_font_name_var.get()}";
        textDocument.applyFill = true;
        
        // Convert primary color
        var rgbVal = {parse_color_to_rgb(self.sub_color_var.get())};
        textDocument.fillColor = [rgbVal[0]/255.0, rgbVal[1]/255.0, rgbVal[2]/255.0];
        
        textDocument.applyStroke = true;
        
        // Convert outline color
        var outlineRgbVal = {parse_color_to_rgb(self.sub_outline_color_var.get())};
        textDocument.strokeColor = [outlineRgbVal[0]/255.0, outlineRgbVal[1]/255.0, outlineRgbVal[2]/255.0];
        textDocument.strokeWidth = {float(self.sub_outline_width_var.get()) * 2};
        
        // Justification mapping
        var alignVal = "{self.sub_alignment_var.get()}";
        if (alignVal === "左寄せ") {{
            textDocument.justification = ParagraphJustification.LEFT_JUSTIFY;
        }} else if (alignVal === "右寄せ") {{
            textDocument.justification = ParagraphJustification.RIGHT_JUSTIFY;
        }} else {{
            textDocument.justification = ParagraphJustification.CENTER_JUSTIFY;
        }}
        
        textProp.setValue(textDocument);

        // Position Y (margin_v from bottom)
        var marginV = {self.sub_margin_v_var.get()};
        textLayer.property("Position").setValue([comp.width / 2, comp.height - marginV]);
    }}

    app.endUndoGroup();
    alert("字幕レイヤー（" + subs.length + "個）と大声ズームヌル（ピーク数: " + loudPeaks.length + "個）を生成しました！\\n動画素材レイヤーの『親とリンク』を『Zoom_Controller』に設定してご使用ください。");
}})();
"""
            with open(jsx_path, "w", encoding="utf-8") as f:
                f.write(jsx_content)
            self.safe_log(f"After Effects用スクリプト(.jsx)を保存しました: {os.path.basename(jsx_path)}")
        except Exception as e:
            self.safe_log(f"After Effects用スクリプトの保存に失敗しました: {str(e)}")


    # ----------------------------------------------------
    # スレッドセーフなUI更新ヘルパー
    # ----------------------------------------------------
    def load_config(self):
        self.config_data = {}
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.json")
        if os.path.exists(config_path):
            try:
                import json
                with open(config_path, "r", encoding="utf-8") as f:
                    self.config_data = json.load(f)
            except Exception:
                pass

    def save_config(self):
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.json")
        try:
            self.config_data["sub_burn_enable"] = self.sub_burn_enable.get()
            self.config_data["sub_font_name"] = self.sub_font_name_var.get()
            self.config_data["sub_font_size"] = self.sub_font_size_var.get()
            self.config_data["sub_color"] = self.sub_color_var.get()
            self.config_data["sub_outline_color"] = self.sub_outline_color_var.get()
            self.config_data["sub_outline_width"] = self.sub_outline_width_var.get()
            self.config_data["sub_shadow_depth"] = self.sub_shadow_depth_var.get()
            self.config_data["sub_shadow_alpha"] = self.sub_shadow_alpha_var.get()
            self.config_data["sub_margin_v"] = self.sub_margin_v_var.get()
            self.config_data["sub_bold"] = self.sub_bold_var.get()
            self.config_data["sub_italic"] = self.sub_italic_var.get()
            self.config_data["sub_alignment"] = self.sub_alignment_var.get()
            
            self.config_data["db_threshold"] = self.db_slider.get()
            self.config_data["min_silence_duration"] = self.duration_slider.get()
            self.config_data["margin"] = self.margin_entry.get()
            self.config_data["min_keep"] = self.keep_entry.get()
            self.config_data["audio_norm"] = self.audio_norm_enable.get()
            self.config_data["filler_cut"] = self.filler_cut_enable.get()
            self.config_data["loud_zoom"] = self.loud_zoom_enable.get()
            self.config_data["sub_export"] = self.sub_export_enable.get()
            self.config_data["greeting_enable"] = self.greeting_enable.get()
            self.config_data["greeting_mode"] = self.greeting_mode.get()
            self.config_data["greeting_sec"] = self.sec_entry.get()
            self.config_data["whisper_model"] = self.model_combo.get()
            
            import json
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(self.config_data, f, indent=4, ensure_ascii=False)
        except Exception:
            pass

    def open_color_picker(self, color_type):
        initial_color = self.sub_color_var.get() if color_type == "color" else self.sub_outline_color_var.get()
        picker = ColorPickerDialog(self, title="色を選択", initial_color=initial_color)
        self.wait_window(picker)
        if picker.result:
            if color_type == "color":
                self.sub_color_var.set(picker.result)
                self.sub_color_preview.configure(fg_color=picker.result)
            else:
                self.sub_outline_color_var.set(picker.result)
                self.sub_outline_color_preview.configure(fg_color=picker.result)

    def select_output_file(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".mp4",
            filetypes=[("MP4 動画", "*.mp4")]
        )
        if file_path:
            self.output_entry.delete(0, "end")
            self.output_entry.insert(0, os.path.normpath(file_path))

    def cancel_processing(self):
        self.is_cancelled = True
        self.safe_log("ユーザーによって処理がキャンセルされました。")
        if hasattr(self, "current_process") and self.current_process:
            try:
                self.current_process.terminate()
            except Exception:
                pass

    def start_processing(self):
        input_path = self.input_entry.get().strip()
        output_path = self.output_entry.get().strip()
        
        if not input_path or not os.path.exists(input_path):
            messagebox.showerror("エラー", "入力ファイルが存在しません。")
            return
            
        if not output_path:
            messagebox.showerror("エラー", "出力ファイルを入力してください。")
            return
            
        self.save_config()
        
        # キャンセル状態・プロセスの初期化
        self.is_cancelled = False
        self.current_process = None
        
        self.is_processing = True
        self.run_btn.configure(state="disabled")
        self.input_btn.configure(state="disabled")
        self.output_btn.configure(state="disabled")
        
        # モーダル進捗ポップアップの表示
        self.progress_dialog = ProgressDialog(self, title="処理進行状況")
        self.progress_dialog.update_progress(0.0, "処理を開始します...")
        
        self.update_progress(0.0, "処理を開始します...")
        
        import threading
        threading.Thread(target=self.process_video, args=(input_path, output_path), daemon=True).start()

    def log(self, text):
        if hasattr(self, "log_textbox") and self.log_textbox:
            self.log_textbox.insert(tk.END, text + "\n")
            self.log_textbox.see(tk.END)
        print(text)

    def safe_log(self, text):
        self.after(0, lambda: self.log(text))
        
    def safe_update_ui(self, progress_val, status_text):
        now = time.time()
        if progress_val >= 1.0 or progress_val <= 0.0 or now - self._last_ui_update >= 0.2:
            self._last_ui_update = now
            self.after(0, lambda: self.update_progress(progress_val, status_text))

    def update_progress(self, val, text):
        self.progress_bar.set(val)
        self.progress_label.configure(text=text)
        if hasattr(self, "progress_dialog") and self.progress_dialog:
            try:
                self.progress_dialog.update_progress(val, text)
            except Exception:
                pass

    def finish_processing(self, success, message):
        self.after(0, lambda: self._finish_ui(success, message))

    def _finish_ui(self, success, message):
        self.is_processing = False
        self.run_btn.configure(state="normal")
        self.input_btn.configure(state="normal")
        self.output_btn.configure(state="normal")
        
        # モーダルダイアログを閉じる
        if hasattr(self, "progress_dialog") and self.progress_dialog:
            try:
                self.progress_dialog.destroy()
            except Exception:
                pass
            self.progress_dialog = None
            
        if success:
            self.update_progress(1.0, "処理完了！")
            messagebox.showinfo("成功", f"切り抜き処理が完了しました！\n保存先:\n{self.output_entry.get()}")
        else:
            self.update_progress(0.0, f"停止: {message}")
            if message == "キャンセルされました":
                messagebox.showinfo("キャンセル", "処理がキャンセルされました。")
            else:
                messagebox.showerror("エラー", f"切り抜き処理に失敗しました。\nログメッセージをご確認ください。")


if __name__ == "__main__":
    app = LongVideoClipperApp()
    app.mainloop()

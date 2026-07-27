import os
import sys
import re
import glob
import queue
import time
import threading
import webbrowser
import traceback
import shutil
import cv2
import PIL.Image
import PIL.ImageDraw
import PIL.ImageFont
import PIL.ImageTk
import customtkinter as ctk
from tkinter import filedialog, messagebox, simpledialog
import tkinter as tk
import json
import colorsys

# 他の自作モジュールからインポート
from utils import (
    seconds_to_hms, seconds_to_hms_ms, seconds_to_minsec,
    minsec_to_seconds, time_to_seconds, clean_filename
)
import audio as audio_mod
import video as video_mod

PREVIEW_W = 216
PREVIEW_H = 384

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

def rgb_to_ass_hex(rgb: tuple) -> str:
    r, g, b = rgb
    return f"&H{b:02X}{g:02X}{r:02X}"

def preprocess_overlay_image(src_path, scale, angle, opacity):
    from PIL import Image
    try:
        with Image.open(src_path) as img:
            img = img.convert("RGBA")
            
            # 1. Scale
            w, h = img.size
            new_w = max(10, int(w * scale))
            new_h = max(10, int(h * scale))
            img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            
            # 2. Rotate
            if angle != 0:
                img = img.rotate(-angle, expand=True, resample=Image.Resampling.BICUBIC)
            
            # 3. Opacity
            if opacity < 1.0:
                r, g, b, a = img.split()
                a = a.point(lambda p: int(p * opacity))
                img = Image.merge("RGBA", (r, g, b, a))
                
            return img
    except Exception as e:
        print(f"⚠️ Image preprocessing failed: {e}")
        return None

FONT_MAP = {
    "MS Gothic": "msgothic.ttc",
    "ＭＳ ゴシック": "msgothic.ttc",
    "MS PGothic": "msgothic.ttc",
    "ＭＳ Ｐゴシック": "msgothic.ttc",
    "Meiryo": "meiryo.ttc",
    "メイリオ": "meiryo.ttc",
    "Yu Gothic": "yugothm.ttc",
    "游ゴシック": "yugothm.ttc",
    "YuGothic": "yugothm.ttc",
    "HG丸ｺﾞｼｯｸM-PRO": "hgrsmp.ttf",
    "BIZ UDPGothic": "BIZ-UDPGothic.ttf",
    "Segoe UI": "segoeui.ttf",
    "Arial": "arial.ttf",
    "Impact": "impact.ttf"
}

def resolve_font_file_win(font_family_name: str) -> str:
    """Windowsのレジストリからフォントファミリー名に対応するフォントファイル名を取得する"""
    import winreg
    try:
        reg_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts")
        num_values = winreg.QueryInfoKey(reg_key)[1]
        best_match = None
        for i in range(num_values):
            name, value, _ = winreg.EnumValue(reg_key, i)
            if font_family_name.lower() in name.lower():
                best_match = value
                if any(w in name.lower() for w in ["regular", "標準", "medium"]):
                    best_match = value
                    break
        winreg.CloseKey(reg_key)
        if best_match:
            return best_match
    except Exception as e:
        print(f"⚠️ winregフォントスキャンエラー: {e}")
    return None

def get_windows_font_path(font_name: str) -> str:
    """Windowsのシステムフォントフォルダからフォントの絶対パスを取得する"""
    resolved = resolve_font_file_win(font_name)
    if not resolved:
        resolved = FONT_MAP.get(font_name, font_name)
    if os.path.isabs(resolved):
        return resolved
    win_font_dir = os.path.join(os.environ.get("SystemRoot", "C:\\Windows"), "Fonts")
    path = os.path.join(win_font_dir, resolved)
    if os.path.exists(path):
        return path
    return resolved


class WhisperProgressDialog(ctk.CTkToplevel):
    def __init__(self, parent, total_count):
        super().__init__(parent)
        self.title("AI字幕の一括生成中...")
        self.geometry("480x220")
        self.resizable(False, False)
        
        self.ui_font_family = parent.ui_font_family
        self.ui_font_size = parent.ui_font_size
        
        self.grab_set()
        
        x = parent.winfo_x() + (parent.winfo_width() - 480) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 220) // 2
        self.geometry(f"480x220+{x}+{y}")
        
        self.label = ctk.CTkLabel(self, text="AI字幕を一括自動生成しています...", font=(self.ui_font_family, self.ui_font_size + 2, "bold"))
        self.label.pack(pady=(25, 5))
        
        self.status_label = ctk.CTkLabel(self, text=f"準備中 (0 / {total_count} 件)...", font=(self.ui_font_family, self.ui_font_size), text_color="#aaaaaa", justify="center")
        self.status_label.pack(pady=5)
        
        self.progress = ctk.CTkProgressBar(self, width=380)
        self.progress.pack(pady=15)
        self.progress.set(0.0)
        
        self.cancel_requested = False
        self.cancel_btn = ctk.CTkButton(self, text="キャンセル中止", fg_color="firebrick", hover_color="darkred", command=self.cancel)
        self.cancel_btn.pack(pady=5)
        
        self.protocol("WM_DELETE_WINDOW", self.cancel)

    def cancel(self):
        if messagebox.askyesno("確認", "AI字幕の自動生成処理を中止しますか？"):
            self.cancel_requested = True
            self.destroy()


class StdoutQueueRedirector:
    def __init__(self, log_queue):
        self.log_queue = log_queue
        self.terminal = sys.stdout

    def write(self, string):
        if self.terminal:
            try: self.terminal.write(string)
            except Exception: pass
        self.log_queue.put(string)

    def flush(self):
        if self.terminal:
            try: self.terminal.flush()
            except Exception: pass


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
        
        p_color = getattr(parent, "theme_primary_color", "#1a73e8")
        h_color = getattr(parent, "theme_primary_hover", "#155cb4")
        
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
        self.parent.config_manager.save_config(self.parent.config_data)
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


class App(ctk.CTk):
    def __init__(self, config_manager):
        super().__init__()
        self.title("きりぬき箇所判定・一括編集ツール")
        self.config_manager = config_manager
        self.config_data = self.config_manager.config_data
        self.ui_font_family = self.config_data.get("ui_font_family", "Yu Gothic UI")
        self.ui_font_size = int(self.config_data.get("ui_font_size", 12))
        self.current_preview_w = 360
        self.current_preview_h = 640
        if "color_history" not in self.config_data:
            self.config_data["color_history"] = ["#FFFF00", "#FFFFFF", "#000000", "#FF0000", "#00FF00", "#0000FF", "#00FFFF", "#FF00FF"]

        self.geometry("1400x900")
        self.minsize(600, 500)
        self.resizable(True, True)

        self.input_video_path = ""
        self.jobs = []
        self.active_job_index = -1
        self.checkboxes = []
        self.log_queue = queue.Queue()
        self.processing_failed = False
        self.error_details = ""
        self.processing_queue = []
        self.queue_widgets = []
        self.preview_cap = None
        self.preview_playing = False
        self.preview_fps = 30
        self.preview_total_frames = 0
        self.preview_current_frame = 0
        self.preview_start_frame = 0
        self.preview_end_frame = 0
        self.job_start_frame = 0
        self.job_end_frame = 0
        self.temp_preview_link = "temp_preview_video.mp4"
        self.subtitle_widgets = []
        self.drag_active_idx = -1
        
        self.theme_primary_color = "#1a73e8"
        self.theme_primary_hover = "#155cb4"
        
        self.bulk_whisper_info = {}
        self.audio_ready = False
        self.temp_play_audio = "temp_play_audio.wav"
        self.loud_zoom_var = ctk.BooleanVar(value=False)
        self.overlay_enabled_var = ctk.BooleanVar(value=False)

        self.create_widgets()
        self.scan_environment()
        self.refresh_presets()
        self.update_log_from_queue()
        self.protocol("WM_DELETE_WINDOW", self.on_close)



    def create_widgets(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.tab_run = self.tabview.add("切り抜き＆字幕編集（一括）")
        self.tab_prompt = self.tabview.add("Geminiプロンプト設定")
        self.tab_global = self.tabview.add("全体設定")
        self.setup_run_tab()
        self.bind("<Configure>", self.on_window_configure)
        self.setup_prompt_tab()
        self.setup_global_tab()

    def setup_run_tab(self):
        self.tab_run.grid_columnconfigure(0, weight=0, minsize=180)
        self.tab_run.grid_columnconfigure(1, weight=1)
        self.tab_run.grid_rowconfigure(0, weight=1)

        self.sidebar_wizard = ctk.CTkFrame(self.tab_run, width=180, corner_radius=8)
        self.sidebar_wizard.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="nsew")
        self.sidebar_wizard.pack_propagate(False)

        self.content_wizard = ctk.CTkFrame(self.tab_run, corner_radius=8, fg_color="transparent")
        self.content_wizard.grid(row=0, column=1, padx=(5, 10), pady=10, sticky="nsew")
        self.content_wizard.grid_columnconfigure(0, weight=1)
        self.content_wizard.grid_rowconfigure(0, weight=0)
        self.content_wizard.grid_rowconfigure(1, weight=1)

        sidebar_hdr = ctk.CTkFrame(self.sidebar_wizard, fg_color="transparent")
        sidebar_hdr.pack(fill="x", padx=5, pady=(10, 5))
        
        self.sidebar_toggle_btn = ctk.CTkButton(
            sidebar_hdr,
            text="☰",
            width=32,
            height=32,
            fg_color="transparent",
            hover_color="#3a3a3a",
            font=ctk.CTkFont(size=16, weight="bold"),
            command=self.toggle_sidebar
        )
        self.sidebar_toggle_btn.pack(side="left", padx=2)
        
        self.sidebar_title_label = ctk.CTkLabel(
            sidebar_hdr,
            text="🎬 きりぬき手順",
            font=ctk.CTkFont(weight="bold", size=13)
        )
        self.sidebar_title_label.pack(side="left", padx=5)

        self.wizard_buttons = {}
        steps = [
            ("step1", "① 切り抜き候補"),
            ("step2", "② 字幕・編集"),
            ("step3", "③ 書き出し・ログ")
        ]
        for key, label in steps:
            btn = ctk.CTkButton(
                self.sidebar_wizard,
                text=label,
                anchor="w",
                height=40,
                fg_color="transparent",
                text_color="white" if ctk.get_appearance_mode() == "Dark" else "black",
                font=ctk.CTkFont(weight="bold", size=12),
                command=lambda k=key: self.switch_wizard_step(k)
            )
            btn.pack(fill="x", padx=10, pady=5)
            self.wizard_buttons[key] = btn

        tf = ctk.CTkFrame(self.content_wizard)
        tf.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
        tf.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(tf, text="対象動画:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.video_entry = ctk.CTkEntry(tf, placeholder_text="動画ファイルを選択してください...")
        self.video_entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        ctk.CTkButton(tf, text="参照...", width=80, fg_color=self.theme_primary_color, hover_color=self.theme_primary_hover, command=self.select_video).grid(row=0, column=2, padx=10, pady=5)
        ctk.CTkButton(tf, text="💾 作業保存", width=85, fg_color=self.theme_primary_color, hover_color=self.theme_primary_hover, command=self.save_project).grid(row=0, column=3, padx=(5, 2), pady=5)
        ctk.CTkButton(tf, text="📂 作業読込", width=85, fg_color=self.theme_primary_color, hover_color=self.theme_primary_hover, command=self.load_project).grid(row=0, column=4, padx=(2, 5), pady=5)
        
        self.grayscale_var = ctk.BooleanVar(value=False)
        self.grayscale_switch = ctk.CTkSwitch(tf, text="グレースケール", variable=self.grayscale_var, command=self.toggle_grayscale)
        self.grayscale_switch.grid(row=0, column=5, padx=(5, 10), pady=5)
        self.tf = tf

        self.step_container = ctk.CTkFrame(self.content_wizard, fg_color="transparent")
        self.step_container.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
        self.step_container.grid_columnconfigure(0, weight=1)
        self.step_container.grid_rowconfigure(0, weight=1)

        self.step1_frame = ctk.CTkFrame(self.step_container, fg_color="transparent")
        self.step2_frame = ctk.CTkFrame(self.step_container, fg_color="transparent")
        self.step3_frame = ctk.CTkFrame(self.step_container, fg_color="transparent")

        self.step1_frame.grid_columnconfigure(0, weight=1)
        self.step1_frame.grid_columnconfigure(1, weight=1)
        self.step1_frame.grid_rowconfigure(0, weight=1)

        lf = ctk.CTkFrame(self.step1_frame)
        lf.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        lf.grid_columnconfigure(0, weight=1)
        lf.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(lf, text="【1. Gemini出力コピペエリア】", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=10, pady=2, sticky="w")
        self.paste_textbox = ctk.CTkTextbox(lf, font=(self.ui_font_family, self.ui_font_size))
        self.paste_textbox.grid(row=1, column=0, padx=10, pady=2, sticky="nsew")
        self.apply_inst_btn = ctk.CTkButton(lf, text="コピペから候補を読み込む", command=self.apply_paste_instructions, fg_color=self.theme_primary_color, hover_color=self.theme_primary_hover)
        self.apply_inst_btn.grid(row=2, column=0, padx=10, pady=6, sticky="ew")

        cf = ctk.CTkFrame(self.step1_frame)
        cf.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        cf.grid_columnconfigure(0, weight=1)
        cf.grid_rowconfigure(1, weight=1)
        self.list_title = ctk.CTkLabel(cf, text="【2. 切り抜き候補一覧】", font=ctk.CTkFont(weight="bold"))
        self.list_title.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.scrollable_frame = ctk.CTkScrollableFrame(cf, label_text="項目をクリックするとプレビューにロード", height=250)
        self.scrollable_frame.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
        self.scrollable_frame.grid_columnconfigure(0, weight=1)
        self.generate_selected_sub_btn = ctk.CTkButton(
            cf, text="🪄 選択した候補の字幕を生成",
            font=ctk.CTkFont(weight="bold"),
            fg_color=self.theme_primary_color, hover_color=self.theme_primary_hover,
            command=self.start_bulk_whisper_for_selected
        )
        self.generate_selected_sub_btn.grid(row=2, column=0, padx=10, pady=6, sticky="ew")

        self.lf = lf
        self.cf = cf

        self.step2_frame.grid_columnconfigure(0, weight=1)
        self.step2_frame.grid_rowconfigure(0, weight=1)

        rf = ctk.CTkScrollableFrame(self.step2_frame, fg_color="transparent")
        rf.grid(row=0, column=0, sticky="nsew")
        rf.grid_columnconfigure(0, weight=1)
        rf.grid_columnconfigure(1, weight=1)
        rf.grid_columnconfigure(2, weight=0, minsize=280)
        rf.grid_rowconfigure(3, weight=1, minsize=340)

        hdr_frame = ctk.CTkFrame(rf, fg_color="transparent")
        hdr_frame.grid(row=0, column=0, columnspan=3, padx=10, pady=(8, 3), sticky="ew")
        hdr_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(hdr_frame, text="【3. プレビュー＆字幕タイムライン編集】", font=ctk.CTkFont(weight="bold")).pack(side="left", anchor="w")
        
        select_box = ctk.CTkFrame(hdr_frame, fg_color="transparent")
        select_box.pack(side="right", anchor="e")
        ctk.CTkLabel(select_box, text="編集対象の候補: ", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=2)
        self.job_select_menu = ctk.CTkOptionMenu(select_box, values=["(候補がありません)"], width=220, command=self.on_job_select_menu_changed)
        self.job_select_menu.pack(side="left", padx=2)

        self.whisper_btn = ctk.CTkButton(rf, text="🪄 AIで字幕を自動生成 (この範囲のみの音声を解析)", command=self.start_whisper_for_active_job)
        self.whisper_btn.grid(row=1, column=0, columnspan=2, padx=10, pady=4, sticky="ew")

        time_ctrl = ctk.CTkFrame(rf)
        time_ctrl.grid(row=2, column=0, columnspan=2, padx=10, pady=3, sticky="ew")
        time_ctrl.grid_columnconfigure(0, weight=1)
        
        # Row 1 of time_ctrl: Playback & Seek Slider
        time_row1 = ctk.CTkFrame(time_ctrl, fg_color="transparent")
        time_row1.pack(fill="x", padx=4, pady=(3, 1))
        
        self.play_btn = ctk.CTkButton(time_row1, text="▶", width=38, command=self.toggle_play)
        self.play_btn.pack(side="left", padx=(2, 2))
        
        ctk.CTkButton(time_row1, text="🎬外部", width=50, command=self.play_in_external_player).pack(side="left", padx=2)
        
        self.time_label = ctk.CTkLabel(time_row1, text="00:00 / 00:00", width=85, font=("Consolas", 11))
        self.time_label.pack(side="left", padx=3)
        
        self.audio_status_lbl = ctk.CTkLabel(time_row1, text="", text_color="orange", font=ctk.CTkFont(size=11))
        self.audio_status_lbl.pack(side="left", padx=3)
        
        self.seek_slider = ctk.CTkSlider(time_row1, from_=0, to=100, number_of_steps=100, command=self.on_seek_drag)
        self.seek_slider.set(0)
        self.seek_slider.pack(side="left", padx=(6, 2), fill="x", expand=True)
        
        # Row 2 of time_ctrl: Start/End Range Controls
        time_row2 = ctk.CTkFrame(time_ctrl, fg_color="transparent")
        time_row2.pack(fill="x", padx=4, pady=(1, 3))
        
        ctk.CTkLabel(time_row2, text="⏱ 範囲指定:", font=ctk.CTkFont(size=11, weight="bold")).pack(side="left", padx=(2, 4))
        ctk.CTkLabel(time_row2, text="開始:").pack(side="left", padx=2)
        self.start_entry = ctk.CTkEntry(time_row2, placeholder_text="00:00:00", width=74, font=("Consolas", 11))
        self.start_entry.pack(side="left", padx=2)
        
        ctk.CTkLabel(time_row2, text="～ 終了:").pack(side="left", padx=2)
        self.end_entry = ctk.CTkEntry(time_row2, placeholder_text="00:00:00", width=74, font=("Consolas", 11))
        self.end_entry.pack(side="left", padx=2)
        
        ctk.CTkButton(time_row2, text="範囲更新", width=65, fg_color="gray30", hover_color="gray45", command=self.update_active_job_range).pack(side="left", padx=6)

        self.preview_container = ctk.CTkFrame(rf, fg_color="#000000", height=340)
        self.preview_container.grid(row=3, column=0, padx=(10, 4), pady=5, sticky="nsew")
        self.preview_container.grid_propagate(False)

        self.preview_panel = ctk.CTkLabel(self.preview_container, text="[再生キー枠またはプレビュー画像]", font=ctk.CTkFont(size=10), fg_color="#000000")
        self.preview_panel.place(relx=0.5, rely=0.5, anchor="center")
        self.preview_container.bind("<Configure>", self.on_preview_container_configure)

        self.sub_scroll = ctk.CTkScrollableFrame(rf, label_text="字幕編集タイムライン (秒数・テキストは手動変更可能)", height=220)
        self.sub_scroll.grid(row=3, column=1, padx=(4, 10), pady=5, sticky="nsew")
        self.sub_scroll.grid_columnconfigure(1, weight=1)

        self.add_queue_btn = ctk.CTkButton(rf, text="➕ 編集した内容で処理キューに追加する", font=ctk.CTkFont(size=14, weight="bold"), fg_color=self.theme_primary_color, hover_color=self.theme_primary_hover, command=self.add_active_job_to_queue)
        self.add_queue_btn.grid(row=4, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

        self.char_panel = ctk.CTkScrollableFrame(rf, width=280)
        self.char_panel.grid(row=1, column=2, rowspan=4, padx=(10, 8), pady=5, sticky="nsew")
        self.setup_char_panel()

        self.rf = rf

        self.step3_frame.grid_columnconfigure(0, weight=1)
        self.step3_frame.grid_rowconfigure(0, weight=1)

        bf = ctk.CTkFrame(self.step3_frame, fg_color="transparent")
        bf.grid(row=0, column=0, sticky="nsew")
        bf.grid_columnconfigure(0, weight=4)
        bf.grid_columnconfigure(1, weight=6)
        bf.grid_rowconfigure(0, weight=1)

        bf_left = ctk.CTkFrame(bf)
        bf_left.grid(row=0, column=0, padx=10, pady=5, sticky="nsew")
        bf_left.grid_columnconfigure(0, weight=1)
        bf_left.grid_rowconfigure(1, weight=1)
        
        ctk.CTkLabel(bf_left, text="【4. 書き出し処理キュー一覧】", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.queue_scrollable = ctk.CTkScrollableFrame(bf_left)
        self.queue_scrollable.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
        self.queue_scrollable.grid_columnconfigure(0, weight=1)
        self.queue_clear_btn = ctk.CTkButton(bf_left, text="🧹 キューをすべてクリア", fg_color="firebrick", hover_color="darkred", command=self.clear_all_queues)
        self.queue_clear_btn.grid(row=2, column=0, padx=5, pady=5, sticky="ew")

        bf_right = ctk.CTkFrame(bf, fg_color="transparent")
        bf_right.grid(row=0, column=1, padx=10, pady=5, sticky="nsew")
        bf_right.grid_columnconfigure(0, weight=1)
        bf_right.grid_rowconfigure(3, weight=1)

        opt_f = ctk.CTkFrame(bf_right)
        opt_f.grid(row=0, column=0, padx=5, pady=(2, 2), sticky="ew")
        opt_f.grid_columnconfigure(0, weight=1)
        cb_f = ctk.CTkFrame(opt_f, fg_color="transparent")
        cb_f.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        self.export_srt_var = ctk.BooleanVar(value=True)
        self.cb_srt = ctk.CTkCheckBox(cb_f, text="字幕ファイルを別で書き出す (.srt)", variable=self.export_srt_var)
        self.cb_srt.pack(side="left", padx=10)

        self.export_ae_csv_var = ctk.BooleanVar(value=False)
        self.cb_csv = ctk.CTkCheckBox(cb_f, text="Ae用時間軸CSVを書き出す (.csv)", variable=self.export_ae_csv_var)
        self.cb_csv.pack(side="left", padx=10)

        self.no_burn_in_var = ctk.BooleanVar(value=False)
        self.cb_noburn = ctk.CTkCheckBox(cb_f, text="動画に字幕を焼き付けない (生動画)", variable=self.no_burn_in_var)
        self.cb_noburn.pack(side="left", padx=10)

        self.run_btn = ctk.CTkButton(bf_right, text="🎬 登録されたすべてのキューを一括切り抜き実行 (開始)", font=ctk.CTkFont(size=16, weight="bold"), height=42, fg_color=self.theme_primary_color, hover_color=self.theme_primary_hover, command=self.start_processing_queue)
        self.run_btn.grid(row=1, column=0, padx=5, pady=5, sticky="ew")

        ctk.CTkLabel(bf_right, text="実行ログ / AI進捗:").grid(row=2, column=0, padx=5, pady=0, sticky="w")
        self.log_text = ctk.CTkTextbox(bf_right, font=("Consolas", 12))
        self.log_text.grid(row=3, column=0, padx=5, pady=2, sticky="nsew")
        self.log_text.configure(state="disabled")

        self.bf = bf
        self.switch_wizard_step("step1")

    def toggle_sidebar(self, force_state=None):
        if force_state is not None:
            self.sidebar_collapsed = force_state
        else:
            self.sidebar_collapsed = not getattr(self, "sidebar_collapsed", False)
            
        if self.sidebar_collapsed:
            self.sidebar_wizard.configure(width=52)
            self.tab_run.grid_columnconfigure(0, minsize=52)
            if hasattr(self, "sidebar_title_label") and self.sidebar_title_label.winfo_ismapped():
                self.sidebar_title_label.pack_forget()
            for key, btn in self.wizard_buttons.items():
                if key == "step1": btn.configure(text="①", width=36)
                elif key == "step2": btn.configure(text="②", width=36)
                elif key == "step3": btn.configure(text="③", width=36)
        else:
            self.sidebar_wizard.configure(width=180)
            self.tab_run.grid_columnconfigure(0, minsize=180)
            if hasattr(self, "sidebar_title_label") and not self.sidebar_title_label.winfo_ismapped():
                self.sidebar_title_label.pack(side="left", padx=5)
            for key, btn in self.wizard_buttons.items():
                if key == "step1": btn.configure(text="① 切り抜き候補", width=160)
                elif key == "step2": btn.configure(text="② 字幕・編集", width=160)
                elif key == "step3": btn.configure(text="③ 書き出し・ログ", width=160)

    def on_window_configure(self, event):
        if event.widget != self: return
        w = event.width
        self.update_responsive_layout(w)

    def update_responsive_layout(self, width):
        if not hasattr(self, "char_panel") or not hasattr(self, "rf"): return
        
        is_narrow = (width < 1150)
        current_mode = getattr(self, "step2_layout_mode", None)
        target_mode = "narrow" if is_narrow else "wide"
        
        if current_mode != target_mode:
            self.step2_layout_mode = target_mode
            
            if target_mode == "narrow":
                # 2-Tier Stacked Vertical Layout for Narrow Windows (二段構成):
                # Row 3: Video Preview Box (Full Width)
                # Row 4: Subtitle Timeline Editor (Full Width)
                # Row 5: Add Queue Button
                # Row 6: Style/Character Panel
                self.preview_container.grid_forget()
                self.sub_scroll.grid_forget()
                self.add_queue_btn.grid_forget()
                self.char_panel.grid_forget()
                
                self.rf.grid_columnconfigure(2, weight=0, minsize=0)
                self.rf.grid_columnconfigure(0, weight=1)
                self.rf.grid_columnconfigure(1, weight=1)
                
                # Row 3: Video Preview Box (Full Width)
                self.preview_container.configure(height=340)
                self.preview_container.grid(row=3, column=0, columnspan=2, padx=10, pady=5, sticky="ew")
                self.rf.grid_rowconfigure(3, weight=0, minsize=340)
                
                # Row 4: Subtitle Timeline Editor (Full Width)
                self.sub_scroll.configure(height=260)
                self.sub_scroll.grid(row=4, column=0, columnspan=2, padx=10, pady=5, sticky="ew")
                self.rf.grid_rowconfigure(4, weight=0, minsize=260)
                
                # Row 5: Add Queue Button
                self.add_queue_btn.grid(row=5, column=0, columnspan=2, padx=10, pady=8, sticky="ew")
                
                # Row 6: Style/Character Panel
                self.char_panel.configure(height=220)
                self.char_panel.grid(row=6, column=0, columnspan=2, padx=10, pady=5, sticky="ew")
                self.rf.grid_rowconfigure(6, weight=0, minsize=220)
                
            else:
                # Wide Mode: Side-by-side 3 columns
                self.preview_container.grid_forget()
                self.sub_scroll.grid_forget()
                self.add_queue_btn.grid_forget()
                self.char_panel.grid_forget()
                
                self.rf.grid_rowconfigure(4, weight=0, minsize=0)
                self.rf.grid_rowconfigure(5, weight=0, minsize=0)
                self.rf.grid_rowconfigure(6, weight=0, minsize=0)
                
                self.rf.grid_columnconfigure(0, weight=1)
                self.rf.grid_columnconfigure(1, weight=1)
                self.rf.grid_columnconfigure(2, weight=0, minsize=280)
                
                self.preview_container.configure(height=340)
                self.preview_container.grid(row=3, column=0, padx=(10, 4), pady=5, sticky="nsew")
                
                self.sub_scroll.configure(height=220)
                self.sub_scroll.grid(row=3, column=1, padx=(4, 10), pady=5, sticky="nsew")
                self.rf.grid_rowconfigure(3, weight=1, minsize=340)
                
                self.add_queue_btn.grid(row=4, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
                
                self.char_panel.configure(height=200)
                self.char_panel.grid(row=1, column=2, rowspan=4, padx=(10, 8), pady=5, sticky="nsew")
                
        if width < 880 and not getattr(self, "sidebar_collapsed", False):
            self.toggle_sidebar(force_state=True)

    def switch_wizard_step(self, step):
        self.step1_frame.pack_forget()
        self.step2_frame.pack_forget()
        self.step3_frame.pack_forget()

        for k, btn in self.wizard_buttons.items():
            if k == step:
                btn.configure(fg_color=self.theme_primary_color, hover_color=self.theme_primary_hover)
            else:
                btn.configure(fg_color="transparent", hover_color="#2b2b2b" if ctk.get_appearance_mode() == "Dark" else "#e0e0e0")

        if step == "step1":
            self.step1_frame.pack(fill="both", expand=True)
        elif step == "step2":
            self.step2_frame.pack(fill="both", expand=True)
            if self.jobs and self.active_job_index == -1:
                self.load_job_to_editor(0)
            elif 0 <= self.active_job_index < len(self.jobs):
                self.render_subtitle_editor_from_active_job()
                self.refresh_job_select_menu()
        elif step == "step3":
            self.step3_frame.pack(fill="both", expand=True)

    def setup_char_panel(self):
        cp_title = ctk.CTkLabel(self.char_panel, text="文字・段落", font=ctk.CTkFont(weight="bold", size=13))
        cp_title.pack(anchor="w", padx=10, pady=(8, 4))
        
        sep = ctk.CTkFrame(self.char_panel, height=2, fg_color="#3a3a3a")
        sep.pack(fill="x", padx=10, pady=2)
        
        import tkinter.font as tkfont
        try: all_families = set(tkfont.families(self))
        except Exception: all_families = set()
        preferred_fonts = ["MS Gothic", "Meiryo", "Yu Gothic", "Segoe UI", "Arial"]
        font_list = [f for f in preferred_fonts if f in all_families]
        font_list.extend(sorted([f for f in all_families if f not in font_list]))
        
        font_lbl = ctk.CTkLabel(self.char_panel, text="フォント (T):", font=ctk.CTkFont(size=11))
        font_lbl.pack(anchor="w", padx=10, pady=(4, 0))
        self.font_menu = ctk.CTkOptionMenu(self.char_panel, values=font_list[:35], width=260, height=24, command=lambda _: self.on_text_style_changed())
        default_font = "MS Gothic" if "MS Gothic" in font_list else font_list[0]
        self.font_menu.set(default_font)
        self.font_menu.pack(anchor="w", padx=10, pady=2)

        size_pos_row = ctk.CTkFrame(self.char_panel, fg_color="transparent")
        size_pos_row.pack(fill="x", padx=10, pady=4)
        
        size_frame = ctk.CTkFrame(size_pos_row, fg_color="transparent")
        size_frame.pack(side="left", fill="both", expand=True)
        ctk.CTkLabel(size_frame, text="サイズ:", font=ctk.CTkFont(size=11)).pack(anchor="w")
        self.fontsize_menu = ctk.CTkOptionMenu(size_frame, values=["24", "28", "32", "36", "40", "44", "48", "54", "64", "72", "80", "96"], width=120, height=24, command=lambda _: self.on_text_style_changed())
        self.fontsize_menu.set("36")
        self.fontsize_menu.pack(anchor="w", fill="x")

        pos_frame = ctk.CTkFrame(size_pos_row, fg_color="transparent")
        pos_frame.pack(side="right", fill="both", expand=True, padx=(10, 0))
        self.margin_v_lbl = ctk.CTkLabel(pos_frame, text="位置 Y (500 px):", font=ctk.CTkFont(size=11))
        self.margin_v_lbl.pack(anchor="w")
        self.margin_v_slider = ctk.CTkSlider(pos_frame, from_=20.0, to=1920.0, number_of_steps=190, command=self.on_margin_v_slider_changed, height=16)
        self.margin_v_slider.set(500.0)
        self.margin_v_slider.pack(anchor="w", fill="x", pady=4)

        color_lbl = ctk.CTkLabel(self.char_panel, text="テキスト色 (HEX/RGB):", font=ctk.CTkFont(size=11))
        color_lbl.pack(anchor="w", padx=10, pady=(4, 0))
        
        color_row = ctk.CTkFrame(self.char_panel, fg_color="transparent")
        color_row.pack(fill="x", padx=10, pady=2)
        self.color_entry = ctk.CTkEntry(color_row, width=120, height=24)
        self.color_entry.insert(0, "#FFFF00")
        self.color_entry.bind("<FocusOut>", lambda _: self.on_text_style_changed())
        self.color_entry.bind("<Return>", lambda _: self.on_text_style_changed())
        self.color_entry.pack(side="left", fill="x", expand=True)
        ctk.CTkButton(color_row, text="🎨", width=24, height=24, command=lambda: self.open_color_picker("color")).pack(side="right", padx=(5, 0))

        style_row = ctk.CTkFrame(self.char_panel, fg_color="transparent")
        style_row.pack(fill="x", padx=10, pady=4)
        self.bold_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(style_row, text="太字 (Bold)", variable=self.bold_var, font=ctk.CTkFont(size=11), command=lambda: self.on_text_style_changed()).pack(side="left", expand=True, anchor="w")
        self.italic_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(style_row, text="斜体 (Italic)", variable=self.italic_var, font=ctk.CTkFont(size=11), command=lambda: self.on_text_style_changed()).pack(side="right", expand=True, anchor="w")

        outline_row = ctk.CTkFrame(self.char_panel, fg_color="transparent")
        outline_row.pack(fill="x", padx=10, pady=4)
        
        ow_frame = ctk.CTkFrame(outline_row, fg_color="transparent")
        ow_frame.pack(side="left", fill="both", expand=True)
        ctk.CTkLabel(ow_frame, text="境界線の太さ:", font=ctk.CTkFont(size=11)).pack(anchor="w")
        self.outline_width_menu = ctk.CTkOptionMenu(ow_frame, values=["0", "1", "2", "3", "4", "5", "6", "8"], width=120, height=24, command=lambda _: self.on_text_style_changed())
        self.outline_width_menu.set("2")
        self.outline_width_menu.pack(anchor="w", fill="x")

        oc_frame = ctk.CTkFrame(outline_row, fg_color="transparent")
        oc_frame.pack(side="right", fill="both", expand=True, padx=(10, 0))
        ctk.CTkLabel(oc_frame, text="境界線色 (HEX/RGB):", font=ctk.CTkFont(size=11)).pack(anchor="w")
        oc_entry_row = ctk.CTkFrame(oc_frame, fg_color="transparent")
        oc_entry_row.pack(fill="x")
        self.outline_color_entry = ctk.CTkEntry(oc_entry_row, width=90, height=24)
        self.outline_color_entry.insert(0, "#000000")
        self.outline_color_entry.bind("<FocusOut>", lambda _: self.on_text_style_changed())
        self.outline_color_entry.bind("<Return>", lambda _: self.on_text_style_changed())
        self.outline_color_entry.pack(side="left", fill="x", expand=True)
        ctk.CTkButton(oc_entry_row, text="🎨", width=24, height=24, command=lambda: self.open_color_picker("outline")).pack(side="right", padx=(5, 0))

        shadow_row = ctk.CTkFrame(self.char_panel, fg_color="transparent")
        shadow_row.pack(fill="x", padx=10, pady=4)
        
        sd_frame = ctk.CTkFrame(shadow_row, fg_color="transparent")
        sd_frame.pack(side="left", fill="both", expand=True)
        ctk.CTkLabel(sd_frame, text="影の深さ:", font=ctk.CTkFont(size=11)).pack(anchor="w")
        self.shadow_depth_menu = ctk.CTkOptionMenu(sd_frame, values=["0", "1", "2", "3", "4", "5", "6", "8"], width=120, height=24, command=lambda _: self.on_text_style_changed())
        self.shadow_depth_menu.set("0")
        self.shadow_depth_menu.pack(anchor="w", fill="x")

        sa_frame = ctk.CTkFrame(shadow_row, fg_color="transparent")
        sa_frame.pack(side="right", fill="both", expand=True, padx=(10, 0))
        self.shadow_alpha_lbl = ctk.CTkLabel(sa_frame, text="影不透明度 (1.00):", font=ctk.CTkFont(size=11))
        self.shadow_alpha_lbl.pack(anchor="w")
        self.shadow_alpha_slider = ctk.CTkSlider(sa_frame, from_=0.0, to=1.0, number_of_steps=100, command=self.on_shadow_alpha_changed, height=16)
        self.shadow_alpha_slider.set(1.0)
        self.shadow_alpha_slider.pack(fill="x", pady=4)

        ctk.CTkLabel(self.char_panel, text="配置 (Alignment):", font=ctk.CTkFont(size=11)).pack(anchor="w", padx=10, pady=(4, 0))
        self.alignment_btn = ctk.CTkSegmentedButton(self.char_panel, values=["左寄せ", "中央寄せ", "右寄せ"],
                                                    font=ctk.CTkFont(size=11), command=lambda _: self.on_text_style_changed())
        self.alignment_btn.set("中央寄せ")
        self.alignment_btn.pack(fill="x", padx=10, pady=2)

        self.cb_loud_zoom = ctk.CTkCheckBox(self.char_panel, text="大声ズームを有効にする", variable=self.loud_zoom_var, font=ctk.CTkFont(size=11), command=lambda: self.on_text_style_changed())
        self.cb_loud_zoom.pack(anchor="w", padx=10, pady=4)

        sep2 = ctk.CTkFrame(self.char_panel, height=2, fg_color="#3a3a3a")
        sep2.pack(fill="x", padx=10, pady=2)

        ctk.CTkLabel(self.char_panel, text="画像オーバーレイ", font=ctk.CTkFont(weight="bold", size=13)).pack(anchor="w", padx=10, pady=(4, 2))
        
        self.cb_overlay = ctk.CTkCheckBox(self.char_panel, text="画像オーバーレイを有効にする", variable=self.overlay_enabled_var, font=ctk.CTkFont(size=11), command=lambda: self.on_text_style_changed())
        self.cb_overlay.pack(anchor="w", padx=10, pady=2)

        preset_row = ctk.CTkFrame(self.char_panel, fg_color="transparent")
        preset_row.pack(fill="x", padx=10, pady=2)
        ctk.CTkLabel(preset_row, text="プリセット:", font=ctk.CTkFont(size=11)).pack(side="left")
        self.preset_menu = ctk.CTkOptionMenu(preset_row, values=[], height=24, width=130, command=self.on_preset_selected)
        self.preset_menu.set("(選択なし)")
        self.preset_menu.pack(side="left", padx=5)
        self.preset_folder_btn = ctk.CTkButton(preset_row, text="📁", width=40, height=24, command=self.open_presets_folder)
        self.preset_folder_btn.pack(side="left", padx=2)

        choose_row = ctk.CTkFrame(self.char_panel, fg_color="transparent")
        choose_row.pack(fill="x", padx=10, pady=2)
        self.overlay_path_entry = ctk.CTkEntry(choose_row, placeholder_text="画像パス...", height=24)
        self.overlay_path_entry.pack(side="left", fill="x", expand=True)
        self.overlay_path_entry.bind("<FocusOut>", lambda _: self.on_text_style_changed())
        self.overlay_path_entry.bind("<Return>", lambda _: self.on_text_style_changed())
        ctk.CTkButton(choose_row, text="参照...", width=50, height=24, command=self.select_overlay_image).pack(side="right")

        # Anchor Point selection row
        anchor_row = ctk.CTkFrame(self.char_panel, fg_color="transparent")
        anchor_row.pack(fill="x", padx=10, pady=2)
        ctk.CTkLabel(anchor_row, text="基準アンカーポイント (Anchor):", font=ctk.CTkFont(size=11)).pack(side="left")
        self.overlay_anchor_menu = ctk.CTkOptionMenu(
            anchor_row, 
            values=["重心 (中央)", "左上", "右上", "左下", "右下"], 
            height=24,
            command=lambda _: self.on_text_style_changed()
        )
        self.overlay_anchor_menu.set("重心 (中央)")
        self.overlay_anchor_menu.pack(side="left", padx=5)

        # Position X Slider
        self.overlay_x_lbl = ctk.CTkLabel(self.char_panel, text="位置 X (100 px):", font=ctk.CTkFont(size=11))
        self.overlay_x_lbl.pack(anchor="w", padx=10, pady=(3, 0))
        self.overlay_x_slider = ctk.CTkSlider(self.char_panel, from_=-500.0, to=1500.0, number_of_steps=2000, command=self.on_overlay_x_slider_changed)
        self.overlay_x_slider.set(100.0)
        self.overlay_x_slider.pack(fill="x", padx=10, pady=2)

        # Position Y Slider
        self.overlay_y_lbl = ctk.CTkLabel(self.char_panel, text="位置 Y (100 px):", font=ctk.CTkFont(size=11))
        self.overlay_y_lbl.pack(anchor="w", padx=10, pady=(3, 0))
        self.overlay_y_slider = ctk.CTkSlider(self.char_panel, from_=-500.0, to=2400.0, number_of_steps=2900, command=self.on_overlay_y_slider_changed)
        self.overlay_y_slider.set(100.0)
        self.overlay_y_slider.pack(fill="x", padx=10, pady=2)

        # Size slider
        self.overlay_scale_lbl = ctk.CTkLabel(self.char_panel, text="倍率 (100%):", font=ctk.CTkFont(size=11))
        self.overlay_scale_lbl.pack(anchor="w", padx=10, pady=(3, 0))
        self.overlay_scale_slider = ctk.CTkSlider(self.char_panel, from_=0.1, to=3.0, number_of_steps=290, command=self.on_overlay_scale_slider_changed)
        self.overlay_scale_slider.set(1.0)
        self.overlay_scale_slider.pack(fill="x", padx=10, pady=2)

        # Rotation slider
        self.overlay_angle_lbl = ctk.CTkLabel(self.char_panel, text="角度 (0°):", font=ctk.CTkFont(size=11))
        self.overlay_angle_lbl.pack(anchor="w", padx=10, pady=(3, 0))
        self.overlay_angle_slider = ctk.CTkSlider(self.char_panel, from_=-180.0, to=180.0, number_of_steps=360, command=self.on_overlay_angle_slider_changed)
        self.overlay_angle_slider.set(0.0)
        self.overlay_angle_slider.pack(fill="x", padx=10, pady=2)

        # Opacity slider
        self.overlay_opacity_lbl = ctk.CTkLabel(self.char_panel, text="不透明度 (1.00):", font=ctk.CTkFont(size=11))
        self.overlay_opacity_lbl.pack(anchor="w", padx=10, pady=(3, 0))
        self.overlay_opacity_slider = ctk.CTkSlider(self.char_panel, from_=0.0, to=1.0, number_of_steps=100, command=self.on_overlay_opacity_slider_changed)
        self.overlay_opacity_slider.set(1.0)
        self.overlay_opacity_slider.pack(fill="x", padx=10, pady=2)



    def save_project(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON Project File", "*.json")],
            initialdir=".",
            title="作業状態を保存"
        )
        if not file_path:
            return
            
        if self.active_job_index != -1:
            self.save_current_editor_to_active_job()
            
        data = {
            "video_path": self.video_entry.get().strip(),
            "jobs": self.jobs,
            "processing_queue": self.processing_queue,
            "buffer_seconds": int(self.buffer_slider.get()),
            "export_srt": self.export_srt_var.get(),
            "export_csv": self.export_ae_csv_var.get(),
            "no_burn_in": self.no_burn_in_var.get()
        }
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            messagebox.showinfo("保存完了", "作業状態を保存しました。")
        except Exception as e:
            messagebox.showerror("エラー", f"保存に失敗しました:\n{e}")

    def load_project(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON Project File", "*.json")],
            initialdir=".",
            title="保存した作業状態を読み込み"
        )
        if not file_path:
            return
            
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            self.video_entry.delete(0, "end")
            self.video_entry.insert(0, data.get("video_path", ""))
            
            self.jobs = data.get("jobs", [])
            self.job_vars = [ctk.BooleanVar(value=True) for _ in self.jobs]
            self.active_job_index = -1
            
            self.processing_queue = data.get("processing_queue", [])
            
            self.buffer_slider.set(data.get("buffer_seconds", 0))
            self.update_buffer_label(self.buffer_slider.get())
            self.export_srt_var.set(data.get("export_srt", True))
            self.export_ae_csv_var.set(data.get("export_csv", False))
            self.no_burn_in_var.set(data.get("no_burn_in", False))
            
            self.render_job_list()
            self.render_queue_list()
            self.render_subtitle_editor_from_active_job()
            self.refresh_job_select_menu()
            
            messagebox.showinfo("読込完了", "作業状態を復元しました。")
        except Exception as e:
            messagebox.showerror("エラー", f"読み込みに失敗しました:\n{e}")

    def setup_global_tab(self):
        # Create left sidebar and right content area inside self.tab_global
        self.tab_global.grid_columnconfigure(0, weight=0, minsize=180)
        self.tab_global.grid_columnconfigure(1, weight=1)
        self.tab_global.grid_rowconfigure(0, weight=1)

        # Left Sidebar Frame
        self.global_sidebar = ctk.CTkFrame(self.tab_global, width=180, corner_radius=8)
        self.global_sidebar.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="nsew")
        self.global_sidebar.pack_propagate(False)

        # Right Content Frame
        self.global_content = ctk.CTkFrame(self.tab_global, corner_radius=8)
        self.global_content.grid(row=0, column=1, padx=(5, 10), pady=10, sticky="nsew")

        # Define subframes inside the content area
        self.sub_frame_ui = ctk.CTkFrame(self.global_content, fg_color="transparent")
        self.sub_frame_profile = ctk.CTkFrame(self.global_content, fg_color="transparent")
        self.sub_frame_dict = ctk.CTkFrame(self.global_content, fg_color="transparent")

        # Sidebar title
        ctk.CTkLabel(self.global_sidebar, text="⚙️ 全体設定メニュー", font=ctk.CTkFont(weight="bold", size=13)).pack(pady=(15, 10))

        # Sidebar buttons
        self.sidebar_buttons = {}
        tabs = [
            ("ui", "全体・表示設定"),
            ("profile", "パーソナルデータ"),
            ("dict", "文字起こし辞書")
        ]
        for key, label in tabs:
            btn = ctk.CTkButton(
                self.global_sidebar,
                text=label,
                anchor="w",
                height=35,
                fg_color="transparent",
                text_color="white" if ctk.get_appearance_mode() == "Dark" else "black",
                font=ctk.CTkFont(size=11),
                command=lambda k=key: self.switch_global_tab(k)
            )
            btn.pack(fill="x", padx=10, pady=4)
            self.sidebar_buttons[key] = btn

        # Initialize sub views
        self.setup_global_ui_tab()   # places widgets inside self.sub_frame_ui
        self.setup_profile_tab()     # places widgets inside self.sub_frame_profile
        self.setup_dict_tab()        # places widgets inside self.sub_frame_dict

        # Default active tab is UI settings
        self.switch_global_tab("ui")

    def switch_global_tab(self, tab_name):
        # Hide all subframes
        self.sub_frame_ui.pack_forget()
        self.sub_frame_profile.pack_forget()
        self.sub_frame_dict.pack_forget()

        # Reset button styles
        for name, btn in self.sidebar_buttons.items():
            if name == tab_name:
                btn.configure(fg_color=self.theme_primary_color, hover_color=self.theme_primary_hover)
            else:
                btn.configure(fg_color="transparent", hover_color="#2b2b2b" if ctk.get_appearance_mode() == "Dark" else "#e0e0e0")

        # Show selected frame
        if tab_name == "ui":
            self.sub_frame_ui.pack(fill="both", expand=True, padx=10, pady=10)
        elif tab_name == "profile":
            self.sub_frame_profile.pack(fill="both", expand=True, padx=10, pady=10)
        elif tab_name == "dict":
            self.sub_frame_dict.pack(fill="both", expand=True, padx=10, pady=10)

    def setup_global_ui_tab(self):
        frame = ctk.CTkFrame(self.sub_frame_ui)
        frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        # UI Font family option menu
        f_row = ctk.CTkFrame(frame, fg_color="transparent")
        f_row.pack(fill="x", padx=10, pady=8)
        ctk.CTkLabel(f_row, text="UIフォントファミリー:").pack(side="left", padx=10)
        self.ui_font_menu = ctk.CTkOptionMenu(
            f_row, 
            values=["Yu Gothic UI", "Segoe UI", "Meiryo", "MS Gothic", "Arial"],
        )
        self.ui_font_menu.set(self.ui_font_family)
        self.ui_font_menu.pack(side="left", padx=5)

        # UI Font size option menu
        s_row = ctk.CTkFrame(frame, fg_color="transparent")
        s_row.pack(fill="x", padx=10, pady=8)
        ctk.CTkLabel(s_row, text="UIフォントサイズ:       ").pack(side="left", padx=10)
        self.ui_font_size_menu = ctk.CTkOptionMenu(
            s_row,
            values=["10", "11", "12", "13", "14", "15", "16", "18"],
        )
        self.ui_font_size_menu.set(str(self.ui_font_size))
        self.ui_font_size_menu.pack(side="left", padx=5)

        # Buffer seconds setting
        b_row = ctk.CTkFrame(frame, fg_color="transparent")
        b_row.pack(fill="x", padx=10, pady=8)
        self.buffer_lbl = ctk.CTkLabel(b_row, text=f"前後追加バッファ時間 ({self.config_data.get('buffer_seconds', 0)}秒):")
        self.buffer_lbl.pack(side="left", padx=10)
        self.buffer_slider = ctk.CTkSlider(
            b_row, from_=0, to=60, number_of_steps=60,
            command=self.update_buffer_label
        )
        self.buffer_slider.set(self.config_data.get("buffer_seconds", 0))
        self.buffer_slider.pack(side="left", padx=5, fill="x", expand=True)

        # Save Button
        save_btn = ctk.CTkButton(
            frame, text="💾 設定を保存して適用",
            font=ctk.CTkFont(weight="bold"),
            fg_color=self.theme_primary_color, hover_color=self.theme_primary_hover,
            command=self.save_global_ui_settings
        )
        save_btn.pack(pady=20)

    def save_global_ui_settings(self):
        self.config_data["ui_font_family"] = self.ui_font_menu.get()
        self.config_data["ui_font_size"] = int(self.ui_font_size_menu.get())
        self.config_data["buffer_seconds"] = int(self.buffer_slider.get())
        self.config_manager.save_config(self.config_data)
        messagebox.showinfo("保存完了", "全体・表示設定を保存しました。\nフォント設定はアプリの再起動後に適用されます。")

    def setup_prompt_tab(self):
        self.tab_prompt.grid_rowconfigure(0, weight=1)
        self.tab_prompt.grid_columnconfigure(0, weight=1)
        self.tab_prompt.grid_columnconfigure(1, weight=1)

        # 左カラム: Geminiプロンプト編集 & コントロール
        left_frame = ctk.CTkFrame(self.tab_prompt, fg_color="transparent")
        left_frame.grid(row=0, column=0, padx=(10, 5), pady=5, sticky="nsew")
        left_frame.grid_columnconfigure(0, weight=1)
        left_frame.grid_rowconfigure(3, weight=1)
        left_frame.grid_rowconfigure(4, weight=0)

        # 1行目: ボタン群
        ptf = ctk.CTkFrame(left_frame)
        ptf.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        ptf.grid_columnconfigure(0, weight=1)
        ptf.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(ptf, text="🌐 Geminiを開く", font=ctk.CTkFont(weight="bold"), height=35,
                      fg_color=self.theme_primary_color, hover_color=self.theme_primary_hover, command=self.open_gemini).grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        ctk.CTkButton(ptf, text="🎬 YouTube Studioを開く", font=ctk.CTkFont(weight="bold"), height=35,
                      fg_color="#e52d27", hover_color="#b31217", command=self.open_youtube_studio).grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        # 2行目: テンプレート管理
        ptf2 = ctk.CTkFrame(left_frame)
        ptf2.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        ptf2.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(ptf2, text="指示書テンプレート:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.tpl_menu = ctk.CTkOptionMenu(ptf2, values=list(self.config_data["templates"].keys()), command=self.on_template_changed)
        self.tpl_menu.set(self.config_data["active_template"])
        self.tpl_menu.grid(row=0, column=1, padx=5, pady=10, sticky="ew")
        
        ctk.CTkButton(ptf2, text="削除", width=55, fg_color="firebrick", hover_color="darkred", command=self.delete_current_template).grid(row=0, column=2, padx=5, pady=10)
        ctk.CTkButton(ptf2, text="別名保存...", width=95, command=self.save_new_template).grid(row=0, column=3, padx=10, pady=10)

        # 3行目: YouTube動画URL ＋ 目標個数
        yf = ctk.CTkFrame(left_frame)
        yf.grid(row=2, column=0, padx=5, pady=5, sticky="ew")
        yf.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(yf, text="🎥 対象のYouTube動画リンク: ", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=10, pady=8, sticky="w")
        self.youtube_entry = ctk.CTkEntry(yf, placeholder_text="https://www.youtube.com/watch?v=...")
        self.youtube_entry.insert(0, self.config_data.get("last_youtube_url", ""))
        self.youtube_entry.grid(row=0, column=1, padx=10, pady=8, sticky="ew")
        
        count_frame = ctk.CTkFrame(yf, fg_color="transparent")
        count_frame.grid(row=0, column=2, padx=10, pady=8, sticky="e")
        ctk.CTkLabel(count_frame, text="目標:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=2)
        self.count_entry = ctk.CTkEntry(count_frame, width=35)
        self.count_entry.insert(0, str(self.config_data["target_count"]))
        self.count_entry.pack(side="left", padx=2)
        ctk.CTkLabel(count_frame, text="個", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=2)

        # 4行目: プロンプト編集テキストボックス
        pmf = ctk.CTkFrame(left_frame)
        pmf.grid(row=3, column=0, padx=5, pady=5, sticky="nsew")
        pmf.grid_rowconfigure(1, weight=1)
        pmf.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(pmf, text="【プロンプト編集】 {video_url}, {count}, {profile}, {video_info} はコピー時に自動置換されます", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.prompt_textbox = ctk.CTkTextbox(pmf, font=(self.ui_font_family, self.ui_font_size))
        self.prompt_textbox.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")

        # 5行目: コピーボタン等
        pbf = ctk.CTkFrame(left_frame)
        pbf.grid(row=4, column=0, padx=5, pady=10, sticky="ew")
        ctk.CTkButton(pbf, text="現在のテンプレートに上書き保存", width=200, command=self.save_current_template).pack(side="left", padx=10, pady=10)
        ctk.CTkButton(pbf, text="📋 プロンプトをコピー", font=ctk.CTkFont(size=14, weight="bold"), height=38,
                      fg_color="forestgreen", hover_color="darkgreen", command=self.copy_prompt).pack(side="right", padx=10, pady=10)

        # 右カラム: パーソナルデータ ＆ 動画情報設定 (スクロール可能)
        right_frame = ctk.CTkFrame(self.tab_prompt, fg_color="transparent")
        right_frame.grid(row=0, column=1, padx=(5, 10), pady=5, sticky="nsew")
        right_frame.grid_columnconfigure(0, weight=1)
        right_frame.grid_rowconfigure(0, weight=1)

        scroll = ctk.CTkScrollableFrame(right_frame, label_text="✨ パーソナルデータ ＆ 動画情報設定")
        scroll.grid(row=0, column=0, sticky="nsew")
        scroll.grid_columnconfigure(0, weight=1)

        # SECTION 1: 配信者パーソナルデータ
        sec1 = ctk.CTkFrame(scroll)
        sec1.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        sec1.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(sec1, text="👤 配信者・チャンネルのパーソナルデータ", font=ctk.CTkFont(size=13, weight="bold")).grid(row=0, column=0, padx=10, pady=(10, 4), sticky="w")
        ctk.CTkLabel(sec1, text="※ (★必須) 項目を入力すると高精度なプロンプトが作成されます。", font=ctk.CTkFont(size=10), text_color="orange").grid(row=1, column=0, padx=10, pady=(0, 8), sticky="w")

        # 1. 配信者名・名義 (★必須)
        ctk.CTkLabel(sec1, text="■ 配信者名・チャンネル名 (★必須)", font=ctk.CTkFont(weight="bold", size=11), text_color="#ff7b7b").grid(row=2, column=0, padx=10, pady=(4, 1), sticky="w")
        self.profile_name_entry = ctk.CTkEntry(sec1, placeholder_text="例: 初狐羽鹿 / @UikoUka")
        self.profile_name_entry.insert(0, self.config_data.get("last_streamer_name", ""))
        self.profile_name_entry.grid(row=3, column=0, padx=10, pady=(0, 6), sticky="ew")

        # 2. キャラクター・特徴 (★必須)
        ctk.CTkLabel(sec1, text="■ キャラクター・主な特徴・性格 (★必須)", font=ctk.CTkFont(weight="bold", size=11), text_color="#ff7b7b").grid(row=4, column=0, padx=10, pady=(4, 1), sticky="w")
        self.profile_char_entry = ctk.CTkEntry(sec1, placeholder_text="例: ツッコミ系VTuber、ポンコツ、元気、毒舌など")
        self.profile_char_entry.insert(0, self.config_data.get("last_streamer_profile_char", ""))
        self.profile_char_entry.grid(row=5, column=0, padx=10, pady=(0, 6), sticky="ew")

        # 3. 現在の主な視聴者層 (★必須)
        ctk.CTkLabel(sec1, text="■ 現在の主な視聴者層・ターゲット (★必須)", font=ctk.CTkFont(weight="bold", size=11), text_color="#ff7b7b").grid(row=6, column=0, padx=10, pady=(4, 1), sticky="w")
        self.profile_target_entry = ctk.CTkEntry(sec1, placeholder_text="例: 10代〜20代男性、ゲーム好き、癒やし求む層")
        self.profile_target_entry.insert(0, self.config_data.get("last_streamer_profile_target", ""))
        self.profile_target_entry.grid(row=7, column=0, padx=10, pady=(0, 6), sticky="ew")

        # 4. 今後狙いたい視聴者層 (★必須)
        ctk.CTkLabel(sec1, text="■ 今後狙いたい・獲得したい視聴者層 (★必須)", font=ctk.CTkFont(weight="bold", size=11), text_color="#ff7b7b").grid(row=8, column=0, padx=10, pady=(4, 1), sticky="w")
        self.profile_target_future_entry = ctk.CTkEntry(sec1, placeholder_text="例: ショート動画から新規で流入させたい同世代の女性層など")
        self.profile_target_future_entry.insert(0, self.config_data.get("last_streamer_profile_target_future", ""))
        self.profile_target_future_entry.grid(row=9, column=0, padx=10, pady=(0, 6), sticky="ew")

        # 5. 話し方・口調・口癖 (任意)
        ctk.CTkLabel(sec1, text="■ 話し方・口調・口癖 (任意)", font=ctk.CTkFont(weight="bold", size=11)).grid(row=10, column=0, padx=10, pady=(4, 1), sticky="w")
        self.profile_tone_entry = ctk.CTkEntry(sec1, placeholder_text="例: 「〜だよ」「〜じゃん」、語尾に「〜きつね」、関西弁")
        self.profile_tone_entry.insert(0, self.config_data.get("last_streamer_profile_tone", ""))
        self.profile_tone_entry.grid(row=11, column=0, padx=10, pady=(0, 6), sticky="ew")

        # 6. 定番フレーズ・決め台詞 (任意)
        ctk.CTkLabel(sec1, text="■ 定番フレーズ・決め台詞 (任意)", font=ctk.CTkFont(weight="bold", size=11)).grid(row=12, column=0, padx=10, pady=(4, 1), sticky="w")
        self.profile_phrases_entry = ctk.CTkEntry(sec1, placeholder_text="例: 「おつ狐〜！」「絶対に許さん！」")
        self.profile_phrases_entry.insert(0, self.config_data.get("last_streamer_profile_phrases", ""))
        self.profile_phrases_entry.grid(row=13, column=0, padx=10, pady=(0, 6), sticky="ew")

        # 7. 得意ジャンル・テーマ (任意)
        ctk.CTkLabel(sec1, text="■ 得意ジャンル・主な配信テーマ (任意)", font=ctk.CTkFont(weight="bold", size=11)).grid(row=14, column=0, padx=10, pady=(4, 1), sticky="w")
        self.profile_genre_entry = ctk.CTkEntry(sec1, placeholder_text="例: 雑談配信、レトロゲーム、歌枠、逆転裁判")
        self.profile_genre_entry.insert(0, self.config_data.get("last_streamer_profile_genre", ""))
        self.profile_genre_entry.grid(row=15, column=0, padx=10, pady=(0, 6), sticky="ew")

        # 8. NG表現・避ける言葉 (任意)
        ctk.CTkLabel(sec1, text="■ NGワード・避ける表現 (任意)", font=ctk.CTkFont(weight="bold", size=11)).grid(row=16, column=0, padx=10, pady=(4, 1), sticky="w")
        self.profile_ng_entry = ctk.CTkEntry(sec1, placeholder_text="例: ネガティブな発言、過度な下ネタ、他者の批判")
        self.profile_ng_entry.insert(0, self.config_data.get("last_streamer_profile_ng", ""))
        self.profile_ng_entry.grid(row=17, column=0, padx=10, pady=(0, 6), sticky="ew")

        # 9. 登録者数 (任意)
        ctk.CTkLabel(sec1, text="■ 登録者数・フォロワー数 (任意)", font=ctk.CTkFont(weight="bold", size=11)).grid(row=18, column=0, padx=10, pady=(4, 1), sticky="w")
        self.profile_subscribers_entry = ctk.CTkEntry(sec1, placeholder_text="例: YouTube 1万人、Twitch 5000人など")
        self.profile_subscribers_entry.insert(0, self.config_data.get("last_streamer_profile_subscribers", ""))
        self.profile_subscribers_entry.grid(row=19, column=0, padx=10, pady=(0, 6), sticky="ew")

        # 10. 主な投稿プラットフォーム (任意)
        ctk.CTkLabel(sec1, text="■ 主な投稿プラットフォーム (任意)", font=ctk.CTkFont(weight="bold", size=11)).grid(row=20, column=0, padx=10, pady=(4, 1), sticky="w")
        self.profile_platforms_entry = ctk.CTkEntry(sec1, placeholder_text="例: YouTubeショート、TikTok、Instagramリール")
        self.profile_platforms_entry.insert(0, self.config_data.get("last_streamer_profile_platforms", ""))
        self.profile_platforms_entry.grid(row=21, column=0, padx=10, pady=(0, 6), sticky="ew")

        # 11. ショート運用実績・バズり傾向 (任意)
        ctk.CTkLabel(sec1, text="■ ショート動画のバズり傾向・実績 (任意)", font=ctk.CTkFont(weight="bold", size=11)).grid(row=22, column=0, padx=10, pady=(4, 1), sticky="w")
        self.profile_shorts_entry = ctk.CTkEntry(sec1, placeholder_text="例: リアクションが大きい箇所がバズりやすい、テンポの早いツッコミが好評")
        self.profile_shorts_entry.insert(0, self.config_data.get("last_streamer_profile_shorts", ""))
        self.profile_shorts_entry.grid(row=23, column=0, padx=10, pady=(0, 10), sticky="ew")

        # SECTION 2: 動画自体の情報記入欄
        sec2 = ctk.CTkFrame(scroll)
        sec2.grid(row=1, column=0, padx=5, pady=10, sticky="ew")
        sec2.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(sec2, text="🎬 今回の対象動画自体の情報・見どころ (任意)", font=ctk.CTkFont(size=13, weight="bold")).grid(row=0, column=0, padx=10, pady=(10, 4), sticky="w")
        ctk.CTkLabel(sec2, text="※ ここに入力したデータはプロンプトの {video_info} に自動反映されます。", font=ctk.CTkFont(size=10), text_color="gray").grid(row=1, column=0, padx=10, pady=(0, 8), sticky="w")

        # 1. 動画/配信タイトル
        ctk.CTkLabel(sec2, text="■ 動画・配信のタイトル / プレイングゲーム名", font=ctk.CTkFont(weight="bold", size=11)).grid(row=2, column=0, padx=10, pady=(4, 1), sticky="w")
        self.video_title_entry = ctk.CTkEntry(sec2, placeholder_text="例: 【逆転裁判#3】裁判で大パニック！？")
        self.video_title_entry.insert(0, self.config_data.get("last_video_title", ""))
        self.video_title_entry.grid(row=3, column=0, padx=10, pady=(0, 6), sticky="ew")

        # 2. 動画の大まかな内容・ハイライト
        ctk.CTkLabel(sec2, text="■ 動画の大まかな内容・ハイライト概要", font=ctk.CTkFont(weight="bold", size=11)).grid(row=4, column=0, padx=10, pady=(4, 1), sticky="w")
        self.video_summary_entry = ctk.CTkEntry(sec2, placeholder_text="例: 証人の矛盾を見つけてドヤ顔したが完全に推理が外れて焦るシーン")
        self.video_summary_entry.insert(0, self.config_data.get("last_video_summary", ""))
        self.video_summary_entry.grid(row=5, column=0, padx=10, pady=(0, 6), sticky="ew")

        # 3. 切り抜いてほしい見どころ・テイスト
        ctk.CTkLabel(sec2, text="■ 特に切り抜いてほしい見どころ・テイスト指定", font=ctk.CTkFont(weight="bold", size=11)).grid(row=6, column=0, padx=10, pady=(4, 1), sticky="w")
        self.video_focus_entry = ctk.CTkEntry(sec2, placeholder_text="例: 爆笑シーン中心、テンポ良くツッコミを立たせる、ドラマチックな展開")
        self.video_focus_entry.insert(0, self.config_data.get("last_video_focus", ""))
        self.video_focus_entry.grid(row=7, column=0, padx=10, pady=(0, 10), sticky="ew")

        # 右カラム下部: 保存ボタン
        ctk.CTkButton(scroll, text="💾 パーソナルデータ ＆ 動画情報を保存", font=ctk.CTkFont(size=13, weight="bold"),
                      fg_color="chocolate", hover_color="sienna", height=35, command=self.save_profile_data_only).grid(row=2, column=0, padx=5, pady=10, sticky="ew")


    def setup_profile_tab(self):
        self.sub_frame_profile.grid_rowconfigure(0, weight=1)
        self.sub_frame_profile.grid_columnconfigure(0, weight=1)
        
        # 縦スクロール可能にするために CTkScrollableFrame を使用
        scroll = ctk.CTkScrollableFrame(self.sub_frame_profile)
        scroll.pack(fill="both", expand=True, padx=5, pady=5)
        scroll.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(scroll, text="【動画投稿者 / 配信者のパーソナルデータ設定】", font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0, padx=15, pady=(15, 5), sticky="w")
        ctk.CTkLabel(scroll, text="※ ここに入力された情報は、プロンプトコピー時に {profile} プレースホルダーへ自動的に埋め込まれます。", font=ctk.CTkFont(size=11), fg_color="transparent").grid(row=1, column=0, padx=15, pady=(0, 10), sticky="w")

        # 1. 配信者特徴
        ctk.CTkLabel(scroll, text="■ 配信者様（またはチャンネル）の主なキャラクターや特徴", font=ctk.CTkFont(weight="bold", size=12)).grid(row=2, column=0, padx=15, pady=(10, 2), sticky="w")
        self.profile_char_entry = ctk.CTkEntry(scroll, placeholder_text="例: ツッコミ系VTuber、ポンコツ、毒舌など")
        self.profile_char_entry.insert(0, self.config_data.get("last_streamer_profile_char", ""))
        self.profile_char_entry.grid(row=3, column=0, padx=15, pady=(0, 6), sticky="ew")

        # 2. 視聴者層
        ctk.CTkLabel(scroll, text="■ 主な視聴者層（例：10代〜20代男性、女性層、ゲーム好きなど）", font=ctk.CTkFont(weight="bold", size=12)).grid(row=4, column=0, padx=15, pady=(6, 2), sticky="w")
        self.profile_target_entry = ctk.CTkEntry(scroll, placeholder_text="例: 10代〜20代男性、ゲーム好きなど")
        self.profile_target_entry.insert(0, self.config_data.get("last_streamer_profile_target", ""))
        self.profile_target_entry.grid(row=5, column=0, padx=15, pady=(0, 6), sticky="ew")

        # 3. ジャンル/概要
        ctk.CTkLabel(scroll, text="■ この動画（または元配信）の簡単なジャンルや概要", font=ctk.CTkFont(weight="bold", size=12)).grid(row=6, column=0, padx=15, pady=(6, 2), sticky="w")
        self.profile_genre_entry = ctk.CTkEntry(scroll, placeholder_text="例: 雑談配信、ゲーム実況、歌枠など")
        self.profile_genre_entry.insert(0, self.config_data.get("last_streamer_profile_genre", ""))
        self.profile_genre_entry.grid(row=7, column=0, padx=15, pady=(0, 6), sticky="ew")

        # 4. 登録者数
        ctk.CTkLabel(scroll, text="■ 現在のチャンネル登録者数・フォロワー数", font=ctk.CTkFont(weight="bold", size=12)).grid(row=8, column=0, padx=15, pady=(6, 2), sticky="w")
        self.profile_subscribers_entry = ctk.CTkEntry(scroll, placeholder_text="例: YouTube 1万人、Twitch 5000人など")
        self.profile_subscribers_entry.insert(0, self.config_data.get("last_streamer_profile_subscribers", ""))
        self.profile_subscribers_entry.grid(row=9, column=0, padx=15, pady=(0, 6), sticky="ew")

        # 5. 主な投稿プラットフォーム
        ctk.CTkLabel(scroll, text="■ 主な投稿プラットフォーム", font=ctk.CTkFont(weight="bold", size=12)).grid(row=10, column=0, padx=15, pady=(6, 2), sticky="w")
        self.profile_platforms_entry = ctk.CTkEntry(scroll, placeholder_text="例: YouTubeショート、TikTok、Instagramリールなど")
        self.profile_platforms_entry.insert(0, self.config_data.get("last_streamer_profile_platforms", ""))
        self.profile_platforms_entry.grid(row=11, column=0, padx=15, pady=(0, 6), sticky="ew")

        # 6. 運用実績
        ctk.CTkLabel(scroll, text="■ 過去のショート動画の運用実績", font=ctk.CTkFont(weight="bold", size=12)).grid(row=12, column=0, padx=15, pady=(6, 2), sticky="w")
        self.profile_shorts_entry = ctk.CTkEntry(scroll, placeholder_text="例: 平均3000再生、最高5万再生、あまりバズったことがないなど")
        self.profile_shorts_entry.insert(0, self.config_data.get("last_streamer_profile_shorts", ""))
        self.profile_shorts_entry.grid(row=13, column=0, padx=15, pady=(0, 15), sticky="ew")

        # 保存ボタン
        ctk.CTkButton(scroll, text="💾 パーソナルデータを保存する", font=ctk.CTkFont(size=13, weight="bold"), fg_color="chocolate", hover_color="sienna",
                      command=self.save_profile_data_only).grid(row=14, column=0, padx=15, pady=15, sticky="ew")

    def save_profile_data_only(self):
        self.config_data["last_streamer_name"] = getattr(self, "profile_name_entry", None) and self.profile_name_entry.get().strip() or ""
        self.config_data["last_streamer_profile_char"] = getattr(self, "profile_char_entry", None) and self.profile_char_entry.get().strip() or ""
        self.config_data["last_streamer_profile_target"] = getattr(self, "profile_target_entry", None) and self.profile_target_entry.get().strip() or ""
        self.config_data["last_streamer_profile_target_future"] = getattr(self, "profile_target_future_entry", None) and self.profile_target_future_entry.get().strip() or ""
        self.config_data["last_streamer_profile_tone"] = getattr(self, "profile_tone_entry", None) and self.profile_tone_entry.get().strip() or ""
        self.config_data["last_streamer_profile_phrases"] = getattr(self, "profile_phrases_entry", None) and self.profile_phrases_entry.get().strip() or ""
        self.config_data["last_streamer_profile_genre"] = getattr(self, "profile_genre_entry", None) and self.profile_genre_entry.get().strip() or ""
        self.config_data["last_streamer_profile_ng"] = getattr(self, "profile_ng_entry", None) and self.profile_ng_entry.get().strip() or ""
        self.config_data["last_streamer_profile_subscribers"] = getattr(self, "profile_subscribers_entry", None) and self.profile_subscribers_entry.get().strip() or ""
        self.config_data["last_streamer_profile_platforms"] = getattr(self, "profile_platforms_entry", None) and self.profile_platforms_entry.get().strip() or ""
        self.config_data["last_streamer_profile_shorts"] = getattr(self, "profile_shorts_entry", None) and self.profile_shorts_entry.get().strip() or ""
        self.config_data["last_video_title"] = getattr(self, "video_title_entry", None) and self.video_title_entry.get().strip() or ""
        self.config_data["last_video_summary"] = getattr(self, "video_summary_entry", None) and self.video_summary_entry.get().strip() or ""
        self.config_data["last_video_focus"] = getattr(self, "video_focus_entry", None) and self.video_focus_entry.get().strip() or ""
        self.config_manager.save_config(self.config_data)
        messagebox.showinfo("保存完了", "パーソナルデータ ＆ 動画情報を保存しました。")


    def setup_dict_tab(self):
        self.sub_frame_dict.grid_rowconfigure(0, weight=1)
        self.sub_frame_dict.grid_columnconfigure(0, weight=1)

        # 辞書・単語登録設定フレーム (1カラムで横いっぱいに広げる)
        dict_frame = ctk.CTkFrame(self.sub_frame_dict)
        dict_frame.grid(row=0, column=0, padx=10, pady=5, sticky="nsew")
        dict_frame.grid_columnconfigure(0, weight=1)
        dict_frame.grid_rowconfigure(2, weight=1) # ①のテキストボックスの引き伸ばし
        dict_frame.grid_rowconfigure(4, weight=1) # ②のテキストボックスの引き伸ばし

        ctk.CTkLabel(dict_frame, text="【AI文字起こし 辞書・単語登録】", font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0, padx=15, pady=(15, 5), sticky="w")

        # 横幅が十分に取れるため、1行で表示
        ctk.CTkLabel(dict_frame, text="① AIに事前に教える単語・固有名詞 (カンマ区切り):", font=ctk.CTkFont(weight="bold")).grid(row=1, column=0, padx=15, pady=(10, 2), sticky="w")
        self.reg_words_textbox = ctk.CTkTextbox(dict_frame, height=120, font=(self.ui_font_family, self.ui_font_size))
        self.reg_words_textbox.grid(row=2, column=0, padx=15, pady=5, sticky="nsew")
        self.reg_words_textbox.insert("1.0", self.config_data.get("registered_words", ""))

        # 同様に1行表示
        ctk.CTkLabel(dict_frame, text="② 自動で書き換える置換辞書 (間違える言葉 = 正しい言葉):", font=ctk.CTkFont(weight="bold")).grid(row=3, column=0, padx=15, pady=(10, 2), sticky="w")
        self.replace_dict_textbox = ctk.CTkTextbox(dict_frame, font=(self.ui_font_family, self.ui_font_size))
        self.replace_dict_textbox.grid(row=4, column=0, padx=15, pady=5, sticky="nsew")
        
        dict_str = ""
        for bad, good in self.config_data.get("replace_dict", {}).items():
            dict_str += f"{bad} = {good}\n"
        self.replace_dict_textbox.insert("1.0", dict_str.strip())

        # ③ タイミング自動調整
        ctk.CTkLabel(dict_frame, text="③ 字幕表示タイミングの自動調整 (文字起こし時のズレ補正):", font=ctk.CTkFont(weight="bold")).grid(row=5, column=0, padx=15, pady=(10, 2), sticky="w")
        
        timing_frame = ctk.CTkFrame(dict_frame, fg_color="transparent")
        timing_frame.grid(row=6, column=0, padx=15, pady=5, sticky="w")
        
        ctk.CTkLabel(timing_frame, text="開始位置の補正 (秒):").pack(side="left", padx=(0, 5))
        self.whisper_start_offset_entry = ctk.CTkEntry(timing_frame, width=60, font=("Consolas", 11))
        self.whisper_start_offset_entry.insert(0, str(self.config_data.get("whisper_start_offset", -0.20)))
        self.whisper_start_offset_entry.pack(side="left", padx=(0, 20))
        
        ctk.CTkLabel(timing_frame, text="終了位置の補正 (秒):").pack(side="left", padx=(0, 5))
        self.whisper_end_offset_entry = ctk.CTkEntry(timing_frame, width=60, font=("Consolas", 11))
        self.whisper_end_offset_entry.insert(0, str(self.config_data.get("whisper_end_offset", -0.20)))
        self.whisper_end_offset_entry.pack(side="left", padx=(0, 10))
        
        ctk.CTkLabel(timing_frame, text="※マイナス（例: -0.2）にすると、字幕の表示タイミングがその秒数だけ早まります。", font=ctk.CTkFont(size=11), text_color="gray60").pack(side="left", padx=10)

        ctk.CTkButton(dict_frame, text="💾 辞書・単語登録・タイミング設定を保存", font=ctk.CTkFont(size=13, weight="bold"), fg_color="chocolate", hover_color="sienna",
                      command=self.save_dictionary_settings).grid(row=7, column=0, padx=15, pady=15, sticky="ew")

    def save_dictionary_settings(self):
        words = self.reg_words_textbox.get("1.0", "end-1c").strip()
        dict_text = self.replace_dict_textbox.get("1.0", "end-1c").strip()
        
        rep_dict = {}
        for line in dict_text.split("\n"):
            line = line.strip()
            if not line:
                continue
            if "=" in line:
                parts = line.split("=", 1)
                bad = parts[0].strip()
                good = parts[1].strip()
                if bad:
                    rep_dict[bad] = good
            elif "：" in line:
                parts = line.split("：", 1)
                bad = parts[0].strip()
                good = parts[1].strip()
                if bad:
                    rep_dict[bad] = good

        try: start_offset = float(self.whisper_start_offset_entry.get().strip())
        except ValueError: start_offset = -0.2
        try: end_offset = float(self.whisper_end_offset_entry.get().strip())
        except ValueError: end_offset = -0.2
        
        self.config_data["registered_words"] = words
        self.config_data["replace_dict"] = rep_dict
        self.config_data["whisper_start_offset"] = start_offset
        self.config_data["whisper_end_offset"] = end_offset
        self.config_manager.save_config(self.config_data)
        messagebox.showinfo("保存完了", "辞書・単語・タイミング設定を保存しました。")

    def scan_environment(self):
        video_dir = "動画"
        os.makedirs(video_dir, exist_ok=True)
        os.makedirs("ショート", exist_ok=True) # 起動時に出力フォルダも自動作成
        mp4_files = glob.glob(os.path.join(video_dir, "*.mp4"))
        if mp4_files:
            self.input_video_path = os.path.abspath(mp4_files[0])
            self.video_entry.delete(0, "end")
            self.video_entry.insert(0, self.input_video_path)

    def select_video(self):
        fp = filedialog.askopenfilename(filetypes=[("MP4 files", "*.mp4"), ("All files", "*.*")])
        if fp:
            self.input_video_path = fp
            self.video_entry.delete(0, "end")
            self.video_entry.insert(0, fp)

    def on_shadow_alpha_changed(self, v):
        self.shadow_alpha_lbl.configure(text=f"影不透明度 ({float(v):.2f}):")
        self.on_text_style_changed()

    def on_margin_v_slider_changed(self, v):
        self.margin_v_lbl.configure(text=f"位置 Y ({int(float(v))} px):")
        self.on_text_style_changed()

    def get_safe_audio_path(self, path):
        if not path: return ""
        abs_path = os.path.abspath(path)
        if not os.path.exists(abs_path): return abs_path
        try:
            import ctypes
            from ctypes import wintypes
            GetShortPathNameW = ctypes.windll.kernel32.GetShortPathNameW
            GetShortPathNameW.argtypes = [wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.DWORD]
            GetShortPathNameW.restype = wintypes.DWORD
            buf = ctypes.create_unicode_buffer(1024)
            ret = GetShortPathNameW(abs_path, buf, 1024)
            if ret > 0 and ret <= 1024:
                return buf.value
        except Exception:
            pass
        return abs_path

    def get_preset_images(self):
        img_dir = "画像"
        os.makedirs(img_dir, exist_ok=True)
        valid_exts = (".png", ".jpg", ".jpeg", ".webp")
        try:
            files = [f for f in os.listdir(img_dir) if f.lower().endswith(valid_exts)]
            return sorted(files)
        except Exception:
            return []

    def refresh_presets(self):
        files = self.get_preset_images()
        self.preset_menu.configure(values=["(選択なし)"] + files)
        self.preset_menu.set("(選択なし)")

    def open_presets_folder(self):
        img_dir = "画像"
        os.makedirs(img_dir, exist_ok=True)
        try:
            os.startfile(img_dir)
        except Exception as e:
            messagebox.showerror("エラー", f"フォルダを開けませんでした: {e}")

    def on_preset_selected(self, filename):
        if filename == "(選択なし)":
            self.overlay_path_entry.delete(0, "end")
            self.on_text_style_changed()
        else:
            p = os.path.abspath(os.path.join("画像", filename))
            self.overlay_path_entry.delete(0, "end")
            self.overlay_path_entry.insert(0, p)
            self.overlay_enabled_var.set(True)
            self.on_text_style_changed()

    def select_overlay_image(self):
        fp = filedialog.askopenfilename(filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.webp"), ("All files", "*.*")])
        if fp:
            self.overlay_path_entry.delete(0, "end")
            self.overlay_path_entry.insert(0, fp)
            self.overlay_enabled_var.set(True)
            self.on_text_style_changed()

    def on_overlay_x_slider_changed(self, v):
        self.overlay_x_lbl.configure(text=f"位置 X ({int(float(v))} px):")
        self.on_text_style_changed()

    def on_overlay_y_slider_changed(self, v):
        self.overlay_y_lbl.configure(text=f"位置 Y ({int(float(v))} px):")
        self.on_text_style_changed()

    def on_overlay_scale_slider_changed(self, v):
        self.overlay_scale_lbl.configure(text=f"倍率 ({int(float(v)*100)}%):")
        self.on_text_style_changed()

    def on_overlay_angle_slider_changed(self, v):
        self.overlay_angle_lbl.configure(text=f"角度 ({int(float(v))}°):")
        self.on_text_style_changed()

    def on_overlay_opacity_slider_changed(self, v):
        self.overlay_opacity_lbl.configure(text=f"不透明度 ({float(v):.2f}):")
        self.on_text_style_changed()

    def update_buffer_label(self, value):
        if hasattr(self, 'buffer_lbl'):
            self.buffer_lbl.configure(text=f"前後追加バッファ時間 ({int(float(value))}秒):")
        self.config_data["buffer_seconds"] = int(float(value))
        self.config_manager.save_config(self.config_data)

    def parse_instructions_text(self, content):
        results = []
        if not content: return results
        
        blocks = re.split(r"\n\s*(?=(?:\d+[\.\)]|■|◆|●|★|【|###|---|\b候補|\b切り抜き|\bClip))", content)
        valid_blocks = [b.strip() for b in blocks if b.strip()]
        
        time_pair_pattern = r"(\d{1,2}:\d{2}(?::\d{2})?)\s*(?:～|~|-|→|to|\b)\s*(\d{1,2}:\d{2}(?::\d{2})?)"
        single_time_pattern = r"(\d{1,2}:\d{2}(?::\d{2})?)"
        
        def process_block(block_text):
            lines = [l.strip() for l in block_text.split("\n") if l.strip()]
            if not lines: return None
            
            start_time = None
            end_time = None
            title = "no_title"
            intro_telop = ""
            
            m_pair = re.search(time_pair_pattern, block_text)
            if m_pair:
                start_time = time_to_seconds(m_pair.group(1))
                end_time = time_to_seconds(m_pair.group(2))
            else:
                found_times = re.findall(single_time_pattern, block_text)
                if len(found_times) >= 2:
                    start_time = time_to_seconds(found_times[0])
                    end_time = time_to_seconds(found_times[1])
                    
            if start_time is None or end_time is None or start_time >= end_time:
                return None
                
            for line in lines:
                if any(k in line for k in ["タイトル", "バズるタイトル", "件名", "見出し"]):
                    m = re.search(r"(?:タイトル|バズるタイトル|件名|見出し)[:：]\s*(.+)", line)
                    if m:
                        raw_title = m.group(1).strip()
                        raw_title = re.sub(r"\*\*|\[|\]|「|」|\"|'", "", raw_title)
                        title = clean_filename(raw_title)
                        
                if any(k in line for k in ["冒頭テロップ", "テロップ", "要約", "概要"]):
                    m = re.search(r"(?:冒頭テロップ|テロップ|要約|概要)[:：]\s*(.+)", line)
                    if m:
                        raw_telop = m.group(1).strip()
                        raw_telop = re.sub(r"\*\*|\[|\]|「|」|\"|'", "", raw_telop)
                        intro_telop = raw_telop

            if title == "no_title":
                for line in lines:
                    if line and not line.startswith("■") and not re.search(single_time_pattern, line):
                        clean_l = re.sub(r"\*\*|\[|\]|「|」|\"|'|#|:|-|^\d+[\.\)]", "", line).strip()
                        if clean_l:
                            title = clean_filename(clean_l[:25])
                            break
            if title == "no_title":
                title = f"切り抜き_{len(results)+1}"
                
            subtitles = []
            if intro_telop:
                subtitles.append({"start": 0.0, "end": 3.0, "text": intro_telop})

            return {
                "start": start_time,
                "end": end_time,
                "title": title,
                "subtitles": subtitles,
                "fontsize": "36",
                "color": "#FFFF00",
                "intro_telop": intro_telop,
                "margin_v": 500,
                "bold": False,
                "italic": False,
                "outline_width": "2",
                "shadow_depth": "0",
                "outline_color": "#000000",
                "alignment": "中央寄せ",
                "shadow_alpha": 1.0
            }
        
        for b in valid_blocks:
            res = process_block(b)
            if res:
                results.append(res)
                
        if not results:
            lines = content.split("\n")
            for i, line in enumerate(lines):
                m_pair = re.search(time_pair_pattern, line)
                if m_pair:
                    s_sec = time_to_seconds(m_pair.group(1))
                    e_sec = time_to_seconds(m_pair.group(2))
                    if s_sec < e_sec:
                        t_str = f"切り抜き_{len(results)+1}"
                        if i > 0 and lines[i-1].strip() and not re.search(single_time_pattern, lines[i-1]):
                            t_str = clean_filename(lines[i-1].strip()[:25])
                        elif i < len(lines)-1 and lines[i+1].strip() and not re.search(single_time_pattern, lines[i+1]):
                            t_str = clean_filename(lines[i+1].strip()[:25])
                        results.append({
                            "start": s_sec,
                            "end": e_sec,
                            "title": t_str,
                            "subtitles": [],
                            "fontsize": "36",
                            "color": "#FFFF00",
                            "intro_telop": "",
                            "margin_v": 500,
                            "bold": False,
                            "italic": False,
                            "outline_width": "2",
                            "shadow_depth": "0",
                            "outline_color": "#000000",
                            "alignment": "中央寄せ",
                            "shadow_alpha": 1.0
                        })
        return results
    def apply_paste_instructions(self):
        try:
            text = self.paste_textbox.get("1.0", "end-1c").strip()
            if not text:
                messagebox.showwarning("警告", "コピペエリアが空です。")
                return
            
            video_path = self.video_entry.get().strip()
            if not video_path or not os.path.exists(video_path):
                messagebox.showerror("エラー", "対象動画ファイルを選択した状態で読み込んでください。")
                return
            
            try:
                import winsound
                winsound.PlaySound(None, winsound.SND_PURGE)
            except Exception: pass
            
            parsed_jobs = self.parse_instructions_text(text)
            self.active_job_index = -1
            
            if not parsed_jobs:
                self.list_title.configure(text="【2. 切り抜き候補一覧】 (検出なし)")
                messagebox.showwarning(
                    "警告", 
                    "候補を抽出できませんでした。\n\n"
                    "コピペデータの中に「01:23:45 〜 01:24:15」のように、"
                    "開始時間と終了時間のペアが含まれているか確認してください。"
                )
                return
                
            for job in parsed_jobs:
                job["subtitles"] = []
                job["fontsize"] = "36"
                job["color"] = "白 (White)"
                job["fontname"] = "MS Gothic"
                job["margin_v"] = 500
                job["loud_zoom"] = False
                
            self.jobs = parsed_jobs
            if hasattr(self, "job_vars"):
                del self.job_vars
            self.render_job_list()
            messagebox.showinfo("完了", f"全 {len(self.jobs)} 件の候補を読み込みました！\n字幕を生成したい候補にチェックを入れ、下の「字幕を生成」ボタンを押してください。")
            
        except Exception as e:
            err_msg = f"解析中に予期せぬエラーが発生しました:\n\n{str(e)}\n\n{traceback.format_exc()}"
            print(err_msg)
            messagebox.showerror("内部エラー", err_msg)

    def render_job_list(self):
        for cb in getattr(self, "checkboxes", []):
            try: cb.destroy()
            except Exception: pass
        self.checkboxes.clear()
        
        self.check_widgets = getattr(self, "check_widgets", [])
        for cw in self.check_widgets:
            try: cw.destroy()
            except Exception: pass
        self.check_widgets.clear()
        
        self.job_row_frames = getattr(self, "job_row_frames", [])
        for jf in self.job_row_frames:
            try: jf.destroy()
            except Exception: pass
        self.job_row_frames.clear()

        if not hasattr(self, "job_vars") or len(self.job_vars) != len(self.jobs):
            self.job_vars = [ctk.BooleanVar(value=True) for _ in self.jobs]

        self.list_title.configure(text=f"【2. 切り抜き候補一覧 ({len(self.jobs)}件)】")
        
        for i, job in enumerate(self.jobs):
            jf = ctk.CTkFrame(self.scrollable_frame, fg_color="transparent")
            jf.grid(row=i, column=0, padx=5, pady=3, sticky="ew")
            self.scrollable_frame.grid_columnconfigure(0, weight=1)
            jf.grid_columnconfigure(1, weight=1)
            
            cb = ctk.CTkCheckBox(jf, text="", variable=self.job_vars[i], width=20, height=20)
            cb.pack(side="left", padx=(5, 2))
            self.check_widgets.append(cb)
            
            btn = ctk.CTkButton(
                jf,
                text=f"No.{i + 1} [{seconds_to_hms(job['start'])}～] {job['title']}",
                anchor="w", 
                fg_color="transparent", 
                text_color="white", 
                hover_color="#2b2b2b",
                font=(self.ui_font_family, self.ui_font_size),
                command=lambda idx=i: self.load_job_to_editor(idx)
            )
            btn.pack(side="left", padx=2, fill="x", expand=True)
            self.checkboxes.append(btn)
            self.job_row_frames.append(jf)

    def start_bulk_whisper_for_selected(self):
        if not self.jobs:
            messagebox.showwarning("警告", "候補が読み込まれていません。")
            return
            
        video_path = self.video_entry.get().strip()
        if not video_path or not os.path.exists(video_path):
            messagebox.showerror("エラー", "対象動画ファイルを選択してください。")
            return

        selected_indices = [i for i, val in enumerate(self.job_vars) if val.get()]
        if not selected_indices:
            messagebox.showwarning("警告", "字幕を生成する候補にチェックを入れてください。")
            return

        dialog = WhisperProgressDialog(self, len(selected_indices))
        self.bulk_whisper_info = {
            "current": 0,
            "total": len(selected_indices) + 1,
            "status": "準備中...",
            "done": False,
            "error": None,
            "cancel": False,
            "selected_indices": selected_indices,
            "jobs_copy": list(self.jobs)
        }

        self.after(100, lambda: self.check_bulk_whisper_progress(dialog))
        
        threading.Thread(
            target=self.run_bulk_whisper_selected_thread,
            args=(selected_indices, video_path),
            daemon=True
        ).start()

    def run_bulk_whisper_selected_thread(self, selected_indices, video_path):
        try:
            audio_mod.init_whisper()
            audio_mod.patch_whisper_assets()
            video_mod.init_video_libs()
            
            if not audio_mod.WHISPER_AVAILABLE:
                self.bulk_whisper_info["error"] = f"openai-whisper が利用できません。\n\n【詳細なエラー理由】:\n{audio_mod.WHISPER_LOAD_ERROR}"
                return
            
            self.bulk_whisper_info["status"] = "AIモデル(Whisper)をロード中..."
            self.bulk_whisper_info["current"] = 1
            
            model = audio_mod.whisper.load_model("small")
            total = len(selected_indices)
            
            reg_words = self.config_data.get("registered_words", "初狐羽鹿, Vtuber, 逆転裁判, 切り抜き")
            rep_dict = self.config_data.get("replace_dict", {})
            
            for seq_idx, idx in enumerate(selected_indices):
                if self.bulk_whisper_info.get("cancel", False):
                    break
                
                job = self.bulk_whisper_info["jobs_copy"][idx]
                temp_audio = os.path.join("temp", f"temp_segment_audio_{idx}.wav")
                
                self.bulk_whisper_info["current"] = seq_idx + 2
                self.bulk_whisper_info["status"] = f"選択 {seq_idx + 1} / {total} 件目の音声解析中...\n「{job['title']}」"
                
                start_time = job["start"]
                end_time = job["end"]
                
                with video_mod.VideoFileClip(self.get_safe_audio_path(video_path)) as v:
                    duration = v.duration
                    if start_time >= duration:
                        print(f"⚠️ スキップ: 開始時間 {seconds_to_hms(start_time)} が動画の長さ {seconds_to_hms(duration)} を超えています。")
                        job["subtitles"] = []
                        continue
                    
                    safe_end_time = min(duration, end_time)
                    a = v.subclip(max(0.0, start_time), safe_end_time).audio
                    if a is not None:
                        a.write_audiofile(temp_audio, codec="pcm_s16le", fps=16000, logger=None)
                        a.close()
                
                try: s_off = float(self.config_data.get("whisper_start_offset", -0.2))
                except ValueError: s_off = -0.2
                try: e_off = float(self.config_data.get("whisper_end_offset", -0.2))
                except ValueError: e_off = -0.2
                subtitles = audio_mod.transcribe_audio_segment(
                    model, temp_audio, initial_prompt=reg_words, replace_dict=rep_dict,
                    start_offset=s_off, end_offset=e_off
                )
                
                if job.get("intro_telop"):
                    first_start = subtitles[0]["start"] if subtitles else 3.0
                    telop_end = min(3.0, max(1.5, first_start))
                    subtitles.insert(0, {
                        "start": 0.0,
                        "end": telop_end,
                        "text": job["intro_telop"]
                    })
                
                job["subtitles"] = subtitles
                
                for _ in range(10):
                    try:
                        if os.path.exists(temp_audio):
                            os.remove(temp_audio)
                        break
                    except Exception:
                        time.sleep(0.1)
            
            if not self.bulk_whisper_info.get("cancel", False):
                self.bulk_whisper_info["done"] = True
                
        except Exception as e:
            self.bulk_whisper_info["error"] = f"{str(e)}\n{traceback.format_exc()}"

    def run_bulk_whisper_thread(self, jobs, video_path):
        try:
            audio_mod.init_whisper()
            audio_mod.patch_whisper_assets()
            video_mod.init_video_libs()
            
            if not audio_mod.WHISPER_AVAILABLE:
                self.bulk_whisper_info["error"] = f"openai-whisper が利用できません。\n\n【詳細なエラー理由】:\n{audio_mod.WHISPER_LOAD_ERROR}"
                return
            
            self.bulk_whisper_info["status"] = "AIモデル(Whisper)をロード中..."
            self.bulk_whisper_info["current"] = 1
            
            model = audio_mod.whisper.load_model("small")
            total = len(jobs)
            
            reg_words = self.config_data.get("registered_words", "初狐羽鹿, Vtuber, 逆転裁判, 切り抜き")
            rep_dict = self.config_data.get("replace_dict", {})
            
            for idx, job in enumerate(jobs):
                if self.bulk_whisper_info.get("cancel", False):
                    break
                
                temp_audio = os.path.join("temp", f"temp_segment_audio_{idx}.wav")
                
                self.bulk_whisper_info["current"] = idx + 2
                self.bulk_whisper_info["status"] = f"候補 {idx + 1} / {total} 件目の音声解析中...\n「{job['title']}」"
                
                start_time = job["start"]
                end_time = job["end"]
                
                with video_mod.VideoFileClip(self.get_safe_audio_path(video_path)) as v:
                    duration = v.duration
                    if start_time >= duration:
                        print(f"⚠️ スキップ: 開始時間 {seconds_to_hms(start_time)} が動画の長さ {seconds_to_hms(duration)} を超えています。")
                        job["subtitles"] = []
                        continue
                    
                    safe_end_time = min(duration, end_time)
                    a = v.subclip(max(0.0, start_time), safe_end_time).audio
                    if a is not None:
                        a.write_audiofile(temp_audio, codec="pcm_s16le", fps=16000, logger=None)
                        a.close()
                
                try: s_off = float(self.config_data.get("whisper_start_offset", -0.2))
                except ValueError: s_off = -0.2
                try: e_off = float(self.config_data.get("whisper_end_offset", -0.2))
                except ValueError: e_off = -0.2
                subtitles = audio_mod.transcribe_audio_segment(
                    model, temp_audio, initial_prompt=reg_words, replace_dict=rep_dict,
                    start_offset=s_off, end_offset=e_off
                )
                
                if job.get("intro_telop"):
                    first_start = subtitles[0]["start"] if subtitles else 3.0
                    telop_end = min(3.0, max(1.5, first_start))
                    subtitles.insert(0, {
                        "start": 0.0,
                        "end": telop_end,
                        "text": job["intro_telop"]
                    })
                
                job["subtitles"] = subtitles
                
                for _ in range(10):
                    try:
                        if os.path.exists(temp_audio):
                            os.remove(temp_audio)
                        break
                    except Exception:
                        time.sleep(0.1)
            
            if not self.bulk_whisper_info.get("cancel", False):
                self.bulk_whisper_info["jobs"] = jobs
                self.bulk_whisper_info["done"] = True
                
        except Exception as e:
            self.bulk_whisper_info["error"] = f"{str(e)}\n{traceback.format_exc()}"

    def check_bulk_whisper_progress(self, dialog):
        info = self.bulk_whisper_info
        if not info: return
        
        if info.get("done", False):
            dialog.destroy()
            prev_idx = self.active_job_index
            self.jobs = info["jobs_copy"]
            self.render_job_list()
            
            target_idx = prev_idx
            if target_idx < 0 or target_idx >= len(self.jobs):
                if info.get("selected_indices"):
                    target_idx = info["selected_indices"][0]
            
            if target_idx >= 0 and target_idx < len(self.jobs):
                self.load_job_to_editor(target_idx)
                self.switch_wizard_step("step2")
            else:
                self.active_job_index = -1
                self.render_subtitle_editor_from_active_job()
                self.refresh_job_select_menu()
                self.show_current_frame()
                
            messagebox.showinfo("完了", "選択された候補の字幕生成が完了しました！\n「② 字幕・編集」ステップへ自動遷移します。")
            self.bulk_whisper_info = {}
            return
            
        if info.get("error"):
            dialog.destroy()
            messagebox.showerror("一括解析エラー", f"音声認識中にエラーが発生しました:\n\n{info['error']}")
            self.bulk_whisper_info = {}
            return
            
        if dialog.cancel_requested:
            info["cancel"] = True
            dialog.destroy()
            self.bulk_whisper_info = {}
            return
            
        current = info.get("current", 0)
        total = info.get("total", 1)
        status = info.get("status", "")
        
        dialog.status_label.configure(text=status)
        dialog.progress.set(current / total)
        
        self.after(100, lambda: self.check_bulk_whisper_progress(dialog))

    def clean_temp_link(self):
        if self.preview_cap:
            self.preview_cap.release(); self.preview_cap = None
        if os.path.exists(self.temp_preview_link):
            try: os.remove(self.temp_preview_link)
            except Exception: pass

    def prepare_preview_audio(self, video_path, start_time, end_time):
        self.audio_ready = False
        def update_ui_status(text, color):
            if hasattr(self, "audio_status_lbl"):
                self.after(0, lambda: self.audio_status_lbl.configure(text=text, text_color=color))

        update_ui_status("🔊 音声抽出中...", "orange")
        
        try:
            import winsound
            winsound.PlaySound(None, winsound.SND_PURGE)
        except Exception: pass
        
        time.sleep(0.05)
        import tempfile
        import subprocess
        temp_dir = tempfile.gettempdir()
        self.temp_play_audio = os.path.join(temp_dir, f"kirinuki_play_audio_{self.active_job_index}.wav")
        
        try:
            if os.path.exists(self.temp_play_audio):
                try: os.remove(self.temp_play_audio)
                except Exception: pass
            
            # Check duration via OpenCV VideoCapture
            abs_video_path = os.path.abspath(video_path)
            cap = cv2.VideoCapture(abs_video_path)
            fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
            total_f = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0
            cap.release()
            tot_sec = total_f / fps if fps > 0 else 0
            
            if tot_sec > 0 and start_time >= tot_sec:
                start_time = max(0.0, tot_sec - 30.0)
            
            duration = max(0.1, end_time - start_time)
            
            import imageio_ffmpeg
            ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
            
            cmd = [
                ffmpeg_exe,
                "-y",
                "-ss", f"{max(0.0, start_time):.3f}",
                "-t", f"{duration:.3f}",
                "-i", abs_video_path,
                "-map", "0:a:0?",
                "-vn",
                "-acodec", "pcm_s16le",
                "-ar", "44100",
                "-ac", "2",
                self.temp_play_audio
            ]
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            p.communicate()
            
            if os.path.exists(self.temp_play_audio) and os.path.getsize(self.temp_play_audio) > 1000:
                self.audio_ready = True
                update_ui_status("🔊 音声準備完了", "green")
                return
        except Exception as e:
            print(f"FFmpeg direct extraction fallback: {e}")
            
        try:
            video_mod.init_video_libs()
            safe_vp = self.get_safe_audio_path(video_path)
            with video_mod.VideoFileClip(safe_vp) as v:
                v_dur = v.duration
                if start_time >= v_dur or v.audio is None:
                    update_ui_status("🔇 音声なし", "red")
                    return
                safe_end = min(v_dur, end_time)
                a = v.subclip(max(0.0, start_time), safe_end).audio
                if a is not None:
                    a.write_audiofile(self.temp_play_audio, codec="pcm_s16le", fps=44100, logger=None)
                    a.close()
                    self.audio_ready = True
                    update_ui_status("🔊 音声準備完了", "green")
                else:
                    update_ui_status("🔇 音声なし", "red")
        except Exception as err:
            print(f"❌ プレビュー音声作成失敗: {err}")
            update_ui_status("🔇 音声エラー", "red")

    def refresh_job_select_menu(self):
        if not hasattr(self, "job_select_menu"): return
        if not self.jobs:
            self.job_select_menu.configure(values=["(候補がありません)"])
            self.job_select_menu.set("(候補がありません)")
            return
        vals = [f"No.{i+1} [{seconds_to_hms(j['start'])}〜] {j['title']}" for i, j in enumerate(self.jobs)]
        self.job_select_menu.configure(values=vals)
        if 0 <= self.active_job_index < len(vals):
            self.job_select_menu.set(vals[self.active_job_index])

    def on_job_select_menu_changed(self, choice):
        if not self.jobs or choice == "(候補がありません)": return
        for i, j in enumerate(self.jobs):
            val_str = f"No.{i+1} [{seconds_to_hms(j['start'])}〜] {j['title']}"
            if choice == val_str:
                self.save_current_editor_to_active_job()
                self.load_job_to_editor(i)
                break

    def load_job_to_editor(self, idx):
        if idx < 0 or idx >= len(self.jobs): return
        self.active_job_index = idx
        job = self.jobs[idx]
        
        for i, btn in enumerate(self.checkboxes):
            btn.configure(fg_color=self.theme_primary_color if i == idx else "transparent",
                          hover_color=self.theme_primary_hover if i == idx else "#2b2b2b")
        self.refresh_list_highlights()

    def toggle_grayscale(self):
        is_gray = self.grayscale_var.get()
        if is_gray:
            self.theme_primary_color = "#555555"
            self.theme_primary_hover = "#777777"
        else:
            self.theme_primary_color = "#1a73e8"
            self.theme_primary_hover = "#155cb4"
            
        def update_widget(widget):
            w_class = widget.__class__.__name__
            if w_class == "CTkButton":
                curr_fg = widget.cget("fg_color")
                if curr_fg not in ["firebrick", "darkred", "transparent", "gray25", "gray40"]:
                    widget.configure(fg_color=self.theme_primary_color, hover_color=self.theme_primary_hover)
            elif w_class == "CTkSwitch":
                widget.configure(progress_color=self.theme_primary_color)
            elif w_class == "CTkSlider":
                widget.configure(button_color=self.theme_primary_color, button_hover_color=self.theme_primary_hover, progress_color=self.theme_primary_color)
            elif w_class == "CTkProgressBar":
                widget.configure(progress_color=self.theme_primary_color)
                
            for child in widget.winfo_children():
                update_widget(child)
                
        update_widget(self)
        self.refresh_list_highlights()

    def refresh_list_highlights(self):
        idx = self.active_job_index
        if idx < 0 or idx >= len(self.jobs): return
        job = self.jobs[idx]
        for i, btn in enumerate(self.checkboxes):
            btn.configure(fg_color=self.theme_primary_color if i == idx else "transparent",
                          hover_color=self.theme_primary_hover if i == idx else "#2b2b2b")
        
        video_path = self.video_entry.get().strip()
        if not video_path or not os.path.exists(video_path):
            messagebox.showerror("エラー", "対象動画ファイルが見つかりません。"); return
        
        self.clean_temp_link()
        abs_path = os.path.abspath(video_path)
        self.preview_cap = cv2.VideoCapture(abs_path)
            
        if not self.preview_cap or not self.preview_cap.isOpened():
            messagebox.showerror("プレビューエラー", "動画プレビューの読み込みに失敗しました。"); return
            
        self.preview_fps = self.preview_cap.get(cv2.CAP_PROP_FPS) or 30
        self.preview_total_frames = int(self.preview_cap.get(cv2.CAP_PROP_FRAME_COUNT))
        tot = self.preview_total_frames / self.preview_fps
        
        if job["start"] >= tot:
            messagebox.showwarning("時間不一致", f"開始時間が動画長({seconds_to_hms(tot)})を超えています。")
            job["start"] = max(0.0, tot - 30.0); job["end"] = tot
            
        self.job_start_frame = min(int(job["start"] * self.preview_fps), self.preview_total_frames - 1)
        self.job_end_frame = min(int(job["end"] * self.preview_fps), self.preview_total_frames)
        self.preview_start_frame = self.job_start_frame
        self.preview_end_frame = self.job_end_frame
        self.preview_current_frame = self.preview_start_frame
        self.preview_playing = False
        
        self.seek_slider.configure(from_=self.preview_start_frame, to=self.preview_end_frame,
                                   number_of_steps=(self.preview_end_frame - self.preview_start_frame + 1))
        self.seek_slider.set(self.preview_current_frame)
        
        self.start_entry.delete(0, "end"); self.start_entry.insert(0, seconds_to_hms(job['start']))
        self.end_entry.delete(0, "end"); self.end_entry.insert(0, seconds_to_hms(job['end']))
        
        self.fontsize_menu.set(job.get("fontsize", "36"))
        
        self.color_entry.delete(0, "end")
        self.color_entry.insert(0, job.get("color", "#FFFF00"))
        
        self.font_menu.set(job.get("fontname", "MS Gothic"))
        
        self.margin_v_slider.set(float(job.get("margin_v", 500)))
        self.margin_v_lbl.configure(text=f"位置 Y ({int(float(self.margin_v_slider.get()))} px):")
        
        self.loud_zoom_var.set(job.get("loud_zoom", False))
        self.bold_var.set(job.get("bold", False))
        self.italic_var.set(job.get("italic", False))
        self.outline_width_menu.set(job.get("outline_width", "2"))
        self.shadow_depth_menu.set(job.get("shadow_depth", "0"))
        
        self.outline_color_entry.delete(0, "end")
        self.outline_color_entry.insert(0, job.get("outline_color", "#000000"))
        
        self.alignment_btn.set(job.get("alignment", "中央寄せ"))
        
        sa = job.get("shadow_alpha", 1.0)
        self.shadow_alpha_slider.set(sa)
        self.shadow_alpha_label.configure(text=f"影不透明度 ({sa:.2f}):")
        
        # Image overlay fields
        self.overlay_enabled_var.set(job.get("overlay_enabled", False))
        
        op = job.get("overlay_path", "")
        self.overlay_path_entry.delete(0, "end")
        self.overlay_path_entry.insert(0, op)
        if op:
            fn = os.path.basename(op)
            if op == os.path.abspath(os.path.join("画像", fn)):
                self.preset_menu.set(fn)
            else:
                self.preset_menu.set("(選択なし)")
        else:
            self.preset_menu.set("(選択なし)")
            
        ox = job.get("overlay_x", 100)
        self.overlay_x_slider.set(float(ox))
        self.overlay_x_lbl.configure(text=f"位置 X ({ox} px):")
        
        oy = job.get("overlay_y", 100)
        self.overlay_y_slider.set(float(oy))
        self.overlay_y_lbl.configure(text=f"位置 Y ({oy} px):")
        
        self.overlay_anchor_menu.set(job.get("overlay_anchor", "重心 (中央)"))
        
        oscl = job.get("overlay_scale", 1.0)
        self.overlay_scale_slider.set(oscl)
        self.overlay_scale_lbl.configure(text=f"倍率 ({int(oscl*100)}%):")
        
        oang = job.get("overlay_angle", 0.0)
        self.overlay_angle_slider.set(oang)
        self.overlay_angle_lbl.configure(text=f"角度 ({int(oang)}°):")
        
        oopac = job.get("overlay_opacity", 1.0)
        self.overlay_opacity_slider.set(oopac)
        self.overlay_opacity_lbl.configure(text=f"不透明度 ({oopac:.2f}):")
        
        threading.Thread(target=self.prepare_preview_audio, args=(abs_path, job["start"], job["end"]), daemon=True).start()
        
        self.update_playback_time_label()
        self.show_current_frame()
        self.render_subtitle_editor_from_active_job()
        self.refresh_job_select_menu()
        self.on_text_style_changed()

    def update_active_job_range(self):
        if self.active_job_index == -1: return
        self.save_current_editor_to_active_job()
        try:
            s = time_to_seconds(self.start_entry.get())
            e = time_to_seconds(self.end_entry.get())
        except Exception:
            messagebox.showerror("エラー", "時間の形式が不正です。"); return
        tot = self.preview_total_frames / self.preview_fps
        if s < 0 or e > tot or s >= e:
            messagebox.showerror("エラー", f"指定範囲が不正です（0 ～ {seconds_to_hms(tot)}）。"); return
        
        job = self.jobs[self.active_job_index]
        job["start"] = s; job["end"] = e
        
        self.job_start_frame = min(int(s * self.preview_fps), self.preview_total_frames - 1)
        self.job_end_frame = min(int(e * self.preview_fps), self.preview_total_frames)
        self.preview_start_frame = self.job_start_frame
        self.preview_end_frame = self.job_end_frame
        self.preview_current_frame = self.preview_start_frame
        
        cmap = {"黄 (Yellow)": "&H00FFFF", "白 (White)": "&HFFFFFF", "赤 (Red)": "&H0000FF", "緑 (Green)": "&H00FF00"}
        for item in self.processing_queue:
            if item.get("job_index") == self.active_job_index:
                item["start"] = s
                item["end"] = e
                item["fontsize"] = job["fontsize"]
                item["fontname"] = job.get("fontname", "MS Gothic")
                item["color_hex"] = cmap.get(job["color"], "&HFFFFFF")
        self.render_queue_list()
        
        video_path = self.video_entry.get().strip()
        if video_path and os.path.exists(video_path):
            threading.Thread(target=self.prepare_preview_audio, args=(os.path.abspath(video_path), s, e), daemon=True).start()
            
        self.show_current_frame(); self.update_playback_time_label()
        self.render_subtitle_editor_from_active_job()
        self.refresh_job_select_menu()
        self.checkboxes[self.active_job_index].configure(
            text=f"No.{self.active_job_index + 1} [{seconds_to_hms(s)}～] {job['title']}")

    def play_in_external_player(self):
        vp = self.video_entry.get().strip()
        if not vp or not os.path.exists(vp): messagebox.showerror("エラー", "動画が見つかりません。"); return
        try: os.startfile(vp)
        except Exception as e: messagebox.showerror("エラー", str(e))

    def toggle_play(self):
        if not self.preview_cap: return
        
        if self.preview_playing:
            self.preview_playing = False
            self.play_btn.configure(text="▶")
            try:
                import winsound
                winsound.PlaySound(None, winsound.SND_PURGE)
            except Exception: pass
        else:
            self.preview_start_frame = self.job_start_frame
            self.preview_end_frame = self.job_end_frame
            if self.preview_current_frame >= self.preview_end_frame or self.preview_current_frame < self.preview_start_frame:
                self.preview_current_frame = self.preview_start_frame
                
            self.preview_cap.set(cv2.CAP_PROP_POS_FRAMES, self.preview_current_frame)
            self.preview_playing = True
            self.play_btn.configure(text="⏸")
            
            if getattr(self, "audio_ready", False) and hasattr(self, "temp_play_audio") and os.path.exists(self.temp_play_audio):
                try:
                    import winsound
                    winsound.PlaySound(None, winsound.SND_PURGE)
                    winsound.PlaySound(self.temp_play_audio, winsound.SND_ASYNC | winsound.SND_FILENAME)
                except Exception as e:
                    print(f"音声再生失敗: {e}")
                    
            self.playback_loop()

    def playback_loop(self):
        if self.preview_playing and self.preview_cap:
            ret, frame = self.preview_cap.read()
            self.preview_current_frame += 1
            
            if not ret or self.preview_current_frame > self.preview_end_frame:
                self.preview_playing = False
                self.play_btn.configure(text="▶")
                try:
                    import winsound
                    winsound.PlaySound(None, winsound.SND_PURGE)
                except Exception: pass
                
                self.preview_current_frame = self.preview_start_frame
                self.preview_cap.set(cv2.CAP_PROP_POS_FRAMES, self.preview_start_frame)
                self.seek_slider.set(self.preview_start_frame)
                self.update_playback_time_label()
                self.show_current_frame()
            else:
                self.display_frame(frame)
                self.seek_slider.set(self.preview_current_frame)
                self.update_playback_time_label()
                
                delay = max(1, int(1000 / self.preview_fps))
                self.after(delay, self.playback_loop)

    def on_seek_drag(self, value):
        self.preview_current_frame = int(value)
        if self.preview_cap:
            try:
                import winsound
                winsound.PlaySound(None, winsound.SND_PURGE)
            except Exception: pass
            if self.preview_playing:
                self.preview_playing = False
                self.play_btn.configure(text="▶")
                
            self.preview_cap.set(cv2.CAP_PROP_POS_FRAMES, self.preview_current_frame)
            self.update_playback_time_label(); self.show_current_frame()

    def show_current_frame(self):
        if self.preview_cap:
            self.preview_cap.set(cv2.CAP_PROP_POS_FRAMES, self.preview_current_frame)
            ret, frame = self.preview_cap.read()
            if ret:
                self.display_frame(frame)
                self.preview_cap.set(cv2.CAP_PROP_POS_FRAMES, self.preview_current_frame)

    def display_frame(self, frame):
        h, w = frame.shape[:2]
        scale = self.current_preview_w / w
        nw, nh = self.current_preview_w, int(h * scale)
        if nh > self.current_preview_h:
            scale = self.current_preview_h / h
            nw, nh = int(w * scale), self.current_preview_h
        nw, nh = max(1, nw), max(1, nh)
        resized = cv2.resize(frame, (nw, nh))
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        canvas = PIL.Image.new("RGB", (self.current_preview_w, self.current_preview_h), (0, 0, 0))
        canvas.paste(PIL.Image.fromarray(rgb), ((self.current_preview_w - nw) // 2, (self.current_preview_h - nh) // 2))

        if self.active_job_index != -1:
            job = self.jobs[self.active_job_index]
            cs = self.preview_current_frame / self.preview_fps
            rel_time = cs - job["start"]
            
            active_text = ""
            for sub in job.get("subtitles", []):
                if sub["start"] <= rel_time <= sub["end"]:
                    active_text = sub["text"]
                    break
            
            if active_text:
                from PIL import ImageDraw, ImageFont
                
                fs_original = float(job.get("fontsize", "36"))
                fs_preview = max(10, int(fs_original * (self.current_preview_w / 1080.0) * 1.5))
                
                fontname = job.get("fontname", "MS Gothic")
                font_file = FONT_MAP.get(fontname, fontname)
                font_path = get_windows_font_path(font_file)
                try:
                    font = ImageFont.truetype(font_path, fs_preview)
                except Exception as e:
                    print(f"⚠️ フォントロード失敗 ({fontname} -> {font_path}): {e}")
                    try:
                        font = ImageFont.truetype(get_windows_font_path("msgothic.ttc"), fs_preview)
                    except Exception:
                        font = ImageFont.load_default()
                
                fill_color = parse_color_to_rgb(job.get("color", "#FFFF00"))
                outline_color = parse_color_to_rgb(job.get("outline_color", "#000000"))
                
                # Create a transparent overlay for text drawing (so we can support shadow alpha)
                overlay = PIL.Image.new("RGBA", canvas.size, (0, 0, 0, 0))
                overlay_draw = ImageDraw.Draw(overlay)
                
                if hasattr(overlay_draw, "textbbox"):
                    bbox = overlay_draw.textbbox((0, 0), active_text, font=font)
                    text_w = bbox[2] - bbox[0]
                    text_h = bbox[3] - bbox[1]
                else:
                    text_w, text_h = overlay_draw.textsize(active_text, font=font)
                
                margin_v = int(job.get("margin_v", 50))
                margin_v_preview = max(5, int(margin_v * (self.current_preview_h / 1920.0)))
                
                align_type = job.get("alignment", "中央寄せ")
                if "左寄せ" in align_type:
                    x = 15
                elif "右寄せ" in align_type:
                    x = self.current_preview_w - text_w - 15
                else:
                    x = (self.current_preview_w - text_w) // 2
                    
                y = self.current_preview_h - text_h - margin_v_preview
                
                # 輪郭 (Outline)
                ow = int(job.get("outline_width", "2"))
                ow_preview = max(0, int(ow * (self.current_preview_h / 1920.0)))
                if ow_preview > 0:
                    for adj_x in range(-ow_preview, ow_preview + 1):
                        for adj_y in range(-ow_preview, ow_preview + 1):
                            if adj_x != 0 or adj_y != 0:
                                overlay_draw.text((x + adj_x, y + adj_y), active_text, font=font, fill=(outline_color[0], outline_color[1], outline_color[2], 255), align="center")
                
                # 影 (Shadow)
                sd = int(job.get("shadow_depth", "0"))
                sd_preview = max(0, int(sd * (self.current_preview_h / 1920.0)))
                shadow_alpha = job.get("shadow_alpha", 1.0)
                if sd_preview > 0 and shadow_alpha > 0.0:
                    overlay_draw.text((x + sd_preview, y + sd_preview), active_text, font=font, fill=(outline_color[0], outline_color[1], outline_color[2], int(shadow_alpha * 255)), align="center")
                
                # テキスト描画 (太字/通常)
                is_bold = job.get("bold", False)
                fill_color_rgba = (fill_color[0], fill_color[1], fill_color[2], 255)
                if is_bold:
                    overlay_draw.text((x, y), active_text, font=font, fill=fill_color_rgba, align="center")
                    overlay_draw.text((x + 1, y), active_text, font=font, fill=fill_color_rgba, align="center")
                else:
                    overlay_draw.text((x, y), active_text, font=font, fill=fill_color_rgba, align="center")
                
                # Composite text overlay back onto canvas
                canvas.paste(overlay, (0, 0), overlay)

            # Draw Image Overlay on the preview canvas
            if job.get("overlay_enabled", False):
                opath = job.get("overlay_path", "")
                if opath and os.path.exists(opath):
                    scale = job.get("overlay_scale", 1.0)
                    angle = job.get("overlay_angle", 0.0)
                    opacity = job.get("overlay_opacity", 1.0)
                    
                    processed = preprocess_overlay_image(opath, scale, angle, opacity)
                    if processed:
                        preview_ratio = self.current_preview_w / 1080.0
                        pw = int(processed.width * preview_ratio)
                        ph = int(processed.height * preview_ratio)
                        if pw > 0 and ph > 0:
                            preview_overlay = processed.resize((pw, ph), PIL.Image.Resampling.LANCZOS)
                            
                            px_base = int(job.get("overlay_x", 100) * preview_ratio)
                            py_base = int(job.get("overlay_y", 100) * preview_ratio)
                            anchor = job.get("overlay_anchor", "重心 (中央)")
                            
                            if anchor == "重心 (中央)":
                                px = px_base - pw // 2
                                py = py_base - ph // 2
                            elif anchor == "右上":
                                px = px_base - pw
                                py = py_base
                            elif anchor == "左下":
                                px = px_base
                                py = py_base - ph
                            elif anchor == "右下":
                                px = px_base - pw
                                py = py_base - ph
                            else: # "左上"
                                px = px_base
                                py = py_base
                                
                            canvas.paste(preview_overlay, (px, py), preview_overlay)

        img = ctk.CTkImage(light_image=canvas, dark_image=canvas, size=(self.current_preview_w, self.current_preview_h))
        self.preview_panel.configure(image=img, text="")
        self.preview_panel.image = img

    def update_playback_time_label(self):
        if self.preview_cap:
            cur_sec = max(0.0, (self.preview_current_frame - self.job_start_frame) / self.preview_fps)
            tot_sec = max(0.0, (self.job_end_frame - self.job_start_frame) / self.preview_fps)
            self.time_label.configure(text=f"{seconds_to_minsec(cur_sec)} / {seconds_to_minsec(tot_sec)}")

    def start_whisper_for_active_job(self):
        if self.active_job_index == -1: messagebox.showwarning("警告", "候補を選択してください。"); return
        audio_mod.init_whisper()
        if not audio_mod.WHISPER_AVAILABLE:
            messagebox.showerror("エラー", f"openai-whisper が検出されませんでした。\n\n【詳細なエラー理由】:\n{audio_mod.WHISPER_LOAD_ERROR}")
            return
        job = self.jobs[self.active_job_index]
        self.whisper_btn.configure(state="disabled", text="⚡ 音声切り出し＆AI認識を実行中...")
        threading.Thread(target=self.whisper_range_thread,
                         args=(self.video_entry.get().strip(), job["start"], job["end"]), daemon=True).start()

    def whisper_range_thread(self, video_path, start_time, end_time):
        video_mod.init_video_libs()
        temp_audio = os.path.join("temp", "temp_segment_audio_single.wav")
        old_out, old_err = sys.stdout, sys.stderr
        sys.stdout = sys.stderr = StdoutQueueRedirector(self.log_queue)
        try:
            print(f"\n🔊 音声抽出中 ({seconds_to_hms(start_time)} ～ {seconds_to_hms(end_time)})...")
            
            if os.path.exists(temp_audio):
                try: os.remove(temp_audio)
                except Exception: pass
                
            with video_mod.VideoFileClip(self.get_safe_audio_path(video_path)) as v:
                duration = v.duration
                if start_time >= duration:
                    raise ValueError(f"開始時間 ({seconds_to_hms(start_time)}) が動画の長さ ({seconds_to_hms(duration)}) を超えています。")
                safe_end_time = min(duration, end_time)
                a = v.subclip(max(0, start_time), safe_end_time).audio
                if a is None:
                    raise ValueError("音声ストリームがありません。")
                a.write_audiofile(temp_audio, codec="pcm_s16le", fps=16000, logger=None)
                a.close()

            audio_mod.patch_whisper_assets()

            print("🧠 Whisperモデルをロード中...")
            model = audio_mod.whisper.load_model("small")

            reg_words = self.config_data.get("registered_words", "初狐羽鹿, Vtuber, 逆転裁判, 切り抜き")
            rep_dict = self.config_data.get("replace_dict", {})

            try: s_off = float(self.config_data.get("whisper_start_offset", -0.2))
            except ValueError: s_off = -0.2
            try: e_off = float(self.config_data.get("whisper_end_offset", -0.2))
            except ValueError: e_off = -0.2
            segs = audio_mod.transcribe_audio_segment(
                model, temp_audio, initial_prompt=reg_words, replace_dict=rep_dict,
                start_offset=s_off, end_offset=e_off
            )
            
            for _ in range(10):
                try:
                    if os.path.exists(temp_audio): os.remove(temp_audio)
                    break
                except Exception: time.sleep(0.1)
                
            self.after(0, lambda: self.on_whisper_range_complete(segs))

        except Exception as err:
            for _ in range(10):
                try:
                    if os.path.exists(temp_audio): os.remove(temp_audio)
                    break
                except Exception: time.sleep(0.1)
            print(f"❌ エラー:\n{traceback.format_exc()}")
            self.after(0, lambda: messagebox.showerror("エラー", str(err)))
        finally:
            sys.stdout, sys.stderr = old_out, old_err
            self.after(0, lambda: self.whisper_btn.configure(
                state="normal", text="🪄 AIで字幕を自動生成 (この範囲のみの音声を解析)"))

    def on_whisper_range_complete(self, segments):
        if self.active_job_index != -1:
            job = self.jobs[self.active_job_index]
            
            if job.get("intro_telop"):
                first_start = segments[0]["start"] if segments else 3.0
                telop_end = min(3.0, max(1.5, first_start))
                segments.insert(0, {
                    "start": 0.0,
                    "end": telop_end,
                    "text": job["intro_telop"]
                })
                
            job["subtitles"] = segments
            self.render_subtitle_editor_from_active_job()
            self.refresh_job_select_menu()
            self.show_current_frame()
            messagebox.showinfo("完了", f"字幕 {len(segments)}件 を生成しました！")

    def render_subtitle_editor_from_active_job(self):
        for wg in self.subtitle_widgets:
            for k in ["start", "end", "text", "frame"]:
                if k in wg and wg[k]: wg[k].destroy()
        self.subtitle_widgets.clear()
        if self.active_job_index == -1: return
        
        subs = self.jobs[self.active_job_index]["subtitles"]
        for i, sub in enumerate(subs):
            rf = ctk.CTkFrame(self.sub_scroll, fg_color="transparent")
            rf.grid(row=i, column=0, columnspan=3, padx=2, pady=2, sticky="ew")
            self.sub_scroll.grid_columnconfigure(0, weight=1)
            
            up_btn = ctk.CTkButton(rf, text="▲", width=18, height=22, fg_color="gray25", hover_color="gray40",
                                   command=lambda idx=i: self.move_subtitle_up(idx))
            up_btn.pack(side="left", padx=1, anchor="center")
            
            down_btn = ctk.CTkButton(rf, text="▼", width=18, height=22, fg_color="gray25", hover_color="gray40",
                                     command=lambda idx=i: self.move_subtitle_down(idx))
            down_btn.pack(side="left", padx=(1, 4), anchor="center")

            pb = ctk.CTkButton(rf, text="▶", width=25, height=25, fg_color="forestgreen", hover_color="darkgreen",
                               command=lambda idx=i: self.play_subtitle_segment(idx))
            pb.pack(side="left", padx=2, anchor="center")
            
            se = ctk.CTkEntry(rf, width=72, font=("Consolas", 11))
            se.insert(0, seconds_to_minsec(sub['start']))
            se.pack(side="left", padx=2, anchor="center")
            se.bind("<KeyRelease>", lambda event: self.on_subtitle_text_edited())
            se.bind("<FocusOut>", lambda event: self.on_subtitle_time_focus_out())
            
            ctk.CTkLabel(rf, text="～").pack(side="left", padx=1, anchor="center")
            
            ee = ctk.CTkEntry(rf, width=72, font=("Consolas", 11))
            ee.insert(0, seconds_to_minsec(sub['end']))
            ee.pack(side="left", padx=2, anchor="center")
            ee.bind("<KeyRelease>", lambda event: self.on_subtitle_text_edited())
            ee.bind("<FocusOut>", lambda event: self.on_subtitle_time_focus_out())
            
            db = ctk.CTkButton(rf, text="✖", width=25, height=25, fg_color="firebrick", hover_color="darkred",
                               command=lambda idx=i: self.delete_subtitle_line(idx))
            db.pack(side="left", padx=2, anchor="center")
            
            te = ctk.CTkTextbox(rf, height=45, font=(self.ui_font_family, self.ui_font_size), activate_scrollbars=False, border_width=1, border_color="#555555")
            te.insert("1.0", sub["text"])
            te.pack(side="left", padx=5, fill="x", expand=True, anchor="center")
            te.bind("<KeyRelease>", lambda event: self.on_subtitle_text_edited())
            
            self.subtitle_widgets.append({"frame": rf, "start": se, "end": ee, "text": te})
            
        row_idx = len(subs)
        add_frame = ctk.CTkFrame(self.sub_scroll, fg_color="transparent")
        add_frame.grid(row=row_idx, column=0, columnspan=3, padx=2, pady=5, sticky="ew")
        
        self.subtitle_widgets.append({"frame": add_frame})
        
        add_btn = ctk.CTkButton(add_frame, text="➕ 字幕行を追加", fg_color="teal", hover_color="darkteal",
                                command=self.add_new_subtitle_line)
        add_btn.pack(pady=2)

        # 一括タイミング調整用コントロールを追加
        shift_frame = ctk.CTkFrame(add_frame, fg_color="transparent")
        shift_frame.pack(pady=(10, 2))
        
        ctk.CTkLabel(shift_frame, text="⏱一括タイミング調整 (秒):", font=ctk.CTkFont(size=11, weight="bold")).pack(side="left", padx=2)
        self.shift_entry = ctk.CTkEntry(shift_frame, width=50, placeholder_text="-0.2", font=("Consolas", 11))
        self.shift_entry.pack(side="left", padx=2)
        shift_btn = ctk.CTkButton(shift_frame, text="シフト適用", width=70, fg_color="gray30", hover_color="gray45",
                                  command=self.shift_all_subtitles)
        shift_btn.pack(side="left", padx=2)

    def play_subtitle_segment(self, sub_idx):
        if self.active_job_index == -1: return
        job = self.jobs[self.active_job_index]
        sub = job["subtitles"][sub_idx]
        
        if self.preview_playing:
            self.toggle_play()
            
        video_path = self.video_entry.get().strip()
        if not video_path or not os.path.exists(video_path): return
        
        abs_start = job["start"] + sub["start"]
        abs_end = job["start"] + sub["end"]
        
        import tempfile
        temp_sub_audio = os.path.join(tempfile.gettempdir(), f"kirinuki_play_audio_sub_{self.active_job_index}.wav")
        
        def prepare_and_play():
            try:
                import winsound
                winsound.PlaySound(None, winsound.SND_PURGE)
            except Exception: pass
            
            try:
                if os.path.exists(temp_sub_audio):
                    try: os.remove(temp_sub_audio)
                    except Exception: pass
                
                with video_mod.VideoFileClip(self.get_safe_audio_path(video_path)) as v:
                    duration = v.duration
                    safe_end = min(duration, abs_end)
                    a = v.subclip(max(0.0, abs_start), safe_end).audio
                    if a is not None:
                        a.write_audiofile(temp_sub_audio, codec="pcm_s16le", fps=44100, logger=None)
                        a.close()
                
                self.after(0, lambda: self.start_sub_segment_playback(abs_start, abs_end, temp_sub_audio))
            except Exception as e:
                print(f"字幕範囲音声の切り出し失敗: {e}")
                
        threading.Thread(target=prepare_and_play, daemon=True).start()

    def start_sub_segment_playback(self, abs_start, abs_end, audio_path):
        if not self.preview_cap: return
        
        self.preview_start_frame = min(int(abs_start * self.preview_fps), self.preview_total_frames - 1)
        self.preview_end_frame = min(int(abs_end * self.preview_fps), self.preview_total_frames)
        self.preview_current_frame = self.preview_start_frame
        
        self.preview_cap.set(cv2.CAP_PROP_POS_FRAMES, self.preview_current_frame)
        self.preview_playing = True
        self.play_btn.configure(text="⏸")
        
        try:
            import winsound
            winsound.PlaySound(self.get_safe_audio_path(audio_path), winsound.SND_ASYNC | winsound.SND_FILENAME)
        except Exception as e:
            print(f"字幕音声再生失敗: {e}")
            
        self.playback_loop()

    def move_subtitle_up(self, sub_idx):
        if self.active_job_index == -1: return
        self.save_current_editor_to_active_job()
        job = self.jobs[self.active_job_index]
        subs = job["subtitles"]
        if sub_idx > 0:
            subs[sub_idx], subs[sub_idx - 1] = subs[sub_idx - 1], subs[sub_idx]
            self.render_subtitle_editor_from_active_job()
            self.refresh_job_select_menu()
            self.show_current_frame()

    def move_subtitle_down(self, sub_idx):
        if self.active_job_index == -1: return
        self.save_current_editor_to_active_job()
        job = self.jobs[self.active_job_index]
        subs = job["subtitles"]
        if sub_idx < len(subs) - 1:
            subs[sub_idx], subs[sub_idx + 1] = subs[sub_idx + 1], subs[sub_idx]
            self.render_subtitle_editor_from_active_job()
            self.refresh_job_select_menu()
            self.show_current_frame()

    def delete_subtitle_line(self, sub_idx):
        if self.active_job_index == -1: return
        self.save_current_editor_to_active_job()
        job = self.jobs[self.active_job_index]
        if 0 <= sub_idx < len(job["subtitles"]):
            del job["subtitles"][sub_idx]
            self.render_subtitle_editor_from_active_job()
            self.refresh_job_select_menu()
            self.show_current_frame()

    def add_new_subtitle_line(self):
        if self.active_job_index == -1: return
        self.save_current_editor_to_active_job()
        job = self.jobs[self.active_job_index]
        
        new_start = 0.0
        if job["subtitles"]:
            new_start = job["subtitles"][-1]["end"]
            
        job_duration = job["end"] - job["start"]
        new_end = min(job_duration, new_start + 2.0)
        
        job["subtitles"].append({
            "start": new_start,
            "end": new_end,
            "text": "新規字幕"
        })
        self.render_subtitle_editor_from_active_job()
        self.refresh_job_select_menu()
        self.show_current_frame()

    def on_subtitle_time_focus_out(self):
        self.save_current_editor_to_active_job()
        job = self.jobs[self.active_job_index]
        job["subtitles"].sort(key=lambda x: x["start"])
        self.render_subtitle_editor_from_active_job()
        self.refresh_job_select_menu()
        self.show_current_frame()

    def on_subtitle_text_edited(self):
        self.save_current_editor_to_active_job()
        self.show_current_frame()

    def shift_all_subtitles(self):
        if self.active_job_index == -1:
            messagebox.showwarning("警告", "対象の候補が選択されていません。")
            return
        
        offset_str = self.shift_entry.get().strip()
        try:
            offset = float(offset_str)
        except ValueError:
            messagebox.showerror("エラー", "数値（例: -0.2 や 0.5 など）を入力してください。")
            return
        
        self.save_current_editor_to_active_job()
        
        job = self.jobs[self.active_job_index]
        subs = job["subtitles"]
        if not subs:
            messagebox.showinfo("情報", "調整する字幕がありません。")
            return
            
        for sub in subs:
            sub["start"] = max(0.0, sub["start"] + offset)
            sub["end"] = max(0.0, sub["end"] + offset)
            
        self.render_subtitle_editor_from_active_job()
        self.refresh_job_select_menu()
        self.show_current_frame()
        messagebox.showinfo("完了", f"すべての字幕タイミングを {offset:+.2f} 秒シフトしました。")

    def save_current_editor_to_active_job(self):
        if self.active_job_index == -1: return
        if not hasattr(self, "subtitle_widgets") or not self.subtitle_widgets:
            return
        subs = []
        for wg in self.subtitle_widgets:
            if "start" in wg and "end" in wg and "text" in wg:
                try:
                    s = minsec_to_seconds(wg["start"].get())
                    e = minsec_to_seconds(wg["end"].get())
                    t = wg["text"].get("1.0", "end-1c").strip()
                    if t: subs.append({"start": s, "end": e, "text": t})
                except ValueError: pass
        self.jobs[self.active_job_index]["subtitles"] = subs
        self.jobs[self.active_job_index]["fontsize"] = self.fontsize_menu.get()
        self.jobs[self.active_job_index]["color"] = self.color_entry.get().strip()
        self.jobs[self.active_job_index]["fontname"] = self.font_menu.get()
        
        try: margin_v = int(self.margin_v_slider.get())
        except Exception: margin_v = 500
        self.jobs[self.active_job_index]["margin_v"] = margin_v
        
        self.jobs[self.active_job_index]["loud_zoom"] = self.loud_zoom_var.get()
        self.jobs[self.active_job_index]["bold"] = self.bold_var.get()
        self.jobs[self.active_job_index]["italic"] = self.italic_var.get()
        self.jobs[self.active_job_index]["outline_width"] = self.outline_width_menu.get()
        self.jobs[self.active_job_index]["shadow_depth"] = self.shadow_depth_menu.get()
        self.jobs[self.active_job_index]["outline_color"] = self.outline_color_entry.get().strip()
        self.jobs[self.active_job_index]["alignment"] = self.alignment_btn.get()
        self.jobs[self.active_job_index]["shadow_alpha"] = float(self.shadow_alpha_slider.get())
        
        # Image overlay fields
        self.jobs[self.active_job_index]["overlay_path"] = self.overlay_path_entry.get().strip()
        self.jobs[self.active_job_index]["overlay_x"] = int(self.overlay_x_slider.get())
        self.jobs[self.active_job_index]["overlay_y"] = int(self.overlay_y_slider.get())
        self.jobs[self.active_job_index]["overlay_scale"] = float(self.overlay_scale_slider.get())
        self.jobs[self.active_job_index]["overlay_angle"] = float(self.overlay_angle_slider.get())
        self.jobs[self.active_job_index]["overlay_opacity"] = float(self.overlay_opacity_slider.get())
        self.jobs[self.active_job_index]["overlay_enabled"] = self.overlay_enabled_var.get()
        self.jobs[self.active_job_index]["overlay_anchor"] = self.overlay_anchor_menu.get()

    def open_color_picker(self, color_type):
        if color_type == "color":
            current_color_str = self.color_entry.get().strip()
            picker = ColorPickerDialog(self, title="テキスト色を選択", initial_color=current_color_str)
            self.wait_window(picker)
            if picker.result:
                self.color_entry.delete(0, "end")
                self.color_entry.insert(0, picker.result.upper())
                self.on_text_style_changed()
        elif color_type == "outline":
            current_color_str = self.outline_color_entry.get().strip()
            picker = ColorPickerDialog(self, title="境界線色を選択", initial_color=current_color_str)
            self.wait_window(picker)
            if picker.result:
                self.outline_color_entry.delete(0, "end")
                self.outline_color_entry.insert(0, picker.result.upper())
                self.on_text_style_changed()

    def on_text_style_changed(self):
        if self.active_job_index == -1: return
        self.save_current_editor_to_active_job()
        job = self.jobs[self.active_job_index]
        
        # Update color preview widgets
        rgb = parse_color_to_rgb(job["color"])
        hex_color = f"#{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}"
        self.color_preview.configure(fg_color=hex_color)
        
        outline_rgb = parse_color_to_rgb(job.get("outline_color", "#000000"))
        outline_hex = f"#{outline_rgb[0]:02X}{outline_rgb[1]:02X}{outline_rgb[2]:02X}"
        if hasattr(self, "outline_color_preview"):
            self.outline_color_preview.configure(fg_color=outline_hex)
            
        color_hex = rgb_to_ass_hex(rgb)
        outline_color_hex = rgb_to_ass_hex(outline_rgb)
        
        amap = {"左寄せ": 1, "中央寄せ": 2, "右寄せ": 3}
        for item in self.processing_queue:
            if item.get("job_index") == self.active_job_index:
                item["fontsize"] = job["fontsize"]
                item["fontname"] = job.get("fontname", "MS Gothic")
                item["color_hex"] = color_hex
                item["margin_v"] = job.get("margin_v", 500)
                item["loud_zoom"] = job.get("loud_zoom", False)
                item["bold"] = job.get("bold", False)
                item["italic"] = job.get("italic", False)
                item["outline_width"] = int(job.get("outline_width", "2"))
                item["shadow_depth"] = int(job.get("shadow_depth", "0"))
                item["outline_color_hex"] = outline_color_hex
                item["alignment"] = amap.get(job.get("alignment", "中央寄せ"), 2)
                item["shadow_alpha"] = job.get("shadow_alpha", 1.0)
                
                # Image overlay parameters
                item["overlay_path"] = job.get("overlay_path", "")
                item["overlay_x"] = job.get("overlay_x", 100)
                item["overlay_y"] = job.get("overlay_y", 100)
                item["overlay_scale"] = job.get("overlay_scale", 1.0)
                item["overlay_angle"] = job.get("overlay_angle", 0.0)
                item["overlay_opacity"] = job.get("overlay_opacity", 1.0)
                item["overlay_enabled"] = job.get("overlay_enabled", False)
                item["overlay_anchor"] = job.get("overlay_anchor", "重心 (中央)")
                
        self.render_queue_list()
        self.show_current_frame()

    def add_active_job_to_queue(self):
        if self.active_job_index == -1: messagebox.showwarning("警告", "項目を選択してください。"); return
        self.save_current_editor_to_active_job()
        job = self.jobs[self.active_job_index]
        vp = self.video_entry.get().strip()
        if not vp or not os.path.exists(vp): messagebox.showerror("エラー", "動画パスが不正です。"); return
        
        rgb = parse_color_to_rgb(job["color"])
        color_hex = rgb_to_ass_hex(rgb)
        outline_rgb = parse_color_to_rgb(job.get("outline_color", "#000000"))
        outline_color_hex = rgb_to_ass_hex(outline_rgb)
        
        amap = {"左寄せ": 1, "中央寄せ": 2, "右寄せ": 3}
        self.processing_queue.append({
            "job_index": self.active_job_index,
            "video_path": vp, "buffer": int(self.buffer_slider.get()),
            "start": job["start"], "end": job["end"], "title": job["title"],
            "subtitles": list(job["subtitles"]), "fontsize": job["fontsize"],
            "fontname": job.get("fontname", "MS Gothic"),
            "color_hex": color_hex,
            "margin_v": job.get("margin_v", 500),
            "loud_zoom": job.get("loud_zoom", False),
            "bold": job.get("bold", False),
            "italic": job.get("italic", False),
            "outline_width": int(job.get("outline_width", "2")),
            "shadow_depth": int(job.get("shadow_depth", "0")),
            "outline_color_hex": outline_color_hex,
            "alignment": amap.get(job.get("alignment", "中央寄せ"), 2),
            "shadow_alpha": job.get("shadow_alpha", 1.0),
            
            # Image overlay parameters
            "overlay_path": job.get("overlay_path", ""),
            "overlay_x": job.get("overlay_x", 100),
            "overlay_y": job.get("overlay_y", 100),
            "overlay_scale": job.get("overlay_scale", 1.0),
            "overlay_angle": job.get("overlay_angle", 0.0),
            "overlay_opacity": job.get("overlay_opacity", 1.0),
            "overlay_enabled": job.get("overlay_enabled", False),
            "overlay_anchor": job.get("overlay_anchor", "重心 (中央)")
        })
        self.render_queue_list()
        messagebox.showinfo("追加完了", f"「{job['title']}」をキューに追加しました！({len(self.processing_queue)}件)")

    def render_queue_list(self):
        for w in self.queue_widgets: w.destroy()
        self.queue_widgets.clear()
        for i, item in enumerate(self.processing_queue):
            rf = ctk.CTkFrame(self.queue_scrollable)
            rf.grid(row=i, column=0, padx=5, pady=4, sticky="ew")
            self.queue_scrollable.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(rf, text=f"{i + 1}. {item['title']}\n   ({seconds_to_hms(item['start'])}～{seconds_to_hms(item['end'])}, 字幕:{len(item['subtitles'])}件)",
                          anchor="w", justify="left", font=ctk.CTkFont(size=11)).pack(side="left", padx=5, pady=2, fill="x", expand=True)
            ctk.CTkButton(rf, text="削除", width=40, height=20, fg_color="#c0392b", hover_color="#962d22",
                          command=lambda idx=i: self.delete_queue_item(idx)).pack(side="right", padx=5)
            self.queue_widgets.append(rf)

    def delete_queue_item(self, idx):
        if 0 <= idx < len(self.processing_queue):
            del self.processing_queue[idx]; self.render_queue_list()

    def clear_all_queues(self):
        if self.processing_queue and messagebox.askyesno("全削除", "すべてのキューを削除しますか？"):
            self.processing_queue.clear(); self.render_queue_list()

    def start_processing_queue(self):
        if not self.processing_queue: messagebox.showwarning("警告", "処理キューが空です。"); return
        for b in [self.run_btn, self.apply_inst_btn, self.add_queue_btn, self.queue_clear_btn]: b.configure(state="disabled")
        self.processing_failed = False; self.error_details = ""
        self.log_text.configure(state="normal"); self.log_text.delete("1.0", "end"); self.log_text.configure(state="disabled")
        
        try:
            import winsound
            winsound.PlaySound(None, winsound.SND_PURGE)
        except Exception: pass
        
        threading.Thread(target=self.process_queue_run_thread, daemon=True).start()

    def process_queue_run_thread(self):
        old_out, old_err = sys.stdout, sys.stderr
        sys.stdout = sys.stderr = StdoutQueueRedirector(self.log_queue)
        try:
            export_srt = self.export_srt_var.get()
            export_ae_csv = self.export_ae_csv_var.get()
            no_burn_in = self.no_burn_in_var.get()

            outdir = "ショート"; os.makedirs(outdir, exist_ok=True)
            print(f"🚀 {len(self.processing_queue)}件のタスクを開始します...\n")
            total = 0
            for idx, item in enumerate(self.processing_queue):
                try:
                    out = video_mod.process_single_clip(
                        video_path=item["video_path"],
                        start_time=item["start"],
                        end_time=item["end"],
                        title=item["title"],
                        subtitles=item["subtitles"],
                        font_size=item["fontsize"],
                        font_name=item["fontname"],
                        color_hex=item["color_hex"],
                        index=idx + 1,
                        outdir=outdir,
                        export_srt=export_srt,
                        export_ae_csv=export_ae_csv,
                        no_burn_in=no_burn_in,
                        margin_v=item.get("margin_v", 50),
                        loud_zoom=item.get("loud_zoom", False),
                        bold=item.get("bold", False),
                        italic=item.get("italic", False),
                        outline_width=item.get("outline_width", 2),
                        shadow_depth=item.get("shadow_depth", 0),
                        outline_color_hex=item.get("outline_color_hex", "&H000000"),
                        alignment=item.get("alignment", 2),
                        shadow_alpha=item.get("shadow_alpha", 1.0),
                        overlay_path=item.get("overlay_path", ""),
                        overlay_x=item.get("overlay_x", 100),
                        overlay_y=item.get("overlay_y", 100),
                        overlay_scale=item.get("overlay_scale", 1.0),
                        overlay_angle=item.get("overlay_angle", 0.0),
                        overlay_opacity=item.get("overlay_opacity", 1.0),
                        overlay_enabled=item.get("overlay_enabled", False),
                        overlay_anchor=item.get("overlay_anchor", "重心 (中央)")
                    )
                    if out:
                        total += 1
                except Exception as e:
                    self.processing_failed = True
                    self.error_details += f"\n--- No.{idx + 1} ({item['title']}) ---\n{traceback.format_exc()}"
                    print(f"  ❌ {e}")
            print(f"\n✨ 完了！({total}本)\n📁 ショート")
            self.after(0, lambda: self.processing_queue.clear())
            self.after(0, self.render_queue_list)

        except Exception as e:
            self.processing_failed = True
            self.error_details += f"\n--- 致命的エラー ---\n{traceback.format_exc()}"
            print(f"\n❌ 予期せぬエラー: {e}")
        finally:
            sys.stdout, sys.stderr = old_out, old_err
            self.after(0, self.enable_ui)

    def enable_ui(self):
        for b in [self.run_btn, self.apply_inst_btn, self.add_queue_btn, self.queue_clear_btn]: b.configure(state="normal")
        self.update_log_from_queue()
        if self.processing_failed: messagebox.showerror("エラー", f"一部エラーが発生しました。\n{self.error_details}")
        else: messagebox.showinfo("完了", "すべての切り抜き処理が正常に完了しました！")

    def on_ui_font_changed(self, new_font):
        self.config_data["ui_font_family"] = new_font
        self.config_manager.save_config(self.config_data)
        messagebox.showinfo("フォント変更", "UIフォント設定を保存しました。アプリを再起動すると適用されます。")

    def on_preview_container_configure(self, event):
        if event.width < 50 or event.height < 50:
            return
        
        w = event.width
        h = event.height
        aspect = 9.0 / 16.0
        
        tw = w
        th = int(w / aspect)
        if th > h:
            th = h
            tw = int(h * aspect)
            
        self.current_preview_w = max(150, tw)
        self.current_preview_h = max(270, th)
        self.show_current_frame()

    def update_log_from_queue(self):
        try:
            while True:
                msg = self.log_queue.get_nowait()
                self.log_text.configure(state="normal")
                self.log_text.insert("end", msg)
                self.log_text.see("end")
                self.log_text.configure(state="disabled")
                self.log_queue.task_done()
        except queue.Empty: pass
        self.after(100, self.update_log_from_queue)

    def open_gemini(self): webbrowser.open("https://gemini.google.com/gem/1-NnW8oFGipP0P0J4AsnmvC1082UrK3xy?usp=sharing")
    def open_youtube_studio(self): webbrowser.open("https://studio.youtube.com/channel/")

    def load_prompt_template(self):
        tpl = self.config_data["templates"][self.config_data["active_template"]]
        self.prompt_textbox.delete("1.0", "end"); self.prompt_textbox.insert("1.0", tpl)

    def on_template_changed(self, c):
        self.config_data["active_template"] = c; self.config_manager.save_config(self.config_data); self.load_prompt_template()

    def save_current_template(self):
        a = self.config_data["active_template"]
        self.config_data["templates"][a] = self.prompt_textbox.get("1.0", "end-1c")
        self.config_manager.save_config(self.config_data); messagebox.showinfo("保存完了", f"「{a}」を上書き保存しました。")

    def save_new_template(self):
        name = simpledialog.askstring("新規保存", "新しいテンプレート名を入力:")
        if not name: return
        name = name.strip()
        if name in self.config_data["templates"] and not messagebox.askyesno("警告", "上書きしますか？"): return
        self.config_data["templates"][name] = self.prompt_textbox.get("1.0", "end-1c")
        self.config_data["active_template"] = name; self.config_manager.save_config(self.config_data)
        self.tpl_menu.configure(values=list(self.config_data["templates"].keys())); self.tpl_menu.set(name)
        messagebox.showinfo("保存完了", f"「{name}」を保存しました。")

    def delete_current_template(self):
        a = self.config_data["active_template"]
        if len(self.config_data["templates"]) <= 1: messagebox.showwarning("警告", "最低1つ残す必要があります。"); return
        if not messagebox.askyesno("削除確認", f"「{a}」を削除しますか？"): return
        del self.config_data["templates"][a]
        nk = list(self.config_data["templates"].keys())[0]
        self.config_data["active_template"] = nk; self.config_manager.save_config(self.config_data)
        self.tpl_menu.configure(values=list(self.config_data["templates"].keys())); self.tpl_menu.set(nk)
        self.load_prompt_template()

    def copy_prompt(self):
        cs = self.count_entry.get().strip()
        if not cs.isdigit() or int(cs) <= 0:
            messagebox.showwarning("警告", "正の整数を入力してください。")
            return
        cv = int(cs)
        url = self.youtube_entry.get().strip()
        
        name_val = getattr(self, "profile_name_entry", None) and self.profile_name_entry.get().strip() or ""
        char_val = getattr(self, "profile_char_entry", None) and self.profile_char_entry.get().strip() or ""
        target_val = getattr(self, "profile_target_entry", None) and self.profile_target_entry.get().strip() or ""
        target_future_val = getattr(self, "profile_target_future_entry", None) and self.profile_target_future_entry.get().strip() or ""

        missing_required = []
        if not name_val: missing_required.append("・配信者名・チャンネル名")
        if not char_val: missing_required.append("・キャラクター・主な特徴・性格")
        if not target_val: missing_required.append("・現在の主な視聴者層・ターゲット")
        if not target_future_val: missing_required.append("・今後狙いたい視聴者層・ターゲット")

        if missing_required:
            err_msg = "高精度なプロンプトを作成するため、以下の【必須項目】を入力してください:\n\n" + "\n".join(missing_required)
            messagebox.showwarning("必須項目の未入力", err_msg)
            return

        tone_val = getattr(self, "profile_tone_entry", None) and self.profile_tone_entry.get().strip() or ""
        phrases_val = getattr(self, "profile_phrases_entry", None) and self.profile_phrases_entry.get().strip() or ""
        genre_val = getattr(self, "profile_genre_entry", None) and self.profile_genre_entry.get().strip() or ""
        ng_val = getattr(self, "profile_ng_entry", None) and self.profile_ng_entry.get().strip() or ""
        subscribers_val = getattr(self, "profile_subscribers_entry", None) and self.profile_subscribers_entry.get().strip() or ""
        platforms_val = getattr(self, "profile_platforms_entry", None) and self.profile_platforms_entry.get().strip() or ""
        shorts_val = getattr(self, "profile_shorts_entry", None) and self.profile_shorts_entry.get().strip() or ""

        v_title = getattr(self, "video_title_entry", None) and self.video_title_entry.get().strip() or ""
        v_summary = getattr(self, "video_summary_entry", None) and self.video_summary_entry.get().strip() or ""
        v_focus = getattr(self, "video_focus_entry", None) and self.video_focus_entry.get().strip() or ""

        self.config_data["target_count"] = cv
        self.config_data["last_youtube_url"] = url
        self.config_data["last_streamer_name"] = name_val
        self.config_data["last_streamer_profile_char"] = char_val
        self.config_data["last_streamer_profile_target"] = target_val
        self.config_data["last_streamer_profile_target_future"] = target_future_val
        self.config_data["last_streamer_profile_tone"] = tone_val
        self.config_data["last_streamer_profile_phrases"] = phrases_val
        self.config_data["last_streamer_profile_genre"] = genre_val
        self.config_data["last_streamer_profile_ng"] = ng_val
        self.config_data["last_streamer_profile_subscribers"] = subscribers_val
        self.config_data["last_streamer_profile_platforms"] = platforms_val
        self.config_data["last_streamer_profile_shorts"] = shorts_val
        self.config_data["last_video_title"] = v_title
        self.config_data["last_video_summary"] = v_summary
        self.config_data["last_video_focus"] = v_focus
        self.config_manager.save_config(self.config_data)
        
        profile_parts = []
        if name_val: profile_parts.append(f"■配信者名・チャンネル名: {name_val}")
        if char_val: profile_parts.append(f"■キャラクター・特徴・性格: {char_val}")
        if target_val: profile_parts.append(f"■現在の主な視聴者層: {target_val}")
        if target_future_val: profile_parts.append(f"■今後狙いたい視聴者層: {target_future_val}")
        if tone_val: profile_parts.append(f"■話し方・口調・口癖: {tone_val}")
        if phrases_val: profile_parts.append(f"■定番フレーズ・決め台詞: {phrases_val}")
        if genre_val: profile_parts.append(f"■得意ジャンル・配信テーマ: {genre_val}")
        if ng_val: profile_parts.append(f"■NGワード・避ける表現: {ng_val}")
        if subscribers_val: profile_parts.append(f"■チャンネル登録者数: {subscribers_val}")
        if platforms_val: profile_parts.append(f"■主な投稿プラットフォーム: {platforms_val}")
        if shorts_val: profile_parts.append(f"■ショート動画のバズり傾向: {shorts_val}")
            
        profile = "\n".join(profile_parts)

        video_parts = []
        if v_title: video_parts.append(f"■動画/配信タイトル: {v_title}")
        if v_summary: video_parts.append(f"■動画の内容・ハイライト概要: {v_summary}")
        if v_focus: video_parts.append(f"■特に切り抜いてほしい見どころ・テイスト: {v_focus}")

        video_info = "\n".join(video_parts)
        
        p = self.prompt_textbox.get("1.0", "end-1c")
        p = p.replace("{count}", str(cv)).replace("{count_plus_2}", str(cv + 2))
        p = p.replace("{video_url}", url).replace("*動画のリンク*", url)
        p = p.replace("{profile}", profile)
        p = p.replace("{video_info}", video_info)
        
        if profile and "{profile}" not in self.prompt_textbox.get("1.0", "end-1c"):
            p += f"\n\n# 配信者パーソナルデータ:\n{profile}"
        if video_info and "{video_info}" not in self.prompt_textbox.get("1.0", "end-1c"):
            p += f"\n\n# 今回の動画情報:\n{video_info}"
            
        self.clipboard_clear()
        self.clipboard_append(p)
        self.update()
        messagebox.showinfo("コピー完了", f"プロンプトをコピーしました！(候補数:{cv}個)")
    def on_close(self):
        try:
            import winsound
            winsound.PlaySound(None, winsound.SND_PURGE)
        except Exception: pass
        
        self.clean_temp_link()
        
        for p in glob.glob("temp_segment_audio_*.wav") + glob.glob("temp_play_audio_*.wav") + ["temp_segment_audio.wav", "temp_play_audio.wav", "temp_segment_audio_single.wav", "temp_play_audio_seek.wav"]:
            try:
                if os.path.exists(p): os.remove(p)
            except Exception: pass
            
        self.destroy()

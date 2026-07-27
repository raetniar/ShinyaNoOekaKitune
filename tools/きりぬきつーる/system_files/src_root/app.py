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
import customtkinter as ctk
from tkinter import filedialog, messagebox, simpledialog
import json

# 他の自作モジュールからインポート
from src.utils import (
    seconds_to_hms, seconds_to_hms_ms, seconds_to_minsec,
    minsec_to_seconds, time_to_seconds, clean_filename
)
import src.audio as audio_mod
import src.video as video_mod

PREVIEW_W = 216
PREVIEW_H = 384

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
        
        self.grab_set()
        
        x = parent.winfo_x() + (parent.winfo_width() - 480) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 220) // 2
        self.geometry(f"480x220+{x}+{y}")
        
        self.label = ctk.CTkLabel(self, text="AI字幕を一括自動生成しています...", font=("Segoe UI", 14, "bold"))
        self.label.pack(pady=(25, 5))
        
        self.status_label = ctk.CTkLabel(self, text=f"準備中 (0 / {total_count} 件)...", font=("Segoe UI", 12), text_color="#aaaaaa", justify="center")
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


class App(ctk.CTk):
    def __init__(self, config_manager):
        super().__init__()
        self.title("きりぬき箇所判定・一括編集ツール")
        
        self.config_manager = config_manager
        self.config_data = self.config_manager.config_data

        self.geometry("1400x1000")
        self.minsize(1150, 850)
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
        
        self.bulk_whisper_info = {}
        self.audio_ready = False
        self.temp_play_audio = "temp_play_audio.wav"

        self.create_widgets()
        self.scan_environment()
        self.update_log_from_queue()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def create_widgets(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.tab_run = self.tabview.add("切り抜き＆字幕編集（一括）")
        self.tab_prompt = self.tabview.add("Geminiプロンプト設定")
        self.setup_run_tab()
        self.bind("<Configure>", self.on_window_configure)
        self.setup_prompt_tab()

    def setup_run_tab(self):
        self.tab_run.grid_rowconfigure(1, weight=1)
        self.tab_run.grid_columnconfigure(0, weight=4)
        self.tab_run.grid_columnconfigure(1, weight=3)
        self.tab_run.grid_columnconfigure(2, weight=5)

        tf = ctk.CTkFrame(self.tab_run)
        tf.grid(row=0, column=0, columnspan=3, padx=10, pady=5, sticky="ew")
        tf.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(tf, text="対象動画:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.video_entry = ctk.CTkEntry(tf, placeholder_text="動画ファイルを選択してください...")
        self.video_entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        ctk.CTkButton(tf, text="参照...", width=80, command=self.select_video).grid(row=0, column=2, padx=10, pady=5)
        ctk.CTkButton(tf, text="💾 作業保存", width=85, command=self.save_project).grid(row=0, column=3, padx=(5, 2), pady=5)
        ctk.CTkButton(tf, text="📂 作業読込", width=85, command=self.load_project).grid(row=0, column=4, padx=(2, 10), pady=5)

        lf = ctk.CTkFrame(self.tab_run)
        lf.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
        lf.grid_rowconfigure(1, weight=1)
        lf.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(lf, text="【1. Gemini出力コピペエリア】", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=10, pady=2, sticky="w")
        self.paste_textbox = ctk.CTkTextbox(lf, height=520, font=("Segoe UI", 12))
        self.paste_textbox.grid(row=1, column=0, padx=10, pady=2, sticky="nsew")
        self.apply_inst_btn = ctk.CTkButton(lf, text="コピペから候補を読み込む", command=self.apply_paste_instructions, fg_color="#1a73e8", hover_color="#155cb4")
        self.apply_inst_btn.grid(row=2, column=0, padx=10, pady=6, sticky="ew")

        cf = ctk.CTkFrame(self.tab_run)
        cf.grid(row=1, column=1, padx=10, pady=5, sticky="nsew")
        cf.grid_rowconfigure(1, weight=1)
        cf.grid_columnconfigure(0, weight=1)
        self.list_title = ctk.CTkLabel(cf, text="【2. 切り抜き候補一覧】", font=ctk.CTkFont(weight="bold"))
        self.list_title.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.scrollable_frame = ctk.CTkScrollableFrame(cf, label_text="項目をクリックするとプレビューにロード")
        self.scrollable_frame.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
        self.scrollable_frame.grid_columnconfigure(0, weight=1)
        
        self.generate_selected_sub_btn = ctk.CTkButton(
            cf, text="🪄 選択した候補の字幕を生成",
            font=ctk.CTkFont(weight="bold"),
            fg_color="#1a73e8", hover_color="#155cb4",
            command=self.start_bulk_whisper_for_selected
        )
        self.generate_selected_sub_btn.grid(row=2, column=0, padx=10, pady=6, sticky="ew")
        cf.grid_rowconfigure(1, weight=1)

        rf = ctk.CTkFrame(self.tab_run)
        rf.grid(row=1, column=2, padx=10, pady=5, sticky="nsew")
        rf.grid_columnconfigure(0, weight=0, minsize=PREVIEW_W + 12)
        rf.grid_columnconfigure(1, weight=1)
        rf.grid_rowconfigure(5, weight=1)
        self.right_frame = rf

        ctk.CTkLabel(rf, text="【3. プレビュー＆字幕タイムライン編集】",
                     font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, columnspan=2, padx=10, pady=(8, 3), sticky="w")

        top_ctrl = ctk.CTkFrame(rf)
        top_ctrl.grid(row=1, column=0, columnspan=2, padx=10, pady=3, sticky="ew")
        ctk.CTkLabel(top_ctrl, text="フォントサイズ:").pack(side="left", padx=(8, 2), pady=4)
        self.fontsize_menu = ctk.CTkOptionMenu(top_ctrl, values=["24", "32", "36", "40", "48", "64"], width=72,
                                               command=lambda _: self.on_text_style_changed())
        self.fontsize_menu.set("36")
        self.fontsize_menu.pack(side="left", padx=2, pady=4)
        ctk.CTkLabel(top_ctrl, text="テロップ色:").pack(side="left", padx=(12, 2), pady=4)
        self.color_menu = ctk.CTkOptionMenu(top_ctrl, values=["黄 (Yellow)", "白 (White)", "赤 (Red)", "緑 (Green)"], width=105,
                                             command=lambda _: self.on_text_style_changed())
        self.color_menu.set("白 (White)")
        self.color_menu.pack(side="left", padx=2, pady=4)

        import tkinter.font as tkfont
        try: all_families = set(tkfont.families(self))
        except Exception: all_families = set()
        preferred_fonts = [
            "MS Gothic", "ＭＳ ゴシック",
            "MS PGothic", "ＭＳ Ｐゴシック",
            "Meiryo", "メイリオ",
            "Yu Gothic", "游ゴシック",
            "YuGothic", "HG丸ｺﾞｼｯｸM-PRO",
            "BIZ UDPGothic", "Segoe UI", "Arial", "Impact"
        ]
        font_list = [f for f in preferred_fonts if f in all_families]
        other_fonts = sorted([f for f in all_families if not f.startswith("@") and f not in font_list])
        font_list.extend(other_fonts)
        if not font_list:
            font_list = ["MS Gothic", "Meiryo", "Yu Gothic"]
        font_list = font_list[:35]

        ctk.CTkLabel(top_ctrl, text="フォント:").pack(side="left", padx=(12, 2), pady=4)
        self.font_menu = ctk.CTkOptionMenu(top_ctrl, values=font_list, width=130,
                                            command=lambda _: self.on_text_style_changed())
        default_font = "MS Gothic" if "MS Gothic" in font_list else font_list[0]
        self.font_menu.set(default_font)
        self.font_menu.pack(side="left", padx=2, pady=4)

        style2_ctrl = ctk.CTkFrame(rf)
        style2_ctrl.grid(row=2, column=0, columnspan=2, padx=10, pady=3, sticky="ew")
        
        ctk.CTkLabel(style2_ctrl, text="テロップ位置:").pack(side="left", padx=(8, 2), pady=4)
        self.margin_v_slider = ctk.CTkSlider(style2_ctrl, from_=20, to=1850, number_of_steps=183, command=lambda _: self.on_text_style_changed())
        self.margin_v_slider.set(500)
        self.margin_v_slider.pack(side="left", padx=2, pady=4, fill="x", expand=True)
        
        self.loud_zoom_var = ctk.BooleanVar(value=False)
        self.cb_loud_zoom = ctk.CTkCheckBox(style2_ctrl, text="大声ズームを有効にする", variable=self.loud_zoom_var, command=lambda: self.on_text_style_changed())
        self.cb_loud_zoom.pack(side="right", padx=(10, 8), pady=4)

        self.whisper_btn = ctk.CTkButton(rf,
                                         text="🪄 AIで字幕を自動生成 (この範囲のみの音声を解析)",
                                         command=self.start_whisper_for_active_job)
        self.whisper_btn.grid(row=3, column=0, columnspan=2, padx=10, pady=4, sticky="ew")

        time_ctrl = ctk.CTkFrame(rf)
        time_ctrl.grid(row=4, column=0, columnspan=2, padx=10, pady=3, sticky="ew")
        self.play_btn = ctk.CTkButton(time_ctrl, text="▶", width=38, command=self.toggle_play)
        self.play_btn.pack(side="left", padx=(4, 2), pady=3)
        ctk.CTkButton(time_ctrl, text="🎬外部", width=55, command=self.play_in_external_player).pack(side="left", padx=2, pady=3)
        self.time_label = ctk.CTkLabel(time_ctrl, text="00:00 / 00:00", width=90)
        self.time_label.pack(side="left", padx=4, pady=3)
        self.seek_slider = ctk.CTkSlider(time_ctrl, from_=0, to=100, number_of_steps=100,
                                         command=self.on_seek_drag)
        self.seek_slider.set(0)
        self.seek_slider.pack(side="left", padx=4, pady=3, fill="x", expand=True)
        ctk.CTkLabel(time_ctrl, text="開始:").pack(side="left", padx=(8, 2), pady=3)
        self.start_entry = ctk.CTkEntry(time_ctrl, placeholder_text="00:00:00", width=78)
        self.start_entry.pack(side="left", padx=2, pady=3)
        ctk.CTkLabel(time_ctrl, text="終了:").pack(side="left", padx=(4, 2), pady=3)
        self.end_entry = ctk.CTkEntry(time_ctrl, placeholder_text="00:00:00", width=78)
        self.end_entry.pack(side="left", padx=2, pady=3)
        ctk.CTkButton(time_ctrl, text="更新", width=50,
                      command=self.update_active_job_range).pack(side="left", padx=4, pady=3)

        self.preview_container = ctk.CTkFrame(rf, width=PREVIEW_W, height=PREVIEW_H, fg_color="#000000")
        self.preview_container.grid(row=5, column=0, padx=(10, 4), pady=5, sticky="n")
        self.preview_container.grid_propagate(False)

        self.preview_panel = ctk.CTkLabel(
            self.preview_container,
            text="[再生キー枠またはプレビュー画像]",
            font=ctk.CTkFont(size=10),
            wraplength=PREVIEW_W - 10,
            fg_color="#000000",
            width=PREVIEW_W,
            height=PREVIEW_H
        )
        self.preview_panel.pack(fill="both", expand=True)

        self.sub_scroll = ctk.CTkScrollableFrame(
            rf, label_text="字幕編集タイムライン (秒数・テキストは手動変更可能)")
        self.sub_scroll.grid(row=5, column=1, padx=(4, 10), pady=5, sticky="nsew")
        self.sub_scroll.grid_columnconfigure(1, weight=1)

        self.add_queue_btn = ctk.CTkButton(
            rf, text="➕ 編集した内容で処理キューに追加する",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#1a73e8", hover_color="#155cb4",
            command=self.add_active_job_to_queue)
        self.add_queue_btn.grid(row=6, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

        bf = ctk.CTkFrame(self.tab_run)
        bf.grid(row=2, column=0, columnspan=3, padx=10, pady=10, sticky="ew")
        bf.grid_columnconfigure(0, weight=4)
        bf.grid_columnconfigure(1, weight=8)

        bf_left = ctk.CTkFrame(bf, fg_color="transparent")
        bf_left.grid(row=0, column=0, padx=10, pady=5, sticky="nsew")
        bf_left.grid_columnconfigure(0, weight=1)
        bf_left.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(bf_left, text="【4. 一括処理待ちのリスト (キュー)】", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.queue_scrollable = ctk.CTkScrollableFrame(bf_left, label_text="", height=180)
        self.queue_scrollable.grid(row=1, column=0, padx=5, pady=2, sticky="nsew")
        self.queue_scrollable.grid_columnconfigure(0, weight=1)
        self.queue_clear_btn = ctk.CTkButton(bf_left, text="キューを空にする", fg_color="#c0392b", hover_color="#962d22", command=self.clear_all_queues)
        self.queue_clear_btn.grid(row=2, column=0, padx=5, pady=5, sticky="ew")

        bf_right = ctk.CTkFrame(bf, fg_color="transparent")
        bf_right.grid(row=0, column=1, padx=10, pady=5, sticky="nsew")
        bf_right.grid_columnconfigure(0, weight=1)
        bf_right.grid_rowconfigure(3, weight=1)

        opt_f = ctk.CTkFrame(bf_right)
        opt_f.grid(row=0, column=0, padx=5, pady=(2, 2), sticky="ew")
        opt_f.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(opt_f, text="前後追加バッファ時間 (秒):").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.buffer_slider = ctk.CTkSlider(opt_f, from_=0, to=60, number_of_steps=60, command=self.update_buffer_label)
        self.buffer_slider.set(0)
        self.buffer_slider.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        self.buffer_val_label = ctk.CTkLabel(opt_f, text=f"{self.config_data['buffer_seconds']}秒", width=40)
        self.buffer_val_label.grid(row=0, column=2, padx=10, pady=5)
        
        cb_f = ctk.CTkFrame(opt_f, fg_color="transparent")
        cb_f.grid(row=1, column=0, columnspan=3, padx=5, pady=5, sticky="ew")

        self.export_srt_var = ctk.BooleanVar(value=True)
        self.cb_srt = ctk.CTkCheckBox(cb_f, text="字幕ファイルを別で書き出す (.srt)", variable=self.export_srt_var)
        self.cb_srt.pack(side="left", padx=10)

        self.export_ae_csv_var = ctk.BooleanVar(value=False)
        self.cb_csv = ctk.CTkCheckBox(cb_f, text="Ae用時間軸CSVを書き出す (.csv)", variable=self.export_ae_csv_var)
        self.cb_csv.pack(side="left", padx=10)

        self.no_burn_in_var = ctk.BooleanVar(value=False)
        self.cb_noburn = ctk.CTkCheckBox(cb_f, text="動画に字幕を焼き付けない (生動画)", variable=self.no_burn_in_var)
        self.cb_noburn.pack(side="left", padx=10)

        self.run_btn = ctk.CTkButton(bf_right, text="🎬 登録されたすべてのキューを一括切り抜き実行 (開始)",
                                     font=ctk.CTkFont(size=16, weight="bold"), height=42, fg_color="#1a73e8", hover_color="#155cb4", command=self.start_processing_queue)
        self.run_btn.grid(row=1, column=0, padx=5, pady=5, sticky="ew")

        ctk.CTkLabel(bf_right, text="実行ログ / AI進捗:").grid(row=2, column=0, padx=5, pady=0, sticky="w")
        self.log_text = ctk.CTkTextbox(bf_right, height=130, font=("Consolas", 12))
        self.log_text.grid(row=3, column=0, padx=5, pady=2, sticky="ew")
        self.log_text.configure(state="disabled")

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

    def setup_prompt_tab(self):
        self.tab_prompt.grid_rowconfigure(0, weight=1)
        self.tab_prompt.grid_columnconfigure(0, weight=1)
        self.tab_prompt.grid_columnconfigure(1, weight=1)

        # 左カラム: Geminiプロンプト設定
        left_frame = ctk.CTkFrame(self.tab_prompt, fg_color="transparent")
        left_frame.grid(row=0, column=0, padx=10, pady=5, sticky="nsew")
        left_frame.grid_columnconfigure(0, weight=1)
        left_frame.grid_rowconfigure(2, weight=1)

        ptf = ctk.CTkFrame(left_frame)
        ptf.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(ptf, text="🌐 Geminiを開く", font=ctk.CTkFont(weight="bold"), height=35,
                      fg_color="#1a73e8", hover_color="#155cb4", command=self.open_gemini).grid(row=0, column=0, padx=10, pady=10, sticky="w")
        ctk.CTkButton(ptf, text="🎬 YouTube Studioを開く", font=ctk.CTkFont(weight="bold"), height=35,
                      fg_color="#e52d27", hover_color="#b31217", command=self.open_youtube_studio).grid(row=0, column=1, padx=10, pady=10, sticky="w")
        ctk.CTkLabel(ptf, text="テンプレート選択:").grid(row=0, column=2, padx=5, pady=10)
        self.tpl_menu = ctk.CTkOptionMenu(ptf, values=list(self.config_data["templates"].keys()), command=self.on_template_changed)
        self.tpl_menu.set(self.config_data["active_template"])
        self.tpl_menu.grid(row=0, column=3, padx=5, pady=10)
        ctk.CTkButton(ptf, text="削除", width=50, fg_color="firebrick", hover_color="darkred", command=self.delete_current_template).grid(row=0, column=4, padx=5, pady=10)
        ctk.CTkButton(ptf, text="別名保存...", width=85, command=self.save_new_template).grid(row=0, column=5, padx=10, pady=10)
        ctk.CTkLabel(ptf, text="目標個数:").grid(row=0, column=6, padx=5, pady=10)
        self.count_entry = ctk.CTkEntry(ptf, width=40)
        self.count_entry.insert(0, str(self.config_data["target_count"]))
        self.count_entry.grid(row=0, column=7, padx=5, pady=10)
        ctk.CTkLabel(ptf, text="個").grid(row=0, column=8, padx=2, pady=10)

        yf = ctk.CTkFrame(left_frame)
        yf.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        yf.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(yf, text="🎥 対象 of YouTube動画リンク: ", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=10, pady=8, sticky="w")
        self.youtube_entry = ctk.CTkEntry(yf, placeholder_text="https://www.youtube.com/watch?v=...")
        self.youtube_entry.insert(0, self.config_data.get("last_youtube_url", ""))
        self.youtube_entry.grid(row=0, column=1, padx=10, pady=8, sticky="ew")

        pmf = ctk.CTkFrame(left_frame)
        pmf.grid(row=2, column=0, padx=5, pady=5, sticky="nsew")
        pmf.grid_rowconfigure(1, weight=1)
        pmf.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(pmf, text="【プロンプト編集】 {video_url} や {count} はコピー時に自動置換されます", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.prompt_textbox = ctk.CTkTextbox(pmf, font=("Segoe UI", 12))
        self.prompt_textbox.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")

        pbf = ctk.CTkFrame(left_frame)
        pbf.grid(row=3, column=0, padx=5, pady=10, sticky="ew")
        ctk.CTkButton(pbf, text="現在のテンプレートに上書き保存", width=220, command=self.save_current_template).pack(side="left", padx=15, pady=10)
        ctk.CTkButton(pbf, text="📋 プロンプトをコピー", font=ctk.CTkFont(size=14, weight="bold"), height=35,
                      fg_color="forestgreen", hover_color="darkgreen", command=self.copy_prompt).pack(side="right", padx=15, pady=10)

        # 右カラム: AI文字起こし 辞書・単語登録設定
        right_frame = ctk.CTkFrame(self.tab_prompt)
        right_frame.grid(row=0, column=1, padx=10, pady=5, sticky="nsew")
        right_frame.grid_columnconfigure(0, weight=1)
        right_frame.grid_rowconfigure(2, weight=1)
        right_frame.grid_rowconfigure(4, weight=1)

        ctk.CTkLabel(right_frame, text="【AI文字起こし 辞書・単語登録】", font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0, padx=15, pady=(15, 5), sticky="w")

        ctk.CTkLabel(right_frame, text="① AIに事前に教える単語・固有名詞 (カンマ区切り):", font=ctk.CTkFont(weight="bold")).grid(row=1, column=0, padx=15, pady=(10, 2), sticky="w")
        self.reg_words_textbox = ctk.CTkTextbox(right_frame, height=120, font=("Segoe UI", 12))
        self.reg_words_textbox.grid(row=2, column=0, padx=15, pady=5, sticky="ew")
        self.reg_words_textbox.insert("1.0", self.config_data.get("registered_words", ""))

        ctk.CTkLabel(right_frame, text="② 自動で書き換える置換辞書 (間違える言葉 = 正しい言葉):", font=ctk.CTkFont(weight="bold")).grid(row=3, column=0, padx=15, pady=(10, 2), sticky="w")
        self.replace_dict_textbox = ctk.CTkTextbox(right_frame, font=("Segoe UI", 12))
        self.replace_dict_textbox.grid(row=4, column=0, padx=15, pady=5, sticky="nsew")
        
        dict_str = ""
        for bad, good in self.config_data.get("replace_dict", {}).items():
            dict_str += f"{bad} = {good}\n"
        self.replace_dict_textbox.insert("1.0", dict_str.strip())

        ctk.CTkButton(right_frame, text="💾 辞書・単語登録を保存", font=ctk.CTkFont(size=13, weight="bold"), fg_color="chocolate", hover_color="sienna",
                      command=self.save_dictionary_settings).grid(row=5, column=0, padx=15, pady=15, sticky="ew")

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

        self.config_data["registered_words"] = words
        self.config_data["replace_dict"] = rep_dict
        self.config_manager.save_config(self.config_data)
        messagebox.showinfo("保存完了", "辞書・単語登録の設定を保存しました。")

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

    def update_buffer_label(self, value):
        self.buffer_val_label.configure(text=f"{int(value)}秒")
        self.config_data["buffer_seconds"] = int(value)
        self.config_manager.save_config(self.config_data)

    def parse_instructions_text(self, content):
        results = []
        blocks = re.split(r"■\s*(?:厳選)?(?:切り抜き)?(?:箇所)?候補", content)
        if len(blocks) <= 1:
            blocks = [content]
        else:
            blocks = blocks[1:]
            
        time_pattern = r"(\d{1,2}:\d{2}(?::\d{2})?)"
        
        for block in blocks:
            lines = block.split('\n')
            times = []
            title = "no_title"
            intro_telop = ""
            
            for line in lines:
                if len(times) < 2:
                    found_times = re.findall(time_pattern, line)
                    if found_times:
                        times.extend(found_times)
                
                if any(k in line for k in ["タイトル", "バズるタイトル"]):
                    m = re.search(r"(?:タイトル|バズるタイトル)[:：]\s*(.+)", line)
                    if m:
                        raw_title = m.group(1).strip()
                        raw_title = re.sub(r"\*\*|\[|\]|「|」", "", raw_title)
                        title = clean_filename(raw_title)
                        
                if "冒頭テロップ" in line:
                    m = re.search(r"冒頭テロップ[:：]\s*(.+)", line)
                    if m:
                        raw_telop = m.group(1).strip()
                        raw_telop = re.sub(r"\*\*|\[|\]|「|」|\"|'", "", raw_telop)
                        intro_telop = raw_telop
            
            if len(times) >= 2:
                start_time = time_to_seconds(times[0])
                end_time = time_to_seconds(times[1])
                
                if title == "no_title":
                    for line in lines:
                        clean_l = line.strip()
                        if clean_l and not clean_l.startswith("■") and "タイムスタンプ" not in clean_l:
                            title = clean_filename(clean_l[:25])
                            break
                
                subtitles = []
                if intro_telop:
                    subtitles.append({
                        "start": 0.0,
                        "end": 3.0,
                        "text": intro_telop
                    })
                
                results.append({
                    "start": start_time,
                    "end": end_time,
                    "title": title,
                    "subtitles": subtitles,
                    "fontsize": "36",
                    "color": "黄 (Yellow)",
                    "intro_telop": intro_telop,
                    "margin_v": 500
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
                font=("Segoe UI", 12),
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
                
                subtitles = audio_mod.transcribe_audio_segment(model, temp_audio, initial_prompt=reg_words, replace_dict=rep_dict)
                
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
                
                subtitles = audio_mod.transcribe_audio_segment(model, temp_audio, initial_prompt=reg_words, replace_dict=rep_dict)
                
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
            self.jobs = info["jobs_copy"]
            self.active_job_index = -1
            self.render_job_list()
            self.render_subtitle_editor_from_active_job()
            self.refresh_job_select_menu()
            self.show_current_frame()
            messagebox.showinfo("完了", "選択された候補の字幕生成が完了しました！")
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

    def prepare_preview_audio(self, video_path, start_time, end_time):
        self.audio_ready = False
        try:
            import winsound
            winsound.PlaySound(None, winsound.SND_PURGE)
        except Exception: pass
        
        time.sleep(0.1)
        self.temp_play_audio = f"temp_play_audio_{self.active_job_index}.wav"
        
        try:
            for p in glob.glob("temp_play_audio_*.wav"):
                if p != self.temp_play_audio:
                    try: os.remove(p)
                    except Exception: pass
            
            if os.path.exists(self.temp_play_audio):
                try: os.remove(self.temp_play_audio)
                except Exception: pass
            
            with video_mod.VideoFileClip(self.get_safe_audio_path(video_path)) as v:
                duration = v.duration
                if start_time >= duration:
                    print("⚠️ プレビュー音声準備: 開始時間が動画長を超えています。")
                    return
                safe_end = min(duration, end_time)
                a = v.subclip(max(0.0, start_time), safe_end).audio
                if a is not None:
                    a.write_audiofile(self.temp_play_audio, codec="pcm_s16le", fps=44100, logger=None)
                    a.close()
            self.audio_ready = True
            print(f"🔊 プレビュー音声をロードしました: {self.temp_play_audio}")
        except Exception as e:
            print(f"プレビュー音声切り出し失敗: {e}")

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
            btn.configure(fg_color="#1a73e8" if i == idx else "transparent",
                          hover_color="#155cb4" if i == idx else "#2b2b2b")
        
        video_path = self.video_entry.get().strip()
        if not video_path or not os.path.exists(video_path):
            messagebox.showerror("エラー", "対象動画ファイルが見つかりません。"); return
        
        self.clean_temp_link()
        abs_path = os.path.abspath(video_path)
        try:
            os.link(abs_path, self.temp_preview_link)
            self.preview_cap = cv2.VideoCapture(self.temp_preview_link)
        except Exception:
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
        self.color_menu.set(job.get("color", "白 (White)"))
        self.font_menu.set(job.get("fontname", "MS Gothic"))
        self.margin_v_slider.set(job.get("margin_v", 500))
        self.loud_zoom_var.set(job.get("loud_zoom", False))
        
        threading.Thread(target=self.prepare_preview_audio, args=(abs_path, job["start"], job["end"]), daemon=True).start()
        
        self.update_playback_time_label()
        self.show_current_frame()
        self.render_subtitle_editor_from_active_job()
        self.refresh_job_select_menu()

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
            
            if self.audio_ready and os.path.exists(self.temp_play_audio):
                try:
                    import winsound
                    cur_sec = self.preview_current_frame / self.preview_fps
                    start_sec = self.preview_start_frame / self.preview_fps
                    end_sec = self.preview_end_frame / self.preview_fps
                    
                    if (cur_sec - start_sec) > 0.5:
                        temp_seek_audio = "temp_play_audio_seek.wav"
                        if os.path.exists(temp_seek_audio):
                            try: os.remove(temp_seek_audio)
                            except Exception: pass
                        
                        vp = self.video_entry.get().strip()
                        with video_mod.VideoFileClip(self.get_safe_audio_path(vp)) as v:
                            a = v.subclip(cur_sec, end_sec).audio
                            if a is not None:
                                a.write_audiofile(temp_seek_audio, codec="pcm_s16le", fps=44100, logger=None)
                                a.close()
                        
                        winsound.PlaySound(temp_seek_audio, winsound.SND_ASYNC | winsound.SND_FILENAME)
                    else:
                        self.preview_current_frame = self.preview_start_frame
                        self.preview_cap.set(cv2.CAP_PROP_POS_FRAMES, self.preview_start_frame)
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
        scale = PREVIEW_W / w
        nw, nh = PREVIEW_W, int(h * scale)
        if nh > PREVIEW_H:
            scale = PREVIEW_H / h
            nw, nh = int(w * scale), PREVIEW_H
        nw, nh = max(1, nw), max(1, nh)
        resized = cv2.resize(frame, (nw, nh))
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        canvas = PIL.Image.new("RGB", (PREVIEW_W, PREVIEW_H), (0, 0, 0))
        canvas.paste(PIL.Image.fromarray(rgb), ((PREVIEW_W - nw) // 2, (PREVIEW_H - nh) // 2))

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
                draw = ImageDraw.Draw(canvas)
                
                fs_original = float(job.get("fontsize", "36"))
                fs_preview = max(10, int(fs_original * (PREVIEW_W / 1080.0) * 1.5))
                
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
                
                color_map = {
                    "黄 (Yellow)": ((255, 255, 0), (0, 0, 0)),
                    "白 (White)": ((255, 255, 255), (0, 0, 0)),
                    "赤 (Red)": ((255, 0, 0), (0, 0, 0)),
                    "緑 (Green)": ((0, 255, 0), (0, 0, 0))
                }
                color_name = job.get("color", "白 (White)")
                fill_color, outline_color = color_map.get(color_name, ((255, 255, 255), (0, 0, 0)))
                
                if hasattr(draw, "textbbox"):
                    bbox = draw.textbbox((0, 0), active_text, font=font)
                    text_w = bbox[2] - bbox[0]
                    text_h = bbox[3] - bbox[1]
                else:
                    text_w, text_h = draw.textsize(active_text, font=font)
                
                margin_v = int(job.get("margin_v", 50))
                margin_v_preview = max(5, int(margin_v * (PREVIEW_H / 1920.0)))
                x = (PREVIEW_W - text_w) // 2
                y = PREVIEW_H - text_h - margin_v_preview
                
                for adj_x in range(-2, 3):
                    for adj_y in range(-2, 3):
                        draw.text((x + adj_x, y + adj_y), active_text, font=font, fill=outline_color, align="center")
                
                draw.text((x, y), active_text, font=font, fill=fill_color, align="center")

        img = ctk.CTkImage(light_image=canvas, dark_image=canvas, size=(PREVIEW_W, PREVIEW_H))
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

            print("✍️  文字起こし実行中...")
            segs = audio_mod.transcribe_audio_segment(model, temp_audio, initial_prompt=reg_words, replace_dict=rep_dict)
            
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
            
            te = ctk.CTkTextbox(rf, height=45, font=("Segoe UI", 12), activate_scrollbars=False, border_width=1, border_color="#555555")
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
            winsound.PlaySound(audio_path, winsound.SND_ASYNC | winsound.SND_FILENAME)
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
        self.jobs[self.active_job_index]["color"] = self.color_menu.get()
        self.jobs[self.active_job_index]["fontname"] = self.font_menu.get()
        self.jobs[self.active_job_index]["margin_v"] = int(self.margin_v_slider.get())
        self.jobs[self.active_job_index]["loud_zoom"] = self.loud_zoom_var.get()

    def on_text_style_changed(self):
        if self.active_job_index == -1: return
        self.save_current_editor_to_active_job()
        job = self.jobs[self.active_job_index]
        
        cmap = {"黄 (Yellow)": "&H00FFFF", "白 (White)": "&HFFFFFF", "赤 (Red)": "&H0000FF", "緑 (Green)": "&H00FF00"}
        for item in self.processing_queue:
            if item.get("job_index") == self.active_job_index:
                item["fontsize"] = job["fontsize"]
                item["fontname"] = job.get("fontname", "MS Gothic")
                item["color_hex"] = cmap.get(job["color"], "&HFFFFFF")
                item["margin_v"] = job.get("margin_v", 500)
                item["loud_zoom"] = job.get("loud_zoom", False)
        self.render_queue_list()
        self.show_current_frame()

    def add_active_job_to_queue(self):
        if self.active_job_index == -1: messagebox.showwarning("警告", "項目を選択してください。"); return
        self.save_current_editor_to_active_job()
        job = self.jobs[self.active_job_index]
        vp = self.video_entry.get().strip()
        if not vp or not os.path.exists(vp): messagebox.showerror("エラー", "動画パスが不正です。"); return
        cmap = {"黄 (Yellow)": "&H00FFFF", "白 (White)": "&HFFFFFF", "赤 (Red)": "&H0000FF", "緑 (Green)": "&H00FF00"}
        self.processing_queue.append({
            "job_index": self.active_job_index,
            "video_path": vp, "buffer": int(self.buffer_slider.get()),
            "start": job["start"], "end": job["end"], "title": job["title"],
            "subtitles": list(job["subtitles"]), "fontsize": job["fontsize"],
            "fontname": job.get("fontname", "MS Gothic"),
            "color_hex": cmap.get(job["color"], "&HFFFFFF"),
            "margin_v": job.get("margin_v", 500),
            "loud_zoom": job.get("loud_zoom", False)
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
                        loud_zoom=item.get("loud_zoom", False)
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

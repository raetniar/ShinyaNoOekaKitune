import os
import shutil
import subprocess
import numpy as np
from src.utils import format_srt_time, seconds_to_hms, seconds_to_hms_ms

# 遅延ロード用
VideoFileClip = None
ColorClip = None
CompositeVideoClip = None
imageio_ffmpeg = None

def init_video_libs():
    """動画編集ライブラリ (MoviePy) のインポート"""
    global VideoFileClip, ColorClip, CompositeVideoClip, imageio_ffmpeg
    if VideoFileClip is not None:
        return
    from moviepy.editor import VideoFileClip as _VFC, ColorClip as _CC, CompositeVideoClip as _CVC
    import imageio_ffmpeg as _iff
    VideoFileClip = _VFC
    ColorClip = _CC
    CompositeVideoClip = _CVC
    imageio_ffmpeg = _iff

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

def detect_loud_segments(clip, threshold_ratio=2.2, min_rms=0.03, window_sec=0.1):
    """音声トラックから大声区間を検出して、開始・終了秒数のリストを返す"""
    if clip.audio is None:
        return []
    fps = 22050
    try:
        audio_data = clip.audio.to_soundarray(fps=fps)
    except Exception as e:
        print(f"  ⚠️ 音声分析に失敗しました: {e}")
        return []
    
    if len(audio_data) == 0:
        return []
    
    if len(audio_data.shape) > 1 and audio_data.shape[1] > 1:
        mono = np.mean(audio_data, axis=1)
    else:
        mono = audio_data.flatten()
        
    chunk_size = int(fps * window_sec)
    num_chunks = len(mono) // chunk_size
    
    rms_values = []
    for i in range(num_chunks):
        chunk = mono[i * chunk_size : (i + 1) * chunk_size]
        rms = np.sqrt(np.mean(np.square(chunk)))
        rms_values.append(rms)
        
    if not rms_values:
        return []
        
    avg_rms = np.mean(rms_values)
    max_rms = np.max(rms_values)
    
    threshold = max(avg_rms * threshold_ratio, min_rms)
    threshold = min(threshold, max_rms * 0.6) # 全てズームするのを防ぐ安全弁
    
    loud_blocks = []
    for idx, rms in enumerate(rms_values):
        if rms >= threshold:
            loud_blocks.append(idx * window_sec)
            
    segments = []
    zoom_duration = 1.5
    current_start = None
    current_end = None
    
    for t in loud_blocks:
        if current_start is None:
            current_start = t
            current_end = t + zoom_duration
        elif t <= current_end:
            current_end = t + zoom_duration
        else:
            segments.append((current_start, min(clip.duration, current_end)))
            current_start = t
            current_end = t + zoom_duration
            
    if current_start is not None:
        segments.append((current_start, min(clip.duration, current_end)))
        
    return segments

def apply_zoom_effect(clip, segments, zoom_factor=1.3):
    """大声区間に対して中央をズーム(拡大)するエフェクトを適用"""
    if not segments:
        return clip
    
    print(f"  🔍 大声区間を検出: {len(segments)} 箇所 (自動ズームを適用します)")
    from moviepy.editor import concatenate_videoclips
    from moviepy.video.fx.crop import crop
    
    clips = []
    last_t = 0.0
    w, h = clip.size
    
    for start, end in segments:
        if start > last_t:
            clips.append(clip.subclip(last_t, start))
        
        zoom_sub = clip.subclip(start, end)
        cw = int(w / zoom_factor)
        ch = int(h / zoom_factor)
        x1 = (w - cw) // 2
        y1 = (h - ch) // 2
        
        try:
            cropped = crop(zoom_sub, x1=x1, y1=y1, width=cw, height=ch)
            resized = cropped.resize(newsize=(w, h))
            clips.append(resized)
        except Exception as e:
            print(f"  ⚠️ ズーム処理失敗: {e}")
            clips.append(zoom_sub)
            
        last_t = end
        
    if last_t < clip.duration:
        clips.append(clip.subclip(last_t, clip.duration))
        
    return concatenate_videoclips(clips, method="compose")

def process_single_clip(
    video_path: str,
    start_time: float,
    end_time: float,
    title: str,
    subtitles: list,
    font_size: str,
    font_name: str,
    color_hex: str,
    index: int,
    outdir: str,
    export_srt: bool,
    export_ae_csv: bool,
    no_burn_in: bool,
    margin_v: int = 50,
    loud_zoom: bool = False,
    bold: bool = False,
    italic: bool = False,
    outline_width: int = 2,
    shadow_depth: int = 0,
    outline_color_hex: str = "&H000000",
    alignment: int = 2,
    shadow_alpha: float = 1.0,
    overlay_path: str = "",
    overlay_x: int = 100,
    overlay_y: int = 100,
    overlay_scale: float = 1.0,
    overlay_angle: float = 0.0,
    overlay_opacity: float = 1.0,
    overlay_enabled: bool = False,
    overlay_anchor: str = "重心 (中央)"
) -> str:
    """
    1件の動画切り出し・合成と、付随する字幕書き出し処理を実行する。
    成功した場合は出力ファイルのパス、スキップされた場合は空文字列を返す。
    """
    if VideoFileClip is None:
        init_video_libs()

    buf = 0
    base = os.path.splitext(os.path.basename(video_path))[0]
    out = os.path.join(outdir, f"{base}_{index}_{title}.mp4")
    tmp = os.path.join("temp", f"temp_raw_{index}.mp4")

    print(f"--\n🎬 [{index}] {title}")
    print(f"⏱️  {seconds_to_hms(start_time)} ～ {seconds_to_hms(end_time)}")

    with VideoFileClip(video_path) as v:
        duration = v.duration
        if start_time >= duration:
            print(f"  ⚠️  スキップ: 開始時間 {seconds_to_hms(start_time)} が動画長を超えています。")
            return ""
        
        safe_start = max(0.0, start_time - buf)
        safe_end = min(duration, end_time + buf)
        clip = v.subclip(safe_start, safe_end)
        cr = clip.resize(width=1080)
        
        # 大声ズームエフェクトの適用
        if loud_zoom:
            try:
                loud_segs = detect_loud_segments(cr)
                cr = apply_zoom_effect(cr, loud_segs)
            except Exception as ez:
                print(f"  ⚠️ ズーム解析中にエラーが発生しました: {ez}")
        
        bg = ColorClip(size=(1080, 1920), color=(0, 0, 0)).set_duration(cr.duration)
        CompositeVideoClip([bg, cr.set_position("center")]).write_videofile(
            tmp, codec="libx264", audio_codec="aac", fps=30, threads=4, logger=None
        )

    print("  -> 縦型レターボックス動画生成完了。")
    out_base = os.path.splitext(out)[0]
    final_srt_path = f"{out_base}.srt"
    final_csv_path = f"{out_base}_Ae.csv"

    if subtitles:
        srt = os.path.join("temp", f"temp_sub_{index}.srt")
        with open(srt, "w", encoding="utf-8") as f:
            for si, sub in enumerate(subtitles):
                sub_start_in_clip = (start_time + sub['start']) - safe_start
                sub_end_in_clip = (start_time + sub['end']) - safe_start
                clean_text = sub['text'].replace('\r\n', '\n')
                f.write(f"{si + 1}\n{format_srt_time(sub_start_in_clip)} --> {format_srt_time(sub_end_in_clip)}\n{clean_text}\n\n")

        if export_srt:
            shutil.copy(srt, final_srt_path)
            print(f"  📁 字幕SRTを出力しました: {final_srt_path}")

        if export_ae_csv:
            with open(final_csv_path, "w", encoding="utf-8-sig") as f:
                f.write("開始時間,終了時間,字幕テキスト\n")
                for sub in subtitles:
                    sub_start_in_clip = (start_time + sub['start']) - safe_start
                    sub_end_in_clip = (start_time + sub['end']) - safe_start
                    t_start = seconds_to_hms_ms(sub_start_in_clip)
                    t_end = seconds_to_hms_ms(sub_end_in_clip)
                    clean_text = sub['text'].replace('\r\n', '\n').replace('"', '""')
                    f.write(f'"{t_start}","{t_end}","{clean_text}"\n')
            print(f"  📁 Ae用CSVを出力しました: {final_csv_path}")

        if no_burn_in:
            temp_overlay_path = ""
            has_overlay = False
            ox = overlay_x
            oy = overlay_y
            if overlay_enabled and overlay_path and os.path.exists(overlay_path):
                processed_img = preprocess_overlay_image(overlay_path, overlay_scale, overlay_angle, overlay_opacity)
                if processed_img:
                    w, h = processed_img.width, processed_img.height
                    if overlay_anchor == "重心 (中央)":
                        ox = overlay_x - w // 2
                        oy = overlay_y - h // 2
                    elif overlay_anchor == "右上":
                        ox = overlay_x - w
                        oy = overlay_y
                    elif overlay_anchor == "左下":
                        ox = overlay_x
                        oy = overlay_y - h
                    elif overlay_anchor == "右下":
                        ox = overlay_x - w
                        oy = overlay_y - h
                    temp_overlay_path = os.path.join(os.path.dirname(out), f"temp_overlay_no_sub_{index}.png")
                    processed_img.save(temp_overlay_path, "PNG")
                    has_overlay = True

            if has_overlay:
                si_info = None
                if os.name == 'nt':
                    si_info = subprocess.STARTUPINFO()
                    si_info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
                r = subprocess.run(
                    [
                        ffmpeg_exe, "-y",
                        "-i", tmp,
                        "-i", temp_overlay_path,
                        "-filter_complex", f"[0:v][1:v]overlay={ox}:{oy}",
                        "-c:a", "copy", out
                    ],
                    startupinfo=si_info, capture_output=True, text=True
                )
                for p in [tmp, temp_overlay_path]:
                    if p and os.path.exists(p):
                        try: os.remove(p)
                        except Exception: pass
                if os.path.exists(srt):
                    try: os.remove(srt)
                    except Exception: pass
                if r.returncode != 0:
                    raise RuntimeError(f"ffmpeg overlayエラー: {r.stderr}")
            else:
                if os.path.exists(out):
                    os.remove(out)
                shutil.move(tmp, out)
                if os.path.exists(srt):
                    os.remove(srt)
                print("  -> 字幕の焼き付けをスキップしました (生動画)。")
        else:
            # ffmpeg subtitlesフィルター用のパスエスケープ処理 (Windows対策)
            srt_ffmpeg = srt.replace("\\", "/")
            if ":" in srt_ffmpeg:
                srt_ffmpeg = srt_ffmpeg.replace(":", "\\:")
            srt_ffmpeg = srt_ffmpeg.replace("'", "'\\\\''")

            ass_bold = -1 if bold else 0
            ass_italic = -1 if italic else 0
            alpha_val = int((1.0 - max(0.0, min(1.0, shadow_alpha))) * 255)
            bbggrr = outline_color_hex.replace("&H", "")
            back_color_hex = f"&H{alpha_val:02X}{bbggrr}"
            style = f"Fontname={font_name},Fontsize={font_size},PrimaryColour={color_hex},OutlineColour={outline_color_hex},BackColour={back_color_hex},BorderStyle=1,Outline={outline_width},Shadow={shadow_depth},Alignment={alignment},MarginV={margin_v},PlayResX=1080,PlayResY=1920,Bold={ass_bold},Italic={ass_italic}"
            
            temp_overlay_path = ""
            has_overlay = False
            ox = overlay_x
            oy = overlay_y
            if overlay_enabled and overlay_path and os.path.exists(overlay_path):
                processed_img = preprocess_overlay_image(overlay_path, overlay_scale, overlay_angle, overlay_opacity)
                if processed_img:
                    w, h = processed_img.width, processed_img.height
                    if overlay_anchor == "重心 (中央)":
                        ox = overlay_x - w // 2
                        oy = overlay_y - h // 2
                    elif overlay_anchor == "右上":
                        ox = overlay_x - w
                        oy = overlay_y
                    elif overlay_anchor == "左下":
                        ox = overlay_x
                        oy = overlay_y - h
                    elif overlay_anchor == "右下":
                        ox = overlay_x - w
                        oy = overlay_y - h
                    temp_overlay_path = os.path.join(os.path.dirname(out), f"temp_overlay_{index}.png")
                    processed_img.save(temp_overlay_path, "PNG")
                    has_overlay = True

            si_info = None
            if os.name == 'nt':
                si_info = subprocess.STARTUPINFO()
                si_info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
            
            if has_overlay:
                filter_complex = f"[0:v]subtitles='{srt_ffmpeg}':force_style='{style}'[v1];[v1][1:v]overlay={ox}:{oy}"
                r = subprocess.run(
                    [
                        ffmpeg_exe, "-y",
                        "-i", tmp,
                        "-i", temp_overlay_path,
                        "-filter_complex", filter_complex,
                        "-c:a", "copy", out
                    ],
                    startupinfo=si_info, capture_output=True, text=True
                )
            else:
                r = subprocess.run(
                    [ffmpeg_exe, "-y", "-i", tmp, "-vf", f"subtitles='{srt_ffmpeg}':force_style='{style}'", "-c:a", "copy", out],
                    startupinfo=si_info, capture_output=True, text=True
                )
                
            for p in [srt, tmp, temp_overlay_path]:
                if p and os.path.exists(p):
                    try: os.remove(p)
                    except Exception: pass
            if r.returncode != 0:
                raise RuntimeError(f"ffmpegエラー: {r.stderr}")
    else:
        if os.path.exists(out):
            os.remove(out)
        shutil.move(tmp, out)

    print(f"  ✅ 完了: {out}")
    return out

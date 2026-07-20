import os
import sys
import wave
import numpy as np

# グローバル状態管理用変数
WHISPER_AVAILABLE = False
WHISPER_LOAD_ERROR = ""
whisper = None

def init_whisper():
    """AI音声認識エンジン (Whisper) のインポートを試みる"""
    global whisper, WHISPER_AVAILABLE, WHISPER_LOAD_ERROR
    if WHISPER_AVAILABLE and whisper is not None:
        return
    try:
        import whisper as _whisper
        whisper = _whisper
        WHISPER_AVAILABLE = True
        WHISPER_LOAD_ERROR = ""
    except Exception as e:
        import traceback
        WHISPER_LOAD_ERROR = f"{str(e)}\n{traceback.format_exc()}"
        WHISPER_AVAILABLE = False

def get_whisper_assets_path():
    """PyInstaller frozen 環境等に応じた Whisper のアセットパスを取得"""
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, 'whisper', 'assets')
    else:
        try:
            import whisper as _whisper
            return os.path.join(os.path.dirname(_whisper.__file__), 'assets')
        except ImportError:
            return ""

def patch_whisper_assets():
    """Whisperの音声アセットパスを frozen 環境向けにパッチ"""
    global WHISPER_AVAILABLE, whisper
    if not WHISPER_AVAILABLE or whisper is None:
        return
    try:
        import whisper.audio as _wa
        assets_path = get_whisper_assets_path()
        if assets_path and os.path.exists(assets_path):
            if hasattr(_wa, '_ASSETS_PATH'):
                _wa._ASSETS_PATH = assets_path
            print(f"Apply Whisper assets path patch: {_wa._ASSETS_PATH}")
    except Exception as e:
        print(f"Whisperアセットパッチ失敗: {e}")

def load_wav_as_numpy(wav_path: str) -> np.ndarray:
    """WAVファイルをNumPyのfloat32配列へ読み込む"""
    with wave.open(wav_path, 'rb') as wf:
        n_channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        n_frames = wf.getnframes()
        raw_data = wf.readframes(n_frames)

    if sampwidth == 2:
        audio = np.frombuffer(raw_data, dtype=np.int16).astype(np.float32) / 32768.0
    elif sampwidth == 4:
        audio = np.frombuffer(raw_data, dtype=np.int32).astype(np.float32) / 2147483648.0
    else:
        audio = np.frombuffer(raw_data, dtype=np.uint8).astype(np.float32) / 128.0 - 1.0

    if n_channels > 1:
        audio = audio.reshape(-1, n_channels).mean(axis=1)

    return audio

def apply_replace_dict(text: str, replace_dict: dict) -> str:
    """指定された置換辞書 (誤り=正解) に従って文字列を置換する"""
    if not replace_dict:
        return text
    for bad_word, good_word in replace_dict.items():
        if bad_word:
            text = text.replace(bad_word, good_word)
    return text

def transcribe_audio_segment(model, audio_path: str, initial_prompt: str = "初狐羽鹿, Vtuber, 逆転裁判, 切り抜き", replace_dict: dict = None) -> list:
    """指定されたWAVの音声ファイルをモデルに入力して文字起こしし、セグメントのリストを返す"""
    audio_np = load_wav_as_numpy(audio_path)
    result = model.transcribe(audio_np, language="ja", fp16=False, initial_prompt=initial_prompt)
    
    segments = [
        {
            "start": float(s["start"]),
            "end": float(s["end"]),
            "text": apply_replace_dict(s["text"].strip(), replace_dict)
        }
        for s in result["segments"]
    ]
    return segments

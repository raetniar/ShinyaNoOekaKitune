import re

def format_srt_time(s: float) -> str:
    """秒数をSRT字幕のタイムスタンプ形式 (HH:MM:SS,mmm) に変換"""
    h, s = divmod(s, 3600)
    m, s = divmod(s, 60)
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int((s - int(s)) * 1000):03d}"

def seconds_to_hms_ms(s: float) -> str:
    """秒数をミリ秒精度の形式 (HH:MM:SS.mmm) に変換"""
    h, s = divmod(s, 3600)
    m, s = divmod(s, 60)
    return f"{int(h):02d}:{int(m):02d}:{s:06.3f}"

def seconds_to_hms(s: float) -> str:
    """秒数を標準形式 (HH:MM:SS) に変換"""
    h, s = divmod(s, 3600)
    m, s = divmod(s, 60)
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d}"

def seconds_to_minsec(s: float) -> str:
    """秒数を分秒形式 (MM:SS) に変換。マイナス値にも対応"""
    m, s2 = divmod(abs(s), 60)
    sign = "-" if s < 0 else ""
    return f"{sign}{int(m):02d}:{int(s2):02d}"

def minsec_to_seconds(t: str) -> float:
    """分秒形式 (MM:SS または HH:MM:SS) または単一秒数を秒数 (float) に変換"""
    t = t.strip()
    if not t:
        return 0.0
    if re.match(r'^-?\d+(\.\d+)?$', t):
        return float(t)
    parts = t.split(':')
    try:
        if len(parts) == 2:
            sign = -1 if parts[0].startswith('-') else 1
            m = abs(int(parts[0]))
            s = float(parts[1])
            return sign * (m * 60 + s)
        elif len(parts) == 3:
            sign = -1 if parts[0].startswith('-') else 1
            h = abs(int(parts[0]))
            m = int(parts[1])
            s = float(parts[2])
            return sign * (h * 3600 + m * 60 + s)
    except ValueError:
        pass
    return 0.0

def time_to_seconds(t: str) -> float:
    """時間文字列を秒数に変換"""
    t = t.strip()
    if not t:
        return 0.0
    if re.match(r'^\d+(\.\d+)?$', t):
        return float(t)
    parts = t.split(':')
    try:
        if len(parts) == 3:
            return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
        if len(parts) == 2:
            return float(parts[0]) * 60 + float(parts[1])
    except ValueError:
        pass
    return 0.0

def clean_filename(s: str) -> str:
    """Windowsのファイル名として使えない文字を除去"""
    return re.sub(r'[\\/:*?"<>|]', '', s).strip()

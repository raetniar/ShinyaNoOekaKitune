import os
import re
import shutil

source_dir = r"g:\マイドライブ\【04_素材・ツールライブラリ】\自作ツール\OBS_YouTubeManager\GIT\YouTubeManager"
target_dir = r"g:\マイドライブ\【04_素材・ツールライブラリ】\GIT_HTML\tools\YouTubeManager"

source_path = os.path.join(source_dir, "YouTubeManagerDock.html")
target_path = os.path.join(target_dir, "YouTubeManager.html")

print("1. Syncing JS and CSS assets for YouTubeManager...")
os.makedirs(target_dir, exist_ok=True)

assets_to_copy = ["youtube_manager.css", "youtube_manager_locales.js", "youtube_manager_version.js", "creators.json"]
for asset in assets_to_copy:
    src_asset = os.path.join(source_dir, asset)
    dst_asset = os.path.join(target_dir, asset)
    if os.path.exists(src_asset):
        shutil.copy2(src_asset, dst_asset)

src_js = os.path.join(source_dir, "js")
dst_js = os.path.join(target_dir, "js")
if os.path.exists(src_js):
    os.makedirs(dst_js, exist_ok=True)
    for item in os.listdir(src_js):
        s = os.path.join(src_js, item)
        d = os.path.join(dst_js, item)
        if os.path.isfile(s):
            shutil.copy2(s, d)

print("2. Reading YouTubeManagerDock.html...")
with open(source_path, "r", encoding="utf-8") as f:
    source_html = f.read()

body_match = re.search(r"<body[^>]*>(.*?)</body>", source_html, re.DOTALL | re.IGNORECASE)
if not body_match:
    raise ValueError("Could not find <body> tag in source file")

source_body_content = body_match.group(1).strip()

head_content = """<!DOCTYPE html>
<html lang="ja">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>YouTubeマネージャー (YouTubeManager)</title>
    
    <!-- Google Fonts: Outfit + Noto Sans JP -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700;900&family=Outfit:wght@300;400;600;800&display=swap" rel="stylesheet">

    <!-- FontAwesome icons -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">

    <script>
        // Immediate API Mock Setup for DEMO mode
        (function() {
            window.youtubeApiRequest = async function(endpoint, method = 'GET', body = null) {
                if (typeof showToast === 'function') {
                    showToast("【DEMO動作】YouTube Data API通信（※実際の枠作成・更新は行われません）");
                }
                return { id: `demo-broadcast-${Date.now()}`, items: [] };
            };
        })();
    </script>

    <link rel="stylesheet" href="youtube_manager.css">

    <style>
        .tool-header-bar {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            flex-wrap: nowrap;
            gap: 16px;
            padding: 12px 16px;
            background-color: var(--bg-card, #181818);
            border-bottom: 1px solid var(--border-color, #383838);
            position: relative;
            z-index: 2000;
            margin: -12px -14px 14px -14px !important;
        }

        body.light-mode .tool-header-bar, body.light-theme .tool-header-bar {
            background-color: #ffffff !important;
            border-bottom-color: #e5e5e5 !important;
        }

        .tool-title-area {
            display: flex;
            flex-direction: column;
            align-items: flex-start;
            gap: 4px;
            flex: 1;
            min-width: 0;
        }

        .tool-name-heading {
            font-size: 1.1rem;
            font-weight: 800;
            letter-spacing: 0.03em;
            color: var(--text-main, #f1f1f1);
            margin: 0;
            line-height: 1.2;
        }

        body.light-mode .tool-name-heading, body.light-theme .tool-name-heading {
            color: #0f0f0f !important;
        }

        .tool-description-sub {
            font-size: 0.78rem;
            color: var(--text-muted, #aaaaaa);
            font-weight: 300;
            margin: 0;
            line-height: 1.3;
        }

        .tool-header-actions {
            display: flex;
            align-items: center;
            gap: 8px;
            flex-shrink: 0;
            white-space: nowrap;
        }

        .header-theme-toggle, .header-booth-btn, .header-github-btn, .back-home-btn {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            font-size: 0.8rem;
            font-weight: 700;
            text-decoration: none;
            padding: 5px 10px;
            border-radius: 6px;
            transition: all 0.2s ease;
            cursor: pointer;
        }

        body.light-mode .header-theme-toggle, body.light-theme .header-theme-toggle {
            color: #111111;
            border-color: #d1d5db;
            background-color: #f3f4f6;
        }

        body.dark-mode .header-booth-btn, body:not(.light-mode):not(.light-theme) .header-booth-btn {
            color: #ffffff;
            background-color: #111111;
            border: 1px solid #ffffff;
        }
        body.dark-mode .header-github-btn, body:not(.light-mode):not(.light-theme) .header-github-btn {
            color: #f0f6fc;
            background-color: #21262d;
            border: 1px solid #30363d;
        }
        body.dark-mode .back-home-btn, body:not(.light-mode):not(.light-theme) .back-home-btn {
            color: #efeff1;
            background-color: #18181b;
            border: 1px solid #3a3a3d;
        }
    </style>
</head>

<body>

    <!-- 共通Webツールヘッダー -->
    <header class="tool-header-bar">
        <div class="tool-title-area">
            <div class="tool-title-row">
                <h1 class="tool-name-heading"><i class="fa-brands fa-youtube" style="color:var(--yt-red);"></i> YouTubeマネージャー (YouTubeManager)</h1>
            </div>
            <span class="tool-description-sub">OBSカスタムドック対応・YouTube Live配信枠の予約生成・タイトル・概要欄・プリセット一括管理</span>
        </div>
        <div class="tool-header-actions">
            <button type="button" class="header-theme-toggle" id="top-header-theme-btn" onclick="toggleTheme()" aria-label="テーマ切替">
                <i class="fa-solid fa-moon"></i> <span class="btn-text">ダーク</span>
            </button>
            <a href="https://toumei2suisai.booth.pm" target="_blank" rel="noopener noreferrer" class="header-booth-btn">
                <i class="fa-solid fa-shop"></i> <span class="btn-text">booth</span>
            </a>
            <a href="https://github.com/MagnestGames" target="_blank" rel="noopener noreferrer" class="header-github-btn">
                <i class="fa-brands fa-github"></i> <span class="btn-text">GitHub</span>
            </a>
            <a href="../../index.html" class="back-home-btn">
                <i class="fa-solid fa-arrow-left"></i> <span class="btn-text">TOPに戻る</span>
            </a>
        </div>
    </header>
"""

footer_content = """
    <!-- 共通Webツールフッター -->
    <script src="../footer.js"></script>
</body>

</html>
"""

full_html = head_content + source_body_content + footer_content

with open(target_path, "w", encoding="utf-8") as f:
    f.write(full_html)

print("Successfully built YouTubeManager.html for Web Demo Mode!")

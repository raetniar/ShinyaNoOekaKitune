import os
import re
import shutil

source_dir = r"G:\マイドライブ\【04_素材・ツールライブラリ】\自作ツール\OBS_TwitchManager\GIT\TwitchManager"
target_dir = r"g:\マイドライブ\【04_素材・ツールライブラリ】\GIT_HTML\tools\TwitchManager"

source_path = os.path.join(source_dir, "TwitchManagerDock.html")
target_path = os.path.join(target_dir, "TwitchManager.html")

print("1. Syncing JS and CSS assets from TwitchManager repository...")
assets_to_copy = ["twitch_manager.css", "twitch_manager_locales.js", "twitch_manager_version.js", "creators.json"]
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

print("2. Reading TwitchManagerDock.html...")
with open(source_path, "r", encoding="utf-8") as f:
    source_html = f.read()

# Extract inner body content of source HTML (between <body> and </body>)
body_match = re.search(r"<body[^>]*>(.*?)</body>", source_html, re.DOTALL | re.IGNORECASE)
if not body_match:
    raise ValueError("Could not find <body> tag in source file")

source_body_content = body_match.group(1).strip()

# Replace Twitch Auth section inside body content for DEMO mode restriction
demo_auth_section = """<div
                style="background:var(--bg-panel); padding:20px; border-radius:12px; margin-bottom:20px; border-left:4px solid var(--twitch-purple);">
                <div class="category-subtitle" id="ui-settings-auth-title" style="margin-bottom:8px;" data-i18n="settingsUi.authTitle">Twitch認証</div>
                <p class="settings-help" id="ui-settings-auth-help" data-i18n="settingsUi.authHelp">Twitch Token Generatorでアクセストークンを取得し、ここに貼り付けて保存します。Client IDと連携先チャンネルは自動で確認します。詳しい手順がわからない場合は、右上のヘルプから画像付きガイドを確認してください。</p>
                <input type="hidden" id="user_id" value="demo_user">
                <input type="hidden" id="user_login" value="demo_user">
                <input type="hidden" id="oauth_redirect_uri" value="http://localhost">
                <input type="hidden" id="client_id" value="demo_client_id">
                <div class="auth-status is-ready" id="ui-settings-auth-status" style="margin-bottom: 12px; background: rgba(0, 200, 117, 0.15); border: 1px solid #00c875; color: #00c875; padding: 10px; border-radius: 8px; font-weight: bold;">連携済み: demo_user</div>
                <span class="field-label" id="ui-settings-access-token" data-i18n="settingsUi.accessToken">アクセストークン</span>
                <div style="position: relative; display: flex; align-items: center; margin-bottom: 15px;">
                    <input type="password" id="token" value="********************************" readonly style="margin-bottom: 0; padding-right: 40px; cursor: pointer; user-select: none;" onclick="showDemoTokenNotice(event)" onfocus="showDemoTokenNotice(event)" onkeydown="showDemoTokenNotice(event)" onpaste="showDemoTokenNotice(event)" onmousedown="showDemoTokenNotice(event)">
                    <button type="button" onclick="showDemoTokenNotice(event)" data-i18n-aria="settingsUi.toggleTokenVisibility" aria-label="アクセストークンの表示を切り替え"
                        style="position: absolute; right: 5px; background: none; border: none; color: var(--text-muted); cursor: pointer; font-size: 16px;">👁</button>
                </div>
                <div style="display:flex; gap:8px; flex-wrap:wrap; margin-top:10px;">
                    <button type="button" class="btn-outline" id="ui-settings-auth-btn" onclick="showDemoTokenNotice(event)" data-i18n="settingsUi.openAuth">Twitch Token GeneratorのURLをコピー</button>
                    <button type="button" class="btn-outline btn-revoke" id="ui-settings-revoke-auth-btn" onclick="showDemoTokenNotice(event)" data-i18n="settingsUi.revokeAuth">Twitch認証を解除</button>
                </div>
            </div>"""

# Regex replacement for Twitch Auth section in settingModal
source_body_content = re.sub(
    r'<div\s+style="background:var\(--bg-panel\);\s*padding:20px;.*?id="ui-settings-revoke-auth-btn".*?</div>\s*</div>',
    demo_auth_section,
    source_body_content,
    flags=re.DOTALL
)

head_content = """<!DOCTYPE html>
<html lang="ja">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Twitchマネージャー (TwitchManager)</title>
    
    <!-- Google Fonts: Outfit (UI用) + Noto Sans JP -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700;900&family=Outfit:wght@300;400;600;800&display=swap" rel="stylesheet">

    <!-- FontAwesome icons -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">

    <script>
        const twitchManagerAudioSourceMode = new URLSearchParams(location.search).get('audio-source') === '1';
        if (twitchManagerAudioSourceMode) document.documentElement.classList.add('audio-source-mode');
    </script>
    <script>
        // Immediate API Mock Setup in <head> to prevent 401 errors on initial script load
        (function() {
            const handleDemoRequest = async (endpoint, method = 'GET', body = null) => {
                const upperMethod = String(method || 'GET').toUpperCase();
                const path = String(endpoint || '').split('?')[0];

                const notifyDemoAction = (msg) => {
                    if (typeof showToast === 'function') {
                        showToast(`【DEMO動作】${msg}（※実際のTwitch操作は行われません）`);
                    }
                    if (typeof raidSoLog === 'function') {
                        raidSoLog(`[DEMO] ${msg}`, 'info');
                    }
                };

                if (path.includes('/channel_points/custom_rewards')) {
                    if (upperMethod === 'GET') {
                        return { data: (typeof cpState !== 'undefined' && cpState.rewards) ? cpState.rewards : [] };
                    }
                    if (upperMethod === 'POST' || upperMethod === 'PATCH' || upperMethod === 'DELETE') {
                        notifyDemoAction('チャンネルポイント操作');
                        return { data: [] };
                    }
                }

                if (path.includes('/streams') || path.includes('/users') || path.includes('/channels') || path.includes('/validate')) {
                    return { data: [{ id: '501391907', user_id: '501391907', login: 'demo_user', display_name: 'demo_user', title: '【DEMO】配信タイトルプレビュー', game_name: 'Just Chatting', type: 'live' }], client_id: 'demo_client_id', login: 'demo_user', user_id: '501391907' };
                }

                if (path.includes('/chat') || path.includes('/predictions') || path.includes('/polls') || path.includes('/clips') || path.includes('/subscriptions') || path.includes('/vips') || path.includes('/eventsub')) {
                    return { data: [] };
                }

                return { data: [] };
            };

            window.apiRequest = async function(endpoint, method = 'GET', body = null, silent = false) {
                return await handleDemoRequest(endpoint, method, body);
            };

            window.raidSoHelix = async function(endpoint, options = {}) {
                return await handleDemoRequest(endpoint, options ? options.method || 'GET' : 'GET', options ? options.body || null : null);
            };
        })();
    </script>

    <link rel="stylesheet" href="twitch_manager.css">

    <style>
        html.audio-source-mode, html.audio-source-mode body { margin: 0; min-height: 100%; background: transparent !important; }
        html.audio-source-mode body { visibility: hidden; }

        /* ==========================================================================
           Web Tool Common Header Integration & Spacing Fixes
           ========================================================================== */
        .tool-header-bar {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            flex-wrap: nowrap;
            gap: 16px;
            padding: 12px 16px;
            background-color: var(--bg-card, #1b1b1f);
            border-bottom: 1px solid var(--border-color, #3f3f46);
            position: relative;
            z-index: 2000;
            margin: -15px -15px 16px -15px !important;
        }

        body.light-mode .tool-header-bar {
            background-color: #ffffff;
            border-bottom-color: #e5e7eb;
        }

        .tool-title-area {
            display: flex;
            flex-direction: column;
            align-items: flex-start;
            gap: 4px;
            flex: 1;
            min-width: 0;
        }

        .tool-title-row {
            display: flex;
            align-items: center;
            gap: 8px;
            flex-wrap: wrap;
        }

        .tool-name-heading {
            font-size: 1.1rem;
            font-weight: 800;
            letter-spacing: 0.03em;
            color: var(--text-main, #efeff1);
            margin: 0;
            line-height: 1.2;
        }

        body.light-mode .tool-name-heading {
            color: #111111;
        }

        .tool-description-sub {
            font-size: 0.78rem;
            color: var(--text-muted, #adadb8);
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

        .header-theme-toggle {
            background: none;
            border: 1px solid var(--border-color, #3f3f46);
            color: var(--text-main, #efeff1);
            padding: 5px 10px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.8rem;
            font-weight: 600;
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
            gap: 6px;
        }

        body.light-mode .header-theme-toggle {
            color: #111111;
            border-color: #d1d5db;
        }

        .header-theme-toggle:hover {
            background-color: rgba(145, 70, 255, 0.15);
        }

        .header-booth-btn, .header-github-btn, .back-home-btn {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            font-size: 0.8rem;
            font-weight: 700;
            text-decoration: none;
            padding: 5px 10px;
            border-radius: 4px;
            transition: all 0.2s ease;
            cursor: pointer;
            white-space: nowrap;
        }

        /* Hide inner content theme toggle button as requested */
        #theme-btn {
            display: none !important;
        }

        /* Full Light Mode / Light Theme styling support */
        body.light-mode, body.light-theme, html.light-mode, html.light-theme {
            background-color: #f4f4f7 !important;
            color: #1f1f23 !important;
        }
        body.light-mode .tool-header-bar, body.light-theme .tool-header-bar {
            background-color: #ffffff !important;
            border-bottom-color: #e5e7eb !important;
        }
        body.light-mode .tool-name-heading, body.light-theme .tool-name-heading {
            color: #111111 !important;
        }
        body.light-mode .tool-description-sub, body.light-theme .tool-description-sub {
            color: #6b7280 !important;
        }
        body.light-mode .header-theme-toggle, body.light-theme .header-theme-toggle {
            color: #111111 !important;
            border-color: #d1d5db !important;
            background-color: #f3f4f6 !important;
        }
        body.light-mode .header-theme-toggle:hover, body.light-theme .header-theme-toggle:hover {
            background-color: #e5e7eb !important;
        }

        /* Light Mode BOOTH / GitHub / Back */
        body.light-mode .header-booth-btn, body.light-theme .header-booth-btn {
            color: #111111;
            background-color: #ffffff;
            border: 1px solid #111111;
        }
        body.light-mode .header-booth-btn:hover, body.light-theme .header-booth-btn:hover {
            color: #ffffff;
            background-color: #111111;
        }
        body.light-mode .header-github-btn, body.light-theme .header-github-btn {
            color: #24292e;
            background-color: #f6f8fa;
            border: 1px solid #d1d5db;
        }
        body.light-mode .header-github-btn:hover, body.light-theme .header-github-btn:hover {
            color: #ffffff;
            background-color: #24292e;
        }
        body.light-mode .back-home-btn, body.light-theme .back-home-btn {
            color: #111111;
            background-color: #f8f9fa;
            border: 1px solid #d1d5db;
        }
        body.light-mode .back-home-btn:hover, body.light-theme .back-home-btn:hover {
            color: #ffffff;
            background-color: #111111;
        }

        /* Dark Mode BOOTH / GitHub / Back */
        body.dark-mode .header-booth-btn, body:not(.light-mode):not(.light-theme) .header-booth-btn {
            color: #ffffff;
            background-color: #111111;
            border: 1px solid #ffffff;
        }
        body.dark-mode .header-booth-btn:hover, body:not(.light-mode):not(.light-theme) .header-booth-btn:hover {
            color: #111111;
            background-color: #ffffff;
        }
        body.dark-mode .header-github-btn, body:not(.light-mode):not(.light-theme) .header-github-btn {
            color: #f0f6fc;
            background-color: #21262d;
            border: 1px solid #30363d;
        }
        body.dark-mode .header-github-btn:hover, body:not(.light-mode):not(.light-theme) .header-github-btn:hover {
            color: #111111;
            background-color: #ffffff;
        }
        body.dark-mode .back-home-btn, body:not(.light-mode):not(.light-theme) .back-home-btn {
            color: #efeff1;
            background-color: #18181b;
            border: 1px solid #3a3a3d;
        }
        body.dark-mode .back-home-btn:hover, body:not(.light-mode):not(.light-theme) .back-home-btn:hover {
            color: #111111;
            background-color: #ffffff;
        }

        /* Override twitch_manager.css margin-top: -15px for sticky-top-wrapper */
        body .sticky-top-wrapper {
            position: relative !important;
            top: auto !important;
            margin-top: 14px !important;
            margin-bottom: 14px !important;
            margin-left: -15px !important;
            margin-right: -15px !important;
            padding: 4px 15px 0 15px !important;
        }

        /* Natural content flow for footer bar instead of fixed/sticky positioning (remove beta-zuke) */
        html body .tab-content.active .sticky-footer-wrapper,
        html body .sticky-footer-wrapper {
            position: relative !important;
            bottom: auto !important;
            left: auto !important;
            right: auto !important;
            width: 100% !important;
            margin-top: 20px !important;
            margin-bottom: 20px !important;
            border-radius: 8px !important;
            border: 1px solid var(--border-color) !important;
            box-shadow: none !important;
            z-index: 10 !important;
        }

        /* Clean bottom padding for tab contents */
        html body .tab-content.active,
        html body .tab-content {
            padding-bottom: calc(var(--common-footer-height, 38px) + 30px) !important;
        }

        @media (max-width: 600px) {
            .tool-header-bar .btn-text {
                display: none;
            }
            .tool-description-sub {
                display: none;
            }
        }
    </style>
</head>

<body>

    <!-- 共通Webツールヘッダー -->
    <header class="tool-header-bar">
        <div class="tool-title-area">
            <div class="tool-title-row">
                <h1 class="tool-name-heading">Twitchマネージャー (TwitchManager)</h1>
            </div>
            <span class="tool-description-sub">OBSカスタムドック対応・Twitch配信タイトル・カテゴリ・レイド・サポーター・チャット一括管理</span>
        </div>
        <div class="tool-header-actions">
            <button type="button" class="header-theme-toggle" id="top-header-theme-btn" onclick="toggleTheme()" aria-label="テーマ切替">
                <i class="fa-solid fa-moon"></i> <span class="btn-text">ダーク</span>
            </button>
            <a href="https://toumei2suisai.booth.pm/items/8654630" target="_blank" rel="noopener noreferrer" class="header-booth-btn">
                <i class="fa-solid fa-shop"></i> <span class="btn-text">booth</span>
            </a>
            <a href="https://github.com/MagnestGames/TwitchManager/releases" target="_blank" rel="noopener noreferrer" class="header-github-btn">
                <i class="fa-brands fa-github"></i> <span class="btn-text">GitHub</span>
            </a>
            <a href="../../index.html" class="back-home-btn">
                <i class="fa-solid fa-arrow-left"></i> <span class="btn-text">TOPに戻る</span>
            </a>
        </div>
    </header>

    <!-- ==========================================================================
         [SWAPPABLE CONTENT AREA] TwitchManager Body Content
         Source: OBS_TwitchManager/GIT/TwitchManager/TwitchManagerDock.html
         Future Updates: Replace the section between [TWITCHMANAGER_CONTENT_START]
                         and [TWITCHMANAGER_CONTENT_END] with the inner <body> of TwitchManagerDock.html
         ========================================================================== -->
    <!-- [TWITCHMANAGER_CONTENT_START] -->
"""

footer_content = """
    <!-- [TWITCHMANAGER_CONTENT_END] -->
    <!-- ========================================================================== -->

    <script>
        function showDemoTokenNotice(event) {
            if (event) {
                event.preventDefault();
                event.stopPropagation();
            }
            const overlay = document.getElementById('custom-dialog-overlay');
            const titleEl = document.getElementById('cd-title');
            const msgEl = document.getElementById('cd-message');
            const inputEl = document.getElementById('cd-input');
            const btnCancel = document.getElementById('cd-btn-cancel');
            const btnNeutral = document.getElementById('cd-btn-neutral');
            const btnOk = document.getElementById('cd-btn-ok');

            if (!overlay) {
                alert("DEMO版にアクセストークンの入力はできません");
                return;
            }

            titleEl.innerText = "🔒 DEMO版の制限";
            msgEl.innerHTML = `
                <div style="text-align: center; padding: 10px 0;">
                    <div style="font-size: 15px; font-weight: bold; color: var(--command-accent, #9146FF); margin-bottom: 12px;">
                        DEMO版にアクセストークンの入力はできません
                    </div>
                    <div style="font-size: 12px; color: var(--text-muted); margin-bottom: 20px; line-height: 1.6;">
                        Web DEMO版ではセキュリティ保護および体験用のため、アクセストークンの連携・入力機能は制限されています。<br>
                        全機能・Twitch連携をご利用になる場合は、BOOTHまたはGitHubより本体（無料）をダウンロードしてください。
                    </div>
                    <div style="display: flex; justify-content: center; gap: 10px; flex-wrap: wrap; margin-top: 10px;">
                        <a href="https://toumei2suisai.booth.pm/items/8654630" target="_blank" rel="noopener noreferrer" 
                           class="btn-primary" style="display: inline-flex; align-items: center; gap: 8px; text-decoration: none; padding: 10px 18px; font-weight: bold; border-radius: 6px; font-size: 12.5px; background: #9146FF; color: #ffffff;">
                            <i class="fa-solid fa-shop"></i> BOOTHでダウンロード ↗
                        </a>
                        <a href="https://github.com/MagnestGames/TwitchManager/releases" target="_blank" rel="noopener noreferrer" 
                           class="btn-secondary" style="display: inline-flex; align-items: center; gap: 8px; text-decoration: none; padding: 10px 18px; font-weight: bold; border-radius: 6px; font-size: 12.5px; background: #21262d; color: #f0f6fc; border: 1px solid #30363d;">
                            <i class="fa-brands fa-github"></i> GitHub Releases ↗
                        </a>
                    </div>
                </div>
            `;
            inputEl.style.display = 'none';
            btnCancel.style.display = 'none';
            btnNeutral.style.display = 'none';
            btnOk.innerText = "閉じる";
            btnOk.onclick = () => {
                overlay.classList.remove('show');
                btnOk.onclick = null;
            };
            overlay.classList.add('show');
        }

        window.openOfficialAuth = function(e) { showDemoTokenNotice(e); };
        window.revokeTwitchAuth = function(e) { showDemoTokenNotice(e); };
        window.togglePasswordVisibility = function(e) { showDemoTokenNotice(e); };

        window.applyTheme = function(theme) {
            const isLight = theme === 'light';
            document.body.classList.toggle('light-theme', isLight);
            document.body.classList.toggle('light-mode', isLight);
            document.documentElement.classList.toggle('light-theme', isLight);
            document.documentElement.classList.toggle('light-mode', isLight);
            const topBtn = document.getElementById('top-header-theme-btn');
            if (topBtn) {
                topBtn.innerHTML = isLight ? 
                    `<i class="fa-solid fa-sun" style="color:#eab308;"></i> <span class="btn-text">ライト</span>` : 
                    `<i class="fa-solid fa-moon"></i> <span class="btn-text">ダーク</span>`;
            }
            try { localStorage.setItem('stream_theme', theme); } catch(e){}
        };

        window.toggleTheme = function() {
            const isLight = document.body.classList.contains('light-theme') || document.body.classList.contains('light-mode');
            applyTheme(isLight ? 'dark' : 'light');
        };

        // === Mock Twitch API for Demo Mode ===
        function setupDemoApiMocks() {
            const handleDemoRequest = async (endpoint, method = 'GET', body = null) => {
                const upperMethod = String(method || 'GET').toUpperCase();
                const path = String(endpoint || '').split('?')[0];

                const notifyDemoAction = (msg) => {
                    if (typeof showToast === 'function') {
                        showToast(`【DEMO動作】${msg}（※実際のTwitch操作は行われません）`);
                    }
                    if (typeof raidSoLog === 'function') {
                        raidSoLog(`[DEMO] ${msg}`, 'info');
                    }
                };

                // Custom rewards
                if (path.includes('/channel_points/custom_rewards')) {
                    if (upperMethod === 'GET') {
                        return { data: (typeof cpState !== 'undefined' && cpState.rewards) ? cpState.rewards : [] };
                    }
                    if (upperMethod === 'POST') {
                        notifyDemoAction('チャンネルポイントを作成しました');
                        let parsedBody = typeof body === 'string' ? JSON.parse(body) : body;
                        const newReward = {
                            id: `demo-cp-${Date.now()}`,
                            title: parsedBody?.title || '新規ポイント',
                            cost: parsedBody?.cost || 100,
                            prompt: parsedBody?.prompt || '',
                            is_enabled: true,
                            is_paused: false,
                            background_color: parsedBody?.background_color || '#9146FF',
                            is_user_input_required: !!parsedBody?.is_user_input_required
                        };
                        if (typeof cpState !== 'undefined') {
                            cpState.rewards.push(newReward);
                            cpState.appRewardIds.push(newReward.id);
                        }
                        if (typeof renderCpTab === 'function') renderCpTab();
                        return { data: [newReward] };
                    }
                    if (upperMethod === 'PATCH') {
                        notifyDemoAction('チャンネルポイントを更新しました');
                        let parsedBody = typeof body === 'string' ? JSON.parse(body) : body;
                        const rewardId = new URLSearchParams((endpoint || '').split('?')[1] || '').get('id');
                        if (typeof cpState !== 'undefined' && cpState.rewards) {
                            const idx = cpState.rewards.findIndex(r => r.id === rewardId);
                            if (idx !== -1) {
                                cpState.rewards[idx] = { ...cpState.rewards[idx], ...parsedBody };
                            }
                        }
                        if (typeof renderCpTab === 'function') renderCpTab();
                        return { data: [(cpState && cpState.rewards && cpState.rewards[0]) || parsedBody || {}] };
                    }
                    if (upperMethod === 'DELETE') {
                        notifyDemoAction('チャンネルポイントを削除しました');
                        if (typeof renderCpTab === 'function') renderCpTab();
                        return { data: [] };
                    }
                }

                // Chat Settings & Clear
                if (path.includes('/chat/settings')) {
                    if (upperMethod === 'PATCH') notifyDemoAction('チャット設定を変更しました');
                    return { data: [{ emote_mode: false, follower_mode: false, slow_mode: false, subscriber_mode: false, unique_chat_mode: false }] };
                }
                if (path.includes('/chat/clear')) {
                    notifyDemoAction('チャットをクリアしました');
                    return { data: [] };
                }

                // Streams & Users & Channels
                if (path.includes('/streams') || path.includes('/users') || path.includes('/channels')) {
                    return { data: [{ id: '501391907', user_id: '501391907', login: 'demo_user', display_name: 'demo_user', title: '【DEMO】配信タイトルプレビュー', game_name: 'Just Chatting', type: 'live' }] };
                }

                // Markers & Announcements
                if (path.includes('/streams/markers')) {
                    notifyDemoAction('配信マーカーを作成しました');
                    return { data: [{ id: 'demo-marker-1', created_at: new Date().toISOString() }] };
                }
                if (path.includes('/chat/announcements')) {
                    notifyDemoAction('チャット告知を送信しました');
                    return { data: [] };
                }

                // Predictions & Polls
                if (path.includes('/predictions')) {
                    if (upperMethod === 'POST') notifyDemoAction('予測を作成しました');
                    if (upperMethod === 'PATCH') notifyDemoAction('予測を終了/キャンセルしました');
                    return { data: [] };
                }
                if (path.includes('/polls')) {
                    if (upperMethod === 'POST') notifyDemoAction('投票を作成しました');
                    if (upperMethod === 'PATCH') notifyDemoAction('投票を終了しました');
                    return { data: [] };
                }

                // Clips, Subs, VIPs, EventSub
                if (path.includes('/clips')) {
                    if (upperMethod === 'POST') notifyDemoAction('クリップを作成しました');
                    return { data: [] };
                }
                if (path.includes('/subscriptions') || path.includes('/vips') || path.includes('/eventsub')) {
                    return { data: [] };
                }

                if (upperMethod !== 'GET') {
                    notifyDemoAction('設定を変更しました');
                }
                return { data: [] };
            };

            window.apiRequest = async function(endpoint, method = 'GET', body = null, silent = false) {
                return await handleDemoRequest(endpoint, method, body);
            };

            window.raidSoHelix = async function(endpoint, options = {}) {
                return await handleDemoRequest(endpoint, options ? options.method || 'GET' : 'GET', options ? options.body || null : null);
            };
        }

        function initDemoDummyData() {
            // 1. Settings & User Info Protection
            if (typeof settings !== 'undefined' && settings) {
                settings.userLogin = 'demo_user';
                settings.userId = '12345678';
                settings.token = 'demo_dummy_token';
            }

            // 2. Stream Time Stats (★ Button)
            const now = new Date();
            const demoParsedVideos = [
                { createdAt: new Date(now.getTime() - 2.5 * 3600 * 1000), durationSec: 9000, isLive: true },
                { createdAt: new Date(now.getTime() - 24 * 3600 * 1000), durationSec: 14400, isLive: false },
                { createdAt: new Date(now.getTime() - 48 * 3600 * 1000), durationSec: 10800, isLive: false },
                { createdAt: new Date(now.getTime() - 72 * 3600 * 1000), durationSec: 12600, isLive: false },
                { createdAt: new Date(now.getTime() - 96 * 3600 * 1000), durationSec: 18000, isLive: false },
            ];
            if (typeof streamStatsCache !== 'undefined') {
                streamStatsCache = {
                    timestamp: Date.now() + 864000000,
                    data: {
                        past7Stats: { count: 5, totalSec: 64800, avgSec: 12960 },
                        weekStats: { count: 5, totalSec: 64800, avgSec: 12960 },
                        monthStats: { count: 18, totalSec: 216000, avgSec: 12000 },
                        isCurrentlyLive: true,
                        currentMonthNum: now.getMonth() + 1,
                        hasData: true,
                        parsedVideos: demoParsedVideos,
                        now: now
                    }
                };
            }
            const btnStats = document.getElementById('stream-time-stats-btn');
            if (btnStats) {
                btnStats.classList.remove('inactive');
                btnStats.classList.add('active');
            }

            // 3. Channel Points (CP Tab)
            if (typeof cpState !== 'undefined') {
                const dummyRewards = [
                    { id: "demo-cp-1", title: "【音】悲鳴SEを鳴らす", cost: 100, prompt: "配信上で効果音が再生されます", is_enabled: true, is_paused: false, background_color: "#9146FF", is_user_input_required: false },
                    { id: "demo-cp-2", title: "スタンプ巨大化", cost: 500, prompt: "画面上にチャットスタンプを大きく表示します", is_enabled: true, is_paused: false, background_color: "#FF69B4", is_user_input_required: false },
                    { id: "demo-cp-3", title: "水飲む (水分補給)", cost: 50, prompt: "配信者に水を飲むよう促します", is_enabled: true, is_paused: false, background_color: "#00C875", is_user_input_required: false },
                    { id: "demo-cp-4", title: "セリフリクエスト", cost: 1000, prompt: "リクエストセリフを配信者が読み上げます", is_enabled: false, is_paused: false, background_color: "#3B82F6", is_user_input_required: true },
                    { id: "demo-cp-5", title: "ゲーム内武器制限", cost: 2000, prompt: "1マッチ指定の武器のみでプレイします", is_enabled: true, is_paused: false, background_color: "#FF9800", is_user_input_required: false },
                    { id: "demo-cp-6", title: "【作業配信】集中タイム", cost: 300, prompt: "15分間BGMのみで作業に集中します", is_enabled: false, is_paused: true, background_color: "#E93D3A", is_user_input_required: false }
                ];

                const dummyGroups = [
                    { id: "grp-1", name: "配信演出", rewardIds: ["demo-cp-1", "demo-cp-2"], autoStreamStart: true, autoStreamEnd: true, autoRaid: false, autoOffMinutes: 0 },
                    { id: "grp-2", name: "健康管理", rewardIds: ["demo-cp-3"], autoStreamStart: false, autoStreamEnd: false, autoRaid: false, autoOffMinutes: 0 },
                    { id: "grp-3", name: "企画・縛り", rewardIds: ["demo-cp-4", "demo-cp-5"], autoStreamStart: false, autoStreamEnd: false, autoRaid: false, autoOffMinutes: 0 }
                ];

                cpState.rewards = dummyRewards;
                cpState.groups = dummyGroups;
                cpState.appRewardIds = dummyRewards.map(r => r.id);
                cpState.isLoading = false;

                if (typeof renderCpTab === 'function') {
                    renderCpTab();
                }
                const totalCountEl = document.getElementById('cp-total-count');
                if (totalCountEl) totalCountEl.textContent = dummyRewards.length;
            }

            // 4. Supporter List (Twitch Tab)
            const setVal = (id, val) => { const el = document.getElementById(id); if (el) el.value = val; };
            setVal('pg-i-first-det', '初見リスナーA');
            setVal('pg-i-raid-det', '仲良し配信者B (15人) https://www.twitch.tv/raider_b');
            setVal('pg-i-follow-det', '新規フォロワーC, フォロワーD');
            setVal('pg-i-cheer-det', '熱心なサポーターE 500');
            setVal('pg-i-sub-det', '常連リスナーF 6か月');
            setVal('pg-i-gift-det', '太腹パトロンG 5個');
            setVal('pg-i-chat-det', 'アクティブチャッターH');
            setVal('pg-i-point-det', 'リスナーI (悲鳴SE)');

            if (typeof updatePostPreview === 'function') {
                updatePostPreview();
            }

            // 5. Prediction & Poll Default Inputs
            setVal('pred-title', '今日のゲーム勝率は？');
            setVal('poll-title', '次回プレイするゲームのジャンルは？');

            // 6. Clips Dummy Data
            const clipContainer = document.getElementById('tw-clip-result');
            if (clipContainer) {
                clipContainer.innerHTML = `
                    <div style="display:flex;flex-direction:column;gap:8px;padding-top:4px;">
                        <div style="background:var(--bg-item);border:1px solid var(--border-color);padding:8px 10px;border-radius:6px;font-size:11px;">
                            <div style="font-weight:bold;color:var(--twitch-purple);margin-bottom:2px;">🎬 神プレイ達成シーン！</div>
                            <div style="color:var(--text-muted);font-size:10px;">再生数: 1,250回 | 作成日: 2026/08/01 | クリエイター: Listener_A</div>
                        </div>
                        <div style="background:var(--bg-item);border:1px solid var(--border-color);padding:8px 10px;border-radius:6px;font-size:11px;">
                            <div style="font-weight:bold;color:var(--twitch-purple);margin-bottom:2px;">🎬 爆笑ハプニングアクシデント</div>
                            <div style="color:var(--text-muted);font-size:10px;">再生数: 890回 | 作成日: 2026/07/28 | クリエイター: Listener_B</div>
                        </div>
                        <div style="background:var(--bg-item);border:1px solid var(--border-color);padding:8px 10px;border-radius:6px;font-size:11px;">
                            <div style="font-weight:bold;color:var(--twitch-purple);margin-bottom:2px;">🎬 奇跡のラスト1秒逆転勝利</div>
                            <div style="color:var(--text-muted);font-size:10px;">再生数: 620回 | 作成日: 2026/07/20 | クリエイター: Listener_C</div>
                        </div>
                    </div>
                `;
            }

            // 7. Subscribers & VIPs Dummy Data
            const subContainer = document.getElementById('tw-sub-list');
            if (subContainer) {
                subContainer.innerHTML = `
                    <div style="display:flex;flex-direction:column;gap:6px;">
                        <div style="background:var(--bg-item);border:1px solid var(--border-color);padding:6px 10px;border-radius:6px;font-size:11px;display:flex;justify-content:space-between;align-items:center;">
                            <span>⭐ <strong>Subscriber_Alpha</strong> (Tier 1)</span>
                            <span style="color:var(--twitch-purple);font-weight:bold;">12ヶ月継続</span>
                        </div>
                        <div style="background:var(--bg-item);border:1px solid var(--border-color);padding:6px 10px;border-radius:6px;font-size:11px;display:flex;justify-content:space-between;align-items:center;">
                            <span>⭐ <strong>Subscriber_Beta</strong> (Tier 3)</span>
                            <span style="color:var(--twitch-purple);font-weight:bold;">5ヶ月継続</span>
                        </div>
                        <div style="background:var(--bg-item);border:1px solid var(--border-color);padding:6px 10px;border-radius:6px;font-size:11px;display:flex;justify-content:space-between;align-items:center;">
                            <span>🎁 <strong>Subscriber_Gamma</strong> (Gifted)</span>
                            <span style="color:var(--text-muted);">新規サブスク</span>
                        </div>
                    </div>
                `;
            }

            const vipContainer = document.getElementById('tw-vip-list');
            if (vipContainer) {
                vipContainer.innerHTML = `
                    <div style="display:flex;flex-direction:column;gap:6px;">
                        <div style="background:var(--bg-item);border:1px solid var(--border-color);padding:6px 10px;border-radius:6px;font-size:11px;display:flex;justify-content:space-between;align-items:center;">
                            <span>💎 <strong>VipUser_01</strong></span>
                            <span style="color:var(--text-muted);font-size:10px;">VIP付与済み</span>
                        </div>
                        <div style="background:var(--bg-item);border:1px solid var(--border-color);padding:6px 10px;border-radius:6px;font-size:11px;display:flex;justify-content:space-between;align-items:center;">
                            <span>💎 <strong>VipUser_02</strong></span>
                            <span style="color:var(--text-muted);font-size:10px;">VIP付与済み</span>
                        </div>
                    </div>
                `;
            }
            const vipSlotEl = document.getElementById('tw-vip-slot-info');
            if (vipSlotEl) {
                vipSlotEl.innerHTML = '<span><span>VIP枠: </span><strong style="color:var(--twitch-purple);">2 / 10 使用中</strong></span>';
            }

            // 8. Friends List (IDリスト タブ)
            if (typeof friends !== 'undefined' && Array.isArray(friends) && friends.length === 0) {
                friends.push(
                    { id: "f-1", name: "ストリーマーA", twitch: "streamer_a", group: "コラボ相手", memo: "毎週土曜日コラボ配信", count: 12, lastRaid: "2026/08/01" },
                    { id: "f-2", name: "ストリーマーB", twitch: "streamer_b", group: "仲良し", memo: "FPS相互応援", count: 8, lastRaid: "2026/07/28" },
                    { id: "f-3", name: "ストリーマーC", twitch: "streamer_c", group: "公式イベント", memo: "大会参加メンバー", count: 5, lastRaid: "2026/07/15" }
                );
                if (typeof renderFriends === 'function') {
                    renderFriends();
                }
            }

            setupDemoApiMocks();
        }

        document.addEventListener('DOMContentLoaded', function() {
            const tokenInput = document.getElementById('token');
            if (tokenInput) {
                tokenInput.value = "********************************";
            }
            setTimeout(initDemoDummyData, 200);
            setTimeout(initDemoDummyData, 800);
        });
    </script>

    <!-- 共通Webツールフッター -->
    <script src="../footer.js"></script>
</body>

</html>
"""

full_html = head_content + source_body_content + footer_content

with open(target_path, "w", encoding="utf-8") as f:
    f.write(full_html)

print("Successfully built TwitchManager.html with complete DEMO protection and mocks")

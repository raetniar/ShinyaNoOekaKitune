/* Streamer Tools Comprehensive i18n Engine (ja / en / zh) */
(function() {
    const I18N_STORAGE_KEY = 'streamer-tool-lang-v1';
    
    const TRANSLATIONS = {
        ja: {
            'brand-logo': 'UIKOUKA | TOOLS',
            'hero-title': '配信者向け素材・ツールライブラリ',
            'hero-subtitle': 'Twitch / YouTube / OBSの配信画面を彩る便利な無料ツール集',
            'filter-all': 'すべて',
            'filter-twitch': 'Twitch',
            'filter-obs': 'OBS',
            'filter-utility': '便利ツール',
            'btn-open-tool': 'ツールを開く',
            'footer-copyright': '© 2026 Streamer Tools. All rights reserved.',

            // Tool 1: Twitch Manager
            'card-title-twitch-manager': 'Twitch マネージャー',
            'card-desc-twitch-manager': '配信イベント通知、音源再生、チャット連携機能を一括管理できる高機能OBSダッシュボード。',

            // Tool 2: Twitch Panel Editor
            'card-title-panel-editor': 'Twitch パネルエディター',
            'card-desc-panel-editor': '配信概要欄を彩るおしゃれなパネル画像を簡単作成。',

            // Tool 3: Twitch Image Resizer
            'card-title-resizer': 'Twitch 画像リサイザー ＆ プレビュー',
            'card-desc-resizer': 'プロフィールアイコン、バナー、スタンプ、サブスクバッジを本物同等の画面で即時プレビュー変換。',

            // Tool 4: SVG Calendar Generator
            'card-title-calendar': 'SVG カレンダージェネレーター',
            'card-desc-calendar': '配信スケジュールや月間イベントに使えるカスタマイズ可能なSVGカレンダー自動生成ツール。',

            // Tool 5: OBS Asset Manager
            'card-title-obs-asset': 'OBS アセットマネージャー',
            'card-desc-obs-asset': 'OBSオーバーレイ素材やアニメーションアセットを整理・ワンクリック適用できる管理ツール。',

            // Resizer Controls
            'resizer-drop-text': '画像をドラッグ＆ドロップ、または',
            'resizer-btn-select': 'ファイルを選択',
            'resizer-preset-title': 'プリセット選択',
            'resizer-btn-export-zip': '一括ダウンロード (ZIP)',
            'resizer-guide-tip': 'ドラッグ：画像移動/文字移動 | ホイール：ズーム',
            'resizer-chat-title': '配信チャット',
            'resizer-chat-placeholder': 'メッセージを送信',
            'resizer-chat-send-btn': 'チャット',
            'resizer-chat-huge-label': 'スタンプ巨大化 (64px)',
            'resizer-search-emote-placeholder': 'スタンプを検索',
            'resizer-created-emotes-label': '作成したスタンプ',

            // Common Presets
            'preset-profile_icon': 'プロフィールアイコン (256x256)',
            'preset-profile_banner': 'プロフィールバナー (1200x480)',
            'preset-offline_banner': 'オフラインバナー (1920x1080)',
            'preset-info_panel': '情報パネル (320x160)',
            'preset-sub_emote': 'スタンプ (112x112)',
            'preset-sub_badge': 'サブスクバッジ (72x72)',
            'preset-bits_badge': 'Bitsバッジ (72x72)',
            'preset-reward_icon': 'チャンネルポイント (112x112)'
        },
        en: {
            'brand-logo': 'UIKOUKA | TOOLS',
            'hero-title': 'Streamer Asset & Tool Library',
            'hero-subtitle': 'Free utility tools designed for Twitch, YouTube & OBS streamers',
            'filter-all': 'All',
            'filter-twitch': 'Twitch',
            'filter-obs': 'OBS',
            'filter-utility': 'Utilities',
            'btn-open-tool': 'Open Tool',
            'footer-copyright': '© 2026 Streamer Tools. All rights reserved.',

            // Tool 1: Twitch Manager
            'card-title-twitch-manager': 'Twitch Manager',
            'card-desc-twitch-manager': 'All-in-one OBS dashboard for stream events, audio playback, and chat integration.',

            // Tool 2: Twitch Panel Editor
            'card-title-panel-editor': 'Twitch Panel Editor',
            'card-desc-panel-editor': 'Create stylish panel images for your Twitch channel about section.',

            // Tool 3: Twitch Image Resizer
            'card-title-resizer': 'Twitch Image Resizer & Previewer',
            'card-desc-resizer': 'Instantly resize & preview profile icons, banners, emotes, and badges in real Twitch UI.',

            // Tool 4: SVG Calendar Generator
            'card-title-calendar': 'SVG Calendar Generator',
            'card-desc-calendar': 'Customizable SVG calendar generator for stream schedules and monthly events.',

            // Tool 5: OBS Asset Manager
            'card-title-obs-asset': 'OBS Asset Manager',
            'card-desc-obs-asset': 'Organize and 1-click apply OBS overlays and animated assets.',

            // Resizer Controls
            'resizer-drop-text': 'Drag & Drop Images here or',
            'resizer-btn-select': 'Select Files',
            'resizer-preset-title': 'Select Preset',
            'resizer-btn-export-zip': 'Download All (ZIP)',
            'resizer-guide-tip': 'Drag: Move Image/Text | Scroll: Zoom',
            'resizer-chat-title': 'Stream Chat',
            'resizer-chat-placeholder': 'Send a message',
            'resizer-chat-send-btn': 'Chat',
            'resizer-chat-huge-label': 'Huge Emote (64px)',
            'resizer-search-emote-placeholder': 'Search Emotes',
            'resizer-created-emotes-label': 'Created Emotes',

            // Common Presets
            'preset-profile_icon': 'Profile Icon (256x256)',
            'preset-profile_banner': 'Profile Banner (1200x480)',
            'preset-offline_banner': 'Offline Banner (1920x1080)',
            'preset-info_panel': 'Info Panel (320x160)',
            'preset-sub_emote': 'Sub Emote (112x112)',
            'preset-sub_badge': 'Sub Badge (72x72)',
            'preset-bits_badge': 'Bits Badge (72x72)',
            'preset-reward_icon': 'Channel Points (112x112)'
        },
        zh: {
            'brand-logo': 'UIKOUKA | 工具集',
            'hero-title': '主播素材与工具库',
            'hero-subtitle': '适用于 Twitch、YouTube 和 OBS 主播的免费实用工具集',
            'filter-all': '全部',
            'filter-twitch': 'Twitch',
            'filter-obs': 'OBS',
            'filter-utility': '实用工具',
            'btn-open-tool': '打开工具',
            'footer-copyright': '© 2026 Streamer Tools. 保留所有权利。',

            // Tool 1: Twitch Manager
            'card-title-twitch-manager': 'Twitch 管理器',
            'card-desc-twitch-manager': '集成直播事件通知、音效播放和聊天互动的多功能 OBS 控制面板。',

            // Tool 2: Twitch Panel Editor
            'card-title-panel-editor': 'Twitch 面板编辑器',
            'card-desc-panel-editor': '轻松创建美观的 Twitch 频道简介面板图片。',

            // Tool 3: Twitch Image Resizer
            'card-title-resizer': 'Twitch 图片调整与预览器',
            'card-desc-resizer': '在真实 Twitch 界面中即时调整并预览头像、横幅、表情和徽章。',

            // Tool 4: SVG Calendar Generator
            'card-title-calendar': 'SVG 日历生成器',
            'card-desc-calendar': '适用于直播计划和月度活动的可自定义 SVG 日历自动生成工具。',

            // Tool 5: OBS Asset Manager
            'card-title-obs-asset': 'OBS 资源管理器',
            'card-desc-obs-asset': '整理并一键应用 OBS 覆盖层素材与动态动画资源。',

            // Resizer Controls
            'resizer-drop-text': '拖拽图片至此处，或',
            'resizer-btn-select': '选择文件',
            'resizer-preset-title': '选择预设',
            'resizer-btn-export-zip': '打包下载 (ZIP)',
            'resizer-guide-tip': '拖拽：移动图片/文字 | 滚轮：缩放',
            'resizer-chat-title': '直播聊天',
            'resizer-chat-placeholder': '发送消息',
            'resizer-chat-send-btn': '发送',
            'resizer-chat-huge-label': '表情放大 (64px)',
            'resizer-search-emote-placeholder': '搜索表情',
            'resizer-created-emotes-label': '已创建的表情',

            // Common Presets
            'preset-profile_icon': '个人头像 (256x256)',
            'preset-profile_banner': '个人横幅 (1200x480)',
            'preset-offline_banner': '离线横幅 (1920x1080)',
            'preset-info_panel': '信息面板 (320x160)',
            'preset-sub_emote': '订阅表情 (112x112)',
            'preset-sub_badge': '订阅徽章 (72x72)',
            'preset-bits_badge': 'Bits徽章 (72x72)',
            'preset-reward_icon': '频道积分 (112x112)'
        }
    };

    function getCurrentLang() {
        return localStorage.getItem(I18N_STORAGE_KEY) || 'ja';
    }

    function setLang(lang) {
        if (!TRANSLATIONS[lang]) return;
        localStorage.setItem(I18N_STORAGE_KEY, lang);
        applyTranslations(lang);
        updateLangSelectorUI(lang);
    }

    function applyTranslations(lang) {
        const dict = TRANSLATIONS[lang] || TRANSLATIONS.ja;
        
        // 1. data-i18n elements
        document.querySelectorAll('[data-i18n]').forEach(el => {
            const key = el.getAttribute('data-i18n');
            if (dict[key]) {
                el.textContent = dict[key];
            }
        });

        // 2. data-i18n-placeholder elements
        document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
            const key = el.getAttribute('data-i18n-placeholder');
            if (dict[key]) {
                el.placeholder = dict[key];
            }
        });
    }

    function updateLangSelectorUI(lang) {
        const selectEl = document.getElementById('global-lang-select');
        if (selectEl) {
            selectEl.value = lang;
        }
    }

    function isRootIndexPage() {
        const path = window.location.pathname.toLowerCase();
        // If in tools subfolder or individual tool file, return false
        if (path.includes('/tools/')) return false;
        return true;
    }

    function createLangSelectorWidget() {
        // Display dropdown ONLY on root index page
        if (!isRootIndexPage()) return;
        if (document.getElementById('global-lang-select-container')) return;

        const container = document.createElement('div');
        container.id = 'global-lang-select-container';
        container.style.cssText = 'position: fixed; top: 14px; right: 20px; z-index: 99999; display: flex; align-items: center; gap: 6px; background: rgba(24, 24, 27, 0.92); border: 1px solid #444; border-radius: 20px; padding: 4px 12px; backdrop-filter: blur(10px); box-shadow: 0 4px 16px rgba(0,0,0,0.6);';

        container.innerHTML = `
            <span style="font-size: 13px; color: #efeff1; display: flex; align-items: center;">🌐</span>
            <select id="global-lang-select" style="background: transparent; border: none; outline: none; color: #efeff1; font-size: 12px; font-weight: 700; cursor: pointer;">
                <option value="ja" style="background: #18181b; color: #fff;">日本語 (JA)</option>
                <option value="en" style="background: #18181b; color: #fff;">English (EN)</option>
                <option value="zh" style="background: #18181b; color: #fff;">中文 (ZH)</option>
            </select>
        `;

        document.body.appendChild(container);

        const selectEl = document.getElementById('global-lang-select');
        if (selectEl) {
            selectEl.value = getCurrentLang();
            selectEl.addEventListener('change', (e) => {
                setLang(e.target.value);
            });
        }
    }

    window.i18n = {
        getCurrentLang,
        setLang,
        applyTranslations
    };

    document.addEventListener('DOMContentLoaded', () => {
        createLangSelectorWidget();
        applyTranslations(getCurrentLang());
    });
})();

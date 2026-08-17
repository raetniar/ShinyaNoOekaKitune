document.addEventListener('DOMContentLoaded', () => {


            const chatList = document.getElementById('chat-messages-list');


            const chatSendBuffer = document.getElementById('chat-send-buffer');


            const chatEmoteSelector = document.getElementById('chat-emote-selector');


            const btnClearBuffer = document.getElementById('btn-clear-chat-buffer');


            const btnSendBuffered = document.getElementById('btn-send-buffered-emotes');


            const checkboxHuge = document.getElementById('chat-huge-emote');


            


            // 送信バッファの状態（画像オブジェクトの配列）


            let chatBuffer = [];





            // チャット欄へメッセージ追加


            function addMockupChatMessage(emoteItems, isHuge = false) {


                if (!chatList) return;


                const msgEl = document.createElement('div');


                msgEl.className = 'mock-chat-message';


                msgEl.style.display = 'flex';


                msgEl.style.alignItems = 'center';


                msgEl.style.flexWrap = 'wrap';


                msgEl.style.gap = '4px';


                msgEl.style.padding = '4px 8px';


                


                const time = new Date().toLocaleTimeString('ja-JP', {hour: '2-digit', minute:'2-digit'});


                


                let emotesHtml = '';


                const sizeStyle = isHuge 


                    ? 'width: 112px; height: 112px; vertical-align: middle; border-radius: 2px;' 


                    : 'width: 28px; height: 28px; vertical-align: middle; border-radius: 2px;';


                


                emoteItems.forEach(item => {


                    emotesHtml += `<img src="${item.src}" alt="stamp" style="${sizeStyle}">`;


                });





                msgEl.innerHTML = `


                    <span class="chat-timestamp" style="font-size: 10px; color: var(--mock-chat-timestamp); margin-right: 4px;">${time}</span>


                    <span class="chat-username" style="color: var(--twitch-chat-mod); font-weight: 700; margin-right: 4px;">You</span>


                    <span class="chat-separator" style="color: var(--text-secondary); margin-right: 4px;">:</span>


                    <div style="display: inline-flex; align-items: center; gap: 4px; flex-wrap: wrap;">${emotesHtml}</div>


                `;


                chatList.appendChild(msgEl);


                chatList.scrollTop = chatList.scrollHeight;


            }





            // セレクター（キュー画像一覧）の描画更新


            window.updateChatEmoteSelector = function() {


                if (!chatEmoteSelector) return;


                chatEmoteSelector.innerHTML = '';


                


                if (state.queue.length === 0) {


                    chatEmoteSelector.innerHTML = '<span style="font-size: 10px; color: var(--text-secondary); opacity: 0.6;">画像がありません</span>';


                    return;


                }


                


                state.queue.forEach(item => {


                    const imgEl = document.createElement('img');


                    imgEl.src = item.src;


                    imgEl.alt = item.name;


                    imgEl.style.width = '24px';


                    imgEl.style.height = '24px';


                    imgEl.style.objectFit = 'cover';


                    imgEl.style.cursor = 'pointer';


                    imgEl.style.border = '1px solid var(--border-color)';


                    imgEl.style.borderRadius = '3px';


                    imgEl.title = item.name;


                    imgEl.addEventListener('click', () => {


                        addToChatBuffer(item);


                    });


                    chatEmoteSelector.appendChild(imgEl);


                });


            };





            // バッファにスタンプを追加


            function addToChatBuffer(item) {


                chatBuffer.push(item);


                renderChatBuffer();


            }





            // バッファ描画更新


            function renderChatBuffer() {


                if (!chatSendBuffer) return;


                chatSendBuffer.innerHTML = '';


                


                if (chatBuffer.length === 0) {


                    chatSendBuffer.innerHTML = '<span style="font-size: 10px; color: var(--text-secondary); opacity: 0.6; padding-left: 4px;">スタンプを選択して並べてね...</span>';


                    return;


                }


                


                chatBuffer.forEach((item, index) => {


                    const wrapper = document.createElement('div');


                    wrapper.style.position = 'relative';


                    wrapper.style.display = 'inline-block';


                    


                    const imgEl = document.createElement('img');


                    imgEl.src = item.src;


                    imgEl.style.width = '24px';


                    imgEl.style.height = '24px';


                    imgEl.style.objectFit = 'cover';


                    imgEl.style.border = '1px solid var(--border-color)';


                    imgEl.style.borderRadius = '3px';


                    


                    // バッファから個別削除するボタン


                    const delBtn = document.createElement('div');


                    delBtn.innerHTML = '&times;';


                    delBtn.style.position = 'absolute';


                    delBtn.style.top = '-4px';


                    delBtn.style.right = '-4px';


                    delBtn.style.width = '10px';


                    delBtn.style.height = '10px';


                    delBtn.style.background = '#eb0400';


                    delBtn.style.color = '#fff';


                    delBtn.style.borderRadius = '50%';


                    delBtn.style.fontSize = '8px';


                    delBtn.style.display = 'flex';


                    delBtn.style.alignItems = 'center';


                    delBtn.style.justifyContent = 'center';


                    delBtn.style.cursor = 'pointer';


                    delBtn.addEventListener('click', (e) => {


                        e.stopPropagation();


                        chatBuffer.splice(index, 1);


                        renderChatBuffer();


                    });


                    


                    wrapper.appendChild(imgEl);


                    wrapper.appendChild(delBtn);


                    chatSendBuffer.appendChild(wrapper);


                });


            }





            // バッファクリア


            btnClearBuffer?.addEventListener('click', () => {


                chatBuffer = [];


                renderChatBuffer();


            });





            // バッファ送信


            btnSendBuffered?.addEventListener('click', () => {


                if (chatBuffer.length === 0) return;


                


                const isHuge = checkboxHuge ? checkboxHuge.checked && chatBuffer.length === 1 : false;


                addMockupChatMessage(chatBuffer, isHuge);


                


                // 送信後にバッファクリア


                chatBuffer = [];


                renderChatBuffer();


            });


        });


        /* ==========================================================================


           Twitch Image Resizer & Creator - Integrated Application Script


           ========================================================================== */





        // 1. App Presets Configuration with category prefixes


        const PRESETS = {
            profile_icon:   { name: 'プロフィールアイコン', width: 256,  height: 256,  prefix: 'ICON',    aspect: '1 / 1',       baseW: 260, baseH: 260 },
            profile_banner: { name: 'チャンネルバナー',     width: 1200, height: 480,  prefix: 'BANNER',  aspect: '1200 / 480',  baseW: 650, baseH: 260 },
            offline_banner: { name: 'オフラインバナー',     width: 1920, height: 1080, prefix: 'OFFLINE', aspect: '1920 / 1080', baseW: 462, baseH: 260 },
            info_panel:     { name: '情報パネル',           width: 320,  height: 160,  prefix: 'PANEL',   aspect: '320 / 160',   baseW: 520, baseH: 260 },
            sub_emote:      { name: 'サブスクスタンプ',     width: 112,  height: 112,  prefix: 'EMOTE',   aspect: '1 / 1',       baseW: 260, baseH: 260 },
            sub_badge:      { name: 'サブスクバッジ',       width: 72,   height: 72,   prefix: 'BADGE',   aspect: '1 / 1',       baseW: 260, baseH: 260 },
            bits_badge:     { name: 'ビッツバッジ',         width: 72,   height: 72,   prefix: 'BITS',    aspect: '1 / 1',       baseW: 260, baseH: 260 },
            reward_icon:    { name: '報酬アイコン',         width: 112,  height: 112,  prefix: 'REWARD',  aspect: '1 / 1',       baseW: 260, baseH: 260 },
            clip_thumb:     { name: 'クリップサムネイル',   width: 1280, height: 720,  prefix: 'CLIP',    aspect: '16 / 9',      baseW: 462, baseH: 260 },

            avatar:         { name: 'プロフィールアイコン', width: 256,  height: 256,  prefix: 'ICON',    aspect: '1 / 1',       baseW: 260, baseH: 260 },
            banner:         { name: 'チャンネルバナー',     width: 1200, height: 480,  prefix: 'BANNER',  aspect: '1200 / 480',  baseW: 650, baseH: 260 },
            offline:        { name: 'オフラインバナー',     width: 1920, height: 1080, prefix: 'OFFLINE', aspect: '1920 / 1080', baseW: 462, baseH: 260 },
            panel:          { name: '情報パネル',           width: 320,  height: 160,  prefix: 'PANEL',   aspect: '320 / 160',   baseW: 520, baseH: 260 },
            emote:          { name: 'サブスクスタンプ',     width: 112,  height: 112,  prefix: 'EMOTE',   aspect: '1 / 1',       baseW: 260, baseH: 260 },
            badge:          { name: 'サブスクバッジ',       width: 72,   height: 72,   prefix: 'BADGE',   aspect: '1 / 1',       baseW: 260, baseH: 260 },
            cheermote:      { name: 'ビッツバッジ',         width: 72,   height: 72,   prefix: 'BITS',    aspect: '1 / 1',       baseW: 260, baseH: 260 },
            point:          { name: '報酬アイコン',         width: 112,  height: 112,  prefix: 'REWARD',  aspect: '1 / 1',       baseW: 260, baseH: 260 }
        };





        // アプリの全体状態


        const state = {


            queue: [],         // 各アップロード画像の個別ステートを格納する配列


            activeImageId: null, // 現在編集対象になっている画像のID


            currentPresetKey: 'avatar',


            isDragging: false,


            dragTarget: null, // 'image' | 'text'


            lastMouseX: 0,


            lastMouseY: 0,


            theme: 'light'


        };





        // 2. DOM Elements


        const elements = {


            themeToggle: document.getElementById('header-theme-toggle'),


            dropZone: document.getElementById('drop-zone'),


            fileInput: document.getElementById('file-input'),


            editorCard: document.getElementById('editor-card'),


            settingsCard: document.getElementById('settings-card'),


            canvas: document.getElementById('editor-canvas'),


            presetSelect: document.getElementById('preset-select'),


            currentPresetBadge: document.getElementById('current-preset-badge'),


            


            // 画像キュー


            queueCard: document.getElementById('queue-card'),


            queueList: document.getElementById('queue-list'),


            queueCountBadge: document.getElementById('queue-count-badge'),


            btnExportAll: document.getElementById('btn-export-all'),


            


            // スライダー＆ボタン


            zoomSlider: document.getElementById('zoom-slider'),


            zoomVal: document.getElementById('zoom-val'),


            btnZoomFit: document.getElementById('btn-zoom-fit'),


            btnRotate: document.getElementById('btn-rotate'),


            btnReset: document.getElementById('btn-reset'),


            


            // 設定項目


            exportNameInput: document.getElementById('export-name-input'),


            namePrefixDisplay: document.getElementById('name-prefix-display'),


            


            // テキストコントロール


            textEnabledCheckbox: document.getElementById('text-enabled'),


            textControlsPanel: document.getElementById('text-controls-panel'),


            textInput: document.getElementById('text-input'),


            fontSelect: document.getElementById('font-select'),


            fontSizeSlider: document.getElementById('font-size-slider'),


            fontSizeVal: document.getElementById('font-size-val'),


            textColorInput: document.getElementById('text-color'),


            textColorHex: document.getElementById('text-color-hex'),


            strokeColorInput: document.getElementById('stroke-color'),


            strokeColorHex: document.getElementById('stroke-color-hex'),


            strokeWidthSlider: document.getElementById('stroke-width-slider'),


            strokeWidthVal: document.getElementById('stroke-width-val'),


            


            // エクスポート


            btnExportSingle: document.getElementById('btn-export-single'),


            btnExportMultiPreset: document.getElementById('btn-export-multi-preset'),


            btnExportAllPresets: document.getElementById('btn-export-all-presets'),


            


            // ファイル名プレビュー


            filenamePreviewList: document.getElementById('filename-preview-list'),


            


            // モックアップ表示部


            previewModeName: document.getElementById('preview-mode-name'),


            mockChatView: document.getElementById('mock-twitch-chat'),


            mockProfileView: document.getElementById('mock-twitch-profile'),


            


            // モックインライン置換部


            previewBadgeInline: document.getElementById('preview-badge-inline'),


            previewEmoteInline: document.getElementById('preview-emote-inline'),


            previewPointsButton: document.getElementById('preview-points-button'),


            previewPointsPopupIcon: document.getElementById('preview-points-popup-icon'),


            previewBannerBg: document.getElementById('preview-banner-bg'),


            previewAvatarCircle: document.getElementById('preview-avatar-circle'),


            previewPanelImg: document.getElementById('preview-panel-img'),


            


            // チャンネルポイントポップアップ


            channelPointsTrigger: document.getElementById('channel-points-trigger'),


            pointsPopup: document.getElementById('points-popup'),


            pointsPopupClose: document.getElementById('points-popup-close')


        };





        const ctx = elements.canvas.getContext('2d');





        // ==========================================================================


        // 3. 初期化 ＆ イベント登録


        // ==========================================================================


                // --- Amazon Ad Rotation Logic ---


        const adLinks = [


            "https://amzn.to/4x1PegD",


            "https://amzn.to/4tU7upp",


            "https://amzn.to/4nIg0Gp",


            "https://amzn.to/43sgXsU",


            "https://amzn.to/3RDRIRQ",


            "https://amzn.to/4dqcKMs",


            "https://amzn.to/4nFXw9o",


            "https://amzn.to/4uqBUR5",


            "https://amzn.to/4nLx2Uf",


            "https://amzn.to/49QcGTR"


        ];





        function initAdRotation() {


            const adContainer = document.getElementById('ad-rotation-container');


            const adAnchor = document.getElementById('ad-link-anchor');


            if (!adContainer || !adAnchor) return;





            let currentIndex = Math.floor(Math.random() * adLinks.length);


            adAnchor.href = adLinks[currentIndex];





            setInterval(() => {


                // Fade out


                adContainer.style.opacity = '0';


                


                setTimeout(() => {


                    // Change link


                    currentIndex = (currentIndex + 1) % adLinks.length;


                    adAnchor.href = adLinks[currentIndex];


                    


                    // Fade in


                    adContainer.style.opacity = '1';


                }, 500); // Wait for fade out


            }, 8000); // Rotate every 8 seconds


        }


        function init() {


            setupTheme();


            setupEventListeners();


            applyPreset();


            switchPreviewTab('chat');


            renderQueueList();


            updateFilenamePreview();


            draw();


            lucide.createIcons();


        }





        function updateThemeUI(theme) {


            localStorage.setItem('twitch-resizer-theme-v3', theme);


            state.theme = theme;


            


            const iconEl = document.getElementById('header-theme-icon');


            const textEl = document.getElementById('header-theme-text');


            


            if (theme === 'dark') {


                document.body.className = 'dark-mode';


                if (iconEl) iconEl.className = 'fa-solid fa-moon';


                if (textEl) textEl.textContent = 'ダークモード';


            } else {


                document.body.className = 'light-mode';


                if (iconEl) iconEl.className = 'fa-solid fa-sun';


                if (textEl) textEl.textContent = 'ライトモード';


            }


            if (typeof draw === 'function') {


                draw();


            }


        }





        // テーマの初期設定


        function setupTheme() {


            try {


                const savedTheme = localStorage.getItem('twitch-resizer-theme-v3') || 'light';


                updateThemeUI(savedTheme);


            } catch(e) {


                updateThemeUI('light');


            }


        }





        // 各種イベントリスナー登録


        function setupEventListeners() {


            elements.themeToggle?.addEventListener('click', toggleTheme);


            elements.dropZone?.addEventListener('click', () => elements.fileInput.click());


            elements.fileInput?.addEventListener('change', handleFileSelect);


            


            elements.dropZone?.addEventListener('dragover', (e) => {


                e.preventDefault();


                elements.dropZone.classList.add('dragover');


            });


            elements.dropZone?.addEventListener('dragleave', () => {


                elements.dropZone.classList.remove('dragover');


            });


            elements.dropZone?.addEventListener('drop', (e) => {


                e.preventDefault();


                elements.dropZone.classList.remove('dragover');


                if (e.dataTransfer.files.length > 0) {


                    handleMultipleFiles(e.dataTransfer.files);


                }


            });





            elements.presetSelect?.addEventListener('change', (e) => {


                state.currentPresetKey = e.target.value;


                const activeImg = getActiveImage();


                if (activeImg) {


                    activeImg.presetKey = state.currentPresetKey;


                    applyPreset();


                    zoomToFit(activeImg);


                    renderQueueList();


                    updateFilenamePreview();


                    draw();


                }


            });





            elements.exportNameInput?.addEventListener('input', (e) => {


                const activeImg = getActiveImage();


                if (activeImg) {


                    const sanitized = e.target.value.replace(/[\/\\?%*:|"<>\s]/g, '_');


                    activeImg.name = sanitized;


                    


                    const queueInput = document.querySelector(`.queue-item[data-id="${activeImg.id}"] .queue-item-name-input`);


                    if (queueInput) {


                        queueInput.value = sanitized;


                    }


                    updateFilenamePreview();


                }


            });





            elements.zoomSlider?.addEventListener('input', (e) => {


                const activeImg = getActiveImage();


                if (activeImg) {


                    activeImg.imgScale = parseFloat(e.target.value);


                    elements.zoomVal.textContent = `${Math.round(activeImg.imgScale * 100)}%`;


                    draw();


                }


            });


            


            elements.btnZoomFit?.addEventListener('click', () => {


                const activeImg = getActiveImage();


                if (activeImg) {


                    zoomToFit(activeImg);


                    draw();


                }


            });





            elements.btnRotate?.addEventListener('click', () => {


                const activeImg = getActiveImage();


                if (activeImg) {


                    activeImg.imgRotation = (activeImg.imgRotation + 90) % 360;


                    draw();


                }


            });





            elements.btnReset?.addEventListener('click', () => {


                const activeImg = getActiveImage();


                if (activeImg) {


                    resetImageTransform(activeImg);


                    draw();


                }


            });





            elements.textEnabledCheckbox?.addEventListener('change', (e) => {


                const activeImg = getActiveImage();


                if (activeImg) {


                    activeImg.textEnabled = e.target.checked;


                    if (activeImg.textEnabled) {


                        elements.textControlsPanel.classList.remove('hidden');


                    } else {


                        elements.textControlsPanel.classList.add('hidden');


                    }


                    draw();


                }


            });





            elements.textInput?.addEventListener('input', (e) => {


                const activeImg = getActiveImage();


                if (activeImg) {


                    activeImg.text = e.target.value;


                    draw();


                }


            });





            elements.fontSelect?.addEventListener('change', (e) => {


                const activeImg = getActiveImage();


                if (activeImg) {


                    activeImg.fontFamily = e.target.value;


                    draw();


                }


            });





            elements.fontSizeSlider?.addEventListener('input', (e) => {


                const activeImg = getActiveImage();


                if (activeImg) {


                    activeImg.fontSize = parseInt(e.target.value);


                    elements.fontSizeVal.textContent = `${activeImg.fontSize}px`;


                    draw();


                }


            });





            elements.textColorInput?.addEventListener('input', (e) => {


                const activeImg = getActiveImage();


                if (activeImg) {


                    activeImg.textColor = e.target.value;


                    elements.textColorHex.textContent = e.target.value.toUpperCase();


                    draw();


                }


            });





            elements.strokeColorInput?.addEventListener('input', (e) => {


                const activeImg = getActiveImage();


                if (activeImg) {


                    activeImg.strokeColor = e.target.value;


                    elements.strokeColorHex.textContent = e.target.value.toUpperCase();


                    draw();


                }


            });





            elements.strokeWidthSlider?.addEventListener('input', (e) => {


                const activeImg = getActiveImage();


                if (activeImg) {


                    activeImg.strokeWidth = parseInt(e.target.value);


                    elements.strokeWidthVal.textContent = `${activeImg.strokeWidth}px`;


                    draw();


                }


            });





            elements.btnExportSingle?.addEventListener('click', exportSingleImage);


            elements.btnExportMultiPreset?.addEventListener('click', exportActiveImageMultiPresets);


            elements.btnExportAllPresets?.addEventListener('click', exportAllQueueMultiPresets);


            elements.btnExportAll?.addEventListener('click', exportAllImagesZip);





            document.querySelectorAll('.batch-preset-checkbox').forEach(cb => {


                cb.addEventListener('change', updateFilenamePreview);


            });





            elements.canvas?.addEventListener('mousedown', handleMouseDown);


            window.addEventListener('mousemove', handleMouseMove);


            window.addEventListener('mouseup', handleMouseUp);


            


            elements.canvas?.addEventListener('wheel', (e) => {


                const activeImg = getActiveImage();


                if (!activeImg) return;


                e.preventDefault();


                const zoomStep = 0.05;


                if (e.deltaY < 0) {


                    activeImg.imgScale = Math.min(5.0, activeImg.imgScale + zoomStep);


                } else {


                    activeImg.imgScale = Math.max(0.1, activeImg.imgScale - zoomStep);


                }


                elements.zoomSlider.value = activeImg.imgScale;


                elements.zoomVal.textContent = `${Math.round(activeImg.imgScale * 100)}%`;


                draw();


            }, { passive: false });





            elements.channelPointsTrigger?.addEventListener('click', (e) => {


                e.stopPropagation();


                elements.pointsPopup.classList.toggle('hidden');


            });


            elements.pointsPopupClose?.addEventListener('click', (e) => {


                e.stopPropagation();


                elements.pointsPopup.classList.add('hidden');


            });


            document.addEventListener('click', () => {


                elements.pointsPopup?.classList.add('hidden');


            });


            elements.pointsPopup?.addEventListener('click', (e) => e.stopPropagation());





            // プレビュータブ切り替えリスナー


            document.querySelectorAll('.preview-tab-btn').forEach(btn => {


                btn.addEventListener('click', (e) => {


                    const target = e.currentTarget.getAttribute('data-target');


                    state.userSelectedTab = target;


                    switchPreviewTab(target);


                });


            });


        }





        // ==========================================================================


        // 4. アプリケーション機能ロジック


        // ==========================================================================





        function getActiveImage() {


            return state.queue.find(item => item.id === state.activeImageId) || null;


        }





        function toggleTheme() {


            const currentTheme = state.theme === 'light' ? 'dark' : 'light';


            updateThemeUI(currentTheme);


        }





        function applyPreset() {


            const activeImg = getActiveImage();


            const presetKey = activeImg ? activeImg.presetKey : state.currentPresetKey;


            const preset = PRESETS[presetKey] || PRESETS.profile_icon;


            


            elements.canvas.width = preset.width;


            elements.canvas.height = preset.height;


            


            // キャンバス画面上の表示枠比率を選択プリセットサイズ(比率)にピッタリ合わせる


            const aspectRatio = preset.width / preset.height;


            elements.canvas.style.aspectRatio = `${preset.width} / ${preset.height}`;


            


            const container = document.querySelector('.canvas-container');


            if (container) {


                const maxW = (container.clientWidth || 400) - 24;


                const maxH = 260;


                


                if (maxW / maxH > aspectRatio) {


                    elements.canvas.style.height = `${maxH}px`;


                    elements.canvas.style.width = `${Math.round(maxH * aspectRatio)}px`;


                } else {


                    elements.canvas.style.width = `${maxW}px`;


                    elements.canvas.style.height = `${Math.round(maxW / aspectRatio)}px`;


                }


            }


            


            if (elements.currentPresetBadge) if (elements.currentPresetBadge) elements.currentPresetBadge.textContent = preset.label;


            if (elements.previewModeName) {


                elements.previewModeName.textContent = `${preset.name} プレビュー`;


            }


            elements.namePrefixDisplay.textContent = `${preset.prefix}_`;


            


            // 手動選択がある場合はそれを優先、無ければプリセットの種類に応じて初期タブを設定


            if (state.userSelectedTab) {


                switchPreviewTab(state.userSelectedTab);


            } else {


                if (['sub_emote', 'sub_badge', 'bits_badge', 'reward_icon', 'emote', 'badge', 'points'].includes(presetKey)) {


                    switchPreviewTab('chat');


                } else {


                    switchPreviewTab('profile');


                }


            }


        }





        // プレビュータブの切り替え


        function switchPreviewTab(tabKey) {


            const tabBtns = document.querySelectorAll('.preview-tab-btn');


            tabBtns.forEach(btn => {


                const target = btn.getAttribute('data-target');


                if (target === tabKey) {


                    btn.classList.add('active');


                } else {


                    btn.classList.remove('active');


                }


            });





            const profileView = document.getElementById('mock-twitch-profile');


            const chatView = document.getElementById('mock-twitch-chat');





            if (tabKey === 'profile') {


                if (profileView) {


                    profileView.style.setProperty('display', 'flex', 'important');


                    profileView.classList.remove('hidden');


                }


                if (chatView) {


                    chatView.style.setProperty('display', 'none', 'important');


                    chatView.classList.add('hidden');


                }


            } else if (tabKey === 'chat') {


                if (profileView) {


                    profileView.style.setProperty('display', 'none', 'important');


                    profileView.classList.add('hidden');


                }


                if (chatView) {


                    chatView.style.setProperty('display', 'flex', 'important');


                    chatView.classList.remove('hidden');


                }


            }


        }





        function handleFileSelect(e) {
            if (e.target && e.target.type === "file") setTimeout(() => { e.target.value = ""; }, 100);


            if (e.target.files.length > 0) {


                handleMultipleFiles(e.target.files);


            }


        }





        function handleMultipleFiles(files) {


            let filesLoaded = 0;


            const totalFiles = files.length;


            


            for (let i = 0; i < totalFiles; i++) {


                const file = files[i];


                const reader = new FileReader();


                


                reader.onload = function(event) {


                    const img = new Image();


                    img.onload = function() {


                        let baseName = file.name.substring(0, file.name.lastIndexOf('.')) || file.name;


                        baseName = baseName.replace(/[\/\\?%*:|"<>\s]/g, '_');


                        


                        const newItem = {


                            id: `img_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,


                            file: file,


                            img: img,


                            src: event.target.result,


                            name: baseName,


                            presetKey: state.currentPresetKey,


                            


                            // トランスフォーム


                            imgX: 0,


                            imgY: 0,


                            imgScale: 1.0,


                            imgRotation: 0,


                            


                            // テキストレイヤー


                            textEnabled: false,


                            text: '',


                            textX: 0,


                            textY: 0,


                            fontSize: 48,


                            fontFamily: "'Noto Sans JP', sans-serif",


                            textColor: '#ffffff',


                            strokeColor: '#9146ff',


                            strokeWidth: 8


                        };


                        


                        zoomToFit(newItem);


                        state.queue.push(newItem);


                        filesLoaded++;


                        


                        if (filesLoaded === totalFiles) {


                            if (!state.activeImageId && state.queue.length > 0) {


                                state.activeImageId = state.queue[0].id;


                            }


                            if (elements.editorCard) elements.editorCard.classList.remove('disabled');


                            if (elements.settingsCard) elements.settingsCard.classList.remove('disabled');


                            


                            renderQueueList();


                            loadActiveImageState();


                            if (typeof applyPreset === 'function') applyPreset();


                            if (typeof draw === 'function') draw();


                        }


                    };


                    img.src = event.target.result;


                };


                reader.readAsDataURL(file);


            }


        }





        function resetImageTransform(imgState) {


            imgState.imgX = 0;


            imgState.imgY = 0;


            imgState.imgRotation = 0;


            imgState.textX = 0;


            imgState.textY = 0;


        }





        function zoomToFit(imgState) {


            if (!imgState || !imgState.img) return;


            


            const preset = PRESETS[imgState.presetKey];


            const canvasWidth = preset.width;


            const canvasHeight = preset.height;


            


            const isRotated90 = (imgState.imgRotation === 90 || imgState.imgRotation === 270);


            const w = isRotated90 ? imgState.img.height : imgState.img.width;


            const h = isRotated90 ? imgState.img.width : imgState.img.height;


            


            const scaleX = canvasWidth / w;


            const scaleY = canvasHeight / h;


            const fitScale = Math.max(scaleX, scaleY);


            


            imgState.imgScale = parseFloat(fitScale.toFixed(2));


            


            const activeImg = getActiveImage();


            if (activeImg && activeImg.id === imgState.id) {


                elements.zoomSlider.value = imgState.imgScale;


                elements.zoomVal.textContent = `${Math.round(imgState.imgScale * 100)}%`;


            }


        }





        // ==========================================================================


        // 4.5. キューマネジメント＆UIレンダラー


        // ==========================================================================


        function renderQueueList() {


            elements.queueList.innerHTML = '';


            elements.queueCountBadge.textContent = `${state.queue.length}枚の画像`;


            


            if (state.queue.length === 0) {


                elements.queueCard.classList.add('hidden');


                elements.editorCard.classList.add('disabled');


                elements.settingsCard.classList.add('disabled');


                state.activeImageId = null;


                resetMockupPlaceholders();


                updateFilenamePreview();


                return;


            }


            


            elements.queueCard.classList.remove('hidden');


            elements.editorCard.classList.remove('disabled');


            elements.settingsCard.classList.remove('disabled');


            


            state.queue.forEach(item => {


                const isActive = (item.id === state.activeImageId);


                


                const row = document.createElement('div');


                row.className = `queue-item ${isActive ? 'active' : ''}`;


                row.setAttribute('data-id', item.id);


                


                row.innerHTML = `


                    <img class="queue-item-thumb" src="${item.img.src}" alt="Thumb">


                    <div class="queue-item-details">


                        <input type="text" class="queue-item-name-input" value="${item.name}" title="カスタム出力ファイル名">


                    </div>


                    <button class="queue-item-delete-btn" title="画像をキューから削除">


                        <i data-lucide="trash-2"></i>


                    </button>


                `;


                


                row.addEventListener('click', (e) => {


                    if (e.target.closest('input') || e.target.closest('select') || e.target.closest('button')) {


                        return;


                    }


                    setActiveImage(item.id);


                });


                


                const nameInput = row.querySelector('.queue-item-name-input');


                nameInput.addEventListener('input', (e) => {


                    const sanitized = e.target.value.replace(/[\/\\?%*:|"<>\s]/g, '_');


                    item.name = sanitized;


                    e.target.value = sanitized;


                    


                    if (item.id === state.activeImageId) {


                        elements.exportNameInput.value = sanitized;


                    }


                });


                


                


                


                const deleteBtn = row.querySelector('.queue-item-delete-btn');


                deleteBtn.addEventListener('click', (e) => {


                    e.stopPropagation();


                    removeImageFromQueue(item.id);


                });


                


                elements.queueList.appendChild(row);


            });


            


            if (window.updateChatEmoteSelector) window.updateChatEmoteSelector();


            lucide.createIcons();


        }





        function setActiveImage(id) {


            state.activeImageId = id;


            renderQueueList();


            loadActiveImageState();


            if (typeof applyPreset === 'function') applyPreset();


            if (typeof draw === 'function') draw();


        }





        function removeImageFromQueue(id) {


            const idx = state.queue.findIndex(item => item.id === id);


            if (idx === -1) return;


            


            state.queue.splice(idx, 1);


            


            if (state.activeImageId === id) {


                if (state.queue.length > 0) {


                    const newActiveIdx = Math.max(0, idx - 1);


                    state.activeImageId = state.queue[newActiveIdx].id;


                } else {


                    state.activeImageId = null;


                }


            }


            


            renderQueueList();


            loadActiveImageState();


            draw();


        }





        function loadActiveImageState() {
            const activeImg = typeof getActiveImage === 'function' ? getActiveImage() : null;
            if (!activeImg) return;
            
            if (typeof elements !== 'undefined' && elements) {
                if (elements.presetSelect && activeImg.presetKey) elements.presetSelect.value = activeImg.presetKey;
                if (elements.exportNameInput) elements.exportNameInput.value = activeImg.name || '';
                if (elements.zoomSlider) elements.zoomSlider.value = activeImg.imgScale || 1;
                if (elements.zoomVal) elements.zoomVal.textContent = `${Math.round((activeImg.imgScale || 1) * 100)}%`;
                
                if (elements.textEnabledCheckbox) elements.textEnabledCheckbox.checked = activeImg.textEnabled || false;
                if (elements.textControlsPanel) {
                    if (activeImg.textEnabled) {
                        elements.textControlsPanel.classList.remove('hidden');
                    } else {
                        elements.textControlsPanel.classList.add('hidden');
                    }
                }
                
                if (elements.textInput) elements.textInput.value = activeImg.text || '';
                if (elements.fontSelect) elements.fontSelect.value = activeImg.fontFamily || "'Noto Sans JP', sans-serif";
                if (elements.fontSizeSlider) elements.fontSizeSlider.value = activeImg.fontSize || 32;
                if (elements.fontSizeVal) elements.fontSizeVal.textContent = `${activeImg.fontSize || 32}px`;
                if (elements.textColorInput) elements.textColorInput.value = activeImg.textColor || '#ffffff';
                if (elements.textColorHex) elements.textColorHex.textContent = activeImg.textColor || '#ffffff';
            }
            
            const sel1 = document.getElementById('preset-selector');
            const sel2 = document.getElementById('preset-key-select');
            if (sel1 && activeImg.presetKey && sel1.value !== activeImg.presetKey) sel1.value = activeImg.presetKey;
            if (sel2 && activeImg.presetKey && sel2.value !== activeImg.presetKey) sel2.value = activeImg.presetKey;
        }





        // ==========================================================================


        // 5. Canvas レンダリングエンジン


        // ==========================================================================


        


        // ==========================================================================


        // 文字入れ・テロップ重ね合わせのイベント連動


        // ==========================================================================


        const overlayInput = document.getElementById('text-overlay-input');


        const posSelect = document.getElementById('text-position-select');


        const fontSelect = document.getElementById('text-font-select');


        const colorPicker = document.getElementById('text-color-picker');


        const strokePicker = document.getElementById('text-stroke-picker');


        const strokeWidthSelect = document.getElementById('text-stroke-width');





        function drawOverlayTextToCtx(targetCtx, w, h) {


            const activeImg = getActiveImage();


            if (!activeImg || !activeImg.textEnabled) return;


            const text = (activeImg.text || '').trim();


            if (!text) return;





            const pos = posSelect ? posSelect.value : 'bottom';


            const fontFamily = fontSelect ? fontSelect.value : "'Noto Sans JP', sans-serif";


            const textColor = colorPicker ? colorPicker.value : '#ffffff';


            const strokeColor = strokePicker ? strokePicker.value : '#9146ff';


            const strokeWidth = strokeWidthSelect ? parseInt(strokeWidthSelect.value, 10) : 4;





            targetCtx.save();


            const fontSize = Math.max(12, Math.round(w * 0.16));


            targetCtx.font = `bold ${fontSize}px ${fontFamily}`;


            targetCtx.textAlign = 'center';


            targetCtx.textBaseline = 'middle';





            let drawX = w / 2;


            let drawY = h * 0.82; // default bottom





            if (pos === 'center') drawY = h / 2;


            else if (pos === 'top') drawY = h * 0.18;


            else if (pos === 'top-left') { drawX = w * 0.25; drawY = h * 0.22; }


            else if (pos === 'bottom-right') { drawX = w * 0.75; drawY = h * 0.78; }





            if (strokeWidth > 0) {


                targetCtx.strokeStyle = strokeColor;


                targetCtx.lineWidth = Math.max(2, Math.round(fontSize * (strokeWidth / 20)));


                targetCtx.lineJoin = 'round';


                targetCtx.lineCap = 'round';


                targetCtx.strokeText(text, drawX, drawY);


            }





            targetCtx.fillStyle = textColor;


            targetCtx.fillText(text, drawX, drawY);


            targetCtx.restore();


        }





        function updateOverlayTextState() {


            const activeImg = getActiveImage();


            if (activeImg) {


                if (elements.textInput) {


                    activeImg.text = elements.textInput.value;


                }


                if (fontSelect) activeImg.fontFamily = fontSelect.value;


                if (colorPicker) activeImg.textColor = colorPicker.value;


                if (strokePicker) activeImg.strokeColor = strokePicker.value;


                if (strokeWidthSelect) activeImg.strokeWidth = parseInt(strokeWidthSelect.value, 10);


            }


            if (typeof draw === 'function') draw();


        }





        [overlayInput, posSelect, fontSelect, colorPicker, strokePicker, strokeWidthSelect].forEach(el => {


            if (el) {


                el.addEventListener('input', updateOverlayTextState);


                el.addEventListener('change', updateOverlayTextState);


            }


        });





        


        // キャンバス編集右上のプリセット切り替えプルダウンの連動


        const presetSelector = document.getElementById('preset-selector');


        if (presetSelector) {


            presetSelector.addEventListener('change', (e) => {


                const activeImg = getActiveImage();


                if (activeImg) {


                    activeImg.presetKey = e.target.value;


                    activeImg.preset = PRESETS[e.target.value] || PRESETS.profile_icon;


                    if (typeof updateEditorUI === 'function') updateEditorUI();


                    if (typeof draw === 'function') draw();


                    if (typeof renderQueue === 'function') renderQueue();


                }


            });


        }





        


        // 文字位置プリセット切り替え処理


        const textPosPreset = document.getElementById('text-pos-preset');


        if (textPosPreset) {


            textPosPreset.addEventListener('change', (e) => {


                const activeImg = getActiveImage();


                if (!activeImg) return;


                const pos = e.target.value;


                const h = elements.canvas.height || 400;


                const w = elements.canvas.width || 400;


                


                activeImg.textX = 0;


                if (pos === 'bottom') activeImg.textY = h * 0.35;


                else if (pos === 'center') activeImg.textY = 0;


                else if (pos === 'top') activeImg.textY = -h * 0.35;


                else if (pos === 'top-left') { activeImg.textX = -w * 0.3; activeImg.textY = -h * 0.3; }


                else if (pos === 'bottom-right') { activeImg.textX = w * 0.3; activeImg.textY = h * 0.3; }


                


                if (typeof draw === 'function') draw();


            });


        }





        


        // テキスト(文字入れ)有効トグルの完全連動ハンドラー


        const textEnabledToggle = document.getElementById('text-enabled');


        const textControlsPanel = document.getElementById('text-controls-panel');


        if (textEnabledToggle && textControlsPanel) {


            textEnabledToggle.addEventListener('change', (e) => {


                const isChecked = e.target.checked;


                const activeImg = getActiveImage();


                if (activeImg) {


                    activeImg.textEnabled = isChecked;


                }


                if (isChecked) {


                    textControlsPanel.classList.remove('hidden');


                } else {


                    textControlsPanel.classList.add('hidden');


                }


                if (typeof draw === 'function') draw();


            });


        }





        // アニメーション再生/停止ボタンの連動


        let isAnimationPlaying = true;


        const btnToggleAnim = document.getElementById('btn-toggle-anim');


        if (btnToggleAnim) {


            btnToggleAnim.addEventListener('click', () => {


                isAnimationPlaying = !isAnimationPlaying;


                const icon = document.getElementById('anim-btn-icon');


                const textSpan = document.getElementById('anim-btn-text');


                if (isAnimationPlaying) {


                    if (icon) icon.setAttribute('data-lucide', 'pause');


                    if (textSpan) textSpan.textContent = '停止';


                } else {


                    if (icon) icon.setAttribute('data-lucide', 'play');


                    if (textSpan) textSpan.textContent = '再生';


                }


                if (window.lucide && window.lucide.createIcons) window.lucide.createIcons();


                if (typeof draw === 'function') draw();


            });


        }





        function draw() {


            ctx.clearRect(0, 0, elements.canvas.width, elements.canvas.height);


            


            const activeImg = getActiveImage();


            


            if (activeImg && activeImg.img) {


                ctx.save();


                ctx.translate(elements.canvas.width / 2 + activeImg.imgX, elements.canvas.height / 2 + activeImg.imgY);


                ctx.rotate((activeImg.imgRotation * Math.PI) / 180);


                


                const drawW = activeImg.img.width * activeImg.imgScale;


                const drawH = activeImg.img.height * activeImg.imgScale;


                


                ctx.drawImage(activeImg.img, -drawW / 2, -drawH / 2, drawW, drawH);


                ctx.restore();


            } else {


                ctx.fillStyle = 'rgba(145, 70, 255, 0.05)';


                ctx.fillRect(0, 0, elements.canvas.width, elements.canvas.height);


                ctx.strokeStyle = 'rgba(145, 70, 255, 0.2)';


                ctx.lineWidth = 2;


                ctx.setLineDash([5, 5]);


                ctx.strokeRect(4, 4, elements.canvas.width - 8, elements.canvas.height - 8);


                ctx.setLineDash([]);


            }


            


            if (activeImg && activeImg.textEnabled && activeImg.text.trim() !== '') {


                ctx.save();


                ctx.font = `${activeImg.strokeWidth > 0 ? 'bold' : ''} ${activeImg.fontSize}px ${activeImg.fontFamily}`;


                ctx.textAlign = 'center';


                ctx.textBaseline = 'middle';


                


                const textDrawX = elements.canvas.width / 2 + activeImg.textX;


                const textDrawY = elements.canvas.height / 2 + activeImg.textY;


                


                if (activeImg.strokeWidth > 0) {


                    ctx.strokeStyle = activeImg.strokeColor;


                    ctx.lineWidth = activeImg.strokeWidth;


                    ctx.lineJoin = 'round';


                    ctx.lineCap = 'round';


                    ctx.strokeText(activeImg.text, textDrawX, textDrawY);


                }


                


                ctx.fillStyle = activeImg.textColor;


                ctx.fillText(activeImg.text, textDrawX, textDrawY);


                ctx.restore();


            }


            


            drawOverlayTextToCtx(ctx, elements.canvas.width, elements.canvas.height);


            updateTwitchMockups();


        }





        function updateTwitchMockups() {


            let dataUrl;


            try {


                dataUrl = elements.canvas.toDataURL('image/png');


            } catch (e) {


                return;


            }


            


            const activeImg = getActiveImage();


            


            if (activeImg) {


                const presetKey = activeImg.presetKey;


                if (presetKey === 'avatar') {


                    elements.previewAvatarCircle.innerHTML = `<img src="${dataUrl}" alt="Avatar">`;


                } else if (presetKey === 'banner' || presetKey === 'offline') {


                    elements.previewBannerBg.style.backgroundImage = `url(${dataUrl})`;


                    elements.previewBannerBg.innerHTML = '';


                } else if (presetKey === 'panel') {


                    elements.previewPanelImg.innerHTML = `<img src="${dataUrl}" alt="Panel">`;


                } else if (presetKey === 'emote') {


                    


                } else if (presetKey === 'badge') {


                    


                } else if (presetKey === 'points') {


                    if (elements.previewPointsButton) elements.previewPointsButton.innerHTML = `<img src="${dataUrl}" alt="Points">`;


                    if (elements.previewPointsPopupIcon) elements.previewPointsPopupIcon.innerHTML = `<img src="${dataUrl}" alt="Points Large">`;


                }


            } else {


                resetMockupPlaceholders();


            }


        }





        function resetMockupPlaceholders() {


            elements.previewAvatarCircle.innerHTML = `<i data-lucide="user" class="avatar-placeholder-icon"></i>`;


            elements.previewBannerBg.style.backgroundImage = 'none';


            elements.previewBannerBg.innerHTML = `<span class="banner-empty-text">ここにプロフィールバナーが表示されます (1200x480)</span>`;


            elements.previewPanelImg.innerHTML = `<span class="panel-empty-text">情報パネル<br>(320x200)</span>`;


            


            


            if (elements.previewPointsButton) elements.previewPointsButton.innerHTML = `<div class="points-empty-slot">★</div>`;


            if (elements.previewPointsPopupIcon) elements.previewPointsPopupIcon.innerHTML = `<div class="points-empty-slot-large">★</div>`;


            lucide.createIcons();


        }





        // ==========================================================================


        // 6. マウスドラッグ ＆ インタラクティブジェスチャー


        // ==========================================================================


        function handleMouseDown(e) {


            const activeImg = getActiveImage();


            if (!activeImg) return;


            


            const mousePos = getCanvasMousePosition(e);


            


            if (activeImg.textEnabled && isMouseOnText(mousePos.x, mousePos.y)) {


                state.dragTarget = 'text';


                state.dragStartTextX = activeImg.textX;


                state.dragStartTextY = activeImg.textY;


            } else {


                state.dragTarget = 'image';


                state.dragStartImgX = activeImg.imgX;


                state.dragStartImgY = activeImg.imgY;


            }


            


            state.isDragging = true;


            state.lastMouseX = mousePos.x;


            state.lastMouseY = mousePos.y;


            elements.canvas.style.cursor = 'grabbing';


        }





        function handleMouseMove(e) {


            const activeImg = getActiveImage();


            if (!activeImg) return;





            if (!state.isDragging) {


                const mousePos = getCanvasMousePosition(e);


                if (activeImg.textEnabled && isMouseOnText(mousePos.x, mousePos.y)) {


                    elements.canvas.style.cursor = 'move';


                } else {


                    elements.canvas.style.cursor = 'grab';


                }


                return;


            }


            


            const mousePos = getCanvasMousePosition(e);


            const dx = mousePos.x - state.lastMouseX;


            const dy = mousePos.y - state.lastMouseY;


            


            if (state.dragTarget === 'text') {


                activeImg.textX += dx;


                activeImg.textY += dy;


            } else {


                activeImg.imgX += dx;


                activeImg.imgY += dy;


            }


            


            state.lastMouseX = mousePos.x;


            state.lastMouseY = mousePos.y;


            draw();


        }





        function handleMouseUp() {


            state.isDragging = false;


            state.dragTarget = null;


            const activeImg = getActiveImage();


            if (activeImg) {


                elements.canvas.style.cursor = 'grab';


            }


        }





        function getCanvasMousePosition(e) {


            const rect = elements.canvas.getBoundingClientRect();


            const scaleX = elements.canvas.width / rect.width;


            const scaleY = elements.canvas.height / rect.height;


            return {


                x: (e.clientX - rect.left) * scaleX,


                y: (e.clientY - rect.top) * scaleY


            };


        }





        function isMouseOnText(mx, my) {


            const activeImg = getActiveImage();


            if (!activeImg) return false;


            


            ctx.save();


            ctx.font = `${activeImg.strokeWidth > 0 ? 'bold' : ''} ${activeImg.fontSize}px ${activeImg.fontFamily}`;


            ctx.textAlign = 'center';


            ctx.textBaseline = 'middle';


            


            const metrics = ctx.measureText(activeImg.text);


            const textWidth = metrics.width;


            const textHeight = activeImg.fontSize;


            


            const textDrawX = elements.canvas.width / 2 + activeImg.textX;


            const textDrawY = elements.canvas.height / 2 + activeImg.textY;


            


            ctx.restore();


            


            return (


                mx >= textDrawX - textWidth / 2 - 10 &&


                mx <= textDrawX + textWidth / 2 + 10 &&


                my >= textDrawY - textHeight / 2 - 10 &&


                my <= textDrawY + textHeight / 2 + 10


            );


        }





        // ==========================================================================


        // 7. エクスポート ＆ ZIP生成処理


        // ==========================================================================


        function exportSingleImage() {


            const activeImg = getActiveImage();


            if (!activeImg) return;


            


            const preset = PRESETS[activeImg.presetKey];


            const dataUrl = elements.canvas.toDataURL('image/png');


            


            let filename;


            if (preset.type === 'single') {


                filename = `${preset.prefix}_${activeImg.name}.png`;


            } else {


                filename = `${preset.prefix}_${activeImg.name}_${preset.width}x${preset.height}.png`;


            }


            


            const link = document.createElement('a');


            link.download = filename;


            link.href = dataUrl;


            link.click();


        }





        function updateFilenamePreview() {


            if (!elements.filenamePreviewList) return;


            if (presetSelector && activeImg) { presetSelector.value = activeImg.presetKey || "profile_icon"; }


            elements.filenamePreviewList.innerHTML = '';


            


            const activeImg = getActiveImage();


            if (!activeImg) {


                const placeholder = document.createElement('div');


                placeholder.className = 'preview-filename-item';


                placeholder.style.borderLeftColor = 'var(--border-color)';


                placeholder.style.opacity = '0.5';


                placeholder.textContent = '編集中の画像がありません';


                elements.filenamePreviewList.appendChild(placeholder);


                return;


            }


            


            const checkedCheckboxes = document.querySelectorAll('.batch-preset-checkbox:checked');


            if (checkedCheckboxes.length === 0) {


                const placeholder = document.createElement('div');


                placeholder.className = 'preview-filename-item';


                placeholder.style.borderLeftColor = 'var(--border-color)';


                placeholder.style.opacity = '0.5';


                placeholder.textContent = '用途が選択されていません';


                elements.filenamePreviewList.appendChild(placeholder);


                return;


            }


            


            checkedCheckboxes.forEach(cb => {


                const presetKey = cb.value;


                const preset = PRESETS[presetKey];


                if (!preset) return;


                


                if (preset.type === 'single') {


                    const filename = `${preset.prefix}_${activeImg.name}.png`;


                    const item = document.createElement('div');


                    item.className = 'preview-filename-item';


                    item.textContent = filename;


                    elements.filenamePreviewList.appendChild(item);


                } else {


                    preset.exportSizes.forEach(size => {


                        const filename = `${preset.prefix}_${activeImg.name}_${size}x${size}.png`;


                        const item = document.createElement('div');


                        item.className = 'preview-filename-item';


                        item.textContent = filename;


                        elements.filenamePreviewList.appendChild(item);


                    });


                }


            });


        }





        function exportActiveImageMultiPresets() {


            const activeImg = getActiveImage();


            if (!activeImg) return;


            


            const checkedCheckboxes = document.querySelectorAll('.batch-preset-checkbox:checked');


            if (checkedCheckboxes.length === 0) {


                alert('出力する用途を少なくとも1つ選択してください。');


                return;


            }


            


            const zip = new JSZip();


            const offCanvas = document.createElement('canvas');


            const offCtx = offCanvas.getContext('2d');


            


            checkedCheckboxes.forEach(cb => {


                const presetKey = cb.value;


                const preset = PRESETS[presetKey];


                if (!preset) return;


                


                offCanvas.width = preset.width;


                offCanvas.height = preset.height;


                offCtx.clearRect(0, 0, preset.width, preset.height);


                


                if (activeImg.img) {


                    offCtx.save();


                    offCtx.translate(preset.width / 2 + activeImg.imgX, preset.height / 2 + activeImg.imgY);


                    offCtx.rotate((activeImg.imgRotation * Math.PI) / 180);


                    const drawW = activeImg.img.width * activeImg.imgScale;


                    const drawH = activeImg.img.height * activeImg.imgScale;


                    offCtx.drawImage(activeImg.img, -drawW / 2, -drawH / 2, drawW, drawH);


                    offCtx.restore();


                }


                


                if (activeImg.textEnabled && activeImg.text.trim() !== '') {


                    offCtx.save();


                    offCtx.font = `${activeImg.strokeWidth > 0 ? 'bold' : ''} ${activeImg.fontSize}px ${activeImg.fontFamily}`;


                    offCtx.textAlign = 'center';


                    offCtx.textBaseline = 'middle';


                    const textDrawX = preset.width / 2 + activeImg.textX;


                    const textDrawY = preset.height / 2 + activeImg.textY;


                    if (activeImg.strokeWidth > 0) {


                        offCtx.strokeStyle = activeImg.strokeColor;


                        offCtx.lineWidth = activeImg.strokeWidth;


                        offCtx.lineJoin = 'round';


                        offCtx.lineCap = 'round';


                        offCtx.strokeText(activeImg.text, textDrawX, textDrawY);


                    }


                    offCtx.fillStyle = activeImg.textColor;


                    offCtx.fillText(activeImg.text, textDrawX, textDrawY);


                    offCtx.restore();


                }


                


                if (preset.type === 'single') {


                    const imgUrl = offCanvas.toDataURL('image/png');


                    const base64Data = imgUrl.split(',')[1];


                    zip.file(`${preset.prefix}_${activeImg.name}.png`, base64Data, { base64: true });


                } else {


                    preset.exportSizes.forEach(size => {


                        const resizeCanvas = document.createElement('canvas');


                        resizeCanvas.width = size;


                        resizeCanvas.height = size;


                        const resizeCtx = resizeCanvas.getContext('2d');


                        resizeCtx.imageSmoothingEnabled = true;


                        resizeCtx.imageSmoothingQuality = 'high';


                        resizeCtx.drawImage(offCanvas, 0, 0, offCanvas.width, offCanvas.height, 0, 0, size, size);


                        


                        const resizeUrl = resizeCanvas.toDataURL('image/png');


                        const base64Data = resizeUrl.split(',')[1];


                        zip.file(`${preset.prefix}_${activeImg.name}_${size}x${size}.png`, base64Data, { base64: true });


                    });


                }


            });


            


            zip.generateAsync({ type: 'blob' }).then(function(content) {


                const url = window.URL.createObjectURL(content);


                const link = document.createElement('a');


                link.download = `twitch_resized_${activeImg.name}.zip`;


                link.href = url;


                link.click();


                setTimeout(() => window.URL.revokeObjectURL(url), 1000);


            });


        }





        function exportAllQueueMultiPresets() {


            if (state.queue.length === 0) return;


            


            const checkedCheckboxes = document.querySelectorAll('.batch-preset-checkbox:checked');


            if (checkedCheckboxes.length === 0) {


                alert('出力する用途を少なくとも1つ選択してください。');


                return;


            }


            


            const zip = new JSZip();


            const offCanvas = document.createElement('canvas');


            const offCtx = offCanvas.getContext('2d');


            


            state.queue.forEach(item => {


                checkedCheckboxes.forEach(cb => {


                    const presetKey = cb.value;


                    const preset = PRESETS[presetKey];


                    if (!preset) return;


                    


                    offCanvas.width = preset.width;


                    offCanvas.height = preset.height;


                    offCtx.clearRect(0, 0, preset.width, preset.height);


                    


                    if (item.img) {


                        offCtx.save();


                        offCtx.translate(preset.width / 2 + item.imgX, preset.height / 2 + item.imgY);


                        offCtx.rotate((item.imgRotation * Math.PI) / 180);


                        const drawW = item.img.width * item.imgScale;


                        const drawH = item.img.height * item.imgScale;


                        offCtx.drawImage(item.img, -drawW / 2, -drawH / 2, drawW, drawH);


                        offCtx.restore();


                    }


                    


                    if (item.textEnabled && item.text.trim() !== '') {


                        offCtx.save();


                        offCtx.font = `${item.strokeWidth > 0 ? 'bold' : ''} ${item.fontSize}px ${item.fontFamily}`;


                        offCtx.textAlign = 'center';


                        offCtx.textBaseline = 'middle';


                        const textDrawX = preset.width / 2 + item.textX;


                        const textDrawY = preset.height / 2 + item.textY;


                        if (item.strokeWidth > 0) {


                            offCtx.strokeStyle = item.strokeColor;


                            offCtx.lineWidth = item.strokeWidth;


                            offCtx.lineJoin = 'round';


                            offCtx.lineCap = 'round';


                            offCtx.strokeText(item.text, textDrawX, textDrawY);


                        }


                        offCtx.fillStyle = item.textColor;


                        offCtx.fillText(item.text, textDrawX, textDrawY);


                        offCtx.restore();


                    }


                    


                    if (preset.type === 'single') {


                        const imgUrl = offCanvas.toDataURL('image/png');


                        const base64Data = imgUrl.split(',')[1];


                        zip.file(`${preset.prefix}_${item.name}.png`, base64Data, { base64: true });


                    } else {


                        preset.exportSizes.forEach(size => {


                            const resizeCanvas = document.createElement('canvas');


                            resizeCanvas.width = size;


                            resizeCanvas.height = size;


                            const resizeCtx = resizeCanvas.getContext('2d');


                            resizeCtx.imageSmoothingEnabled = true;


                            resizeCtx.imageSmoothingQuality = 'high';


                            resizeCtx.drawImage(offCanvas, 0, 0, offCanvas.width, offCanvas.height, 0, 0, size, size);


                            


                            const resizeUrl = resizeCanvas.toDataURL('image/png');


                            const base64Data = resizeUrl.split(',')[1];


                            zip.file(`${preset.prefix}_${item.name}_${size}x${size}.png`, base64Data, { base64: true });


                        });


                    }


                });


            });


            


            zip.generateAsync({ type: 'blob' }).then(function(content) {


                const url = window.URL.createObjectURL(content);


                const link = document.createElement('a');


                link.download = 'twitch_all_presets_batch.zip';


                link.href = url;


                link.click();


                setTimeout(() => window.URL.revokeObjectURL(url), 1000);


            });


        }





        // ==========================================================================


        // 8. キュー内の全画像をZIPで一括エクスポート


        // ==========================================================================


        function exportAllImagesZip() {


            if (state.queue.length === 0) {


                alert('キューに画像がありません。');


                return;


            }


            const preset = PRESETS[state.currentPreset];


            if (!preset) {


                alert('有効なプリセットが選択されていません。');


                return;


            }


            


            const zip = new JSZip();


            const offCanvas = document.createElement('canvas');


            const offCtx = offCanvas.getContext('2d');


            


            state.queue.forEach(item => {


                offCanvas.width = preset.width;


                offCanvas.height = preset.height;


                offCtx.clearRect(0, 0, preset.width, preset.height);


                


                if (item.img) {


                    offCtx.save();


                    offCtx.translate(preset.width / 2 + item.imgX, preset.height / 2 + item.imgY);


                    offCtx.rotate((item.imgRotation * Math.PI) / 180);


                    const drawW = item.img.width * item.imgScale;


                    const drawH = item.img.height * item.imgScale;


                    offCtx.drawImage(item.img, -drawW / 2, -drawH / 2, drawW, drawH);


                    offCtx.restore();


                }


                


                if (item.textEnabled && item.text.trim() !== '') {


                    offCtx.save();


                    offCtx.font = `${item.strokeWidth > 0 ? 'bold' : ''} ${item.fontSize}px ${item.fontFamily}`;


                    offCtx.textAlign = 'center';


                    offCtx.textBaseline = 'middle';


                    const textDrawX = preset.width / 2 + item.textX;


                    const textDrawY = preset.height / 2 + item.textY;


                    if (item.strokeWidth > 0) {


                        offCtx.strokeStyle = item.strokeColor;


                        offCtx.lineWidth = item.strokeWidth;


                        offCtx.lineJoin = 'round';


                        offCtx.lineCap = 'round';


                        offCtx.strokeText(item.text, textDrawX, textDrawY);


                    }


                    offCtx.fillStyle = item.textColor;


                    offCtx.fillText(item.text, textDrawX, textDrawY);


                    offCtx.restore();


                }


                


                if (preset.type === 'single') {


                    const imgUrl = offCanvas.toDataURL('image/png');


                    const base64Data = imgUrl.split(',')[1];


                    zip.file(`${preset.prefix}_${item.name}.png`, base64Data, { base64: true });


                } else {


                    preset.exportSizes.forEach(size => {


                        const resizeCanvas = document.createElement('canvas');


                        resizeCanvas.width = size;


                        resizeCanvas.height = size;


                        const resizeCtx = resizeCanvas.getContext('2d');


                        resizeCtx.imageSmoothingEnabled = true;


                        resizeCtx.imageSmoothingQuality = 'high';


                        resizeCtx.drawImage(offCanvas, 0, 0, offCanvas.width, offCanvas.height, 0, 0, size, size);


                        


                        const resizeUrl = resizeCanvas.toDataURL('image/png');


                        const base64Data = resizeUrl.split(',')[1];


                        zip.file(`${preset.prefix}_${item.name}_${size}x${size}.png`, base64Data, { base64: true });


                    });


                }


            });


            


            zip.generateAsync({ type: 'blob' }).then(function(content) {


                const url = window.URL.createObjectURL(content);


                const link = document.createElement('a');


                link.download = `twitch_queue_${preset.prefix}_all.zip`;


                link.href = url;


                link.click();


                setTimeout(() => window.URL.revokeObjectURL(url), 1000);


            });


        }


        // ==========================================================================


        // 14. [NEW] 法的モーダル制御 ＆ 日本語ポリシーデータ


        // ==========================================================================


        const LEGAL_DOCS = {


            privacy: {


                title: 'プライバシーポリシー',


                icon: 'shield',


                content: `


                    <p>当ツール（以下、「本サービス」）は、ユーザーのプライバシーの保護を最優先事項として運営しております。</p>


                    


                    <h3>1. 完全ローカル処理の遵守</h3>


                    <p>本サービスはHTML5 Canvas技術を利用し、<strong>ユーザーがアップロードしたすべての画像データをユーザーのブラウザ（ローカル）内のみで処理します。</strong> 画像データが外部のサーバーに送信、保存、あるいは解析されることは一切ありません。完全オフライン環境であっても同様に動作します。</p>


                    


                    <h3>2. 広告配信サービスについて</h3>


                    <p>本サービスでは、運営費用を補うために第三者配信の広告サービス（Google AdSense等）を利用しています。これらの広告配信事業者は、ユーザーの興味に応じた商品やサービスの広告を表示するため、本サービスや他のウェブサイトへのアクセスに関する情報「Cookie」（氏名、住所、メールアドレス、電話番号は含まれません）を使用することがあります。</p>


                    


                    <h3>3. 利用状況の解析について</h3>


                    <p>本サービスでは、サービスの改善およびユーザー体験の向上のため、個人を特定しない形でのトラフィックデータ収集を行う場合があります。ブラウザのセキュリティ設定よりCookieを無効にすることで、収集を拒否することが可能です。</p>


                    


                    <h3>4. お問い合わせ</h3>


                    <p>プライバシーポリシーに関するご質問やお問い合わせは、本ツールの配布プラットフォーム、または「免責事項・お問い合わせ」に記載の窓口までご連絡ください。</p>


                `


            },


            terms: {


                title: '利用規約',


                icon: 'file-text',


                content: `


                    <p>この利用規約（以下、「本規約」）は、本リサイズツール（以下、「本サービス」）の利用条件を定めるものです。</p>


                    


                    <h3>1. 利用許諾</h3>


                    <p>ユーザーは、本規約に従って本サービスを個人的、あるいは商用（Twitch配信でのスタンプやバッジ等への使用）の目的で無償で利用することができます。ソースコードの複製や改造、自己のサイトでの公開も非営利・個人利用に限り自由に行っていただけます。</p>


                    


                    <h3>2. 禁止事項</h3>


                    <p>ユーザーは、本サービスの利用にあたり、以下の行為を行ってはなりません。</p>


                    <ul>


                        <li>本サービスの意図的な不具合の利用や攻撃行為</li>


                        <li>本サービスのサーバーリソースを悪用する行為</li>


                        <li>公序良俗に反する画像、他者の知的財産権を侵害する画像の編集・作成</li>


                        <li>その他、運営が不適切と判断する行為</li>


                    </ul>


                    


                    <h3>3. 免責について</h3>


                    <p>本サービスのソースコードの改変・再配布について、開発元は何ら制限を設けません。ただし、それによって生じた損害については一切の責任を免れるものとします。</p>


                `


            },


            disclaimer: {


                title: '免責事項・お問い合わせ',


                icon: 'mail',


                content: `


                    <h3>免責事項</h3>


                    <p>本サービスで提供される変換結果、エクスポートされたZIPファイルの完全性、安全性、有用性について、運営は一切の保証を行いません。</p>


                    <p><strong>本サービスのご利用によりユーザーまたは第三者に生じた損害、不利益、データ消失、Twitchアカウントに対する措置等について、運営は一切の責任を負いません。</strong> ユーザー自身の責任においてご利用いただきますようお願い申し上げます。</p>


                    


                    <h3>不具合報告・お問い合わせ</h3>


                    <p>本ツールはオープンに無料公開されています。機能のバグ報告や機能追加のご要望がございましたら、以下の方法でお気軽にご連絡ください。</p>


                    <ul>


                        <li><strong>GitHub等の配布リポジトリ:</strong> IssueまたはPull Request（開発版公開元）</li>


                        <li><strong>SNS/E-mail:</strong> 配布元のウェブサイト、またはプロフィールの連絡先まで</li>


                    </ul>


                    <p>※個別のご質問やカスタム機能の対応にはお時間をいただく、あるいは対応できない場合がございます。予めご了承ください。</p>


                `


            }


        };





        let modalElements = {};





        function setupModalEvents() {


            modalElements = {


                modal: document.getElementById('legal-modal'),


                overlayBg: document.getElementById('modal-overlay-bg'),


                titleText: document.getElementById('modal-title-text'),


                bodyContent: document.getElementById('modal-body-content'),


                closeBtn: document.getElementById('modal-close-btn'),


                okBtn: document.getElementById('modal-ok-btn'),


                linkPrivacy: document.getElementById('link-privacy'),


                linkTerms: document.getElementById('link-terms'),


                linkDisclaimer: document.getElementById('link-disclaimer')


            };





            if (!modalElements.modal) return;





            modalElements.linkPrivacy?.addEventListener('click', (e) => { e.preventDefault(); openLegalModal('privacy'); });


            modalElements.linkTerms?.addEventListener('click', (e) => { e.preventDefault(); openLegalModal('terms'); });


            modalElements.linkDisclaimer?.addEventListener('click', (e) => { e.preventDefault(); openLegalModal('disclaimer'); });





            modalElements.closeBtn?.addEventListener('click', closeLegalModal);


            modalElements.okBtn?.addEventListener('click', closeLegalModal);


            modalElements.overlayBg?.addEventListener('click', closeLegalModal);





            window.addEventListener('keydown', (e) => {


                if (e.key === 'Escape' && !modalElements.modal.classList.contains('hidden')) {


                    closeLegalModal();


                }


            });


        }





        function openLegalModal(docKey) {


            const doc = LEGAL_DOCS[docKey];


            if (!doc) return;





            modalElements.titleText.innerHTML = `<i data-lucide="${doc.icon}"></i> ${doc.title}`;


            modalElements.bodyContent.innerHTML = doc.content;


            


            lucide.createIcons();


            modalElements.modal.classList.remove('hidden');


            document.body.style.overflow = 'hidden'; // 背景スクロール固定


        }





        function closeLegalModal() {


            if (modalElements.modal) {


                modalElements.modal.classList.add('hidden');


                document.body.style.overflow = '';


            }


        }





        // アプリの起動


        document.addEventListener('DOMContentLoaded', init);

function drawTextOverlay(ctx, activeItem) {
            if (!activeItem || !activeItem.textEnabled || !activeItem.text) return;
            
            const text = activeItem.text;
            const textProps = activeItem.textProps || {};
            const fontSize = textProps.size || activeItem.fontSize || 32;
            const fontFamily = textProps.font || activeItem.fontFamily || "'Noto Sans JP', sans-serif";
            const textColor = textProps.color || activeItem.textColor || '#ffffff';
            const letterSpacing = parseInt(textProps.letterSpacing || 0, 10);
            const curveVal = parseInt(textProps.curve || 0, 10);
            
            ctx.save();
            ctx.font = `bold ${fontSize}px ${fontFamily}`;
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            
            const posX = ctx.canvas.width / 2 + (activeItem.textX || 0);
            const posY = ctx.canvas.height / 2 + (activeItem.textY || 0);
            
            ctx.strokeStyle = '#000000';
            ctx.lineWidth = Math.max(4, fontSize / 7);
            ctx.lineJoin = 'round';
            ctx.fillStyle = textColor;
            
            const chars = text.split('');
            if (chars.length === 0) {
                ctx.restore();
                return;
            }

            if (curveVal !== 0 && chars.length > 1) {
                const radius = Math.max(80, 2500 / Math.abs(curveVal));
                const direction = curveVal > 0 ? 1 : -1;
                const charStepAngle = (fontSize * 0.75 + letterSpacing) / radius;
                const totalAngle = (chars.length - 1) * charStepAngle;
                const startAngle = -totalAngle / 2;

                chars.forEach((ch, i) => {
                    ctx.save();
                    const angle = startAngle + i * charStepAngle;
                    const offsetX = Math.sin(angle) * radius;
                    const offsetY = (1 - Math.cos(angle)) * radius * direction;

                    ctx.translate(posX + offsetX, posY + offsetY);
                    ctx.rotate(angle * direction);

                    ctx.strokeText(ch, 0, 0);
                    ctx.fillText(ch, 0, 0);
                    ctx.restore();
                });
            } else {
                let totalW = 0;
                const charWidths = chars.map(ch => {
                    const w = ctx.measureText(ch).width;
                    totalW += w;
                    return w;
                });
                totalW += (chars.length - 1) * letterSpacing;

                let startX = posX - totalW / 2;
                chars.forEach((ch, i) => {
                    const charW = charWidths[i];
                    const drawX = startX + charW / 2;
                    ctx.strokeText(ch, drawX, posY);
                    ctx.fillText(ch, drawX, posY);
                    startX += charW + letterSpacing;
                });
            }
            
            ctx.restore();
        }
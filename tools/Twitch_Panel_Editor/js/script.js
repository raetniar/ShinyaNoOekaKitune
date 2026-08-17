// Elements
const editorTextarea = document.getElementById('editor-textarea');
const previewPanel = document.getElementById('preview-panel');
const titleInput = document.getElementById('input-title');
const saveStatus = document.getElementById('save-status');
const historyList = document.getElementById('history-list');
const btnNew = document.getElementById('btn-new');
const btnExport = document.getElementById('btn-export');
const inputImport = document.getElementById('input-import');
const inputImageFile = document.getElementById('input-image-file');
const btnClearImage = document.getElementById('btn-clear-image');
const inputImageAlt = document.getElementById('input-image-alt');
const inputImageLink = document.getElementById('input-image-link');
const imageFileName = document.getElementById('image-file-name');
const previewPanelLink = document.getElementById('preview-panel-link');
const previewPanelImage = document.getElementById('preview-panel-image');
const previewPanelImageNolink = document.getElementById('preview-panel-image-nolink');
const toggleSidebarBtn = document.getElementById('toggle-sidebar-btn');
const togglePreviewBtn = document.getElementById('toggle-preview-btn');
const sidebar = document.querySelector('.sidebar');
const previewSection = document.querySelector('.preview-section');
const toolbarBtns = document.querySelectorAll('.btn-toolbar[data-action]');
const inputImageHeight = document.getElementById('input-image-height');
const selectImageBg = document.getElementById('select-image-bg');
const btnDownloadImage = document.getElementById('btn-download-image');

// State
let currentId = null;
let saveTimeout = null;
let currentImageData = null;
let originalImageObj = null;

// Constants
const STORAGE_KEY = 'twitch_panel_editor_history';
const THEME_KEY = 'twitch_panel_editor_theme';

// Global Panel Toggle/Close Functions
window.toggleSidebar = function() {
    const sb = document.querySelector('.sidebar');
    if (sb) sb.classList.toggle('collapsed');
};

window.closeSidebar = function() {
    const sb = document.querySelector('.sidebar');
    if (sb) sb.classList.add('collapsed');
};

window.togglePreview = function() {
    const ps = document.querySelector('.preview-section');
    if (ps) ps.classList.toggle('collapsed');
};

window.closePreview = function() {
    const ps = document.querySelector('.preview-section');
    if (ps) ps.classList.add('collapsed');
};

// Initialize
function init() {
    // Configure Marked.js
    marked.setOptions({
        breaks: true, // Twitchの現在の仕様に合わせ、シングル改行をそのまま改行として反映
        gfm: true      // GitHub Flavored Markdown
    });

    // Load theme
    const savedTheme = 'light'; // Light mode fixed as default
    updateThemeUI(savedTheme);

    // Load History
    loadHistoryList();

    // Event Listeners
    editorTextarea.addEventListener('input', handleInput);
    titleInput.addEventListener('input', handleInput);
    inputImageAlt.addEventListener('input', handleInput);
    inputImageLink.addEventListener('input', handleInput);
    btnNew.addEventListener('click', createNew);
    btnExport.addEventListener('click', exportBackup);
    inputImport.addEventListener('change', importBackup);
    inputImageFile.addEventListener('change', handleImageUpload);
    btnClearImage.addEventListener('click', clearImage);
    inputImageHeight?.addEventListener('input', () => { if (originalImageObj) processImage(); });
    selectImageBg?.addEventListener('change', () => { if (originalImageObj) processImage(); });
    btnDownloadImage?.addEventListener('click', downloadImage);
    
    // Header Theme Toggle Event
    const headerThemeToggle = document.getElementById('header-theme-toggle');
    if (headerThemeToggle) {
        headerThemeToggle.addEventListener('click', () => {
            const currentTheme = localStorage.getItem(THEME_KEY) || 'light';
            const newTheme = currentTheme === 'light' ? 'dark' : 'light';
            updateThemeUI(newTheme);
        });
    }

    function updateToggleButtonVisibility() {
        if (toggleSidebarBtn) toggleSidebarBtn.style.display = '';
        if (togglePreviewBtn) togglePreviewBtn.style.display = '';
    }

    toggleSidebarBtn?.addEventListener('click', () => {
        window.toggleSidebar();
    });
    
    togglePreviewBtn?.addEventListener('click', () => {
        window.togglePreview();
    });

    // パネル側の閉じるボタン
    const btnCloseSidebar = document.getElementById('btn-close-sidebar');
    if(btnCloseSidebar) {
        btnCloseSidebar.addEventListener('click', () => {
            window.closeSidebar();
        });
    }

    const btnClosePreview = document.getElementById('btn-close-preview');
    if(btnClosePreview) {
        btnClosePreview.addEventListener('click', () => {
            window.closePreview();
        });
    }
    
    // Help Modal
    const btnHelpTwitch = document.getElementById('btn-help-twitch');
    const helpModal = document.getElementById('help-modal');
    const closeHelpModal = document.getElementById('close-help-modal');
    if (btnHelpTwitch) {
        btnHelpTwitch.addEventListener('click', () => {
            helpModal.classList.add('show');
        });
    }
    if (closeHelpModal) {
        closeHelpModal.addEventListener('click', () => {
            helpModal.classList.remove('show');
        });
    }
    window.addEventListener('click', (e) => {
        if (e.target === helpModal) {
            helpModal.classList.remove('show');
        }
    });

    // Responsive auto-collapse
    const mqlSidebar = window.matchMedia('(max-width: 1000px)');
    const mqlPreview = window.matchMedia('(max-width: 700px)');

    function handleMqlSidebar(e) {
        if (e.matches) {
            sidebar.classList.add('collapsed');
        } else {
            sidebar.classList.remove('collapsed');
        }
        updateToggleButtonVisibility();
    }
    
    function handleMqlPreview(e) {
        if (e.matches) {
            previewSection.classList.add('collapsed');
        } else {
            previewSection.classList.remove('collapsed');
        }
        updateToggleButtonVisibility();
    }

    // Initialize state
    if (mqlSidebar.matches) sidebar.classList.add('collapsed');
    if (mqlPreview.matches) previewSection.classList.add('collapsed');
    updateToggleButtonVisibility();

    // Add listeners
    if (mqlSidebar.addEventListener) {
        mqlSidebar.addEventListener('change', handleMqlSidebar);
        mqlPreview.addEventListener('change', handleMqlPreview);
    } else {
        // Fallback for older browsers
        mqlSidebar.addListener(handleMqlSidebar);
        mqlPreview.addListener(handleMqlPreview);
    }

    toolbarBtns.forEach(btn => {
        btn.addEventListener('mousedown', (e) => {
            e.preventDefault(); // フォーカスの消失を防ぐ
        });
        btn.addEventListener('click', (e) => {
            const action = e.currentTarget.getAttribute('data-action');
            insertMarkdown(action);
        });
    });

    // テンプレート挿入ボタン
    const templates = {
        about: "# 自己紹介\n\nはじめまして！〇〇と申します。\n普段はFPSやRPGを中心に配信しています！\n\n気軽にコメントしてね！",
        specs: "# PCスペック\n\n- **CPU**: \n- **GPU**: \n- **メモリ**: \n- **マウス**: \n- **キーボード**: \n- **マイク**: ",
        links: "# リンク集\n\n- [Twitter(X)](https://x.com/)\n- [YouTube](https://youtube.com/)\n- [欲しいものリスト](https://amazon.co.jp/)",
        rules: "# 配信ルール\n\nみんなが楽しめるように以下のルールを守ってね！\n\n1. 他の人が不快になるコメントは禁止\n2. 配信に関係のない話題（自分語り等）は控えめに\n3. 荒らしはスルーでお願いします",
        games: "# よく遊ぶゲーム\n\n- VALORANT\n- Apex Legends\n- 雑談\n- その他色々！"
    };

    document.querySelectorAll('.btn-template').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const templateKey = e.target.getAttribute('data-template');
            if(templates[templateKey]) {
                const text = templates[templateKey];
                const start = editorTextarea.selectionStart;
                const end = editorTextarea.selectionEnd;
                const currentVal = editorTextarea.value;
                editorTextarea.value = currentVal.substring(0, start) + text + "\n\n" + currentVal.substring(end);
                editorTextarea.selectionStart = editorTextarea.selectionEnd = start + text.length + 2;
                editorTextarea.focus();
                handleInput();
                
                // 挿入後、ドロップダウンを自動で閉じる
                const details = e.target.closest('details');
                if(details) details.removeAttribute('open');
            }
        });
    });

    // 全文コピー機能 (ファイルプロトコル・セキュリティ制限環境フル対応)
    const copyToClipboard = async (btn) => {
        const text = editorTextarea ? editorTextarea.value : '';
        if (!text || text.trim() === '') {
            alert('コピーするテキストがありません。');
            return;
        }

        const showSuccess = () => {
            if (!btn) return;
            const originalText = btn.innerHTML;
            btn.innerHTML = '<i class="fa-solid fa-check" style="color:#20c997;"></i> コピー完了';
            btn.style.color = "#20c997";
            setTimeout(() => {
                btn.innerHTML = originalText;
                btn.style.color = "";
            }, 2000);
        };

        let copied = false;

        // 1. クリップボードAPIを試行
        if (navigator.clipboard) {
            try {
                await navigator.clipboard.writeText(text);
                copied = true;
            } catch (e) {
                console.warn('Clipboard API fallback:', e);
            }
        }

        // 2. 画面上のtextarea選択によるexecCommand試行（off-screen不具合回避）
        if (!copied && editorTextarea) {
            try {
                editorTextarea.focus();
                editorTextarea.select();
                copied = document.execCommand('copy');
            } catch (e) {
                console.warn('execCommand fallback:', e);
            }
        }

        if (copied) {
            showSuccess();
        } else {
            // 3. ブラウザ権限制限時のプロンプト表示フォールバック
            window.prompt('以下を Ctrl+C (または Cmd+C) でコピーしてください:', text);
            showSuccess();
        }
    };

    const btnCopyAll = document.getElementById('btn-copy-all');
    if (btnCopyAll) {
        btnCopyAll.addEventListener('mousedown', (e) => e.preventDefault());
        btnCopyAll.addEventListener('click', () => {
            copyToClipboard(btnCopyAll);
        });
    }
}

// Insert Markdown from Toolbar
function insertMarkdown(action) {
    const start = editorTextarea.selectionStart;
    const end = editorTextarea.selectionEnd;
    const text = editorTextarea.value;
    const selectedText = text.substring(start, end);
    let before = '';
    let after = '';
    let defaultText = '';

    switch(action) {
        case 'bold': before = '**'; after = '**'; defaultText = '太字'; break;
        case 'italic': before = '*'; after = '*'; defaultText = '斜体'; break;
        case 'h1': before = '# '; defaultText = '見出し'; break;
        case 'link': 
            if (selectedText.startsWith('http://') || selectedText.startsWith('https://')) {
                before = '['; after = '](' + selectedText + ')'; defaultText = 'リンクテキスト';
            } else {
                before = '['; after = '](https://)'; defaultText = 'リンクテキスト';
            }
            break;
        case 'list': before = '- '; defaultText = 'リスト項目'; break;
        case 'ordered-list': before = '1. '; defaultText = 'リスト項目'; break;
        case 'quote': before = '> '; defaultText = ''; break;
        case 'code': before = '`'; after = '`'; defaultText = 'コード'; break;
    }

    let insertText = selectedText || defaultText;
    let finalCursorStart, finalCursorEnd;

    if (action === 'link' && (selectedText.startsWith('http://') || selectedText.startsWith('https://'))) {
        // URLを選択してリンクボタンを押した場合、テキストはURL自身ではなく「リンクテキスト」などのプレースホルダーにする
        insertText = defaultText;
        editorTextarea.value = text.substring(0, start) + before + insertText + after + text.substring(end);
        finalCursorStart = start + before.length;
        finalCursorEnd = finalCursorStart + insertText.length;
    } else if (action === 'link') {
        // 通常のリンク挿入（テキストを選択している場合、または何も選択していない場合）
        editorTextarea.value = text.substring(0, start) + before + insertText + after + text.substring(end);
        if (selectedText) {
            // URL部分を選択状態にする
            finalCursorStart = start + before.length + insertText.length + ']('.length;
            finalCursorEnd = finalCursorStart + 'https://'.length;
        } else {
            // リンクテキスト部分を選択状態にする
            finalCursorStart = start + before.length;
            finalCursorEnd = finalCursorStart + defaultText.length;
        }
    } else {
        editorTextarea.value = text.substring(0, start) + before + insertText + after + text.substring(end);
        if (selectedText) {
            finalCursorStart = start + before.length;
            finalCursorEnd = finalCursorStart + selectedText.length;
        } else {
            finalCursorStart = start + before.length;
            finalCursorEnd = finalCursorStart + defaultText.length;
        }
    }
    
    editorTextarea.focus();
    editorTextarea.setSelectionRange(finalCursorStart, finalCursorEnd);
    
    handleInput();
}

// Render Markdown and Image to Preview
function renderPreview() {
    // Markdown
    const rawMarkdown = editorTextarea.value;
    const html = marked.parse(rawMarkdown);
    const sanitizedHtml = DOMPurify.sanitize(html);
    previewPanel.innerHTML = sanitizedHtml;

    // Image
    if (currentImageData) {
        const linkUrl = inputImageLink.value.trim();
        if (linkUrl) {
            previewPanelLink.href = linkUrl;
            previewPanelLink.style.display = 'block';
            previewPanelImage.src = currentImageData;
            previewPanelImage.alt = inputImageAlt.value;
            previewPanelImageNolink.style.display = 'none';
            previewPanelImageNolink.src = '';
        } else {
            previewPanelLink.style.display = 'none';
            previewPanelLink.href = '';
            previewPanelImageNolink.src = currentImageData;
            previewPanelImageNolink.alt = inputImageAlt.value;
            previewPanelImageNolink.style.display = 'block';
        }
    } else {
        previewPanelLink.style.display = 'none';
        previewPanelImageNolink.style.display = 'none';
        previewPanelImage.src = '';
        previewPanelImageNolink.src = '';
    }
}

// Handle Image Upload
function handleImageUpload(e) {
    const file = e.target.files[0];
    if (!file) return;

    // 画像サイズチェック (Twitch制限: 2.9MB)
    const MAX_SIZE = 2.9 * 1024 * 1024;
    if (file.size > MAX_SIZE) {
        imageFileName.innerHTML = `<span style="color: #ff4a4a;">⚠️ 制限オーバー(2.9MB超): ${file.name}</span>`;
    } else {
        imageFileName.textContent = file.name;
    }
    
    const reader = new FileReader();
    reader.onload = function(event) {
        const img = new Image();
        img.onload = function() {
            originalImageObj = img;
            processImage();
        };
        img.src = event.target.result;
    };
    reader.readAsDataURL(file);
}

// Process Image with Canvas (Resize and Padding)
function processImage() {
    if (!originalImageObj) return;

    const targetWidth = 320;
    let targetHeight = inputImageHeight ? parseInt(inputImageHeight.value) : NaN;
    
    const aspectRatio = originalImageObj.height / originalImageObj.width;
    
    // If no target height is specified, use the original aspect ratio
    if (!targetHeight || isNaN(targetHeight) || targetHeight <= 0) {
        targetHeight = Math.round(targetWidth * aspectRatio);
    }

    const canvas = document.createElement('canvas');
    canvas.width = targetWidth;
    canvas.height = targetHeight;
    const ctx = canvas.getContext('2d');

    // Fill background
    const bgColor = selectImageBg ? selectImageBg.value : 'transparent';
    if (bgColor !== 'transparent') {
        ctx.fillStyle = bgColor;
        ctx.fillRect(0, 0, targetWidth, targetHeight);
    } else {
        ctx.clearRect(0, 0, targetWidth, targetHeight);
    }

    // Calculate scale and offset for "contain" behavior
    const scale = Math.min(targetWidth / originalImageObj.width, targetHeight / originalImageObj.height);
    const drawWidth = originalImageObj.width * scale;
    const drawHeight = originalImageObj.height * scale;
    
    const offsetX = (targetWidth - drawWidth) / 2;
    const offsetY = (targetHeight - drawHeight) / 2;

    ctx.drawImage(originalImageObj, offsetX, offsetY, drawWidth, drawHeight);

    currentImageData = canvas.toDataURL('image/png');
    if (btnDownloadImage) btnDownloadImage.disabled = false;
    handleInput();
}

// Download processed image
function downloadImage() {
    if (!currentImageData) return;
    const a = document.createElement('a');
    a.href = currentImageData;
    a.download = `twitch_panel_image_${Date.now()}.png`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
}

// Clear Image
function clearImage() {
    currentImageData = null;
    originalImageObj = null;
    inputImageFile.value = '';
    imageFileName.textContent = '画像未設定';
    inputImageAlt.value = '';
    inputImageLink.value = '';
    if (btnDownloadImage) btnDownloadImage.disabled = true;
    handleInput();
}

// Handle Input with Debounce for Saving
function handleInput() {
    renderPreview();
    
    saveStatus.textContent = '保存中...';
    clearTimeout(saveTimeout);
    saveTimeout = setTimeout(() => {
        saveCurrentItem();
    }, 1000);
}

// Save Current Item to LocalStorage
function saveCurrentItem() {
    const content = editorTextarea.value;
    const title = titleInput.value.trim() || '名称未設定';
    const altText = inputImageAlt.value;
    const linkUrl = inputImageLink.value;
    
    if (!content && !titleInput.value && !currentImageData) {
        saveStatus.textContent = '';
        return; // Don't save empty drafts
    }

    let history = getHistory();
    const now = new Date().toISOString();

    if (!currentId) {
        currentId = Date.now().toString();
        history.unshift({
            id: currentId,
            title: title,
            content: content,
            imageData: currentImageData,
            imageAlt: altText,
            imageLink: linkUrl,
            updatedAt: now
        });
    } else {
        const index = history.findIndex(item => item.id === currentId);
        if (index > -1) {
            history[index].title = title;
            history[index].content = content;
            history[index].imageData = currentImageData;
            history[index].imageAlt = altText;
            history[index].imageLink = linkUrl;
            history[index].updatedAt = now;
            // Move to top
            const item = history.splice(index, 1)[0];
            history.unshift(item);
        } else {
            // Failsafe
            history.unshift({
                id: currentId,
                title: title,
                content: content,
                imageData: currentImageData,
                imageAlt: altText,
                imageLink: linkUrl,
                updatedAt: now
            });
        }
    }

    localStorage.setItem(STORAGE_KEY, JSON.stringify(history));
    saveStatus.textContent = '保存完了';
    
    // Refresh list
    renderHistoryList(history);
    
    setTimeout(() => {
        if (saveStatus.textContent === '保存完了') {
            saveStatus.textContent = '';
        }
    }, 2000);
}

// Get History from LocalStorage
function getHistory() {
    const data = localStorage.getItem(STORAGE_KEY);
    return data ? JSON.parse(data) : [];
}

// Load and Render History List
function loadHistoryList() {
    const history = getHistory();
    renderHistoryList(history);
    
    // Load most recent if available
    if (history.length > 0) {
        loadItem(history[0].id);
    } else {
        createNew();
    }
}

// HTML Escape helper to prevent XSS
function escapeHtml(unsafe) {
    return (unsafe || '').toString()
         .replace(/&/g, "&amp;")
         .replace(/</g, "&lt;")
         .replace(/>/g, "&gt;")
         .replace(/"/g, "&quot;")
         .replace(/'/g, "&#039;");
}

function renderHistoryList(history) {
    historyList.innerHTML = '';
    
    history.forEach(item => {
        const li = document.createElement('li');
        li.className = `history-item ${item.id === currentId ? 'active' : ''}`;
        
        const dateObj = new Date(item.updatedAt);
        const dateStr = `${dateObj.getMonth()+1}/${dateObj.getDate()} ${dateObj.getHours()}:${String(dateObj.getMinutes()).padStart(2, '0')}`;
        
        const safeTitle = escapeHtml(item.title);
        
        li.innerHTML = `
            <div class="history-info">
                <span class="history-title" title="${safeTitle}">${safeTitle}</span>
                <span class="history-date">${dateStr}</span>
            </div>
            <button class="btn-delete" title="削除">×</button>
        `;
        
        li.addEventListener('click', (e) => {
            if (e.target.className !== 'btn-delete') {
                loadItem(item.id);
            }
        });
        
        li.querySelector('.btn-delete').addEventListener('click', (e) => {
            e.stopPropagation();
            deleteItem(item.id);
        });
        
        historyList.appendChild(li);
    });
}

// Load Specific Item
function loadItem(id) {
    const history = getHistory();
    const item = history.find(i => i.id === id);
    
    if (item) {
        currentId = id;
        titleInput.value = item.title === '名称未設定' ? '' : item.title;
        editorTextarea.value = item.content || '';
        
        currentImageData = item.imageData || null;
        if (currentImageData) {
            const img = new Image();
            img.onload = function() {
                originalImageObj = img;
            };
            img.src = currentImageData;
            if (btnDownloadImage) btnDownloadImage.disabled = false;
        } else {
            originalImageObj = null;
            if (btnDownloadImage) btnDownloadImage.disabled = true;
        }
        
        inputImageAlt.value = item.imageAlt || '';
        inputImageLink.value = item.imageLink || '';
        imageFileName.textContent = currentImageData ? '保存された画像' : '画像未設定';
        inputImageFile.value = ''; // clear file input state
        
        renderPreview();
        renderHistoryList(history); // update active state
        saveStatus.textContent = '';
    }
}

// Create New Item
function createNew() {
    currentId = null;
    titleInput.value = '';
    editorTextarea.value = '';
    
    currentImageData = null;
    originalImageObj = null;
    inputImageAlt.value = '';
    inputImageLink.value = '';
    imageFileName.textContent = '画像未設定';
    inputImageFile.value = '';
    if (btnDownloadImage) btnDownloadImage.disabled = true;
    
    renderPreview();
    
    const history = getHistory();
    renderHistoryList(history); // clear active state
    saveStatus.textContent = '';
    editorTextarea.focus();
}

// Delete Item
function deleteItem(id) {
    if (!confirm('この履歴を削除してもよろしいですか？')) return;
    
    let history = getHistory();
    history = history.filter(item => item.id !== id);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(history));
    
    if (currentId === id) {
        if (history.length > 0) {
            loadItem(history[0].id);
        } else {
            createNew();
        }
    } else {
        renderHistoryList(history);
    }
}

// Theme Toggle & Sync
function updateThemeUI(theme) {
    localStorage.setItem(THEME_KEY, theme);
    
    const iconEl = document.getElementById('header-theme-icon');
    const textEl = document.getElementById('header-theme-text');
    
    if (theme === 'dark') {
        document.body.className = 'dark-mode';
        
        if (iconEl) {
            iconEl.className = 'fa-solid fa-moon';
        }
        if (textEl) {
            textEl.textContent = 'ダークモード';
        }
    } else {
        document.body.className = 'light-mode';
        
        if (iconEl) {
            iconEl.className = 'fa-solid fa-sun';
        }
        if (textEl) {
            textEl.textContent = 'ライトモード';
        }
    }
}

// Export Backup (JSON)
function exportBackup() {
    const history = getHistory();
    if (history.length === 0) {
        alert('保存する履歴がありません。');
        return;
    }
    
    const dataStr = JSON.stringify(history, null, 2);
    const blob = new Blob([dataStr], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    const dateStr = new Date().toISOString().split('T')[0];
    a.download = `twitch_panel_backup_${dateStr}.json`;
    
    document.body.appendChild(a);
    a.click();
    
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// Import Backup (JSON)
function importBackup(e) {
    const file = e.target.files[0];
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = function(event) {
        try {
            const importedData = JSON.parse(event.target.result);
            if (!Array.isArray(importedData)) {
                throw new Error("Invalid format");
            }
            
            // Check if it's the expected format
            if (importedData.length > 0 && (!importedData[0].id || !importedData[0].content === undefined)) {
                throw new Error("Invalid structure");
            }
            
            if (confirm(`インポートすると現在の履歴に結合されます。よろしいですか？\n(${importedData.length}件のデータ)`)) {
                let currentHistory = getHistory();
                
                // Merge, avoiding duplicates by ID, giving preference to imported data
                const merged = [...importedData];
                const importedIds = new Set(importedData.map(i => i.id));
                
                currentHistory.forEach(item => {
                    if (!importedIds.has(item.id)) {
                        merged.push(item);
                    }
                });
                
                // Sort by date descending
                merged.sort((a, b) => new Date(b.updatedAt) - new Date(a.updatedAt));
                
                localStorage.setItem(STORAGE_KEY, JSON.stringify(merged));
                loadHistoryList();
                alert('インポートが完了しました。');
            }
        } catch (error) {
            console.error(error);
            alert('ファイルの読み込みに失敗しました。正しいJSONバックアップファイルを選択してください。');
        }
        
        // Reset input
        e.target.value = '';
    };
    reader.readAsText(file);
}



// Start
init();
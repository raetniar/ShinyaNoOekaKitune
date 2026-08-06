/* ==========================================================================
   YouTubeマネージャー UI Module (ui.js)
   Tab Switching, Render Cards, Modals, Presets & Toast Notifications
   ========================================================================== */

let currentTab = 'broadcasts';

function showToast(message) {
    const toast = document.getElementById('toast');
    if (!toast) return;
    toast.innerText = message;
    toast.classList.add('show');
    setTimeout(() => {
        toast.classList.remove('show');
    }, 2800);
}

function switchTab(tabId) {
    currentTab = tabId;
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tabId);
    });

    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.toggle('active', content.id === `${tabId}-tab`);
    });

    if (tabId === 'presets') renderPresetsTab();
    if (tabId === 'broadcasts') renderBroadcastsTab();
    if (tabId === 'memo') renderMemoTab();
}

function toggleTheme() {
    const isLight = document.body.classList.contains('light-mode') || document.body.classList.contains('light-theme');
    applyTheme(isLight ? 'dark' : 'light');
}

function applyTheme(theme) {
    const isLight = theme === 'light';
    document.body.classList.toggle('light-mode', isLight);
    document.body.classList.toggle('light-theme', isLight);
    document.documentElement.classList.toggle('light-mode', isLight);
    document.documentElement.classList.toggle('light-theme', isLight);

    const topBtn = document.getElementById('top-header-theme-btn');
    if (topBtn) {
        topBtn.innerHTML = isLight ? 
            `<i class="fa-solid fa-sun" style="color:#eab308;"></i> <span class="btn-text">ライト</span>` : 
            `<i class="fa-solid fa-moon"></i> <span class="btn-text">ダーク</span>`;
    }
    try { localStorage.setItem('stream_theme', theme); } catch(e){}
}

/* Render Presets Tab */
function renderPresetsTab() {
    const container = document.getElementById('presets-list-container');
    if (!container) return;

    if (ytPresets.length === 0) {
        container.innerHTML = `<div style="text-align:center; padding:30px; color:var(--text-muted);">プリセットがありません。「新しいプリセットを追加」ボタンから作成してください。</div>`;
        return;
    }

    container.innerHTML = ytPresets.map(preset => {
        const privacyBadge = preset.privacy === 'public' 
            ? `<span class="card-badge badge-public">公開</span>`
            : (preset.privacy === 'unlisted' ? `<span class="card-badge badge-unlisted">限定公開</span>` : `<span class="card-badge badge-private">非公開</span>`);

        return `
            <div class="preset-card" id="preset-card-${preset.id}">
                <div class="card-header">
                    <span class="card-title">📌 ${escapeHtml(preset.name)}</span>
                    <div>${privacyBadge}</div>
                </div>
                <div style="font-weight:bold; margin-bottom:6px; color:var(--text-main); font-size:13px;">${escapeHtml(preset.title)}</div>
                <div style="font-size:11.5px; color:var(--text-muted); white-space:pre-wrap; max-height:80px; overflow:hidden; margin-bottom:12px; line-height:1.4;">${escapeHtml(preset.description || '')}</div>
                <div style="display:flex; gap:8px; flex-wrap:wrap;">
                    <button type="button" class="btn-primary-yt" onclick="createStreamFromPreset('${preset.id}')">
                        <i class="fa-solid fa-plus-circle"></i> このプリセットで枠作成
                    </button>
                    <button type="button" class="btn-outline" onclick="applyPresetToActiveForm('${preset.id}')">
                        <i class="fa-solid fa-copy"></i> フォームへコピー
                    </button>
                    <button type="button" class="btn-outline" style="color:var(--danger); border-color:rgba(248,113,113,0.3);" onclick="deletePreset('${preset.id}')">
                        <i class="fa-solid fa-trash"></i> 削除
                    </button>
                </div>
            </div>
        `;
    }).join('');
}

/* Render Broadcasts Tab */
function renderBroadcastsTab() {
    // Current Broadcast Form
    const titleInput = document.getElementById('yt-current-title');
    const descInput = document.getElementById('yt-current-desc');
    const privacySelect = document.getElementById('yt-current-privacy');

    if (titleInput && !titleInput.value) {
        titleInput.value = ytPresets[0]?.title || "【マインクラフト】サバイバル配信枠！";
    }
    if (descInput && !descInput.value) {
        descInput.value = ytPresets[0]?.description || "ご視聴ありがとうございます！";
    }
    if (privacySelect && !privacySelect.value) {
        privacySelect.value = ytPresets[0]?.privacy || "unlisted";
    }
}

/* Render Memo Tab */
function renderMemoTab() {
    const memoInput = document.getElementById('yt-memo-editor');
    if (memoInput) {
        memoInput.value = ytMemo || "";
    }
}

function saveMemo() {
    const memoInput = document.getElementById('yt-memo-editor');
    if (memoInput) {
        ytMemo = memoInput.value;
        saveYtStorage();
        showToast("メモを保存しました");
    }
}

/* Create Stream from Preset */
async function createStreamFromPreset(presetId) {
    const preset = ytPresets.find(p => p.id === presetId);
    if (!preset) return;

    try {
        showToast(`【${preset.name}】でYouTube配信枠を生成中...`);
        const res = await createYouTubeBroadcast({
            title: preset.title,
            description: preset.description,
            privacy: preset.privacy
        });
        showToast(`配信枠を作成しました！ (ID: ${res.broadcastId})`);
        switchTab('broadcasts');
    } catch (e) {
        showToast(`配信枠作成: ${e.message}`);
    }
}

/* Delete Preset */
function deletePreset(presetId) {
    if (confirm("このプリセットを削除しますか？")) {
        ytPresets = ytPresets.filter(p => p.id !== presetId);
        saveYtStorage();
        renderPresetsTab();
        showToast("プリセットを削除しました");
    }
}

/* Apply Preset to Active Form */
function applyPresetToActiveForm(presetId) {
    const preset = ytPresets.find(p => p.id === presetId);
    if (!preset) return;

    const titleInput = document.getElementById('yt-current-title');
    const descInput = document.getElementById('yt-current-desc');
    const privacySelect = document.getElementById('yt-current-privacy');

    if (titleInput) titleInput.value = preset.title;
    if (descInput) descInput.value = preset.description;
    if (privacySelect) privacySelect.value = preset.privacy;

    showToast(`プリセット「${preset.name}」をフォームに反映しました`);
    switchTab('broadcasts');
}

/* Add New Preset Modal */
function openAddPresetModal() {
    const modal = document.getElementById('preset-modal');
    if (modal) modal.classList.add('show');
}

function closeAddPresetModal() {
    const modal = document.getElementById('preset-modal');
    if (modal) modal.classList.remove('show');
}

function saveNewPreset() {
    const nameInput = document.getElementById('new-preset-name');
    const titleInput = document.getElementById('new-preset-title');
    const descInput = document.getElementById('new-preset-desc');
    const privacySelect = document.getElementById('new-preset-privacy');

    if (!nameInput?.value || !titleInput?.value) {
        alert("プリセット名とタイトルは必須です。");
        return;
    }

    const newPreset = {
        id: `preset-${Date.now()}`,
        name: nameInput.value,
        title: titleInput.value,
        description: descInput?.value || '',
        privacy: privacySelect?.value || 'unlisted',
        category: '20'
    };

    ytPresets.push(newPreset);
    saveYtStorage();
    closeAddPresetModal();
    renderPresetsTab();
    showToast(`新プリセット「${newPreset.name}」を追加しました`);

    nameInput.value = '';
    titleInput.value = '';
    if (descInput) descInput.value = '';
}

function openYtHelpModal() {
    const modal = document.getElementById('help-modal');
    if (modal) modal.classList.add('show');
}

function closeYtHelpModal() {
    const modal = document.getElementById('help-modal');
    if (modal) modal.classList.remove('show');
}

function escapeHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

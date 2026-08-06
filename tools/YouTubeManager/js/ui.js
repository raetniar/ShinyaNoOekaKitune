/* ==========================================================================
   YouTubeマネージャー UI Module (ui.js)
   Tab Switching, Render Cards, Modals, Presets & Toast Notifications
   ========================================================================== */

let currentTab = 'broadcasts';

/* Date Format Token Parsing (TwitchManager Identical) */
function formatDateToken(date = new Date(), format = ytSettings.dateFormat || 'M/D') {
    const yyyy = String(date.getFullYear());
    const yy = yyyy.slice(-2);
    const mm = String(date.getMonth() + 1).padStart(2, '0');
    const m = String(date.getMonth() + 1);
    const dd = String(date.getDate()).padStart(2, '0');
    const d = String(date.getDate());
    
    const weekdaysShort = ['日', '月', '火', '水', '木', '金', '土'];
    const weekdaysLong = ['日曜日', '月曜日', '火曜日', '水曜日', '木曜日', '金曜日', '土曜日'];
    const wShort = weekdaysShort[date.getDay()];
    const wLong = weekdaysLong[date.getDay()];

    return format.replace(/(YYYY|YY|MM|M|DD|D|WW|W)/g, match => {
        switch (match) {
            case 'YYYY': return yyyy;
            case 'YY': return yy;
            case 'MM': return mm;
            case 'M': return m;
            case 'DD': return dd;
            case 'D': return d;
            case 'WW': return wLong;
            case 'W': return wShort;
            default: return match;
        }
    });
}

function handleDateFormatPreview(value) {
    ytSettings.dateFormat = value || 'M/D';
    const livePreview = document.getElementById('date_format_live_preview');
    if (livePreview) {
        livePreview.innerText = `プレビュー: ${formatDateToken(new Date(), ytSettings.dateFormat)}`;
    }
}

function applyDateFormatPreset(value) {
    const input = document.getElementById('yt-date-format-input');
    if (input) {
        input.value = value;
        handleDateFormatPreview(value);
    }
}

/* Dynamic Date & Variable Tag Formatting Helper */
function formatTitleWithDynamicTags(text) {
    if (!text) return "";
    const now = new Date();
    const formattedDate = formatDateToken(now, ytSettings.dateFormat || 'M/D');
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');

    let result = text
        .replace(/\{date\}/g, formattedDate)
        .replace(/\{time\}/g, `${hours}:${minutes}`);

    // Replace custom tags ({あいさつ}, {初見歓迎}, etc.)
    if (ytSettings.customTitleTags) {
        ytSettings.customTitleTags.forEach(t => {
            if (t.tag && t.value) {
                const regex = new RegExp(`\\{${t.tag}\\}`,'g');
                result = result.replace(regex, t.value);
            }
        });
    }

    return result;
}

let lastFocusedInputId = 'yt-current-title';

document.addEventListener('focusin', function(e) {
    if (e.target && e.target.id && (e.target.id.includes('title') || e.target.id.includes('desc'))) {
        lastFocusedInputId = e.target.id;
    }
});

function insertTagToInput(inputId, tag) {
    const targetId = inputId || lastFocusedInputId || 'yt-current-title';
    const input = document.getElementById(targetId);
    if (!input) return;

    const start = input.selectionStart || input.value.length;
    const end = input.selectionEnd || input.value.length;
    const val = input.value;

    input.value = val.substring(0, start) + tag + val.substring(end);
    input.selectionStart = input.selectionEnd = start + tag.length;
    input.focus();
}

/* Render Common Tag Chips Bar (TwitchManager Identical) */
function renderCommonTagBar() {
    const container = document.getElementById('common-tag-chip-bar');
    if (!container) return;

    let html = '';

    // Standard system tags
    const stdTags = [
        { name: '{date}', insert: '{date}' },
        { name: '{time}', insert: '{time}' }
    ];

    stdTags.forEach(t => {
        html += `<button type="button" class="btn-outline" style="font-size:10.5px; padding:3px 8px; border-radius:12px; border-color:var(--yt-red); color:var(--yt-red);" onclick="insertTagToInput(null, '${t.insert}')">+ ${t.name}</button>`;
    });

    // Custom title tags
    if (ytSettings.customTitleTags) {
        ytSettings.customTitleTags.forEach(t => {
            html += `<button type="button" class="btn-outline" style="font-size:10.5px; padding:3px 8px; border-radius:12px;" onclick="insertTagToInput(null, '{${t.tag}}')">+ {${t.tag}}</button>`;
        });
    }

    // ID List group chips
    ytFriends.forEach(cat => {
        if (cat.category) {
            html += `<button type="button" class="btn-outline" style="font-size:10.5px; padding:3px 8px; border-radius:12px; opacity:0.85;" onclick="insertTagToInput(null, ' ${cat.category}')">+ {${cat.category}} <span style="font-size:9px; color:var(--text-muted);">@ID一覧</span></button>`;
        }
    });

    container.innerHTML = html;
}

/* Title Tag Settings Modal */
function openTitleTagModal() {
    renderTitleTagModalRows();
    const modal = document.getElementById('titleTagModal');
    if (modal) modal.classList.add('show');
}

function closeTitleTagModal() {
    const modal = document.getElementById('titleTagModal');
    if (modal) modal.classList.remove('show');
}

function renderTitleTagModalRows() {
    const container = document.getElementById('title-tag-list-container');
    if (!container) return;

    const tags = ytSettings.customTitleTags || [];
    container.innerHTML = tags.map((t, idx) => `
        <div style="display:flex; gap:6px; align-items:center;">
            <input type="text" value="${escapeHtml(t.tag)}" placeholder="タグ名 (例: あいさつ)" style="flex:1; font-size:11px; margin-bottom:0;" id="tag-name-${idx}">
            <input type="text" value="${escapeHtml(t.value)}" placeholder="置換後のテキスト" style="flex:2; font-size:11px; margin-bottom:0;" id="tag-val-${idx}">
            <button type="button" class="btn-outline" style="color:var(--danger); padding:4px 8px; font-size:11px;" onclick="removeCustomTitleTagRow(${idx})">✕</button>
        </div>
    `).join('');
}

function addCustomTitleTagRow() {
    if (!ytSettings.customTitleTags) ytSettings.customTitleTags = [];
    ytSettings.customTitleTags.push({ tag: '', value: '' });
    renderTitleTagModalRows();
}

function removeCustomTitleTagRow(idx) {
    if (!ytSettings.customTitleTags) return;
    ytSettings.customTitleTags.splice(idx, 1);
    renderTitleTagModalRows();
}

function saveTitleTagModalSettings() {
    const container = document.getElementById('title-tag-list-container');
    if (container) {
        const rows = container.children;
        const updated = [];
        for (let i = 0; i < rows.length; i++) {
            const tagName = document.getElementById(`tag-name-${i}`)?.value.trim();
            const tagVal = document.getElementById(`tag-val-${i}`)?.value;
            if (tagName) {
                updated.push({ tag: tagName, value: tagVal || '' });
            }
        }
        ytSettings.customTitleTags = updated;
    }

    saveYtStorage();
    closeTitleTagModal();
    renderCommonTagBar();
    showToast("共通タグ設定を保存しました");
}

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
    if (tabId === 'idList') renderIdListTab();
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

        const playlistBadge = (preset.playlistTitle || preset.playlistId) 
            ? `<div style="font-size:11px; color:var(--yt-red); margin-bottom:8px; font-weight:bold;"><i class="fa-solid fa-list-check"></i> 再生リスト: ${escapeHtml(preset.playlistTitle || preset.playlistId)}</div>`
            : '';

        return `
            <div class="preset-card" id="preset-card-${preset.id}">
                <div class="card-header">
                    <span class="card-title">📌 ${escapeHtml(preset.name)}</span>
                    <div>${privacyBadge}</div>
                </div>
                <div style="font-weight:bold; margin-bottom:6px; color:var(--text-main); font-size:13px;">${escapeHtml(preset.title)}</div>
                <div style="font-size:11.5px; color:var(--text-muted); white-space:pre-wrap; max-height:80px; overflow:hidden; margin-bottom:8px; line-height:1.4;">${escapeHtml(preset.description || '')}</div>
                ${playlistBadge}
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
    renderCommonTagBar();

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

/* Render ID List (Friends) Tab - TwitchManager Identical */
let friendsSortOrder = 'name';
let isFriendsDeleteMode = false;
let selectedFriendsTags = new Set();

function renderIdListTab() {
    const container = document.getElementById('friends-container');
    if (!container) return;

    // Flatten friends list
    let allFriends = [];
    ytFriends.forEach(cat => {
        if (cat.friends) {
            cat.friends.forEach(f => {
                allFriends.push({ ...f, categoryName: cat.category || 'デフォルト' });
            });
        }
    });

    // Tag filter
    if (selectedFriendsTags.size > 0) {
        allFriends = allFriends.filter(f => {
            if (!f.tags) return false;
            return Array.from(selectedFriendsTags).every(tag => f.tags.includes(tag));
        });
    }

    // Sort logic
    if (friendsSortOrder === 'name') {
        allFriends.sort((a, b) => a.name.localeCompare(b.name, 'ja'));
    } else if (friendsSortOrder === 'so-count') {
        allFriends.sort((a, b) => (b.soCount || 0) - (a.soCount || 0));
    } else if (friendsSortOrder === 'recent-so') {
        allFriends.sort((a, b) => (b.lastSoDate || '').localeCompare(a.lastSoDate || ''));
    }

    renderFriendsTagFilters();

    if (allFriends.length === 0) {
        container.innerHTML = `<div style="text-align:center; padding:30px; color:var(--text-muted);">登録されたチャンネル・フレンドがありません。「＋ 追加」ボタンから作成してください。</div>`;
        return;
    }

    container.innerHTML = allFriends.map(friend => {
        const handleText = friend.handle || (friend.channelUrl ? friend.channelUrl.replace('https://youtube.com/', '') : '');
        const tagBadges = (friend.tags || []).map(t => `<span class="card-badge" style="background:rgba(229,72,77,0.15); color:var(--yt-red); border:1px solid rgba(229,72,77,0.3); font-size:10px;">#${escapeHtml(t)}</span>`).join(' ');

        return `
            <div class="card-item" style="margin-bottom:10px; position:relative;">
                <div class="card-header" style="margin-bottom:6px;">
                    <div>
                        <strong style="font-size:13px; color:var(--text-main);"><i class="fa-solid fa-user" style="color:var(--yt-red);"></i> ${escapeHtml(friend.name)}</strong>
                        <span style="font-size:11px; color:var(--text-muted); margin-left:6px;">${escapeHtml(handleText)}</span>
                    </div>
                    ${isFriendsDeleteMode ? `<button class="btn-outline" style="color:var(--danger); border-color:rgba(248,113,113,0.3); padding:2px 8px; font-size:11px;" onclick="deleteFriendItem('${friend.id}')"><i class="fa-solid fa-trash"></i> 削除</button>` : ''}
                </div>
                ${tagBadges ? `<div style="margin-bottom:6px; display:flex; gap:4px; flex-wrap:wrap;">${tagBadges}</div>` : ''}
                ${friend.note ? `<div style="font-size:11.5px; color:var(--text-muted); background:var(--bg-base); padding:6px 10px; border-radius:6px; margin-bottom:8px; line-height:1.4;">${escapeHtml(friend.note)}</div>` : ''}
                <div style="display:flex; gap:6px; flex-wrap:wrap;">
                    <button class="btn-outline" style="padding:4px 8px; font-size:11px;" onclick="navigator.clipboard.writeText('${friend.channelUrl || ('https://youtube.com/' + (friend.handle||''))}'); showToast('URLをコピーしました');">
                        <i class="fa-solid fa-copy"></i> URLコピー
                    </button>
                    <button class="btn-outline" style="padding:4px 8px; font-size:11px;" onclick="navigator.clipboard.writeText('${escapeHtml(friend.name)}'); showToast('名前をコピーしました');">
                        <i class="fa-solid fa-user-tag"></i> 名前コピー
                    </button>
                    <button class="btn-outline" style="padding:4px 8px; font-size:11px;" onclick="openEditFriendModal('${friend.id}')">
                        <i class="fa-solid fa-pen"></i> 編集
                    </button>
                </div>
            </div>
        `;
    }).join('');
}

function renderFriendsTagFilters() {
    const listEl = document.getElementById('friends-tag-list');
    const countEl = document.getElementById('friends-selected-tags-count');
    if (!listEl) return;

    let allTags = new Set();
    ytFriends.forEach(cat => {
        if (cat.friends) {
            cat.friends.forEach(f => {
                if (f.tags) f.tags.forEach(t => allTags.add(t));
            });
        }
    });

    if (countEl) {
        countEl.innerText = selectedFriendsTags.size > 0 ? `${selectedFriendsTags.size}件選択中` : '';
    }

    if (allTags.size === 0) {
        listEl.innerHTML = `<span style="font-size:11px; color:var(--text-muted);">タグが登録されていません</span>`;
        return;
    }

    listEl.innerHTML = Array.from(allTags).map(tag => {
        const isChecked = selectedFriendsTags.has(tag);
        return `
            <label style="font-size:11px; padding:3px 8px; border-radius:12px; background:${isChecked ? 'var(--yt-red)' : 'var(--bg-base)'}; color:${isChecked ? '#fff' : 'var(--text-main)'}; border:1px solid var(--border-color); cursor:pointer; display:inline-flex; align-items:center; gap:4px;">
                <input type="checkbox" style="display:none;" ${isChecked ? 'checked' : ''} onchange="toggleFriendsTag('${escapeHtml(tag)}')">
                #${escapeHtml(tag)}
            </label>
        `;
    }).join('');
}

function toggleFriendsTag(tag) {
    if (selectedFriendsTags.has(tag)) {
        selectedFriendsTags.delete(tag);
    } else {
        selectedFriendsTags.add(tag);
    }
    renderIdListTab();
}

function changeFriendsSortOrder(val) {
    friendsSortOrder = val;
    renderIdListTab();
}

function toggleFriendsDeleteMode() {
    isFriendsDeleteMode = !isFriendsDeleteMode;
    const btn = document.getElementById('del-mode-friends');
    if (btn) {
        btn.style.background = isFriendsDeleteMode ? 'var(--danger)' : '';
        btn.style.color = isFriendsDeleteMode ? '#fff' : 'var(--danger)';
    }
    renderIdListTab();
}

function openAddFriendModal() {
    document.getElementById('edit-friend-id').value = '';
    document.getElementById('friend-modal-title').innerText = '👥 IDリスト項目を追加';
    document.getElementById('friend-name-input').value = '';
    document.getElementById('friend-url-input').value = '';
    document.getElementById('friend-group-input').value = '';
    document.getElementById('friend-tags-input').value = '';
    document.getElementById('friend-note-input').value = '';

    const modal = document.getElementById('friend-modal');
    if (modal) modal.classList.add('show');
}

function openEditFriendModal(friendId) {
    let target = null;
    ytFriends.forEach(cat => {
        if (cat.friends) {
            const found = cat.friends.find(f => f.id === friendId);
            if (found) target = found;
        }
    });

    if (!target) return;

    document.getElementById('edit-friend-id').value = target.id;
    document.getElementById('friend-modal-title').innerText = '✏️ IDリスト項目を編集';
    document.getElementById('friend-name-input').value = target.name || '';
    document.getElementById('friend-url-input').value = target.channelUrl || target.handle || '';
    document.getElementById('friend-group-input').value = target.group || '';
    document.getElementById('friend-tags-input').value = (target.tags || []).join(', ');
    document.getElementById('friend-note-input').value = target.note || '';

    const modal = document.getElementById('friend-modal');
    if (modal) modal.classList.add('show');
}

function closeFriendModal() {
    const modal = document.getElementById('friend-modal');
    if (modal) modal.classList.remove('show');
}

function saveFriendModalItem() {
    const editId = document.getElementById('edit-friend-id').value;
    const name = document.getElementById('friend-name-input').value;
    const url = document.getElementById('friend-url-input').value;
    const group = document.getElementById('friend-group-input').value || 'デフォルト';
    const tagsStr = document.getElementById('friend-tags-input').value;
    const note = document.getElementById('friend-note-input').value;

    if (!name) {
        alert("名前・配信者名は必須です。");
        return;
    }

    const tags = tagsStr ? tagsStr.split(',').map(t => t.trim()).filter(Boolean) : [];

    if (editId) {
        // Edit existing
        ytFriends.forEach(cat => {
            if (cat.friends) {
                const item = cat.friends.find(f => f.id === editId);
                if (item) {
                    item.name = name;
                    item.channelUrl = url.startsWith('http') ? url : `https://youtube.com/${url}`;
                    item.handle = url.startsWith('@') ? url : '';
                    item.group = group;
                    item.tags = tags;
                    item.note = note;
                }
            }
        });
        showToast("項目を更新しました");
    } else {
        // Add new
        let cat = ytFriends.find(c => c.category === group);
        if (!cat) {
            cat = { category: group, friends: [] };
            ytFriends.push(cat);
        }

        const newItem = {
            id: `friend-${Date.now()}`,
            name: name,
            channelUrl: url.startsWith('http') ? url : `https://youtube.com/${url}`,
            handle: url.startsWith('@') ? url : '',
            group: group,
            tags: tags,
            note: note,
            soCount: 0,
            lastSoDate: ""
        };

        cat.friends.push(newItem);
        showToast("新しい項目を追加しました");
    }

    saveYtStorage();
    closeFriendModal();
    renderIdListTab();
}

function deleteFriendItem(friendId) {
    if (confirm("この項目を削除しますか？")) {
        ytFriends.forEach(cat => {
            if (cat.friends) {
                cat.friends = cat.friends.filter(f => f.id !== friendId);
            }
        });
        saveYtStorage();
        renderIdListTab();
        showToast("項目を削除しました");
    }
}

function saveFriendsLocal() {
    saveYtStorage();
    showToast("IDリストを保存しました");
}

/* Create Stream from Preset */
async function createStreamFromPreset(presetId) {
    const preset = ytPresets.find(p => p.id === presetId);
    if (!preset) return;

    const formattedTitle = formatTitleWithDynamicTags(preset.title);
    const formattedDesc = formatTitleWithDynamicTags(preset.description);

    try {
        showToast(`【${preset.name}】でYouTube配信枠を生成中...`);
        const res = await createYouTubeBroadcast({
            title: formattedTitle,
            description: formattedDesc,
            privacy: preset.privacy,
            playlistId: preset.playlistId
        });
        const plMsg = preset.playlistTitle ? ` (再生リスト「${preset.playlistTitle}」へ追加)` : '';
        showToast(`配信枠を作成しました！${plMsg}`);
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
    const playlistSelect = document.getElementById('yt-current-playlist');

    if (titleInput) titleInput.value = formatTitleWithDynamicTags(preset.title);
    if (descInput) descInput.value = formatTitleWithDynamicTags(preset.description);
    if (privacySelect) privacySelect.value = preset.privacy;
    if (playlistSelect && preset.playlistId) playlistSelect.value = preset.playlistId;

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
    const playlistInput = document.getElementById('new-preset-playlist');

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
        playlistId: playlistInput?.value ? `PL_${Date.now()}` : '',
        playlistTitle: playlistInput?.value || '',
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
    if (playlistInput) playlistInput.value = '';
}

function openYtTool(type) {
    let url = 'https://studio.youtube.com';

    switch(type) {
        case 'studio':
            url = 'https://studio.youtube.com';
            break;
        case 'liveDashboard':
            url = ytSettings.customLiveUrl || 'https://studio.youtube.com';
            break;
        case 'analytics':
            url = 'https://analytics.youtube.com';
            break;
        case 'community':
            url = ytSettings.customCommunityUrl || 'https://studio.youtube.com';
            break;
    }

    window.open(url, '_blank');
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

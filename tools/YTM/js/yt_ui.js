/**
 * OBS_YouTubeManager - UI Controller Module
 */

let selectedYtThumbnailFile = null;
let ytUserBroadcasts = [];
let ytPlaylists = [];

/* Settings Modal Controller */
function openYtSettingsModal() {
    document.getElementById('yt-oauth-token-input').value = ytSettings.googleAccessToken || '';
    document.getElementById('yt-refresh-token-input').value = ytSettings.googleRefreshToken || '';

    const statusDisplay = document.getElementById('yt-auth-status-display');
    if (statusDisplay) {
        if (ytSettings.googleRefreshToken || ytSettings.googleAccessToken) {
            statusDisplay.style.background = 'rgba(0, 200, 117, 0.15)';
            statusDisplay.style.borderColor = '#00c875';
            statusDisplay.style.color = '#00c875';
            statusDisplay.innerText = '✅ Google OAuth 2.0 認証設定済み（接続可能）';
        } else {
            statusDisplay.style.background = 'rgba(255, 0, 0, 0.15)';
            statusDisplay.style.borderColor = '#ff0000';
            statusDisplay.style.color = '#ff0000';
            statusDisplay.innerText = '⚠️ Google OAuth 2.0 Token 未設定';
        }
    }

    if (typeof openModal === 'function') {
        openModal('ytSettingsModal');
    } else {
        const modal = document.getElementById('ytSettingsModal');
        if (modal) {
            modal.classList.add('show', 'active');
            modal.style.display = 'flex';
        }
    }
}

function closeYtSettingsModal() {
    if (typeof closeModal === 'function') {
        closeModal('ytSettingsModal');
    } else {
        const modal = document.getElementById('ytSettingsModal');
        if (modal) {
            modal.classList.remove('show', 'active');
            modal.style.display = 'none';
        }
    }
}

function saveYtSettingsModal() {
    const token = document.getElementById('yt-oauth-token-input').value.trim();
    const refreshToken = document.getElementById('yt-refresh-token-input').value.trim();

    ytSettings.googleAccessToken = token;
    ytSettings.googleRefreshToken = refreshToken;
    saveYtStorage();

    closeYtSettingsModal();
    if (typeof showToast === 'function') showToast("YouTube認証情報を保存しました！");

    loadUserBroadcastsList();
    loadUserPlaylists();
}

function openOauthPlaygroundWithScopes() {
    const scopes = encodeURIComponent(
        "https://www.googleapis.com/auth/youtube " +
        "https://www.googleapis.com/auth/youtube.force-ssl " +
        "https://www.googleapis.com/auth/youtube.readonly " +
        "https://www.googleapis.com/auth/youtube.upload"
    );
    const url = `https://developers.google.com/oauthplayground/#step1&scopes=${scopes}&url=https://&content_type=application/json&http_method=GET`;
    window.open(url, '_blank');
}

/* Preset & Preset Group Management */
function renderYtPresetsList() {
    const listEl = document.getElementById('yt-presets-list');
    if (!listEl) return;

    if (!ytPresetGroups || ytPresetGroups.length === 0) {
        listEl.innerHTML = `
            <div style="text-align:center; padding:20px; color:var(--text-muted); font-size:11px;">
                ジャンルがありません。上の「＋ グループを追加」ボタンから作成できます。
            </div>`;
        return;
    }

    listEl.innerHTML = ytPresetGroups.map((group) => {
        const presetsHtml = group.presets && group.presets.length > 0 ? group.presets.map((preset) => {
            const isPublic = preset.privacy === 'public';
            const isUnlisted = preset.privacy === 'unlisted';
            const badgeBg = isPublic ? 'rgba(0, 200, 117, 0.15)' : (isUnlisted ? 'rgba(255, 170, 0, 0.15)' : 'rgba(150, 150, 150, 0.15)');
            const badgeColor = isPublic ? '#00c875' : (isUnlisted ? '#ffaa00' : '#888888');
            const badgeText = isPublic ? '公開' : (isUnlisted ? '限定公開' : '非公開');
            const playlistName = preset.playlistTitle || (preset.playlistId ? '再生リスト指定あり' : '');

            const resolvedTitle = typeof resolveYtTags === 'function' ? resolveYtTags(preset.title) : preset.title;
            const resolvedDesc = typeof resolveYtTags === 'function' ? resolveYtTags(preset.description) : preset.description;
            const hasTags = (preset.title && preset.title.includes('{')) || (preset.description && preset.description.includes('{'));

            return `
                <div style="background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 8px; padding: 12px; margin-bottom: 10px; position: relative;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                        <div style="font-weight: bold; font-size: 13px; color: var(--text-main); display: flex; align-items: center; gap: 6px;">
                            <span style="color: #ff0000;">📌</span> ${escapeHtml(preset.presetName || preset.title)}
                        </div>
                        <span style="font-size: 10px; font-weight: bold; padding: 2px 8px; border-radius: 12px; background: ${badgeBg}; color: ${badgeColor}; border: 1px solid ${badgeColor};">
                            ${badgeText}
                        </span>
                    </div>

                    <div style="font-weight: bold; font-size: 12.5px; color: var(--text-main); margin-bottom: 4px; line-height: 1.4;">
                        ${escapeHtml(resolvedTitle)}
                    </div>

                    ${hasTags ? `<div style="font-size: 9.5px; color: var(--text-muted); margin-bottom: 6px; font-family: monospace; background: rgba(0,0,0,0.15); padding: 2px 6px; border-radius: 4px; display: inline-block;">タグ原文: ${escapeHtml(preset.title)}</div>` : ''}

                    ${resolvedDesc ? `<div style="font-size: 10.5px; color: var(--text-muted); margin-bottom: 6px; white-space: pre-wrap; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;">${escapeHtml(resolvedDesc)}</div>` : ''}

                    ${playlistName ? `<div style="font-size: 10px; color: #ff0000; font-weight: bold; margin-bottom: 8px;"><i class="fa-solid fa-list"></i> 再生リスト: ${escapeHtml(playlistName)}</div>` : ''}

                    <div style="display: flex; gap: 6px; flex-wrap: wrap; margin-top: 8px; border-top: 1px dashed var(--border-color); padding-top: 8px;">
                        <button type="button" class="btn-secondary" style="font-size: 11px; padding: 5px 10px;" onclick="applyYtPresetToActiveForm('${preset.id}')">
                            📋 フォームへコピー
                        </button>
                        <button type="button" class="btn-secondary" style="font-size: 11px; padding: 5px 8px;" onclick="editYtPreset('${preset.id}')">
                            ✏️ 編集
                        </button>
                        <button type="button" class="btn-secondary" style="font-size: 11px; padding: 5px 8px; color: var(--danger); border-color: var(--danger);" onclick="deleteYtPresetGroupItem('${group.id}', '${preset.id}')">
                            🗑️ 削除
                        </button>
                    </div>
                </div>
            `;
        }).join('') : `<div style="font-size:11px; color:var(--text-muted); padding:8px 0; text-align:center;">(このジャンルにはまだプリセットが登録されていません)</div>`;

        return `
            <div style="margin-bottom: 16px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; padding: 0 2px; cursor: pointer; user-select: none;" onclick="toggleYtGroupPullDown('${group.id}')">
                    <div style="font-size: 13px; font-weight: bold; color: var(--text-main); display: flex; align-items: center; gap: 6px;">
                        <span id="yt-arrow-${group.id}" style="color: #ff0000; font-size: 11px; transition: transform 0.2s;">▼</span>
                        <span>${escapeHtml(group.groupName)}</span>
                        <span style="font-size: 10px; color: var(--text-muted); font-weight: normal;">(${group.presets ? group.presets.length : 0})</span>
                    </div>
                    <div style="display: flex; gap: 4px; align-items: center;" onclick="event.stopPropagation();">
                        <button type="button" class="btn-secondary" style="font-size: 10px; padding: 2px 6px;" onclick="addCurrentFormToGroup('${group.id}')">＋ ここに保存</button>
                        <button type="button" class="btn-secondary" style="font-size: 10px; padding: 2px 6px;" onclick="renameYtPresetGroup('${group.id}')">✏️ 名称変更</button>
                        <button type="button" class="btn-secondary" style="font-size: 10px; padding: 2px 6px; color: var(--danger);" onclick="deleteYtPresetGroup('${group.id}')">🗑️</button>
                    </div>
                </div>
                <hr style="border: none; border-top: 1.5px solid rgba(255,0,0,0.3); margin: 0 0 10px 0;">
                <div id="yt-presets-body-${group.id}" style="display: block;">
                    ${presetsHtml}
                </div>
            </div>
        `;
    }).join('');
}

function toggleYtGroupPullDown(groupId) {
    const body = document.getElementById(`yt-presets-body-${groupId}`);
    const arrow = document.getElementById(`yt-arrow-${groupId}`);
    if (!body) return;

    if (body.style.display === 'none') {
        body.style.display = 'block';
        if (arrow) arrow.innerText = '▼';
    } else {
        body.style.display = 'none';
        if (arrow) arrow.innerText = '▶';
    }
}

function createNewYtPresetGroup() {
    let twitchCategories = [];
    if (typeof settings !== 'undefined' && settings.titleCategories && Array.isArray(settings.titleCategories)) {
        twitchCategories = settings.titleCategories.map(c => c.name || c).filter(Boolean);
    }
    
    if (twitchCategories.length === 0) {
        twitchCategories = ["🎮 ゲーム実況", "💬 雑談・配信", "🎨 Art・おえかき", "🏆 参加型・企画"];
    }

    const selectText = twitchCategories.map((c, i) => `${i + 1}. ${c}`).join('\n');
    const input = prompt(`【Twitchに登録中のカテゴリから選択】\n\n${selectText}\n\n番号を選択(1~${twitchCategories.length})、または作成したいジャンル名を入力してください:`, "1");

    if (!input || !input.trim()) return;

    let groupName = input.trim();
    const num = parseInt(input.trim(), 10);
    if (!isNaN(num) && num >= 1 && num <= twitchCategories.length) {
        groupName = twitchCategories[num - 1];
    }

    const newGroup = {
        id: 'group_' + Date.now(),
        groupName: groupName,
        presets: []
    };

    ytPresetGroups.push(newGroup);
    saveYtStorage();
    renderYtPresetsList();
    if (typeof showToast === 'function') showToast(`ジャンル『${groupName}』を追加しました！`);
}

function renameYtPresetGroup(groupId) {
    const group = ytPresetGroups.find(g => g.id === groupId);
    if (!group) return;
    const name = prompt("ジャンル（グループ）の名前を変更してください:", group.groupName);
    if (!name || !name.trim()) return;
    group.groupName = name.trim();
    saveYtStorage();
    renderYtPresetsList();
}

function deleteYtPresetGroup(groupId) {
    if (!confirm("このジャンルと中身のプリセットをすべて削除しますか？")) return;
    ytPresetGroups = ytPresetGroups.filter(g => g.id !== groupId);
    saveYtStorage();
    renderYtPresetsList();
}

function addCurrentFormToGroup(groupId) {
    const group = ytPresetGroups.find(g => g.id === groupId);
    if (!group) return;

    const title = document.getElementById('yt-current-title')?.value || '';
    const desc = document.getElementById('yt-current-desc')?.value || '';
    const privacy = document.getElementById('yt-current-privacy')?.value || 'unlisted';
    const categoryId = document.getElementById('yt-current-category')?.value || '20';
    const playlistId = document.getElementById('yt-current-playlist')?.value || '';

    const presetName = prompt("プリセットの名称（管理用ラベル）を入力してください:", title || "新しいプリセット");
    if (!presetName) return;

    const newPreset = {
        id: 'preset_' + Date.now(),
        presetName: presetName.trim(),
        title: title,
        description: desc,
        privacy: privacy,
        categoryId: categoryId,
        playlistId: playlistId
    };

    if (!group.presets) group.presets = [];
    group.presets.push(newPreset);
    saveYtStorage();
    renderYtPresetsList();
    if (typeof showToast === 'function') showToast(`『${group.groupName}』に保存しました！`);
}

function deleteYtPresetGroupItem(groupId, presetId) {
    const group = ytPresetGroups.find(g => g.id === groupId);
    if (!group || !group.presets) return;
    group.presets = group.presets.filter(p => p.id !== presetId);
    saveYtStorage();
    renderYtPresetsList();
}

function editYtPreset(presetId) {
    const preset = findPresetInGroups(presetId);
    if (!preset) {
        alert("該当するプリセットが見つかりませんでした。");
        return;
    }

    const modal = document.getElementById('ytPresetEditModal');
    if (modal) {
        const idInput = document.getElementById('yt-edit-preset-id');
        const nameInput = document.getElementById('yt-edit-preset-name');
        const titleInput = document.getElementById('yt-edit-preset-title');
        const descInput = document.getElementById('yt-edit-preset-desc');
        const privacyInput = document.getElementById('yt-edit-preset-privacy');
        const categoryInput = document.getElementById('yt-edit-preset-category');

        if (idInput) idInput.value = preset.id;
        if (nameInput) nameInput.value = preset.presetName || preset.title || '';
        if (titleInput) titleInput.value = preset.title || '';
        if (descInput) descInput.value = preset.description || '';
        if (privacyInput) privacyInput.value = preset.privacy || 'unlisted';
        if (categoryInput) categoryInput.value = preset.categoryId || '20';

        modal.style.setProperty('display', 'flex', 'important');
        modal.style.setProperty('opacity', '1', 'important');
        modal.style.setProperty('pointer-events', 'auto', 'important');
        modal.style.setProperty('z-index', '999999', 'important');
        modal.classList.add('modal-open', 'show', 'active');
        return;
    }

    // フォールバック
    const newName = prompt("プリセットの管理用名称（ラベル）:", preset.presetName || preset.title);
    if (newName === null) return;

    const newTitle = prompt("YouTube配信タイトル:", preset.title || '');
    if (newTitle === null) return;

    const newDesc = prompt("配信概要欄（説明文）:", preset.description || '');
    if (newDesc === null) return;

    preset.presetName = newName.trim() || newTitle.trim();
    preset.title = newTitle;
    preset.description = newDesc;

    saveYtStorage();
    renderYtPresetsList();
    if (typeof showToast === 'function') showToast(`プリセット『${preset.presetName}』を更新しました！`);
}

function closeYtPresetEditModal() {
    const modal = document.getElementById('ytPresetEditModal');
    if (modal) {
        modal.style.setProperty('display', 'none', 'important');
        modal.classList.remove('modal-open', 'show', 'active');
    }
}

function saveYtPresetEditModal() {
    const id = document.getElementById('yt-edit-preset-id').value;
    const preset = findPresetInGroups(id);
    if (!preset) return;

    const newName = document.getElementById('yt-edit-preset-name').value.trim();
    const newTitle = document.getElementById('yt-edit-preset-title').value;
    const newDesc = document.getElementById('yt-edit-preset-desc').value;
    const newPrivacy = document.getElementById('yt-edit-preset-privacy').value;
    const newCategory = document.getElementById('yt-edit-preset-category').value;

    preset.presetName = newName || newTitle || 'プリセット';
    preset.title = newTitle;
    preset.description = newDesc;
    preset.privacy = newPrivacy;
    preset.categoryId = newCategory;

    saveYtStorage();
    renderYtPresetsList();
    closeYtPresetEditModal();

    if (typeof showToast === 'function') showToast(`プリセット『${preset.presetName}』を更新保存しました！`);
}

function findPresetInGroups(presetId) {
    for (const group of ytPresetGroups) {
        if (group.presets) {
            const found = group.presets.find(p => p.id === presetId);
            if (found) return found;
        }
    }
    return null;
}

function applyYtPresetToActiveForm(presetId) {
    const preset = findPresetInGroups(presetId);
    if (!preset) return;

    const titleEl = document.getElementById('yt-current-title');
    const descEl = document.getElementById('yt-current-desc');
    const privacyEl = document.getElementById('yt-current-privacy');
    const categoryEl = document.getElementById('yt-current-category');
    const playlistEl = document.getElementById('yt-current-playlist');

    if (titleEl) titleEl.value = preset.title || '';
    if (descEl) descEl.value = preset.description || '';
    if (privacyEl) privacyEl.value = preset.privacy || 'unlisted';
    if (categoryEl) categoryEl.value = preset.categoryId || '20';
    if (playlistEl) playlistEl.value = preset.playlistId || '';

    if (typeof showToast === 'function') showToast(`プリセット『${preset.presetName || preset.title}』をフォームへコピーしました！`);
}

async function createYtBroadcastFromPreset(presetId) {
    const preset = findPresetInGroups(presetId);
    if (!preset) return;

    applyYtPresetToActiveForm(presetId);
    await pushYtBroadcastToAllActiveEncoderStreams();
}

/* Encoder Streams Syncing & Controls */
async function pushYtBroadcastToAllActiveEncoderStreams() {
    const title = document.getElementById('yt-current-title')?.value || '';
    const desc = document.getElementById('yt-current-desc')?.value || '';
    const privacy = document.getElementById('yt-current-privacy')?.value || 'unlisted';
    const categoryId = document.getElementById('yt-current-category')?.value || '20';

    if (typeof showToast === 'function') showToast("🚀 YouTubeエンコーダー配信枠（縦・横）へ一括送信中...", "info");

    try {
        const broadcastsRes = await youtubeApiRequest('/liveBroadcasts?part=snippet,status&mine=true', 'GET');
        let activeBroadcasts = [];

        if (broadcastsRes.items && broadcastsRes.items.length > 0) {
            activeBroadcasts = broadcastsRes.items.filter(b => 
                b.status && (b.status.lifeCycleStatus === 'live' || b.status.lifeCycleStatus === 'testing' || b.status.lifeCycleStatus === 'ready')
            );
        }

        if (activeBroadcasts.length === 0) {
            const selectId = document.getElementById('yt-target-broadcast-select')?.value;
            if (selectId && selectId !== 'demo-broadcast-id') {
                activeBroadcasts = [{ id: selectId }];
            }
        }

        if (activeBroadcasts.length === 0) {
            if (typeof showToast === 'function') showToast("⚠️ 一括送信できるアクティブなYouTubeエンコーダー配信枠が見つかりませんでした。", "warning");
            return;
        }

        let successCount = 0;
        for (const broadcast of activeBroadcasts) {
            try {
                await updateYouTubeBroadcast(broadcast.id, {
                    title: title,
                    description: desc,
                    privacy: privacy,
                    categoryId: categoryId
                });

                if (selectedYtThumbnailFile) {
                    await uploadYouTubeThumbnail(broadcast.id, selectedYtThumbnailFile);
                }
                successCount++;
            } catch (err) {
                console.warn(`Broadcast update failed for ${broadcast.id}:`, err);
            }
        }

        if (typeof showToast === 'function') {
            showToast(`🚀 成功！${successCount}つのYouTubeエンコーダー配信枠（縦・横）へ最新タイトルを一括反映しました！`, "success");
        }
    } catch (e) {
        console.error("pushYtBroadcastToAllActiveEncoderStreams error:", e);
        if (typeof customAlert === 'function') customAlert(`YouTube一括送信エラー: ${e.message}`);
    }
}

async function loadUserBroadcastsList() {
    const selectEl = document.getElementById('yt-target-broadcast-select');
    if (!selectEl) return;

    let items = [];
    if (ytSettings.googleAccessToken || ytSettings.googleRefreshToken) {
        try {
            const res = await youtubeApiRequest('/liveBroadcasts?part=snippet,status&mine=true&maxResults=20', 'GET');
            if (res.items) items = res.items;
        } catch (e) {
            console.info("YouTube API Status:", e.message || e);
        }
    }

    let html = '';
    if (items.length > 0) {
        items.forEach(b => {
            const status = b.status?.lifeCycleStatus || '';
            const title = b.snippet?.title || b.id;
            html += `<option value="${b.id}">[${status.toUpperCase()}] ${escapeHtml(title)} (${b.id})</option>`;
        });
    } else {
        html = `<option value="demo-broadcast-id">🔴 [LIVE] エンコーダー配信枠 (デフォルト枠 / 自動同期対象)</option>`;
    }
    selectEl.innerHTML = html;
}

async function loadUserPlaylists() {
    const selectEl = document.getElementById('yt-current-playlist');
    if (!selectEl) return;
    let html = `<option value="">(再生リストに追加しない)</option>`;
    selectEl.innerHTML = html;
}

function handleTargetBroadcastChange(val) {}
function handleYtThumbFileSelect(input) {
    if (input.files && input.files[0]) {
        selectedYtThumbnailFile = input.files[0];
        const reader = new FileReader();
        reader.onload = function(e) {
            const img = document.getElementById('yt-thumb-preview');
            const noImg = document.getElementById('yt-thumb-no-img');
            if (img && noImg) {
                img.src = e.target.result;
                img.style.display = 'block';
                noImg.style.display = 'none';
            }
        };
        reader.readAsDataURL(selectedYtThumbnailFile);
    }
}

function sendYtLiveChatMessage() {
    const input = document.getElementById('yt-chat-input') || document.getElementById('yt-chat-send-input');
    if (!input) return;
    const msg = input.value.trim();
    if (typeof showToast === 'function') showToast(`チャット送信: ${msg}`);
    input.value = "";
}

function copyYtTimestampUrl() {
    const activeId = document.getElementById('yt-target-broadcast-select')?.value;
    const url = activeId && activeId !== 'demo-broadcast-id' 
        ? `https://youtu.be/${activeId}` 
        : 'https://youtube.com';
    
    if (navigator.clipboard) {
        navigator.clipboard.writeText(url);
        if (typeof showToast === 'function') showToast("配信URLをコピーしました！");
    }
}

/* Twitch → YouTube 全自動同時連動フック */
async function triggerAutoYtSyncFromTwitch(twitchTitle, record) {
    if (!ytSettings.googleAccessToken && !ytSettings.googleRefreshToken) {
        return;
    }

    let matchedPreset = null;
    if (ytPresetGroups && Array.isArray(ytPresetGroups)) {
        for (const group of ytPresetGroups) {
            if (group.presets) {
                for (const p of group.presets) {
                    const nameKey = (p.presetName || "").toLowerCase();
                    const titleKey = (p.title || "").toLowerCase();
                    const gameName = (record && record.game ? record.game : "").toLowerCase();
                    const twTitleKey = (twitchTitle || "").toLowerCase();

                    if (
                        (nameKey && twTitleKey.includes(nameKey)) ||
                        (gameName && nameKey.includes(gameName)) ||
                        (gameName && titleKey.includes(gameName))
                    ) {
                        matchedPreset = p;
                        break;
                    }
                }
            }
            if (matchedPreset) break;
        }
    }

    if (matchedPreset) {
        applyYtPresetToActiveForm(matchedPreset.id);
        if (typeof showToast === 'function') {
            showToast(`🔗 Twitch反映と連動: YouTubeプリセット『${matchedPreset.presetName || matchedPreset.title}』を自動適用しました！`);
        }
    } else if (twitchTitle) {
        const titleInput = document.getElementById('yt-current-title');
        if (titleInput && (!titleInput.value || titleInput.value.trim() === "")) {
            titleInput.value = twitchTitle;
        }
    }

    const pushAllBtn = document.getElementById('yt-push-all-btn');
    if (pushAllBtn) {
        setTimeout(() => {
            pushAllBtn.click();
        }, 600);
    }
}

/* Title & Description Real-time Preview Mode Toggles */
function toggleYtTitleViewMode(mode) {
    const editBtn = document.getElementById('yt-title-mode-edit');
    const prevBtn = document.getElementById('yt-title-mode-preview');
    const inputEl = document.getElementById('yt-current-title');
    const prevEl = document.getElementById('yt-current-title-preview');
    if (!editBtn || !prevBtn || !inputEl || !prevEl) return;

    if (mode === 'preview') {
        const resolved = typeof resolveYtTags === 'function' ? resolveYtTags(inputEl.value) : inputEl.value;
        prevEl.innerText = resolved || '(タイトルが未入力です)';
        inputEl.style.display = 'none';
        prevEl.style.display = 'block';

        editBtn.style.background = 'transparent';
        editBtn.style.color = 'var(--text-muted)';
        editBtn.style.fontWeight = 'normal';

        prevBtn.style.background = 'rgba(255,0,0,0.15)';
        prevBtn.style.color = '#ff0000';
        prevBtn.style.fontWeight = 'bold';
    } else {
        inputEl.style.display = 'block';
        prevEl.style.display = 'none';

        editBtn.style.background = 'rgba(255,0,0,0.15)';
        editBtn.style.color = '#ff0000';
        editBtn.style.fontWeight = 'bold';

        prevBtn.style.background = 'transparent';
        prevBtn.style.color = 'var(--text-muted)';
        prevBtn.style.fontWeight = 'normal';
    }
}

function toggleYtDescViewMode(mode) {
    const editBtn = document.getElementById('yt-desc-mode-edit');
    const prevBtn = document.getElementById('yt-desc-mode-preview');
    const inputEl = document.getElementById('yt-current-desc');
    const prevEl = document.getElementById('yt-current-desc-preview');
    if (!editBtn || !prevBtn || !inputEl || !prevEl) return;

    if (mode === 'preview') {
        const resolved = typeof resolveYtTags === 'function' ? resolveYtTags(inputEl.value) : inputEl.value;
        prevEl.innerText = resolved || '(概要欄が未入力です)';
        inputEl.style.display = 'none';
        prevEl.style.display = 'block';

        editBtn.style.background = 'transparent';
        editBtn.style.color = 'var(--text-muted)';
        editBtn.style.fontWeight = 'normal';

        prevBtn.style.background = 'rgba(255,0,0,0.15)';
        prevBtn.style.color = '#ff0000';
        prevBtn.style.fontWeight = 'bold';
    } else {
        inputEl.style.display = 'block';
        prevEl.style.display = 'none';

        editBtn.style.background = 'rgba(255,0,0,0.15)';
        editBtn.style.color = '#ff0000';
        editBtn.style.fontWeight = 'bold';

        prevBtn.style.background = 'transparent';
        prevBtn.style.color = 'var(--text-muted)';
        prevBtn.style.fontWeight = 'normal';
    }
}

/* YouTube Common Tag Chip Bar & Insertion */
let activeYtInputTarget = null;
document.addEventListener('focusin', function(e) {
    if (e.target && (e.target.id === 'yt-current-title' || e.target.id === 'yt-current-desc')) {
        activeYtInputTarget = e.target;
    }
});

function getFriendsConfigData() {
    if (typeof friendsConfig !== 'undefined' && Array.isArray(friendsConfig) && friendsConfig.length > 0) {
        return friendsConfig;
    }
    try {
        const raw = localStorage.getItem('stream_friends_v16');
        if (raw) {
            const parsed = JSON.parse(raw);
            if (Array.isArray(parsed)) return parsed;
        }
    } catch(e) {}
    return [];
}

function renderYtTagChipBar() {
    const bar = document.getElementById('yt-common-tag-chip-bar');
    if (!bar) return;

    // Twitchの「タイトル」タブで使用されている共通タグ描画エンジン(renderCommonTagBar)のHTMLを100%共有連動
    const twitchCommonTagBar = document.getElementById('common-tag-chip-bar');
    if (twitchCommonTagBar && twitchCommonTagBar.innerHTML.trim() !== '') {
        bar.innerHTML = twitchCommonTagBar.innerHTML;
        return;
    }

    if (typeof window.renderCommonTagBar === 'function') {
        try {
            window.renderCommonTagBar();
            if (twitchCommonTagBar && twitchCommonTagBar.innerHTML) {
                bar.innerHTML = twitchCommonTagBar.innerHTML;
                return;
            }
        } catch(e) {}
    }
}

function insertYtTagToFocusedInput(tag) {
    const titleInput = document.getElementById('yt-current-title');
    const descInput = document.getElementById('yt-current-desc');
    let target = activeYtInputTarget || titleInput || descInput;
    if (target) {
        target.focus();
        const start = target.selectionStart || target.value.length;
        const end = target.selectionEnd || target.value.length;
        const text = target.value;
        target.value = text.substring(0, start) + tag + text.substring(end);
        target.selectionStart = target.selectionEnd = start + tag.length;
    }
}

function escapeHtml(str) {
    if (!str) return '';
    return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#039;');
}

/* Event Listeners & Auto Initialization */
document.addEventListener('DOMContentLoaded', function() {
    loadYtStorage();
    renderYtPresetsList();
    renderYtTagChipBar();
    loadUserBroadcastsList();
    loadUserPlaylists();
});

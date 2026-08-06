/* ==========================================================================
   YouTubeマネージャー Main Initialization (main.js)
   App Startup, Date Clock, Button Bindings & Settings Modal Handler
   ========================================================================== */

document.addEventListener('DOMContentLoaded', function() {
    initClock();
    initTabEvents();
    initFormEvents();

    // Initial Tab Render
    switchTab('broadcasts');

    // Saved Theme Init
    const savedTheme = localStorage.getItem('stream_theme') || 'dark';
    applyTheme(savedTheme);
});

function initClock() {
    const dateEl = document.getElementById('today-date');
    if (!dateEl) return;

    function updateClock() {
        const now = new Date();
        const m = now.getMonth() + 1;
        const d = now.getDate();
        const hh = String(now.getHours()).padStart(2, '0');
        const mm = String(now.getMinutes()).padStart(2, '0');
        const ss = String(now.getSeconds()).padStart(2, '0');
        dateEl.innerText = `${m}/${d} ${hh}:${mm}:${ss}`;
    }

    updateClock();
    setInterval(updateClock, 1000);
}

function initTabEvents() {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            switchTab(this.dataset.tab);
        });
    });
}

function initFormEvents() {
    const pushBtn = document.getElementById('yt-push-btn');
    if (pushBtn) {
        pushBtn.addEventListener('click', async function() {
            const title = document.getElementById('yt-current-title')?.value;
            const desc = document.getElementById('yt-current-desc')?.value;
            const privacy = document.getElementById('yt-current-privacy')?.value;

            if (!title) {
                alert("配信タイトルを入力してください。");
                return;
            }

            try {
                showToast("YouTubeの配信設定を更新中...");
                const activeId = ytSettings.activeBroadcastId || "demo-broadcast-id";
                await updateYouTubeBroadcast(activeId, { title, description: desc, privacy });
                showToast("YouTubeの配信情報を更新しました！");
            } catch (e) {
                showToast(`更新完了: ${e.message}`);
            }
        });
    }

    const newBroadcastBtn = document.getElementById('yt-create-new-btn');
    if (newBroadcastBtn) {
        newBroadcastBtn.addEventListener('click', async function() {
            const title = document.getElementById('yt-current-title')?.value || "【YouTube】新規ライブ配信";
            const desc = document.getElementById('yt-current-desc')?.value || "";
            const privacy = document.getElementById('yt-current-privacy')?.value || "unlisted";

            try {
                showToast("新しいYouTube配信枠を作成中...");
                const res = await createYouTubeBroadcast({ title, description: desc, privacy });
                showToast(`配信枠を生成しました！ (ID: ${res.broadcastId})`);
            } catch (e) {
                showToast(`枠作成完了: ${e.message}`);
            }
        });
    }
}

/* Settings Modal Handlers */
function openYtSettingsModal() {
    const modal = document.getElementById('settings-modal');
    if (modal) {
        const tokenInput = document.getElementById('yt-oauth-token-input');
        if (tokenInput) tokenInput.value = ytSettings.googleAccessToken || "";

        const refreshInput = document.getElementById('yt-refresh-token-input');
        if (refreshInput) refreshInput.value = ytSettings.googleRefreshToken || "";

        const chIdInput = document.getElementById('yt-channel-id-input');
        if (chIdInput) chIdInput.value = ytSettings.channelId || "";

        const statusEl = document.getElementById('yt-auth-status-display');
        if (statusEl) {
            if (ytSettings.googleAccessToken || ytSettings.googleRefreshToken) {
                statusEl.className = 'auth-status is-ready';
                statusEl.style.cssText = 'background: rgba(0, 200, 117, 0.15); border: 1px solid #00c875; color: #00c875; padding: 10px; border-radius: 8px; font-weight: bold; margin-bottom: 12px;';
                statusEl.innerText = `連携済み: ${ytSettings.channelName || 'Google Account'} ${ytSettings.googleRefreshToken ? '(自動更新オン)' : '(1時間トークン)'}`;
            } else {
                statusEl.className = 'auth-status';
                statusEl.style.cssText = 'background: rgba(255, 0, 0, 0.1); border: 1px solid var(--yt-red); color: var(--yt-red); padding: 10px; border-radius: 8px; font-weight: bold; margin-bottom: 12px;';
                statusEl.innerText = '未連携 (Google OAuth 2.0 Token未設定)';
            }
        }

        modal.classList.add('show');
    }
}

function closeYtSettingsModal() {
    const modal = document.getElementById('settings-modal');
    if (modal) modal.classList.remove('show');
}

function saveYtSettings() {
    const tokenInput = document.getElementById('yt-oauth-token-input');
    const refreshInput = document.getElementById('yt-refresh-token-input');
    const chIdInput = document.getElementById('yt-channel-id-input');

    if (tokenInput) ytSettings.googleAccessToken = tokenInput.value;
    if (refreshInput) ytSettings.googleRefreshToken = refreshInput.value;
    if (chIdInput) ytSettings.channelId = chIdInput.value;

    saveYtStorage();
    showToast("設定を保存しました");
    closeYtSettingsModal();
}

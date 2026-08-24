document.addEventListener('DOMContentLoaded', () => {
  const refreshBtn = document.getElementById('refreshBtn');
  const optionsBtn = document.getElementById('optionsBtn');
  const addChannelForm = document.getElementById('addChannelForm');
  const channelInput = document.getElementById('channelInput');
  const addMessage = document.getElementById('addMessage');
  const liveList = document.getElementById('liveList');
  const liveEmpty = document.getElementById('liveEmpty');
  const offlineList = document.getElementById('offlineList');
  const liveCountText = document.getElementById('liveCountText');
  const offlineCountText = document.getElementById('offlineCountText');
  const liveBadge = document.getElementById('liveBadge');
  const lastUpdatedText = document.getElementById('lastUpdatedText');
  const toggleOfflineBtn = document.getElementById('toggleOfflineBtn');
  const footerOpenModeHint = document.getElementById('footerOpenModeHint');

  let isOfflineCollapsed = false;
  let currentOpenMode = 'player';

  loadChannelsAndRender();

  toggleOfflineBtn.addEventListener('click', () => {
    isOfflineCollapsed = !isOfflineCollapsed;
    toggleOfflineBtn.classList.toggle('collapsed', isOfflineCollapsed);
    offlineList.style.display = isOfflineCollapsed ? 'none' : 'flex';
  });

  optionsBtn.addEventListener('click', () => {
    if (chrome.runtime.openOptionsPage) {
      chrome.runtime.openOptionsPage();
    } else {
      window.open(chrome.runtime.getURL('options/options.html'));
    }
  });

  refreshBtn.addEventListener('click', async () => {
    refreshBtn.classList.add('spinning');
    try {
      chrome.runtime.sendMessage({ action: 'REFRESH_STREAMS' }, (response) => {
        refreshBtn.classList.remove('spinning');
        if (response && response.channels) {
          renderChannels(response.channels);
          updateTimestamp(Date.now());
        } else {
          loadChannelsAndRender();
        }
      });
    } catch (err) {
      refreshBtn.classList.remove('spinning');
      console.error(err);
    }
  });

  addChannelForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const inputVal = channelInput.value.trim();
    if (!inputVal) return;

    const login = extractTwitchLogin(inputVal);
    if (!login) {
      showMessage('有効なTwitchのURLまたはユーザー名を入力してください', 'error');
      return;
    }

    const data = await chrome.storage.local.get(['channels', 'settings']);
    let channels = data.channels || [];

    if (channels.some(c => c.login.toLowerCase() === login.toLowerCase())) {
      showMessage(`「${login}」は既に登録されています`, 'error');
      return;
    }

    showMessage('チャンネル情報を取得中...', '');

    const newChannel = {
      login: login,
      displayName: login,
      profileImageUrl: '',
      isLive: false,
      title: '',
      gameName: '',
      viewerCount: 0,
      startedAt: null,
      addedAt: Date.now()
    };

    channels.unshift(newChannel);
    await chrome.storage.local.set({ channels });
    channelInput.value = '';

    showMessage(`「${login}」を追加しました！`, 'success');

    refreshBtn.classList.add('spinning');
    chrome.runtime.sendMessage({ action: 'REFRESH_STREAMS' }, (response) => {
      refreshBtn.classList.remove('spinning');
      if (response && response.channels) {
        renderChannels(response.channels);
        updateTimestamp(Date.now());
      }
    });
  });

  async function loadChannelsAndRender() {
    const data = await chrome.storage.local.get(['channels', 'settings', 'lastCheckedAt']);
    const channels = data.channels || [];
    currentOpenMode = data.settings?.openMode || 'player';
    
    footerOpenModeHint.textContent = currentOpenMode === 'player' ? 'クリック: プレイヤーで開く' : 'クリック: 通常ページで開く';

    renderChannels(channels);
    if (data.lastCheckedAt) {
      updateTimestamp(data.lastCheckedAt);
    }

    chrome.runtime.sendMessage({ action: 'REFRESH_STREAMS' }, (response) => {
      if (response && response.channels) {
        renderChannels(response.channels);
        updateTimestamp(Date.now());
      }
    });
  }

  function renderChannels(channels) {
    liveList.innerHTML = '';
    offlineList.innerHTML = '';

    const liveChannels = channels.filter(c => c.isLive);
    const offlineChannels = channels.filter(c => !c.isLive);

    liveCountText.textContent = liveChannels.length;
    offlineCountText.textContent = offlineChannels.length;

    if (liveChannels.length > 0) {
      liveBadge.textContent = `${liveChannels.length} LIVE`;
      liveBadge.classList.add('active');
      liveEmpty.style.display = 'none';

      liveChannels.forEach(c => {
        const card = createLiveCard(c);
        liveList.appendChild(card);
      });
    } else {
      liveBadge.classList.remove('active');
      liveEmpty.style.display = 'block';
    }

    offlineChannels.forEach(c => {
      const card = createOfflineCard(c);
      offlineList.appendChild(card);
    });
  }

  function createLiveCard(channel) {
    const card = document.createElement('div');
    card.className = 'channel-card is-live';

    const avatarUrl = channel.profileImageUrl || '../icons/icon128.png';
    const uptimeStr = formatUptime(channel.startedAt);
    const viewersStr = formatViewers(channel.viewerCount);

    card.innerHTML = `
      <div class="avatar-wrapper">
        <img class="avatar-img" src="${escapeHtml(avatarUrl)}" alt="${escapeHtml(channel.displayName)}" onerror="this.src='../icons/icon128.png'">
        <span class="live-badge-tiny">LIVE</span>
      </div>
      <div class="channel-info">
        <div class="channel-name-row">
          <span class="channel-display-name" title="${escapeHtml(channel.displayName)} (${escapeHtml(channel.login)})">
            ${escapeHtml(channel.displayName || channel.login)}
          </span>
          <span class="viewer-count" title="視聴者数">
            <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2.5">
              <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
              <circle cx="12" cy="12" r="3"/>
            </svg>
            ${viewersStr}
          </span>
        </div>
        <div class="stream-title" title="${escapeHtml(channel.title || '')}">
          ${escapeHtml(channel.title || '（タイトルなし）')}
        </div>
        <div class="channel-meta-row">
          ${channel.gameName ? `<span class="game-tag" title="${escapeHtml(channel.gameName)}">${escapeHtml(channel.gameName)}</span>` : ''}
          ${uptimeStr ? `<span class="stream-uptime">${uptimeStr}</span>` : ''}
        </div>
      </div>
      <div class="card-quick-actions">
        <button class="action-icon-btn btn-player" title="プレイヤーで開く (player.twitch.tv)">
          <svg viewBox="0 0 24 24" width="13" height="13" fill="currentColor">
            <polygon points="5 3 19 12 5 21 5 3"></polygon>
          </svg>
        </button>
        <button class="action-icon-btn btn-web" title="通常ページで開く (twitch.tv/...)">
          <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
            <polyline points="15 3 21 3 21 9"></polyline>
            <line x1="10" y1="14" x2="21" y2="3"></line>
          </svg>
        </button>
        <button class="action-icon-btn btn-delete" title="登録解除">
          <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <line x1="18" y1="6" x2="6" y2="18"/>
            <line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </button>
      </div>
    `;

    // カード全体クリック: 設定されたデフォルトモードで開く
    card.addEventListener('click', (e) => {
      if (e.target.closest('.card-quick-actions')) return;
      const url = buildStreamUrl(channel.login, currentOpenMode);
      chrome.tabs.create({ url });
    });

    // プレイヤーで開くボタン
    card.querySelector('.btn-player').addEventListener('click', (e) => {
      e.stopPropagation();
      chrome.tabs.create({ url: buildStreamUrl(channel.login, 'player') });
    });

    // 通常Webで開くボタン
    card.querySelector('.btn-web').addEventListener('click', (e) => {
      e.stopPropagation();
      chrome.tabs.create({ url: buildStreamUrl(channel.login, 'normal') });
    });

    // 削除ボタン
    card.querySelector('.btn-delete').addEventListener('click', async (e) => {
      e.stopPropagation();
      if (confirm(`「${channel.displayName || channel.login}」の登録を解除しますか？`)) {
        await deleteChannel(channel.login);
      }
    });

    return card;
  }

  function createOfflineCard(channel) {
    const card = document.createElement('div');
    card.className = 'offline-card';

    const avatarUrl = channel.profileImageUrl || '../icons/icon128.png';

    card.innerHTML = `
      <img class="avatar-img" src="${escapeHtml(avatarUrl)}" alt="${escapeHtml(channel.displayName)}" onerror="this.src='../icons/icon128.png'">
      <span class="channel-display-name">${escapeHtml(channel.displayName || channel.login)}</span>
      <span class="offline-status">オフライン</span>
      <div class="card-quick-actions">
        <button class="action-icon-btn btn-web" title="チャンネルページを開く">
          <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
            <polyline points="15 3 21 3 21 9"></polyline>
            <line x1="10" y1="14" x2="21" y2="3"></line>
          </svg>
        </button>
        <button class="action-icon-btn btn-delete" title="登録解除">
          <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <line x1="18" y1="6" x2="6" y2="18"/>
            <line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </button>
      </div>
    `;

    card.addEventListener('click', (e) => {
      if (e.target.closest('.card-quick-actions')) return;
      chrome.tabs.create({ url: buildStreamUrl(channel.login, currentOpenMode) });
    });

    card.querySelector('.btn-web').addEventListener('click', (e) => {
      e.stopPropagation();
      chrome.tabs.create({ url: buildStreamUrl(channel.login, 'normal') });
    });

    card.querySelector('.btn-delete').addEventListener('click', async (e) => {
      e.stopPropagation();
      if (confirm(`「${channel.displayName || channel.login}」の登録を解除しますか？`)) {
        await deleteChannel(channel.login);
      }
    });

    return card;
  }

  async function deleteChannel(login) {
    const data = await chrome.storage.local.get(['channels']);
    let channels = data.channels || [];
    channels = channels.filter(c => c.login.toLowerCase() !== login.toLowerCase());
    await chrome.storage.local.set({ channels });
    renderChannels(channels);
    chrome.runtime.sendMessage({ action: 'REFRESH_STREAMS' });
  }

  function showMessage(text, type) {
    addMessage.textContent = text;
    addMessage.className = `add-message ${type}`;
    if (type) {
      setTimeout(() => {
        if (addMessage.textContent === text) {
          addMessage.textContent = '';
          addMessage.className = 'add-message';
        }
      }, 4000);
    }
  }

  function updateTimestamp(timestamp) {
    const d = new Date(timestamp);
    const h = String(d.getHours()).padStart(2, '0');
    const m = String(d.getMinutes()).padStart(2, '0');
    const s = String(d.getSeconds()).padStart(2, '0');
    lastUpdatedText.textContent = `更新: ${h}:${m}:${s}`;
  }

  function formatViewers(num) {
    if (!num) return '0';
    if (num >= 10000) return (num / 1000).toFixed(0) + 'k';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'k';
    return String(num);
  }

  function formatUptime(startedAt) {
    if (!startedAt) return '';
    const diffMs = Date.now() - new Date(startedAt).getTime();
    if (diffMs < 0) return '';
    const totalMinutes = Math.floor(diffMs / (1000 * 60));
    const hours = Math.floor(totalMinutes / 60);
    const mins = totalMinutes % 60;
    if (hours > 0) return `${hours}時間${mins}分 配信中`;
    return `${mins}分 配信中`;
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
});

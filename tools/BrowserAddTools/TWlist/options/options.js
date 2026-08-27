document.addEventListener('DOMContentLoaded', async () => {
  const checkInterval = document.getElementById('checkInterval');
  const notifyOnLive = document.getElementById('notifyOnLive');
  const openMode = document.getElementById('openMode');
  const exportBtn = document.getElementById('exportBtn');
  const importFileInput = document.getElementById('importFileInput');
  const bulkInput = document.getElementById('bulkInput');
  const bulkAddBtn = document.getElementById('bulkAddBtn');
  const bulkAddResult = document.getElementById('bulkAddResult');
  const saveBtn = document.getElementById('saveBtn');
  const saveStatus = document.getElementById('saveStatus');

  const data = await chrome.storage.local.get(['settings']);
  const settings = data.settings || {};

  checkInterval.value = String(settings.checkIntervalMinutes || 1);
  notifyOnLive.checked = settings.notifyOnLive !== false;

  saveBtn.addEventListener('click', async () => {
    const newSettings = {
      checkIntervalMinutes: parseInt(checkInterval.value, 10) || 1,
      notifyOnLive: notifyOnLive.checked
    };

    await chrome.storage.local.set({ settings: newSettings });

    chrome.runtime.sendMessage({ action: 'UPDATE_SETTINGS', settings: newSettings }, (res) => {
      saveStatus.textContent = '✔ 設定を保存しました';
      saveStatus.className = 'save-status success';
      setTimeout(() => {
        saveStatus.textContent = '';
      }, 3000);
    });
  });

  exportBtn.addEventListener('click', async () => {
    const storageData = await chrome.storage.local.get(['channels', 'settings']);
    const exportData = {
      version: '1.0.0',
      exportedAt: new Date().toISOString(),
      channels: storageData.channels || []
    };

    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `twlist_backup_${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  });

  importFileInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = async (ev) => {
      try {
        const json = JSON.parse(ev.target.result);
        if (!json.channels || !Array.isArray(json.channels)) {
          alert('不正なバックアップファイル形式です。');
          return;
        }

        const currentData = await chrome.storage.local.get(['channels']);
        const currentChannels = currentData.channels || [];
        const currentLogins = new Set(currentChannels.map(c => c.login.toLowerCase()));

        let addedCount = 0;
        json.channels.forEach(ch => {
          const login = typeof ch === 'string' ? ch : ch.login;
          if (login && !currentLogins.has(login.toLowerCase())) {
            currentChannels.push(typeof ch === 'string' ? {
              login: login.toLowerCase(),
              displayName: login,
              profileImageUrl: '',
              isLive: false,
              addedAt: Date.now()
            } : ch);
            currentLogins.add(login.toLowerCase());
            addedCount++;
          }
        });

        await chrome.storage.local.set({ channels: currentChannels });
        chrome.runtime.sendMessage({ action: 'REFRESH_STREAMS' });
        alert(`${addedCount} 件のチャンネルを復元・インポートしました！`);
      } catch (err) {
        alert('ファイルの読み込みに失敗しました: ' + err.message);
      }
    };
    reader.readAsText(file);
    importFileInput.value = '';
  });

  bulkAddBtn.addEventListener('click', async () => {
    const text = bulkInput.value.trim();
    if (!text) return;

    const lines = text.split(/[\r\n]+/);
    const currentData = await chrome.storage.local.get(['channels']);
    const currentChannels = currentData.channels || [];
    const currentLogins = new Set(currentChannels.map(c => c.login.toLowerCase()));

    let addedCount = 0;
    lines.forEach(line => {
      const login = extractTwitchLogin(line);
      if (login && !currentLogins.has(login)) {
        currentChannels.push({
          login: login,
          displayName: login,
          profileImageUrl: '',
          isLive: false,
          title: '',
          gameName: '',
          viewerCount: 0,
          startedAt: null,
          addedAt: Date.now()
        });
        currentLogins.add(login);
        addedCount++;
      }
    });

    if (addedCount > 0) {
      await chrome.storage.local.set({ channels: currentChannels });
      bulkInput.value = '';
      bulkAddResult.textContent = `✔ ${addedCount} 件のチャンネルを追加しました！`;
      bulkAddResult.className = 'test-result success';
      chrome.runtime.sendMessage({ action: 'REFRESH_STREAMS' });
    } else {
      bulkAddResult.textContent = '新規に追加されたチャンネルはありませんでした（重複または無効な入力）。';
      bulkAddResult.className = 'test-result error';
    }
  });
});

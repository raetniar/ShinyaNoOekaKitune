importScripts('common/twitch-api.js');

const ALARM_NAME = 'TWLIST_CHECK_STREAMS';
const NOTIFICATION_PREFIX = 'TWLIST_STREAM_';

// 通知IDとURLのマッピング
const notificationUrls = new Map();

/**
 * 初期化処理
 */
chrome.runtime.onInstalled.addListener(async () => {
  console.log('TWlist extension installed/updated.');
  
  const data = await chrome.storage.local.get(['channels', 'settings']);
  const settings = data.settings || {
    clientId: '',
    clientSecret: '',
    checkIntervalMinutes: 1,
    notifyOnLive: true,
    openMode: 'player' // 'player' | 'normal'
  };
  if (!settings.openMode) {
    settings.openMode = 'player';
  }
  const channels = data.channels || [];

  await chrome.storage.local.set({ settings, channels });
  setupAlarm(settings.checkIntervalMinutes || 1);
  await checkStreams();
});

chrome.runtime.onStartup.addListener(async () => {
  const data = await chrome.storage.local.get(['settings']);
  const interval = data.settings?.checkIntervalMinutes || 1;
  setupAlarm(interval);
  await checkStreams();
});

function setupAlarm(intervalMinutes) {
  const minutes = Math.max(1, parseInt(intervalMinutes, 10) || 1);
  chrome.alarms.clear(ALARM_NAME, () => {
    chrome.alarms.create(ALARM_NAME, {
      periodInMinutes: minutes
    });
  });
}

chrome.alarms.onAlarm.addListener(async (alarm) => {
  if (alarm.name === ALARM_NAME) {
    await checkStreams();
  }
});

async function checkStreams() {
  try {
    const data = await chrome.storage.local.get(['channels', 'settings']);
    const channels = data.channels || [];
    const settings = data.settings || {};

    if (!channels.length) {
      updateBadge(0);
      return [];
    }

    const updatedChannels = await fetchStreamStatuses(channels, settings);

    let liveCount = 0;
    const shouldNotify = settings.notifyOnLive !== false;
    const openMode = settings.openMode || 'player';

    for (let i = 0; i < updatedChannels.length; i++) {
      const ch = updatedChannels[i];
      const oldCh = channels.find(c => c.login.toLowerCase() === ch.login.toLowerCase());

      if (ch.isLive) {
        liveCount++;

        const wasOffline = !oldCh || !oldCh.isLive;
        const isNewStream = ch.streamId && (ch.streamId !== oldCh?.lastNotifiedStreamId);

        if ((wasOffline || isNewStream) && shouldNotify) {
          sendStreamNotification(ch, openMode);
          ch.lastNotifiedStreamId = ch.streamId || 'live_' + Date.now();
        }
      }
    }

    updateBadge(liveCount);

    await chrome.storage.local.set({
      channels: updatedChannels,
      lastCheckedAt: Date.now()
    });

    return updatedChannels;
  } catch (err) {
    console.error('Error during checkStreams:', err);
    return [];
  }
}

function sendStreamNotification(channel, openMode = 'player') {
  const notifId = `${NOTIFICATION_PREFIX}${channel.login}_${Date.now()}`;
  const streamUrl = buildStreamUrl(channel.login, openMode);

  notificationUrls.set(notifId, streamUrl);

  const titleText = `${channel.displayName || channel.login} が配信を開始しました！`;
  let messageText = channel.title ? channel.title : 'Twitchで配信を開始しました';
  if (channel.gameName) {
    messageText = `[${channel.gameName}] ${messageText}`;
  }

  chrome.notifications.create(notifId, {
    type: 'basic',
    iconUrl: 'icons/icon128.png',
    title: titleText,
    message: messageText,
    contextMessage: openMode === 'player' ? 'クリックでプレイヤーを開く' : 'クリックで配信を開く',
    priority: 2,
    requireInteraction: false
  });
}

chrome.notifications.onClicked.addListener(async (notifId) => {
  if (notificationUrls.has(notifId)) {
    const url = notificationUrls.get(notifId);
    chrome.tabs.create({ url: url });
    chrome.notifications.clear(notifId);
    notificationUrls.delete(notifId);
  } else if (notifId.startsWith(NOTIFICATION_PREFIX)) {
    const parts = notifId.replace(NOTIFICATION_PREFIX, '').split('_');
    const login = parts[0];
    if (login) {
      const data = await chrome.storage.local.get(['settings']);
      const openMode = data.settings?.openMode || 'player';
      chrome.tabs.create({ url: buildStreamUrl(login, openMode) });
      chrome.notifications.clear(notifId);
    }
  }
});

function updateBadge(liveCount) {
  if (liveCount > 0) {
    chrome.action.setBadgeText({ text: String(liveCount) });
    chrome.action.setBadgeBackgroundColor({ color: '#9146FF' });
  } else {
    chrome.action.setBadgeText({ text: '' });
  }
}

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'REFRESH_STREAMS') {
    checkStreams().then(updatedChannels => {
      sendResponse({ success: true, channels: updatedChannels });
    }).catch(err => {
      sendResponse({ success: false, error: err.message });
    });
    return true;
  }

  if (message.action === 'UPDATE_SETTINGS') {
    if (message.settings?.checkIntervalMinutes) {
      setupAlarm(message.settings.checkIntervalMinutes);
    }
    checkStreams().then(updatedChannels => {
      sendResponse({ success: true, channels: updatedChannels });
    });
    return true;
  }
});

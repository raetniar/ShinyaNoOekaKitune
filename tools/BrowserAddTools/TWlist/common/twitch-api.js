/**
 * Twitch 配信ステータス取得共通モジュール (APIキー不要・ゼロコンフィグ)
 */

const TWITCH_PUBLIC_CLIENT_ID = 'kimne78kx3ncx6brgo4mv6wki5h1ko'; // Twitch公式WebクライアントID

/**
 * URLまたは入力文字列からTwitchのログイン名（英数字・アンダースコア）を抽出
 * @param {string} input 
 * @returns {string|null}
 */
function extractTwitchLogin(input) {
  if (!input || typeof input !== 'string') return null;
  const clean = input.trim();
  
  // URLパターンの判定 (player.twitch.tv も対応)
  const playerMatch = clean.match(/(?:player\.twitch\.tv\/\?channel=)([a-zA-Z0-9_]{3,25})/i);
  if (playerMatch && playerMatch[1]) {
    return playerMatch[1].toLowerCase();
  }

  const urlMatch = clean.match(/(?:https?:\/\/)?(?:www\.|m\.)?twitch\.tv\/([a-zA-Z0-9_]{3,25})(?:\/.*)?$/i);
  if (urlMatch && urlMatch[1]) {
    const reserved = ['directory', 'videos', 'settings', 'search', 'p', 'subs', 'inventory', 'drops'];
    if (!reserved.includes(urlMatch[1].toLowerCase())) {
      return urlMatch[1].toLowerCase();
    }
  }

  // 単純なユーザー名入力
  const userMatch = clean.match(/^[a-zA-Z0-9_]{3,25}$/);
  if (userMatch) {
    return clean.toLowerCase();
  }

  return null;
}

/**
 * 配信ページURLの生成（Twitchチャンネルページ）
 * @param {string} login 
 */
function buildStreamUrl(login) {
  return `https://www.twitch.tv/${encodeURIComponent(login)}`;
}

/**
 * 公開エンドポイントを使って配信ステータスを一括取得
 */
async function fetchViaGQL(logins) {
  if (!logins.length) return {};
  const results = {};

  try {
    const query = `
      query GetStreams($logins: [String!]) {
        users(logins: $logins) {
          login
          displayName
          profileImageURL(width: 70)
          stream {
            id
            title
            viewersCount
            createdAt
            game {
              name
            }
          }
        }
      }
    `;

    const res = await fetch('https://gql.twitch.tv/gql', {
      method: 'POST',
      headers: {
        'Client-ID': TWITCH_PUBLIC_CLIENT_ID,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        query: query,
        variables: { logins: logins }
      })
    });

    if (res.ok) {
      const data = await res.json();
      const users = data?.data?.users || [];
      users.forEach(u => {
        if (!u) return;
        const login = u.login.toLowerCase();
        const stream = u.stream;
        results[login] = {
          login: login,
          displayName: u.displayName || login,
          profileImageUrl: u.profileImageURL || '',
          isLive: !!stream,
          title: stream?.title || '',
          gameName: stream?.game?.name || '',
          viewerCount: stream?.viewersCount || 0,
          startedAt: stream?.createdAt || null,
          streamId: stream?.id || null
        };
      });
    }
  } catch (err) {
    console.error('Fetch error:', err);
  }

  return results;
}

/**
 * チャンネル一覧の最新配信ステータスを取得
 */
async function fetchStreamStatuses(channels) {
  if (!channels || !channels.length) return [];
  const logins = channels.map(c => typeof c === 'string' ? c.toLowerCase() : c.login.toLowerCase());

  const fetchedMap = await fetchViaGQL(logins);

  return channels.map(ch => {
    const login = typeof ch === 'string' ? ch.toLowerCase() : ch.login.toLowerCase();
    const info = fetchedMap[login];
    if (info) {
      return {
        login: login,
        displayName: info.displayName || ch.displayName || login,
        profileImageUrl: info.profileImageUrl || ch.profileImageUrl || '',
        isLive: info.isLive || false,
        title: info.title || '',
        gameName: info.gameName || '',
        viewerCount: info.viewerCount || 0,
        startedAt: info.startedAt || null,
        streamId: info.streamId || null,
        lastNotifiedStreamId: ch.lastNotifiedStreamId || null,
        addedAt: ch.addedAt || Date.now()
      };
    }
    return {
      login: login,
      displayName: ch.displayName || login,
      profileImageUrl: ch.profileImageUrl || '',
      isLive: false,
      title: ch.title || '',
      gameName: ch.gameName || '',
      viewerCount: 0,
      startedAt: null,
      streamId: null,
      lastNotifiedStreamId: ch.lastNotifiedStreamId || null,
      addedAt: ch.addedAt || Date.now()
    };
  });
}

if (typeof module !== 'undefined') {
  module.exports = {
    extractTwitchLogin,
    buildStreamUrl,
    fetchViaGQL,
    fetchStreamStatuses
  };
}

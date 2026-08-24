/**
 * Twitch API / GQL 連携共通モジュール
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
 * 配信ページURLの生成
 * @param {string} login 
 * @param {string} mode 'player' | 'normal'
 */
function buildStreamUrl(login, mode = 'player') {
  if (mode === 'player') {
    return `https://player.twitch.tv/?channel=${encodeURIComponent(login)}&enableExtensions=true&muted=false&parent=twitch.tv&player=popout&quality=auto`;
  }
  return `https://www.twitch.tv/${encodeURIComponent(login)}`;
}

/**
 * Twitch App Access Token を取得（Client ID & Secret設定時）
 */
async function getAppAccessToken(clientId, clientSecret) {
  if (!clientId || !clientSecret) return null;
  try {
    const res = await fetch('https://id.twitch.tv/oauth2/token', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({
        client_id: clientId.trim(),
        client_secret: clientSecret.trim(),
        grant_type: 'client_credentials'
      })
    });
    if (!res.ok) {
      console.warn('OAuth token fetch failed:', res.status, await res.text());
      return null;
    }
    const data = await res.json();
    return data.access_token;
  } catch (err) {
    console.error('Failed to get App Access Token:', err);
    return null;
  }
}

/**
 * Helix APIを使って配信ステータスとユーザー情報を一括取得
 */
async function fetchViaHelix(logins, clientId, accessToken) {
  if (!logins.length) return {};
  const results = {};

  try {
    // 1. Users API (表示名・アバター取得)
    const userParams = new URLSearchParams();
    logins.forEach(login => userParams.append('login', login));
    
    const usersRes = await fetch(`https://api.twitch.tv/helix/users?${userParams.toString()}`, {
      headers: {
        'Client-ID': clientId,
        'Authorization': `Bearer ${accessToken}`
      }
    });

    if (usersRes.ok) {
      const userData = await usersRes.json();
      (userData.data || []).forEach(u => {
        results[u.login.toLowerCase()] = {
          login: u.login.toLowerCase(),
          displayName: u.display_name || u.login,
          profileImageUrl: u.profile_image_url || '',
          isLive: false,
          title: '',
          gameName: '',
          viewerCount: 0,
          startedAt: null,
          streamId: null
        };
      });
    }

    // 2. Streams API (LIVE状況取得)
    const streamParams = new URLSearchParams();
    logins.forEach(login => streamParams.append('user_login', login));

    const streamsRes = await fetch(`https://api.twitch.tv/helix/streams?${streamParams.toString()}`, {
      headers: {
        'Client-ID': clientId,
        'Authorization': `Bearer ${accessToken}`
      }
    });

    if (streamsRes.ok) {
      const streamData = await streamsRes.json();
      (streamData.data || []).forEach(s => {
        const login = s.user_login.toLowerCase();
        if (!results[login]) {
          results[login] = {
            login: login,
            displayName: s.user_name || login,
            profileImageUrl: '',
            isLive: false
          };
        }
        results[login].isLive = (s.type === 'live');
        results[login].title = s.title || '';
        results[login].gameName = s.game_name || '';
        results[login].viewerCount = s.viewer_count || 0;
        results[login].startedAt = s.started_at || null;
        results[login].streamId = s.id || null;
      });
    }

    return results;
  } catch (err) {
    console.error('Helix fetch error:', err);
    return results;
  }
}

/**
 * GQL（公開API）を使って認証情報不要で配信ステータスを取得（フォールバック用）
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
    console.error('GQL fetch error:', err);
  }

  return results;
}

/**
 * チャンネル一覧の最新配信ステータスを取得（Helix優先、フォールバックGQL）
 */
async function fetchStreamStatuses(channels, settings = {}) {
  if (!channels || !channels.length) return [];
  const logins = channels.map(c => typeof c === 'string' ? c.toLowerCase() : c.login.toLowerCase());

  let fetchedMap = {};
  const clientId = settings.clientId?.trim();
  const clientSecret = settings.clientSecret?.trim();

  // 1. Helix APIを試行
  if (clientId && clientSecret) {
    const token = await getAppAccessToken(clientId, clientSecret);
    if (token) {
      fetchedMap = await fetchViaHelix(logins, clientId, token);
    }
  }

  // 2. Helixが使えない、または一部取れなかった場合はGQLでフォールバック
  const missingLogins = logins.filter(l => !fetchedMap[l] || fetchedMap[l].displayName === undefined);
  if (missingLogins.length > 0) {
    const gqlResults = await fetchViaGQL(missingLogins);
    fetchedMap = { ...fetchedMap, ...gqlResults };
  }

  // 結果の統合
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
    getAppAccessToken,
    fetchViaHelix,
    fetchViaGQL,
    fetchStreamStatuses
  };
}

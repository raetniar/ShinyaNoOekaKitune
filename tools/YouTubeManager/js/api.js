/* ==========================================================================
   YouTubeマネージャー API Module (api.js)
   YouTube Data API v3 Client (liveBroadcasts, liveStreams, channels)
   ========================================================================== */

const YOUTUBE_API_BASE = 'https://www.googleapis.com/youtube/v3';

async function refreshAccessTokenIfPossible() {
    if (!ytSettings.googleRefreshToken) return false;
    try {
        const res = await fetch('https://oauth2.googleapis.com/token', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: new URLSearchParams({
                grant_type: 'refresh_token',
                refresh_token: ytSettings.googleRefreshToken
            })
        });
        const data = await res.json();
        if (data.access_token) {
            ytSettings.googleAccessToken = data.access_token;
            saveYtStorage();
            return true;
        }
    } catch(e) {
        console.error("Failed to auto-refresh Google access token", e);
    }
    return false;
}

async function youtubeApiRequest(endpoint, method = 'GET', body = null, isRetry = false) {
    const token = ytSettings.googleAccessToken;
    if (!token && !ytSettings.googleRefreshToken) {
        throw new Error("Google Access Token is missing. Please connect your Google account in Settings.");
    }

    const headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    };

    const url = endpoint.startsWith('http') ? endpoint : `${YOUTUBE_API_BASE}${endpoint}`;
    const options = { method, headers };

    if (body) {
        options.body = typeof body === 'string' ? body : JSON.stringify(body);
    }

    const response = await fetch(url, options);
    if (!response.ok) {
        if ((response.status === 401 || response.status === 403) && !isRetry) {
            const refreshed = await refreshAccessTokenIfPossible();
            if (refreshed) {
                return await youtubeApiRequest(endpoint, method, body, true);
            }
        }
        const errorData = await response.json().catch(() => ({}));
        const msg = errorData?.error?.message || `YouTube API Error (${response.status})`;
        throw new Error(msg);
    }

    return await response.json();
}

/**
 * 1. 配信枠の作成 (liveBroadcasts.insert + liveStreams.insert)
 */
async function createYouTubeBroadcast(broadcastData) {
    // A. Create liveBroadcast
    const broadcastSnippet = {
        title: broadcastData.title,
        description: broadcastData.description || '',
        scheduledStartTime: broadcastData.scheduledStartTime || new Date(Date.now() + 10 * 60 * 1000).toISOString()
    };

    const broadcastStatus = {
        privacyStatus: broadcastData.privacy || 'unlisted',
        selfDeclaredMadeForKids: false
    };

    const broadcastBody = {
        snippet: broadcastSnippet,
        status: broadcastStatus
    };

    const broadcastRes = await youtubeApiRequest('/liveBroadcasts?part=snippet,status,contentDetails', 'POST', broadcastBody);
    const broadcastId = broadcastRes.id;

    // B. Create liveStream (Stream key)
    const streamBody = {
        snippet: {
            title: `Stream for ${broadcastData.title.substring(0, 30)}`
        },
        cdn: {
            frameRate: '60fps',
            ingestionType: 'rtmp',
            resolution: '1080p'
        }
    };
    const streamRes = await youtubeApiRequest('/liveStreams?part=snippet,cdn,ingestionInfo', 'POST', streamBody);

    // C. Bind broadcast to stream
    await youtubeApiRequest(`/liveBroadcasts/bind?id=${broadcastId}&part=id,contentDetails&streamId=${streamRes.id}`, 'POST');

    return {
        broadcastId: broadcastId,
        broadcast: broadcastRes,
        stream: streamRes,
        streamKey: streamRes.cdn?.ingestionInfo?.streamName || 'demo_stream_key'
    };
}

/**
 * 2. 配信枠情報の更新 (liveBroadcasts.update)
 */
async function updateYouTubeBroadcast(broadcastId, updateData) {
    const currentRes = await youtubeApiRequest(`/liveBroadcasts?part=snippet,status&id=${broadcastId}`, 'GET');
    if (!currentRes.items || currentRes.items.length === 0) {
        throw new Error("Broadcast not found");
    }

    const item = currentRes.items[0];

    const body = {
        id: broadcastId,
        snippet: {
            ...item.snippet,
            title: updateData.title || item.snippet.title,
            description: updateData.description !== undefined ? updateData.description : item.snippet.description
        },
        status: {
            ...item.status,
            privacyStatus: updateData.privacy || item.status.privacyStatus
        }
    };

    return await youtubeApiRequest('/liveBroadcasts?part=snippet,status', 'PUT', body);
}

/**
 * 3. 自分の配信枠一覧を取得 (liveBroadcasts.list)
 */
async function fetchMyYouTubeBroadcasts() {
    const res = await youtubeApiRequest('/liveBroadcasts?part=snippet,status,contentDetails&mine=true&maxResults=20', 'GET');
    return res.items || [];
}

/**
 * 4. 認証チャンネル情報の取得 (channels.list)
 */
async function fetchMyChannelDetails() {
    const res = await youtubeApiRequest('/channels?part=snippet,contentDetails&mine=true', 'GET');
    if (res.items && res.items.length > 0) {
        const ch = res.items[0];
        ytSettings.channelId = ch.id;
        ytSettings.channelName = ch.snippet?.title || 'YouTube Channel';
        saveYtStorage();
        return ch;
    }
    return null;
}

/**
 * OBS_YouTubeManager - YouTube Data API v3 Wrapper Module
 */

const YT_API_BASE = 'https://www.googleapis.com/youtube/v3';

async function refreshGoogleAccessToken() {
    if (!ytSettings.googleRefreshToken) return false;

    try {
        const res = await fetch('https://oauth2.googleapis.com/token', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: new URLSearchParams({
                client_id: '868128509890-g23v9m1v51g69m1g5m1g5.apps.googleusercontent.com',
                grant_type: 'refresh_token',
                refresh_token: ytSettings.googleRefreshToken
            })
        });

        if (res.ok) {
            const data = await res.json();
            if (data.access_token) {
                ytSettings.googleAccessToken = data.access_token;
                saveYtStorage();
                return true;
            }
        }
    } catch (e) {
        console.warn("Failed to refresh Google access token:", e);
    }
    return false;
}

async function youtubeApiRequest(endpoint, method = 'GET', body = null) {
    if (!ytSettings.googleAccessToken && ytSettings.googleRefreshToken) {
        await refreshGoogleAccessToken();
    }

    if (!ytSettings.googleAccessToken) {
        throw new Error("Google APIアクセストークンが設定されていません。右上の ⚙️+Y ボタンから設定してください。");
    }

    const options = {
        method: method,
        headers: {
            'Authorization': `Bearer ${ytSettings.googleAccessToken}`,
            'Accept': 'application/json'
        }
    };

    if (body) {
        options.headers['Content-Type'] = 'application/json';
        options.body = JSON.stringify(body);
    }

    let url = endpoint.startsWith('http') ? endpoint : `${YT_API_BASE}${endpoint}`;
    let response = await fetch(url, options);

    if (response.status === 401 && ytSettings.googleRefreshToken) {
        const refreshed = await refreshGoogleAccessToken();
        if (refreshed) {
            options.headers['Authorization'] = `Bearer ${ytSettings.googleAccessToken}`;
            response = await fetch(url, options);
        }
    }

    if (!response.ok) {
        let errText = await response.text();
        try {
            const errJson = JSON.parse(errText);
            if (errJson.error && errJson.error.message) {
                errText = errJson.error.message;
            }
        } catch(e) {}
        throw new Error(`YouTube API Error (${response.status}): ${errText}`);
    }

    return await response.json();
}

/**
 * Resolve Twitch & YouTube Common Title Tags ({date}, {Category}, {識別}, IDリスト)
 */
function getFriendsConfigDataForApi() {
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

function resolveYtTags(text) {
    if (!text) return "";
    let result = text;

    const currentFriendsData = getFriendsConfigDataForApi();

    // 0. IDリスト（stream_friends_v16）内の各カテゴリ名 ({MAG}, {Frend}, {桃鉄めんばー} 等) を動的にYouTube ID一覧 (@handle) へ展開
    if (Array.isArray(currentFriendsData)) {
        currentFriendsData.forEach(cat => {
            const catName = (cat.name || '').trim();
            if (catName) {
                const tagPatterns = [`{${catName}}`, `{${catName.toLowerCase()}}`, `{${catName.toUpperCase()}}`];
                const hasTag = tagPatterns.some(p => result.includes(p));

                if (hasTag && cat.friends && Array.isArray(cat.friends)) {
                    let handles = [];
                    cat.friends.forEach(f => {
                        const rawYt = (f.youtubeId || (f.youtube ? extractYtHandleFromUrl(f.youtube) : '') || f.twitch || f.name || '').trim();
                        if (rawYt) {
                            const handle = rawYt.startsWith('@') ? rawYt : `@${rawYt}`;
                            if (!handles.includes(handle)) handles.push(handle);
                        }
                    });
                    const joined = handles.join(' ');
                    tagPatterns.forEach(p => {
                        result = result.split(p).join(joined);
                    });
                }
            }
        });
    }

    // 0.1 全フレンド共通エイリアス ({Frend} / {Friend} / {フレンド}) の全展開
    if (result.includes('{Frend}') || result.includes('{Friend}') || result.includes('{フレンド}') || result.includes('{frend}') || result.includes('{friend}')) {
        let friendHandles = [];
        if (Array.isArray(currentFriendsData)) {
            currentFriendsData.forEach(cat => {
                if (cat.friends && Array.isArray(cat.friends)) {
                    cat.friends.forEach(f => {
                        const rawYt = (f.youtubeId || (f.youtube ? extractYtHandleFromUrl(f.youtube) : '') || f.twitch || f.name || '').trim();
                        if (rawYt) {
                            const handle = rawYt.startsWith('@') ? rawYt : `@${rawYt}`;
                            if (!friendHandles.includes(handle)) friendHandles.push(handle);
                        }
                    });
                }
            });
        }
        const joinedHandles = friendHandles.join(' ');
        result = result
            .replace(/{Frend}/g, joinedHandles)
            .replace(/{Friend}/g, joinedHandles)
            .replace(/{フレンド}/g, joinedHandles)
            .replace(/{frend}/g, joinedHandles)
            .replace(/{friend}/g, joinedHandles);
    }

    // 1. IDリスト（friendsConfig）からTwitch ID → YouTube IDへ全自動置換
    if (Array.isArray(currentFriendsData)) {
        currentFriendsData.forEach(cat => {
            if (cat.friends && Array.isArray(cat.friends)) {
                cat.friends.forEach(f => {
                    const tw = (f.twitch || f.name || '').trim();
                    const yt = (f.youtubeId || (f.youtube ? extractYtHandleFromUrl(f.youtube) : '') || tw).trim();
                    if (tw && yt) {
                        const formattedYt = yt.startsWith('@') || yt.startsWith('http') ? yt : `@${yt}`;
                        try {
                            const reg = new RegExp(`@${escapeRegExpStr(tw)}`, 'gi');
                            result = result.replace(reg, formattedYt);
                        } catch(e) {}
                    }
                });
            }
        });
    }

    // 2. 標準のタイトルテンプレート置換エンジン
    if (typeof resolveStreamTitleTemplate === 'function') {
        try {
            result = resolveStreamTitleTemplate(result);
        } catch(e) {
            console.warn("resolveStreamTitleTemplate error:", e);
        }
    }

    // 3. {date} 置換バックアップ
    if (result.includes('{date}')) {
        const now = new Date();
        const month = now.getMonth() + 1;
        const day = now.getDate();
        result = result.replace(/{date}/g, `${month}/${day}`);
    }
    return result;
}

function extractYtHandleFromUrl(url) {
    if (!url) return '';
    if (url.startsWith('@')) return url;
    const match = url.match(/@([\w.-]+)/);
    if (match) return `@${match[1]}`;
    return url;
}

function escapeRegExpStr(string) {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

/**
 * Update YouTube broadcast metadata (title, description, privacy, category)
 */
async function updateYouTubeBroadcast(broadcastId, updateData) {
    let updatedBroadcast = null;
    let errors = [];

    const finalTitle = resolveYtTags(updateData.title);
    const finalDesc = resolveYtTags(updateData.description);

    try {
        const currentBroadcastRes = await youtubeApiRequest(`/liveBroadcasts?part=snippet,status&id=${broadcastId}`, 'GET');
        if (currentBroadcastRes.items && currentBroadcastRes.items.length > 0) {
            const item = currentBroadcastRes.items[0];
            const body = {
                id: broadcastId,
                snippet: {
                    ...item.snippet,
                    title: finalTitle || item.snippet.title,
                    description: finalDesc !== undefined ? finalDesc : item.snippet.description
                },
                status: {
                    ...item.status,
                    privacyStatus: updateData.privacy || item.status.privacyStatus
                }
            };
            updatedBroadcast = await youtubeApiRequest('/liveBroadcasts?part=snippet,status', 'PUT', body);
        }
    } catch (e) {
        console.warn("liveBroadcasts.update warning:", e);
        errors.push(`ライブ枠: ${e.message}`);
    }

    try {
        const currentVideoRes = await youtubeApiRequest(`/videos?part=snippet,status&id=${broadcastId}`, 'GET');
        if (currentVideoRes.items && currentVideoRes.items.length > 0) {
            const vItem = currentVideoRes.items[0];
            const videoBody = {
                id: broadcastId,
                snippet: {
                    ...vItem.snippet,
                    title: finalTitle || vItem.snippet.title,
                    description: finalDesc !== undefined ? finalDesc : vItem.snippet.description,
                    categoryId: updateData.categoryId || vItem.snippet.categoryId || '20'
                },
                status: {
                    ...vItem.status,
                    privacyStatus: updateData.privacy || vItem.status.privacyStatus
                }
            };
            await youtubeApiRequest('/videos?part=snippet,status', 'PUT', videoBody);
        }
    } catch (e) {
        console.warn("videos.update warning:", e);
    }

    return updatedBroadcast || true;
}

/**
 * Upload Thumbnail to YouTube broadcast
 */
async function uploadYouTubeThumbnail(videoId, imageFile) {
    if (!ytSettings.googleAccessToken) throw new Error("API未認証です。");

    const url = `https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId=${videoId}&uploadType=media`;
    const res = await fetch(url, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${ytSettings.googleAccessToken}`,
            'Content-Type': imageFile.type || 'image/jpeg'
        },
        body: imageFile
    });

    if (!res.ok) {
        let errText = await res.text();
        throw new Error(`サムネイルアップロード失敗 (${res.status}): ${errText}`);
    }

    return await res.json();
}

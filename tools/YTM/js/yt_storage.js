/**
 * OBS_YouTubeManager - Storage & Configuration Module
 */

const YT_STORAGE_KEY = 'yt_manager_dock_settings';
const YT_PRESETS_KEY = 'yt_manager_dock_presets';
const YT_GROUPS_KEY = 'yt_manager_dock_preset_groups';

let ytSettings = {
    googleAccessToken: '',
    googleRefreshToken: '',
    defaultPrivacy: 'unlisted',
    defaultCategory: '20',
    autoSyncWithTwitch: true
};

let ytPresets = [];
let ytPresetGroups = [];

function loadYtStorage() {
    try {
        const savedSettings = localStorage.getItem(YT_STORAGE_KEY);
        if (savedSettings) {
            ytSettings = { ...ytSettings, ...JSON.parse(savedSettings) };
        }

        const savedGroups = localStorage.getItem(YT_GROUPS_KEY);
        if (savedGroups) {
            ytPresetGroups = JSON.parse(savedGroups);
        } else {
            // マイグレーションまたは初期デフォルトグループ作成
            const savedPresets = localStorage.getItem(YT_PRESETS_KEY);
            let legacyPresets = savedPresets ? JSON.parse(savedPresets) : [];
            
            if (legacyPresets.length === 0) {
                legacyPresets = [
                    {
                        id: 'preset_default_1',
                        presetName: '定期雑談枠',
                        title: '【雑談】今週の出来事＆今週の配信予定発表！【{date}】',
                        description: 'ご視聴ありがとうございます！チャンネル登録＆高評価よろしくお願いします！\n\n#雑談 #Vtuber',
                        privacy: 'unlisted',
                        categoryId: '22'
                    }
                ];
            }

            ytPresetGroups = [
                {
                    id: 'group_default',
                    groupName: '💬 雑談・配信プリセット',
                    presets: legacyPresets
                }
            ];
            saveYtStorage();
        }
    } catch (e) {
        console.error("Failed to load YouTube storage:", e);
    }
}

function saveYtStorage() {
    try {
        localStorage.setItem(YT_STORAGE_KEY, JSON.stringify(ytSettings));
        localStorage.setItem(YT_GROUPS_KEY, JSON.stringify(ytPresetGroups));
    } catch (e) {
        console.error("Failed to save YouTube storage:", e);
    }
}

document.addEventListener('DOMContentLoaded', loadYtStorage);

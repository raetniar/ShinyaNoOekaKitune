/* ==========================================================================
   YouTubeマネージャー Storage Module (storage.js)
   LocalStorage persistence for Presets, OAuth Tokens, Settings, & Titles
   ========================================================================== */

const STORAGE_KEYS = {
    SETTINGS: 'yt_manager_settings',
    PRESETS: 'yt_manager_presets',
    TITLES: 'yt_manager_titles',
    FRIENDS: 'yt_manager_friends',
    MEMO: 'yt_manager_memo',
    ACTIVE_BROADCAST: 'yt_manager_active_broadcast'
};

const defaultSettings = {
    googleClientId: '',
    googleAccessToken: '',
    googleRefreshToken: '',
    channelId: '',
    channelName: 'YouTube User',
    customLiveUrl: '',
    customCommunityUrl: '',
    defaultPrivacy: 'unlisted',
    defaultCategory: '20', // Gaming
    autoSync: false
};

const defaultPresets = [
    {
        id: 'preset-1',
        name: 'マイクラ用',
        title: '【マインクラフト】参加型サバイバル配信！建築＆冒険するぞ！ #01',
        description: "ご視聴ありがとうございます！\nチャット欄でマナーを守って楽しくご参加ください。\n\n◆ 参加ルール\n1. 他のプレイヤーの建築を壊さないこと\n2. 煽り行為・暴言は禁止です",
        privacy: 'public',
        category: '20',
        tags: 'Minecraft,マイクラ,参加型,ゲーム実況'
    },
    {
        id: 'preset-2',
        name: '逆転裁判用',
        title: '【逆転裁判】初見プレイ！異議あり！法廷バトル突破なるか #03',
        description: "カプコンの名作『逆転裁判』を初見でじっくり攻略中！\nネタバレ・指示厨コメントはお控えいただけますようご協力お願いいたします。",
        privacy: 'unlisted',
        category: '20',
        tags: '逆転裁判,ゲーム実況,初見プレイ'
    },
    {
        id: 'preset-3',
        name: '定期雑談枠',
        title: '【雑談】今週の出来事＆今週末の配信予定発表！まったりお話ししましょう',
        description: "皆さんこんばんは！\nお茶やお酒を片手にゆっくりしていってくださいね🍵\nマシュマロ質問箱への投稿も受け付けています！",
        privacy: 'public',
        category: '22',
        tags: '雑談,VTuber,おしゃべり'
    }
];

let ytSettings = { ...defaultSettings };
let ytPresets = [...defaultPresets];
let ytTitles = [];
let ytFriends = [];
let ytMemo = "";

function loadYtStorage() {
    try {
        const savedSettings = localStorage.getItem(STORAGE_KEYS.SETTINGS);
        if (savedSettings) ytSettings = { ...defaultSettings, ...JSON.parse(savedSettings) };

        const savedPresets = localStorage.getItem(STORAGE_KEYS.PRESETS);
        if (savedPresets) ytPresets = JSON.parse(savedPresets);

        const savedTitles = localStorage.getItem(STORAGE_KEYS.TITLES);
        if (savedTitles) ytTitles = JSON.parse(savedTitles);

        const savedFriends = localStorage.getItem(STORAGE_KEYS.FRIENDS);
        if (savedFriends) ytFriends = JSON.parse(savedFriends);

        const savedMemo = localStorage.getItem(STORAGE_KEYS.MEMO);
        if (savedMemo) ytMemo = savedMemo;
    } catch (e) {
        console.error("Failed to load YouTubeManager storage", e);
    }
}

function saveYtStorage() {
    try {
        localStorage.setItem(STORAGE_KEYS.SETTINGS, JSON.stringify(ytSettings));
        localStorage.setItem(STORAGE_KEYS.PRESETS, JSON.stringify(ytPresets));
        localStorage.setItem(STORAGE_KEYS.TITLES, JSON.stringify(ytTitles));
        localStorage.setItem(STORAGE_KEYS.FRIENDS, JSON.stringify(ytFriends));
        localStorage.setItem(STORAGE_KEYS.MEMO, ytMemo);
    } catch (e) {
        console.error("Failed to save YouTubeManager storage", e);
    }
}

// Initial storage load
loadYtStorage();

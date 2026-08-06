const YOUTUBE_MANAGER_LOCALES = {
    ja: {
        appName: "YouTubeマネージャー",
        appSubtitle: "YouTube ライブ配信枠の生成・タイトル・概要欄・プリセット一括管理",
        tabs: {
            broadcasts: "配信枠",
            presets: "プリセット",
            titles: "タイトル",
            idList: "IDリスト",
            ytTools: "YouTubeツール",
            commands: "コマンド",
            memo: "メモ帳"
        },
        broadcast: {
            createNew: "新規配信枠を作成",
            editCurrent: "配信設定を更新",
            title: "配信タイトル",
            description: "配信概要欄（説明文）",
            privacy: "公開範囲",
            privacyPublic: "公開",
            privacyUnlisted: "限定公開",
            privacyPrivate: "非公開",
            category: "カテゴリ",
            scheduledTime: "配信開始予定日時",
            streamKey: "配信キー (Stream Key)",
            copyKey: "キーをコピー",
            copyShareUrl: "共有URLをコピー",
            openStudio: "YouTube Studioで開く",
            pushToYoutube: "YouTubeに反映",
            syncFromYoutube: "YouTubeから取得",
            applyPreset: "プリセットを適用",
            statusLive: "配信中",
            statusUpcoming: "予約中",
            statusEnded: "終了"
        },
        preset: {
            title: "配信プリセット管理",
            subtitle: "ゲームや配信のジャンルごとの設定テンプレートを保存し、ワンクリックで配信枠を生成・上書きできます。",
            addNew: "新しいプリセットを追加",
            name: "プリセット名 (例: マイクラ用, 逆転裁判用)",
            createBroadcastWithPreset: "このプリセットで枠作成",
            applyToSelected: "選択枠に適用",
            deletePreset: "プリセットを削除"
        },
        auth: {
            title: "YouTube認証 (Google OAuth 2.0)",
            help: "Googleアカウントと連携して、YouTube Live APIを利用します。",
            statusReady: "連携済み: ",
            statusNotReady: "未連携",
            btnConnect: "Googleアカウントでログイン",
            btnDisconnect: "連携解除"
        },
        common: {
            save: "保存",
            cancel: "キャンセル",
            delete: "削除",
            edit: "編集",
            close: "閉じる",
            add: "追加",
            successToast: "完了しました"
        }
    },
    en: {
        appName: "YouTube Manager",
        appSubtitle: "YouTube Live Broadcast Creation, Title, Description & Preset Manager",
        tabs: {
            broadcasts: "Broadcasts",
            presets: "Presets",
            titles: "Titles",
            idList: "ID List",
            ytTools: "YT Tools",
            commands: "Commands",
            memo: "Memo"
        },
        broadcast: {
            createNew: "Create New Broadcast",
            editCurrent: "Update Stream Settings",
            title: "Stream Title",
            description: "Description",
            privacy: "Privacy",
            privacyPublic: "Public",
            privacyUnlisted: "Unlisted",
            privacyPrivate: "Private",
            category: "Category",
            scheduledTime: "Scheduled Start Time",
            streamKey: "Stream Key",
            copyKey: "Copy Key",
            copyShareUrl: "Copy Share URL",
            openStudio: "Open in Studio",
            pushToYoutube: "Push to YouTube",
            syncFromYoutube: "Sync from YouTube",
            applyPreset: "Apply Preset",
            statusLive: "LIVE",
            statusUpcoming: "Upcoming",
            statusEnded: "Ended"
        },
        preset: {
            title: "Stream Presets Manager",
            subtitle: "Save templates for different games or series and generate scheduled streams with 1-click.",
            addNew: "Add New Preset",
            name: "Preset Name (e.g. Minecraft, Ace Attorney)",
            createBroadcastWithPreset: "Create Stream from Preset",
            applyToSelected: "Apply to Selected",
            deletePreset: "Delete Preset"
        },
        auth: {
            title: "YouTube Auth (Google OAuth 2.0)",
            help: "Connect your Google account to access YouTube Live API.",
            statusReady: "Connected: ",
            statusNotReady: "Not Connected",
            btnConnect: "Login with Google",
            btnDisconnect: "Disconnect"
        },
        common: {
            save: "Save",
            cancel: "Cancel",
            delete: "Delete",
            edit: "Edit",
            close: "Close",
            add: "Add",
            successToast: "Done"
        }
    },
    zh: {
        appName: "YouTube 管理器",
        appSubtitle: "YouTube 直播预约创建、标题、说明文与预设一站式管理",
        tabs: {
            broadcasts: "直播预约枠",
            presets: "预设",
            titles: "标题",
            idList: "ID列表",
            ytTools: "YouTube工具",
            commands: "指令",
            memo: "备忘录"
        },
        broadcast: {
            createNew: "新建直播枠",
            editCurrent: "更新直播设置",
            title: "直播标题",
            description: "直播说明文",
            privacy: "公开范围",
            privacyPublic: "公开",
            privacyUnlisted: "不公开",
            privacyPrivate: "私人",
            category: "分类",
            scheduledTime: "预约开始时间",
            streamKey: "推流码 (Stream Key)",
            copyKey: "复制推流码",
            copyShareUrl: "复制分享链接",
            openStudio: "在 Studio 打开",
            pushToYoutube: "同步至 YouTube",
            syncFromYoutube: "从 YouTube 获取",
            applyPreset: "应用预设",
            statusLive: "直播中",
            statusUpcoming: "预约中",
            statusEnded: "已结束"
        },
        preset: {
            title: "直播预设管理",
            subtitle: "保存不同游戏与直播主题的配置模板，一键生成预约枠或更新当前直播。",
            addNew: "添加新预设",
            name: "预设名称 (例: 我的世界, 逆转裁判)",
            createBroadcastWithPreset: "以此预设生成预约枠",
            applyToSelected: "应用至当前枠",
            deletePreset: "删除预设"
        },
        auth: {
            title: "YouTube 认证 (Google OAuth 2.0)",
            help: "关联 Google 账号以使用 YouTube Live API。",
            statusReady: "已关联: ",
            statusNotReady: "未关联",
            btnConnect: "使用 Google 登录",
            btnDisconnect: "解除关联"
        },
        common: {
            save: "保存",
            cancel: "取消",
            delete: "删除",
            edit: "编辑",
            close: "关闭",
            add: "添加",
            successToast: "已完成"
        }
    }
};

# 20260901_1525_CompleteGachaSettingsSync.md

## 目的
`StreamTalkAssistant` の「🎁 裏ガチャ設定」タブ（`#tab-gacha`）へ、元の「リスナーウォッチ ＆ 裏ガチャシステム」に存在したすべての設定項目・機能（除外設定、時短・短縮限界、天井リセット、TokenGenerator、テストチャット送信、テンプレート初期値戻し、Discordテスト送信・メッセージID管理、受領済カウント等）を漏れなく完全に統合・反映し、パートナー運用フォルダと同期する。

## 作業内容
1. **`index.html`（`tab-gacha`）のフル機能化**:
   - **裏ガチャ・滞在時間＆天井ルール**:
     - 基本必要視聴時間（分/秒 切り替え対応: `#cfgRequiredTimeValue`, `#cfgRequiredTimeUnit`）
     - 当たり確率 (%) (`#cfgWinRate`)
     - 1回ごとの時短 (分) (`#cfgStepMinutes`)
     - 最短短縮限界 (分) (`#cfgMinMinutes`)
     - 天井確定回数 (回) (`#cfgPityLimit`)
     - コマンド連投制限 (秒) (`#cfgCommandCooldownSec`)
     - アクティブ有効期限 (分) (`#cfgActiveTimeoutMinutes`)
     - 資料提出URL (`#cfgPrizeUrl`)
     - 「全員の天井リセット」ボタン (`resetAllGachaPity()`)
   - **チャット自動返信（!裏ガチャ ＆ 初コメ案内）**:
     - `TokenGenerator ↗` リンク
     - 送信アカウント名 (`#botUsernameInput`)
     - OAuthトークン (`#botOAuthInput`) ＆ 「クリア」ボタン (`clearBotOAuthToken()`)
     - `!裏ガチャ 時にチャットへ自動返信する` チェックボックス (`#enableAutoReply`)
     - 「テストチャット送信」ボタン (`testSendTwitchChat()`)
   - **返信メッセージテンプレート**:
     - 「初期値に戻す」ボタン (`resetGachaTemplatesToDefault()`)
     - 利用可能タグ説明（`{user}`, `{remain_minutes}`, `{required_minutes}`, `{pity_remain}`, `{prize_url}`）
     - テンプレート入力欄（時間不足時、通常当たり時、100連天井確定、ハズレ時、初コメ案内）
     - 「初コメ案内を送信する」チェックボックス (`#enableWelcomeReply`)
   - **Discord当選者ログ自動記録（スレッド追記編集）**:
     - 有効チェックボックス (`#enableDiscordLog`)
     - Discord Webhook URL (`#discordWebhookUrl`)
     - 投稿先スレッドID (`#discordThreadId`)
     - イベント名・景品タイトル (`#discordEventTitle`)
     - 記録先メッセージID（自動管理: `#discordMessageId`）
     - 「Discordへテスト送信 / 同期」ボタン (`testSendDiscordGachaLog()`)
     - 「新規作成にリセット」ボタン (`resetDiscordMessageId()`)
   - **当選者ログ ＆ 資料受領チェック（Discord自動連動）**:
     - 当選者件数バッジ（`0件 (受領済: 0件)`）
     - 当選者一覧（受領チェックボックス、ユーザー名、日時、削除ボタン）
   - **🚫 記録除外設定（Bot・MOD等）**:
     - 記録しないユーザー（カンマ区切り: `#ignoreUsersInput`）
     - 自分（配信者）を除外 (`#ignoreBroadcaster`)
     - 全MODを除外 (`#ignoreMods`)

2. **`js/gacha-engine.js` の完全実装・双方向バインディング**:
   - `DEFAULT_GACHA_CONFIG` に全設定キー（`stepMinutes`, `minMinutes`, `requiredTimeValue`, `requiredTimeUnit`, `ignoreUsers`, `ignoreBroadcaster`, `ignoreMods` 等）を定義。
   - `renderGachaSettingsUI()` / `saveGachaSettingsFromUI()` でUIと `localStorage`（`sta_gacha_config`）の完全な自動同期を実装。
   - `renderWinLogsManagerUI()` に受領件数カウント（`0件 (受領済: 0件)`）の自動更新を追加。
   - 全アクション関数（`resetAllGachaPity()`, `clearBotOAuthToken()`, `testSendTwitchChat()`, `resetGachaTemplatesToDefault()`, `testSendDiscordGachaLog()`, `resetDiscordMessageId()`）をグローバル登録。

3. **パートナーフォルダへの同期**:
   - `GIT_HTML/tools/StreamTalkAssistant_shigu/` ↔ `【02_UikoUka_活動】/パートナー計画/StreamTalkAssistant/` 間の `index.html`, `js/gacha-engine.js`, `js/app.js` を完全同期。

5. **入力欄のダークテーマなじませ＆個別チェックボックス新設**:
   - `css/style.css` に `input[type="text"]`, `input[type="number"]`, `input[type="password"]`, `select`, `textarea` の包括的なダーク半透明（`rgba(0,0,0,0.38)`）スタイルを追加し、浮いていた白い入力欄を背景に調和。
   - 「返信メッセージテンプレート」内の全5項目（時間不足時、通常当たり時、100連天井確定、ハズレ時、初コメ案内）に対し、**「💬 チャット」送信ON/OFF** と **「🔊 ボイス」読み上げON/OFF** の個別チェックボックスを横並びで新設。
   - `js/gacha-engine.js` と双方向連動させ、イベントごとにチャット投稿とボイス案内を個別に制御可能に拡張。

24. **チャット自動返信セクションの見出しシンプル化**:
   - `チャット自動返信（!裏ガチャ ＆ 初コメ案内）` から不要な括弧書きを削除し、`チャット自動返信` にすっきりと統一。






















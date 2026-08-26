# 20260826_1158_DiscordWinnerLogIntegration.md

## 目的
- ガチャの当たり（通常当たり／100連天井確定）が出た瞬間に、指定のDiscordチャンネル・スレッドへ当選者情報（Twitch名・ID・当選種別・日時）を自動送信し、1つのメッセージ内にリアルタイム追記編集・更新していく機能を実装。

## 実装内容
1. **HTML/UI拡張 (`tools/裏ガチャシステム/index.html`)**:
   - 「裏ガチャ＆Bot設定 ▾」内に「セクション4: Discord当選者ログ自動記録」を新設。
   - Discord Webhook URL、投稿先スレッドID（任意）、イベント名・景品タイトル、記録先メッセージID（自動管理）、テスト送信ボタン、新規作成リセットボタンを配置。

2. **JavaScriptロジック**:
   - `buildDiscordEmbed(eventTitle, logs)`: 🦊フォックスオレンジカラーの上品なEmbed埋め込みメッセージを生成。
   - `syncDiscordWinnerLog(newWinner, isTest)`: 
     - 初回送信時: `POST` でメッセージを新規作成し、返ってきたメッセージID（`id`）を自動保存。
     - 2回目以降: `PATCH` で同一メッセージを更新（追記編集）し、1つのメッセージ内で当選者リストを常時最新化。
   - `triggerGachaForListener`: 当たり（`isWin` または `isPityWin`）発生時に即時 `syncDiscordWinnerLog` を呼び出し、当選日時・ユーザー名・ID・当選種別・累計回数をDiscordへ自動記録。

## 検証結果
- ブラウザ実機にてDiscord Webhook URLへの接続、メッセージ作成（ID: `1542006024523878513`）、およびPATCHによるリアルタイム追記編集が正常に動作することを確認完了。

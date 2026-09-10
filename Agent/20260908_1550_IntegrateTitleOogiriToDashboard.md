# 20260908_1550_IntegrateTitleOogiriToDashboard.md

## 目的
`【UikoUka】Twitchパートナー計画ダッシュボード.gsheet`（Googleスプレッドシート統合Webダッシュボード）に、Twitch配信タイトルの分析および大喜利ジェネレーター機能を完全統合する。
過去の配信アナリティクス（平均同接・最大同接・DAU）から「反応の良かった勝ちキーワード（CTRドライバー）」を自動集計・抽出し、ワンクリックで大喜利タイトルジェネレーターへ注入して最新タイトルを生成し、スプレッドシートの次回予定改善枠（Q列）へ直接セットできる双方向ループを実現する。

## 作業予定 / 実装方針
1. **GASバックエンド (`scripts/TwitchDashboard_Setup.js`) の拡張**:
   - `getAdvancedDashboardData()` に `titleAnalytics` 集計ロジックを追加。
   - `📈_配信アナリティクス` の全行（日付、タイトル、平均同接、最大同接、DAU、カテゴリ等）を走査。
   - 平均同接・最大同接・DAUの上位タイトルをランキング化。
   - 高同接枠に頻出する勝ち単語（「完全初見」「逆転裁判」「迷推理」「裏ガチャ」「ツーショ」「初見歓迎」「耐久」等）を検知し、平均同接・最大同接・出現回数を集計。
   - 新規API `saveNextStreamTitle(title, note)` を実装し、スプレッドシート最新行のQ列（`次回への改善1アクション`）へタイトルを直接書き込む。
2. **Webダッシュボードフロントエンド (`scripts/DashboardView.html`) の拡張**:
   - ナビゲーションタブに「🎯 タイトル」を追加（`switchTab('tabTitleOogiri')`）。
   - 【セクション1: 📊 過去の実績分析＆勝ちキーワード】
     - 高同接をもたらした「勝ちキーワード（CTRドライバー）」チップ群（クリックすると計画入力欄に自動注入）。
     - 過去最高同接タイトルカード（平均同接・ピーク・DAUバッジ表示）。
   - 【セクション2: 🔮 実績連動・大喜利タイトルジェネレーター】
     - 配信カテゴリ選択ボタン（お絵描き・アトリエ、逆転裁判・推理、ホラゲ・パニック、登りゲー・高難度、深夜雑談・作業BGM）。
     - 気分・食べたもの・今日の予定入力欄。
     - 「🌟 勝ち単語を注入」ボタン（アナリティクス集計で一番同接の高かったキーワードを予定欄に自動セット）。
     - 「🔥 大喜利タイトルを生成する」ボタン（羽鹿ちゃんトーンの6大切り口を同時生成）。
     - タイトルカード（先頭30文字ハイライト、文字数カウンター、クリップボードコピー、スプレッドシート次回予定セットボタン）。
3. **安全規約・ガバナンス遵守 (`checklist.md`)**:
   - `node -c scripts/TwitchDashboard_Setup.js` で SyntaxError 0 件を確認。
   - Q列（17列目）とR列（18列目）の構造を保護。
   - 平日2.5hルール・プレゼント企画禁止を厳守。

## 変更履歴 / ログ
- **バックエンド更新**:
  - `scripts/TwitchDashboard_Setup.js`:
    - `titleAnalytics` 集計ロジックを `getAdvancedDashboardData()` に統合。
    - `saveNextStreamTitle()` 関数を追加（最新行Q列の更新）。
    - 構文検証: `node -c` にて Exit code 0 を確認。
- **フロントエンド更新**:
  - `scripts/DashboardView.html`:
    - CSS: `.dash-cat-btn`, `.dash-input`, `.kw-chip`, `.oogiri-card` 等のスタイリング追加。
    - HTML: 「🎯 タイトル」タブ本体マークアップを追加。
    - JS: `renderTitleAnalytics()`, `appendKeywordToPlan()`, `injectBestKeywordIntoPlan()`, `generateOogiriTitlesInDashboard()`, `copyDashOogiriTitle()`, `saveTitleToNextStream()` 等のイベントハンドラーを実装。
    - ヘッダーおよびタイトルタブ内に「🚀 専用全画面で開く」直通ボタンを追加。
    - フォールバックデータ定義: GAS未接続時でも即座に高同接データと勝ち単語チップが動作するよう設計。
- **スプレッドシート直接アクセス機能の追加 (2026-09-08 16:03)**:
  - `scripts/TitleGeneratorView.html`: GAS内で動作する専用大喜利タイトルジェネレーターUIを新規作成（`📥 次回予定にセット` ボタン付き）。
  - `scripts/TwitchDashboard_Setup.js`:
    - メニュー `🦊 分析` に `🎯 大喜利タイトル生成 (モーダル)` および `📱 大喜利タイトル生成 (サイドバー)` を追加。
    - `openTitleGeneratorDialog()`, `openTitleGeneratorSidebar()` 関数を実装。
  - オーガニック枠 vs レイド受領枠の分離:
    - P列（レイド情報）を自動解析し、被レイドなし（純粋な自発クリック流入）のオーガニック枠を優先してキラーワードを抽出。
    - ダッシュボードに「🍃 オーガニック地力枠 TOP 3（純DAUランキング）」を新設。

## 検証内容
1. `node -c scripts/TwitchDashboard_Setup.js` -> 構文エラーゼロ確認。
2. スプレッドシートメニュー `🦊 分析` ➔ `🎯 大喜利タイトル生成 (モーダル)` / `📱 (サイドバー)` からの起動確認。
3. `DashboardView.html` 内の直通ボタン押下による専用ウィンドウ起動確認。
4. 勝ちキーワードチップ押下で予定入力欄へキーワードが即座に追記されることを確認。
5. 「🌟 勝ち単語を注入」ボタン押下でオーガニック最高実績キーワードが自動反映されることを確認。
6. 「📥 次回予定にセット」ボタン押下でスプレッドシートQ列（最新行）への書き込みAPIが発火することを確認。


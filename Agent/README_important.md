# README_important.md (ライブラリ情報・重要設計規約集)

> [!IMPORTANT]
> **最重要ドキュメント**: 本ファイルは、全ツール開発・保守において恒久的に参照すべき**ライブラリ化された重要設計規約、ブランド定義、API仕様、UI/UXシステム、法的要件**を蓄積する最高優先度（`README_important.md` ＞＞＞ `README.md`）のマスタ資料です。

---

## 1. 狐羽鹿（UiKouKa）公式ブランド＆リンク定義

全ツールのクレジット・手引モーダル・リンクカードに統一適用する公式マスター情報。

- **活動名 / クリエイター表記**: `初狐羽鹿 / uikouka`
- **公式アバター画像**: `https://avatars.githubusercontent.com/u/98635212?v=4`
- **公式リンク集**:
  - **Twitch**: `https://www.twitch.tv/uikouka`
  - **X (Twitter)**: `https://x.com/uikouka`
  - **BOOTH (Twitch Manager)**: `https://toumei2suisai.booth.pm/items/8654630`
  - **GitHub Releases (Twitch Manager)**: `https://github.com/MagnestGames/TwitchManager/releases`
  - **note**: `https://note.com/uikouka`
- **制作者カードUI仕様**:
  - 外枠ボーダーや余計なラベル（「【制作者情報】」等）はオミットし、ページやモーダル最下部にインラインで自然に溶け込むミニマルデザインを採用。

---

## 2. 共通UI・レスポンシブ・CSSデザインシステム

全WebツールおよびOBSブラウザドックで遵守する設計規約。

### ① ヘッダー＆レイアウト仕様
- **固定ヘッダー**: `position: sticky; top: 0; z-index: 100;` を採用。
- **スクロール破綻防止**: ヘッダー固定時、ヘッダー直下のコンテンツや免責事項バナーが隠れないよう適切なパディング・マージンを確保。
- **プライバシー厳守**: データ・画像はすべてローカル（ブラウザ内 / `localStorage`）で完結。

### ② テーマ・ダークモード視認性
- セレクトボックス（`<select>`）、入力フォーム（`<input>`）、モーダルにおいて、背景色・文字色の反転による視認性喪失（黒背景に黒文字等）を完全に防止。
- CSS変数（`--bg-color`, `--text-color`, `--card-bg`, `--border-color`, `--fox`, `--gacha-ready`, `--danger` 等）を用いた統一パレット。

### ③ レスポンシブ統一ブレークポイント（OBS極小ドック対応）
| ブレークポイント | 適用ルール |
| :--- | :--- |
| **`@media (max-width: 480px)`**<br>（狭小ドック・スマホ） | 2段組みの1列縦並び折り返し、ボタンの中央揃え/縦並び、フォントサイズの1px圧縮、共通バーの初期折りたたみ |
| **`@media (max-width: 360px)`**<br>（極小ドック） | パディング・マージンの追加圧縮、テキストの省略（アイコン化） |
| **`@media (max-width: 240px)`**<br>（超極小限界） | 限界幅でのレイアウト破綻防止、カード内最小余白の適用 |

### ④ アイコン・フォント規約
- **原則SVG化**: ユーザーから明示的な指定がない限り、**OS依存の絵文字はできる限り使用せず、スタイリッシュなインラインSVGアイコン**（アウトライン・モダンデザイン）に統一すること。
- **フォント**: `Zen Kaku Gothic New`, `Zen Maru Gothic`, `Inter` 等のモダンWebフォントを採用。

### ⑤ デザインリファレンス最優先参照 (`Reference/`)
- ボタンデザインやUI装飾を設計・実装する際は、リポジトリ内の **`Reference/`（`Reference/CSS/` 配下のCSSボタンデザイン集・PDF資料等）を最優先で参照**し、リッチで洗練されたスタイルを採用すること。
- `Reference/` フォルダはローカル資料用のため、**Git管理対象外（`.gitignore`）** として運用する。

### ⑥ カスタムスクロールバー仕様（背景透明化 ＆ テーマ統一）
- 全ツールのスクロールバーはブラウザデフォルトの白いトラック背景を排し、**トラック背景完全透明化（`background: transparent;`）** を適用する。
- つまみ（サム）は本体の境界線・テーマカラー（`--line-light` / `--moss` / `--fox` 等）と滑らかな角丸（`border-radius: 10px;`）を用いて一体化させる。
- `scrollbar-width: thin;` および `::-webkit-scrollbar` を併用して全ブラウザ・OBSドックで統一。

---

## 3. Twitch連携・IRC WebSocket・API仕様規約

### ① Twitch IRC WebSocket ハンドシェイク (`wss://irc-ws.chat.twitch.tv:443`)
- **Capability要求**: `CAP REQ :twitch.tv/tags twitch.tv/commands twitch.tv/membership`
- **匿名接続（読取専用）**: `PASS SCHMOOPIIE` / `NICK justinfan<ランダム数字>`
- **Bot認証（チャット送信可）**: `PASS oauth:<トークン>` / `NICK <botアカウント名>`
  - **推奨トークン生成**: [`https://twitchtokengenerator.com/`](https://twitchtokengenerator.com/)（旧tmi.twitchapps終了に伴う公式推奨代替）。必要スコープは `chat:read` および `chat:edit`。
- **接続完了判定**: `001` (Welcome)、`376` (End of MOTD)、`JOIN #<channel>` を検知して即時に「接続中」へステータス更新。
- **認証エラー検知**: `NOTICE * :Login unsuccessful` を検知し、ユーザーにトークン再確認を通知。
- **キープアライブ**: `PING` 受信時に即座に `PONG :tmi.twitch.tv` を返信。

### ② TitleManager コマンドタブ標準順序
1. **配信管理** (`stream`: !title, !game, /marker, /announce)
2. **広告管理** (`ads`: 30s, 60s, 3m)
3. **シャウトアウト** (`so`: /shoutout ID)
4. **モデレート** (`mod`: Clear, Unique, Poll, Prediction, Slow, Sub-only)
5. **コラボURL** (`collab`: multistre.am / twitchtheater.tv)

### ③ 日付自動挿入仕様
- `MM/DD (例: 05/12)` などの日付プレースホルダー置換機能。
- 初回起動時・未設定時の強制選択フォールバックロジックを常装。

---

## 4. Chrome拡張機能・ストア公開・法的ドキュメント規約

- **プライバシーポリシー標準要件**:
  - 「ユーザーの個人情報、チャットログ、画像データを外部サーバーへ送信・収集・共有しない」ことを明記。
  - Chromeウェブストア審査基準（単一用途ポリシー、最小限の権限要求）に完全準拠。
- **免責事項・ガイドライン**:
  - 各ツール内に公式免責事項（Twitch公式ツールではなくファンメイドである旨、API利用規約の遵守）を常設。

---

## 5. ドキュメント運用・ライフサイクル管理ルール

- **ドキュメントの優先順位**:
  - **`README_important.md`** ＞＞＞ **`README.md`**
- **`README_important.md`**: ライブラリ化・共通化された設計規約、ブランド、定数、API仕様を蓄積（常に最新かつ有効な情報のみを整理）。
- **`README.md`**: 日々のタスクサマリー・作業履歴ログ（作業ログが強め）。
- **`./Agent/Archive/` のクリーンアップ**:
  - 1ヶ月以上前の古い作業ログは、必要な重要事項を本 `README_important.md` へ移管・蓄積した上で、適宜削除してリポジトリを軽量に保つ。

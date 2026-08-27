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

## 4. 「きりぬきつーる」（Python / Desktop App）設計規約

### ① 基本技術スタック ＆ 依存関係固定ルール
- **GUI**: `CustomTkinter`（モダンダークテーマ標準）
- **動画・音声編集**: `moviepy<2.0.0` 固定（2.0.0以上の破壊的変更によるプレビュー・レンダリング不具合防止）
- **音声認識**: `openai-whisper`（PyTorch・CUDA対応、PyInstallerでのアセット・メタデータ同梱必須）
- **画像・動画プレビュー**: `OpenCV (cv2)`, `Pillow (PIL)`, `pygame.mixer`（音声シーク再生）

### ② 完全ローカル自己学習エンジン仕様 (`system_files/learned/learned_data.json`)
ユーザーの日常的な字幕編集履歴から完全ローカル（外部通信ゼロ）で継続学習する仕組み：
- **`vocabulary`（頻出固有名詞）**: ユーザーが編集した特有の単語を自動収集し、次回のWhisper実行時の `initial_prompt` へ自動注入。
- **`corrections`（自動誤字修正辞書）**: 「Whisperの誤変換 ➔ ユーザーの正解」の置換ペアを蓄積し、文字起こし直後に自動一括置換。
- **`stats`（学習統計）**: 累計学習回数を管理。設定画面からワンクリックでリセット可能。
- **Git管理対象外**: 個人学習データはプライバシー保護のため `.gitignore` 対象（`.gitkeep` のみ追跡）。

### ③ Gemini API連携 ＆ プロンプト設計仕様
- **モデル**: `gemini-1.5-flash`（`temperature: 0.3`, `topP: 0.95`）
- **5軸個別採点（各20点・合計100点満点 `score_breakdown`）**:
  1. `hook_stop_rate`（初速フック力・0〜3秒の離脱防止）
  2. `standalone_context`（文脈自立性・初見理解度）
  3. `emotional_peak`（感情ピーク強度・笑い/驚き/共感）
  4. `follow_through_power`（フォロー転換力・配信者魅力）
  5. `loop_timing_quality`（オチ＆ループ性・余韻0.5秒以内）
- **サムネイル最適フレーム抽出 (`thumbnail_frame`)**: 表情やリアクションが最も強い静止画サムネイル時刻を秒単位で抽出。
- **文脈自立性の自己監査 (`context_check`)**: 前後の配信文脈を知らなくても完結しているかの判定根拠を明記。
- **IN側の間判定**: クリップ開始直前に0.3秒以上の無音・間を確保して冒頭の単語切れを防止。

### ④ UI/UX・導線設計規約
- **Step 1（切り抜き候補）**:
  - メインヘッダーに `対象動画:` と `YouTube URL:`（`🌐 開く` ボタン付き）を配置し、プロンプト設定タブと双方向リアルタイム連動。
  - 左下に `✨ Gemini APIで自動解析` と `📋 コピペから読み込む` を並列配置。
- **全体設定**:
  - 「全体設定」タブを開いてすぐの第1画面に `🔑 Google Gemini API Key 設定` を大きく配置（表示切替・AI Studioリンク付き）。
  - `gemini_api_key_var` による一元管理（入力即時保持・自動保存）。
- **ディレクトリ構成の整理規約**:
  - ルート直下は `きりぬきつーる.exe`, `動画/`, `ショート/`, `画像/`, `system_files/` のみ配置。
  - ドキュメント・仕様書・画像は `system_files/docs/` に集約。

---

## 5. 「裏ガチャシステム」（Web Tool）設計規約

- **アーキテクチャ**: HTML/CSS/Vanilla JS 単一ファイル構成（サーバー不要・完全ローカル）。
- **配信中検知＆オフラインガード**:
  - 配信オフライン時はガチャ結果のチャット送信を無効化し、裏方・テストでの誤爆を完全防止。
- **天井（Pity）リセット管理**:
  - 全リスナーの天井リセットは「誤操作防止の2段階確認ダイアログ」を常装。
  - 当選時の個別天井リセットと連動。
- **Discord Webhook連携**:
  - 当選者のステータス（連絡済・素材受取済・未着手・作成中・納品済）をチェックリスト管理し、Discordスレッドへ自動ログ送信。
- **アクティブタイムアウト（15分）**:
  - 一定時間チャットのないリスナーを待機状態に遷移させ、アクティブな視聴者を正確に把握。

---

## 6. Chrome拡張機能・ストア公開・法的ドキュメント規約

- **プライバシーポリシー標準要件**:
  - 「ユーザーの個人情報、チャットログ、画像データを外部サーバーへ送信・収集・共有しない」ことを明記。
  - Chromeウェブストア審査基準（単一用途ポリシー、最小限の権限要求）に完全準拠。
- **免責事項・ガイドライン**:
  - 各ツール内に公式免責事項（Twitch公式ツールではなくファンメイドである旨、API利用規約の遵守）を常設。

---

## 7. ドキュメント運用・ライフサイクル管理ルール

- **ドキュメントの優先順位**:
  - **`README_important.md`** ＞＞＞ **`README.md`**
- **`README_important.md`**: ライブラリ化・共通化された設計規約、ブランド、定数、API仕様を蓄積（常に最新かつ有効な情報のみを整理）。
- **`README.md`**: 日々のタスクサマリー・作業履歴ログ（作業ログが強め）。
- **定期アーカイブ＆クリーンアップ**:
  - 作業ログが蓄積した場合は要点を `README.md` / `README_important.md` へ統合・整理し、不要となった過去ログファイルを削除してリポジトリを軽量・クリーンに保つ。

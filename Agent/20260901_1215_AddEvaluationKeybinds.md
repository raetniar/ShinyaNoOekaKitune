# StreamTalkAssistant 対話学習・セリフ評価キーバインド（T1/T2）実装 完了記録

- **実施日時**: 2026-09-01 12:15
- **11. petAI.jsの変数再宣言（SyntaxError）解消 ＆ 全JSモジュール読込完全同期**:
  - `petAI.js` 内で `let buddyName` などが `youka.js` と重複宣言されていたことによる構文エラーを解消。`typeof` による安全な条件代入・参照構造に改修。
  - `index.html` に未読込だった `gacha-engine.js`, `obs-websocket.js`, `petAI.js`, `art-stream-learner.js`, `stamp-manager.js`, `chat-summary-engine.js`, `cross-context-engine.js` の全スクリプトタグを漏れなく追加。
  - タブ切替関数（`switchTab`）において、カルテタブや設定タブを開いた際に自動で最新のリスナー一覧や設定UIを即時再描画するようブラッシュアップ。
  - パートナー計画側（実運用フォルダ）および `StreamTalkAssistant_shigu` への完全同期とブラウザ検証を実施（コンソールエラー0件、正常動作を確認）。
- **対象ツール**: StreamTalkAssistant / StreamTalkAssistant_shigu (初狐羽鹿 × ゆる狐AI「ようか」)
- **関連ファイル**:
  - `tools/StreamTalkAssistant/evaluation.html` (新規作成: 対話学習・返答評価マネージャー)
  - `tools/StreamTalkAssistant/index.html` (ヘッダー「学習」ボタン ＆ 吹き出しT1/T2ボタン追加)
  - `tools/StreamTalkAssistant/js/learning-engine.js` (対話ログ自動記録 ＆ キーバインド判定 ＆ 最新セリフ評価関数)
  - `tools/StreamTalkAssistant/js/tts.js` (speakYouka発話時の対話ログ自動記録フック)
  - `tools/StreamTalkAssistant/js/youka.js` (askGeminiLLMへのGood/Bad模範例プロンプト注入)
  - `tools/StreamTalkAssistant_shigu/evaluation.html` (同期)
  - `tools/StreamTalkAssistant_shigu/index.html` (同期)
  - `tools/StreamTalkAssistant_shigu/js/learning-engine.js` (同期)
  - `tools/StreamTalkAssistant_shigu/js/tts.js` (同期)
  - `tools/StreamTalkAssistant_shigu/js/youka.js` (同期)

---

## 🎯 実装内容と仕様

1. **ショートカットキー / キーバインドによるセリフ評価**:
   - `T1` または `1` (テンキー含む) ➜ 最新セリフ（または選択中のセリフ）を **👍 良い返事 (Good / 模範回答)** として評価。
   - `T2` または `2` (テンキー含む) ➜ 最新セリフ（または選択中のセリフ）を **👎 悪い返事 (Bad / NG例)** として評価。
   - `T3` または `3` / `0` (テンキー含む) ➜ **⚪ 未評価 (null)** に戻す。
   - 入力欄（`<input>`, `<textarea>`）フォーカス時はショートカットキーが暴発しないよう完全ガード。
2. **対話学習・返答評価マネージャー画面 (`evaluation.html`)**:
   - デフォルトは未評価（`rating: null`）として安全に記録。
   - 上下キー（`↑ / ↓` または `j / k`）でセリフを選択してキーボードだけで高速レビュー可能。
   - `E` キーで「理想の言い回し（模範回答）」の編集・登録モーダルを表示。
   - JSONファイルとしての保存・エクスポートおよび履歴一括クリア機能。
3. **メインUI (`index.html`) の連携**:
   - ヘッダーのセンサーバーに **「学習」ボタン** を配置し、クリックでいつでも `evaluation.html` を開けるように整備。
   - ようかの吹き出しカンペ右上に **`[T1] 👍 Good` / `[T2] 👎 Bad` ボタン** を設置し、マウス操作でもワンクリック評価可能。
4. **学習データのAI思考エンジンへの還元**:
   - `youka_golden_dialogues` (模範回答) および `youka_negative_dialogues` (NG回答) を `askGeminiLLM` のシステムプロンプトに自動注入し、評価を繰り返すほどようかの口調・返答クオリティが理想通りに洗練される仕組みを構築。
5. **自動おしゃべり（自律トークストリーム）停止防止 ＆ 堅牢化**:
   - **音声OFF（ミュート）時のループ継続**: 音声OFF時でも画面カンペ更新と遅延タイマーにより `tts-playback-ended` を発火させ、自律ループが停止しないよう改修。
   - **自律見守りハートビート（Watchdog Timer: 3秒ごと）**: 18秒以上沈黙が続いた場合に自動で次の話題を展開する自己復帰機構を新設。
   - **ブラウザTTS/VOICEVOXのスタック完全防止**: Web Speech APIのバックグラウンド抑制対策（定期resume）および最大15秒の強制アンロックセーフティを実装。
   - **全分岐フォールバック保護**: Gemini生成や即興ソングで例外が発生しても、必ず固定山札トークへフォールバックして発話を途切れさせない設計に強化。
6. **評価マネージャー（`evaluation.html`）のリアルタイム自動追加・同期**:
   - **画面の自動再描画（Auto-Sync）**: `BroadcastChannel('youka_evaluation_sync')` ＋ `storage` イベント ＋ 1.5秒ポーリングの3重同期を実装。配信管理画面（`index.html`）でようかが喋るたびに、別タブで開いた評価画面へ即座に新しいセリフカードがリアルタイム追加・表示されるよう改修。
7. **別タブ廃止 ＆ 配信管理画面への完全内蔵（3大タブ化）**:
   - ヘッダーの「学習」ボタンを押した際に別タブを開く動作を完全廃止し、**配信管理画面（`index.html`）内の「🎓 対話学習・セリフ評価」タブへ即座に切り替わるUI**へと統合。
   - OBSカスタムブラウザドックや単一ウィンドウ内で、セリフのリアルタイム確認・`T1`/`T2`ワンキー評価・理想セリフの編集・JSON保存がすべてシームレスに完結するように整備。
8. **全関連フォルダ（パートナー計画・shigu）への完全同期**:
   - `G:\マイドライブ\【02_UikoUka_活動】\パートナー計画\StreamTalkAssistant\`
   - `tools/StreamTalkAssistant_shigu/`
   上記すべての作業フォルダへ最新コードを完全同期反映。
9. **リスナーカルテ（`renderMemoryList`）の重要事項 ＆ コメント履歴の完全表示**:
   - リスナーCRMデータベース（`safeListenerDatabase`）から常連さん情報（`🌟 役割`, `🍴 好物`, `🎮 好きなゲーム`, `🌸 推しトピック`）を取得し、重要事項バッジとしてリッチ表示。
   - `listenerMemory` 内に直近コメント履歴（`recentComments`）を蓄積し、カルテカード内に「💬 直近のコメント履歴」を分かりやすく表示するように復元・強化。
   - `chatLogs` からのコメント履歴自動逆引き補完、および各リスナーへの **「✏ メモ（重要事項の直接入力・保存）」機能** を新設。
10. **リスナーノート（`Listener_Notes.md`）の一括インポート・読み込み機能の搭載**:
   - 「リスナーカルテ」タブのヘッダーに **「📥 ノート読込」ボタン** を新設。
   - `Listener_Notes.md` などのMarkdownファイルを選択するだけで、全リスナー情報（名前・ID・役職・通算コメント数・好物・ゲーム・累積トピック）を自動解析してカルテに一括インポート・統合する仕組みを実装。
   - 起動時にもCRMデータベースから常連リスナー一覧が自動でカルテに初期同期・表示されるように強化。
11. **petAI.jsの変数再宣言（SyntaxError）解消 ＆ 全JSモジュール読込完全同期**:
    - `petAI.js` 内で `let buddyName` などが `youka.js` と重複宣言されていたことによる構文エラーを解消。`typeof` による安全な条件代入・参照構造に改修。
    - タブ切替関数（`switchTab`）において、カルテタブや設定タブを開いた際に自動で最新のリスナー一覧や設定UIを即時再描画するようブラッシュアップ。
12. **不要モジュール（stamp-manager.js / obs-websocket.js）の完全オミット**:
    - `stamp-manager.js` (スタンプ管理) および `obs-websocket.js` (OBS WebSocket連携) をプロジェクトからオミット・ファイル削除。
    - `index.html` のスクリプト読み込みタグを整理・最適化。
    - 実運用フォルダ（パートナー計画）および `StreamTalkAssistant_shigu` への完全同期とブラウザ検証を実施（エラー0件・クリーン動作を確認）。
13. **学習データ専用フォルダ（`learned_data/`）の新設 ＆ JSON統合・クリーンアップ**:
    - `StreamTalkAssistant/learned_data/` フォルダを新設。
    - ルート直下に散らばっていた `youka_brain_2026-08-31.json`, `youka_brain_2026-08-31 (1).json`（重複・差分ファイル）を最新版（20発話・19語彙）へ統合し、`learned_data/youka_brain.json` として正規化格納。
    - 評価データ `youka_evaluations_2026-09-01.json`（54件のGood/Bad評価）を `learned_data/youka_evaluations.json` として正規化格納。
    - ルート直下の古い重複JSONファイルを完全削除し、フォルダ内をクリーンに整頓。
14. **別ファイル版 `evaluation.html` の完全オミット（ファイル削除）**:
    - `index.html` 内へ「対話学習・セリフ評価」タブとして完全統合されたため、単体ファイルとしての `evaluation.html` をプロジェクトから削除。
    - 実運用フォルダ（パートナー計画）および `StreamTalkAssistant_shigu` のHTMLファイルを `index.html` と `overlay.html`（OBS透過用）の2つにスッキリ整理。
15. **裏ガチャ設定の独立タブ化（「🎁 裏ガチャ設定」タブ新設・完全復活）**:
    - タブナビゲーションを 4大タブ（「👥 リスナーカルテ」「🎓 対話学習・セリフ評価」「🎁 裏ガチャ設定」「⚙️ ペット設定 ＆ OBS」）へ拡張。
    - `gacha-engine.js` と完全連動する「裏ガチャシステム設定 ＆ 当選者管理」UIセクションを独立タブ（`#tab-gacha`）として新設。
    - 必要視聴時間、当選確率、天井回数、連投防止CT、賞品URL/賞品名、Discord Webhook/スレッド連携、Twitch Bot OAuth、ようかちゃん返信テンプレート、リアルタイム当選者管理リストをすべて1クリックで直感的に設定・確認・保存可能に整備。
    - パートナー計画側（実運用フォルダ）および `StreamTalkAssistant_shigu` への完全同期を実施。

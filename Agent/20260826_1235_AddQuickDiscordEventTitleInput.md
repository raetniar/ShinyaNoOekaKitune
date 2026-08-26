# 20260826_1235_AddQuickDiscordEventTitleInput.md

## 目的
- 「全員の天井リセット」ボタンのすぐ下に、Discord発信時の景品タイトル（資料置き場タイトル）をサッと入力・編集できるスリムな入力バーを新設。

## 実装内容
1. **HTML/UI拡張 (`tools/裏ガチャシステム/index.html`)**:
   - セクション1（ルール設定）の「全員の天井リセット」ボタン直下に、Discordカラーをアクセントにしたスリムな入力バー（`#discordEventTitleQuick`）を配置。

2. **JavaScript連携**:
   - `loadData()` で初期値をロード。
   - `syncEventTitle(newTitle)`: セクション1のクイック入力欄（`discordEventTitleQuick`）とセクション4の入力欄（`discordEventTitle`）が双方向で完全リアルタイム同期するよう連携。

## 検証結果
- ブラウザ実機にて入力・値の保持（LocalStorage保存）・ページ再読み込み後の永続化を確認完了。

# 20260826_1300_UpdateDefaultActiveTimeoutTo15Min.md

## 目的
- アクティブ有効期限（コメント放置タイムアウト）の初期デフォルト値を「20分」から「15分」へ変更。

## 実装内容
1. **HTML & JavaScript (`tools/裏ガチャシステム/index.html`)**:
   - セクション1の `#cfgActiveTimeoutMinutes` の `value` および `placeholder` を `15` に設定。
   - `config.activeTimeoutMinutes` のデフォルト初期値・フォールバック値をすべて `15` に統一。

## 検証結果
- ブラウザ実機にて、設定ドロワー内の「アクティブ有効期限 (分 / 放置停止)」が `15` と表示され、リロード後も正常に保持されることを確認完了。

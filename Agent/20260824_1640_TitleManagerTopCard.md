# 目的

配信タイトル管理ツールをツール一覧の一部としてトップページに掲載する。

# 実装方針

- 既存の単体HTML `tools/Title_manager_localize_Ver0.4.html` は移動せず、そのまま利用する。
- ルートの `index.html` と同期用の `tools/index.html` に同一のツールカードを追加する。

# 変更履歴 / 検証

- 2026-08-24: 「配信タイトル管理」カードを追加。
- カードから `tools/Title_manager_localize_Ver0.4.html` へ遷移するリンクを設定。
- 2つのトップHTMLのSHA-256が一致することを確認する。

# 備考

タイトル管理ツールはブラウザ内の localStorage を利用する単体HTMLとして維持する。
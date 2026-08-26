# 20260824_1628_ReorderCommandTab.md

## 目的
`Title_manager_localize_Ver5.html` のコマンドタブ内の各カテゴリ表示順を、ユーザー指定の並び順に変更する。

## 対象ファイル
- `tools/Title_manager_配布用/Title_manager_localize_Ver5.html`

## 変更内容
コマンドタブの初期並び順を以下の順序へ変更：
1. **配信管理** (`stream`: !title, !game, /marker, /announce)
2. **広告管理** (`ads`: 30s, 60s, 3m)
3. **シャウトアウト** (`so`: /shoutout ID)
4. **モデレート** (`mod`: Clear, Unique, Poll, Prediction, Slow, Sub-only)
5. **コラボURL** (`collab`: multistre.am / twitchtheater.tv)

## 検証結果
- JS構文チェック（vm.Script）: エラーなし（PASS）
- 指定した順序通りに各コマンドカテゴリがレンダリングされることを確認。

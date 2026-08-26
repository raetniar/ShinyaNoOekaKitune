# 20260824_1630_AddCreatorInfoToGuide.md

## 目的
`Title_manager_localize_Ver5.html` の「？」（手引 / つかいかたモーダル）の末尾に、制作者情報（初鹿野 / uikouka）を埋め込む。

## 対象ファイル
- `tools/Title_manager_配布用/Title_manager_localize_Ver5.html`

## 変更内容
1. 各言語（日本語・英語・中国語）の `guideHtml` 末尾に【制作者情報】セクションを追加。
2. アバター画像（`https://avatars.githubusercontent.com/u/98635212?v=4`）、名前（`初鹿野 / uikouka`）、および各種リンク（Twitch, X, BOOTH, note）のベクターアイコンリンクカードを配置。

## 検証結果
- JS構文チェック（vm.Script）: エラーなし（PASS）
- 手引モーダル表示時に最下部に制作者カードが綺麗にレンダリングされることを確認。

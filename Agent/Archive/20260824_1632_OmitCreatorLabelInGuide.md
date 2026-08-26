# 20260824_1632_OmitCreatorLabelInGuide.md

## 目的
`Title_manager_localize_Ver5.html` の手引モーダル内の「【制作者情報】」という見出しラベルを削除（オミット）し、よりシンプルですっきりしたカード表示にする。

## 対象ファイル
- `tools/Title_manager_配布用/Title_manager_localize_Ver5.html`

## 変更内容
- `guideHtml` 内の `【制作者情報】` ラベルを削除。

## 検証結果
- JS構文チェック（vm.Script）: エラーなし（PASS）
- 手引モーダル最下部にラベルなしでカードのみがスマートに表示されることを確認。

# 20260824_1641_FixGuideHtmlUndefined.md

## 目的
`Title_manager_localize_Ver5.html` で英語（EN）や中国語（ZH）を選択した際に、手引モーダル（「？」ボタン）の中身が `undefined` になって表示されなかった問題を修正する。

## 原因
- 先程の言語辞書リファクタリング時に、`langMap.en` および `langMap.zh` の `guideHtml` プロパティが正常に紐付いていなかった。

## 変更内容
1. 日本語（`ja`）、英語（`en`）、繁体中文（`zh`）の各辞書に、それぞれ高品質にローカライズされた `guideHtml` を直接組み込み。
2. 販促カード（Twitch Manager）および制作者情報カード（初狐羽鹿 / uikouka）も全言語に完全収録。

## 検証結果
- `guideHtml` 文字数: ja: 9759文字 / en: 10295文字 / zh: 9522文字（すべて非ゼロ・完全収録）
- 各言語の販促カード数: ja: 1個 / en: 1個 / zh: 1個
- JS構文チェック（vm.Script）: エラーなし（PASS）

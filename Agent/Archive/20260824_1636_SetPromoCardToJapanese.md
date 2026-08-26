# 20260824_1636_SetPromoCardToJapanese.md

## 目的
`Title_manager_localize_Ver5.html` の手引モーダル内の「Twitch Manager」販促カードの表記を、言語設定にかかわらず日本語のオリジナル文言に統一する。

## 対象ファイル
- `tools/Title_manager_配布用/Title_manager_localize_Ver5.html`

## 変更内容
- 英語・中国語の手引データ内でも、販促カードは指定の日本語表記（「✨ より多機能な統合管理ツール「Twitch Manager」」/「Twitchのアレヤコレヤをすべて一つのdockで管理したいという人向けのツールです。」/「🛍️ BOOTHで見る」/「📦 GitHub Releases」）を表示するよう統一。

## 検証結果
- JS構文チェック（vm.Script）: エラーなし（PASS）
- どの言語モードでも指定の日本語メッセージでカードが表示されることを確認。

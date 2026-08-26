# 20260824_1645_LocalizePromoCardsByLanguage.md

## 目的
`Title_manager_localize_Ver5.html` の手引モーダル内の販促カード（Twitch Manager）について、英語（EN）および中国語（ZH）モード選択時に日本語のまま残っていた文言を、それぞれの言語に合わせた自然なプロ翻訳に完全対応させる。

## 対象ファイル
- `tools/Title_manager_配布用/Title_manager_localize_Ver5.html`

## 変更内容
1. **英語（EN）**:
   - タイトル: `✨ All-in-One Dock Tool: "Twitch Manager"`
   - 説明文: `An all-in-one dock tool designed for streamers who want to manage everything on Twitch from a single dock.`
   - ボタン: `🛍️ View on BOOTH` / `📦 GitHub Releases`
2. **中国語（ZH）**:
   - タイトル: `✨ 多功能整合管理工具「Twitch Manager」`
   - 説明文: `专为想在一个 OBS Dock 中搞定 Twitch 所有直播管理操作的主播打造。`
   - ボタン: `🛍️ 在 BOOTH 查看` / `📦 GitHub Releases`
3. **日本語（JA）**:
   - タイトル: `✨ より多機能な統合管理ツール「Twitch Manager」`
   - 説明文: `Twitchのアレヤコレヤをすべて一つのdockで管理したいという人向けのツールです。`
   - ボタン: `🛍️ BOOTHで見る` / `📦 GitHub Releases`

## 検証結果
- `langMap.ja`, `langMap.en`, `langMap.zh` 内の各テキスト・ボタン文言の一致検証: すべて `true`（PASS）
- JS構文チェック（vm.Script）: エラーなし（PASS）

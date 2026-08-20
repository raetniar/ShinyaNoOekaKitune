# 作業計画・記録: 全ツールページのデザイン統一（Stickyヘッダー・レスポンシブ・背景ウォーターマーク・トップカード追加）

- **日付**: 2026-08-20
- **タスク名**: DesignStandardizationAllTools
- **目的**: トップページ（`index.html`）の洗練されたデザイン世界観を崩さず、全ツールページ（`tools/` 配下）のヘッダー仕様（`position: sticky`）、レスポンシブ時のツールチップ挙動、ボタンやフォント、背景ウォーターマーク表示（右下固定・切り抜きなし・透過）をプロ品質に統一し、トップページのコレクション一覧にTwitchチャンネルカード（Card 6）を追加・説明文を更新する。

---

## 1. 統一仕様（デザインスタンダード）
1. **ヘッダー仕様**:
   - `position: sticky; top: 0; left: 0; right: 0; width: 100%; box-sizing: border-box; z-index: 1000;`
   - `body { padding-top: 0 !important; }`
   - コンテンツ上部マージン: `.app-container, .tool-main-container, main, .app-main-layout { margin-top: 16px !important; }`
2. **タイトル行 & 盾マーク（安全性表示）**:
   - `.tool-title-row { display: flex; align-items: center; gap: 8px; flex-wrap: nowrap !important; }`
   - `.tool-name-heading { white-space: nowrap !important; }`
   - アバターアイコン・タイトル・盾マークの改行を完全阻止。
   - `@media (max-width: 1024px)` でサブ説明文・安全性テキストを非表示にし、盾マークホバーでツールチップ（`pointer-events: none; max-width: 300px;`）表示。
3. **右側アクションボタン（レスポンシブ連動）**:
   - `[ライト/ダーク切替]` `[Booth]` `[TOPに戻る]`
   - `@media (max-width: 1024px)` でボタンテキスト（`.btn-text`）を非表示化し、**アイコンのみのコンパクト表示**に切り替え。ウィンドウ幅縮小時のヘッダー窮屈さ・改行崩れを完全解消。
4. **背景ウォーターマーク装飾（右下固定・切り抜きなし）**:
   - 画像: `https://avatars.githubusercontent.com/u/98635212?v=4`
   - 配置: `position: fixed; right: 12px; bottom: 12px;`
   - サイズ: `width: min(40vw, 45vh, 360px); height: min(40vw, 45vh, 360px);`（横幅40%以下、縦は画面内に収まる設計）
   - 切り抜き: `border-radius` なし（元のアートワーク・四角形のまま自然に配置）
   - 透明度: 10〜12%（ダークモード 0.12 / ライトモード 0.09）
   - 操作阻害防止: `pointer-events: none; user-select: none; z-index: 0;`
5. **トップページ（コレクション一覧）Card 6 のデザイン・文言調整**:
   - 淡い水色のグラデーション背景（`thumb-color-2`）と50%アイコン（`72px × 72px`）。
   - 説明文: 「不定期にだいたい深夜23時以降などにTwitchにて生息・配信中。ソロゲーム実況やお絵描きなどを主にしています。」
   - リンク先: `https://www.twitch.tv/uikouka`
6. **タイポグラフィ & カラーシステム**:
   - フォント: `Outfit`, `Noto Sans JP`
   - モード切替（`body.light-mode` / `body.dark-mode`）の美しいコントラスト維持。
7. **クリーンアップ**:
   - 不要な `beta-notice` バナーおよび重複したアバター/ロゴアイコンの削除。

---

## 2. 適用完了ファイル一覧
1. **トップページ（Collection & Portal）**
   - `index.html`
   - `tools/index.html`
2. **Twitch Image Resizer**
   - `tools/Twitch_Image_Resizer/index.html`
   - `tools/Twitch_Image_Resizer/Twitch_Image_Resizer.html`
   - `tools/Twitch_Image_Resizer/Twitch_Image_Resizer_02.html`
   - `tools/Twitch_Image_Resizer/css/style.css`
3. **SVG Calendar Generator**
   - `tools/SVGCalendarGenerator.html`
4. **OBS Asset Manager**
   - `tools/OBS_AssetManager_damo.html`
5. **Twitch Panel Editor**
   - `tools/Twitch_Panel_Editor/index.html`
   - `tools/Twitch_Panel_Editor/Twitch_Panel_Editor.html`
   - `tools/Twitch_Panel_Editor/css/style.css`
6. **Twitch Manager**
   - `tools/TwitchManager/TwitchManager.html`
   - `tools/TwitchManager/build_demo.py`

---

## 3. 検証結果
- トップページのCard 6オーバーレイ説明文が指定通りの新しい文言に更新されていることを確認。

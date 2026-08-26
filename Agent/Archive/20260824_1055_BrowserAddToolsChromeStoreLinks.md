# BrowserAddTools Chromeウェブストア公式リンク差し替え作業

## 目的
`tools/BrowserAddTools/index.html` 内の拡張機能（Shopping Stream Privacy Filter、TW-Alert）について、BOOTHのダウンロードリンクからChromeウェブストアの公式公開URLへ差し替え・リンク配置を行う。

## 対象URL
1. **Shopping Stream Privacy Filter**:
   `https://chromewebstore.google.com/detail/shopping-stream-privacy-f/peoalpmdnnhebdhnpphjeehgogchjigp`
2. **TW-Alert: Stream Notifier**:
   `https://chromewebstore.google.com/detail/tw-alert-stream-notifier/jjaaggndajhobhhgddpooepalojhompi?hl=ja`

## 作業予定 / 実装方針
1. `tools/BrowserAddTools/index.html` 内の各カード内ボタン、および右側詳細エリアのアクションボタンをChromeウェブストア公式リンクへ更新。
2. ボタンデザイン（`.chrome-store-btn` 等）をChromeアイコン（`fa-brands fa-chrome`）付きでスタイリング。
3. 変更後の表示確認・リンク整合性の検証。

## 変更履歴 / ログ
- 2026-08-24:
  - `tools/BrowserAddTools/index.html` 内のリンクを更新：
    - `Shopping Stream Privacy Filter` のダウンロード先を Chrome ウェブストア公式リンク（`peoalpmdnnhebdhnpphjeehgogchjigp`）へ差し替え。
    - `TW-Alert: Stream Notifier` のダウンロード先を Chrome ウェブストア公式リンク（`jjaaggndajhobhhgddpooepalojhompi`）へ差し替え。
    - カード内オーバーレイボタンに `.store-btn`（Chromeアイコン付き）を適用。
    - 各ツールの詳細解説エリア下部にダイレクトアクセス用の `.tool-action-row`（`.btn-store-main` / `.btn-booth-main` / `.btn-doneru-main`）を新設。
    - `Shopping Stream Privacy Mask` の紹介文言を「お名前・お届け先住所・注文履歴・干し芋リスト」から「お名前・お届け先住所など個人情報」へ修正。
    - `Browser Screen Filter` のBOOTHリンクを解除し、カード内および詳細エリアのボタンを「公開待機中」（`.btn-disabled` / `.btn-disabled-main`）に変更。
    - Zip配布版の導入手順マニュアルセクション（`#sec-manual`）および関連CSSを削除。
  - レスポンシブおよびデザイン表示確認を実施し、整合性を検証完了。
  - ユーザー指示に基づき、`main` ブランチへコミット＆プッシュ完了（Commit: `e91af21`）。

## 残課題 / 備考
- `Browser Screen Filter` は現在「公開待機中」表示。今後Chromeウェブストアで公開された際に同様にURLを配置可能。

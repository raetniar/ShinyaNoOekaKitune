# Amazon紹介枠

## 目的 / 方針
ユーザー提供のミネラルウォーターのアソシエイトリンクを、LIVEとWORKSの間に1件配置。本文を邪魔しない横長枠、スマホは縦配置。広告ラベルと参加表記を同じ枠内に明示。

## 変更
- index.html: aside#break追加。ASIN B092D5HM5S、tag=raetniar-22、th=1、linkCode/linkId/ref_を保持。検索結果由来のdib/qid等のみ除去。
- assets/hub.css: 既存の昼夜配色変数を使う局所スタイル。追加ライブラリ・外部画像・追跡スクリプトなし。
- 提供URLのスラッグから商品分類を記載。Amazon商品ページの取得は失敗したため、商品名の詳細、容量、本数、価格、味、成分、愛用実績を掲載しない。
- 文案はWeb版Claudeの同じチャットで添削し、回答完了を確認して最終案を採用。
- Claude: https://claude.ai/chat/d07f0a7b-c9b8-4693-8a30-564051bd0e98
- 公式参加表記の参照: https://affiliate.amazon.co.jp/help/node/topic/GPXFHVYZMTGPUMPE
- バックアップはチェックアウト外 ../index-before-affiliate.html, ../hub-before-affiliate.css。

## 残課題
楽天の実リンクは未提供。追加しない。

# 作業記録: スマホ用 Multi-Stream Viewer の新規開発

## 1. 目的
- スマホ（縦画面・横画面）環境において軽量・低負荷で複数Twitch配信を同時視聴できるWebツール「スマホ用 Multi-Stream Viewer」を新規作成する。
- Twitch公式チャットへのログインおよびコメント投稿を完全サポートし、片手でも直感的に操作できるモバイルファーストなUXを実現する。

## 2. 作業予定 / 実装方針
- 対象ディレクトリ: `tools/スマホ用multiStreamViewer/`
  - `index.html`: アプリ構造、モーダル、UIコンポーネント
  - `css/style.css`: モバイル特化レイアウト（縦2分割/2x2/フォーカス/PIP）、Twitchダーク/ライトテーマ、セーフエリア対応
  - `js/app.js`: 配信プレイヤー管理、ソロ音声排他制御、チャットドロワー制御、URL同期、プリセット/履歴保存
  - `README.md`: 使用手順と機能仕様
- ポータル連携: `index.html` および `tools/index.html` にツールカードを追加

## 3. 変更履歴 / ログ
- 2026-08-25 12:05: 実装計画書作成および設計確定。
- 2026-08-25 12:06: 
  - `tools/スマホ用multiStreamViewer/css/style.css` 作成（ゼロフレームワーク高パフォーマンスCSS）
  - `tools/スマホ用multiStreamViewer/js/app.js` 作成（状態管理、URLクエリ/ハッシュ同期、チャット埋め込み、ソロ音声、プリセット機能）
  - `tools/スマホ用multiStreamViewer/index.html` 作成（モバイル最適化UI、下部フローティングアクションバー、チャットボトムシート）
  - `tools/スマホ用multiStreamViewer/README.md` 作成（ドキュメント整備）
  - `index.html` および `tools/index.html` に新規カードを同期追加
- 2026-08-25 12:15:
  - 既存のTMSD（Twitch Multi-Stream Dashboard）機能を統合。
  - バッチファイル・Pythonプロキシサーバー不要の完全スタンドアロンWebアプリ化。
  - YouTube配信・動画（`youtube.com/watch?v=...`, `youtu.be/...`, `youtube.com/live/...`）およびYouTubeライブチャットの同時埋め込み対応。
  - `Twitch.Embed` SDK連携、マルチparent（`localhost`, `127.0.0.1`, `location.hostname`）対応。
  - `file:///` 実行時の案内バナーと各配信カードへの直接ポップアウトボタン追加。

## 4. 残課題 / 備考
- Twitch埋め込みの親ドメイン（parent）仕様について、ローカル直接起動（`file://`）はTwitchサーバー側で拒否されるため、Web公開（GitHub Pages等）またはローカルサーバー（Live Server等）経由での起動が必須。
- YouTube配信はローカル（`file://`）でもWebでも直接再生可能。

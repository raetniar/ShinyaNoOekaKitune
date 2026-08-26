# 20260826_1117_CustomScrollbarColoring.md

## 目的
- 裏ガチャシステム（`tools/裏ガチャシステム/index.html`）のスクロールバー背景を完全透明化し、つまみ（サム）の色味をダークモス・フォックステーマに調和させる。
- リポジトリ設計マスタ（`Agent/README_important.md`）に共通スクロールバー規約を恒久化。

## 実装内容
1. **裏ガチャシステム (`tools/裏ガチャシステム/index.html`)**:
   - `scrollbar-width: thin;` および `scrollbar-color: var(--line-light) transparent;` を全要素に適用。
   - WebKit系（Chrome, Edge, OBSブラウザドック）向けに `::-webkit-scrollbar-track { background: transparent; }` を適用し、トラック背景を完全透明化。
   - `::-webkit-scrollbar-thumb` に `--line-light`（通常時）、`--moss`（ホバー時）、`--fox`（アクティブ時）の段階的グラデーションと角丸10pxピルスタイルを実装。

2. **共通規約 (`Agent/README_important.md`)**:
   - 「⑥ カスタムスクロールバー仕様（背景透明化 ＆ テーマ統一）」を追記。

## 検証結果
- ブラウザ実機にてスクロール動作・透明背景・ホバー時のカラー変化を確認完了。

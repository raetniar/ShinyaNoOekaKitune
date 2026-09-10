# 20260909_1420_FixDrawerToggleButtonPositionAndOverlap.md

## 目的
コンパクトモード（幅狭画面表示時）において、画面上部に浮動配置されていた「☰ 編集ツール」ボタン（FAB）が、時間制御パネル（シークバー・範囲指定・「⏱ 微調整 ▼」ボタン）の右端と縦横位置で完全に被って重なっていた問題を解消する。

## 原因分析
- `app.py` の `update_responsive_layout` において、`drawer_toggle_btn.place(relx=0.98, rely=0.18, anchor="ne")` と相対比率（`rely=0.18`）で画面全体フレーム（`rf`）に対して配置されていた。
- ヘッダーが折りたたまれた際やウィンドウ縦幅に応じて `rely=0.18` の縦位置が Row 1 の `time_row2`（範囲指定・微調整行）と完全に一致してしまい、「⏱ 微調整 ▼」ボタンの上に「☰ 編集ツール」ボタンが覆いかぶさって操作不能になっていた。

## 実装方針
1. **親ウィジェットのプレビューコンテナ化**:
   - `self.drawer_toggle_btn` の親を `self.preview_container`（Row 2）に変更。
   - 上段の時間制御バー（Row 1 の `time_ctrl`）とは行・境界が完全に分離され、物理的に被る可能性を100%排除。
2. **プレビュー右上余白への安定配置**:
   - `self.drawer_toggle_btn.place(relx=0.98, y=10, anchor="ne")` に変更。
   - プレビュー領域の上端から10px下、右端から2%左の余白スペース（ユーザーが直感的に指示したオレンジの丸の位置）にピタッと安定配置。
3. **コンパクト＆洗練されたピル型デザイン**:
   - 幅115px、高さ30px、角丸15pxに最適化。
   - 動画リサイズ時（`on_preview_container_configure`）にも `self.drawer_toggle_btn.lift()` を実行し、常に最前面に維持。

## 変更履歴 / 検証ログ
- `system_files/src/app.py`:
  - `setup_drawer_components`: 親を `self.preview_container` に設定、ボタンサイズ・角丸最適化。
  - `update_responsive_layout`: `place(relx=0.98, y=10, anchor="ne")` に変更。
  - `on_preview_container_configure`: リサイズ時の `lift()` 呼び出しを追加。
- 構文検証（`py_compile`）: 正常通過（エラーなし）。
- PyInstallerビルド＆最新EXE配備。

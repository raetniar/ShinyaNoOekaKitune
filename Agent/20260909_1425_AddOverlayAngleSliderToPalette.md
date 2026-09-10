# 20260909_1425_AddOverlayAngleSliderToPalette.md

## 目的
ポップアップ／パレット（ドロワー）内の「画像演出 (オーバーレイ)」設定エリアにおいて、メイン側のタブ2「画像演出」には実装されていた「角度（回転）」スライダーおよび「不透明度」スライダーが存在しなかったため、パレット側にも「角度 (-180° 〜 +180°)」スライダーおよび「不透明度 (0.00 〜 1.00)」スライダーを追加し、メイン画面・プレビュー動画描画・リセット処理との双方向完全同期を実現する。

## 実装方針
1. **パレット内UIの拡張 (`system_files/src/app.py`)**:
   - `setup_palette_styles`:
     - 「倍率」スライダーの直下に「角度 (-180° 〜 +180°)」スライダー（`p_overlay_angle_slider`）およびラベル（`p_overlay_angle_lbl`）を追加。
     - 「不透明度 (0.00 〜 1.00)」スライダー（`p_overlay_opacity_slider`）およびラベル（`p_overlay_opacity_lbl`）を追加。
     - リセットボタンの文言を「画像の位置・回転・倍率をリセット」に変更。
2. **双方向同期ハンドラの実装**:
   - パレット側ハンドラ:
     - `on_palette_overlay_angle_changed(self, v)`: メイン側の `overlay_angle_slider` / `overlay_angle_lbl` と同期し、`on_text_style_changed()` でプレビュー動画を再描画。
     - `on_palette_overlay_opacity_changed(self, v)`: メイン側の `overlay_opacity_slider` / `overlay_opacity_lbl` と同期。
   - メイン側ハンドラ:
     - `on_overlay_angle_slider_changed(self, v)`: パレット側の `p_overlay_angle_slider` / `p_overlay_angle_lbl` へ同期。
     - `on_overlay_opacity_slider_changed(self, v)`: パレット側の `p_overlay_opacity_slider` / `p_overlay_opacity_lbl` へ同期。
3. **リセット＆ジョブ切り替え時の同期**:
   - `reset_overlay_transform`: パレット側角度（0.0°）および不透明度（1.00）のリセット処理を追加。
   - `render_subtitle_editor_from_active_job`: 切り抜き候補切り替え時に、パレット側の位置・倍率・角度・不透明度スライダーを保存値へ一括同期。
4. **PyInstaller によるスタンドアロンEXEの再ビルド＆配備**。

## 変更履歴 / 検証ログ
- `system_files/src/app.py`:
  - `setup_palette_styles`: 角度スライダー、不透明度スライダーのUI要素を追加。
  - `on_palette_overlay_angle_changed`, `on_palette_overlay_opacity_changed`: 同期ハンドラ実装。
  - `on_overlay_angle_slider_changed`, `on_overlay_opacity_slider_changed`: パレット側同期を追加。
  - `reset_overlay_transform`: パレット側リセット追加。
  - `render_subtitle_editor_from_active_job`: ジョブ切り替え時同期追加。
- 構文検証（`py_compile`）: 正常通過（エラーなし）。
- PyInstallerビルド＆最新EXE配備。

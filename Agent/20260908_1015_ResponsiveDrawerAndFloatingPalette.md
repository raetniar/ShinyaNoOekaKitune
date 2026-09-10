# 20260908_1015_ResponsiveDrawerAndFloatingPalette.md

## 1. 目的
- 『きりぬきつーる』（`tools/きりぬきつーる`）において、幅が狭い画面（ノートPC、分割表示、低解像度環境等）におけるUI/UXを再定義。
- 従来の「縦1列スタック（プレビュー・字幕・スタイルが縦長に積み重なり画面外へ押し出される問題）」を解消し、**「プレビューの常時大画面表示」** を最優先に維持した上で、編集ツールを **「右からスライドインするオーバーレイドロワー（案A）」** および **「半透明でプレビュー動画を透かして見れる別ウィンドウ透過フローティングパレット（案C）」** を自由に切り替えられるハイブリッドUIを実装・配備する。

---

## 2. 実装方針とUI/UX設計

### ① プレビュー絶対表示（大画面・アスペクト維持）
- ウィンドウ幅が 900px 未満になった際、自動的にコンパクトレイアウトへ切り替え。
- プレビュー領域（`preview_container`）を全幅・全高に最優先拡張（Row 2, Column 0-3）。
- 既存の `on_preview_container_configure` の 9:16 アスペクト自動計算により、画面中央に最も大きなプレビューが美しいベゼル枠で表示される。
- 上部には再生・一時停止・外部再生・シークバー・範囲指定・微調整トグル（`time_ctrl`）を横幅いっぱいに配置し、プレビューの動画制御を常時快適に保つ。

### ② 【案A（標準・初期状態）】右スライドイン・オーバーレイドロワー
- 画面右上にスタイリッシュな青色FABボタン（`self.drawer_toggle_btn`:「☰ 編集ツール」）を配置。
- ボタン押下で、画面右側からオーバーレイドロワー（`self.drawer_bg_frame`: 背景 `#12151b`、境界線 `#3b82f6`）が展開。
- ドロワーヘッダーにセグメントボタン（`["📝 字幕編集", "🎨 スタイル設定"]`）を配置し、省スペースで両方の編集機能へワンタップで切り替え可能。
  - **「📝 字幕編集」選択時**: 字幕タイムライン（`sub_scroll`）と下部固定アクションボタン（`bottom_action_box`）をドロワー内に配置。
  - **「🎨 スタイル設定」選択時**: スタイル・キャラクタ設定（`char_panel`）をドロワー内に配置。
- 「✕ 閉じる」またはトグルボタン押下でスムーズに収納され、プレビュー全画面表示へ復帰。

### ③ 【案C（選択可能）】透過フローティングパレット
- ドロワーヘッダーの「🪟 透過化」ボタンをクリックすると、即座に独立した半透明ウィンドウ（`self.floating_palette`: `ctk.CTkToplevel`）が浮遊。
- `attributes("-alpha", self.palette_alpha)` により、パレット越しに背後のプレビュー動画がリアルタイムに透けて見える。
- ヘッダーバーに「透過度スライダー（0.40〜1.00）」と「📌 ドロワーに戻す」ボタンを完備。
  - スライダー操作で透過率がリアルタイムに変化し、設定（`palette_alpha`）に自動保存。
  - 「📌 ドロワーに戻す」をクリックするとパレットが破棄され、元のドロワーモード（案A）へスムーズに復帰。
- パレット内にも「📝 字幕クイック編集」「🎨 スタイル設定」タブを内蔵し、字幕編集やスタイル変更がメインのプレビュー画面へ即時反映される。

### ④ ワイドモード（幅900px以上）との完全同期
- ウィンドウ幅を広げると、自動的にドロワーやパレットを整頓し、従来の洗練された「3カラム並列ワイドモード（左: プレビュー / 中央: 字幕 / 右: スタイル）」へ破綻なく復帰。

---

## 3. 変更履歴 / 検証ログ

1. **`app.py` の修正**:
   - `App.__init__` に `compact_mode_active`, `drawer_open`, `compact_submode`, `palette_alpha`, `floating_palette`, `drawer_active_tab` を初期化。
   - `self.time_ctrl` をインスタンス変数化し、レスポンシブ切り替えで上部全幅配置を可能に。
   - `setup_drawer_components(rf)`: ドロワー背景、ヘッダー、セグメントボタン、FABトグルボタンの初期化。
   - `toggle_drawer`, `show_drawer_content`, `hide_drawer_content`, `update_drawer_tab_content`, `on_drawer_tab_changed`: ドロワー開閉およびコンテンツ切り替えロジック。
   - `switch_to_palette_mode`, `switch_to_drawer_mode`, `open_floating_palette`, `close_floating_palette`, `on_palette_alpha_change`, `setup_palette_subtitles`, `setup_palette_styles`, `refresh_palette_subtitle_list`: 案C 透過パレットのライフサイクル・UI・透過度制御・データ連動。
   - `render_subtitle_editor_from_active_job`: パレット起動時の字幕リスト自動同期処理を追加。
   - `update_responsive_layout`: 幅 900px 未満でのプレビュー絶対表示＆ドロワー/パレット表示への刷新。

2. **静的解析・テスト**:
   - `ruff check system_files/src --select=F,E9,RUF013` ➔ **All checks passed (0 errors)**
   - `python -m py_compile system_files/src/app.py` ➔ **OK**
   - 単体・結合テスト (`test_drawer_palette.py`):
     - `test_drawer_toggle`: ドロワーの開閉・ボタン表示切り替え ➔ **PASS**
     - `test_palette_mode_switch`: 案Cへの切り替え、透過度変更、案Aへの復帰 ➔ **PASS**
     - `test_responsive_narrow_mode`: 幅800pxでの狭小モード移行 ➔ **PASS**
     - `test_responsive_wide_mode_restore`: 幅1200pxでのワイドモード復元 ➔ **PASS**
     - 総合判定: **OK (4/4 passed)**
   - 既存統合テスト (`comprehensive_test.py`): 全テスト **PASS**

3. **スタンドアロン EXE 再ビルド＆配備**:
   - `きりぬきつーる.spec` を PyInstaller で再ビルド（exit code 0）。
   - 生成された最新バイナリ（338,978,536 bytes / 約323MB）をルートの `tools/きりぬきつーる/きりぬきつーる.exe` へ上書き配備完了。
   - 最終ビルド日時: 2026-09-08 10:13:25

---

## 4. 残課題 / 備考
- 次回起動時もユーザーが選択したモード（案A / 案C）および透過度（0.40〜1.00）が `config.json` から安全に復元される設計となっている。

# 作業記録: 画像演出タブのコンパクト化（アンカーマス左配置＆プリセット・ボタン右配置）

## 目的
ユーザーからの指示画像に基づき、「画像演出」タブ上部のレイアウトをコンパクト化：
- 左側: □と十字のアンカーマス（`AnchorSelector`）
- 右側:
  - 上段: プリセット画像の選択ドロップダウン（`preset_menu`）
  - 下段: フォルダを開くボタン（`📁`）とリロードボタン（`🔄`）を横並び2分割均等配置

## 変更内容
1. **`system_files/src/app.py`**:
   - `AnchorSelector.__init__`:
     - `layout="vertical"` オプションと `canvas_size` 引数を追加。
     - マスの下に「基準: 中央」ラベルをコンパクトに配置可能に拡張。
   - `setup_char_panel` の `tab_img`:
     - `compact_top_box` による左右2カラムグリッドを構築。
     - 左列（column=0）に `AnchorSelector(..., layout="vertical", canvas_size=60)` を配置。
     - 右列（column=1）の上段に `preset_menu`、下段に `preset_folder_btn` と `preset_reload_btn` を横並び配置。
     - 縦幅が大幅に圧縮され、スライダー領域のスクロール負担を軽減。
   - サブタイトルEntryの `bind` コールバックを `lambda event=None:` に安全化。

## 検証結果
- `py_compile`: Exit code 0
- 自動テスト（`test_sub_ui.py`, `test_auto_queue.py`）: 全項目Pass

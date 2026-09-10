# 20260908_1205_VideoAndYoutubeUrlIntegratedManager.md

## 1. 目的
- 『きりぬきつーる』（`tools/きりぬきつーる`）において、元動画とYouTube URLをセットで管理し、後日の作業復元や複数動画の連続処理を圧倒的に効率化するための統合管理システムを実装。
- ユーザー要望に基づき、**「案1: 同名テキスト自動検出（サイドカー）」**、**「案2: テキスト/CSV動画リスト読込（プレイリスト）」**、**「案4: フォルダ一括スキャン＆マニフェスト出力」** を1つの調和した仕組みとしてUI/UXへ統合・配備する。

---

## 2. 実装方針と機能詳細

### ① 【案1】同名テキスト自動検出＆ワンタップ保存（サイドカー方式）
- **自動ロード**:
  `select_video()` で動画が選択された際、またはプレイリストで動画が切り替わった際に、同じフォルダ内の同名ファイル（`動画名.txt`、`動画名.url`、`動画名_url.txt`）を自動探索。
  正規表現（`https?://...` または `URL=...`）によりYouTube URLを抽出し、ヘッダーのYouTube URL欄へ自動入力。
- **ワンタップ保存**:
  ヘッダーの「💾 URL保存」ボタンを押すことで、現在の動画と同じ場所に `動画名.txt`（中身にYouTube URL）を即座に出力・更新。次回から完全自動ロードされる。

### ② 【案2】テキスト/CSV/TSV動画リスト一括インポート（プレイリスト型）
- ヘッダーの「📋 リスト」ボタンから、カンマ/タブ/パイプ区切りのリストファイル（`video_list.txt` / `.csv` / `.tsv`）を一括インポート。
  - フォーマット: `動画パスまたはファイル名, YouTube_URL, メモタイトル`
  - 相対パスはリストファイル基準で絶対パス自動解決。
- 読み込み後、ヘッダーに「作業リスト: `[1/5] 🔗 01_動画.mp4 ▼`」プルダウンが出現。
- ドロップダウン選択、または「◀ 前へ」「次へ ▶」ボタンを押すだけで、元動画とYouTube URLがセットで瞬時に切り替わる。

### ③ 【案4】フォルダ一括スキャン＆マニフェスト出力
- ヘッダーの「📂 フォルダ」ボタンから作業動画フォルダを選択。
- フォルダ内の全動画（`.mp4`, `.mkv`, `.mov`, `.avi`, `.webm`）を自動検出。
- フォルダ内の `video_list.txt` や各動画の「同名テキスト（案1）」からURLを自動集約してプレイリスト化。
- 「💾 リスト書き出し」ボタンを押すことで、フォルダ内に `video_list.txt` を自動生成。

### ④ ヘッダーUIの拡張（常時可視化）
- 対象動画の直下に「YouTube URL入力欄」と「💾 URL保存」ボタンを常時配置。
  どのタブ（候補・編集・書き出し）からでも動画とURLの組み合わせが一目で確認可能に。
- 広幅（wide）および狭幅（narrow）の両レイアウトに完全対応。

---

## 3. 変更履歴 / 検証ログ

1. **`app.py` の修正**:
   - `App.__init__` に `video_playlist`, `playlist_active_idx`, `current_scanned_folder` を追加。
   - `setup_run_tab`: ヘッダーに動画ボタングループ（参照 / リスト / フォルダ）、YouTube URL入力欄、URL保存ボタン、プレイリストフレームを追加。
   - `apply_header_layout`: 広幅・狭幅両方で動画・YouTube・プレイリスト要素が綺麗に整列するようレイアウト定義を更新。
   - ロジック追加:
     - `detect_and_load_sidecar_url(video_path)`
     - `save_sidecar_url()`
     - `load_video_playlist_file()`
     - `scan_video_folder()`
     - `update_playlist_ui()`
     - `load_playlist_item(idx)`
     - `on_playlist_item_selected(selection)`
     - `select_prev_playlist_item()`
     - `select_next_playlist_item()`
     - `export_playlist_to_file()`
     - `clear_playlist()`
     - `select_video`: 動画手動選択時に `detect_and_load_sidecar_url` を自動呼び出し。

2. **静的解析・テスト**:
   - `ruff check system_files/src --select=F,E9,RUF013` ➔ **All checks passed (0 errors)**
   - `python -m py_compile system_files/src/app.py` ➔ **OK**
   - 単体テスト (`test_video_url_manager.py`):
     - `test_sidecar_txt_detection`: .txt からのURL自動検出 ➔ **PASS**
     - `test_sidecar_url_file_detection`: .url からのURL自動検出 ➔ **PASS**
     - `test_playlist_loading_and_selection`: プレイリスト切り替え・前へ次へ ➔ **PASS**
     - **3/3 全テスト合格 (OK)**
   - 既存テスト (`test_drawer_palette.py`, `comprehensive_test.py`): 全テスト **PASS**

3. **スタンドアロン EXE 再ビルド＆配備**:
   - PyInstaller で再ビルドを実施。
   - `tools/きりぬきつーる/きりぬきつーる.exe` へ最新バイナリを上書き配備完了。

---

## 4. 残課題 / 備考
- プレーンテキストファイル（`.txt`）を標準としているため、メモ帳やExcel、スプレッドシート等で自由にURLリストを編集・共有可能。

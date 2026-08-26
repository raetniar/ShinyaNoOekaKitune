# 20260826_1540_AddSyncedYouTubeURLHeaderAndRebuildExe.md

## 目的
- メインヘッダーエリア（対象動画の直下）に「YouTube URL:」入力欄と「🌐 開く」ボタンを追加。
- 「Geminiプロンプト設定」タブ側のURL入力欄と `StringVar` を介してリアルタイム双方向連動させ、Step 1（切り抜き候補画面）から直接YouTube URLを入力・更新できるように改善。

## 実施内容
1. **`src/app.py` の修正**:
   - `__init__` に `self.youtube_url_var = tk.StringVar(value=self.config_data.get("last_youtube_url", ""))` を定義。
   - `setup_run_tab` のメインヘッダー（`tf`）に行1を追加：
     - `YouTube URL:` ラベル
     - `self.header_yt_entry`（`textvariable=self.youtube_url_var`）
     - `🌐 開く` ボタン（ブラウザでYouTube動画を直接開く）
   - `setup_prompt_tab` の `self.youtube_entry` にも `textvariable=self.youtube_url_var` を設定。
   - `build_full_prompt` で `self.youtube_url_var.get()` を参照するように統一。
2. **スタンドアロン exe の再ビルド**:
   - PyInstaller ビルドを実行し、`tools/きりぬきつーる/きりぬきつーる.exe` を更新。

## 検証結果
- ビルド成功（Exit Code 0）
- メイン画面（Step 1）のヘッダーから直接 YouTube URL を入力・連動できることを確認。

# 20260909_1430_ExportModeSeparateLayersTransparentMOV.md

## 目的
動画出力時において、従来の「焼き込み済み（MP4 1本）」だけでなく、Premiere ProやAfter Effects、DaVinci Resolve等の外部NLEでタイムライン編集が自由に行えるよう、**「元データ動画（MP4）」と「字幕・画像レイヤー（アルファチャンネル付き透過QuickTime MOV）」の素材分離書き出し**（2〜3ファイル構成）を選択可能にする。

## 実装方針
1. **動画レンダリングエンジン (`system_files/src/video.py`) の拡張**:
   - `process_single_clip` に `export_mode: str = "burn_in"` パラメータを追加。
   - **`export_mode == "burn_in"` (基本・デフォルト)**:
     - 従来通り、映像・音声・字幕・画像オーバーレイ・演出をすべて焼き込んだ完成版ショート動画（MP4）を1本出力。
   - **`export_mode == "separate_layer"` (素材分離: 2ファイル構成)**:
     - ① **元データ動画 (`[base]_[index]_[title]_base.mp4`)**: 字幕・画像なし。レイアウト調整（ブラー背景等）＋音響正規化（-14 LUFS）を適用したクリーンな背景映像。
     - ② **透過レイヤーMOV (`[base]_[index]_[title]_overlay.mov`)**: FFmpegの透過RGBA仮想キャンバス（`color=c=black@0.0:s=1080x1920:d={duration}:r=30`）上に、字幕および画像オーバーレイをタイムコード通りに合成し、`-c:v png -pix_fmt rgba`（アルファチャンネル付きQuickTime MOV）として出力。
   - **`export_mode == "full_separate"` (完全分離: 3ファイル構成)**:
     - ① 元データ動画 (`..._base.mp4`)
     - ② 透過字幕MOV (`..._subtitles.mov`)
     - ③ 透過画像MOV (`..._images.mov`)
   - 商業納品パッケージ自動生成（`package_delivery`）時にも、生成されたすべての元動画および透過MOVが納品フォルダへ自動同梱されるようループを拡張。
2. **UI・キュー管理 (`system_files/src/app.py`)**:
   - Step 3「書き出し設定」オプション領域の最上段（0行目）に「出力形式:」セレクターを新設。
     - `🎬 焼き込み済み (MP4 1本) 【基本】` （デフォルト）
     - `📦 素材分離 (元動画MP4 ＋ 透過レイヤーMOV)`
     - `🗂️ 完全分離 (元動画MP4 ＋ 透過字幕MOV ＋ 透過画像MOV)`
   - `create_queue_item_from_job` および `start_processing_queue` で `export_mode` をキュー管理・引き渡し。
   - `save_project` / `load_project` で `export_mode` の保存・復元に対応。
3. **PyInstaller によるスタンドアロンEXEの再ビルド＆配備**。

## 変更履歴 / 検証ログ
- `system_files/src/video.py`:
  - `export_mode` パラメータ追加、透過MOV生成（`-f lavfi -i color=c=black@0.0... -c:v png -pix_fmt rgba`）および元動画分離出力パイプラインを実装。
- `system_files/src/app.py`:
  - Step 3 に「出力形式」プルダウン追加、キュー引き渡し、保存・復元処理を統合。
- 構文検証（`py_compile`）: 正常通過（エラーなし）。
- PyInstallerビルド＆最新EXE配備。

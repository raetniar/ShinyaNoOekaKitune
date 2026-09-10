# 20260907_1256_SubtitleSyncAndMultilineWrap.md

## 目的
ユーザーからの指摘・要望に基づき、以下の3点を根本改修し、最新の実行バイナリ（`tools/きりぬきつーる/きりぬきつーる.exe`）へビルド・反映する。
1. **字幕表示タイミングの遅れ感・ボイス非同期の解消**:
   - プレビュー再生時のタイマー累積遅延（`self.after` の累積誤差）を解消し、`time.perf_counter()` に基づく実時間同期（A/V Sync）を導入。
   - Whisper自動認識の初期オフセットを `-0.35` 秒に早め、ボイス立ち上がりとジャストフィットするように調整。
   - 字幕タイムライン下部にワンタップ微調整ボタン（`[ ⏪ -0.5s ] [ ◀ -0.2s ] [ ▶ +0.2s ] [ ⏩ +0.5s ]`）を追加し、再生を聞きながら即座にシフト可能にした。
2. **字幕文字の横幅見切れ防止（自動折り返し＋手動改行の完全サポート）**:
   - プレビュー画面（Canvas/PIL）で、指定幅（`current_preview_w - 24`）を超える長文テキストを自然な位置で自動折り返し描画する `wrap_text_for_preview` を導入。
   - 手動で入力された改行コード `\n` を尊重し、複数行テキストを行ごとに綺麗に中央寄せ（または左・右寄せ）して上下マージンに合わせて配置。
   - 動画書き出し時（`src/video.py`）でも同様に長文折り返しを行う `wrap_subtitle_text` を追加し、SRT/動画上での文字見切れを完全防止。
3. **字幕編集入力欄の改行対応（「開業できるようにしておいて」）**:
   - 各字幕カード内のテキスト入力欄（`CTkTextbox`）の高さを `38px` から `54px`（2〜3行対応）に拡大し、スクロールバーも有効化。
   - Enterキーで自然に改行入力できるようにし、保存時も `rstrip('\r\n')` で中間の改行を安全に保持。

---

## 変更ファイル一覧
- `system_files/src/app.py`:
  - `wrap_text_for_preview` ヘルパー関数の追加
  - `show_current_frame` / `display_frame` の複数行・自動折り返し描画対応
  - `toggle_play` / `playback_loop` / `start_sub_segment_playback` の実時間 perf_counter 同期
  - 字幕カード入力欄の `height=54` 拡大＆スクロールバー有効化
  - タイムライン下部へのワンタップ微調整ボタン（`[ ⏪ -0.5s ] [ ◀ -0.2s ] [ ▶ +0.2s ] [ ⏩ +0.5s ]`）＆ `apply_quick_shift` 追加
  - `save_current_editor_to_active_job` での複数行改行（`\n`）の安全保持
  - Whisperデフォルトオフセットの `-0.35` 秒への最適化
- `system_files/src/video.py`:
  - `wrap_subtitle_text` 関数の追加（動画書き出し時の見切れ防止）
  - `import re` の追加
- `system_files/src/audio.py`:
  - `transcribe_audio_segment` のデフォルト `start_offset` を `-0.35` 秒に最適化
- `tools/きりぬきつーる/きりぬきつーる.exe`:
  - PyInstaller による最新版ワンファイルexeの再ビルド＆デプロイ完了

---

## 検証結果
- `py_compile` による全モジュール構文チェック通過（エラー0件）
- `wrap_text_for_preview` / `wrap_subtitle_text` の自動折り返し＆手動改行保持テスト完全パス
- GUIモックでの複数行字幕保存・プレビュー・クイックシフト処理完全パス
- 最新exe（338,972,186 bytes）の配備完了

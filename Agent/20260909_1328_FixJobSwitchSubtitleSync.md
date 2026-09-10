# 20260909_1328_FixJobSwitchSubtitleSync.md

## 1. 目的
- ユーザー様からのご指摘・ご要望：
  > **「1　を切り替えたときに、字幕が前の情報のママになる。字幕も切り替えに反映して」**
- 対象：
  - 『きりぬきつーる』（`tools/きりぬきつーる`）の「② 字幕・編集」画面における切り抜き候補選択メニュー（`job_select_menu`: `No.1 [...]` ➔ `No.2 [...]` など）および「◀ 前へ」「次へ ▶」ボタン。
- 課題：
  - 候補を No.1 から No.2 に切り替えた際、プレビュー上の字幕および字幕タイムライン（メイン画面およびポップアップウィンドウ「きりぬき編集ツール」）に、切り替え前の No.1 の字幕内容がそのまま残り、No.2 の固有字幕が反映されない（またはNo.1のデータで上書きされてしまう）不具合が発生していた。

---

## 2. 原因の徹底分析
1. **ウィジェット破棄時の `<FocusOut>` による誤上書き**:
   - `load_job_to_editor(idx)` により `self.active_job_index` が切り替え先（例: 1）に変更された後、`render_subtitle_editor_from_active_job()` が旧ウィジェットを `destroy()` する。
   - `CTkEntry` や `CTkTextbox` の破棄直前に Tkinter のウィンドウマネージャーによって `<FocusOut>` イベントが発火。
   - `<FocusOut>` ハンドラ内の `save_current_editor_to_active_job()` が、すでに切り替え先となった `self.active_job_index`（＝No.2）に対して、**破棄前の No.1 のウィジェット内容をそのまま代入して上書き保存**してしまっていた。
2. **切り替えガードフラグの欠如**:
   - レンダリング中（ウィジェット破棄・再生成中）やジョブ切り替え中であることを示すガードがなく、イベントループ上で不要な自動保存が割り込んでいた。
3. **実行順序の問題**:
   - `refresh_list_highlights()` 内で、字幕エディタ描画（`render_subtitle_editor_from_active_job`）よりも先に `show_current_frame()`（プレビュー描画）が呼ばれていた。
4. **ポップアップ側（透過パレット）の同期キー不一致**:
   - `refresh_palette_subtitle_list` でメイン側のウィジェット参照キーが一部 `text_entry` と誤認されており、安全な同期が行われていなかった。

---

## 3. 実装方針と解決策

### ① ジョブ切り替え・字幕レンダリング時のガードフラグ導入
- `self.is_rendering_subtitles`: 字幕ウィジェットの破棄・再生成中フラグ。
- `self.is_switching_job`: ジョブ切り替え処理中フラグ。
- `self.is_rendering_palette`: 透過パレット（ポップアップ）更新中フラグ。
- これらのフラグが立っている間は、`<FocusOut>`、`<KeyRelease>`、`save_current_editor_to_active_job` による自動保存を即座に安全遮断。

### ② ウィジェット破棄前のイベント解除 (`unbind`) とリスト先行クリア
- `render_subtitle_editor_from_active_job` 内で、ウィジェットを `destroy()` する前に、まず `<FocusOut>` および `<KeyRelease>` のバインドを明示的に解除。
- かつ `self.subtitle_widgets.clear()` を破棄ループ前に先行して実行することで、万が一イベントが発火しても空配列として扱われ誤保存が物理的に起きないよう二重防御。

### ③ `save_current_editor_to_active_job` の保存対象インデックス明示
- 引数 `target_idx=None` を追加。
- `load_job_to_editor(idx)` にて、`self.active_job_index` を変更する前に、切り替え元のインデックスに対して明示的に `self.save_current_editor_to_active_job(target_idx=self.active_job_index)` を実行。

### ④ レンダリング順序の最適化
- `refresh_list_highlights` において、`render_subtitle_editor_from_active_job()` を `show_current_frame()` より先に実行し、エディタとデータが確実に新ジョブになった状態でプレビューフレームを描画。

### ⑤ ポップアップウィンドウ（きりぬき編集ツール）の安全な同期
- パレット側のテキスト変更時、メイン側の `CTkTextbox`（キー `"text"`）を正確に参照して同期。

---

## 4. 検証ログ
1. **静的構文チェック**:
   - `python -m py_compile system_files/src/app.py` ➔ **ALL PASS (Syntax OK)**
2. **ジョブ切り替え字幕同期の自動テスト (`test_job_switch_subtitles.py`)**:
   - ジョブ0ロード時の字幕検証 ➔ **PASS**
   - ポップアップウィンドウ展開 ➔ **PASS**
   - ジョブ1切り替え時のデータ保持検証（上書きされていないこと） ➔ **PASS**
   - ジョブ1のエディタ・ポップアップ表示内容がジョブ1固有テキストであること ➔ **PASS**
   - 再度ジョブ0へ切り替えた際のジョブ0字幕正常復元検証 ➔ **PASS**
   - 全自動テスト項目: **ALL JOB SWITCH SUBTITLE TESTS PASSED PERFECTLY!**
3. **スタンドアロン EXE 再ビルド＆配備**:
   - `uv run --python 3.9 ... pyinstaller --clean -y きりぬきつーる.spec`（Exit Code 0）
   - 最新バイナリ（340,254,660 バイト）をルートの `tools/きりぬきつーる/きりぬきつーる.exe` へ配備完了。
   - 更新日時: **2026-09-09 13:28:21**

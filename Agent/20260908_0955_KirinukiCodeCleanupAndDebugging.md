# 20260908_0955_KirinukiCodeCleanupAndDebugging.md

## 1. 目的
- 『きりぬきつーる』（`tools/きりぬきつーる`）のコードベース全体の整理、静的解析、未定義変数・例外スコープ等の致命的バグのデバッグおよび安定化。
- モジュール間の一貫性検証、単体・統合テストの実行、およびスタンドアロン EXE の再ビルドと最新版配備。

---

## 2. 検出された問題点と実装方針

### ① `config.py` の `re` モジュール未定義クラッシュ（致命的バグ）
- **事象**: `ConfigManager.create_profile` 内で `re.sub(r'[\\/:*?"<>|]', '', profile_name)` を呼び出しているが、モジュール先頭で `import re` が欠落していた。
- **影響**: UI から新規案件プロファイルを作成しようとすると `NameError: name 're' is not defined` が発生し、アプリケーションが即座にクラッシュする。
- **対策**: `config.py` の先頭に `import re` を追加。

### ② `app.py` の `rgb_to_ass_hex` 関数未定義クラッシュ（致命的バグ）
- **事象**: `sync_jobs_to_queue` および `create_queue_item_from_job` 内で `rgb_to_ass_hex` を呼び出しているが、関数定義が削除・欠落していた。
- **影響**: 字幕スタイル適用やレンダリングキュー登録を実行した際に `NameError: name 'rgb_to_ass_hex' is not defined` で即時クラッシュする。
- **対策**: `utils.py` に `rgb_to_ass_hex(rgb: tuple) -> str`（RGBタプルからASSカラーコード `&HBBGGRR` への変換）を定義し、`app.py` でインポートして共有。

### ③ `app.py` の例外ブロック内ラムダ式クロージャによるスコープ消失バグ
- **事象**: `app.py` の 4022 行目（Whisper 再解析例外処理）にて `except Exception as err:` の直後に `self.after(0, lambda: messagebox.showerror("エラー", str(err)))` を呼び出していた。Python 3 では `except` スコープを抜けると例外変数 `err` が消去されるため、実行時に `NameError: name 'err' is not defined` が発生していた。
- **対策**: `err_msg = str(err)` を事前に安全に文字列化し、`lambda msg=err_msg: messagebox.showerror("エラー", msg)` としてデフォルト引数に束縛。

### ④ コード整理と型アノテーション（PEP 484 準拠）
- **`app.py`**:
  - 未使用インポート（`shutil`, `colorchooser`, `seconds_to_hms_ms`）の削除。
  - `load_job_to_editor` 内の未使用変数 `job = self.jobs[idx]` の削除。
- **`utils.py`**:
  - プレースホルダーの存在しない冗長な `f""` プレフィックスを通常文字列へ修正。
  - `fill_col = (*ImageColor.getrgb(color), 255)` へタプル展開を最適化。
- **`video.py` / `audio.py` / `config.py`**:
  - `from typing import Optional` を導入し、`job_info: Optional[dict] = None`、`replace_dict: Optional[dict] = None`、`device: Optional[str] = None`、`custom_ng_words: Optional[list] = None` など暗黙の Optional を PEP 484 準拠へ統一。
  - `all_vf = [sub_filter, *extra_vf_filters]` のリスト結合構文最適化。

---

## 3. 変更履歴 / 検証ログ

1. **静的解析・構文検査 (Ruff & py_compile)**:
   - `ruff check system_files/src --select=F,E9,RUF013` を実行。すべての致命的エラー、未定義シンボル、暗黙の Optional が完全に解消（All checks passed, 0 errors）。
   - `python -m py_compile` で `app.py`, `audio.py`, `config.py`, `main.py`, `setup_gui.py`, `utils.py`, `video.py` の全ソースコードが正常にコンパイルされることを確認。
2. **単体・統合機能テスト (`comprehensive_test.py`)**:
   - `utils.py`:
     - SRT時間フォーマット、標準HMS、分秒変換、秒数パースの双方向変換テスト（PASS）
     - `rgb_to_ass_hex`: 赤 `&H0000FF`、緑 `&H00FF00`、青 `&HFF0000` の色相変換テスト（PASS）
     - `calculate_overlay_placement`: アンカー基準座標計算テスト（PASS）
   - `config.py`:
     - NGワード検出テスト（PASS）
     - `create_profile` / `delete_profile` のファイル名正規化および作成・削除テスト（PASS、`re` 未定義バグの解消を確認）
   - `app.py`:
     - カラーコード変換（`parse_color_to_rgb`, `rgb_to_ass_hex`）の統合動作テスト（PASS）
3. **スタンドアロン EXE 再ビルド＆配備**:
   - `uv run --python 3.9` 環境にて PyInstaller で `きりぬきつーる.spec` を再ビルド（exit code 0）。
   - 生成された `system_files/dist/きりぬきつーる.exe`（338,974,682 bytes / 約323MB）をルートの `tools/きりぬきつーる/きりぬきつーる.exe` へ上書き配備完了。
   - 最終ビルド・更新日時: 2026-09-08 09:57:21

---

## 4. 残課題 / 備考
- 今後の機能拡張時も `utils.py` の共通関数を再利用し、`app.py` や `video.py` で重複ロジックを持たない方針を維持する。

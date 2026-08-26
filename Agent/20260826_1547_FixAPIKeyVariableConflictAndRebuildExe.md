# 20260826_1547_FixAPIKeyVariableConflictAndRebuildExe.md

## 目的
- APIキーを入力したにもかかわらず「Gemini APIキーが必要です」と表示されてしまう不具合の修正。

## 原因
- `setup_global_ui_tab` で定義した `self.gemini_api_key_entry` が、その後に実行された `setup_dict_tab` の重複した空の `self.gemini_api_key_entry` によって上書きされていたため。

## 修正内容
1. **変数の一元管理 (`gemini_api_key_var`)**:
   - `__init__` に `self.gemini_api_key_var = tk.StringVar(value=self.config_data.get("gemini_api_key", ""))` を定義。
   - `setup_global_ui_tab` の入力欄に `textvariable=self.gemini_api_key_var` を設定。
2. **重複箇所の完全撤去**:
   - `setup_dict_tab` 側の重複したAPI設定フレームを削除。
3. **実行時の確実な自動同期**:
   - `start_gemini_api_analysis` 実行時に `self.gemini_api_key_var.get()` から直接キーを取得し、`config_data` に即座に保存・適用。
4. **PyInstaller スタンドアロン exe の再ビルド**:
   - `tools/きりぬきつーる/きりぬきつーる.exe` を更新。

## 検証結果
- ビルド成功（Exit Code 0）
- APIキーが確実にプログラム全体で保持・保存され、エラーダイアログが出ずに自動解析が開始されることを確認。

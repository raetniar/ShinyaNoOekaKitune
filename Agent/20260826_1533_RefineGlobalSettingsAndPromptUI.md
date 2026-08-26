# 20260826_1533_RefineGlobalSettingsAndPromptUI.md

## 目的
- ユーザーのフィードバックに基づき、UIの配置を最適化：
  1. 「全体設定」タブを開いた直後のメイン画面に「🔑 Google Gemini API Key 設定」欄を大きく追加。
  2. 「Geminiプロンプト設定」タブ右下の不要な重複ボタン（「Gemini APIで自動解析実行」）を削除し、コピーボタンのみに整理。
  3. スタンドアロン実行ファイル（`きりぬきつーる.exe`）の再ビルド・配置。

## 実施内容
1. **`src/app.py` の修正**:
   - `setup_global_ui_tab`:
     - 「🔑 Google Gemini API Key 設定」フレームを新設（入力欄・表示切替チェック・AI Studioリンクボタン）。
     - `save_global_ui_settings` にて APIキーを `config.json` へ安全に保存。
   - `setup_prompt_tab`:
     - 右下の重複ボタンを削除し、「📋 プロンプトをコピー」ボタンを配置。
2. **スタンドアロン exe の再ビルド**:
   - PyInstaller によるビルドを実行し、`tools/きりぬきつーる/きりぬきつーる.exe` を更新。

## 検証結果
- ビルド成功（Exit Code 0）
- 「全体設定」を開いて即座にAPIキーの入力・保存ができることを確認。
- 「Geminiプロンプト設定」画面のボタン配置がスッキリ整理されたことを確認。

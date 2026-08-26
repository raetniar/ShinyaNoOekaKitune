# 20260826_1456_ImplementReviewedEnhancementsToCodebase.md

## 目的
- ユーザーからのレビューに基づき、『きりぬきつーる』のソースコードに全5項目の改善を実際に実装・適用。

## 実装内容
1. **JSON構造化パース ＋ マークダウン正規表現フォールバック (`src/app.py`)**:
   - `parse_instructions_text`:
     - 第1層: ````json ... ```` の構造化JSON（または生JSON）を最優先パース（キーの揺れ `clips`/`candidates`/`start_time` にも完全対応）。
     - 第2層: JSONパースに失敗した場合、従来のマークダウン正規表現による柔軟な抽出へ自動フォールバック。
2. **Gemini API 直接呼出（ワンクリック自動解析） (`src/app.py`, `src/config.py`)**:
   - `config.json` に `gemini_api_key` を追加。
   - 「全体設定」タブに「⑤ 🔑 Google Gemini API Key」入力欄（マスク表示切替付き）を追加。
   - 「Geminiプロンプト設定」タブに「✨ Gemini APIで自動解析実行」ボタンを追加し、標準 `urllib` による軽量な REST API（`gemini-1.5-flash`）呼出を実装。応答テキストを自動反映して即座にタブ1へ移動。
3. **Whisper ハードウェアアクセラレーション（CUDA/GPU自動検出 ＆ CPUフォールバック） (`src/audio.py`, `src/app.py`)**:
   - `get_optimal_device()` を新設し、`torch.cuda.is_available()` で CUDA GPUと CPU を自動判別。
   - GPU時は `fp16=True`、CPU時は `fp16=False` で最適化。
   - ロードログおよび進捗表示に動作モードを明示。
4. **自己学習データ肥大化防止のローリング上限 (`src/config.py`)**:
   - `learn_subtitle_diff`:
     - `vocabulary`: 最大500語（頻度上位500件にトリミング）。
     - `corrections`: 最大300件にトリミング。
     - `timing_offsets`: 直近100件のローリングバッファ。
5. **セキュリティ & Git管理の整合性**:
   - `tools/きりぬきつーる/.gitignore` に `system_files/config.json` を追加し、リポジトリ用には `config.example.json` を配置。
   - `src/config.py` の `load_config` で `config.json` がない場合は `config.example.json` から安全に初期生成。

## 検証結果
- 単体テストにて以下を検証完了：
  - CUDA/CPUデバイス検出および動作モード文字列の生成
  - 大量データ追加時の語彙（500件上限）・誤字修正（300件上限）トリミングの正常動作
  - 全Pythonファイルのコンパイルチェック（`py_compile`）成功

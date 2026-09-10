# 20260908_1450_SplashZOrderFixAllowLowering.md

## 1. 目的
- ユーザー様からのご指摘・ご要望：
  > **「ずべてのツール（エクスプローラーなど）より上に固定表示されるので、他のものを上に持ってこれるように変更したい」**
- **課題分析**:
  - `きりぬきつーる.spec` で `always_on_top=False` を指定していても、PyInstaller内部のTclテンプレート（`splash_templates.py`）により、Windowsでは `wm overrideredirect . 1`（無枠ポップアップ）および `raise .`（強制最前面引き上げ）が実行される。
  - Windows のウィンドウマネージャー（DWM）の仕様上、タスクバーに項目がない無枠ポップアップは他アプリ（エクスプローラーやブラウザ）をクリックしても背面に回らず、常に最上位レイヤーに居座ってしまう。
- **解決方針**:
  1. **強制最前面（`raise .`）の完全撤廃**:
     - `きりぬきつーる.spec` 内で Splash クラスをカスタマイズし、ブートスクリプトから `raise .` を完全除去。
  2. **フォーカス移動時・クリック時の自動背面退避（`lower .`）**:
     - Tcl スクリプトへ `bind all <FocusOut> {lower .}` および `bind all <Button-1> {lower .}` を注入。
     - エクスプローラーなど他のアプリをクリックした瞬間、またはスプラッシュをクリックした瞬間に、スプラッシュが他のウィンドウの背面にスッと回るよう制御。
  3. **Python起動時の補強 (`src/main.py`)**:
     - Python起動直後にスプラッシュウィンドウが存在する場合、Windows API（`SetWindowPos` の `HWND_NOTOPMOST`）でOSレベルの最前面フラグを解除。

---

## 2. 変更内容
1. `tools/きりぬきつーる/system_files/きりぬきつーる.spec`:
   - `NonTopmostSplash` クラスを定義し、生成されるTclスクリプトから `raise .` を除外し、`<FocusOut>` と `<Button-1>` で `lower .` されるよう拡張。
2. `tools/きりぬきつーる/system_files/src/main.py`:
   - Python初期化直後にスプラッシュウィンドウの最前面属性を解除するセーフガード処理を実装。
3. EXEの再ビルド＆配備:
   - `tools/きりぬきつーる/きりぬきつーる.exe` へ最新バイナリを反映。

---

## 3. 検証ログ
1. **構文・動作チェック**:
   - `src/main.py` ➔ **PASS**
   - `きりぬきつーる.spec` ➔ **PASS**
2. **EXE 再ビルド＆配備**:
   - `uv run --python 3.9 --with customtkinter --with opencv-python --with "moviepy<2.0.0" --with openai-whisper --with pillow --with pyinstaller pyinstaller --clean -y きりぬきつーる.spec`（Exit Code 0）
   - Tcl スクリプト検証（`NonTopmostSplash-00_script.tcl`）:
     - `raise .` ➔ **完全除去確認**
     - `bind all <FocusOut> {lower .}` ➔ **注入確認**
     - `bind all <Button-1> {lower .}` ➔ **注入確認**
     - `bind all <Double-Button-1> {exit}` ➔ **注入確認**
   - 最新バイナリ（338,993,703 バイト）をルートの `tools/きりぬきつーる/きりぬきつーる.exe` へ配備完了。
   - 更新日時: **2026-09-08 14:51:56**

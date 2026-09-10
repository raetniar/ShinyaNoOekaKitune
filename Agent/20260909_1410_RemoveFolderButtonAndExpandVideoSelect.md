# 20260909_1410_RemoveFolderButtonAndExpandVideoSelect.md

## 目的
メイン画面ヘッダー2行目において、「動画 参照...」ボタンの右隣にあった「📂 フォルダ」ボタンが左側のデータ管理・参照機能と重複して見えていたため撤去し、「動画 参照...」ボタンを単独で幅180px（上段の「作業保存」「作業読込」ボタングループの合計幅と完全に一致）に統一拡大して、ヘッダー右側ブロックの縦横ラインと整列感を極限まで向上させる。

## 実装方針
1. `tools/きりぬきつーる/system_files/src/utils.py`:
   - `get_modern_icon` に `"video"` （ビデオカメラアイコン）のベクターライク描画ロジックを追加。
2. `tools/きりぬきつーる/system_files/src/app.py`:
   - `self.scan_folder_btn` の画面パック（表示）を撤去（互換用ダミー保持）。
   - `self.video_select_btn` の幅を `width=180` に拡大し、`image=get_modern_icon("video", (14, 14))` を付与してモダン化。
   - 1行目右（作業保存88px + 作業読込88px + gap4px = 180px）、2行目右（動画参照180px）、3行目右（グレースケールスイッチ180px枠）の3段すべてで横幅180pxの縦ラインが一直線に揃うレイアウトを実現。
3. PyInstaller によるスタンドアロンEXEの再ビルド＆配備。

## 変更履歴 / ログ
- `system_files/src/utils.py`: `video` アイコン描画追加。
- `system_files/src/app.py`: `scan_folder_btn` 撤去、`video_select_btn` 幅180px＆アイコン化。
- 構文検証（`py_compile`）: 正常通過（エラーなし）。
- PyInstallerビルド＆ルート配置完了。

## 残課題 / 備考
- なし（ヘッダー全体のミニマル・統合UIが完成）。

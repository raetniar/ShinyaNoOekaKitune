# 20260824_1623_UpdateLockIconToSvg.md

## 目的
`Title_manager_localize_Ver5.html` のヘッダーにある並べ替え機能の鍵アイコン（絵文字 🔒/🔓）を、`TwitchManager` と同じ高精細なベクター SVG アイコンへ変更する。

## 対象ファイル
- `tools/Title_manager_配布用/Title_manager_localize_Ver5.html`

## 変更内容
1. HTMLの `#lock-btn` 内のアイコンを TwitchManager と同仕様のロック SVG に変更。
2. JSの `toggleSortLock()` 内で、ロック状態（閉じた錠前 SVG）とアンロック状態（開いた錠前 SVG）が動的に切り替わるよう更新。
3. アンロック時にボタンが緑色（`#00b06f`）にハイライトされる `.btn-head-purple.unlocked` CSS クラスを適用。

## 検証結果
- JS構文チェック（vm.Script）: エラーなし（PASS）
- ロック・アンロック切り替え時の SVG 描画およびハイライトスタイルの適用を確認。

# 20260824_1622_FixDateFormatDefaultSelection.md

## 目的
`Title_manager_localize_Ver5.html` の設定モーダルで「日付の表示形式 ({date}用)」のセレクトボックスが初期表示時に空白になっていた不具合を修正し、デフォルトで `MM/DD (例: 05/12)` が選択表示されるようにする。

## 対象ファイル
- `tools/Title_manager_配布用/Title_manager_localize_Ver5.html`

## 変更内容
1. HTMLの `<option value="MM/DD">` に `selected` 属性を付与。
2. `settings.dateFormat` が未設定の場合のフォールバック初期値として `'MM/DD'` を設定。
3. `initLanguage()` 内で言語切り替え時に option テキストを置換する際、選択中の値がリセットされないよう再バインド処理を追加。
4. 設定モーダルを開いた際（`openModal('settingModal')`）に `settings.dateFormat` をセレクトボックスの値へ同期反映。

## 検証結果
- JS構文チェック（vm.Script）: エラーなし（PASS）
- デフォルト選択および言語切り替え時の選択値保持を確認。

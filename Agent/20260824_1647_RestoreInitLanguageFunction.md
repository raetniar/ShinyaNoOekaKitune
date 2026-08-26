# 20260824_1647_RestoreInitLanguageFunction.md

## 目的
`Title_manager_localize_Ver5.html` の起動時（`window.onload`）に発生していた `Uncaught ReferenceError: initLanguage is not defined` エラーを解消する。

## 原因
- `langMap` の一括リプレイス時に、直前にあった `initLanguage()` 関数およびグローバル変数の宣言部分が上書きされて消失していた。

## 変更内容
1. `initLanguage()` 関数および変数宣言（`currentLang`, `config`, `friendsConfig`, `memoConfig`, `settings`, `isSortLocked`）を復元。
2. ユーザーが選択した言語（JP / EN / ZH）が `localStorage`（`settings.language`）に自動保存され、リロード後も前回の言語設定が維持されるよう処理を強化。

## 検証結果
- JS構文チェック（vm.Script）: エラーなし（PASS）
- 起動時の `initLanguage()` 呼び出しが正常に実行され、ReferenceError が完全に解消されたことを確認。

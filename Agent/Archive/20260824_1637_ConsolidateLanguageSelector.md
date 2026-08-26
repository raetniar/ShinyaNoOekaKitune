# 20260824_1637_ConsolidateLanguageSelector.md

## 目的
`Title_manager_localize_Ver5.html` のヘッダーにある3つの言語切り替えボタン（JP / EN / ZH）を1つのコンパクトなプルダウン（セレクトボックス）に統合する。

## 対象ファイル
- `tools/Title_manager_配布用/Title_manager_localize_Ver5.html`

## 変更内容
1. ヘッダーの `<button>JP</button><button>EN</button><button>ZH</button>` を、1つの `<select id="lang-select">` プルダウンに変更。
2. `setLanguage()` 実行時にセレクトボックスの選択状態が確実に同期するよう処理を追加。
3. ヘッダーの幅を大幅にスリム化し、他のボタン（並べ替え・手引・設定）とのスペース効率と視認性を向上。

## 検証結果
- JS構文チェック（vm.Script）: エラーなし（PASS）
- プルダウンでの切り替えおよび自動同期が正常に動作することを確認。

# 20260826_1305_AlignDiscordTitleAndPityResetRow.md

## 目的
- セクション1下部のレイアウトを整理し、「Discord発信景品タイトル」の入力欄を左側に、「全員の天井リセット」ボタンをその右側に横並びで美しく配置。

## 実装内容
1. **HTML構造の最適化 (`tools/裏ガチャシステム/index.html`)**:
   - 上段・下段に分かれていた2行を1つのスリムバー（`flex: row; justify-content: space-between; align-items: center;`）に統合。
   - 左側：`Discord景品タイトル:` ラベル ＋ タイトル即時入力欄（`#discordEventTitleQuick`）
   - 右側：`全員の天井リセット` ボタン（`#resetAllPityBtn`）

## 検証結果
- ブラウザ実機にて、1行で左に入力欄、右にリセットボタンが綺麗に収まり、デザインの一体感と操作性が大幅に向上したことを確認完了。

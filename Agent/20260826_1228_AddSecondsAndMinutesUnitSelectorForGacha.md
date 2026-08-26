# 20260826_1228_AddSecondsAndMinutesUnitSelectorForGacha.md

## 目的
- 基本必要視聴時間を「1秒」などテスト時や即時解放時にも直感的に設定できるよう、小数点（0.01等）のわかりにくさを廃止し、「数値 ＋ 単位（分/秒）選択ドロップダウン」によるUIとロジックの秒単位完全対応を実装。

## 実装内容
1. **HTML/UI拡張 (`tools/裏ガチャシステム/index.html`)**:
   - 「基本必要視聴時間」の入力欄を `[ 数値入力 (cfgRequiredTimeValue) ] [ 単位セレクト (cfgRequiredTimeUnit: 分 / 秒) ]` の2分割UIに刷新。

2. **JavaScriptロジック**:
   - `config.requiredTimeValue`（数値）および `config.requiredTimeUnit`（'min' | 'sec'）を追加。
   - `getRequiredSecondsForUser(l)` / `getElapsedSecondsForUser(l)`: 内部計算を秒単位に統一し、ミリ秒・秒単位で正確に経過と判定を算出。
   - `formatDurationString(sec)`: 60秒未満なら「30秒」「1秒」、60秒以上なら「1分」「1分30秒」「60分」と自動で可読性の高い文字列に変換。
   - `render()` / `triggerGachaForListener`: プログレスバー・残り時間・返信メッセージテンプレート（`{remain_minutes}`, `{remain_time}`）で秒数・分数を正しく反映。
   - 秒単位または5分以下の設定時は、カードの自動更新インターバル（`tickerInterval`）を1秒間隔に高速化し、秒カウントダウンが滑らかにアニメーション。

## 検証結果
- ブラウザ実機にて「秒」を選択して `1`（1秒）に設定した際、リスナーのカードが即座に「解放中」になりガチャ実行が可能になること、および「分」に戻した際に正確に「あと〇分〇秒」と再計算されることを確認完了。

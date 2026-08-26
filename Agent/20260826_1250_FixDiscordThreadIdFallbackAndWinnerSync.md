# 20260826_1250_FixDiscordThreadIdFallbackAndWinnerSync.md

## 目的
- 天井確定当たり（または通常当たり）が出た際に、Discord Webhookへ当選者ログが反映されなかった原因を調査・修正し、確実にDiscordメッセージが追記編集されるよう改善。

## 原因分析
- 「投稿先スレッドID」欄に親チャンネルのチャンネルID（数値）が誤入力されていたため、Discord APIが `?thread_id=...` に対して `400 Unknown Channel` エラーを返して送信が弾かれていた。

## 実装内容
1. **JavaScript改修 (`tools/裏ガチャシステム/index.html`)**:
   - `syncDiscordWinnerLog`:
     - 親チャンネルIDがスレッドID欄に入力されていた場合の自動クリーン処理を追加。
     - スレッドID付きリクエストで万が一 400 エラーが発生した場合、自動的に通常チャンネル宛（スレッドIDなし）へフォールバックして即時再送する自動リカバリー処理を実装。
     - `config.discordThreadId` のデフォルト値を空欄に整頓。

## 検証結果
- ブラウザ実機およびNode.jsテストにて、Discord Webhookへのメッセージ更新（PATCH: 200 OK）が正常に完了し、当選者リストが即座に追記更新されることを確認完了。

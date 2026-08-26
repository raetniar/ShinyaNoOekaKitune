# 20260826_1512_ImplementScoreBreakdownAndContextCheck.md

## 目的
- ユーザーからのフィードバックに基づき、Gemini用プロンプトおよびパーサーに以下の3大改善を反映：
  1. **5軸個別採点（`score_breakdown`）**: `hook_stop_rate`, `standalone_context`, `emotional_peak`, `follow_through_power`, `loop_timing_quality`
  2. **サムネイル最適フレーム（`thumbnail_frame`）**: 再生前の静止画として最も引きの強い瞬間を出力
  3. **文脈自立性のチェックリスト化 & 自己監査（`context_check`）**: 代名詞・過去ネタ・伏線分離の除外条件を具体化
  4. **IN側の無音判定（0.3秒以上の間・呼吸）と感情タイプの多様性指示**

## 変更ファイル
- `system_files/src/config.py`: `DEFAULT_PROMPT_TEMPLATE` に改善版プロンプトを適用。
- `system_files/config.example.json`: テンプレート設定を同期更新。
- `system_files/src/app.py`:
  - `parse_instructions_text`: `score_total` / `score`, `score_breakdown`, `thumbnail_frame`, `context_check`, `follow_hook`, `loop_reason` の抽出・保存を実装。
  - `render_job_list`: 切り抜き候補ボタンに `[{score}点]` バッジを表示。
  - Windows環境（CP932）でのエンコードエラー防止の安全ガードを追加。
- `きりぬきつーる_仕様書.md`: 第9章に `score_breakdown`, `thumbnail_frame`, `context_check` の仕様を追記。

## 検証結果
- 単体テストにて以下を検証完了：
  - JSON構造化データからの `score_breakdown`, `thumbnail_frame`, `context_check` の正常抽出
  - 候補一覧UIへのスコアバッジ表示
  - 全Pythonファイルのコンパイルチェック正常通過

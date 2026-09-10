# 作業記録: ③への画面切り替え時におけるレンダリングキュー自動同期＆秒数精度向上

## 目的
ユーザーからの要望に基づき：
1. 「字幕編集タイムライン (秒数・テキストは手動変更可能)」の見出しラベルのオミット（縦余白の有効活用）。
2. 「キュー追加ボタンを押さなくても、編集した内容が自動的に③（レンダリング・書き出し実行）の画面切り替え時にキューへ反映・レンダリング準備完了になる」機能の実装。

## 変更内容
1. **`system_files/src/app.py`**:
   - `self.sub_scroll = ctk.CTkScrollableFrame(rf)`：見出しラベルをオミット。
   - `create_queue_item_from_job(self, job, job_index)`：Jobからキュー登録用辞書を安全に生成する共通ヘルパーを新設。
   - `sync_jobs_to_queue(self)`：③のタブ遷移時（`switch_wizard_step("step3")`）に自動実行。キューが空なら候補を自動投入し、既にキューがあれば編集中のアクティブ候補の内容を上書き同期。
   - `add_active_job_to_queue(self)`：手動でボタンを押した場合も重複追加せず上書き更新するようリファクタリング。
2. **`system_files/src/utils.py`**:
   - `seconds_to_minsec`：小数の微調整秒数（例: 00:01.5, 00:01.2）を切り捨てず高精度にフォーマット・保持できるよう拡張。

## 検証結果
- `py_compile`: Exit code 0
- 自動テスト（`scratch/test_auto_queue.py`）:
  - 手動キュー追加なしでStep 3切り替え時の自動キュー登録: ✅ Pass
  - Step 2で再編集・シフト後のStep 3切り替え時の自動上書き同期（重複なし）: ✅ Pass
- 自動テスト（`scratch/test_sub_ui.py`）:
  - タイムラインラベルオミット後の全機能動作: ✅ Pass
  - `ALL TESTS PASSED SUCCESSFULLY!`

# 20260826_1445_UpdateKirinukiToolSpecV2BasedOnReview.md

## 目的
- ユーザーからの専門的レビュー（バズポイント検出の自動化方針、JSONパース堅牢化、WhisperのGPU/CPU実行仕様、config.jsonのGitセキュリティ除外、learned_dataの肥大化防止リミット）を反映し、仕様書およびGit管理設定をアップデート。

## 実装・反映内容
1. **セキュリティ & Git管理強化**:
   - `tools/きりぬきつーる/.gitignore`: `system_files/config.json` を除外対象に追加。
   - `tools/きりぬきつーる/system_files/config.example.json`: 公開リポジトリ用テンプレートを新設。
2. **仕様書の改訂 (`きりぬきつーる_仕様書.md` v2.0)**:
   - ① **バズポイント検出のハイブリッド方針**: 無料コピペ（長尺Web版Gemini活用）とAPI直接呼出（ワンクリック自動化）の両立設計。
   - ② **2段構えパース**: JSON構造化出力優先 ➔ マークダウン正規表現フォールバック ➔ 手動追加UI。
   - ③ **Whisper実行環境 & ピンポイント切り出し設計**: `torch.cuda.is_available()` によるGPU/CPU自動判定。候補区間（15〜58秒）のみをWAV切り出しして文字起こしするため、CPUでも数秒で完了する高効率アーキテクチャを明記。
   - ④ **データ肥大化防止**: `corrections`（最大300件）、`vocabulary`（最大500件）、`timing_offsets`（直近100件ローリングバッファ）の上限リミット仕様を明記。

## 確認結果
- 仕様書v2.0の更新、および `.gitignore` / `config.example.json` の配置を完了。

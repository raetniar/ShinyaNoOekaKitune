# 20260908_1630_GeminiInfiniteTitleGeneratorIntegration.md

## 目的
ユーザーからの要望「これgeminiAPIとつなげてより分析を強化したタイトル生成をほぼ無限のパターンで作れるようにして」に基づき、GASバックエンドおよび各タイトル生成UI（サイドバー、ダッシュボード内蔵、単体Webツール）をGemini APIと完全接続する。
過去配信アナリティクスから抽出した「勝ちパターン単語」や「被レイドなし（純オーガニック）高同接タイトル」をプロンプトに自動注入し、入力された状態（カテゴリ・気分・食事・予定）を掛け合わせて、毎回異なる切り口の洗練された大喜利タイトルを無限パターンで即座にAI生成できるようにする。

## 対象ファイル
1. [`scripts/TwitchDashboard_Setup.js`](file:///g:/マイドライブ/【02_UikoUka_活動】/パートナー計画/scripts/TwitchDashboard_Setup.js)
2. [`scripts/TitleGeneratorView.html`](file:///g:/マイドライブ/【02_UikoUka_活動】/パートナー計画/scripts/TitleGeneratorView.html)
3. [`scripts/DashboardView.html`](file:///g:/マイドライブ/【02_UikoUka_活動】/パートナー計画/scripts/DashboardView.html)
4. [`tools/TwitchTitleGenerator/index.html`](file:///g:/マイドライブ/【04_素材・ツールライブラリ】/GIT_HTML/tools/TwitchTitleGenerator/index.html)
5. [`learn.md`](file:///g:/マイドライブ/【02_UikoUka_活動】/パートナー計画/learn.md)

## 実施した変更
1. **GAS `generateTitlesWithGemini(cat, mood, food, plan, count)` の実装**:
   - `getAdvancedDashboardData()` からリアルタイムに「純オーガニック上位タイトル」「高平均同接の勝ち単語リスト」を取得。
   - 初狐羽鹿の配信ペルソナ（お絵描きアトリエ、ポンコツ感、AI相棒ようかのお説教漫才、平日最長2.5h厳守、スマホ先頭30文字最適化）を体系化したシステムプロンプトを構築。
   - `responseMimeType: "application/json"` を用いて、バッジ名・タイトル本文・解説tips・先頭30文字を含むJSON配列を安全に取得。
   - `gemini-2.5-flash` ➔ `gemini-flash-latest` ➔ `gemini-2.0-flash` の自動多段階フォールバック。
2. **`TitleGeneratorView.html` へのGemini AIボタン・ローディング・連携処理の追加**:
   - 「✨ Gemini AIで無限大喜利生成（分析強化版）」ボタンをメインに配置。
   - 通信中の洗練されたローディング表示と、ワンクリックでのQ列反映・コピー機能。
3. **`DashboardView.html` へのGemini AIボタン追加と共通カード描画**:
   - セクション2の大喜利ジェネレーターに「✨ Gemini AIで無限大喜利生成」ボタンを追加。
4. **`tools/TwitchTitleGenerator/index.html` のハイブリッドAI化**:
   - クライアントサイドでの直接API呼び出しと多重フォールバックに対応。

## 検証結果
- `node -c scripts/TwitchDashboard_Setup.js`: Exit Code 0（構文エラーなし）
- 全ファイルでの整合性とフォールバック動作を確認。

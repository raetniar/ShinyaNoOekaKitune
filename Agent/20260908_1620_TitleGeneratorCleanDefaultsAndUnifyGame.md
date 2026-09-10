# 20260908_1620_TitleGeneratorCleanDefaultsAndUnifyGame.md

## 目的
1. **初期値の空白化**: タイトル生成UIの入力欄（気分・食べたもの・予定）にあらかじめ入っていた固定デフォルト値（"ねむい", "白湯", "こまさんツーショ制作 1時まで"）を全撤廃し、未入力状態（プレースホルダーのみ）で起動できるようにする。
2. **ゲームカテゴリの一本化**: 「逆転裁判」「ホラゲ」「登りゲー」の3分類を撤廃し、「🎮 ゲーム実況・参加型」という単一の大カテゴリに統一する。
3. **空入力時の自然なフォールバック**: 入力欄が空の場合でも構文エラーや不自然な文字列結合を起こさず、自然な仮タイトルを生成・プレビューできるようにする。

## 対象ファイル
1. [`scripts/TitleGeneratorView.html`](file:///g:/マイドライブ/【02_UikoUka_活動】/パートナー計画/scripts/TitleGeneratorView.html)
2. [`scripts/DashboardView.html`](file:///g:/マイドライブ/【02_UikoUka_活動】/パートナー計画/scripts/DashboardView.html)
3. [`tools/TwitchTitleGenerator/index.html`](file:///g:/マイドライブ/【04_素材・ツールライブラリ】/GIT_HTML/tools/TwitchTitleGenerator/index.html)
4. [`learn.md`](file:///g:/マイドライブ/【02_UikoUka_活動】/パートナー計画/learn.md)

## 実施した変更
1. **入力欄の `value=""` 化**:
   - `inputMood`, `inputFood`, `inputPlan` からハードコードされた固定テキストを削除。
   - プレースホルダー（例示テキスト）と下部のクイックタグチップ（ワンクリック入力）は保持し、入力体験を最適化。
2. **カテゴリボタンの3大統合**:
   - `🎨 お絵描き・アトリエ` (art)
   - `🎮 ゲーム実況・参加型` (game)
   - `☕ 深夜雑談・作業BGM` (chat)
3. **大喜利タイトル生成ロジックの統合**:
   - `game` カテゴリにおいて、従来の「ポンコツ迷推理」「教えて指示厨」「AIようかお説教」「IQ3叫び」「1ミス/絶叫即終了」「初見歓迎まったり」の6大キラー構文をバランスよく網羅。
   - 未入力時のフォールバック変数（`rawMood`, `rawFood`, `rawPlan`）を導入し、空文字の場合は自然な繋ぎ（「うとうと」「白湯」「ゲーム実況」）を適用。

## 検証結果
- `node -c scripts/TwitchDashboard_Setup.js`: Exit Code 0（構文エラーなし）
- 全3ファイルでカテゴリ・入力欄・生成テンプレートの完全同期を確認。

# 20260826_1435_ImplementWhisperLocalAdaptiveLearning.md

## 目的
- ユーザーがショート字幕編集画面でテキストや時間を修正した際、その修正差分から自動的にローカルで自己学習し、次回以降のWhisper音声認識の精度を自律的に向上させる「適応型ローカル自己学習エンジン」の実装。
- 外部通信ゼロ・完全オフラインで動作し、プライバシーを100%保護。

## 実装内容
1. **学習データ管理 (`src/config.py`)**:
   - `ConfigManager` にローカル学習データ管理（`%APPDATA%/KirinukiTool/learned_data.json`）を追加。
   - `learn_subtitle_diff(raw_subs, edited_subs)`:
     - `difflib.SequenceMatcher` による誤認識単語 ➔ 正解単語の自動差分抽出（`corrections`）。
     - 編集後テキストからの頻出単語・固有名詞の抽出と頻度カウント（`vocabulary`）。
     - タイミング微調整の統計オフセット学習（`timing_offsets`）。
   - `get_effective_registered_words()`: 手動登録単語 ＋ 学習された高頻度単語を Whisper `initial_prompt` 用にマージ。
   - `get_effective_replace_dict()`: 手動置換辞書 ＋ 学習された修正パターンを自動マージ。
   - `reset_learned_data()`: 学習データのリセット機能。

2. **音声認識エンジンとの連携 (`src/audio.py`)**:
   - `transcribe_audio_segment`: 各セグメントに `raw_text`（Whisper生出力テキスト）と生タイムスタンプを保持させ、学習時の差分検出精度を最大化。

3. **GUI・トリガー連携 (`src/app.py`)**:
   - 一括/単体Whisper音声認識時に `get_effective_registered_words()` / `get_effective_replace_dict()` を自動適用。
   - 字幕編集・キュー追加時に `learn_subtitle_diff()` を自動トリガー。
   - 全体設定タブ（`setup_dict_tab`）に「④ 🧠 AI自己学習データ管理」セクションを追加（学習語数・修正パターン数表示、リセットボタン）。
   - モジュールインポートの安全ガード（`try: from src.utils ... except ImportError: from utils ...`）を適用。

## 検証結果
- 単体テスト（差分学習テスト）にて、修正された単語（例: `ういこ` ➔ `初狐羽鹿`、`サマ` ➔ `裁判`）が自動で抽出され、次回プロンプトと置換辞書へ反映されることを確認完了。
- 全Pythonファイルのコンパイルチェック（`py_compile`）に成功。

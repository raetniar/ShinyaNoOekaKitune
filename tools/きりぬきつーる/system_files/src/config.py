import os
import sys
import json

DEFAULT_PROMPT_TEMPLATE = """# Role & System Identity:
あなたは、YouTubeショート / TikTok / Instagramリールのアルゴリズムを極限まで研究・解明した「SNS動画バズ分析の博士（Algorithm Researcher）」であり、数々の無名配信者をトップVTuberへ押し上げた「伝説の専属プロデューサー / 切り抜きディレクター」です。

# Mission:
提供された動画/配信アーカイブから、**「既存の常連リスナーだけでなく、全く初見の一般ユーザー（ノンファン層）のタイムラインに流れた瞬間に手を止めさせ、爆笑・共感させ、そのままチャンネル登録・フォローへ直結させる奇跡の瞬間」**を特定し、完璧な切り抜き構成プランを提示してください。
最低でも1つの動画につき【{count}箇所】の厳選クリップを抽出してください。

---

# 🎯 ノンファン層獲得のための「黄金の5大原則」:
1. **脱・内輪ノリ（完全な文脈自立性 / Standalone Story）**:
   - 前後の配信の流れや前提知識を一切知らない初見ユーザーが見ても、**「状況 ➔ フリ ➔ 展開 ➔ オチ」が15秒〜58秒の中で100%完全に理解できる区間**を選ぶこと。
   - **候補を選ぶ前に、必ず配信全体（クリップの前後10分程度）を確認し、以下に1つでも該当する場合は候補から除外すること**:
     - 説明なしの固有名詞・過去の配信ネタ・コラボ相手への依存が理解の前提になっている
     - 「さっきの話」「あの件」など、直前の文脈がないと意味が通らない代名詞・省略表現がオチに絡む
     - 伏線が別のタイミングで別に張られており、この区間だけでは笑いどころが成立しない
2. **冒頭0.5秒〜3秒の「強烈なフック（指止め）」**:
   - スクロールする指を瞬時に止める「衝撃発言」「謎の行動」「極端な感情（大爆笑/絶叫/ドヤ顔/大失態）」から始まること。
3. **気持ちのいいIN / OUT（神タイミングの呼吸）**:
   - **開始（IN）**: 言葉の頭切れがなく、話題や状況が立ち上がる自然かつインパクトのある瞬間から開始する。可能な限り、直前に0.3秒以上の無音・呼吸・間があるタイミングを選ぶ（不自然な音の断絶を避けるため）。
   - **終了（OUT）**: オチのツッコミ・爆笑・シュールな静寂・画面停止が最も気持ちよく決まり、**「思わずもう1周ループ再生したくなる」最高の余韻の瞬間**でスパッと切ること（尻切れトンボや意味のない余白は厳禁）。
4. **配信者の「コアの魅力・ギャップ」の可視化**:
   - 「可愛いのに口が悪い」「知的ぶっているのに盛大にポンコツ」「声が良すぎるのにやってることが狂気」など、配信者の最大の武器・人間味が一発で伝わるシーン。
5. **エンゲージメント誘発（コメント・シェア欲）**:
   - 「これは草」「分かりすぎるｗ」「自分ならこうする」など、視聴者が思わずコメント欄を開きたくなる議論・共感トリガーを含むこと。

---

# 📊 100点満点での「バズ＆フォロー転換」評価基準 (各20点・必ず個別採点すること):
1. **[Hook & Stop Rate] (20点)**: 最初の3秒で離脱を防ぎ、指を止めさせる引きの強さ
2. **[Standalone Context] (20点)**: 前後の文脈が不要で、このクリップ単体で話がスッキリ通じるか
3. **[Emotional Peak] (20点)**: 感情の起伏（笑い・驚き・尊さ・ツッコミどころ）が最大化されているか
4. **[Follow-Through Power] (20点)**: 初見視聴者が「この人もっと見たい！」とチャンネル登録したくなる魅力があるか
5. **[Loop & Timing Quality] (20点)**: 開始からオチまでのテンポが良く、終了タイミングが完璧に決まっているか

**{count}箇所は、全て同じ種類の感情（例:爆笑のみ）に偏らせず、可能な範囲で「笑い」「尊さ・共感」「ドン引き/カオス」「知的な鋭さ」など異なる魅力タイプを混ぜて提示すること。**

---

# Output Format (JSON形式を最優先で出力してください):

```json
[
  {
    "title": "初見が思わずタップするバズタイトル(15字以内・フック重視)",
    "start": "00:00:00",
    "end": "00:00:00",
    "thumbnail_frame": "00:00:00",
    "score_total": 98,
    "score_breakdown": {
      "hook_stop_rate": 20,
      "standalone_context": 19,
      "emotional_peak": 20,
      "follow_through_power": 19,
      "loop_timing_quality": 20
    },
    "hook": "冒頭3秒で引きつける衝撃のフック",
    "climax": "展開からオチへの流れ",
    "intro_telop": "画面中央に出すインパクト絶大な冒頭テロップ(15文字以内)",
    "follow_hook": "なぜこのシーンが初見のフォロー・登録につながるかの分析",
    "loop_reason": "なぜこの終了タイミングが気持ちよくループするかの解説",
    "context_check": "前後の文脈に依存していないと判断した理由（黄金原則1のチェック結果）"
  }
]
```

（※JSONに続けて、各候補の詳細な解説や構成案をマークダウン形式で記載しても構いません）

---

# Input Data:
# 配信者の特徴・ターゲット層: {profile}
# 今回の動画情報: {video_info}
{video_url}"""

def get_app_root_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

class ConfigManager:
    def __init__(self, config_dir, config_path):
        self.config_dir = config_dir
        self.config_path = config_path
        
        # system_files/learned/learned_data.json に保存
        self.app_root = get_app_root_dir()
        self.learned_dir = os.path.join(self.app_root, "system_files", "learned")
        self.learned_path = os.path.join(self.learned_dir, "learned_data.json")
        
        self.config_data = {}
        self.learned_data = {
            "vocabulary": {},
            "corrections": {},
            "timing_offsets": [],
            "stats": {"total_learned_edits": 0, "last_learned_at": ""}
        }

    def load_learned_data(self):
        """ローカルの自己学習データをロード（system_files/learned/learned_data.json）"""
        os.makedirs(self.learned_dir, exist_ok=True)
        
        # 過去パス（直下learnedやAPPDATA）からの自動移行
        old_root_path = os.path.join(self.app_root, "learned", "learned_data.json")
        old_appdata_path = os.path.join(self.config_dir, "learned_data.json")
        
        if not os.path.exists(self.learned_path):
            if os.path.exists(old_root_path):
                try:
                    import shutil
                    shutil.copy2(old_root_path, self.learned_path)
                except Exception: pass
            elif os.path.exists(old_appdata_path):
                try:
                    import shutil
                    shutil.copy2(old_appdata_path, self.learned_path)
                except Exception: pass

        if os.path.exists(self.learned_path):
            try:
                with open(self.learned_path, "r", encoding="utf-8") as f:
                    self.learned_data = json.load(f)
            except Exception:
                pass
        if "vocabulary" not in self.learned_data: self.learned_data["vocabulary"] = {}
        if "corrections" not in self.learned_data: self.learned_data["corrections"] = {}
        if "timing_offsets" not in self.learned_data: self.learned_data["timing_offsets"] = []
        if "stats" not in self.learned_data: self.learned_data["stats"] = {"total_learned_edits": 0, "last_learned_at": ""}
        return self.learned_data

    def save_learned_data(self):
        """ローカルの自己学習データを保存（完全オフライン・外部通信ゼロ）"""
        os.makedirs(self.learned_dir, exist_ok=True)
        try:
            with open(self.learned_path, "w", encoding="utf-8") as f:
                json.dump(self.learned_data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"学習データ保存失敗: {e}")

    def reset_learned_data(self):
        """自己学習データのリセット"""
        self.learned_data = {
            "vocabulary": {},
            "corrections": {},
            "timing_offsets": [],
            "stats": {"total_learned_edits": 0, "last_learned_at": ""}
        }
        self.save_learned_data()

    def get_effective_registered_words(self) -> str:
        """手動登録単語 ＋ 学習された高頻度単語を結合して Whisper initial_prompt 用に生成"""
        manual_words = [w.strip() for w in self.config_data.get("registered_words", "").split(",") if w.strip()]
        
        # 学習された単語の中から頻度上位（2回以上出現、または手動修正された語）を抽出
        learned_words = []
        vocab = self.learned_data.get("vocabulary", {})
        sorted_vocab = sorted(vocab.items(), key=lambda x: x[1], reverse=True)
        for word, count in sorted_vocab[:15]: # 上位15単語
            if word not in manual_words and len(word) >= 2:
                learned_words.append(word)
                
        all_words = manual_words + learned_words
        return ", ".join(all_words) if all_words else "初狐羽鹿, Vtuber, 逆転裁判, 切り抜き"

    def get_effective_replace_dict(self) -> dict:
        """手動置換辞書 ＋ 学習された誤字修正パターンを結合"""
        effective = dict(self.config_data.get("replace_dict", {}))
        # 学習された補正パターンを追加（手動設定が優先）
        for bad_w, good_w in self.learned_data.get("corrections", {}).items():
            if bad_w not in effective:
                effective[bad_w] = good_w
        return effective

    def learn_subtitle_diff(self, raw_subtitles: list, edited_subtitles: list):
        """ユーザーが字幕を編集した差分を解析し、単語・誤字置換・タイミングを自己学習"""
        if not raw_subtitles or not edited_subtitles:
            return 0
            
        import difflib
        import datetime
        import re

        edits_count = 0
        vocab = self.learned_data.setdefault("vocabulary", {})
        corrections = self.learned_data.setdefault("corrections", {})
        timing_offsets = self.learned_data.setdefault("timing_offsets", [])

        # 1. テキスト差分学習
        for r_sub, e_sub in zip(raw_subtitles, edited_subtitles):
            r_text = r_sub.get("raw_text") or r_sub.get("text", "")
            e_text = e_sub.get("text", "")
            
            if not r_text or not e_text or r_text == e_text:
                continue

            # 差分マッチャーで置換ペアを抽出
            matcher = difflib.SequenceMatcher(None, r_text, e_text)
            for tag, i1, i2, j1, j2 in matcher.get_opcodes():
                if tag == 'replace':
                    bad_part = r_text[i1:i2].strip()
                    good_part = e_text[j1:j2].strip()
                    if bad_part and good_part and bad_part != good_part:
                        if len(bad_part) <= 20 and len(good_part) <= 20: # 妥当な長さのフレーズのみ
                            corrections[bad_part] = good_part
                            edits_count += 1
                elif tag == 'insert':
                    inserted_word = e_text[j1:j2].strip()
                    if len(inserted_word) >= 2:
                        vocab[inserted_word] = vocab.get(inserted_word, 0) + 1

            # 編集後テキスト内の日本語名詞・固有名詞らしき単語の出現カウント
            words = re.findall(r'[一-龥々〆ヵヶぁ-んァ-ヶA-Za-z0-9_]{2,}', e_text)
            for w in words:
                vocab[w] = vocab.get(w, 0) + 1

            # 2. タイミング微調整の学習
            r_start = r_sub.get("raw_start", r_sub.get("start", 0.0))
            e_start = e_sub.get("start", 0.0)
            diff_start = e_start - r_start
            if abs(diff_start) > 0.05 and abs(diff_start) < 2.0:
                timing_offsets.append(diff_start)
                if len(timing_offsets) > 100:
                    timing_offsets.pop(0)

        # 肥大化防止のトリミング（上限ガード）
        if len(vocab) > 500:
            sorted_v = sorted(vocab.items(), key=lambda x: x[1], reverse=True)[:500]
            self.learned_data["vocabulary"] = dict(sorted_v)
        if len(corrections) > 300:
            corr_items = list(corrections.items())[-300:]
            self.learned_data["corrections"] = dict(corr_items)

        if edits_count > 0 or len(raw_subtitles) > 0:
            self.learned_data["stats"]["total_learned_edits"] = self.learned_data["stats"].get("total_learned_edits", 0) + edits_count
            self.learned_data["stats"]["last_learned_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.save_learned_data()

        return edits_count

    def load_config(self):
        os.makedirs(self.config_dir, exist_ok=True)
        
        # config.json がない場合、config.example.json から初期作成
        example_path = os.path.join(self.config_dir, "config.example.json")
        if not os.path.exists(self.config_path) and os.path.exists(example_path):
            try:
                import shutil
                shutil.copy2(example_path, self.config_path)
            except Exception: pass

        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    self.config_data = json.load(f)
            except Exception:
                self.config_data = {}
        if "templates" not in self.config_data or not self.config_data["templates"]:
            self.config_data["templates"] = {"標準の指示書テンプレート": DEFAULT_PROMPT_TEMPLATE.strip()}
        if "active_template" not in self.config_data or self.config_data["active_template"] not in self.config_data["templates"]:
            self.config_data["active_template"] = list(self.config_data["templates"].keys())[0]
        if "buffer_seconds" not in self.config_data:
            self.config_data["buffer_seconds"] = 0
        if "target_count" not in self.config_data:
            self.config_data["target_count"] = 5
        if "last_youtube_url" not in self.config_data:
            self.config_data["last_youtube_url"] = ""
        if "last_streamer_profile_char" not in self.config_data:
            self.config_data["last_streamer_profile_char"] = ""
        if "last_streamer_profile_target" not in self.config_data:
            self.config_data["last_streamer_profile_target"] = ""
        if "last_streamer_profile_genre" not in self.config_data:
            self.config_data["last_streamer_profile_genre"] = ""
        if "last_streamer_profile_subscribers" not in self.config_data:
            self.config_data["last_streamer_profile_subscribers"] = ""
        if "last_streamer_profile_platforms" not in self.config_data:
            self.config_data["last_streamer_profile_platforms"] = ""
        if "last_streamer_profile_shorts" not in self.config_data:
            self.config_data["last_streamer_profile_shorts"] = ""
        if "registered_words" not in self.config_data:
            self.config_data["registered_words"] = "初狐羽鹿, Vtuber, 逆転裁判, 切り抜き"
        if "replace_dict" not in self.config_data:
            self.config_data["replace_dict"] = {"初小端": "初狐羽鹿", "逆転サマ": "逆転裁判"}
        if "gemini_api_key" not in self.config_data:
            self.config_data["gemini_api_key"] = ""
        if "ui_font_family" not in self.config_data:
            self.config_data["ui_font_family"] = "Yu Gothic UI"
        if "ui_font_size" not in self.config_data:
            self.config_data["ui_font_size"] = 12
            
        self.load_learned_data()
        return self.config_data

    def save_config(self, config_data):
        self.config_data = config_data
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config_data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"設定保存失敗: {e}")

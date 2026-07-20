import os
import json

DEFAULT_PROMPT_TEMPLATE = """# Role:

あなたは100万登録超えのYouTubeチャンネルを担当する「プロの切り抜きディレクター」かつ「SNSマーケティングスペシャリスト」です。提供された動画コンテンツから、TikTok, YouTubeショート、Instagramリールで爆発的に拡散（バズ）する可能性が最も高い瞬間を特定し、詳細な編集プランを提示してください。
最低でも一つの動画につき{count}つのクリップ箇所を提示してください。



# Constraints:

1. 時間厳守：1つの候補は15秒以上〜58秒以内とする。

2. 構成重視：動画の最初の3秒で視聴者を離脱させない「強烈なフック（引き）」がある箇所を優先する。

3. 文脈の完結：その1分弱を見るだけで、話の前後を知らなくても内容が理解できる、あるいは「続きが気になる」構成にする。




# Evaluation Metrics (100点満点での評価基準):

各候補を以下の5項目（各20点）で分析し、合計点が高い順に抽出してください。

1. [Hook]：冒頭3秒で視聴者の手を止めさせるインパクトがあるか

2. [Emotion]：笑い、驚き、怒り、感動などの感情 of 振れ幅が大きいか

3. [Shareability]：誰かに教えたくなる、または議論（コメント）が起きやすい内容か

4. [Density]：無駄な間がなく、情報の密度が高いか

5. [Visual/Audio Focus]：テロップやエフェクトを入れやすい、動きや声のトーンの変化があるか



# Task Workflow:

1. 提供された文字起こし（または動画内容）を全スキャンし、盛り上がりを検知する。

2. 上記評価基準に基づき、スコアが高い上位{count}〜{count_plus_2}箇所を特定する。

3. 各箇所の「正確な開始・終了タイムスタンプ」を算出する。

4. 「フック・展開・オチ」を明確にした構成案を作成する。



# Output Format:

---

## ■ 厳選切り抜き候補 No.1（スコア：[点数] / 100）

- **タイムスタンプ:** [00:00:00] 〜 [00:00:00]（約[00]秒）

- **バズるタイトル:** [視聴者の欲望や好奇心を刺激する15文字以内のタイトル]

- **バズるタグ:** [視聴者の欲望や好奇心を刺激するハッシュタグ3～5種]

- **バズる概要欄:** [視聴者の欲望や好奇心を刺激する概要欄]

- **実際の動画の再生位置（時間）:** [00:00:00] 〜 [00:00:00]（約[00]秒）


- **【簡易的な動画構成】**

1. [00s-03s] **フック:** (例: 衝撃の発言から開始し、ズームアップ)

2. [03s-15s] **展開(フリ):** (例: なぜその発言に至ったかの経緯をテンポよく見せる)

3. [15s-終了] **クライマックス:** (例: 最高のリアクションや決定的な一言)



- **【動画としてのオチの付け方】**

- [オチの種類]: (例: 逆ギレ落ち / 無言 of シュール落ち / 爆笑落ち / 綺麗にまとめる教訓落ち)

- [具体的な終了方]: (例: 「〇〇じゃねーか！」というツッコミの瞬間に画面を白黒にして停止、または爆発エフェクトでカットアウト)



- **戦略的分析:**

- **フック:** 冒頭で[〇〇]という要素があるため、視聴維持率が高まります。

- **バズポイント:** [例: ギャップ萌え、共感、論破など]



- **編集指示書:**

- **冒頭テロップ:** [画面中央に大きく出すべき1行目のテキスト]

- **推奨BGM/効果音:** [例：不穏なBGMから一気に明るい曲へ切り替え、等]



---

（これを候補数分繰り返す）



# Input Data:

{video_url}"""

class ConfigManager:
    def __init__(self, config_dir, config_path):
        self.config_dir = config_dir
        self.config_path = config_path
        self.config_data = {}

    def load_config(self):
        os.makedirs(self.config_dir, exist_ok=True)
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
        if "registered_words" not in self.config_data:
            self.config_data["registered_words"] = "初狐羽鹿, Vtuber, 逆転裁判, 切り抜き"
        if "replace_dict" not in self.config_data:
            self.config_data["replace_dict"] = {"初小端": "初狐羽鹿", "逆転サマ": "逆転裁判"}
        return self.config_data

    def save_config(self, config_data):
        self.config_data = config_data
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config_data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"設定保存失敗: {e}")

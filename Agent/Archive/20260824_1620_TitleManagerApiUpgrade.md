# 20260824_1620_TitleManagerApiUpgrade.md

## 目的
`Title_manager_localize_Ver5.html` の Twitch API 認証・通信ロジックを、`TwitchManager`（`dev_1.0.3_NarrowViewportUI` 等）で実績のある最新の接続方式（アクセストークン自動検証・ID自動補完・ワンクリック連携方式）へ刷新・移植する。

## 対象ファイル
- `tools/Title_manager_配布用/Title_manager_localize_Ver5.html`

## 変更内容
1. **設定画面 UI の簡素化**:
   - 従来ユーザーが手動入力していた `user_id`, `user_login`, `client_id` を `type="hidden"` 化。
   - ユーザーは `Access Token`（またはToken GeneratorのURL全体）を貼り付けるだけのシンプルな入力導線に変更。
   - `ui-settings-auth-status` による連携ステータス表示（ログイン中: {ユーザー名} / 未連携）を追加。
   - 「Twitch Token GeneratorのURLをコピー」「Twitch連携を解除」ボタンを追加。
2. **トークン抽出・自動検証ロジックの導入**:
   - `extractTwitchAccessToken(value)`: `oauth:` プレフィックスやURLハッシュ（`#access_token=...`）から純粋なトークンを自動抽出。
   - `refreshTwitchAuthFromToken(showError)`: `https://id.twitch.tv/oauth2/validate` を呼び出して有効性を検証し、`user_id`, `login`, `client_id` を自動取得。
   - `onTokenInputChanged()`: 入力時のリアルタイム自動検証（debounce）。
   - `saveSettings()`: 保存時に自動検証を実行。
3. **API通信の安全性向上**:
   - `apiRequest`, `pushToTwitch`, `syncWithTwitch` で、`settings.userId` が未設定の場合でもトークンから自動で認証補完を試行する安全設計を導入。

## 検証結果
- JS構文チェック（vm.Script）: エラーなし（PASS）
- 設定モーダル表示・トークン入力・自動検証・保存処理の連携フロー確認完了

# TitleRaidDock

Twitch 配信用の OBS カスタムブラウザドックです。

## 配布内容

- `TitleRaidDock.html`
- `sounds/`
- `README.md`

## 導入手順

1. 配布フォルダを任意の場所に置きます。
2. OBS で `ドック` > `カスタムブラウザドック` を開きます。
3. 名前に `TitleRaidDock` などを入力します。
4. URL に `TitleRaidDock.html` の `file:///` 形式の URL を貼り付けます。

例:

```text
file:///C:/Users/ユーザー名/Documents/TitleRaidDock/TitleRaidDock.html
```

`C:\Users\...` のような Windows パスをそのまま貼ると、フォルダ一覧が表示されることがあります。OBS には必ず `file:///` で始まる URL を登録してください。

## 初期設定

1. ドック右上の設定ボタンを開きます。
2. `Twitch Token GeneratorのURLをコピー` を押し、コピーしたURLを普段使っているブラウザで開きます。
3. Twitch Token Generatorで `Custom Scope Token` を選び、必要な権限にチェックを入れて `Generate Token` します。
4. 表示された `ACCESS TOKEN` を、設定画面の `アクセストークン` 欄へ貼り付けて保存します。
5. 保存後、連携先チャンネルとClient IDは自動で確認されます。
6. 音源を追加・変更した場合は、`音源リストを更新` から `sounds/` フォルダを選び直します。

## バックアップ

ブラウザキャッシュを削除する前や別環境へ移す前に、`バックアップ` タブで設定をコピーしてください。

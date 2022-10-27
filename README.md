# discordpy-startup

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

- Herokuでdiscord.pyを始めるテンプレートです。
- Use Template からご利用ください。
- 使い方はこちら： [Discord Bot 最速チュートリアル【Python&Heroku&GitHub】 - Qiita](https://qiita.com/1ntegrale9/items/aa4b373e8895273875a8)

## 各種ファイル情報

### discordbot.py
PythonによるDiscordBotのアプリケーションファイルです。

### requirements.txt
使用しているPythonのライブラリ情報の設定ファイルです。

### Procfile
Herokuでのプロセス実行コマンドの設定ファイルです。

### runtime.txt
Herokuでの実行環境の設定ファイルです。

### app.json
Herokuデプロイボタンの設定ファイルです。

### .github/workflows/flake8.yaml
GitHub Actions による自動構文チェックの設定ファイルです。

### .gitignore
Git管理が不要なファイル/ディレクトリの設定ファイルです。

### LICENSE
このリポジトリのコードの権利情報です。MITライセンスの範囲でご自由にご利用ください。

### README.md
このドキュメントです。

# 行ったこと
- fly.ioに移行
- view リファクタリング
- logging
- 一部 aiohttpに
- message edit時の読み上げ

# 行うこと
- message削除機能 副隊長にロール

## requirementsの書き方

### インストール
```
pip install -r requirements.txt
```
### 書き出し
```
pip freeze > requirements.txt
```
## herokuへのプッシュ
```
heroku git:remote -a example-app
```
```
git push heroku main
```
## herokuから環境変数を取得
```
heroku config:pull -a appname
```

## discord.py 2.0 インストール
```
python -m pip install git+https://github.com/Rapptz/discord.py
```

# Emoji
 ==================== Emojis ====================  
🌱  :seedling: 初めてのコミット（Initial Commit）  
🔖  :bookmark: バージョンタグ（Version Tag）  
✨  :sparkles: 新機能（New Feature）  
🐛  :bug: バグ修正（Bugfix）  
♻️  :recycle: リファクタリング(Refactoring)  
📚  :books: ドキュメント（Documentation）  
🎨  :art: デザインUI/UX(Accessibility)  
🐎  :horse: パフォーマンス（Performance）  
🔧  :wrench: ツール（Tooling）  
🚨  :rotating_light: テスト（Tests）  
💩  :hankey: 非推奨追加（Deprecation）  
🗑️  :wastebasket: 削除（Removal）  
🚧  :construction: WIP(Work In Progress)

https://discord.com/api/oauth2/authorize?client_id=758857025516994570&permissions=287548099648&scope=bot%20applications.commands

# 行ったこと
- ボイスチャンネルのメンバーを取得する
- ボイチャ入出ログ機能
- extension(Cogs)使ったスラッシュコマンドの実装方法確認
- コンテキストメニュー実装方法確認
- クランマッチスケジュールに報酬獲得条件を追加
- ボタン実装(クランマッチスケジュール、ダイス、ダイス結果、登録、チーム分け)
- チーム分け(ランダム)実装
- cogの正しい使い方(?cogreload)コマンド実装
- 基本的にボタンView上に表示させる
- ボイチャ分け、チーム分け実装
- ホスト太字
- cog整理 (Eventの処理をcog化)
- discord.py 2.0への移行
- ボイスチャットログをスマートにする　入室何人とか
- ボイス退出の処理　メンバーの中からテンダボットを探してdisconnectする
- ボイス入室、退室の名前をボットボイス入室、退出に変更
- スラッシュコマンドごとにインスタンス生成する　TendaView
- Modalのアクセスについて検討
- wiki参照して機体ページ表示
- 起動時にインタラクション不通になったボタンを無効化する機能を追加
- ボイチャ分けしたときにチーム編成が消えてしまうのを修正
- 「ダイスロール」実行後、「ダイス結果」が有効にならないバグを修正
- wiki参照ステータス表示ベータ
- メンバー選択バグ修正, embed対応(仮)
- メンバー選択人が抜けた後の処理
- 右クリックメニューで機体検索できるように
- ボイスチャット状況をボタンと同じところに
- レート分けした時の名前表示をdisplay_nameに
- ボイチャ移動の時に取り残されるのを防ぐためにasyncio.sleep(1)を入れた
- ランダム機体選択機能追加
- メッセージ更新処理 (ダイス)
- ダイス結果を順々に表示させていく、さらにソート50に近いも表示
- 読み上げ自動化
- debugモードを選択できるように
- ランダム機体選択数字かぶらないように
- 読み上げ中に投稿したメッセージが読み上げられないバグを修正
- ステージ取得
- クランマッチお知らせ embed化
- 公式, wikiのボタン設置
- 2022年8月1日-> 2022/8/1
- 正方形クロップ
- ms選択(一括)の数字かぶらないように
- ルール決め刷新 (マップ取得利用した画像等)

# アイディア
- 練習、本番後にクランマッチスケジュールを表示
- ボイスチャンネル内メンバーを取得する処理を関数化
- コンテキストメニューに追加 (登録、機体決め、クランマッチ、wiki、ゲームルール選択)
- 選択画像上に名前載せる？
- コンテキストメニューにボット入室、退室追加
- アラームコマンド
- メッセージ送信方式を編集から逐次削除方式に、Embed化 (チーム決め、メンバー選択, レーティング登録)
- class化
- refresh message化 ダイス、クランマッチスケジュール
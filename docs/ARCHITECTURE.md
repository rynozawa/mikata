# Architecture

## 目的

OpenClaw Companionは、CLI上のエージェント作業に「一緒に作業している感覚」を足すプロトタイプです。単なる実行ログではなく、横にいる共同開発者が状況を見て声をかける体験を狙います。

## ディレクトリ構成

```text
openclaw_companion/
  app.py          Textual UI、画面構成、イベント処理
  agent.py        タスク実行アダプタ。現在はローカルコマンドと擬似Agent
  focus.py        キーボード、アイドル、アクティブウィンドウの監視
  models.py       FocusSnapshot、CompanionMessage、Tone
  personality.py  反応モードと発話ルール
docs/
  ARCHITECTURE.md
  DEMO.md
  FUTURE.md
```

## コンポーネント

### CLI UI

Textualで常駐UIを作ります。

- 左: 会話ログ、タスク進捗、Companionの声かけ
- 右: focus score、idle、terminal active、app switches、active window
- 下: タスク入力

ターミナル上で人が隣にいる感覚を出すため、UIを「ダッシュボード」ではなく「作業卓」に寄せています。ログは機械的なイベントだけでなく、開始、観察、励まし、軽い冗談が混ざります。

### Agent Task

`AgentRunner` は将来のOpenClaw連携ポイントです。

- `!command`: ローカルコマンドを実行
- 通常テキスト: 擬似エージェントとして段階的な進捗を返す

OpenClaw本体とつなぐ場合は、`AgentRunner.run()` の中をOpenClaw CLI呼び出し、HTTP API、またはPython SDKに置き換えます。

### Focus Monitor

`FocusMonitor` は4秒ごとに以下をサンプリングします。

- キーボード入力数
- 最後の入力からのアイドル秒数
- アクティブウィンドウ名
- ターミナルが前面かどうか
- 直近のウィンドウ切替回数

スコアは簡易式です。

```text
score =
  50
  + keyboard activity
  + terminal active bonus
  - idle penalty
  - rapid app switching penalty
```

監視の目的は評価や叱責ではなく、自己調整の補助です。声かけは罪悪感を煽らず、「戻れる小さな一歩」を提示します。

### Personality

`CompanionPersonality` が `praise` / `neutral` / `tease` / `encourage` を選びます。

- praise: 集中継続を認識して強化
- neutral: 横にいる感覚を維持
- tease: 脱線を軽く指摘
- encourage: 停滞を再始動できる粒度に戻す

重要なのは、作業者を管理対象にしないことです。Companionは上司ではなく、同じ机にいる共同作業者として振る舞います。

### Distraction AI Reaction

`distraction.py` がアクティブウィンドウ名から `twitter`、`x.com`、`youtube`、`steam`、ゲーム名などを検知します。

検知した場合、`AIReactionEngine` が短い日本語の声かけを生成します。

- `OPENAI_API_KEY` がある: Responses APIへ文脈を渡して生成
- `OPENAI_API_KEY` がない: ローカルの安全なフォールバック文言

生成プロンプトでは、監視感、罪悪感、威圧を避け、35文字以内で「次の小さな一手」へ戻すように制約しています。

## データフロー

```text
User input
  -> Textual Input
  -> AgentRunner
  -> Conversation Log

Keyboard / Window state
  -> FocusMonitor
  -> FocusSnapshot
  -> StatusPanel
  -> distraction detection
  -> AIReactionEngine
  -> CompanionPersonality
  -> Conversation Log
```

## ローカル優先

現時点ではデータを永続化しません。観測値はメモリ内のみで扱い、ハッカソンのデモで導入しやすい構成にしています。

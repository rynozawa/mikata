# ADHD OpenClaw Pet

画面の端にAIキャラが常駐し、タスク集中とOpenClawのコーディング作業を一緒に見せるハッカソンMVPです。

## セットアップ

```bash
npm install
npm run dev
```

ブラウザで `http://127.0.0.1:5173` を開きます。

macOSで常駐風ウィンドウも出す場合:

```bash
npm run desktop
```

## OpenClaw連携

デフォルトはデモモードです。OpenClaw未インストール環境でも、実装中、テスト中、commit中、PR作成中、完了の流れを再現します。

実OpenClawを走らせる場合:

```bash
OPENCLAW_REAL=1 OPENCLAW_WORKSPACE=/path/to/demo-repo npm run dev
```

このモードでは、アプリが `openclaw agent --message ... --thinking high` を実行します。ハッカソンでは必ずデモ用リポジトリを `OPENCLAW_WORKSPACE` に指定してください。

## プライバシー境界

MVPで扱うのはメタ情報のみです。

- アイドル秒数
- アクティブアプリ名
- Gitブランチ、未コミット数、最終コミット
- OpenClawジョブ状態と実行ログ
- 直近のユーザー入力メモ

以下は保存しません。

- キー入力本文
- スクリーンショット
- メール本文
- チャット本文
- 画面本文

## デモの流れ

1. 今日のタスクを追加し、「今やる1つ」にする
2. AIキャラが現在タスクと気分に応じた声かけを出す
3. `OpenClawに任せる` を押す
4. キャラが作業中の動きになり、OpenClawログが進む
5. `停止` や `脱線` を押して、リマインドの反応を見る
6. 完了後もキャラが応援・整理モードで伴走する

## 検証コマンド

```bash
npm test -- --run
npm run build
```

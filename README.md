# OpenClaw Companion

ターミナル上で一緒に作業してくれる「Companion Worker」のハッカソン向けプロトタイプです。

OpenClaw Companion は、コーディングや課題実装を代行するだけのCLIではなく、作業中のユーザーの横にいる友人・先輩・共同開発者のように振る舞います。集中している時は静かに伴走し、脱線しそうな時は軽い皮肉や励ましで作業へ戻します。

## 想定ユーザー

- CLI中心で作業するソフトウェア開発者
- 42 Tokyo生など、ターミナルで課題に取り組む人
- 一人作業で集中維持が難しい人
- ADHD傾向などで作業開始・継続に困難がある人

## 主な機能

- Textual製のターミナルUI
- CompanionログとWorkerログの分離表示
- OpenClaw / Codex などローカルAIワーカーへのタスク委譲
- `!pytest` や `!dir` などのローカルコマンド実行
- キーボード、マウス、アクティブウィンドウ、アイドル時間の簡易観測
- X / YouTube / ゲーム / SNS などへの脱線検知
- 状況に応じた励まし、皮肉、応援メッセージ生成
- `docs/terminal-kaomoji.txt` に2行の顔文字ステータスを出力
- VOICEVOX Engine が起動している場合、脱線・停滞時の注意を読み上げ

## セットアップ

```powershell
cd C:\Users\nsabu\Documents\mikatahakkason
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[windows-monitor]"
```

## 起動

```powershell
openclaw-companion
```

仮想環境を有効化せずに起動する場合:

```powershell
C:\Users\nsabu\Documents\mikatahakkason\.venv\Scripts\openclaw-companion.exe
```

## OpenClaw / Codex 連携

Companionは、通常タスクをローカルAIワーカーへ渡します。コマンド形式は環境変数で指定できます。

Codex直結の例:

```powershell
$env:OPENCLAW_COMPANION_AGENT_CMD='C:\Users\nsabu\.vscode\extensions\openai.chatgpt-26.519.32039-win32-x64\bin\windows-x86_64\codex.exe exec --sandbox workspace-write -C C:\Users\nsabu\Documents\mikatahakkason {prompt}'
openclaw-companion
```

OpenClaw Gateway経由の例:

```powershell
$env:OPENCLAW_COMPANION_AGENT_CMD='C:\Users\nsabu\AppData\Roaming\npm\openclaw.cmd agent --agent main --message {prompt}'
openclaw-companion
```

`{prompt}` がCompanionから渡されるタスク本文に置き換わります。

## 使い方

入力欄にタスクを入れて Enter を押します。

例:

```text
htmlのテトリスを tetris.html として実装して
```

```text
課題.pdfを読んで、問題を解いて実装して
```

```text
READMEを発表向けに整えて
```

`!` で始めるとAIではなくローカルシェルコマンドとして実行します。

```text
!pytest
```

```text
!dir
```

## 画面操作

- `F5` / `F6`: Focusペインを狭く / 広く
- `F7` / `F8`: Companion / Worker の高さ比率を変更
- `Alt+←` / `Alt+→`: Focusペインを狭く / 広く
- `Alt+↓` / `Alt+↑`: Companion / Worker の高さ比率を変更
- `Ctrl+0`: レイアウトをリセット
- `q`, `Esc`, `Ctrl+C`: 終了
- 入力欄で `exit`, `quit`, `:q`: 終了

## 顔文字サイド表示

`docs/terminal-kaomoji.txt` は、Companionの現在状態を2行だけで出力するファイルです。

別ペインで次を実行すると、tmux風に端へ常駐表示できます。

```powershell
while ($true) { cls; Get-Content docs\terminal-kaomoji.txt; Start-Sleep 1 }
```

表示例:

```text
(=_=)
I am working. Are you surfing?
```

PowerShell/tmuxで文字化けしにくいように、この2行表示はASCIIのみで出力しています。

## VOICEVOX読み上げ

VOICEVOX Engineをローカルで手動起動しておくと、Companionが脱線・停滞時の声かけを読み上げます。

想定URL:

```text
http://127.0.0.1:50021
```

VOICEVOX Engineを起動してからCompanionを起動してください。起動時にWorker欄へ `VOICEVOX connected` と出れば有効です。

設定を変える場合:

```powershell
$env:VOICEVOX_URL="http://127.0.0.1:50021"
$env:VOICEVOX_SPEAKER="3"
$env:VOICEVOX_COOLDOWN="20"
```

読み上げを無効化する場合:

```powershell
$env:VOICEVOX_ENABLED="0"
```

## デモ手順

1. Companionを起動する
2. `htmlのテトリスを tetris.html として実装して` を入力する
3. Worker欄にCodex/OpenClawの作業ログが流れる
4. XやYouTubeを開く
5. Companionがすぐに皮肉を言い、顔文字表示も変わる
6. `tetris.html` が生成されることを見せる

## ディレクトリ構成

```text
openclaw_companion/
  app.py              Textual UI
  agent.py            タスク実行とシェルコマンド
  openclaw_bridge.py  OpenClaw / Codex 連携
  focus.py            集中状態の観測
  distraction.py      X / YouTube / SNS などの検知
  ai_reactions.py     AIによる声かけ生成
  personality.py      ルールベースの声かけ
  activity_journal.py 作業ログ記録
  kaomoji_status.py   2行顔文字ステータス出力
docs/
  ARCHITECTURE.md
  DEMO.md
  FUTURE.md
  terminal-kaomoji.txt
```

## 注意

- 作業ログは `logs/activity.jsonl` に保存されます。
- `.venv/`, `logs/`, `__pycache__/`, `*.egg-info/` は `.gitignore` で除外しています。
- X / YouTube は発表用に即時反応しやすくしています。

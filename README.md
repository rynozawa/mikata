# OpenClaw Companion

Terminal companion worker prototype.

It stays in the terminal, helps with coding tasks, and reacts to focus drift like a friendly coworker sitting next to you.

## MVP

- CLI UI with Textual
- Task input and progress log
- Local command execution with `!`
- Delegation to the local OpenClaw/OpenClew agent on this PC
- Focus monitor for keyboard activity, idle time, active window, and app switching
- AI-generated distraction reactions through the local agent

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[windows-monitor]"
```

## Connect To Local OpenClaw

By default Companion tries these local commands:

1. `openclaw`
2. `openclew`
3. `codex`

If your local agent uses a different command shape, set a command template:

```powershell
$env:OPENCLAW_COMPANION_AGENT_CMD='openclaw run --yes {prompt}'
openclaw-companion
```

If your agent expects the prompt on stdin:

```powershell
$env:OPENCLAW_COMPANION_AGENT_CMD='openclaw run --yes'
$env:OPENCLAW_COMPANION_AGENT_STDIN='1'
openclaw-companion
```

The `{prompt}` placeholder is replaced with the task or companion reaction prompt.

## Usage

- Type a task and press Enter.
- `!dir`, `!pytest`, etc. run local shell commands.
- Normal tasks are passed to the local OpenClaw/OpenClew worker.
- Examples:
  - `htmlでテトリスを実装して`
  - `課題.pdfから問題を解いて実装して`
  - `このプロジェクトのREADMEを整えて`
- When Twitter/X, YouTube, Steam, games, Discord, etc. become active, Companion asks the local agent to generate a short nudge.
- `Ctrl+C` quits.

## Files

- `openclaw_companion/app.py`: Textual UI
- `openclaw_companion/agent.py`: task delegation and shell commands
- `openclaw_companion/openclaw_bridge.py`: local OpenClaw/OpenClew bridge
- `openclaw_companion/focus.py`: focus monitor
- `openclaw_companion/distraction.py`: distraction detection
- `openclaw_companion/ai_reactions.py`: local-agent-generated reactions
- `docs/ARCHITECTURE.md`: architecture notes
- `docs/DEMO.md`: demo scenario
- `docs/FUTURE.md`: future ideas

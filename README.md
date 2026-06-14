# OpenClaw Companion

OpenClaw Companion is an open-source terminal companion for developers using
local AI coding agents such as Codex, OpenClaw, or OpenClew.

It stays next to your coding workflow in the terminal: you can delegate a task
to a local agent, run shell commands, keep a lightweight progress log, and get
small focus nudges when your active window suggests you have drifted away from
the work. The project is intentionally local-first so individual developers and
OSS maintainers can experiment with agent workflows without sending project
state to a hosted service by default.

## Why This Exists

AI coding agents are useful, but the surrounding workflow can still feel
fragmented: prompts live in one place, commands in another, progress in another,
and focus recovery is left to the developer. OpenClaw Companion explores a small
OSS layer around those tools:

- a terminal UI for task delegation and progress feedback
- a bridge to Codex/OpenClaw-style local agent commands
- local command execution with explicit `!` commands
- local focus and distraction signals
- optional VOICEVOX speech for focus recovery nudges
- a two-line terminal status file for side-pane displays

The goal is not to replace an AI coding agent. It is to make agent-assisted
maintenance work easier to operate, observe, and improve.

## Status

This is an early prototype. The terminal UI, local command bridge, focus signals,
distraction detection, VOICEVOX integration, and kaomoji status output are
present. APIs and UI behavior may change while the project is still small.

## Features

- Textual-based terminal UI
- Separate companion and worker logs
- Task delegation to local AI workers such as Codex, OpenClaw, or OpenClew
- `!pytest`, `!dir`, and other explicit local shell commands
- Keyboard, mouse, active-window, idle-time, and app-switching signals
- Distraction detection for X, YouTube, games, social apps, and similar windows
- AI-generated or rule-based focus nudges
- `docs/terminal-kaomoji.txt` side-pane status output
- Optional VOICEVOX Engine speech for distraction or stalled-work nudges

## Setup

Requirements:

- Python 3.10+
- A local agent command such as `codex`, `openclaw`, or `openclew` if you want
  task delegation
- Windows optional dependencies if you want active-window monitoring on Windows
- Optional VOICEVOX Engine if you want local speech output

Create an environment and install the package:

```powershell
cd <YOUR_PROJECT_DIR>
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev,windows-monitor]"
```

On macOS or Linux:

```bash
cd <YOUR_PROJECT_DIR>
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Run

```bash
openclaw-companion
```

In the terminal UI:

- Type a normal task to send it to the configured local agent.
- Prefix a command with `!` to run it locally, for example `!pytest`.
- Press `q`, `Esc`, or `Ctrl+C` to quit.

## Connect Codex, OpenClaw, Or Another Local Agent

By default, Companion tries these commands in order:

1. `openclaw`
2. `openclew`
3. `codex`

If your local agent uses a different command shape, set a command template:

```powershell
$env:OPENCLAW_COMPANION_AGENT_CMD='<PATH_TO_CODEX_OR_OPENCLAW> {prompt}'
openclaw-companion
```

The `{prompt}` placeholder is replaced with the task or companion reaction
prompt.

If your agent expects the prompt on stdin:

```powershell
$env:OPENCLAW_COMPANION_AGENT_CMD='<PATH_TO_CODEX_OR_OPENCLAW>'
$env:OPENCLAW_COMPANION_AGENT_STDIN='1'
openclaw-companion
```

Unix shell equivalent:

```bash
export OPENCLAW_COMPANION_AGENT_CMD='<PATH_TO_CODEX_OR_OPENCLAW> {prompt}'
openclaw-companion
```

## Optional VOICEVOX Speech

If VOICEVOX Engine is running locally, Companion can read some distraction or
stalled-work nudges aloud.

Default endpoint:

```text
http://127.0.0.1:50021
```

Configuration:

```powershell
$env:VOICEVOX_URL='http://127.0.0.1:50021'
$env:VOICEVOX_SPEAKER='3'
$env:VOICEVOX_COOLDOWN='20'
```

Disable speech:

```powershell
$env:VOICEVOX_ENABLED='0'
```

## Side-Pane Status

`docs/terminal-kaomoji.txt` contains the current two-line companion status. You
can show it in another terminal pane:

```powershell
while ($true) { cls; Get-Content docs\terminal-kaomoji.txt; Start-Sleep 1 }
```

## Development

Install development dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Run tests:

```bash
pytest
```

## Project Docs

- [Architecture](docs/ARCHITECTURE.md)
- [Demo Scenario](docs/DEMO.md)
- [Future Ideas](docs/FUTURE.md)

## Privacy And Secrets

Do not commit local `.env` files, API keys, tokens, screenshots with private
workspace data, or machine-specific paths. Configure local agents through
environment variables such as `OPENCLAW_COMPANION_AGENT_CMD`.

## License

MIT. See [LICENSE](LICENSE).

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
- focus and distraction signals that remain local to the machine
- personality hooks that make agent work feel less like a cold job runner

The goal is not to replace an AI coding agent. It is to make agent-assisted
maintenance work easier to operate, observe, and improve.

## Status

This is an early prototype. The core terminal flow, local command bridge, focus
signals, and distraction detection are present. APIs and UI behavior may change
while the project is still small.

## Setup

Requirements:

- Python 3.10+
- A local agent command such as `codex`, `openclaw`, or `openclew` if you want
  task delegation
- Windows optional dependencies if you want active-window monitoring on Windows

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
- Press `Ctrl+C` to quit.

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

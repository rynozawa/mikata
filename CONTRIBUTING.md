# Contributing

Thanks for taking a look at OpenClaw Companion. This project is a small
local-first experiment around AI coding agent workflows, and issues or pull
requests are welcome.

## Development Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

On Windows, install the optional monitor dependencies when working on
active-window or keyboard activity features:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev,windows-monitor]"
```

## Tests

Run the test suite before opening a pull request:

```bash
pytest
```

## Good First Areas

- Improve Codex/OpenClaw command adapters.
- Add more tests around focus and distraction detection.
- Make the terminal UI easier to scan during long-running agent tasks.
- Improve local-only privacy controls and documentation.

## Pull Requests

Small, focused pull requests are easiest to review. Please include a short
description of the change, any user-facing behavior, and the test command you
ran.

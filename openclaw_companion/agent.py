from __future__ import annotations

import asyncio
import os
import shlex
from collections.abc import AsyncIterator

from .openclaw_bridge import LocalAgentBridge


TASK_PROMPT = """You are the local AI worker behind OpenClaw Companion.
Work in the current project directory.
The user wants this done:

{task}

If implementation is requested, edit/create the necessary files.
If a PDF or assignment is mentioned, inspect local files when possible, solve the task,
and create implementation files or a concise solution note.
Stream useful progress updates. Be concrete about files changed and commands run."""


class AgentRunner:
    """Runs shell commands or delegates real work to the local OpenClaw/OpenClew agent."""

    def __init__(self, bridge: LocalAgentBridge | None = None) -> None:
        self.bridge = bridge or LocalAgentBridge()

    async def run(self, task: str) -> AsyncIterator[str]:
        stripped = task.strip()
        if stripped.startswith("!"):
            async for line in self._run_command(stripped[1:].strip()):
                yield line
            return

        yield "Handing this to the local OpenClaw worker on your PC."
        prompt = TASK_PROMPT.format(task=stripped)
        async for line in self.bridge.stream(prompt):
            yield line

    async def _run_command(self, command: str) -> AsyncIterator[str]:
        if not command:
            yield "Empty command. Try something like `!pytest`."
            return

        yield f"Running `{command}`."
        if os.name == "nt":
            proc = await asyncio.create_subprocess_exec(
                "powershell",
                "-NoProfile",
                "-Command",
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )
        else:
            proc = await asyncio.create_subprocess_exec(
                *shlex.split(command),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )

        assert proc.stdout is not None
        while True:
            line = await proc.stdout.readline()
            if not line:
                break
            yield line.decode(errors="replace").rstrip()

        code = await proc.wait()
        if code == 0:
            yield "Command finished."
        else:
            yield f"Command exited with code {code}. Let's read the log together."

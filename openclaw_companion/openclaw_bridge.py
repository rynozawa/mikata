from __future__ import annotations

import asyncio
import os
import shlex
from collections.abc import AsyncIterator
from dataclasses import dataclass


DEFAULT_AGENT_COMMANDS = (
    "openclaw",
    "openclew",
    "codex exec --sandbox workspace-write",
)


@dataclass(slots=True)
class LocalAgentBridge:
    """Bridge to the AI agent already installed on this PC.

    Configuration:
    - OPENCLAW_COMPANION_AGENT_CMD:
      Command template. If it contains {prompt}, the prompt is substituted there.
      Example: openclaw run --yes {prompt}
    - OPENCLAW_COMPANION_AGENT_STDIN=1:
      Send the prompt to stdin instead of passing it as an argument.
    """

    timeout_seconds: int = 240

    def configured_command(self) -> list[str]:
        command = os.getenv("OPENCLAW_COMPANION_AGENT_CMD", "").strip()
        if command:
            return shlex.split(command, posix=os.name != "nt")
        for candidate in DEFAULT_AGENT_COMMANDS:
            return [candidate]
        return []

    def command_candidates(self) -> list[list[str]]:
        command = os.getenv("OPENCLAW_COMPANION_AGENT_CMD", "").strip()
        if command:
            return [shlex.split(command, posix=os.name != "nt")]
        return [shlex.split(candidate, posix=os.name != "nt") for candidate in DEFAULT_AGENT_COMMANDS]

    def is_configured(self) -> bool:
        return bool(self.configured_command())

    async def ask(self, prompt: str) -> str | None:
        chunks: list[str] = []
        async for line in self.stream(prompt):
            chunks.append(line)
        output = "\n".join(chunks).strip()
        return output or None

    async def stream(self, prompt: str) -> AsyncIterator[str]:
        candidates = self._argv_candidates_for_prompt(prompt)
        if not candidates:
            yield self.setup_hint()
            return

        use_stdin = os.getenv("OPENCLAW_COMPANION_AGENT_STDIN", "").lower() in {"1", "true", "yes"}
        proc = None
        last_missing = candidates[0][0]
        for argv in candidates:
            try:
                proc = await asyncio.create_subprocess_exec(
                    *argv,
                    stdin=asyncio.subprocess.PIPE if use_stdin else None,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.STDOUT,
                )
                break
            except FileNotFoundError:
                last_missing = argv[0]
        if proc is None:
            yield self.setup_hint(last_missing)
            return

        if use_stdin and proc.stdin is not None:
            proc.stdin.write(prompt.encode("utf-8"))
            await proc.stdin.drain()
            proc.stdin.close()

        assert proc.stdout is not None
        try:
            while True:
                line = await asyncio.wait_for(proc.stdout.readline(), timeout=self.timeout_seconds)
                if not line:
                    break
                yield line.decode("utf-8", errors="replace").rstrip()
        except asyncio.TimeoutError:
            proc.kill()
            yield "Local OpenClaw timed out. The task may need a smaller first step."
            return

        code = await proc.wait()
        if code != 0:
            yield f"Local OpenClaw exited with code {code}."

    def _argv_for_prompt(self, prompt: str) -> list[str]:
        argv = self.configured_command()
        if not argv:
            return []

        replaced = False
        result: list[str] = []
        for part in argv:
            if "{prompt}" in part:
                result.append(part.replace("{prompt}", prompt))
                replaced = True
            else:
                result.append(part)

        use_stdin = os.getenv("OPENCLAW_COMPANION_AGENT_STDIN", "").lower() in {"1", "true", "yes"}
        if not replaced and not use_stdin:
            result.append(prompt)
        return result

    def _argv_candidates_for_prompt(self, prompt: str) -> list[list[str]]:
        return [self._inject_prompt(argv, prompt) for argv in self.command_candidates()]

    @staticmethod
    def _inject_prompt(argv: list[str], prompt: str) -> list[str]:
        replaced = False
        result: list[str] = []
        for part in argv:
            if "{prompt}" in part:
                result.append(part.replace("{prompt}", prompt))
                replaced = True
            else:
                result.append(part)

        use_stdin = os.getenv("OPENCLAW_COMPANION_AGENT_STDIN", "").lower() in {"1", "true", "yes"}
        if not replaced and not use_stdin:
            result.append(prompt)
        return result

    @staticmethod
    def setup_hint(command_name: str | None = None) -> str:
        command = command_name or "openclaw/openclew/codex"
        return (
            f"Cannot find local agent command `{command}`. "
            "Set OPENCLAW_COMPANION_AGENT_CMD, for example: "
            "`$env:OPENCLAW_COMPANION_AGENT_CMD='openclaw run --yes {prompt}'`"
        )

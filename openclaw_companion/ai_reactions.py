from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from .distraction import DistractionSignal
from .models import FocusSnapshot, Tone
from .openclaw_bridge import LocalAgentBridge


REACTION_PROMPT = """You are Claw, a terminal companion worker.
The user is coding or studying. A likely distraction is active.

category={category}
keyword={keyword}
window_title={window_title}
focus_score={score}
idle_seconds={idle_seconds}
app_switches={app_switches}

Write exactly ONE short Japanese message.
Rules:
- 35 characters max.
- Friendly coworker tone.
- Playful is OK, but do not shame, threaten, or guilt-trip.
- Do not mention monitoring or surveillance.
- Nudge the user back to one tiny next action."""


@dataclass
class AIReactionEngine:
    cooldown_seconds: int = 45
    bridge: LocalAgentBridge = field(default_factory=lambda: LocalAgentBridge(timeout_seconds=20))
    rng: random.Random = field(default_factory=random.Random)
    last_reacted_at: datetime | None = None
    last_label: str = ""

    async def generate(
        self,
        signal: DistractionSignal,
        snapshot: FocusSnapshot,
    ) -> tuple[Tone, str] | None:
        if not self._should_react(signal):
            return None

        self.last_reacted_at = datetime.now()
        self.last_label = signal.label

        generated = await self._generate_with_local_agent(signal, snapshot)
        if generated:
            return Tone.TEASE, generated
        return Tone.TEASE, self._fallback(signal)

    def _should_react(self, signal: DistractionSignal) -> bool:
        now = datetime.now()
        if self.last_reacted_at is None:
            return True
        if now - self.last_reacted_at >= timedelta(seconds=self.cooldown_seconds):
            return True
        return signal.label != self.last_label and self.rng.random() < 0.35

    async def _generate_with_local_agent(
        self,
        signal: DistractionSignal,
        snapshot: FocusSnapshot,
    ) -> str | None:
        prompt = REACTION_PROMPT.format(
            category=signal.category,
            keyword=signal.keyword,
            window_title=signal.window_title[:120],
            score=snapshot.score,
            idle_seconds=f"{snapshot.idle_seconds:.0f}",
            app_switches=snapshot.app_switches,
        )
        output = await self.bridge.ask(prompt)
        if not output or output.startswith("Cannot find local agent command"):
            return None
        return _clean(output)

    def _fallback(self, signal: DistractionSignal) -> str:
        by_category = {
            "social": [
                f"{signal.keyword} is tempting. One line first.",
                "That tab can wait. One tiny step?",
            ],
            "video": [
                "Video later. One command now?",
                "Before play, one small commit?",
            ],
            "game": [
                "One turn here before the match?",
                "Game later. One file now?",
            ],
            "chat": [
                "Reply after one small step?",
                "One task first, then messages.",
            ],
        }
        choices = by_category.get(signal.category, ["Tiny detour. Back to one step?"])
        return self.rng.choice(choices)


def _clean(text: str) -> str:
    first_line = text.strip().strip("\"'").splitlines()[0] if text.strip() else ""
    return " ".join(first_line.split())[:80]

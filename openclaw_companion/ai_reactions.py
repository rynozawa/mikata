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
worker_busy={worker_busy}
recent_activity={recent_activity}

Write exactly ONE short Japanese message.
Rules:
- 55 characters max.
- Friendly coworker tone.
- Playful sarcasm is OK. Example energy:
  "僕は作業中なのに、君はのんきなもんだね"
  "君の仕事、ネットサーフィン担当だっけ"
- Do not shame, threaten, or guilt-trip.
- Do not mention monitoring or surveillance.
- Nudge the user back to one tiny next action."""


FOCUS_COACH_PROMPT = """You are Claw, a terminal companion worker sitting next to the user.
Infer the user's current work state from the local signals below.

focus_score={score}
keyboard_events={keyboard_events}
mouse_events={mouse_events}
idle_seconds={idle_seconds}
terminal_active={terminal_active}
app_switches={app_switches}
active_window={active_window}
activity_level={activity_level}
context={context}
worker_busy={worker_busy}
recent_activity={recent_activity}

Write exactly ONE short Japanese message.
Rules:
- 45 characters max.
- Sound like a close coworker/friend, not a manager.
- Choose praise, encouragement, playful pressure, or mild sarcasm as appropriate.
- Never shame, threaten, guilt-trip, or mention surveillance.
- Be specific to the state and suggest one tiny next action."""


@dataclass
class AIReactionEngine:
    cooldown_seconds: int = 150
    focus_cooldown_seconds: int = 210
    bridge: LocalAgentBridge = field(default_factory=lambda: LocalAgentBridge(timeout_seconds=20))
    rng: random.Random = field(default_factory=random.Random)
    last_reacted_at: datetime | None = None
    last_focus_reacted_at: datetime | None = None
    last_label: str = ""

    async def generate(
        self,
        signal: DistractionSignal,
        snapshot: FocusSnapshot,
        *,
        worker_busy: bool = False,
        recent_activity: str = "",
    ) -> tuple[Tone, str] | None:
        if not self._should_react(signal):
            return None

        self.last_reacted_at = datetime.now()
        self.last_label = signal.label

        if signal.demo_fast:
            return Tone.TEASE, self._fallback(signal)

        generated = await self._generate_with_local_agent(
            signal,
            snapshot,
            worker_busy=worker_busy,
            recent_activity=recent_activity,
        )
        if generated:
            return Tone.TEASE, generated
        return Tone.TEASE, self._fallback(signal)

    async def generate_focus(
        self,
        snapshot: FocusSnapshot,
        *,
        worker_busy: bool = False,
        recent_activity: str = "",
    ) -> tuple[Tone, str] | None:
        if not self._should_generate_focus(snapshot):
            return None
        self.last_focus_reacted_at = datetime.now()
        prompt = FOCUS_COACH_PROMPT.format(
            score=snapshot.score,
            keyboard_events=snapshot.keyboard_events,
            mouse_events=snapshot.mouse_events,
            idle_seconds=f"{snapshot.idle_seconds:.0f}",
            terminal_active=snapshot.terminal_active,
            app_switches=snapshot.app_switches,
            active_window=snapshot.active_window[:120],
            activity_level=snapshot.activity_level,
            context=snapshot.context,
            worker_busy=worker_busy,
            recent_activity=recent_activity,
        )
        output = await self.bridge.ask(prompt)
        if not output or output.startswith("Cannot find local agent command"):
            return None
        return self._tone_for_snapshot(snapshot), _clean(output)

    def _should_react(self, signal: DistractionSignal) -> bool:
        if signal.demo_fast:
            return True
        now = datetime.now()
        if self.last_reacted_at is None:
            return True
        if now - self.last_reacted_at >= timedelta(seconds=self.cooldown_seconds):
            return True
        return signal.label != self.last_label and self.rng.random() < 0.18

    def _should_generate_focus(self, snapshot: FocusSnapshot) -> bool:
        if snapshot.context == "distraction":
            return False
        if snapshot.activity_level not in {"stalled", "quiet"} and snapshot.app_switches < 8:
            return False
        now = datetime.now()
        if self.last_focus_reacted_at is None:
            return True
        return now - self.last_focus_reacted_at >= timedelta(seconds=self.focus_cooldown_seconds)

    @staticmethod
    def _tone_for_snapshot(snapshot: FocusSnapshot) -> Tone:
        if snapshot.activity_level == "stalled" or snapshot.score <= 35:
            return Tone.ENCOURAGE
        if snapshot.app_switches >= 8:
            return Tone.TEASE
        return Tone.NEUTRAL

    async def _generate_with_local_agent(
        self,
        signal: DistractionSignal,
        snapshot: FocusSnapshot,
        *,
        worker_busy: bool,
        recent_activity: str,
    ) -> str | None:
        prompt = REACTION_PROMPT.format(
            category=signal.category,
            keyword=signal.keyword,
            window_title=signal.window_title[:120],
            score=snapshot.score,
            idle_seconds=f"{snapshot.idle_seconds:.0f}",
            app_switches=snapshot.app_switches,
            worker_busy=worker_busy,
            recent_activity=recent_activity,
        )
        output = await self.bridge.ask(prompt)
        if not output or output.startswith("Cannot find local agent command"):
            return None
        return _clean(output)

    def _fallback(self, signal: DistractionSignal) -> str:
        by_category = {
            "social": [
                "僕は作業中なのに、君はのんきなもんだね。",
                "君の仕事、ネットサーフィン担当だっけ。",
                "そのタイムライン、納期を倒してくれる？",
            ],
            "video": [
                "YouTubeは逃げない。今は一手だけ戻ろう。",
                "僕が働いてる横で優雅だね。戻ろうか。",
                "再生前に、こっちを一コマンドだけ。",
            ],
            "game": [
                "試合前に、こっちを一ターン進めよ。",
                "ゲームは後で勝とう。今は一ファイル。",
            ],
            "chat": [
                "返信の前に、一手だけ進める？",
                "会話も大事。先に作業を一口だけ。",
            ],
        }
        choices = by_category.get(signal.category, ["寄り道っぽい。次の一手に戻ろう。"])
        return self.rng.choice(choices)


def _clean(text: str) -> str:
    first_line = text.strip().strip("\"'").splitlines()[0] if text.strip() else ""
    return " ".join(first_line.split())[:80]

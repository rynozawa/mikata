from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .models import FocusSnapshot, Tone


KAOMOJI_BY_MOOD = {
    "flow": "o(^_^)o",
    "working": "(>_<)/",
    "watching": "(-_-)",
    "tease": "(=_=)",
    "stalled": "(-_-;)",
    "done": "v(^_^)v",
    "error": "(_ _;)",
}

ASCII_MESSAGE_BY_MOOD = {
    "flow": "Nice flow. I will stay quiet.",
    "working": "Worker is moving. I am watching.",
    "watching": "I am here. One small step.",
    "tease": "I am working. Are you surfing?",
    "stalled": "Stuck? Name the next tiny step.",
    "done": "Done. That step became real.",
    "error": "Blocked. Check the worker log.",
}


@dataclass
class KaomojiStatus:
    path: Path = Path("docs/terminal-kaomoji.txt")
    mood: str = "watching"
    message: str = ASCII_MESSAGE_BY_MOOD["watching"]

    def update(
        self,
        *,
        mood: str | None = None,
        message: str | None = None,
        snapshot: FocusSnapshot | None = None,
        busy: bool = False,
    ) -> None:
        if mood is not None:
            self.mood = mood
        elif snapshot is not None:
            self.mood = self._mood_from_snapshot(snapshot, busy)

        if message is not None:
            self.message = self._ascii_message(self.mood, message)
        elif mood is not None or snapshot is not None:
            self.message = ASCII_MESSAGE_BY_MOOD.get(self.mood, ASCII_MESSAGE_BY_MOOD["watching"])

        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(self._render(), encoding="ascii", errors="replace")

    def _render(self) -> str:
        face = KAOMOJI_BY_MOOD.get(self.mood, KAOMOJI_BY_MOOD["watching"])
        return f"{face}\n{self.message}\n"

    @staticmethod
    def _mood_from_snapshot(snapshot: FocusSnapshot, busy: bool) -> str:
        if snapshot.context == "distraction":
            return "tease"
        if snapshot.activity_level == "stalled" or snapshot.idle_seconds >= 180:
            return "stalled"
        if busy:
            return "working"
        if snapshot.context in {"terminal", "coding"} and snapshot.activity_level in {"typing", "active"}:
            return "flow"
        return "watching"

    @staticmethod
    def _ascii_message(mood: str, message: str) -> str:
        if message.isascii():
            return message[:72]
        return ASCII_MESSAGE_BY_MOOD.get(mood, ASCII_MESSAGE_BY_MOOD["watching"])


def mood_from_tone(tone: Tone) -> str:
    if tone == Tone.PRAISE:
        return "flow"
    if tone == Tone.TEASE:
        return "tease"
    if tone == Tone.ENCOURAGE:
        return "stalled"
    return "watching"

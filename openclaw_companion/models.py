from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class Tone(str, Enum):
    PRAISE = "praise"
    NEUTRAL = "neutral"
    TEASE = "tease"
    ENCOURAGE = "encourage"


@dataclass(slots=True)
class FocusSnapshot:
    score: int
    keyboard_events: int
    idle_seconds: float
    terminal_active: bool
    app_switches: int
    active_window: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass(slots=True)
class CompanionMessage:
    speaker: str
    text: str
    tone: Tone = Tone.NEUTRAL
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def line(self) -> str:
        clock = self.timestamp.strftime("%H:%M:%S")
        return f"[dim]{clock}[/dim] [{self.tone.value}]{self.speaker}[/] {self.text}"

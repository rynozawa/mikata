from __future__ import annotations

import json
from collections import deque
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path

from .distraction import detect_distraction
from .models import FocusSnapshot


@dataclass
class ActivityJournal:
    path: Path = Path("logs/activity.jsonl")
    recent: deque[FocusSnapshot] = field(default_factory=lambda: deque(maxlen=90))
    distraction_ticks: int = 0

    def record(self, snapshot: FocusSnapshot) -> None:
        self.recent.append(snapshot)
        self.distraction_ticks = self.distraction_ticks + 1 if snapshot.context == "distraction" else 0
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = asdict(snapshot)
        payload["timestamp"] = snapshot.timestamp.isoformat()
        with self.path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(payload, ensure_ascii=False) + "\n")

    def summary(self) -> str:
        if not self.recent:
            return "no activity yet"
        total = len(self.recent)
        contexts: dict[str, int] = {}
        active = 0
        for snapshot in self.recent:
            contexts[snapshot.context] = contexts.get(snapshot.context, 0) + 1
            if snapshot.activity_level in {"typing", "active"}:
                active += 1
        last = self.recent[-1]
        signal = detect_distraction(last.active_window)
        distraction = signal.label if signal else "none"
        context_summary = ", ".join(f"{key}:{value}" for key, value in sorted(contexts.items()))
        return (
            f"samples={total}; active_samples={active}; contexts={context_summary}; "
            f"last_context={last.context}; last_activity={last.activity_level}; "
            f"last_window={last.active_window[:80]}; current_distraction={distraction}; "
            f"consecutive_distraction_ticks={self.distraction_ticks}"
        )

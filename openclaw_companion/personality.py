from __future__ import annotations

import random
from dataclasses import dataclass, field

from .models import FocusSnapshot, Tone


@dataclass
class CompanionPersonality:
    name: str = "Claw"
    rng: random.Random = field(default_factory=random.Random)
    last_band: str = "unknown"

    def greet(self) -> tuple[Tone, str]:
        return Tone.NEUTRAL, "いるよ。今日は横で一緒に進めよう。まず一手だけ切ろう。"

    def task_started(self, task: str) -> tuple[Tone, str]:
        return Tone.NEUTRAL, f"了解。`{task}` を見に行く。進み具合はここに流すね。"

    def task_done(self) -> tuple[Tone, str]:
        return Tone.PRAISE, "一区切り。今の一歩、ちゃんと前に進んでる。"

    def task_failed(self) -> tuple[Tone, str]:
        return Tone.ENCOURAGE, "詰まったっぽい。ログを一緒に読めばほどけるやつ。"

    def react_to_focus(self, snapshot: FocusSnapshot) -> tuple[Tone, str] | None:
        band = self._band(snapshot.score, snapshot.idle_seconds)
        if band == self.last_band and self.rng.random() > 0.35:
            return None

        self.last_band = band
        if band == "flow":
            return Tone.PRAISE, self.rng.choice(
                [
                    "いい感じ、そのまま行こう。",
                    "今の触り方、集中に入ってる。強い。",
                    "手が止まってない。ここは流れに乗ろう。",
                ]
            )
        if band == "stalled":
            return Tone.ENCOURAGE, self.rng.choice(
                [
                    "5分近く止まってる。詰まった場所だけ言葉にしてみる？",
                    "一回、次の最小ステップに割ろう。",
                    "止まるのは普通。ここから小さく再起動しよ。",
                ]
            )
        if band == "scattered":
            return Tone.TEASE, self.rng.choice(
                [
                    "……さっきから窓が忙しいね。主役のターミナルに戻る？",
                    "画面移動が速い。検索か、寄り道か、どっちだろう。",
                    "今ちょっと散ってる。10分だけ一緒に戻ろう。",
                ]
            )
        return Tone.NEUTRAL, self.rng.choice(
            [
                "ここにいるよ。次の一手を一緒に決めよう。",
                "ペースは悪くない。焦らず積もう。",
                "作業台は温まってる。続きからいける。",
            ]
        )

    @staticmethod
    def _band(score: int, idle_seconds: float) -> str:
        if idle_seconds >= 240:
            return "stalled"
        if score >= 78:
            return "flow"
        if score <= 35:
            return "scattered"
        return "steady"

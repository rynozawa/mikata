from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from .models import FocusSnapshot, Tone


@dataclass
class CompanionPersonality:
    name: str = "Claw"
    rng: random.Random = field(default_factory=random.Random)
    last_band: str = "unknown"
    last_reacted_at: datetime | None = None
    min_reaction_gap: timedelta = timedelta(seconds=75)

    def greet(self) -> tuple[Tone, str]:
        return Tone.NEUTRAL, "いるよ。今日は横で進めよう。必要な時だけ声かけるね。"

    def task_started(self, task: str) -> tuple[Tone, str]:
        return Tone.NEUTRAL, f"了解。`{task}` はWorkerに渡した。こっちは見守るね。"

    def task_working(self) -> tuple[Tone, str]:
        return Tone.NEUTRAL, "作業中... 詳細はWorker欄に流してる。"

    def task_done(self) -> tuple[Tone, str]:
        return Tone.PRAISE, "完了。今の一手、ちゃんと形になった。"

    def task_failed(self) -> tuple[Tone, str]:
        return Tone.ENCOURAGE, "詰まったっぽい。Worker欄の最後のログから一緒にほどこう。"

    def react_to_focus(self, snapshot: FocusSnapshot) -> tuple[Tone, str] | None:
        band = self._band(snapshot)
        now = datetime.now()
        changed_band = band != self.last_band
        if self.last_reacted_at and now - self.last_reacted_at < self.min_reaction_gap and not changed_band:
            return None
        if not changed_band and self.rng.random() > 0.22:
            return None

        self.last_band = band
        self.last_reacted_at = now
        return self._message_for_band(band, snapshot)

    def _message_for_band(self, band: str, snapshot: FocusSnapshot) -> tuple[Tone, str]:
        if band == "flow":
            return Tone.PRAISE, self.rng.choice(
                [
                    "いい集中。今は話しかけすぎないでおく。",
                    "手が動いてる。ここはそのまま押そう。",
                    "流れに入ってるね。次の区切りまで行こう。",
                ]
            )
        if band == "building":
            return Tone.PRAISE, self.rng.choice(
                [
                    "コード側にいるね。小さく作ってすぐ確かめよう。",
                    "今の姿勢いい。まず動く形まで持っていこう。",
                    "作業台に戻れてる。ここから一段積もう。",
                ]
            )
        if band == "reading":
            return Tone.NEUTRAL, self.rng.choice(
                [
                    "読んでる時間っぽい。次にメモを一行だけ残そう。",
                    "情報集め中だね。迷子になる前に仮説を置こう。",
                    "調査ならOK。あとで実装に戻る目印だけ作ろう。",
                ]
            )
        if band == "stalled":
            return Tone.ENCOURAGE, self.rng.choice(
                [
                    "止まってる。原因を一語で置くなら何だろう。",
                    "詰まりなら、次の最小手だけ一緒に切ろう。",
                    "いったん深呼吸。ファイル名だけ決めるところからでいい。",
                ]
            )
        if band == "distraction":
            return Tone.TEASE, self.rng.choice(
                [
                    "その寄り道、顔に出てる。戻るなら今が軽い。",
                    "別窓が主役になりかけてる。ターミナルに一票。",
                    "誘惑が来たね。10分だけこっちに賭けよう。",
                ]
            )
        if band == "scattered":
            return Tone.TEASE, self.rng.choice(
                [
                    "窓移動が多いね。探し物か、逃避か、どっちだろう。",
                    "少し散ってる。タスク名を一回だけ読み直そう。",
                    "画面が忙しい。次に触る場所を一つに絞ろう。",
                ]
            )
        return Tone.NEUTRAL, self.rng.choice(
            [
                "ペースは悪くない。静かに横で見てる。",
                "必要なら呼んで。今は一手ずつで十分。",
                "ここにいるよ。急がず、でも止めずにいこう。",
            ]
        )

    @staticmethod
    def _band(snapshot: FocusSnapshot) -> str:
        if snapshot.context == "distraction":
            return "distraction"
        if snapshot.idle_seconds >= 180 or snapshot.activity_level == "stalled":
            return "stalled"
        if snapshot.app_switches >= 7:
            return "scattered"
        if snapshot.context in {"terminal", "coding"} and snapshot.activity_level in {"typing", "active"}:
            return "flow" if snapshot.score >= 76 else "building"
        if snapshot.context in {"reading", "browser"}:
            return "reading"
        if snapshot.score <= 35:
            return "scattered"
        return "steady"

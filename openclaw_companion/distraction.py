from __future__ import annotations

import re
from dataclasses import dataclass


DISTRACTION_KEYWORDS: dict[str, tuple[str, ...]] = {
    "social": (
        "twitter",
        "x.com",
        "tweetdeck",
        "instagram",
        "tiktok",
        "threads",
        "facebook",
    ),
    "video": (
        "youtube",
        "netflix",
        "prime video",
        "twitch",
        "niconico",
        "ニコニコ",
    ),
    "game": (
        "steam",
        "epic games",
        "valorant",
        "minecraft",
        "roblox",
        "league of legends",
        "genshin",
        "原神",
        "game",
    ),
    "chat": (
        "discord",
        "slack",
    ),
    "forum": (
        "reddit",
        "5ch",
        "qiita trend",
    ),
}


@dataclass(frozen=True, slots=True)
class DistractionSignal:
    category: str
    keyword: str
    window_title: str

    @property
    def label(self) -> str:
        return f"{self.category}:{self.keyword}"


def detect_distraction(window_title: str) -> DistractionSignal | None:
    normalized = window_title.casefold()
    if re.search(r"(^|[\s/|:-])x($|[\s/|:-])", normalized):
        return DistractionSignal("social", "x", window_title)
    for category, keywords in DISTRACTION_KEYWORDS.items():
        for keyword in keywords:
            if keyword.casefold() in normalized:
                return DistractionSignal(category, keyword, window_title)
    return None

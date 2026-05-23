from __future__ import annotations

import json
import os
import tempfile
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

try:
    import winsound
except Exception:  # pragma: no cover - non-Windows fallback
    winsound = None


@dataclass
class VoicevoxSpeaker:
    base_url: str = field(default_factory=lambda: os.getenv("VOICEVOX_URL", "http://127.0.0.1:50021"))
    speaker_id: int = field(default_factory=lambda: int(os.getenv("VOICEVOX_SPEAKER", "3")))
    cooldown_seconds: int = field(default_factory=lambda: int(os.getenv("VOICEVOX_COOLDOWN", "120")))
    enabled: bool = field(default_factory=lambda: os.getenv("VOICEVOX_ENABLED", "1") != "0")
    last_spoken_at: float = 0.0

    def is_available(self) -> bool:
        if not self.enabled:
            return False
        try:
            with urllib.request.urlopen(f"{self.base_url}/version", timeout=1.5) as response:
                return response.status == 200
        except OSError:
            return False

    def speak(self, text: str, *, force: bool = False) -> bool:
        if not self.enabled:
            return False
        now = time.monotonic()
        if now - self.last_spoken_at < self.cooldown_seconds:
            return False
        cleaned = self._clean_text(text)
        if not cleaned:
            return False
        try:
            query = self._audio_query(cleaned)
            wav = self._synthesis(query)
            self._play_wav(wav)
        except OSError:
            return False
        self.last_spoken_at = now
        return True

    def _audio_query(self, text: str) -> bytes:
        params = urllib.parse.urlencode({"text": text, "speaker": self.speaker_id})
        request = urllib.request.Request(
            f"{self.base_url}/audio_query?{params}",
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=5) as response:
            return response.read()

    def _synthesis(self, query: bytes) -> bytes:
        params = urllib.parse.urlencode({"speaker": self.speaker_id})
        request = urllib.request.Request(
            f"{self.base_url}/synthesis?{params}",
            data=query,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=10) as response:
            return response.read()

    @staticmethod
    def _play_wav(wav: bytes) -> None:
        path = Path(tempfile.gettempdir()) / "openclaw_companion_voicevox.wav"
        path.write_bytes(wav)
        if winsound is not None:
            winsound.PlaySound(str(path), winsound.SND_FILENAME | winsound.SND_ASYNC)

    @staticmethod
    def _clean_text(text: str) -> str:
        text = text.replace("`", "").replace("[", "").replace("]", "")
        return " ".join(text.split())[:80]

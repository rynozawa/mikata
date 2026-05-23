from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field

from .models import FocusSnapshot

try:
    import psutil
except Exception:  # pragma: no cover - optional dependency
    psutil = None

try:
    import pygetwindow as gw
except Exception:  # pragma: no cover - optional dependency
    gw = None

try:
    from pynput import keyboard
except Exception:  # pragma: no cover - optional dependency
    keyboard = None


TERMINAL_HINTS = ("powershell", "cmd", "windows terminal", "terminal", "wezterm", "openclaw")


@dataclass
class FocusMonitor:
    window_history_size: int = 12
    keyboard_events: int = 0
    last_input_at: float = field(default_factory=time.monotonic)
    last_sample_at: float = field(default_factory=time.monotonic)
    window_history: deque[str] = field(default_factory=lambda: deque(maxlen=12))
    listener: object | None = None
    simulated_tick: int = 0

    def start(self) -> None:
        if keyboard is None:
            return
        self.listener = keyboard.Listener(on_press=self._on_key_press)
        self.listener.daemon = True
        self.listener.start()

    def stop(self) -> None:
        if self.listener is not None:
            self.listener.stop()

    def sample(self) -> FocusSnapshot:
        now = time.monotonic()
        elapsed = max(now - self.last_sample_at, 1.0)
        active_window = self._active_window_title()
        terminal_active = self._is_terminal_window(active_window)

        self.window_history.append(active_window)
        switches = self._count_switches()
        idle_seconds = now - self.last_input_at
        events_per_minute = self.keyboard_events / elapsed * 60.0

        score = 50
        score += min(int(events_per_minute * 1.5), 30)
        score += 15 if terminal_active else -12
        score -= min(int(idle_seconds / 10), 35)
        score -= min(switches * 5, 25)
        score = max(0, min(100, score))

        snapshot = FocusSnapshot(
            score=score,
            keyboard_events=self.keyboard_events,
            idle_seconds=idle_seconds,
            terminal_active=terminal_active,
            app_switches=switches,
            active_window=active_window,
        )
        self.keyboard_events = 0
        self.last_sample_at = now
        return snapshot

    def _on_key_press(self, _key: object) -> None:
        self.keyboard_events += 1
        self.last_input_at = time.monotonic()

    def _active_window_title(self) -> str:
        if gw is not None:
            try:
                window = gw.getActiveWindow()
                if window and window.title:
                    return window.title.lower()
            except Exception:
                pass

        process_name = self._foreground_fallback_process()
        if process_name:
            return process_name.lower()

        self.simulated_tick += 1
        if self.simulated_tick % 9 == 0:
            return "browser - social tab"
        return "windows terminal - openclaw companion"

    @staticmethod
    def _foreground_fallback_process() -> str:
        if psutil is None:
            return ""
        try:
            current = psutil.Process()
            return current.name()
        except Exception:
            return ""

    @staticmethod
    def _is_terminal_window(title: str) -> bool:
        return any(hint in title for hint in TERMINAL_HINTS)

    def _count_switches(self) -> int:
        if len(self.window_history) < 2:
            return 0
        return sum(
            previous != current
            for previous, current in zip(self.window_history, list(self.window_history)[1:])
        )

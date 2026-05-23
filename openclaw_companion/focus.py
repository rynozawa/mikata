from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field

from .distraction import detect_distraction
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
    from pynput import keyboard, mouse
except Exception:  # pragma: no cover - optional dependency
    keyboard = None
    mouse = None


TERMINAL_HINTS = ("powershell", "cmd", "windows terminal", "terminal", "wezterm", "openclaw")
CODING_HINTS = ("code", "vscode", "visual studio", "pycharm", "cursor", "github", "git")
DOC_HINTS = ("pdf", "word", "notion", "obsidian", "readme", "docs")


@dataclass
class FocusMonitor:
    window_history_size: int = 20
    keyboard_events: int = 0
    mouse_events: int = 0
    last_input_at: float = field(default_factory=time.monotonic)
    last_sample_at: float = field(default_factory=time.monotonic)
    window_history: deque[str] = field(default_factory=lambda: deque(maxlen=20))
    keyboard_listener: object | None = None
    mouse_listener: object | None = None
    simulated_tick: int = 0

    def start(self) -> None:
        if keyboard is not None:
            self.keyboard_listener = keyboard.Listener(on_press=self._on_key_press)
            self.keyboard_listener.daemon = True
            self.keyboard_listener.start()
        if mouse is not None:
            self.mouse_listener = mouse.Listener(
                on_move=self._on_mouse_event,
                on_click=self._on_mouse_event,
                on_scroll=self._on_mouse_event,
            )
            self.mouse_listener.daemon = True
            self.mouse_listener.start()

    def stop(self) -> None:
        for listener in (self.keyboard_listener, self.mouse_listener):
            if listener is not None:
                listener.stop()

    def sample(self) -> FocusSnapshot:
        now = time.monotonic()
        elapsed = max(now - self.last_sample_at, 1.0)
        active_window = self._active_window_title()
        terminal_active = self._is_terminal_window(active_window)

        self.window_history.append(active_window)
        switches = self._count_switches()
        idle_seconds = now - self.last_input_at
        keyboard_per_minute = self.keyboard_events / elapsed * 60.0
        mouse_per_minute = self.mouse_events / elapsed * 60.0
        context = self._classify_context(active_window)
        activity_level = self._activity_level(keyboard_per_minute, mouse_per_minute, idle_seconds)

        score = 48
        score += min(int(keyboard_per_minute * 1.3), 28)
        score += min(int(mouse_per_minute * 0.35), 12)
        score += 16 if terminal_active else 0
        score += 10 if context in {"coding", "terminal"} else 0
        score -= 18 if context == "distraction" else 0
        score -= min(int(idle_seconds / 12), 35)
        score -= min(switches * 4, 24)
        score = max(0, min(100, score))

        snapshot = FocusSnapshot(
            score=score,
            keyboard_events=self.keyboard_events,
            mouse_events=self.mouse_events,
            idle_seconds=idle_seconds,
            terminal_active=terminal_active,
            app_switches=switches,
            active_window=active_window,
            activity_level=activity_level,
            context=context,
        )
        self.keyboard_events = 0
        self.mouse_events = 0
        self.last_sample_at = now
        return snapshot

    def _on_key_press(self, _key: object) -> None:
        self.keyboard_events += 1
        self.last_input_at = time.monotonic()

    def _on_mouse_event(self, *_args: object) -> None:
        self.mouse_events += 1
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

    def _classify_context(self, title: str) -> str:
        if detect_distraction(title) is not None:
            return "distraction"
        if self._is_terminal_window(title):
            return "terminal"
        if any(hint in title for hint in CODING_HINTS):
            return "coding"
        if any(hint in title for hint in DOC_HINTS):
            return "reading"
        if "browser" in title or "chrome" in title or "edge" in title:
            return "browser"
        return "unknown"

    @staticmethod
    def _activity_level(keyboard_per_minute: float, mouse_per_minute: float, idle_seconds: float) -> str:
        if idle_seconds >= 180:
            return "stalled"
        if keyboard_per_minute >= 45:
            return "typing"
        if keyboard_per_minute >= 8 or mouse_per_minute >= 35:
            return "active"
        if mouse_per_minute >= 8:
            return "browsing"
        return "quiet"

    def _count_switches(self) -> int:
        if len(self.window_history) < 2:
            return 0
        return sum(
            previous != current
            for previous, current in zip(self.window_history, list(self.window_history)[1:])
        )

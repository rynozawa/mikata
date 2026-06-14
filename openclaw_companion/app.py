from __future__ import annotations

import asyncio

from rich.text import Text
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import Footer, Header, Input, Label, RichLog, Static

from .activity_journal import ActivityJournal
from .agent import AgentRunner
from .ai_reactions import AIReactionEngine
from .distraction import detect_distraction
from .focus import FocusMonitor
from .kaomoji_status import KaomojiStatus, mood_from_tone
from .models import CompanionMessage, FocusSnapshot, Tone
from .personality import CompanionPersonality
from .voicevox import VoicevoxSpeaker


class StatusPanel(Static):
    score = reactive(50)
    idle = reactive(0.0)
    active_window = reactive("unknown")
    terminal_active = reactive(False)
    switches = reactive(0)
    mouse_events = reactive(0)
    activity_level = reactive("quiet")
    context = reactive("unknown")

    def render(self) -> Text:
        color = "green" if self.score >= 75 else "yellow" if self.score >= 45 else "red"
        terminal = "yes" if self.terminal_active else "no"
        return Text.from_markup(
            "\n".join(
                [
                    "[b]Focus[/b]",
                    f"score: [{color}]{self.score:>3}[/]",
                    f"idle: {self.idle:>4.0f}s",
                    f"terminal: {terminal}",
                    f"switches: {self.switches}",
                    f"mouse: {self.mouse_events}",
                    f"activity: {self.activity_level}",
                    f"context: {self.context}",
                    "",
                    "[b]active[/b]",
                    self.active_window[:34] or "unknown",
                ]
            )
        )

    def update_from_snapshot(self, snapshot: FocusSnapshot) -> None:
        self.score = snapshot.score
        self.idle = snapshot.idle_seconds
        self.active_window = snapshot.active_window
        self.terminal_active = snapshot.terminal_active
        self.switches = snapshot.app_switches
        self.mouse_events = snapshot.mouse_events
        self.activity_level = snapshot.activity_level
        self.context = snapshot.context


class OpenClawCompanionApp(App):
    CSS = """
    Screen {
        layout: vertical;
    }

    #body {
        height: 1fr;
    }

    #main {
        width: 1fr;
    }

    .log-panel {
        height: 1fr;
        border: solid $accent;
    }

    #side {
        width: 42;
        border: solid $primary;
        padding: 1;
    }

    #prompt {
        dock: bottom;
        height: 3;
        border: solid $accent;
    }

    RichLog {
        padding: 1;
    }

    Label {
        height: 1;
    }
    """

    BINDINGS = [
        ("ctrl+c", "quit", "Quit"),
        ("q", "quit", "Quit"),
        ("escape", "quit", "Quit"),
        ("ctrl+h", "narrow_side", "Side -"),
        ("ctrl+l", "widen_side", "Side +"),
        ("ctrl+j", "grow_worker", "Worker +"),
        ("ctrl+k", "grow_companion", "Companion +"),
        ("f5", "narrow_side", "Side -"),
        ("f6", "widen_side", "Side +"),
        ("f7", "grow_worker", "Worker +"),
        ("f8", "grow_companion", "Companion +"),
        ("alt+left", "narrow_side", "Side -"),
        ("alt+right", "widen_side", "Side +"),
        ("alt+down", "grow_worker", "Worker +"),
        ("alt+up", "grow_companion", "Companion +"),
        ("ctrl+0", "reset_layout", "Reset layout"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.focus_monitor = FocusMonitor()
        self.personality = CompanionPersonality()
        self.ai_reactions = AIReactionEngine()
        self.activity_journal = ActivityJournal()
        self.kaomoji_status = KaomojiStatus()
        self.voicevox = VoicevoxSpeaker()
        self.agent = AgentRunner()
        self.conversation_log: RichLog | None = None
        self.worker_log: RichLog | None = None
        self.status: StatusPanel | None = None
        self.companion_panel: Vertical | None = None
        self.worker_panel: Vertical | None = None
        self.side_panel: Vertical | None = None
        self.busy = False
        self.side_width = 42
        self.companion_percent = 50
        self.layout_version = 0

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="body"):
            with Vertical(id="main"):
                with Vertical(id="companion-panel", classes="log-panel"):
                    yield Label("Companion")
                    yield RichLog(id="conversation", highlight=True, markup=True)
                with Vertical(id="worker-panel", classes="log-panel"):
                    yield Label("Worker")
                    yield RichLog(id="worker", highlight=True, markup=True)
            with Vertical(id="side"):
                yield StatusPanel(id="status")
        yield Input(placeholder="Task: 例 `READMEを作って` / `!pytest`", id="prompt")
        yield Footer()

    def on_mount(self) -> None:
        self.conversation_log = self.query_one("#conversation", RichLog)
        self.worker_log = self.query_one("#worker", RichLog)
        self.status = self.query_one("#status", StatusPanel)
        self.companion_panel = self.query_one("#companion-panel", Vertical)
        self.worker_panel = self.query_one("#worker-panel", Vertical)
        self.side_panel = self.query_one("#side", Vertical)
        self.apply_layout_sizes(announce=False)
        self.focus_monitor.start()
        tone, text = self.personality.greet()
        self.say(tone, text)
        self.kaomoji_status.update(mood="watching", message=text, busy=self.busy)
        if self.voicevox.is_available():
            self.write_worker("[green]VOICEVOX connected[/green]")
        else:
            self.write_worker("[yellow]VOICEVOX not found. Start VOICEVOX Engine on 127.0.0.1:50021 to enable speech.[/yellow]")
        self.set_interval(3.0, self.tick_focus)

    def on_unmount(self) -> None:
        self.focus_monitor.stop()

    async def on_key(self, event) -> None:
        key_actions = {
            "f5": self.action_narrow_side,
            "f6": self.action_widen_side,
            "f7": self.action_grow_worker,
            "f8": self.action_grow_companion,
            "alt+left": self.action_narrow_side,
            "alt+right": self.action_widen_side,
            "alt+down": self.action_grow_worker,
            "alt+up": self.action_grow_companion,
        }
        action = key_actions.get(event.key)
        if action is None:
            return
        event.prevent_default()
        event.stop()
        action()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        task = event.value.strip()
        event.input.value = ""
        if not task:
            return
        if task.lower() in {"q", "quit", "exit", ":q", "/quit"}:
            self.exit()
            return
        if self.busy:
            self.say(Tone.ENCOURAGE, "今Workerが動いてる。終わったら次を受けるね。")
            return
        self.write_user(task)
        self.run_worker(self.run_task(task), exclusive=False)

    async def run_task(self, task: str) -> None:
        self.busy = True
        self.kaomoji_status.update(mood="working", message="Workerが作業中。", busy=self.busy)
        tone, text = self.personality.task_started(task)
        self.say(tone, text)
        tone, text = self.personality.task_working()
        self.say(tone, text)
        self.write_worker(f"[b]task[/b] {task}")
        try:
            async for line in self.agent.run(task):
                self.write_worker(line)
            tone, text = self.personality.task_done()
            self.say(tone, text)
            self.kaomoji_status.update(mood="done", message=text, busy=self.busy)
        except Exception as exc:
            tone, text = self.personality.task_failed()
            self.say(tone, f"{text} ({exc})")
            self.write_worker(f"[red]error[/red] {exc}")
            self.kaomoji_status.update(mood="error", message=text, busy=self.busy)
        finally:
            self.busy = False

    def tick_focus(self) -> None:
        snapshot = self.focus_monitor.sample()
        self.activity_journal.record(snapshot)
        self.kaomoji_status.update(snapshot=snapshot, busy=self.busy)
        if self.status is not None:
            self.status.update_from_snapshot(snapshot)
        distraction = detect_distraction(snapshot.active_window)
        if distraction is not None:
            self.run_worker(self.react_to_distraction(distraction, snapshot), exclusive=False)
            return
        reaction = self.personality.react_to_focus(snapshot)
        if reaction is not None:
            tone, text = reaction
            self.say(tone, text)
        if not self.busy:
            self.run_worker(self.react_to_focus_with_worker(snapshot), exclusive=False)

    async def react_to_distraction(self, distraction, snapshot: FocusSnapshot) -> None:
        reaction = await self.ai_reactions.generate(
            distraction,
            snapshot,
            worker_busy=self.busy,
            recent_activity=self.activity_journal.summary(),
        )
        if reaction is None:
            return
        tone, text = reaction
        self.say(tone, text)
        self.speak_warning(text)

    async def react_to_focus_with_worker(self, snapshot: FocusSnapshot) -> None:
        reaction = await self.ai_reactions.generate_focus(
            snapshot,
            worker_busy=self.busy,
            recent_activity=self.activity_journal.summary(),
        )
        if reaction is None:
            return
        tone, text = reaction
        self.say(tone, text)
        if tone in {Tone.TEASE, Tone.ENCOURAGE}:
            self.speak_warning(text)

    def write_user(self, text: str) -> None:
        if self.conversation_log is not None:
            self.conversation_log.write(f"[dim]you[/dim] {text}")

    def write_worker(self, text: str) -> None:
        if self.worker_log is not None:
            self.worker_log.write(f"[dim]worker[/dim] {text}")

    def say(self, tone: Tone, text: str) -> None:
        if self.conversation_log is None:
            return
        message = CompanionMessage("Claw", text, tone)
        self.conversation_log.write(message.line)
        self.kaomoji_status.update(mood=mood_from_tone(tone), message=text, busy=self.busy)

    def speak_warning(self, text: str, *, force: bool = False) -> None:
        self.run_worker(self.speak_warning_async(text, force=force), exclusive=False)

    async def speak_warning_async(self, text: str, *, force: bool = False) -> None:
        await asyncio.to_thread(self.voicevox.speak, text, force=force)

    def action_narrow_side(self) -> None:
        self.side_width = max(24, self.side_width - 8)
        self.apply_layout_sizes()

    def action_widen_side(self) -> None:
        self.side_width = min(80, self.side_width + 8)
        self.apply_layout_sizes()

    def action_grow_worker(self) -> None:
        self.companion_percent = max(25, self.companion_percent - 5)
        self.apply_layout_sizes()

    def action_grow_companion(self) -> None:
        self.companion_percent = min(75, self.companion_percent + 5)
        self.apply_layout_sizes()

    def action_reset_layout(self) -> None:
        self.side_width = 42
        self.companion_percent = 50
        self.apply_layout_sizes()

    def apply_layout_sizes(self, announce: bool = True) -> None:
        self.layout_version += 1
        if self.side_panel is not None:
            self.side_panel.styles.width = self.side_width
            self.side_panel.styles.min_width = self.side_width
            self.side_panel.styles.max_width = self.side_width
            self.side_panel.refresh(layout=True)
        if self.companion_panel is not None:
            self.companion_panel.styles.height = f"{self.companion_percent}fr"
            self.companion_panel.refresh(layout=True)
        if self.worker_panel is not None:
            self.worker_panel.styles.height = f"{100 - self.companion_percent}fr"
            self.worker_panel.refresh(layout=True)
        self.refresh(layout=True)
        if announce:
            self.say(
                Tone.NEUTRAL,
                f"layout #{self.layout_version}: Focus {self.side_width}, Companion {self.companion_percent}%",
            )


def main() -> None:
    app = OpenClawCompanionApp()
    app.run()


if __name__ == "__main__":
    main()

from __future__ import annotations

from rich.text import Text
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import Footer, Header, Input, Label, RichLog, Static

from .agent import AgentRunner
from .ai_reactions import AIReactionEngine
from .distraction import detect_distraction
from .focus import FocusMonitor
from .models import CompanionMessage, FocusSnapshot, Tone
from .personality import CompanionPersonality


class StatusPanel(Static):
    score = reactive(50)
    idle = reactive(0.0)
    active_window = reactive("unknown")
    terminal_active = reactive(False)
    switches = reactive(0)

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


class OpenClawCompanionApp(App):
    CSS = """
    Screen {
        layout: vertical;
    }

    #body {
        height: 1fr;
    }

    #log-area {
        width: 1fr;
        border: solid $accent;
    }

    #side {
        width: 38;
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

    BINDINGS = [("ctrl+c", "quit", "Quit")]

    def __init__(self) -> None:
        super().__init__()
        self.focus_monitor = FocusMonitor()
        self.personality = CompanionPersonality()
        self.ai_reactions = AIReactionEngine()
        self.agent = AgentRunner()
        self.conversation_log: RichLog | None = None
        self.status: StatusPanel | None = None
        self.busy = False

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="body"):
            with Vertical(id="log-area"):
                yield Label("Conversation")
                yield RichLog(id="conversation", highlight=True, markup=True)
            with Vertical(id="side"):
                yield StatusPanel(id="status")
        yield Input(placeholder="Task: 例 `READMEを作って` / `!pytest`", id="prompt")
        yield Footer()

    def on_mount(self) -> None:
        self.conversation_log = self.query_one("#conversation", RichLog)
        self.status = self.query_one("#status", StatusPanel)
        self.focus_monitor.start()
        tone, text = self.personality.greet()
        self.say(tone, text)
        self.set_interval(4.0, self.tick_focus)

    def on_unmount(self) -> None:
        self.focus_monitor.stop()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        task = event.value.strip()
        event.input.value = ""
        if not task or self.busy:
            if self.busy:
                self.say(Tone.ENCOURAGE, "今のタスクを走らせてる。終わったら次に行こう。")
            return
        self.write_user(task)
        self.run_worker(self.run_task(task), exclusive=False)

    async def run_task(self, task: str) -> None:
        self.busy = True
        tone, text = self.personality.task_started(task)
        self.say(tone, text)
        try:
            async for line in self.agent.run(task):
                self.say(Tone.NEUTRAL, line)
            tone, text = self.personality.task_done()
            self.say(tone, text)
        except Exception as exc:
            tone, text = self.personality.task_failed()
            self.say(tone, f"{text} ({exc})")
        finally:
            self.busy = False

    def tick_focus(self) -> None:
        snapshot = self.focus_monitor.sample()
        if self.status is not None:
            self.status.update_from_snapshot(snapshot)
        reaction = self.personality.react_to_focus(snapshot)
        if reaction is not None:
            tone, text = reaction
            self.say(tone, text)
        distraction = detect_distraction(snapshot.active_window)
        if distraction is not None:
            self.run_worker(self.react_to_distraction(distraction, snapshot), exclusive=False)

    async def react_to_distraction(self, distraction, snapshot: FocusSnapshot) -> None:
        reaction = await self.ai_reactions.generate(distraction, snapshot)
        if reaction is None:
            return
        tone, text = reaction
        self.say(tone, text)

    def write_user(self, text: str) -> None:
        if self.conversation_log is not None:
            self.conversation_log.write(f"[dim]you[/dim] {text}")

    def say(self, tone: Tone, text: str) -> None:
        if self.conversation_log is None:
            return
        message = CompanionMessage("Claw", text, tone)
        self.conversation_log.write(message.line)


def main() -> None:
    app = OpenClawCompanionApp()
    app.run()


if __name__ == "__main__":
    main()

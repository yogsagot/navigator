"""Shared test helpers.

The application takes over a real tty, which a test cannot provide, so tests
run it against :class:`FakeTerminal` and post events directly with
``Application.post_event``.
"""

from __future__ import annotations

import asyncio

import pytest

from navkit.application import Application
from navkit.events import Event
from navkit.screen import ScreenBuffer
from navkit.style import Style
from navkit.widget import Widget


class FakeTerminal:
    """A terminal that records what would have been written.

    ``frames`` holds one entry per flush, so its length is the number of
    repaints the application actually performed.
    """

    def __init__(self, width: int = 40, height: int = 10):
        self.size = (width, height)
        self.is_tty = False
        self.input_fd = -1
        self.frames: list[str] = []
        self.started = False
        self.stopped = False
        self.title: str | None = None
        self._pending: list[str] = []

    def start(self) -> None:
        self.started = True

    def stop(self) -> None:
        self.stopped = True

    def set_title(self, title: str) -> None:
        self.title = title

    def read(self, size: int = 0) -> bytes:
        return b""

    def write(self, text: str) -> None:
        if text:
            self._pending.append(text)

    def flush(self) -> None:
        if self._pending:
            self.frames.append("".join(self._pending))
            self._pending = []

    @property
    def painted(self) -> str:
        """Everything painted so far, as one string."""
        return "".join(self.frames)


class RecordingWidget(Widget):
    """A widget that fills its area and remembers the events it received."""

    def __init__(self, fill: str = ".", **kwargs):
        super().__init__(**kwargs)
        self.fill_char = fill
        self.keys: list[str] = []
        self.mice: list[tuple[int, int]] = []
        self.renders = 0
        self.handles = True

    def render(self, buffer: ScreenBuffer) -> None:
        self.renders += 1
        buffer.fill(self.x, self.y, self.width, self.height, self.fill_char, self.style)

    def on_key(self, event) -> bool:
        self.keys.append(event.name)
        self.invalidate()
        return self.handles

    def on_mouse(self, event) -> bool:
        self.mice.append((event.x, event.y))
        self.invalidate()
        return self.handles


def run_app(
    app: Application,
    actions=(),
    *,
    settle: float = 0.02,
    timeout: float = 5.0,
):
    """Run *app* until it exits, applying *actions* once the loop is live.

    Each action is either an :class:`~navkit.events.Event` to post or a
    callable taking the application.  The application is asked to exit after
    the last action unless it already stopped on its own.
    """

    async def drive() -> None:
        await asyncio.sleep(settle)
        for action in actions:
            if isinstance(action, Event):
                app.post_event(action)
            else:
                action(app)
            await asyncio.sleep(settle)
        if app.is_running:
            app.exit()

    async def main():
        driver = asyncio.ensure_future(drive())
        try:
            return await app.run_async()
        finally:
            driver.cancel()

    return asyncio.run(asyncio.wait_for(main(), timeout))


@pytest.fixture
def terminal() -> FakeTerminal:
    return FakeTerminal()


@pytest.fixture
def blue() -> Style:
    return Style(fg=7, bg=4)
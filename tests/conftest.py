"""Shared test helpers.

The application takes over a real tty, which a test cannot provide, so tests
run it against :class:`FakeTerminal` and post events directly with
``Application.post_event``.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from navkit.application import Application
from navkit.capabilities import FULL, TerminalInfo
from navkit.events import Event
from navkit.reactive import SCHEDULER, flush_effects
from navkit.screen import Surface
from navkit.style import Style
from navkit.widget import Widget

ROOT = Path(__file__).resolve().parent.parent


class FakeTerminal:
    """A terminal that records what would have been written.

    ``frames`` holds one entry per flush, so its length is the number of
    repaints the application actually performed.
    """

    def __init__(
        self, width: int = 40, height: int = 10, info: TerminalInfo | None = None
    ):
        # Full capability by default, so a test asserting on painted escapes
        # sees what the styles say and not what the environment running the
        # suite allows.  Pass a TerminalInfo to assert on the downgrade.
        self.info = info or FULL
        self.size = (width, height)
        self.is_tty = False
        self.input_fd = -1
        self.frames: list[str] = []
        self.started = False
        self.stopped = False
        self.title: str | None = None
        #: How many times the bell was rung.
        self.bells = 0
        #: What was copied, as ``(text, primary)``, and which reads were asked for.
        self.clipboard: list[tuple[str, bool]] = []
        self.clipboard_queries: list[bool] = []
        #: Between suspend() and resume(), and what was written raw meanwhile.
        self.suspended = False
        self.relayed: list[bytes] = []
        self._pending: list[str] = []

    def start(self) -> None:
        self.started = True

    def stop(self) -> None:
        self.stopped = True

    def suspend(self) -> None:
        self.suspended = True

    def resume(self) -> None:
        self.suspended = False

    def write_bytes(self, data: bytes) -> None:
        self.relayed.append(data)

    def set_title(self, title: str) -> None:
        self.title = title

    def bell(self) -> None:
        self.bells += 1

    def set_clipboard(self, text: str, *, primary: bool = False) -> None:
        self.clipboard.append((text, primary))

    def query_clipboard(self, *, primary: bool = False) -> None:
        self.clipboard_queries.append(primary)

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
        self.doubles: list[tuple[int, int]] = []
        self.renders = 0
        self.handles = True

    def render(self, surface: Surface) -> None:
        self.renders += 1
        # From 0, 0: the surface already covers exactly this widget.
        surface.fill(0, 0, self.width, self.height, self.fill_char, self.style)

    async def on_key(self, event) -> bool:
        self.keys.append(event.name)
        self.invalidate()
        return self.handles

    async def on_mouse_click(self, event) -> bool:
        self.mice.append((event.x, event.y))
        self.invalidate()
        return self.handles

    async def on_double_click(self, event) -> bool:
        # Separate from `mice': a double-click is delivered *as well as* the
        # press that completed it, so a test wants to see the two apart.
        self.doubles.append((event.x, event.y))
        self.invalidate()
        return self.handles


class Until:
    """A ``run_app`` action that waits until ``predicate(app)`` holds.

    For work that runs on a thread -- a file read, a search -- whose end is
    not a fixed number of steps away.  Fails the test if *timeout* passes
    first, rather than letting the next action act too soon.
    """

    def __init__(self, predicate, timeout: float = 2.0) -> None:
        self.predicate = predicate
        self.timeout = timeout


# Until everything ``spawn`` started has ended: a save, a copy, any command whose
# work goes to a thread.  Its file can be on disk while the task is still running,
# and what follows the write -- the text marked unchanged, the bell -- lands only
# once the task is done, so a fixed number of steps waits long enough only on a
# fast machine.  Not for work left waiting on a dialog, which never ends by itself.
IDLE = Until(lambda app: not app._tasks)


def run_app(
    app: Application,
    actions=(),
    *,
    settle: float = 0.02,
    timeout: float = 5.0,
):
    """Run *app* until it exits, applying *actions* once the loop is live.

    Each action is either an :class:`~navkit.events.Event` to post, an
    :class:`Until` to wait on, or a callable taking the application.  The
    application is asked to exit after the last action unless it already
    stopped on its own.
    """

    waited_out: list[Until] = []

    async def drive() -> None:
        await asyncio.sleep(settle)
        for action in actions:
            if isinstance(action, Until):
                loop = asyncio.get_running_loop()
                deadline = loop.time() + action.timeout
                while not action.predicate(app):
                    if loop.time() > deadline:
                        waited_out.append(action)
                        app.exit()
                        return
                    await asyncio.sleep(0.005)
                continue
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

    result = asyncio.run(asyncio.wait_for(main(), timeout))
    if waited_out:
        raise AssertionError(f"Until: still waiting after {waited_out[0].timeout}s")
    return result


def awaited(coro):
    """Run one awaitable to completion, for a test calling a handler directly.

    Every event handler is ``async def``, so a test that reaches past the
    event loop -- ``awaited(root.dispatch_key(KeyEvent("a")))`` -- needs a loop
    of its own.  ``asyncio.run`` rather than a pytest plugin: the project
    carries one runtime dependency and pytest alone for development, and this
    is one line.
    """
    return asyncio.run(coro)


def settle() -> None:
    """Run the effects a change has queued, as the event loop would.

    Only needed by tests that drive a widget's model directly: with no
    application running, nothing is draining the shared scheduler, so a
    deferred reaction such as rescanning a directory has not happened yet.
    """
    flush_effects()


@pytest.fixture(autouse=True)
def _english():
    """Every test speaks English with no catalogues: the language is shared."""
    from navkit import i18n

    sources = list(i18n._SOURCES)
    i18n._SOURCES.clear()
    i18n._CACHE.clear()
    i18n._PLAIN.clear()
    i18n.LOCALE.code = i18n.SOURCE
    yield
    i18n.LOCALE.code = i18n.SOURCE
    i18n._SOURCES[:] = sources
    i18n._CACHE.clear()
    i18n._PLAIN.clear()


@pytest.fixture(autouse=True)
def _quiet_scheduler():
    """Keep one test's queued effects out of the next one."""
    SCHEDULER.clear()
    yield
    SCHEDULER.clear()


@pytest.fixture(autouse=True)
def _fresh_database():
    """Every test gets an empty ``:memory:`` database: the one every model uses.

    That is what keeps one test's input history out of the next one, and every
    test off the disk -- ``main()`` is the only thing that opens a file.
    """
    from navkit.database import DATABASE
    from navml.history import HISTORY, MAX_ENTRIES

    DATABASE.open()
    # Navigator sizes the shared store from its settings; put it back.
    HISTORY.limit = MAX_ENTRIES
    yield
    DATABASE.close()
    HISTORY.limit = MAX_ENTRIES


@pytest.fixture(autouse=True)
def _default_keys():
    """Every test starts from the keys the code binds: ``keybindings.ini``'s
    overrides live on the classes, and would outlast the test that made them."""
    from navkit.commands import restore_keys

    restore_keys()
    yield
    restore_keys()


@pytest.fixture(autouse=True)
def _default_settings(monkeypatch, tmp_path):
    """Every test starts from the default settings, and none can touch ``~/.config``.

    ``SETTINGS`` is shared like ``HISTORY``, and a setup dialog's OK saves to
    ``config_path()`` -- which ``XDG_CONFIG_HOME`` here points into the test's
    own temporary directory.
    """
    from navigator import filetypes
    from navigator.settings import SETTINGS

    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    SETTINGS.reset()
    filetypes.use_masks(filetypes.CATEGORIES)  # *Highlight groups*' masks, put in force by a Shell
    yield
    SETTINGS.reset()
    filetypes.use_masks(filetypes.CATEGORIES)


@pytest.fixture(autouse=True)
def _outside_navigator(monkeypatch):
    """Run as if from a plain terminal, even when pytest is started in nav's console.

    Navigator marks every child it starts, and ``main()`` refuses to run under
    that mark.
    """
    from navkit.process import MARKER

    monkeypatch.delenv(MARKER, raising=False)


@pytest.fixture(autouse=True)
def _repository_root(monkeypatch):
    """Run every test from the repository root, whatever pytest was started in.

    The generator tests name the shipped components by relative path
    (``navml/widgets/dialog/button/button.nml``) and the import tests start a
    subprocess that has to find ``navml`` on its own, so a run started from
    ``tests/`` -- an IDE's default -- would otherwise fail them in bulk.
    """
    monkeypatch.chdir(ROOT)


@pytest.fixture
def terminal() -> FakeTerminal:
    return FakeTerminal()


@pytest.fixture
def blue() -> Style:
    return Style(fg=7, bg=4)

def mounted(widget, *, size=(80, 24), stylesheet=None):
    """*widget* as the root of a live application, laid out and mounted.

    Needed because a widget's effects belong in ``mounted()`` rather than in
    ``__init__`` -- ``remove()`` disposes a subtree's effects, so anything
    that can be taken out and put back has to declare them where they will be
    declared again.  A detached widget therefore has *no* effects running, and
    a test that builds one and asserts on its model is asserting on a model
    that was never computed.

    The application is real but its terminal is not, so nothing is painted
    until something asks.  The widget is returned, not the application; reach
    it with ``widget.application`` when a test needs one.
    """
    from navkit.application import Application

    application = Application(
        widget, terminal=FakeTerminal(width=size[0], height=size[1])
    )
    if stylesheet is not None:
        application.stylesheet = stylesheet
    settle()
    return widget

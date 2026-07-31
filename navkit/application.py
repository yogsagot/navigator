"""The application object and its event loop.

:class:`Application` is the only place in navkit that owns an asyncio loop.  It
wires the terminal's input to an event queue, dispatches events to the widget
tree, and repaints the screen once per batch of events rather than once per
event -- so a burst of keystrokes or a fast mouse drag costs a single frame.

    class Hello(Application):
        def on_key(self, event):
            if event.matches("f10", "ctrl+q"):
                self.exit()
                return True
            return False

    Hello(root=SomeWidget()).run()
"""

from __future__ import annotations

import asyncio
import contextlib
import signal
from typing import Any

from navkit.events import (
    Event,
    KeyEvent,
    MouseEvent,
    PasteEvent,
    ResizeEvent,
    WakeEvent,
)
from navkit.screen import ScreenBuffer, render_diff
from navkit.style import DEFAULT_STYLE, Style
from navkit.terminal import InputParser, Terminal
from navkit.widget import Widget

#: How long to wait before deciding a lone ``ESC`` really was the escape key
#: and not the start of a sequence the terminal is still sending.
ESCAPE_TIMEOUT = 0.05


_WAKE = WakeEvent()


class Application:
    """Owns the event loop, the terminal and the root of the widget tree."""

    def __init__(
        self,
        root: Widget | None = None,
        *,
        terminal: Terminal | None = None,
        title: str | None = None,
        background: Style = DEFAULT_STYLE,
        max_fps: int = 60,
        mouse: bool = True,
    ):
        self.terminal = terminal or Terminal(mouse=mouse)
        self.title = title
        self.background = background
        self.result: Any = None

        self._root: Widget | None = None
        self._running = False
        self._dirty = True
        self._events: asyncio.Queue[Event] = asyncio.Queue()
        self._parser = InputParser()
        self._loop: asyncio.AbstractEventLoop | None = None
        self._escape_timer: asyncio.TimerHandle | None = None
        self._signals: list[int] = []
        self._reader_fd: int | None = None

        self._back = ScreenBuffer(*self.terminal.size, background)
        self._front: ScreenBuffer | None = None
        self._min_frame_interval = 1.0 / max_fps if max_fps > 0 else 0.0
        self._last_frame = 0.0

        if root is not None:
            self.root = root

    # -- widget tree --------------------------------------------------------

    @property
    def root(self) -> Widget | None:
        """The widget filling the screen."""
        return self._root

    @root.setter
    def root(self, widget: Widget | None) -> None:
        if self._root is not None:
            self._root._application = None
        self._root = widget
        if widget is not None:
            widget._application = self
            widget.layout(*self.terminal.size)
        self.invalidate()

    # -- lifecycle ----------------------------------------------------------

    @property
    def is_running(self) -> bool:
        """True between the first frame and :meth:`exit`."""
        return self._running

    def run(self) -> Any:
        """Run the application until it exits, returning :attr:`result`."""
        return asyncio.run(self.run_async())

    async def run_async(self) -> Any:
        """Run the application on the current asyncio loop."""
        self._loop = asyncio.get_running_loop()
        self._running = True
        self.terminal.start()
        if self.title:
            self.terminal.set_title(self.title)
        try:
            self._attach_input()
            self._resize(*self.terminal.size)
            self.on_start()
            await self._main_loop()
        finally:
            self._running = False
            self._detach_input()
            with contextlib.suppress(Exception):
                self.on_stop()
            self.terminal.stop()
            self._loop = None
        return self.result

    def exit(self, result: Any = None) -> None:
        """Ask the event loop to stop after the current batch of events."""
        if result is not None:
            self.result = result
        self._running = False
        self._wake()

    def post_event(self, event: Event) -> None:
        """Queue *event* as if it had arrived from the terminal.

        The event joins the current batch, so it is dispatched before the next
        frame rather than after it.
        """
        self._events.put_nowait(event)

    def on_start(self) -> None:
        """Called once the terminal is ready, before the first frame."""

    def on_stop(self) -> None:
        """Called after the loop ends, before the terminal is restored."""

    # -- painting -----------------------------------------------------------

    def invalidate(self) -> None:
        """Request a repaint.  Cheap and safe to call many times per frame."""
        if not self._dirty:
            self._dirty = True
            self._wake()

    def _wake(self) -> None:
        """Nudge the loop when it is parked waiting for input."""
        if self._loop is not None and not self._events.full():
            self._events.put_nowait(_WAKE)

    async def _render(self) -> None:
        """Compose a frame and flush the difference to the terminal."""
        if self._min_frame_interval and self._loop is not None:
            overdue = self._min_frame_interval - (self._loop.time() - self._last_frame)
            if overdue > 0:
                await asyncio.sleep(overdue)

        self._back.clear(self.background)
        if self._root is not None:
            self._root.render_tree(self._back)

        output = render_diff(self._front, self._back)
        if output:
            self.terminal.write(output)
            self.terminal.flush()

        if self._front is None:
            self._front = ScreenBuffer(self._back.width, self._back.height)
        self._front.copy_from(self._back)
        self._dirty = False
        self._last_frame = self._loop.time() if self._loop is not None else 0.0

    def _resize(self, width: int, height: int) -> None:
        self._back.resize(width, height, self.background)
        self._front = None  # sizes differ -- force a full repaint
        if self._root is not None:
            self._root.layout(width, height)
        self._dirty = True

    # -- event loop ---------------------------------------------------------

    async def _main_loop(self) -> None:
        await self._render()
        while self._running:
            event = await self._events.get()
            self._handle(event)
            # Drain whatever else arrived in the meantime: a paste or a mouse
            # drag should cost one frame, not one frame per event.
            while self._running and not self._events.empty():
                self._handle(self._events.get_nowait())
            if self._running and self._dirty:
                await self._render()

    def _handle(self, event: Event) -> None:
        if isinstance(event, WakeEvent):
            return
        if isinstance(event, ResizeEvent):
            self._resize(event.width, event.height)
        try:
            if self.on_event(event):
                return
            if isinstance(event, KeyEvent):
                if not self.on_key(event) and self._root is not None:
                    self._root.dispatch_key(event)
            elif isinstance(event, MouseEvent):
                if not self.on_mouse(event) and self._root is not None:
                    self._root.dispatch_mouse(event)
            elif isinstance(event, ResizeEvent):
                self.on_resize(event)
            elif isinstance(event, PasteEvent):
                self.on_paste(event)
        except Exception:
            self.exit()
            raise

    # Hooks -- an application subclass sees every event before the widgets do.

    def on_event(self, event: Event) -> bool:
        """Handle any event.  Return True to stop it reaching the widgets."""
        return False

    def on_key(self, event: KeyEvent) -> bool:
        return False

    def on_mouse(self, event: MouseEvent) -> bool:
        return False

    def on_resize(self, event: ResizeEvent) -> None:
        pass

    def on_paste(self, event: PasteEvent) -> None:
        pass

    # -- input plumbing -----------------------------------------------------

    def _attach_input(self) -> None:
        assert self._loop is not None
        if self.terminal.is_tty:
            self._reader_fd = self.terminal.input_fd
            self._loop.add_reader(self._reader_fd, self._on_readable)
        for signum in (signal.SIGWINCH, signal.SIGTERM, signal.SIGHUP):
            with contextlib.suppress(NotImplementedError, ValueError, AttributeError):
                self._loop.add_signal_handler(signum, self._on_signal, signum)
                self._signals.append(signum)

    def _detach_input(self) -> None:
        if self._loop is None:
            return
        if self._escape_timer is not None:
            self._escape_timer.cancel()
            self._escape_timer = None
        if self._reader_fd is not None:
            with contextlib.suppress(Exception):
                self._loop.remove_reader(self._reader_fd)
            self._reader_fd = None
        for signum in self._signals:
            with contextlib.suppress(Exception):
                self._loop.remove_signal_handler(signum)
        self._signals.clear()

    def _on_readable(self) -> None:
        data = self.terminal.read()
        if not data:
            # End of input: the tty went away, so there is nothing left to do.
            self.exit()
            return
        for event in self._parser.feed(data):
            self.post_event(event)
        self._schedule_escape_flush()

    def _schedule_escape_flush(self) -> None:
        """Arm the timer that turns an ambiguous ``ESC`` into an escape key."""
        if self._escape_timer is not None:
            self._escape_timer.cancel()
            self._escape_timer = None
        if self._parser.pending_escape and self._loop is not None:
            self._escape_timer = self._loop.call_later(
                ESCAPE_TIMEOUT, self._flush_escape
            )

    def _flush_escape(self) -> None:
        self._escape_timer = None
        for event in self._parser.flush():
            self.post_event(event)

    def _on_signal(self, signum: int) -> None:
        if signum == signal.SIGWINCH:
            self.post_event(ResizeEvent(*self.terminal.size))
        else:
            self.exit()
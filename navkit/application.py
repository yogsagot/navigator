"""The application object and its event loop.

:class:`Application` is the only place in navkit that owns an asyncio loop.  It
wires the terminal's input to an event queue, dispatches events to the widget
tree, and repaints the screen once per batch of events rather than once per
event -- so a burst of keystrokes or a fast mouse drag costs a single frame.

The order within one turn of the loop is fixed: dispatch the whole batch, run
the reactive effects it queued, then paint.  Effects may change state and so
must run before the frame is composed; nothing reactive runs during the paint
itself.

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
from navkit.reactive import SCHEDULER, flush_effects, reactive
from navkit.screen import ScreenBuffer, render_diff
from navkit.style import DEFAULT_STYLE, Style
from navkit.stylesheet import Stylesheet
from navkit.terminal import HIDE_CURSOR, InputParser, Terminal, place_cursor
from navkit.widget import Widget

#: How long to wait before deciding a lone ``ESC`` really was the escape key
#: and not the start of a sequence the terminal is still sending.
ESCAPE_TIMEOUT = 0.05


_WAKE = WakeEvent()


class Application:
    """Owns the event loop, the terminal and the root of the widget tree."""

    #: The sheet every widget under this application resolves against.
    #: Observable, which is what makes loading a theme restyle the tree: each
    #: widget's style is derived from this, so replacing it marks all of them
    #: stale and the next frame repaints in the new colours.  A sheet held in a
    #: plain attribute would change nothing until an unrelated write happened.
    stylesheet: Stylesheet | None = reactive(None)
    #: The widget keys are sent to, or None while nothing holds the keyboard.
    #: Observable for the same reason the sheet is: ``Widget.focused`` is
    #: derived from it, so moving focus restyles the widget that had it and the
    #: one that takes it without either being told.  Assigning it directly is
    #: allowed and unpoliced -- :meth:`Widget.focus` is the door with the
    #: checks on it, and delivery re-checks what it needs anyway.
    focused: Widget | None = reactive(None)

    def __init__(
        self,
        root: Widget | None = None,
        *,
        terminal: Terminal | None = None,
        title: str | None = None,
        background: Style | None = None,
        stylesheet: Stylesheet | None = None,
        max_fps: int = 60,
        mouse: bool = True,
        palette: tuple[tuple[int, int, int], ...] | None = None,
        reprogram_palette: bool = False,
    ):
        # `mouse', `palette' and `reprogram_palette' are preferences for the
        # terminal this constructs, and are ignored when one is handed in --
        # a caller that built its own has already stated them.
        self.terminal = terminal or Terminal(
            mouse=mouse, palette=palette, reprogram_palette=reprogram_palette
        )
        self.title = title
        self._background = background
        self.stylesheet = stylesheet
        self.result: Any = None

        self._root: Widget | None = None
        #: Modal widgets, innermost last, each with whatever held the focus
        #: when it took over.  Maintained by the mount walks.
        self._modals: list[tuple[Widget, Widget | None]] = []
        self._running = False
        self._dirty = True
        self._events: asyncio.Queue[Event] = asyncio.Queue()
        self._parser = InputParser()
        self._loop: asyncio.AbstractEventLoop | None = None
        self._escape_timer: asyncio.TimerHandle | None = None
        self._signals: list[int] = []
        self._reader_fd: int | None = None

        self._back = ScreenBuffer(*self.terminal.size, self.background)
        self._front: ScreenBuffer | None = None
        self._min_frame_interval = 1.0 / max_fps if max_fps > 0 else 0.0
        self._last_frame = 0.0
        #: What the last frame left the terminal's cursor doing, so a frame
        #: that changes nothing about it emits nothing about it either.
        self._cursor_shown: tuple[int, int, str] | None = None

        if root is not None:
            self.root = root

    @property
    def background(self) -> Style:
        """What a cell looks like where no widget painted.

        **Derived from the root widget's resolved style**, not stated twice.
        The sheet already says what the desktop looks like -- `navigator.nss`
        has ``Manager { fg: $desktop-fg; bg: $desktop-bg }`` -- and an
        application that also took the colour as a constructor argument was
        reading the same two variables by a second route, through a helper
        that had to go behind the cascade to the raw variables because it ran
        "before any widget exists to ask".  Asking the root at paint time is
        later, and later is when the answer exists.

        Passing an explicit ``background=`` still overrides it, for a root
        that paints only part of itself, or for no root at all.
        """
        if self._background is not None:
            return self._background
        return self._root.style if self._root is not None else DEFAULT_STYLE

    @background.setter
    def background(self, style: Style | None) -> None:
        self._background = style
        self.invalidate()

    # -- widget tree --------------------------------------------------------

    @property
    def root(self) -> Widget | None:
        """The widget filling the screen."""
        return self._root

    @root.setter
    def root(self, widget: Widget | None) -> None:
        if self._root is not None:
            # Unmounted while it is still attached, so a handler sees the
            # application it is leaving, and before the focus into it goes
            # stale.
            self._root._unmount()
            self._root._application = None
            if self.focused is not None:
                self.focused = None
        self._root = widget
        if widget is not None:
            widget._application = self
            widget.layout(*self.terminal.size)
            # After the layout: a mount handler is owed a settled geometry,
            # which is most of why it exists rather than __init__.
            widget._mount()
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
            # An effect queued from outside a dispatch -- a timer callback, or
            # a write to something that is not a widget -- has to be able to
            # nudge a loop that is parked on the event queue.
            SCHEDULER.wake = self._wake
            self._attach_input()
            self._resize(*self.terminal.size)
            self.on_start()
            await self._main_loop()
        finally:
            self._running = False
            SCHEDULER.wake = None
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

    # -- modal and overlay ---------------------------------------------------

    @property
    def modal(self) -> Widget | None:
        """The widget holding all input, or None.  The innermost, if nested.

        Maintained by the mount walks rather than by a caller: a widget whose
        :attr:`Widget.modal` is set claims the input when it is mounted and
        releases it when it is unmounted, so every route out of the tree --
        ``remove()``, a replaced root, an ancestor going with it -- gives the
        input back without anybody remembering to.  A plain property over a
        plain list: nothing derives from it reactively yet, and a widget that
        wants to *look* different while it is blocked can be given a computed
        when something actually asks for one.
        """
        return self._modals[-1][0] if self._modals else None

    def overlay(self, widget: Widget) -> Widget:
        """Put *widget* on top of everything, and return it.

        The last child of the root: rendering walks children forwards and
        hit-testing backwards, so last is on top and asked first.  A widget
        deep in the tree opens one with ``self.application.overlay(dialog)``,
        which is the point -- where a dialog is *created* has nothing to do
        with where it belongs on the screen.

        Closing it is ``app.root.remove(dialog)``, which already unmounts the
        subtree, disposes its effects, releases the input if it was modal and
        hands the focus back to whatever had it.
        """
        if self._root is None:
            raise RuntimeError("no root widget to put an overlay on")
        return self._root.add(widget)

    def _push_modal(self, widget: Widget) -> None:
        """Called by the mount walk.  Remembers what had the focus."""
        self._modals.append((widget, self.focused))

    def _pop_modal(self, widget: Widget) -> None:
        """Called by the unmount walk.  Hands the focus back if it was on top.

        A modal that is not the top one -- removed out of order, or carried
        off with an ancestor -- simply leaves the stack: the focus belongs to
        whatever is still holding the input, not to the thing behind it.
        """
        for index, (held, restore) in enumerate(self._modals):
            if held is not widget:
                continue
            del self._modals[index]
            if index == len(self._modals):
                self.focused = None
                if restore is not None and restore.mounted:
                    restore.focus()
            return

    def _claim_focus(self) -> None:
        """Put the focus inside the active modal, if it is not there already.

        Run once a subtree has finished mounting, so a modal is choosing from
        children that exist. A modal with nothing focusable in it takes the
        focus away rather than leaving it outside, where it would keep a
        widget the user can no longer reach looking like the live one.
        """
        modal = self.modal
        if modal is None or (self.focused is not None and modal._holds(self.focused)):
            return
        order = modal.focusable()
        self.focused = order[0] if order else None

    def focus_next(self, reverse: bool = False) -> Widget | None:
        """Move focus along the tab order, wrapping.  The new holder, or None.

        The order is ``root.focusable()`` -- visible, focusable widgets in tree
        order -- or the active modal's, which is the whole of what makes a
        dialog's Tab stay inside the dialog.  Taken fresh each time rather than kept, because the tree is
        reactive and a cached order would be wrong the moment a widget is
        added, hidden or disabled; the walk is over the tree an event loop
        already repaints in full.

        A focus that is no longer in the order -- the widget was hidden, or
        removed -- does not stop the move: the search starts from the end it
        came from, so Tab out of a vanished widget lands on the first one.
        """
        scope = self.modal or self._root
        order = scope.focusable() if scope is not None else []
        if not order:
            return None
        if self.focused in order:
            index = order.index(self.focused) + (-1 if reverse else 1)
        else:
            index = -1 if reverse else 0
        self.focused = order[index % len(order)]
        return self.focused

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

        output = render_diff(self._front, self._back, self.terminal.info)
        cursor = self._cursor()
        if cursor != self._cursor_shown:
            # Emitted after the diff, always: painting moves the terminal's
            # own cursor as a side effect, so anything placed before it would
            # be left wherever the last cell was written.
            output += place_cursor(*cursor) if cursor is not None else HIDE_CURSOR
            self._cursor_shown = cursor
        elif output and cursor is not None:
            # Unchanged, but the paint just moved it.  The position alone --
            # it is already visible and already the right shape.
            output += f"\x1b[{cursor[1] + 1};{cursor[0] + 1}H"
        if output:
            self.terminal.write(output)
            self.terminal.flush()

        if self._front is None:
            self._front = ScreenBuffer(self._back.width, self._back.height)
        self._front.copy_from(self._back)
        self._dirty = False
        self._last_frame = self._loop.time() if self._loop is not None else 0.0

    def _cursor(self) -> tuple[int, int, str] | None:
        """Screen position and shape of the terminal cursor, or None for none.

        **Shown exactly where the keys go.** The widget asked is the one at
        the head of the focus path -- the same walk :meth:`Widget.dispatch_key`
        makes, so the same modal, the same visibility test and the same answer
        of "nobody" when nothing holds the keyboard. A caret on a widget that
        could not receive what is typed into it would be a lie told once per
        frame.
        """
        scope = self.modal or self._root
        if scope is None:
            return None
        path = scope._focus_path()
        if not path:
            return None
        widget = path[0]
        position = widget.cursor_position()
        if position is None:
            return None
        x, y = position
        if not (0 <= x < widget.width and 0 <= y < widget.height):
            return None
        offset_x, offset_y = widget.offset()
        x, y = offset_x + widget.x + x, offset_y + widget.y + y
        if not (0 <= x < self._back.width and 0 <= y < self._back.height):
            return None
        return x, y, widget.style_property("caret", "default")

    def _resize(self, width: int, height: int) -> None:
        self._back.resize(width, height, self.background)
        self._front = None  # sizes differ -- force a full repaint
        if self._root is not None:
            self._root.layout(width, height)
        self._dirty = True

    # -- event loop ---------------------------------------------------------

    async def _main_loop(self) -> None:
        self._flush_effects()
        await self._render()
        while self._running:
            event = await self._events.get()
            self._handle(event)
            # Drain whatever else arrived in the meantime: a paste or a mouse
            # drag should cost one frame, not one frame per event.
            while self._running and not self._events.empty():
                self._handle(self._events.get_nowait())
            if self._running:
                self._flush_effects()
            if self._running and self._dirty:
                await self._render()

    def _flush_effects(self) -> None:
        """Run the reactions this batch of events queued, before painting.

        Effects assign reactive attributes, so they belong here rather than
        inside :meth:`_render`: whatever they change is part of the frame that
        is about to be composed.  A failing reaction takes the application
        down the same way a failing event handler does.
        """
        try:
            flush_effects()
        except Exception:
            self.exit()
            raise

    def _handle(self, event: Event) -> None:
        if isinstance(event, WakeEvent):
            return
        if isinstance(event, ResizeEvent):
            self._resize(event.width, event.height)
        try:
            if self.on_event(event):
                return
            if isinstance(event, KeyEvent):
                # Dispatching on the modal rather than the root is the whole
                # of keyboard exclusivity: the walk runs from the focused
                # widget up to whatever it was called on, so it neither starts
                # outside the modal nor bubbles past it.
                target = self.modal or self._root
                if not self.on_key(event) and target is not None:
                    target.dispatch_key(event)
            elif isinstance(event, MouseEvent):
                if not self.on_mouse(event):
                    self._dispatch_mouse(event)
            elif isinstance(event, ResizeEvent):
                self.on_resize(event)
            elif isinstance(event, PasteEvent):
                self.on_paste(event)
            else:
                # Anything posted that the four branches above do not know.
                # It has no sender in the widget tree -- nobody announced it --
                # so it stops here, at the hook its own class names.  A widget's
                # event goes the other way, through ``Widget.announce``.
                handler = getattr(self, event.handler, None)
                # A bare ``Event`` derives ``on_event``, which every event has
                # already been offered to above; the hooks are only distinct
                # when the names are.
                if handler is not None and handler != self.on_event:
                    handler(event)
        except Exception:
            self.exit()
            raise

    def _dispatch_mouse(self, event: MouseEvent) -> None:
        """Route a mouse action into the tree, or into the modal alone.

        The mouse is where modality costs something, because it routes by
        position rather than by focus: every widget under the pointer is on
        the path, whether or not it is supposed to be reachable. So the event
        is moved into the modal's parent's frame and offered there, and one
        that lands outside the modal reaches nothing at all -- not the widgets
        underneath, and not the modal either, whose coordinates it is not in.

        Dismissing on an outside click is a *policy*, and belongs to whatever
        widget wants it: it can watch the application's own ``on_mouse``,
        which still sees every action before any of this.
        """
        modal = self.modal
        if modal is None:
            if self._root is not None:
                self._root.dispatch_mouse(event)
            return
        dx, dy = modal.offset()
        local = event.translated(-dx, -dy)
        if modal.contains(local.x, local.y):
            modal.dispatch_mouse(local)

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
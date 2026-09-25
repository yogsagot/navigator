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
import inspect
import math
import signal
import time
from collections.abc import Awaitable, Callable, Coroutine
from dataclasses import dataclass
from typing import Any

from navkit.events import (
    DoubleClickEvent,
    Event,
    KeyEvent,
    MouseClickEvent,
    PasteEvent,
    ResizeEvent,
    WakeEvent,
)
from navkit.reactive import SCHEDULER, flush_effects, reactive
from navkit.screen import ScreenBuffer, render_diff
from navkit.style import DEFAULT_STYLE, Style
from navkit.stylesheet import Stylesheet
from navkit.terminal import HIDE_CURSOR, InputParser, Terminal, place_cursor
from navkit.widget import Widget, _call, check_handlers

#: How long to wait before deciding a lone ``ESC`` really was the escape key
#: and not the start of a sequence the terminal is still sending.
ESCAPE_TIMEOUT = 0.05

#: How long after a press a second one at the same cell is a double-click.
#: What GTK and Qt both default to.  Unlike :data:`ESCAPE_TIMEOUT` the
#: constructor takes it: the escape window is calibrated against a terminal's
#: transmission, which is nobody's preference, and this one against a user's
#: hand, which is the application's to state.
DOUBLE_CLICK_TIMEOUT = 0.4


_WAKE = WakeEvent()


class Repeat:
    """A callback :meth:`Application.call_every` runs every *seconds*.

    Returned rather than hidden so its owner can :meth:`cancel` it -- a widget
    from :meth:`Widget.unmounting`, which is the hook that exists for exactly
    this.  Every tick is delivered **through the event queue**, so the callback
    runs inside a batch like any handler: its effects are flushed and one frame
    is painted after it, and an exception it raises stops the application.
    See *Timers: through the queue* in ``navkit/DESIGN.md``.
    """

    def __init__(
        self,
        app: Application,
        seconds: float,
        callback: Callable[[], Awaitable[Any]],
    ) -> None:
        self.seconds = seconds
        self.callback = callback
        #: True once :meth:`cancel` has run, or the application stopped.
        self.cancelled = False
        self._app = app
        self._handle: asyncio.TimerHandle | None = None
        self._next = 0.0

    def cancel(self) -> None:
        """Stop ticking.  Idempotent, and a tick already queued is dropped."""
        self.cancelled = True
        if self._handle is not None:
            self._handle.cancel()
            self._handle = None
        self._app._repeats.discard(self)

    def _arm(self, loop: asyncio.AbstractEventLoop) -> None:
        """Start counting from now.  The first tick is one period away."""
        self._next = loop.time() + self.seconds
        self._handle = loop.call_at(self._next, self._fire, loop)

    def _fire(self, loop: asyncio.AbstractEventLoop) -> None:
        """The loop's timer went off: queue a tick and arm the next one.

        Scheduled against the original start rather than the moment this ran,
        so a slow batch does not push every later tick back.  A loop that fell
        more than a period behind **skips** the slots it missed instead of
        queueing a burst of them -- a clock that was stalled has nothing to
        catch up on.
        """
        self._handle = None
        if self.cancelled:
            return
        self._app.post_event(_Tick(self))
        now = loop.time()
        self._next += self.seconds
        if self._next <= now:
            self._next += math.floor((now - self._next) / self.seconds + 1) * self.seconds
        self._handle = loop.call_at(self._next, self._fire, loop)


@dataclass(frozen=True, slots=True)
class _Tick(Event):
    """Internal: one period of a :class:`Repeat` elapsed.

    Private, like the wake, and never offered to ``on_event``: it is how a
    timer gets into a batch, not something the terminal said.
    """

    repeat: Repeat


class ClickTracker:
    """Counts presses of one button at one cell into a run of clicks.

    **Deliberately clockless**: :meth:`press` is told the time rather than
    reading one.  That is what lets the whole rule be tested in a plain
    function with no event loop, no application and no fake clock -- the one
    thing ``tests/conftest.py`` cannot provide.  The application owns
    ``loop.time()`` and passes it in.

    See *What the detector keys on* in ``navkit/DESIGN.md``.
    """

    def __init__(self, timeout: float = DOUBLE_CLICK_TIMEOUT) -> None:
        #: Zero disables double-click detection altogether.
        self.timeout = timeout
        self._where: tuple[int, int, str] | None = None
        self._when = 0.0
        self._count = 0

    def press(self, event: MouseClickEvent, now: float) -> int:
        """How many clicks *event* completes -- 1, 2, 3... -- or 0 for none.

        **The run counts upward and never restarts inside itself**, so a
        triple click reports 3 and a fourth press 4.  Only a count of exactly
        two raises anything, which is how a fast triple click cannot fire a
        second double-click: restarting at 1 after each pair would have
        entered the same directory twice.

        A wheel detent arrives as a press and is not one -- two notches at one
        cell inside the window is the *normal* way to use a wheel.  It ends
        the run as well as being excluded from it, because the content under
        the pointer has just moved and the cell no longer denotes what it did.
        """
        if event.action != "press" or event.button == "none":
            return 0
        if event.is_wheel:
            self.reset()
            return 0
        where = (event.x, event.y, event.button)
        if (
            self.timeout > 0
            and where == self._where
            and now - self._when <= self.timeout
        ):
            self._count += 1
        else:
            self._count = 1
        self._where, self._when = where, now
        return self._count

    def reset(self) -> None:
        """Forget the run: the cell no longer denotes what it did.

        Called whenever navkit knows that much -- a wheel scrolled the content
        out from under the pointer, a resize moved the layout, a modal opened
        or closed over it.
        """
        self._where = None
        self._count = 0


class Application:
    """Owns the event loop, the terminal and the root of the widget tree."""

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        check_handlers(cls)

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
        double_click: float = DOUBLE_CLICK_TIMEOUT,
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
        self.result: Any = None

        self._root: Widget | None = None
        #: Modal widgets, innermost last, each with whatever held the focus
        #: when it took over.  Maintained by the mount walks.
        self._modals: list[tuple[Widget, Widget | None]] = []
        #: The widget every mouse action goes to regardless of position, or
        #: None.  See :meth:`capture_mouse`.
        self._capture: Widget | None = None
        self._running = False
        self._dirty = True
        self._events: asyncio.Queue[Event] = asyncio.Queue()
        self._parser = InputParser()
        self._loop: asyncio.AbstractEventLoop | None = None
        self._escape_timer: asyncio.TimerHandle | None = None
        #: Turns two presses and a clock into a double-click.  Zero off.
        self._clicks = ClickTracker(double_click)
        #: Work started by :meth:`spawn`, held so that nothing is collected
        #: mid-flight and everything can be cancelled on the way out.
        self._tasks: set[asyncio.Task[Any]] = set()
        #: Everything :meth:`call_every` is running, armed or waiting for
        #: the loop to start.
        self._repeats: set[Repeat] = set()
        #: True while a handler is running, which is what makes waiting for
        #: input from inside one a diagnosable error -- see :meth:`spawn`.
        self._dispatching = False
        self._signals: list[int] = []
        self._reader_fd: int | None = None
        # An observable, so its write asks for a frame -- which needs the
        # loop state above to exist already.
        self.stylesheet = stylesheet

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
            for repeat in self._repeats:
                repeat._arm(self._loop)
            self._resize(*self.terminal.size)
            await self.on_start()
            await self._main_loop()
        finally:
            self._running = False
            SCHEDULER.wake = None
            await self._cancel_tasks()
            for repeat in list(self._repeats):
                repeat.cancel()
            self._detach_input()
            with contextlib.suppress(Exception):
                await self.on_stop()
            self.terminal.stop()
            self._loop = None
        return self.result

    def exit(self, result: Any = None) -> None:
        """Ask the event loop to stop after the current batch of events."""
        if result is not None:
            self.result = result
        self._running = False
        self._wake()

    # -- work that outlives a handler ----------------------------------------

    def spawn(self, work: Coroutine[Any, Any, Any]) -> asyncio.Task[Any]:
        """Run *work* beside the event loop, so that it may wait for input.

        **A handler cannot wait for input, and this is the way out.**
        :meth:`_main_loop` awaits ``_handle`` and only then paints, so a
        handler that awaits something a later keystroke will resolve is
        holding the one consumer of the event queue: the keystroke is read,
        queued, and never dispatched, and no frame is produced in the
        meantime.  A dialog awaited from inside ``on_key`` therefore never
        appears and never answers.  Starting the work here instead lets the
        handler return, the batch finish and the frame paint, and the waiting
        happens in a task that is not in anybody's way.

        The task is **held** rather than left to the caller: a bare
        ``create_task`` whose result nobody keeps may be collected while it is
        still running, and takes its exception with it.  Whatever is still
        pending when the application stops is cancelled, so a dialog left open
        at exit tears itself down through its own ``finally`` instead of
        leaking.
        """
        if self._loop is None:
            raise RuntimeError("the application is not running")
        task = self._loop.create_task(work)
        self._tasks.add(task)
        task.add_done_callback(self._finished)
        return task

    def call_every(
        self, seconds: float, callback: Callable[[], Awaitable[Any]]
    ) -> Repeat:
        """Await *callback* every *seconds*, inside a batch, until cancelled.

        **The one clock navkit offers**, because the loop is the only one event
        handling can reach.  May be called before the application runs -- a
        tree is mounted from the constructor, long before there is a loop --
        in which case the count starts when :meth:`run_async` does.  Stopping
        the application cancels every one.

        *callback* takes no argument and must be ``async``, for the reason
        every ``on_*`` must: it is awaited where a handler would be.
        """
        if not seconds > 0:
            raise ValueError(f"call_every needs a positive interval, not {seconds!r}")
        if not inspect.iscoroutinefunction(callback):
            raise TypeError(f"call_every needs an async callback, not {callback!r}")
        repeat = Repeat(self, seconds, callback)
        self._repeats.add(repeat)
        if self._running and self._loop is not None:
            repeat._arm(self._loop)
        return repeat

    def _finished(self, task: asyncio.Task[Any]) -> None:
        """Forget a finished task, and let its failure out.

        A task that raised would otherwise be reported by asyncio long
        afterwards, as "exception was never retrieved", with the loop still
        running and the screen unchanged.  Failing the way a handler does --
        stop, then re-raise -- keeps one rule for both.
        """
        self._tasks.discard(task)
        if not task.cancelled() and task.exception() is not None:
            self.exit()
            raise task.exception()  # type: ignore[misc]

    async def _cancel_tasks(self) -> None:
        """Stop everything :meth:`spawn` started, on the way out."""
        pending = [task for task in self._tasks if not task.done()]
        for task in pending:
            task.cancel()
        for task in pending:
            with contextlib.suppress(asyncio.CancelledError, Exception):
                await task
        self._tasks.clear()

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

    # -- mouse capture -------------------------------------------------------

    @property
    def mouse_capture(self) -> Widget | None:
        """The widget holding the mouse, or None."""
        return self._capture

    def capture_mouse(self, widget: Widget) -> None:
        """Send every mouse action to *widget* until the button is released.

        What a drag needs.  Routing is by position, and a pointer dragging a
        window's edge is routinely *outside* the window by the time the
        terminal reports it -- a fast hand, or a resize the window refuses
        past its minimum -- so without this the drag stops the moment the
        pointer outruns what it is dragging.  While held, an action is
        delivered straight to *widget*'s handler in its own coordinates, with
        no hit test; the application's own hook still sees it first.

        Released by itself after a ``release`` is delivered, when *widget* is
        unmounted, and when a modal opens that does not hold it.
        """
        self._capture = widget

    def release_mouse(self) -> None:
        """Let the mouse route by position again."""
        self._capture = None

    def _push_modal(self, widget: Widget) -> None:
        """Called by the mount walk.  Remembers what had the focus."""
        # Something else is under the pointer now, so a press before this and
        # one after it are not two clicks on one thing.
        self._clicks.reset()
        if self._capture is not None and not widget._holds(self._capture):
            self._capture = None
        self._modals.append((widget, self.focused))

    def _pop_modal(self, widget: Widget) -> None:
        """Called by the unmount walk.  Hands the focus back if it was on top.

        A modal that is not the top one -- removed out of order, or carried
        off with an ancestor -- simply leaves the stack: the focus belongs to
        whatever is still holding the input, not to the thing behind it.
        """
        self._clicks.reset()  # as `_push_modal': the cell changed meaning
        for index, (held, restore) in enumerate(self._modals):
            if held is not widget:
                continue
            del self._modals[index]
            if index == len(self._modals):
                self.focused = None
                if restore is not None and restore.is_mounted:
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

    async def on_start(self) -> None:
        """Called once the terminal is ready, before the first frame.

        ``async def`` like every other ``on_*``, and it costs nothing here:
        this runs inside :meth:`run_async`, which can await it.  That is the
        whole of the rule -- a hook that *cannot* be awaited where it is
        called does not get an ``on_*`` name, which is why the widget
        lifecycle is :meth:`Widget.mounted` rather than ``on_mount``.
        """

    async def on_stop(self) -> None:
        """Called after the loop ends, before the terminal is restored."""

    # -- painting -----------------------------------------------------------

    def invalidate(self) -> None:
        """Request a repaint.  Cheap and safe to call many times per frame."""
        if not self._dirty:
            self._dirty = True
            self._wake()

    def _reactive_changed(self, name: str) -> None:
        """One of the application's own observables changed: repaint.

        The same hook ``Widget`` has, and needed for the same reason.  A
        write reaches ``_reactive_changed`` only on the object it was made
        to, and every widget derived from ``focused`` or ``stylesheet`` is
        merely marked stale -- so without this, moving the focus and nothing
        else (Tab between two panels) restyled both widgets and asked for no
        frame, and the change showed up with the next unrelated key.
        """
        self.invalidate()

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
        self._clicks.reset()  # the layout moved out from under the pointer
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
            await self._handle(event)
            # Drain whatever else arrived in the meantime: a paste or a mouse
            # drag should cost one frame, not one frame per event.  A handler
            # that awaits lets the loop's other work run -- reading input,
            # pty output, timers -- but cannot produce a frame, because
            # ``_render`` is only ever awaited from here.
            while self._running and not self._events.empty():
                await self._handle(self._events.get_nowait())
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

    async def _handle(self, event: Event) -> None:
        if isinstance(event, WakeEvent):
            return
        if isinstance(event, _Tick):
            await self._tick(event.repeat)
            return
        if isinstance(event, ResizeEvent):
            self._resize(event.width, event.height)
        # Saved and restored rather than set and cleared: `_handle' returns
        # early for a claimed event and re-enters itself for a double click,
        # so a plain reset would report "not dispatching" while the outer call
        # still is.
        dispatching, self._dispatching = self._dispatching, True
        try:
            if await self.on_event(event):
                return
            if isinstance(event, KeyEvent):
                # Dispatching on the modal rather than the root is the whole
                # of keyboard exclusivity: the walk runs from the focused
                # widget up to whatever it was called on, so it neither starts
                # outside the modal nor bubbles past it.
                target = self.modal or self._root
                if not await self.on_key(event) and target is not None:
                    await target.dispatch_key(event)
            elif isinstance(event, MouseClickEvent):
                # Counted from the press itself, before it is delivered and
                # whatever claims it: whether a widget consumed a press says
                # nothing about whether the user clicked twice.  A
                # DoubleClickEvent is a conclusion *about* presses and is
                # never counted as one, which bounds the recursion below at
                # one level.
                clicks = (
                    0
                    if isinstance(event, DoubleClickEvent)
                    else self._clicks.press(event, self._now())
                )
                await self._deliver_mouse(event)
                if clicks == 2:
                    # Inline rather than posted, so cause and effect stay
                    # adjacent: the press's own release is usually already in
                    # the queue from the same read, and queueing would deliver
                    # it in between.  Through `_handle' so `on_event' sees it,
                    # as it sees the escape key navkit manufactures.
                    await self._handle(DoubleClickEvent.of(event))
            elif isinstance(event, ResizeEvent):
                await self.on_resize(event)
            elif isinstance(event, PasteEvent):
                await self.on_paste(event)
            else:
                # Anything posted that the four branches above do not know.
                # It has no sender in the widget tree -- nobody emitted it --
                # so it stops here, at the hook its own class names.  A widget's
                # event goes the other way, through ``Widget.emit``.
                handler = getattr(self, event.handler, None)
                # A bare ``Event`` derives ``on_event``, which every event has
                # already been offered to above; the hooks are only distinct
                # when the names are.
                if handler is not None and handler != self.on_event:
                    await _call(self, event, handler)
        except Exception:
            self.exit()
            raise
        finally:
            self._dispatching = dispatching

    async def _tick(self, repeat: Repeat) -> None:
        """Run one tick of *repeat*, as a handler: failure stops the app.

        A cancelled one is skipped here as well as at the timer, because its
        tick may already have been queued when its owner let go of it.
        """
        if repeat.cancelled:
            return
        dispatching, self._dispatching = self._dispatching, True
        try:
            await repeat.callback()
        except Exception:
            self.exit()
            raise
        finally:
            self._dispatching = dispatching

    def _now(self) -> float:
        """The loop's clock, or a real one when there is no loop yet.

        Not ``_render``'s fallback of ``0.0``: a frame stamped "long ago" is
        the right default there, but two presses both stamped ``0.0`` are a
        double-click by the rule, so a test calling :meth:`_handle` directly
        would manufacture one out of nothing.  ``monotonic()`` is the clock
        asyncio's own is built on, and is always there.
        """
        return self._loop.time() if self._loop is not None else time.monotonic()

    async def _deliver_mouse(self, event: MouseClickEvent) -> None:
        """Offer *event* to this application's own hook, then to the tree.

        Looked up under ``event.handler`` for the reason
        :meth:`Widget.dispatch_mouse` does it: ``on_mouse_click`` is what a plain
        ``MouseClickEvent`` derives, so this is the call that was always made, and
        a refinement reaches its own hook or goes straight past the
        application to the widgets.
        """
        hook = getattr(self, event.handler, None)
        if hook is None or not await _call(self, event, hook):
            await self._dispatch_mouse(event)

    async def _dispatch_mouse(self, event: MouseClickEvent) -> None:
        """Route a mouse action into the tree, or into the modal alone.

        The mouse is where modality costs something, because it routes by
        position rather than by focus: every widget under the pointer is on
        the path, whether or not it is supposed to be reachable. So the event
        is moved into the modal's parent's frame and offered there, and one
        that lands outside the modal reaches nothing at all -- not the widgets
        underneath, and not the modal either, whose coordinates it is not in.

        Dismissing on an outside click is a *policy*, and belongs to whatever
        widget wants it: it can watch the application's own ``on_mouse_click``,
        which still sees every action before any of this.
        """
        capture = self._capture
        if capture is not None:
            dx, dy = capture.offset()
            local = event.translated(-dx - capture.x, -dy - capture.y)
            try:
                handler = getattr(capture, event.handler, None)
                if handler is not None:
                    await _call(capture, local, handler)
            finally:
                if event.action == "release" and self._capture is capture:
                    self._capture = None
            return
        modal = self.modal
        if modal is None:
            if self._root is not None:
                await self._root.dispatch_mouse(event)
            return
        dx, dy = modal.offset()
        local = event.translated(-dx, -dy)
        if modal.contains(local.x, local.y):
            await modal.dispatch_mouse(local)

    # Hooks -- an application subclass sees every event before the widgets do.

    async def on_event(self, event: Event) -> bool:
        """Handle any event.  Return True to stop it reaching the widgets."""
        return False

    async def on_key(self, event: KeyEvent) -> bool:
        return False

    async def on_mouse_click(self, event: MouseClickEvent) -> bool:
        return False

    async def on_resize(self, event: ResizeEvent) -> None:
        pass

    async def on_paste(self, event: PasteEvent) -> None:
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
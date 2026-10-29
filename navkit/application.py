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
import dataclasses
import functools
import inspect
import math
import signal
import threading
import weakref
import time
from collections import deque
from collections.abc import Awaitable, Callable, Coroutine
from dataclasses import dataclass
from typing import Any

from navkit.events import (
    ClickOutsideEvent,
    ContextMenuEvent,
    DoubleClickEvent,
    Event,
    KeyEvent,
    KeyReleaseEvent,
    ModifiersEvent,
    MouseClickEvent,
    PasteEvent,
    ResizeEvent,
    WakeEvent,
)
from navkit.glyphs import DEFAULT_MARKS
from navkit.reactive import SCHEDULER, flush_effects, reactive
from navkit.capabilities import BIDI_WORDS
from navkit.screen import ScreenBuffer, Surface, for_words, render_diff
from navkit.style import DEFAULT_STYLE, Style
from navkit.stylesheet import Stylesheet
from navkit.tooltip import ShowTooltip, Tooltip
from navkit.terminal import HIDE_CURSOR, InputParser, Terminal, place_cursor
from navkit import clipboard, commands, i18n
from navkit.widget import Widget, _call, check_handlers

#: How long to wait before deciding a lone ``ESC`` really was the escape key
#: and not the start of a sequence the terminal is still sending.
ESCAPE_TIMEOUT = 0.05

#: Left and Right on a mirrored screen: each is the other (``Application._unmirror``).
_ARROW_MIRROR = {"left": "right", "right": "left"}

#: How long after a press a second one at the same cell is a double-click.
#: What GTK and Qt both default to.  Unlike :data:`ESCAPE_TIMEOUT` the
#: constructor takes it: the escape window is calibrated against a terminal's
#: transmission, which is nobody's preference, and this one against a user's
#: hand, which is the application's to state.
DOUBLE_CLICK_TIMEOUT = 0.4

#: How long a paste waits for the terminal to answer an OSC 52 query before it
#: pastes the application's own copy instead.  A terminal that answers does so
#: in milliseconds; one that is slower is asking its user first (Ghostty's
#: ``clipboard-read = ask``), and one that never answers (VTE, JediTerm) is
#: the case this is for.
CLIPBOARD_ANSWER_TIMEOUT = 0.5

#: Milliseconds the mouse pointer must rest on a widget with a tooltip before
#: the tooltip shows.  Overridable per application (``tooltip_delay=``); zero off.
TOOLTIP_DELAY = 1000

#: Seconds after a tooltip was taken down by the pointer moving on during
#: which the next one shows at once (:data:`TOOLTIP_FOLLOW_ON_DELAY`) rather
#: than after the whole delay: sweeping along the key bar or down a menu reads
#: one tooltip after another without stopping at each.
TOOLTIP_FOLLOW_ON = 2.0
#: Seconds the pointer rests before a follow-on tooltip shows: long enough
#: that the cells crossed on the way show nothing.
TOOLTIP_FOLLOW_ON_DELAY = 0.08

#: How many failures :meth:`Application.report_error` may be offered inside
#: :data:`ERROR_STORM_WINDOW` seconds before the next one stops the
#: application regardless: an effect or a timer that fails every turn would
#: otherwise bury the user in error boxes.
ERROR_STORM_LIMIT = 5
ERROR_STORM_WINDOW = 10.0

#: How many dimmed styles :meth:`Application._painting_modal` remembers
#: before starting over.  A frame holds a few dozen; this only bounds a
#: session that paints an unbounded variety of colours behind a dialog.
DIMMED_STYLES_LIMIT = 4096


_WAKE = WakeEvent()


class Repeat:
    """A callback :meth:`Application.call_every` runs every *seconds*.

    Returned rather than hidden so its owner can :meth:`cancel` it -- a widget
    from :meth:`Widget.unmounting`, which is the hook that exists for exactly
    this.  Every tick is delivered **through the event queue**, so the callback
    runs inside a batch like any handler: its effects are flushed and one frame
    is painted after it, and an exception it raises goes to
    :meth:`Application.fail`, as a handler's does.
    See *Timers: through the queue* in ``navkit/DESIGN.md``.
    """

    def __init__(
        self,
        app: Application,
        seconds: float,
        callback: Callable[[], Awaitable[Any]],
        once: bool = False,
    ) -> None:
        self.seconds = seconds
        self.callback = callback
        #: Ticks once and is done: :meth:`Application.call_later`'s.
        self.once = once
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
        if self.once:
            return
        now = loop.time()
        self._next += self.seconds
        if self._next <= now:
            self._next += math.floor((now - self._next) / self.seconds + 1) * self.seconds
        self._handle = loop.call_at(self._next, self._fire, loop)


class _ThreadHook:
    """``threading.excepthook`` while an application runs: a thread's death
    goes to it (:meth:`Application._thread_exception`), and once it is gone,
    to the hook that was there before.

    Holds the application weakly.  A ``Thread`` keeps the hook in place when
    it was made, so a long-lived worker -- a shared pool's -- started while an
    application ran would otherwise keep that application, and everything it
    built, alive as long as the worker: in a process that runs many (a test
    suite), all of them.
    """

    def __init__(self, app: Application, previous: Callable[[threading.ExceptHookArgs], Any]) -> None:
        self._app = weakref.ref(app)
        self._previous = previous

    def __call__(self, args: threading.ExceptHookArgs) -> None:
        app = self._app()
        if app is None or not app.is_running:
            self._previous(args)
            return
        app._thread_exception(args)


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


def _is_plain_motion(event: MouseClickEvent) -> bool:
    """A report of the pointer moving with no button held -- mode 1003's."""
    return event.action == "move" and event.button == "none"


def describe_event(event: Event) -> str:
    """*event* in a few words for a log: a key by its name, a mouse action
    with its cell, a paste by its length only -- never the text it carried."""
    if isinstance(event, KeyEvent):
        return f"key {event.name}"
    if isinstance(event, MouseClickEvent):
        return f"{type(event).__name__} {event.button} {event.action} at {event.x},{event.y}"
    if isinstance(event, PasteEvent):
        return f"paste of {len(event.text)} characters ({event.origin})"
    if isinstance(event, ResizeEvent):
        return f"resize to {event.width}x{event.height}"
    if isinstance(event, _Tick):
        callback = event.repeat.callback
        return f"timer {getattr(callback, '__qualname__', repr(callback))}"
    return type(event).__name__


class Application:
    """Owns the event loop, the terminal and the root of the widget tree."""

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        check_handlers(cls)
        commands.check_keys(cls)

    #: Keys bound before any widget sees them -- the application's key table,
    #: which runs where :meth:`on_key` runs and so keeps its keys from the
    #: whole tree.  Stood aside from while a modal is up, because a modal
    #: means *nothing outside me* and this table is outside it.
    keys: Any = {}

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
    #: The innermost widget under the mouse pointer, or None.  Moved by every
    #: report of the pointer's position -- a plain motion, which reaches no
    #: widget, and a press -- so ``Widget.hovered`` and the ``:hovered`` state
    #: follow it the way ``focused`` follows the keyboard.  Left alone while
    #: the mouse is captured: a drag is not the pointer wandering.
    hovered: Widget | None = reactive(None)
    #: Where the terminal last said the mouse pointer was, ``(x, y)`` on the
    #: screen, or None before it has said.  Plain, not reactive: a fact for
    #: whoever asks (DN's ``MouseWhere``), moved by every report.
    pointer: tuple[int, int] | None = None
    #: The modifier keys held down right now -- some of ``ctrl``, ``alt`` and
    #: ``shift``.  Moved only by a :class:`ModifiersEvent`, which only a
    #: terminal speaking the kitty keyboard protocol sends, so elsewhere it is
    #: always empty.  Reactive, so a key bar reading it in ``render()`` swaps
    #: its row while Alt is held and swaps it back on the release.
    modifiers: frozenset[str] = reactive(frozenset())
    #: The keys of a chord pressed so far -- ``"ctrl+k"`` after Ctrl+K, when
    #: some table on the way to the focus binds a chord beginning with it --
    #: or empty.  The next key completes the chord or abandons it, and is
    #: swallowed either way, as WordStar's was.  Reactive, so whatever shows
    #: that a chord is pending (an editor's info line) follows it.
    chord: str = reactive("")
    #: Which set of :data:`navkit.glyphs.MARKS` a check box or radio button
    #: whose ``look`` is ``auto`` draws with.  Plain, read at every paint:
    #: whoever changes it calls :meth:`invalidate`.
    marks: str = DEFAULT_MARKS
    #: Counts the times :meth:`use_terminal_info` replaced what the terminal
    #: is thought to support.  Nothing reads the number: :attr:`Widget.glyphs`
    #: reads the field so that a caption bound to the glyph tier is
    #: recomputed when the tier changes.
    info_revision: int = reactive(0)

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
        tooltip_delay: int = TOOLTIP_DELAY,
        palette: tuple[tuple[int, int, int], ...] | None = None,
        reprogram_palette: bool = False,
        dim_modal: bool = False,
    ):
        # `mouse', `palette' and `reprogram_palette' are preferences for the
        # terminal this constructs, and are ignored when one is handed in --
        # a caller that built its own has already stated them.
        self.terminal = terminal or Terminal(
            mouse=mouse, palette=palette, reprogram_palette=reprogram_palette
        )
        self._title = title
        self._background = background
        #: Whether what lies beneath the top modal is painted dimmed.  Off by
        #: default and experimental -- see :meth:`_painting_modal`.
        self.dim_modal = dim_modal
        #: Which way the screen reads: ``"auto"`` follows the language (a
        #: catalogue whose ``[meta]`` says ``direction = "rtl"``,
        #: :func:`navkit.i18n.is_rtl`), ``"rtl"`` and ``"ltr"`` say so outright.
        #: A right-to-left screen is the whole frame mirrored on its way out
        #: (:attr:`rtl`).
        self.direction = "auto"
        #: The direction the last frame was painted in, so a change of language
        #: repaints everything rather than reusing a modal's underlay.
        self._rtl_painted = False
        #: Each style painted behind a modal, and its dimmed twin.  Kept from
        #: frame to frame so that an unchanged cell holds the *same* style
        #: object as last time, which is what lets :func:`render_diff` rule a
        #: row out in one comparison instead of comparing every cell's style
        #: field by field -- the dim pass otherwise cost more than the frame.
        self._dimmed: dict[Style, Style] = {}
        #: The top modal and a copy of the frame as it stood just before that
        #: modal painted -- everything beneath it, dimmed already.  See
        #: :meth:`_render`: a frame whose every change is inside the modal
        #: starts from this instead of painting the whole tree again.
        self._underlay: tuple[Widget, ScreenBuffer] | None = None
        #: Whether anything outside the top modal may have changed since the
        #: last frame, which is what :attr:`_underlay` cannot be used across.
        self._below_dirty = True
        #: Set while :meth:`_render` paints the whole tree, which is the only
        #: time :meth:`_painting_modal` may take an underlay.
        self._composing = False
        #: Set while :meth:`_render` paints over an underlay, which is dimmed
        #: already and must not be dimmed or taken again.
        self._reusing = False
        #: Whether a copy reaches the desktop's clipboard and a paste reads it
        #: (:meth:`copy_to_clipboard`).  Off, the clipboard is a private one
        #: inside the application, as Turbo Vision's was.
        self.system_clipboard = True
        #: The private clipboard and primary selection, by *primary*.  Kept
        #: whichever way :attr:`system_clipboard` is, so turning it off still
        #: has the last copy to paste.
        self._private_clipboard: dict[bool, str] = {False: "", True: ""}
        #: Whether an OSC 52 query is waiting for the terminal's answer.  An
        #: answer arriving while it is not -- after the private copy was
        #: pasted instead, or never asked for -- is dropped.
        self._clipboard_asked = False
        #: Whether :meth:`clipboard_unavailable` has been called this run.
        self._clipboard_hinted = False
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
        #: The events :meth:`post_event` queued that are not yet handled and
        #: painted, by ``id``: what :attr:`busy` waits on.
        self._posted: set[int] = set()
        self._parser = InputParser()
        self._loop: asyncio.AbstractEventLoop | None = None
        self._escape_timer: asyncio.TimerHandle | None = None
        #: Turns two presses and a clock into a double-click.  Zero off.
        self._clicks = ClickTracker(double_click)
        #: Milliseconds the pointer rests before a tooltip shows; zero for none.
        self.tooltip_delay = tooltip_delay
        #: The tooltip waiting for the pointer to rest, and the one shown.
        self._tooltip_timer: Repeat | None = None
        self._tooltip: Widget | None = None
        #: Until when (``time.monotonic()``) the next tooltip follows on at
        #: once: one was shown and the pointer moved on.  Zero when not.
        self._tooltip_warm_until = 0.0
        #: Work started by :meth:`spawn`, held so that nothing is collected
        #: mid-flight and everything can be cancelled on the way out.
        self._tasks: set[asyncio.Task[Any]] = set()
        #: Everything :meth:`call_every` is running, armed or waiting for
        #: the loop to start.
        self._repeats: set[Repeat] = set()
        #: True while a handler is running, which is what makes waiting for
        #: input from inside one a diagnosable error -- see :meth:`spawn`.
        self._dispatching = False
        #: ``time.monotonic()`` when the frame loop took the batch it is still
        #: handling or painting, None while it waits for input; and that
        #: batch's first event, described.  Plain fields, so a watchdog on
        #: another thread may read them to tell a stall from an idle loop.
        self.handling_since: float | None = None
        self.handling = ""
        #: The last input events, ``(time.time(), description)``, oldest
        #: first: what was done before a stall.  Timer ticks, wakes and bare
        #: pointer motion are left out, and a paste is kept as its length.
        self.recent_events: deque[tuple[float, str]] = deque(maxlen=64)
        self._signals: list[int] = []
        self._reader_fd: int | None = None
        #: Who the terminal is lent to by :meth:`release_terminal`, or None.
        self._released: Callable[[bytes], bytes] | None = None
        #: The failure that stops the application, raised out of
        #: :meth:`run_async` once the terminal is given back.  See
        #: :meth:`fail`.
        self._failure: BaseException | None = None
        #: When the recent failures happened, for the storm guard.
        self._failure_times: list[float] = []
        #: True while :meth:`report_error` runs, so a failure inside it is
        #: not offered to it again.
        self._reporting = False
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

    @property
    def busy(self) -> bool:
        """Whether an event :meth:`post_event` queued is still to be handled
        and painted: what a driver waits out before it looks, so it sees what
        the event did.  Timer ticks and terminal input do not count -- a fast
        timer would keep the queue from ever being empty."""
        return bool(self._posted)

    def run(self) -> Any:
        """Run the application until it exits, returning :attr:`result`."""
        return asyncio.run(self.run_async())

    async def run_async(self) -> Any:
        """Run the application on the current asyncio loop.

        **Never ends silently on a failure.**  Whatever stopped it -- a
        handler, an effect, a spawned task, a loop callback, a thread -- is
        raised from here once the terminal has been given back, so it reaches
        a normal screen the way any Python program's traceback does.  See
        :meth:`fail`.
        """
        self._loop = asyncio.get_running_loop()
        self._running = True
        self._failure = None
        self._failure_times = []
        self.terminal.start()
        # A Backspace that is 0x7F leaves 0x08 to mean Ctrl+H.
        self._parser.ctrl_h = getattr(self.terminal, "erase", None) == 0x7F
        if self.title:
            self.terminal.set_title(self.title)
        # Both would otherwise print into the alternate screen, which is
        # wiped on the way out: the asyncio default writes a callback's or an
        # unretrieved task's exception to stderr, and so does threading's.
        previous_handler = self._loop.get_exception_handler()
        self._loop.set_exception_handler(self._loop_exception)
        previous_excepthook = threading.excepthook
        threading.excepthook = _ThreadHook(self, previous_excepthook)
        try:
            # An effect queued from outside a dispatch -- a timer callback, or
            # a write to something that is not a widget -- has to be able to
            # nudge a loop that is parked on the event queue.
            SCHEDULER.wake = self._wake
            self._attach_input()
            for repeat in self._repeats:
                repeat._arm(self._loop)
            self._resize(*self.terminal.size)
            try:
                await self.on_start()
            except Exception as error:
                # Nothing to continue into: the desktop is half built.
                self.fail(error, fatal=True)
                raise
            await self._main_loop()
        finally:
            self._running = False
            SCHEDULER.wake = None
            await self._cancel_tasks()
            for repeat in list(self._repeats):
                repeat.cancel()
            self._detach_input()
            try:
                await self.on_stop()
            except Exception as error:
                # Too late for a box: reported, and raised below if nothing
                # else already is.
                self.fail(error, fatal=True)
            self.terminal.stop()
            self._loop.set_exception_handler(previous_handler)
            threading.excepthook = previous_excepthook
            self._loop = None
        if self._failure is not None:
            raise self._failure
        return self.result

    @property
    def title(self) -> str | None:
        """What the terminal's window or tab is called while this runs."""
        return self._title

    @title.setter
    def title(self, title: str | None) -> None:
        self._title = title
        if title and self._running:
            # Out at once: a frame flushes only when a cell changed.
            self.terminal.set_title(title)
            self.terminal.flush()

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

    # -- the clipboard -------------------------------------------------------

    def copy_to_clipboard(self, text: str, *, primary: bool = False) -> None:
        """Put *text* on the clipboard, or on the primary selection.

        Both ways at once (:mod:`navkit.clipboard`): OSC 52 to the terminal,
        which reaches a clipboard over ssh, and the desktop's own tool beside
        it, which reaches one whatever the terminal thinks of OSC 52.  The
        tool runs in an executor and is not waited for.
        """
        if not text:
            return
        self._private_clipboard[primary] = text
        if not self.system_clipboard:
            return
        self.terminal.set_clipboard(text, primary=primary)
        if self._loop is not None and self.terminal.is_tty:
            self._loop.run_in_executor(
                None, functools.partial(clipboard.copy, text, primary=primary)
            )

    def request_clipboard(self, *, primary: bool = False) -> None:
        """Ask for the clipboard; what it holds arrives as a :class:`PasteEvent`.

        So a paste the user asked Navigator for -- Ctrl+V, a middle click --
        and one the terminal made on its own take the one path.  The desktop's
        tool is asked first, since it answers without a prompt; the terminal
        only if there is none.  A terminal that does not answer within
        :data:`CLIPBOARD_ANSWER_TIMEOUT` -- VTE and JediTerm never do -- gets
        the application's own last copy pasted instead, and
        :meth:`clipboard_unavailable` is called once to say so.
        """
        if self._loop is None:
            return
        if not self.system_clipboard:
            # A paste the terminal makes itself (its own Ctrl+Shift+V) is
            # still the desktop's: that never asks the application.
            text = self._private_clipboard[primary]
            if text:
                self.post_event(PasteEvent(text))
            return
        self.spawn(self._read_clipboard(primary))

    async def _read_clipboard(self, primary: bool) -> None:
        text = None
        if self.terminal.is_tty:
            assert self._loop is not None
            text = await self._loop.run_in_executor(
                None, functools.partial(clipboard.paste, primary=primary)
            )
        if text:
            self.post_event(PasteEvent(text))
            return
        if text is None and self.terminal.info.clipboard:
            self._clipboard_asked = True
            self.terminal.query_clipboard(primary=primary)
            await asyncio.sleep(CLIPBOARD_ANSWER_TIMEOUT)
            if not self._clipboard_asked:
                return  # answered, and pasted
            self._clipboard_asked = False
        if text is None:
            private = self._private_clipboard[primary]
            if private:
                self.post_event(PasteEvent(private, origin="private"))

    def clipboard_unavailable(self) -> None:
        """A paste had to use the application's own copy; called once a run.

        The desktop's clipboard could not be read -- no tool for it is
        installed and the terminal did not answer OSC 52 -- so what was
        pasted is the application's last copy, not what another program may
        have copied since.  Nothing here; an application tells its user.
        Called after the paste has been dispatched, so a dialog it opens
        cannot catch the paste.
        """

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
        return self._schedule(Repeat(self, seconds, callback))

    def call_later(
        self, seconds: float, callback: Callable[[], Awaitable[Any]]
    ) -> Repeat:
        """Await *callback* once, *seconds* from now, inside a batch.

        :meth:`call_every` ticking once: the same handle, cancellable until
        the tick has run, and the same path through the event queue.
        """
        if not seconds > 0:
            raise ValueError(f"call_later needs a positive delay, not {seconds!r}")
        if not inspect.iscoroutinefunction(callback):
            raise TypeError(f"call_later needs an async callback, not {callback!r}")
        return self._schedule(Repeat(self, seconds, callback, once=True))

    def _schedule(self, repeat: Repeat) -> Repeat:
        self._repeats.add(repeat)
        if self._running and self._loop is not None:
            repeat._arm(self._loop)
        return repeat

    def _finished(self, task: asyncio.Task[Any]) -> None:
        """Forget a finished task, and let its failure out.

        Through :meth:`fail`, as a handler's is.  It used to be re-raised
        here, inside a done-callback, where asyncio's default handler printed
        it into the alternate screen just before that was wiped -- and the
        application exited without a word.
        """
        self._tasks.discard(task)
        if not task.cancelled() and task.exception() is not None:
            self.fail(task.exception())  # type: ignore[arg-type]

    # -- failures --------------------------------------------------------------

    def fail(self, error: BaseException, *, fatal: bool = False) -> bool:
        """*error* escaped the application's code: report it, or stop.

        **The one funnel every failure goes through**, wherever it was raised:
        a handler, a tick, an effect, a widget's ``render``, a spawned task, a
        loop callback or a thread.  :meth:`log_error` is told first, always.
        Then :meth:`report_error` is offered it, and True from there means the
        application has shown it and carries on.  Otherwise -- *fatal*, no
        loop running, a failure while one is being reported, or too many in
        a row (:data:`ERROR_STORM_LIMIT`) -- the error is kept and the
        application stops, and :meth:`run_async` raises it once the terminal
        is given back.  Returns whether the application carries on.

        The first fatal failure wins; a later one is logged and dropped,
        because the first is the cause and the rest are usually its echo.
        """
        if error is self._failure:
            return False
        with contextlib.suppress(Exception):
            self.log_error(error)
        if not fatal and self._running and self._loop is not None and not self._reporting:
            now = self._loop.time()
            recent = [t for t in self._failure_times if now - t < ERROR_STORM_WINDOW]
            recent.append(now)
            self._failure_times = recent
            if len(recent) <= ERROR_STORM_LIMIT:
                self._reporting = True
                try:
                    if self.report_error(error):
                        return True
                except Exception as during:
                    with contextlib.suppress(Exception):
                        self.log_error(during)
                finally:
                    self._reporting = False
        if self._failure is None:
            self._failure = error
        self.exit()
        return False

    def report_error(self, error: BaseException) -> bool:
        """Show *error* to the user and return True to carry on, or False to stop.

        Called from :meth:`fail`, synchronously and possibly from inside a
        frame's paint, so it must not wait for anything: an application that
        shows a box starts it with ``spawn``.  The default returns False -- stop, and
        let :meth:`run_async` raise it -- which is what a test wants too.
        """
        return False

    def log_error(self, error: BaseException) -> None:
        """Record *error* somewhere that outlives the screen.  Nothing by default.

        Called for every failure :meth:`fail` sees, whether it is then shown,
        stopped on, or dropped as an echo.  Must not raise and must not wait.
        """

    def _loop_exception(self, loop: asyncio.AbstractEventLoop, context: dict[str, Any]) -> None:
        """asyncio's exception handler: a callback or a task nobody awaited failed.

        A context without an exception is a warning -- a task destroyed while
        pending -- and goes to asyncio's own handler, as before.
        """
        error = context.get("exception")
        if isinstance(error, Exception):
            self.fail(error)
        else:
            loop.default_exception_handler(context)

    def _thread_exception(self, args: threading.ExceptHookArgs) -> None:
        """A thread died of *args*: fail on the loop, where the box can open."""
        if not isinstance(args.exc_value, Exception):
            return
        loop = self._loop
        if loop is None:
            self.fail(args.exc_value)
            return
        with contextlib.suppress(RuntimeError):
            loop.call_soon_threadsafe(self.fail, args.exc_value)

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
        self._below_dirty = True
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
        self._below_dirty = True
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
        if not isinstance(event, _Tick | WakeEvent):
            self._posted.add(id(event))
        self._events.put_nowait(event)

    def call_from_thread(self, callback: Callable[..., Any], *args: Any) -> None:
        """Run *callback* on the loop, from any thread, then let it paint.

        The one way for a thread that is not the loop's -- a file-system
        watcher, say -- to reach the widgets: it queues the call and returns
        at once.  Dropped while no loop is running, or once it has closed, so
        a thread outliving the application has nothing to fail over.
        """
        loop = self._loop
        if loop is None or not self._running:
            return

        def run() -> None:
            callback(*args)
            self.post_event(WakeEvent())

        with contextlib.suppress(RuntimeError):  # the loop has closed
            loop.call_soon_threadsafe(run)

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

    def invalidate(self, widget: Widget | None = None) -> None:
        """Request a repaint.  Cheap and safe to call many times per frame.

        *widget* is what changed, when a widget is asking for itself
        (:meth:`Widget.invalidate`).  A change inside the top modal leaves
        what lies beneath it as it was, which lets :meth:`_render` reuse
        that; anything else -- no widget named included -- does not.
        """
        if not self._below_dirty and (
            widget is None or (modal := self.modal) is None or not modal._holds(widget)
        ):
            self._below_dirty = True
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

    # -- lending the terminal ---------------------------------------------------

    @property
    def released(self) -> bool:
        """Whether the terminal is lent out by :meth:`release_terminal`."""
        return self._released is not None

    def release_terminal(self, on_input: Callable[[bytes], bytes]) -> None:
        """Lend the real terminal out, as Midnight Commander's Ctrl+O does.

        The screen and its modes are given back (:meth:`Terminal.suspend`),
        nothing is painted, and every byte read goes raw to *on_input*, which
        returns whatever of it is still the application's -- the bytes after
        the key that ended the loan, once it has called
        :meth:`reclaim_terminal`.  The loop goes on running, so timers, pty
        output and resizes are still handled.
        """
        self._released = on_input
        for event in self._parser.flush():
            self.post_event(event)
        self.terminal.suspend()
        self._cursor_shown = None

    def bell(self) -> None:
        """Ring the terminal's bell -- DOS Navigator's ``Beep`` -- now: a frame
        is written whole within one turn, so nothing of one is pending here."""
        bell = getattr(self.terminal, "bell", None)
        if bell is not None:
            bell()
            self.terminal.flush()

    def redraw(self) -> None:
        """Paint the next frame whole, every cell, whatever the terminal is
        thought to show already -- for a screen something else has written
        over.  Turbo Vision's ``Application^.Redraw``."""
        self._front = None
        self._cursor_shown = None
        self.invalidate()

    def use_terminal_info(self, info: Any) -> None:
        """Use *info* -- a :class:`~navkit.capabilities.TerminalInfo` -- from
        the next frame on, and paint that frame whole.  This is how a running
        application changes its colour depth or glyph tier."""
        self.terminal.info = info
        self.info_revision += 1
        self.redraw()

    def reclaim_terminal(self) -> None:
        """End a :meth:`release_terminal` loan: the screen back, repainted whole."""
        if self._released is None:
            return
        self._released = None
        self.terminal.resume()
        self._front = None
        self._cursor_shown = None
        self._dirty = False
        self.invalidate()

    async def _render(self) -> None:
        """Compose a frame and flush the difference to the terminal."""
        if self._released is not None:
            # Lent out: the frame waits for reclaim_terminal, which repaints.
            return
        if self._min_frame_interval and self._loop is not None:
            overdue = self._min_frame_interval - (self._loop.time() - self._last_frame)
            if overdue > 0:
                await asyncio.sleep(overdue)

        rtl = self.rtl
        if rtl != self._rtl_painted:
            self._rtl_painted = rtl
            self._below_dirty = True
            self._underlay = None
        self._back.rtl = rtl
        modal = self.modal
        underlay = self._underlay
        if (
            underlay is not None
            and not self._below_dirty
            and underlay[0] is modal
            and modal is not None
            and modal.parent is not None
            and modal.visible
            and underlay[1].width == self._back.width
            and underlay[1].height == self._back.height
        ):
            # Only the modal changed: start from what lay beneath it last
            # time and paint the modal and whatever stands above it.  A
            # progress box ticking over a full desktop is otherwise the whole
            # tree, every tick, for a few changed cells.
            self._back.copy_from(underlay[1])
            self._reusing = True
            try:
                self._render_above(modal)
            finally:
                self._reusing = False
        else:
            self._underlay = None
            self._back.clear(self.background)
            if self._root is not None:
                self._composing = True
                try:
                    self._root.render_tree(self._back)
                finally:
                    self._composing = False
        self._below_dirty = False

        shown = self._back.mirrored() if rtl else self._back
        if self.terminal.info.bidi == BIDI_WORDS:
            shown = for_words(shown)
        output = render_diff(self._front, shown, self.terminal.info)
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
        self._front.copy_from(shown)
        self._dirty = False
        self._last_frame = self._loop.time() if self._loop is not None else 0.0

    def _painting_modal(self, widget: Widget) -> None:
        """*widget*, a modal, is about to paint: dim what is already painted.

        Called by :meth:`Widget.render_tree` just before a modal widget paints
        itself.  Everything in the frame so far is what the modal is blocking,
        and everything after it -- the modal, its children, and any overlay a
        control inside it opened, such as a history drop-down -- is painted
        over the dimmed cells at full strength.  Only the *top* modal dims, so
        a dialog opened from a dialog dims the first one once, not twice.

        Rewriting cells after they are painted needs no widget's cooperation,
        which is the reason it is done here rather than by a style state.  It
        only marks the cells ``dim``; what faint *looks* like is decided at the
        edge, in :meth:`TerminalInfo.adapt_style`, because SGR 2 alone is
        ignored for direct-RGB colours by VTE-based terminals.

        It is also where the frame so far is kept as the modal's underlay,
        which :meth:`_render` paints over instead of the whole tree while
        nothing beneath the modal changes.
        """
        if widget is not self.modal or self._reusing:
            return
        if self.dim_modal and widget.dims_behind:
            self._dim_behind()
        if self._composing:
            underlay = ScreenBuffer(self._back.width, self._back.height)
            underlay.copy_from(self._back)
            self._underlay = (widget, underlay)

    def _dim_behind(self) -> None:
        dimmed = self._dimmed

        def dim(style: Style) -> Style:
            twin = dimmed.get(style)
            if twin is None:
                if len(dimmed) >= DIMMED_STYLES_LIMIT:
                    dimmed.clear()
                twin = dimmed[style] = style.derive(dim=True)
            return twin

        self._back.restyle(dim)

    def _render_above(self, modal: Widget) -> None:
        """Paint *modal* and everything painted after it, over its underlay.

        The tail of a whole-tree paint, in the same order: the modal's own
        subtree, then -- walking up -- each ancestor's later children and its
        :meth:`~Widget.render_after`.  What came before is the underlay.
        """
        path = [modal]
        while path[-1].parent is not None:
            path.append(path[-1].parent)
        path.reverse()  # the root first
        surfaces: list[Surface] = []
        surface: Surface = self._back
        for widget in path[:-1]:
            surface = surface.view(widget.x, widget.y, widget.width, widget.height)
            surfaces.append(surface)
        modal.render_tree(surfaces[-1])
        for depth in range(len(path) - 2, -1, -1):
            parent, child, own = path[depth], path[depth + 1], surfaces[depth]
            for later in parent.children[parent.children.index(child) + 1:]:
                later.render_tree(own)
            parent._guarded(parent.render_after, own)

    def _cursor(self) -> tuple[int, int, str] | None:
        """Screen position and shape of the terminal cursor, or None for none.

        **Shown exactly where the keys go.** The widgets asked are the ones
        on the focus path -- the same walk :meth:`Widget.dispatch_key` makes,
        so the same modal, the same visibility test and the same answer of
        "nobody" when nothing holds the keyboard. A caret on a widget that
        could not receive what is typed into it would be a lie told once per
        frame.

        **The nearest one with a caret wins**, head first, which is the order
        a key is offered in. A widget holding the keyboard with no caret of
        its own -- a list -- declines the printable keys, they walk up, and an
        ancestor that types them somewhere is where they are really going.
        """
        scope = self.modal or self._root
        if scope is None:
            return None
        path = scope._focus_path()
        for widget in path:
            position = widget.cursor_position()
            if position is not None:
                break
        else:
            return None
        x, y = position
        if not (0 <= x < widget.width and 0 <= y < widget.height):
            return None
        offset_x, offset_y = widget.offset()
        x, y = offset_x + widget.x + x, offset_y + widget.y + y
        if not (0 <= x < self._back.width and 0 <= y < self._back.height):
            return None
        if self._back.rtl:
            x = self._mirror_x(x, widget)
        return x, y, widget.style_property("caret", "default")

    @property
    def rtl(self) -> bool:
        """Whether the screen is mirrored, reading right to left (:attr:`direction`)."""
        if self.direction == "auto":
            return i18n.is_rtl()
        return self.direction == "rtl"

    def _mirror_x(self, x: int, widget: Widget | None) -> int:
        """Screen column *x* of the frame as painted, where a mirrored screen
        shows it -- or, since mirroring is its own inverse, the other way.

        Inside a widget that keeps left to right (:attr:`Widget.mirrors`) the
        column is reversed within that widget first, as its cells were.
        """
        keeper = widget.unmirrored() if widget is not None else None
        if keeper is not None:
            left = keeper.offset()[0] + keeper.x
            x = 2 * left + keeper.width - 1 - x
        return self._back.width - 1 - x

    def _unmirror(self, event: Event) -> Event:
        """*event*, a mouse report in screen columns, in the frame's own.

        Left and Right trade places too, for whatever holds the keyboard on a
        mirrored screen (:meth:`Widget.arrows_mirrored`): the next menu, the
        next column, the next cell is to the left there.

        Done as the event comes off the queue -- once, so the double-click
        and context menu derived from it are already in the frame's columns.
        """
        if isinstance(event, KeyEvent) and self._back.rtl and event.key in _ARROW_MIRROR:
            scope = self.modal or self._root
            path = scope._focus_path() if scope is not None else []
            head = path[0] if path else scope  # nothing focused: keys go to the root
            if head is not None and head.unmirrored() is None and head.arrows_mirrored():
                return dataclasses.replace(event, key=_ARROW_MIRROR[event.key])
            return event
        if not (isinstance(event, MouseClickEvent) and self._back.rtl):
            return event
        x = self._back.width - 1 - event.x
        scope = self.modal or self._root
        target = None
        if scope is not None:
            dx, dy = scope.offset() if scope is not self._root else (0, 0)
            target = scope.widget_at(x - dx, event.y - dy)
        keeper = target.unmirrored() if target is not None else None
        if keeper is not None:
            left = keeper.offset()[0] + keeper.x
            x = 2 * left + keeper.width - 1 - x
        return dataclasses.replace(event, x=x)

    def _resize(self, width: int, height: int) -> None:
        self._clicks.reset()  # the layout moved out from under the pointer
        self._below_dirty = True
        self._back.resize(width, height, self.background)
        self._front = None  # sizes differ -- force a full repaint
        if self._root is not None:
            self._root.layout(width, height)
        self._dirty = True

    # -- event loop ---------------------------------------------------------

    async def _main_loop(self) -> None:
        self._flush_effects()
        await self._paint()
        while self._running:
            event = await self._events.get()
            batch = [id(event)]
            event = self._unmirror(event)
            self.handling_since, self.handling = time.monotonic(), describe_event(event)
            await self._handle(event)
            # Drain whatever else arrived in the meantime: a paste or a mouse
            # drag should cost one frame, not one frame per event.  A handler
            # that awaits lets the loop's other work run -- reading input,
            # pty output, timers -- but cannot produce a frame, because
            # ``_render`` is only ever awaited from here.
            while self._running and not self._events.empty():
                event = self._events.get_nowait()
                batch.append(id(event))
                await self._handle(self._unmirror(event))
            if self._running:
                self._flush_effects()
            if self._running and self._dirty:
                await self._paint()
            self._posted.difference_update(batch)
            self.handling_since = None

    async def _paint(self) -> None:
        """:meth:`_render`, where a failure always stops the application.

        A widget's own ``render`` failing is caught in
        :meth:`Widget.render_tree` and reported without stopping anything; what
        reaches here is the frame machinery itself, and a box could not be
        painted over it.
        """
        try:
            await self._render()
        except Exception as error:
            self.fail(error, fatal=True)
            raise

    def _flush_effects(self) -> None:
        """Run the reactions this batch of events queued, before painting.

        Effects assign reactive attributes, so they belong here rather than
        inside :meth:`_render`: whatever they change is part of the frame that
        is about to be composed.  A failing reaction goes to :meth:`fail`
        the same way a failing event handler does.
        """
        # Again after a failure that was reported: the effects queued behind
        # the one that failed are owed this frame too.  Each pass consumes the
        # failing one, and the storm guard ends a run of them.
        while True:
            try:
                flush_effects()
                return
            except Exception as error:
                if not self.fail(error):
                    raise

    async def _handle(self, event: Event) -> None:
        if isinstance(event, WakeEvent):
            return
        if not isinstance(event, _Tick):
            # Input, or anything posted, may change what lies beneath the
            # modal without a widget there asking: the focus path's key bar,
            # a command enabled by a field.  Only a timer's tick is trusted to
            # say through invalidate() what it changed.
            self._below_dirty = True
        if not isinstance(event, _Tick | ModifiersEvent) and not (
            isinstance(event, MouseClickEvent) and _is_plain_motion(event)
        ):
            self.recent_events.append((time.time(), describe_event(event)))
        if isinstance(event, _Tick):
            await self._tick(event.repeat)
            return
        if isinstance(event, ResizeEvent):
            self._resize(event.width, event.height)
        if isinstance(event, ModifiersEvent):
            # A fact about the keyboard rather than something to act on, kept
            # the way the pointer's position is: nothing is offered it.
            self.modifiers = event.modifiers
            return
        # Any input takes a tooltip away, shown or waiting; only the pointer
        # coming to rest (below) asks for one again.  The pointer moving off
        # one shown keeps the next quick; anything else makes it wait again.
        motion = isinstance(event, MouseClickEvent) and _is_plain_motion(event)
        if motion and self._tooltip is not None:
            self._tooltip_warm_until = time.monotonic() + TOOLTIP_FOLLOW_ON
        elif not motion:
            self._tooltip_warm_until = 0.0
        self._drop_tooltip()
        if isinstance(event, KeyEvent) and not self.chord and self._is_show_tooltip(event):
            # Read off the application's own table even past a modal, which
            # that table otherwise stands aside for: a dialog is where it is
            # most wanted.
            self.show_focus_tooltip()
            return
        # Saved and restored rather than set and cleared: `_handle' returns
        # early for a claimed event and re-enters itself for a double click,
        # so a plain reset would report "not dispatching" while the outer call
        # still is.
        if isinstance(event, MouseClickEvent):
            self.pointer = (event.x, event.y)
        if isinstance(event, MouseClickEvent) and _is_plain_motion(event):
            # The pointer moving with no button held.  A fact the application
            # keeps rather than an event anybody is offered: mode 1003 reports
            # one per cell crossed, every existing ``on_mouse_click`` was
            # written for presses, releases and drags, and all a motion can
            # mean on its own is "the pointer is here now".
            self._hover(event)
            if self.tooltip_delay > 0:
                delay = self.tooltip_delay / 1000
                if time.monotonic() < self._tooltip_warm_until:
                    delay = min(delay, TOOLTIP_FOLLOW_ON_DELAY)
                self._tooltip_timer = self.call_later(delay, self._show_tooltip)
            return
        dispatching, self._dispatching = self._dispatching, True
        try:
            if await self.on_event(event):
                return
            if isinstance(event, KeyEvent):
                if await self._chord_key(event):
                    return
                # Dispatching on the modal rather than the root is the whole
                # of keyboard exclusivity: the walk runs from the focused
                # widget up to whatever it was called on, so it neither starts
                # outside the modal nor bubbles past it.
                target = self.modal or self._root
                if await self._run_key(event):
                    return
                if not await self.on_key(event) and target is not None:
                    await target.dispatch_key(event)
            elif isinstance(event, MouseClickEvent):
                # Counted from the press itself, before it is delivered and
                # whatever claims it: whether a widget consumed a press says
                # nothing about whether the user clicked twice.  A
                # DoubleClickEvent is a conclusion *about* presses and is
                # never counted as one, which bounds the recursion below at
                # one level.
                derived = isinstance(event, (DoubleClickEvent, ContextMenuEvent))
                clicks = 0 if derived else self._clicks.press(event, self._now())
                # Taken before delivery: a press that grabs the mouse (a
                # drag starting) is not asking for a menu.
                captured_before = self._capture is not None
                # A press says where the pointer is as well, which keeps the
                # hover right on a terminal that never reports plain motion.
                if event.action == "press":
                    self._hover(event)
                await self._deliver_mouse(event)
                if clicks == 2:
                    # Inline rather than posted, so cause and effect stay
                    # adjacent: the press's own release is usually already in
                    # the queue from the same read, and queueing would deliver
                    # it in between.  Through `_handle' so `on_event' sees it,
                    # as it sees the escape key navkit manufactures.
                    await self._handle(DoubleClickEvent.of(event))
                if (
                    not derived
                    and event.button == "right"
                    and event.action == "press"
                    and not captured_before
                    and self._capture is None
                ):
                    # After the press and inline, as the double-click is:
                    # whoever gives the right button a meaning of its own has
                    # had it, and a press that took the capture declines.
                    await self._handle(ContextMenuEvent.of(event))
            elif isinstance(event, KeyReleaseEvent):
                # The focused widget alone, and no key table or walk up: a
                # release means something only to whoever took the press.
                # Inside the modal, as a key would be, so a dialog that opened
                # between press and release does not hand it to what is under.
                focused = self.focused
                if focused is not None and (self.modal is None or self.modal._holds(focused)):
                    handler = getattr(focused, event.handler, None)
                    if handler is not None:
                        await _call(focused, event, handler)
            elif isinstance(event, ResizeEvent):
                await self.on_resize(event)
            elif isinstance(event, PasteEvent):
                if event.origin == "answer":
                    if not self._clipboard_asked:
                        return  # too late: the private copy went instead
                    self._clipboard_asked = False
                # The application first, as with a key, and then where the
                # keyboard is -- the modal's focused line, under a dialog.
                if not await self.on_paste(event):
                    target = self.modal or self._root
                    if target is not None:
                        await target.dispatch_paste(event)
                if event.origin == "private" and not self._clipboard_hinted:
                    self._clipboard_hinted = True
                    self.clipboard_unavailable()
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
        except Exception as error:
            if not self.fail(error):
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
        if repeat.once:
            repeat.cancel()
        dispatching, self._dispatching = self._dispatching, True
        try:
            await repeat.callback()
        except Exception as error:
            if not self.fail(error):
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

    # -- tooltips ---------------------------------------------------------------

    def tooltip_here(self) -> str:
        """The tooltip for where the pointer is, or ``""``.

        Asked of the widget under the pointer (:attr:`hovered`) and then its
        ancestors, nearest first, each in its own coordinates
        (:meth:`Widget.tooltip_at`): a widget without one shows what it sits
        in says -- unless it is one that stops the walk
        (:attr:`Widget.tooltip_passes`).
        """
        if self.pointer is None:
            return ""
        return self.tooltip_from(self.hovered, *self.pointer)

    @staticmethod
    def tooltip_from(widget: Widget | None, x: int, y: int) -> str:
        """The tooltip at screen cell *x*, *y*, asked of *widget* -- what is
        painted there -- and then its ancestors, nearest first, each in its
        own coordinates, until one answers or stops the walk
        (:attr:`Widget.tooltip_passes`)."""
        while widget is not None:
            ox, oy = widget.offset()
            text = widget.tooltip_at(x - ox - widget.x, y - oy - widget.y)
            if text or not widget.tooltip_passes:
                return text
            widget = widget.parent
        return ""

    async def _show_tooltip(self) -> None:
        """The pointer rested: put up what it rests on says, if anything.

        As the root's last child, over everything -- a modal too, since what
        stands after a modal is painted after it.
        """
        self._tooltip_timer = None
        text = self.tooltip_here()
        if not text or self._root is None or self.pointer is None:
            return
        self._tooltip = self.overlay(Tooltip(text, self.pointer))

    def _is_show_tooltip(self, event: KeyEvent) -> bool:
        binding = commands.key_table(type(self)).get(event.name)
        return binding is not None and isinstance(commands.command_of(binding), ShowTooltip)

    async def on_show_tooltip(self, event: ShowTooltip) -> bool:
        self.show_focus_tooltip()
        return True

    def show_focus_tooltip(self) -> bool:
        """Put up the tooltip of where the keyboard is, beside it -- the
        nearest widget on the focus path's :meth:`Widget.tooltip_anchor`,
        asked of whatever is painted there and its ancestors as the pointer
        would be.  False, showing nothing, where there is none."""
        self._drop_tooltip()
        scope = self.modal or self._root
        if scope is None or self._root is None:
            return False
        path = scope._focus_path() or [scope]
        widget = path[0]
        ax, ay = widget.tooltip_anchor()
        ox, oy = widget.offset()
        x, y = ox + widget.x + ax, oy + widget.y + ay
        # What is painted there: a descendant of the focused widget, if one
        # is (an open menu's box), else the widget itself.
        found = widget.widget_at(widget.x + ax, widget.y + ay) or widget
        text = self.tooltip_from(found, x, y)
        if not text:
            return False
        self._tooltip = self.overlay(Tooltip(text, (x, y)))
        return True

    def _drop_tooltip(self) -> None:
        """Forget the tooltip waiting to show and take down the one shown."""
        if self._tooltip_timer is not None:
            self._tooltip_timer.cancel()
            self._tooltip_timer = None
        tooltip, self._tooltip = self._tooltip, None
        if tooltip is not None and tooltip.parent is not None:
            tooltip.parent.remove(tooltip)

    def _hover(self, event: MouseClickEvent) -> None:
        """Move :attr:`hovered` to whatever is under *event*'s position.

        Confined to the modal the way delivery is: outside it nothing is
        hovered, because nothing out there is reachable.
        """
        if self._capture is not None:
            return
        modal = self.modal
        if modal is not None:
            dx, dy = modal.offset()
            self.hovered = modal.widget_at(event.x - dx, event.y - dy)
        elif self._root is not None:
            self.hovered = self._root.widget_at(event.x, event.y)

    async def _dispatch_mouse(self, event: MouseClickEvent) -> None:
        """Route a mouse action into the tree, or into the modal alone.

        The mouse is where modality costs something, because it routes by
        position rather than by focus: every widget under the pointer is on
        the path, whether or not it is supposed to be reachable. So the event
        is moved into the modal's parent's frame and offered there, and one
        that lands outside the modal reaches nothing at all -- not the widgets
        underneath, and not the modal either, whose coordinates it is not in.

        Dismissing on an outside click is a *policy*, and belongs to whatever
        widget wants it: a press that misses the modal is offered to the modal
        itself as a :class:`ClickOutsideEvent`, and what it does then is its
        own business.
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
        elif (
            event.action == "press"
            and not event.is_wheel
            and not isinstance(event, (DoubleClickEvent, ContextMenuEvent))
        ):
            outside = ClickOutsideEvent.of(local).translated(-modal.x, -modal.y)
            handler = getattr(modal, outside.handler, None)
            if handler is not None:
                await _call(modal, outside, handler)

    # -- commands ------------------------------------------------------------

    def _key_tables(self) -> list[dict[str, commands.Binding]]:
        """The tables a key is looked up in, in the order it is: the
        application's (not past a modal), then the focus path's, nearest first."""
        scope = self.modal or self._root
        tables = [] if self.modal is not None else [commands.key_table(type(self))]
        if scope is not None:
            path = scope._focus_path() or [scope]
            tables += [commands.key_table(type(widget)) for widget in path]
        return tables

    async def _chord_key(self, event: KeyEvent) -> bool:
        """A key that begins, continues or ends a chord; False for any other.

        A key completing a chord runs the first binding of it found where a
        key is looked up.  One that neither completes nor continues the chord
        held is swallowed with it -- it was typed as the chord's second key,
        not as text.  Only the tables on the current path count, so Ctrl+K
        is held for an editor's chords and still reaches a program in the
        console.
        """
        if event.name in ("", None):
            return False
        sequence = f"{self.chord} {event.name}" if self.chord else event.name
        tables = self._key_tables()
        if self.chord:
            self.chord = ""
            for table in tables:
                binding = table.get(sequence)
                if binding is not None:
                    await commands.run(self, binding)
                    return True
        if any(sequence in commands.chord_prefixes(table) for table in tables):
            self.chord = sequence
            return True
        return bool(sequence != event.name)

    async def _run_key(self, event: KeyEvent) -> bool:
        """The application's own key table, before the tree and never past a
        modal."""
        if self.modal is not None:
            return False
        binding = commands.key_table(type(self)).get(event.name)
        return binding is not None and await commands.run(self, binding)

    async def run_command(
        self, binding: commands.Binding, start: Widget | None = None
    ) -> bool:
        """Ask for a command as if its key had been pressed.

        What a key bar button and a menu item call.  False if the command is
        disabled or nobody claimed it.  *start* asks from a widget other than
        the focus -- a context menu runs its choice from the widget it was
        opened over -- see :func:`navkit.commands.origin`.
        """
        return await commands.run(self, binding, start)

    def command_enabled(
        self, binding: commands.Binding, start: Widget | None = None
    ) -> bool:
        """Whether asking for *binding*'s command now would run it.

        *start* asks from a widget other than the focus -- see
        :func:`navkit.commands.origin`.
        """
        return commands.enabled(self, binding, start)

    def command_checked(
        self, binding: commands.Binding, start: Widget | None = None
    ) -> bool | None:
        """Whether *binding*'s command is a toggle that is on now -- see
        :func:`navkit.commands.checked`."""
        return commands.checked(self, binding, start)

    def bindings(self, start: Widget | None = None) -> dict[str, commands.Command]:
        """Every key that asks for a command right now -- what a key bar shows."""
        return commands.bindings(self, start)

    def enables(self, command: commands.Command) -> bool:
        """Whether the application will run *command* now.  See
        :meth:`Widget.enables`."""
        return not self.refusal(command)

    def refusal(self, command: commands.Command) -> str:
        """Why the application will not run *command* now, ``""`` when it
        will.  See :meth:`Widget.refusal`."""
        return ""

    def command_disabled_reason(
        self, binding: commands.Binding, start: Widget | None = None
    ) -> str:
        """Why *binding*'s command cannot run now, ``""`` when it can or
        nobody says -- see :func:`navkit.commands.disabled_reason`."""
        return commands.disabled_reason(self, binding, start)

    def checks(self, command: commands.Command) -> bool | None:
        """Whether *command* is a toggle that is on now.  See
        :meth:`Widget.checks`."""
        return None

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

    async def on_paste(self, event: PasteEvent) -> bool:
        """A paste, before the focused widget is offered it; True keeps it."""
        return False

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
        if self._released is not None:
            # Raw, to whoever the terminal was released to; what it hands
            # back -- whatever followed the key that reclaimed it -- is ours.
            data = self._released(data)
            if not data:
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
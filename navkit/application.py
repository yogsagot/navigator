"""The application object and its event loop.

:class:`Application` is the only place in navkit that owns an asyncio loop.  It
wires the terminal's input to an event queue, dispatches events to the widget
tree, and repaints the screen once per batch of events rather than once per
event -- so a burst of keystrokes or a fast mouse drag costs a single frame.

The order within one turn of the loop is fixed: dispatch the whole batch, run
the reactive effects it queued, then paint.  Effects may change state and so
must run before the frame is composed; nothing reactive runs during the paint
itself.

The methods are split by feature into mixins (:class:`navkit.widget.Mixin`)
in :mod:`navkit.app` -- ``focus``, ``painting``, ``dispatch``, ``input`` --
imported just before the class, since each takes what it shares from here.
What stays here is the state, the lifecycle, the clipboard, failures, holding
the mouse and ``enables``/``checks``; the globals the tests patch on this
module (``REPEAT_DELAY``, ``CLIPBOARD_ANSWER_TIMEOUT``) are read by these.

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
import functools
import inspect
import math
import threading
import weakref
from collections import deque
from collections.abc import Awaitable, Callable, Coroutine
from dataclasses import dataclass
from typing import Any

from navkit.events import Event, KeyEvent, MouseClickEvent, PasteEvent, ResizeEvent, WakeEvent
from navkit.glyphs import DEFAULT_MARKS
from navkit.reactive import SCHEDULER, reactive
from navkit.graphics import GraphicsLayer
from navkit.screen import ScreenBuffer
from navkit.style import DEFAULT_STYLE, Style
from navkit.stylesheet import Stylesheet
from navkit.terminal import InputParser, Terminal
from navkit import clipboard, commands
from navkit.widget import Widget, check_handlers

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
#: How long a terminal's paste is held while the pointer rests on a widget
#: that claims the middle button, waiting for the release that says it was
#: VTE's middle click (see :meth:`Application._hold_paste`).
MIDDLE_PASTE_WINDOW = 0.5

#: A held button's repetition (:meth:`Application.hold_mouse`): Turbo Vision's
#: ``evMouseAuto``, which came ``RepeatDelay`` (8) ticks of the 18.2 Hz clock
#: after the press and then one every tick while the button stayed down
#: (``DRIVERS.PAS``).  DN zeroed ``RepeatDelay`` around a few of its loops (the
#: viewer's quarters, the panel, the dBase viewer), which repeated as fast as
#: the machine polled the mouse; a departure: Navigator waits the same first
#: delay there too, since on a modern loop no delay turns a click into a page.
REPEAT_DELAY = 8 / 18.2
REPEAT_EVERY = 1 / 18.2

#: How long a paste waits for the terminal to answer an OSC 52 query before it
#: pastes the application's own copy instead.  A terminal that answers does so
#: in milliseconds; one that is slower is asking its user first (Ghostty's
#: ``clipboard-read = ask``), and one that never answers (VTE, JediTerm) is
#: the case this is for.
CLIPBOARD_ANSWER_TIMEOUT = 0.5

#: How long the terminal has to answer :meth:`Terminal.query_graphics` before
#: it is taken to draw no pictures.  Its last question is one every terminal
#: answers, so this is only for one that answers nothing at all.
GRAPHICS_ANSWER_TIMEOUT = 1.0

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


class MouseHold:
    """A held mouse button repeating, :meth:`Application.hold_mouse`'s.

    *step* is awaited as ``step(x, y, auto)`` with the pointer's last place in
    the widget's coordinates: ``auto`` True for a tick of the clock (TV's
    ``evMouseAuto``), False for a move when *moves* is set (its
    ``evMouseMove``).  It returning False stops the ticks; the capture stays
    until the release, as DN's loop went on waiting for it.  *done*, if
    given, is called once when the hold ends, however it ends.
    """

    def __init__(
        self,
        app: Application,
        widget: Widget,
        step: Callable[[int, int, bool], Awaitable[bool | None]],
        x: int,
        y: int,
        delay: float,
        every: float,
        moves: bool,
        done: Callable[[], Any] | None = None,
    ) -> None:
        self.widget = widget
        self.step = step
        self.x, self.y = x, y
        self.moves = moves
        #: How many ticks have been delivered.
        self.ticks = 0
        #: True once the hold has ended.
        self.cancelled = False
        self._done = done
        self._app = app
        self._every = every
        self._timer: Repeat | None = app.call_later(delay, self._start)

    def cancel(self) -> None:
        """End the hold: no more ticks or moves, and *done* called.  Idempotent."""
        if self.cancelled:
            return
        self.cancelled = True
        self._stop()
        if self._done is not None:
            self._done()

    def _stop(self) -> None:
        if self._timer is not None:
            self._timer.cancel()
            self._timer = None

    async def _start(self) -> None:
        if self.cancelled:
            return
        self._timer = self._app.call_every(self._every, self._tick)
        await self._tick()

    async def _tick(self) -> None:
        if self.cancelled or self._app._hold is not self:
            self._stop()
            return
        self.ticks += 1
        if await self.step(self.x, self.y, True) is False:
            self._stop()

    async def _moved(self, x: int, y: int) -> None:
        self.x, self.y = x, y
        if self.moves and not self.cancelled:
            await self.step(x, y, False)


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

# The class's methods, split by feature into mixins (navkit.widget.Mixin).
# Imported here, after everything above, because each of them imports what it
# needs of this module from this module: the names exist by now.
from navkit.app.focus import Focus
from navkit.app.painting import Painting
from navkit.app.dispatch import Dispatch
from navkit.app.input import Input


class Application(Focus, Painting, Dispatch, Input):
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
    #: Whether the terminal's window has the focus: True or False as its last
    #: focus report said (:class:`FocusEvent`), ``None`` while it has said
    #: nothing -- a terminal without focus reports, or the screen just taken
    #: back from a :meth:`release_terminal`.  What decides whether a
    #: :meth:`notify` is worth sending.
    terminal_focused: bool | None = reactive(None)
    #: The keys of a chord pressed so far -- ``"ctrl+k"`` after Ctrl+K, when
    #: some table on the way to the focus binds a chord beginning with it --
    #: or empty.  The next key completes the chord or abandons it, and is
    #: swallowed either way, as WordStar's was.  Reactive, so whatever shows
    #: that a chord is pending (an editor's info line) follows it.
    chord: str = reactive("")
    #: Given every key and paste before anything handles it, when set: what a
    #: recorder of keystrokes hangs off (Navigator's macros).  Plain, and
    #: called on the loop; it must not raise or block.
    input_tap: Callable[[Event], None] | None = None
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
        #: What the next frame has to repaint: the widgets that asked, when
        #: every one of them ``paints_alone`` (:meth:`_render` then repaints
        #: only their cells), or None for the whole frame -- anything else
        #: asking, input, a modal coming or going, a resize.
        self._damage: set[Widget] | None = None
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
        #: The held button repeating for the capture, or None
        #: (:meth:`hold_mouse`).
        self._hold: MouseHold | None = None
        self._running = False
        self._dirty = True
        self._events: asyncio.Queue[Event] = asyncio.Queue()
        #: The events :meth:`post_event` queued that are not yet handled and
        #: painted, by ``id``: what :attr:`busy` waits on.
        self._posted: set[int] = set()
        self._parser = InputParser()
        self._parser.charset = getattr(getattr(self.terminal, "info", None), "charset", "utf-8")
        # The console's programs write in the terminal's charset too.
        from navkit import console

        console.CHARSET = self._parser.charset
        #: The pictures on the screen (:mod:`navkit.graphics`).
        self._graphics = GraphicsLayer()
        #: What the terminal has answered to :meth:`Terminal.query_graphics`
        #: so far, while it is being asked; None otherwise.
        self._graphics_answers: dict[str, Any] | None = None
        self._graphics_timer: asyncio.TimerHandle | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._escape_timer: asyncio.TimerHandle | None = None
        #: Turns two presses and a clock into a double-click.  Zero off.
        self._clicks = ClickTracker(double_click)
        #: The middle button is down (a press seen, its release not yet).
        self._middle_down = False
        #: A terminal paste held back by :meth:`_hold_paste`, its timer, and
        #: the one let go, which is not held again.
        self._held_paste: tuple[PasteEvent, Repeat] | None = None
        self._paste_let_go: PasteEvent | None = None
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
        #: The size the last resize asked for, laid out or still queued: a
        #: ``SIGWINCH`` that names it again changes nothing.
        self._asked_size: tuple[int, int] | None = None
        self._min_frame_interval = 1.0 / max_fps if max_fps > 0 else 0.0
        self._last_frame = 0.0
        #: What the last frame left the terminal's cursor doing, so a frame
        #: that changes nothing about it emits nothing about it either.
        self._cursor_shown: tuple[int, int, str, tuple[int, int, int] | None] | None = None
        #: The cursor colour last sent (OSC 12), ``None`` for the terminal's
        #: own.  Kept apart from the position: a hidden cursor keeps its
        #: colour, and a redraw does not change what the terminal holds.
        self._caret_color: tuple[int, int, int] | None = None

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
            self._ask_graphics()
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

    # -- notifications -------------------------------------------------------

    def notify(self, title: str, body: str, method: str | None = None, *, app_name: str = "") -> bool:
        """A desktop notification of *title* and *body* (:mod:`navkit.notify`),
        by *method* -- ``"osc9"``, ``"osc777"``, ``"notify-send"`` or
        ``"none"`` -- else as the terminal's info says; *app_name* is what
        ``notify-send`` files it under.  Sent whatever the
        focus; a caller that wants it only for an absent user asks
        :attr:`terminal_focused` first.  Whether it went out."""
        from navkit import notify

        return notify.send(self, title, body, method or self.terminal.info.notifications,
                           app_name=app_name)

    # -- the clipboard -------------------------------------------------------

    def private_clipboard(self, primary: bool = False) -> str:
        """The application's own last copy (or primary selection), "" when none."""
        return self._private_clipboard[primary]

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

    def hold_mouse(
        self,
        widget: Widget,
        event: MouseClickEvent,
        step: Callable[[int, int, bool], Awaitable[bool | None]],
        *,
        delay: float | None = None,
        every: float | None = None,
        moves: bool = False,
        done: Callable[[], Any] | None = None,
    ) -> MouseHold:
        """Capture the mouse for *widget* and repeat *step* while the button is held.

        Turbo Vision's ``repeat ... until not MouseEvent(Event, evMouseAuto)``
        loop, which a terminal cannot give by itself: it reports a press,
        moves and a release, and nothing while the pointer rests.  So a clock
        does: *delay* after the press (:data:`REPEAT_DELAY`), then every
        *every* (:data:`REPEAT_EVERY`), ``step(x, y, True)`` is awaited inside
        a batch, at the pointer's last place.  With *moves*, a move awaits
        ``step(x, y, False)`` too.  The press itself is the caller's to act
        on, from the handler that called this with it (*event*).  *done* is
        called once when the hold ends.

        While it holds, the captured moves and the release go to it and not
        to *widget*'s handler; a double click still reaches the handler.  It
        ends with whatever ends the capture: the release, :meth:`release_mouse`,
        *widget* unmounted, or a modal opening that does not hold it.
        """
        self._set_capture(None)
        self._set_capture(widget)
        hold = MouseHold(
            self, widget, step, event.x, event.y,
            REPEAT_DELAY if delay is None else delay,
            REPEAT_EVERY if every is None else every,
            moves,
            done,
        )
        self._hold = hold
        return hold

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

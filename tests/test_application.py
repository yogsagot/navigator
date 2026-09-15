"""The application lifecycle and its event loop."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

from navkit.application import Application, ClickTracker
from navkit.events import (
    DoubleClickEvent,
    Event,
    KeyEvent,
    MouseEvent,
    PasteEvent,
    ResizeEvent,
)
from navkit.reactive import effect, peek, reactive
from navkit.style import Style
from navkit.stylesheet import parse
from navkit.terminal import HIDE_CURSOR, SHOW_CURSOR
from navkit.widget import Widget

from conftest import FakeTerminal, RecordingWidget, run_app


def test_run_starts_and_restores_the_terminal(terminal):
    app = Application(RecordingWidget(), terminal=terminal, title="Navigator")
    run_app(app)
    assert (terminal.started, terminal.stopped) == (True, True)
    assert terminal.title == "Navigator"


def test_exit_result_is_returned(terminal):
    app = Application(RecordingWidget(), terminal=terminal)
    assert run_app(app, [lambda a: a.exit("bye")]) == "bye"


def test_the_first_frame_is_painted_before_any_event(terminal):
    root = RecordingWidget(fill="#")
    run_app(Application(root, terminal=terminal))
    assert root.renders >= 1
    assert len(terminal.frames) == 1
    assert "#" in terminal.frames[0]


def test_keys_reach_the_root_widget(terminal):
    root = RecordingWidget()
    run_app(
        Application(root, terminal=terminal),
        [KeyEvent("a", "a"), KeyEvent("q", ctrl=True)],
    )
    assert root.keys == ["a", "ctrl+q"]


def test_mouse_events_reach_the_root_widget(terminal):
    root = RecordingWidget(width=40, height=10)
    run_app(Application(root, terminal=terminal), [MouseEvent(3, 4, "left")])
    assert root.mice == [(3, 4)]


def test_application_hooks_see_events_before_the_widgets(terminal):
    seen = []

    class App(Application):
        async def on_event(self, event):
            seen.append(type(event).__name__)
            return isinstance(event, KeyEvent) and event.key == "swallowed"

        async def on_key(self, event):
            return event.key == "handled"

        async def on_paste(self, event):
            seen.append(event.text)

    root = RecordingWidget()
    run_app(
        App(root, terminal=terminal),
        [
            KeyEvent("swallowed"),
            KeyEvent("handled"),
            KeyEvent("passed"),
            PasteEvent("text"),
        ],
    )
    assert root.keys == ["passed"]  # the other two never got there
    assert "PasteEvent" in seen and "text" in seen


def test_a_batch_of_events_costs_a_single_frame(terminal):
    root = RecordingWidget()

    def burst(app):
        # All five are queued before the loop wakes, so they form one batch.
        for index in range(5):
            app.post_event(KeyEvent(str(index)))

    run_app(Application(root, terminal=terminal), [burst])
    assert root.keys == ["0", "1", "2", "3", "4"]
    # One render for the initial paint, one for the whole batch.
    assert root.renders == 2


def test_an_unchanged_frame_writes_nothing(terminal):
    class Quiet(RecordingWidget):
        async def on_key(self, event):
            self.invalidate()  # asks for a repaint, but paints the same thing
            return True

    run_app(Application(Quiet(), terminal=terminal), [KeyEvent("a")])
    assert len(terminal.frames) == 1  # the diff was empty, so nothing was sent


def test_nothing_is_rendered_when_no_repaint_was_asked_for(terminal):
    class Silent(RecordingWidget):
        async def on_key(self, event):
            return True  # handled, and does not invalidate

    root = Silent()
    run_app(Application(root, terminal=terminal), [KeyEvent("a")])
    assert root.renders == 1


def test_invalidate_wakes_an_idle_loop(terminal):
    root = RecordingWidget(fill="a")

    def repaint(app):
        root.fill_char = "b"
        app.invalidate()

    run_app(Application(root, terminal=terminal), [repaint])
    assert len(terminal.frames) == 2
    assert "b" in terminal.frames[1]


def test_resize_relayouts_and_fully_repaints(terminal):
    root = RecordingWidget()
    run_app(Application(root, terminal=terminal), [ResizeEvent(80, 24)])
    assert (root.width, root.height) == (80, 24)
    assert "\x1b[2J" in terminal.frames[-1]  # a full clear, not a partial diff


def test_resize_hook_is_called(terminal):
    sizes = []

    class App(Application):
        async def on_resize(self, event):
            sizes.append((event.width, event.height))

    run_app(App(RecordingWidget(), terminal=terminal), [ResizeEvent(100, 40)])
    assert sizes == [(100, 40)]


def test_root_can_be_replaced_while_running(terminal):
    first, second = RecordingWidget(fill="1"), RecordingWidget(fill="2")

    def swap(app):
        app.root = second

    app = Application(first, terminal=terminal)
    run_app(app, [swap])
    assert app.root is second
    assert (second.width, second.height) == terminal.size
    assert "2" in terminal.painted


def test_widget_invalidate_reaches_the_application(terminal):
    root = RecordingWidget(fill="x")
    child = root.add(RecordingWidget(fill="y", width=2, height=1))

    def touch(app):
        child.fill_char = "z"
        child.invalidate()

    run_app(Application(root, terminal=terminal), [touch])
    assert "z" in terminal.painted


def test_is_running_tracks_the_loop(terminal):
    app = Application(RecordingWidget(), terminal=terminal)
    states = []
    run_app(app, [lambda a: states.append(a.is_running)])
    assert states == [True]
    assert app.is_running is False


def test_the_background_style_fills_unpainted_cells(terminal):
    class Empty(RecordingWidget):
        def render(self, buffer):
            self.renders += 1

    run_app(Application(Empty(), terminal=terminal, background=Style(bg=4)))
    assert Style(bg=4).sgr() in terminal.frames[0]


def test_an_exception_in_a_handler_stops_the_application(terminal):
    class Boom(Application):
        async def on_key(self, event):
            raise RuntimeError("boom")

    app = Boom(RecordingWidget(), terminal=terminal)
    try:
        run_app(app, [KeyEvent("a")])
    except RuntimeError as error:
        assert str(error) == "boom"
    else:
        raise AssertionError("the exception should have propagated")
    # The terminal is still restored, so the tty is left usable.
    assert terminal.stopped is True


def test_end_of_input_exits(terminal):
    app = Application(RecordingWidget(), terminal=terminal)

    def eof(a):
        a._on_readable()  # the tty went away

    run_app(app, [eof])
    assert app.is_running is False


def test_max_fps_throttles_repaints(terminal):
    """Frames are paced, so a flood of repaints cannot outrun the terminal."""
    root = RecordingWidget()

    async def flood():
        app = Application(root, terminal=terminal, max_fps=20)

        async def driver():
            await asyncio.sleep(0.01)
            for index in range(4):
                root.fill_char = str(index)
                app.invalidate()
                await asyncio.sleep(0)  # let the loop paint between changes
            await asyncio.sleep(0.06)
            app.exit()

        task = asyncio.ensure_future(driver())
        await app.run_async()
        await task

    started = asyncio.run(asyncio.wait_for(flood(), 5))
    # 4 repaints at 20fps would take 200ms without pacing being observable;
    # what matters is that every paint was serialised, not dropped.
    assert len(terminal.frames) >= 2
    assert started is None


def test_a_second_terminal_size_is_picked_up_on_resize():
    terminal = FakeTerminal(20, 5)
    root = RecordingWidget()
    app = Application(root, terminal=terminal)

    def grow(a):
        terminal.size = (60, 20)
        a.post_event(ResizeEvent(*terminal.size))

    run_app(app, [grow])
    assert (root.width, root.height) == (60, 20)

class ReactingWidget(RecordingWidget):
    """A widget whose label is kept in step with the last key by an effect."""

    last_key = reactive("-")
    label = reactive("")

    def __init__(self):
        super().__init__()
        self.painted: list[str] = []
        self.runs = 0
        effect(self, ReactingWidget.follow)

    def follow(self) -> None:
        self.runs += 1
        self.label = f"key {self.last_key}"

    async def on_key(self, event) -> bool:
        self.last_key = event.name
        return await super().on_key(event)

    def render(self, buffer) -> None:
        super().render(buffer)
        self.painted.append(peek(self, ReactingWidget.label))


def test_effects_run_before_the_frame_is_painted(terminal):
    root = ReactingWidget()
    run_app(Application(root, terminal=terminal), [KeyEvent("a")])
    # The second frame already sees what the effect assigned.
    assert root.painted == ["key -", "key a"]


def test_a_batch_of_events_flushes_effects_once(terminal):
    root = ReactingWidget()

    def burst(app):
        # All five are queued before the loop wakes, so they form one batch.
        for index in range(5):
            app.post_event(KeyEvent(str(index)))

    run_app(Application(root, terminal=terminal), [burst])
    # One run when the effect was created, one for the whole batch.
    assert (root.runs, root.label) == (2, "key 4")


def test_an_effect_scheduled_while_the_loop_is_idle_wakes_it(terminal):
    class Model(RecordingWidget):
        n = reactive(0)

        def __init__(self):
            super().__init__()
            self.seen: list[int] = []
            effect(self, Model.watch)

        def watch(self) -> None:
            self.seen.append(self.n)

    root = Model()
    # Assigning from a plain callable, not from an event handler: nothing but
    # the scheduler's wake hook can get the parked loop to notice.
    run_app(Application(root, terminal=terminal), [lambda app: setattr(root, "n", 7)])
    assert root.seen == [0, 7]


# -- events the loop does not know about -----------------------------------


@dataclass(frozen=True, slots=True)
class TickEvent(Event):
    """An event with no sender in the tree: posted, never emitted."""

    n: int = 0


def test_a_posted_event_reaches_the_hook_its_class_names(terminal):
    class Ticking(Application):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.ticks: list[int] = []

        async def on_tick(self, event: TickEvent) -> None:
            self.ticks.append(event.n)

    app = Ticking(root=RecordingWidget(), terminal=terminal)
    run_app(app, [TickEvent(1), TickEvent(2)])
    assert app.ticks == [1, 2]


def test_a_posted_event_with_no_hook_is_dropped_quietly(terminal):
    app = Application(RecordingWidget(), terminal=terminal)
    run_app(app, [TickEvent(1)])
    assert not app.is_running


def test_on_event_still_intercepts_an_unknown_event(terminal):
    class Ticking(Application):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.ticks: list[int] = []

        async def on_event(self, event) -> bool:
            return isinstance(event, TickEvent)

        async def on_tick(self, event: TickEvent) -> None:
            self.ticks.append(event.n)

    app = Ticking(root=RecordingWidget(), terminal=terminal)
    run_app(app, [TickEvent(1)])
    assert app.ticks == []


def test_a_bare_event_is_offered_to_on_event_once(terminal):
    # ``Event`` derives the handler name ``on_event``, which every event has
    # already been offered to before the fallback is reached.
    class Counting(Application):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.seen = 0

        async def on_event(self, event) -> bool:
            self.seen += 1
            return False

    app = Counting(root=RecordingWidget(), terminal=terminal)
    run_app(app, [Event()])
    assert app.seen == 1


# -- the terminal's own cursor ---------------------------------------------


class Field(Widget):
    """A widget that wants a caret, wherever it says it is."""

    def __init__(self, at: tuple[int, int] | None = (0, 0), **kwargs):
        super().__init__(**kwargs)
        self.at = at
        self.can_focus = True

    def render(self, surface) -> None:
        surface.fill(0, 0, self.width, self.height, "_", self.style)

    def cursor_position(self):
        return self.at


def field_app(terminal, **kwargs):
    root = RecordingWidget(width=terminal.size[0], height=terminal.size[1])
    field = root.add(Field(x=5, y=2, width=10, height=1))
    return Application(root=root, terminal=terminal, **kwargs), root, field


def test_no_cursor_is_shown_while_nothing_asks_for_one(terminal):
    app, root, field = field_app(terminal)
    run_app(app)
    assert SHOW_CURSOR not in terminal.painted


def test_a_focused_field_places_and_shows_the_cursor(terminal):
    app, root, field = field_app(terminal)
    run_app(app, [lambda a: (field.focus(), a.invalidate())])
    # The field sits at 5, 2 and wants its own 0, 0: screen 5, 2, which the
    # escape counts from one.
    assert "\x1b[3;6H" + SHOW_CURSOR in terminal.painted


def test_the_cursor_follows_the_position_the_widget_reports(terminal):
    app, root, field = field_app(terminal)

    def move(a):
        field.focus()
        field.at = (4, 0)
        a.invalidate()

    run_app(app, [move])
    assert "\x1b[3;10H" in terminal.painted


def test_a_widget_that_wants_no_cursor_hides_it_again(terminal):
    app, root, field = field_app(terminal)

    def drop(a):
        field.at = None
        a.invalidate()

    run_app(app, [lambda a: (field.focus(), a.invalidate()), drop])
    assert terminal.painted.rindex(HIDE_CURSOR) > terminal.painted.rindex(SHOW_CURSOR)


def test_losing_the_focus_hides_the_cursor(terminal):
    app, root, field = field_app(terminal)
    run_app(
        app,
        [
            lambda a: (field.focus(), a.invalidate()),
            lambda a: (setattr(a, "focused", None), a.invalidate()),
        ],
    )
    assert terminal.painted.rindex(HIDE_CURSOR) > terminal.painted.rindex(SHOW_CURSOR)


def test_a_cursor_behind_an_invisible_ancestor_is_not_shown(terminal):
    app, root, field = field_app(terminal)

    def hide(a):
        field.focus()
        field.visible = False
        a.invalidate()

    run_app(app, [hide])
    assert SHOW_CURSOR not in terminal.painted


def test_a_cursor_outside_the_widget_is_refused(terminal):
    app, root, field = field_app(terminal)
    field.at = (99, 0)
    run_app(app, [lambda a: (field.focus(), a.invalidate())])
    assert SHOW_CURSOR not in terminal.painted


def test_the_caret_shape_comes_from_the_stylesheet(terminal):
    app, root, field = field_app(terminal, stylesheet=parse("Field { caret: bar }"))
    run_app(app, [lambda a: (field.focus(), a.invalidate())])
    assert "\x1b[6 q" in terminal.painted


def test_the_default_shape_leaves_the_terminals_own_alone(terminal):
    app, root, field = field_app(terminal)
    run_app(app, [lambda a: (field.focus(), a.invalidate())])
    assert " q" not in terminal.painted


def test_an_unchanged_cursor_is_not_reemitted(terminal):
    app, root, field = field_app(terminal)
    run_app(app, [lambda a: (field.focus(), a.invalidate()), lambda a: None])
    assert terminal.painted.count(SHOW_CURSOR) == 1


def test_a_repaint_puts_the_cursor_back_after_the_painting(terminal):
    # Painting moves the terminal's own cursor as a side effect, so a frame
    # that drew anything has to place it again even though it did not move.
    app, root, field = field_app(terminal)

    def repaint(a):
        root.fill_char = "#"
        a.invalidate()

    run_app(app, [lambda a: (field.focus(), a.invalidate()), repaint])
    last = terminal.frames[-1]
    assert last.rindex("\x1b[3;6H") > last.rindex("#")


def test_a_handler_that_awaits_still_costs_one_frame(terminal):
    # The guarantee this change is most likely to break.  A handler may now
    # yield to the loop mid-batch, but `_render' is only ever awaited from
    # `_main_loop', so nothing can paint until the batch has drained.
    class Slow(Application):
        async def on_key(self, event) -> bool:
            await asyncio.sleep(0)  # a real yield to the loop
            self.invalidate()
            return True

    root = RecordingWidget()
    app = Slow(root=root, terminal=terminal)

    def both(a):
        a.post_event(KeyEvent("a"))
        a.post_event(KeyEvent("b"))

    before = len(terminal.frames)
    run_app(app, [both])
    assert len(terminal.frames) - before == 1


# -- the double-click navkit synthesises -----------------------------------
#
# The terminal reports no such thing: SGR gives press, release and move, so
# two presses and a clock have to produce it.  `ClickTracker' is clockless on
# purpose -- it is *told* the time -- which is what lets the whole rule be
# tested here with no loop and no fake clock.


PRESS = MouseEvent(3, 4, "left", "press")


def test_a_second_press_at_the_same_cell_inside_the_window_is_a_double():
    tracker = ClickTracker(0.4)
    assert tracker.press(PRESS, 1.00) == 1
    assert tracker.press(PRESS, 1.10) == 2


def test_a_third_rapid_press_is_not_a_second_double_click():
    """The run counts upward and never restarts inside itself.

    Only a count of exactly two raises anything, so a fast triple click fires
    one double-click; restarting at 1 after each pair would have entered the
    same directory twice.
    """
    tracker = ClickTracker(0.4)
    counts = [tracker.press(PRESS, t) for t in (1.00, 1.10, 1.15, 1.20)]
    assert counts == [1, 2, 3, 4]


def test_a_gap_longer_than_the_window_starts_a_new_run():
    tracker = ClickTracker(0.4)
    assert tracker.press(PRESS, 1.0) == 1
    assert tracker.press(PRESS, 1.5) == 1


def test_another_cell_or_another_button_starts_a_new_run():
    """The exact cell, with no tolerance: missing a double-click costs the
    user a repeat, inventing one on the row next door opens something nobody
    asked to open."""
    tracker = ClickTracker(0.4)
    assert tracker.press(PRESS, 1.00) == 1
    assert tracker.press(MouseEvent(3, 5, "left", "press"), 1.05) == 1
    assert tracker.press(MouseEvent(3, 5, "right", "press"), 1.10) == 1


def test_a_wheel_detent_is_not_a_click_and_ends_the_run():
    """Two notches in one cell inside the window is the normal way to use a
    wheel -- and the content under the pointer has just moved, so the cell no
    longer denotes what it did."""
    tracker = ClickTracker(0.4)
    wheel = MouseEvent(3, 4, "wheel_up", "press")
    assert tracker.press(PRESS, 1.00) == 1
    assert tracker.press(wheel, 1.02) == 0
    assert tracker.press(PRESS, 1.04) == 1


def test_a_release_or_a_move_is_never_counted():
    tracker = ClickTracker(0.4)
    assert tracker.press(MouseEvent(3, 4, "left", "release"), 1.0) == 0
    assert tracker.press(MouseEvent(3, 4, "left", "move"), 1.0) == 0
    assert tracker.press(MouseEvent(3, 4, "none", "press"), 1.0) == 0


def test_a_zero_window_disables_it():
    tracker = ClickTracker(0)
    assert [tracker.press(PRESS, t) for t in (1.0, 1.0)] == [1, 1]


def test_a_double_click_is_delivered_as_well_as_the_press(terminal):
    """Additive, deliberately: suppressing the second press would take input
    away from every on_mouse already written against the stream."""
    widget = RecordingWidget(width=20, height=10)
    app = Application(widget, terminal=terminal)
    run_app(app, [PRESS, PRESS])

    assert widget.mice == [(3, 4), (3, 4)]
    assert widget.doubles == [(3, 4)]


def test_a_press_a_widget_consumed_still_counts_toward_a_double(terminal):
    """Whether anything claimed a press says nothing about whether the user
    clicked twice -- and Navigator's own hook claims every press in a panel,
    so the other choice would make the feature unreachable."""
    widget = RecordingWidget(width=20, height=10)
    widget.handles = True
    app = Application(widget, terminal=terminal)
    run_app(app, [PRESS, PRESS])

    assert widget.doubles == [(3, 4)]


def test_a_slow_pair_is_two_presses_and_nothing_else(terminal):
    """Shrinking the window rather than sleeping 0.4s of real time: run_app
    leaves 0.02s between actions, which is twenty times too slow for this."""
    widget = RecordingWidget(width=20, height=10)
    app = Application(widget, terminal=terminal, double_click=0.001)
    run_app(app, [PRESS, PRESS])

    assert widget.mice == [(3, 4), (3, 4)]
    assert widget.doubles == []


def test_the_double_click_is_offered_to_on_event_like_any_other(terminal):
    """It re-enters `_handle', as the escape key navkit manufactures does."""
    seen: list[str] = []

    class App(Application):
        async def on_event(self, event) -> bool:
            seen.append(type(event).__name__)
            return False

    app = App(RecordingWidget(width=20, height=10), terminal=terminal)
    run_app(app, [PRESS, PRESS])

    assert seen.count("DoubleClickEvent") == 1
    assert seen.count("MouseEvent") == 2


def test_a_double_click_is_never_counted_as_a_press(terminal):
    """What bounds the recursion at one level: four presses raise two
    double-clicks, not a cascade."""
    widget = RecordingWidget(width=20, height=10)
    app = Application(widget, terminal=terminal)
    run_app(app, [PRESS, PRESS, PRESS, PRESS])

    assert widget.mice == [(3, 4)] * 4
    assert widget.doubles == [(3, 4)]


def test_a_resize_forgets_the_run(terminal):
    """The layout moved out from under the pointer, so the cell no longer
    denotes what it did."""
    widget = RecordingWidget(width=20, height=10)
    app = Application(widget, terminal=terminal)
    run_app(app, [PRESS, ResizeEvent(40, 12), PRESS])

    assert widget.doubles == []

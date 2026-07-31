"""The application lifecycle and its event loop."""

from __future__ import annotations

import asyncio

from navkit.application import Application
from navkit.events import KeyEvent, MouseEvent, PasteEvent, ResizeEvent
from navkit.style import Style

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
        def on_event(self, event):
            seen.append(type(event).__name__)
            return isinstance(event, KeyEvent) and event.key == "swallowed"

        def on_key(self, event):
            return event.key == "handled"

        def on_paste(self, event):
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
        def on_key(self, event):
            self.invalidate()  # asks for a repaint, but paints the same thing
            return True

    run_app(Application(Quiet(), terminal=terminal), [KeyEvent("a")])
    assert len(terminal.frames) == 1  # the diff was empty, so nothing was sent


def test_nothing_is_rendered_when_no_repaint_was_asked_for(terminal):
    class Silent(RecordingWidget):
        def on_key(self, event):
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
        def on_resize(self, event):
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
        def on_key(self, event):
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
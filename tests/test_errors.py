"""A failure is never silent: ``Application.fail`` and what goes through it."""

from __future__ import annotations

import asyncio
import threading

import pytest

from conftest import FakeTerminal, run_app
from navkit.application import ERROR_STORM_LIMIT, Application
from navkit.events import KeyEvent
from navkit.reactive import effect, reactive
from navkit.screen import Surface
from navkit.widget import Widget


class Boom(Exception):
    pass


class Painter(Widget):
    def render(self, surface: Surface) -> None:
        surface.fill(0, 0, self.width, self.height, ".", self.style)


class Reporting(Application):
    """Shows every failure (records it) and carries on, as the error box does."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.reported: list[BaseException] = []
        self.logged: list[BaseException] = []

    def report_error(self, error):
        self.reported.append(error)
        return True

    def log_error(self, error):
        self.logged.append(error)


def _app(cls=Application, root=None):
    return cls(root or Painter(), terminal=FakeTerminal(width=10, height=3))


def test_a_failing_spawned_task_is_raised_out_of_run():
    """It used to be re-raised inside a done-callback, where asyncio printed
    it into the alternate screen and ``run`` returned as if nothing happened."""
    app = _app()

    async def work():
        raise Boom("in a task")

    with pytest.raises(Boom, match="in a task"):
        run_app(app, [lambda a: a.spawn(work()), lambda a: None])


def test_a_failing_loop_callback_is_raised_out_of_run():
    app = _app()

    def callback():
        raise Boom("in a callback")

    with pytest.raises(Boom, match="in a callback"):
        run_app(app, [lambda a: asyncio.get_running_loop().call_soon(callback), lambda a: None])


def test_a_failing_thread_is_raised_out_of_run():
    app = _app()

    def worker():
        raise Boom("in a thread")

    def start(a):
        thread = threading.Thread(target=worker)
        thread.start()
        thread.join()

    with pytest.raises(Boom, match="in a thread"):
        run_app(app, [start, lambda a: None, lambda a: None])


def test_a_failing_on_stop_is_raised_out_of_run():
    class Stopping(Application):
        async def on_stop(self):
            raise Boom("on the way out")

    with pytest.raises(Boom, match="on the way out"):
        run_app(_app(Stopping))


def test_a_reported_failure_lets_the_application_carry_on():
    root = Painter()
    app = _app(Reporting, root)
    keys: list[str] = []

    async def on_key(event):
        if event.key == "x":
            raise Boom("handler")
        keys.append(event.key)
        return True

    root.on_key = on_key
    root.focus()
    run_app(app, [KeyEvent(key="x"), KeyEvent(key="a")])
    assert [str(e) for e in app.reported] == ["handler"]
    assert app.logged == app.reported
    assert keys == ["a"], "the next key was still dispatched"


def test_a_failing_effect_is_reported_and_the_rest_still_run():
    class Model(Widget):
        value: int = reactive(0)

        def render(self, surface):
            pass

    root = Model()
    app = _app(Reporting, root)
    seen: list[int] = []

    def failing(owner):
        if owner.value == 1:
            raise Boom("effect")

    def watching(owner):
        seen.append(owner.value)

    effect(root, failing)
    effect(root, watching)

    def bump(a):
        root.value = 1

    run_app(app, [bump])
    assert [str(e) for e in app.reported] == ["effect"]
    assert seen[-1] == 1, "the effect after the failing one still ran"


def test_a_failing_render_is_reported_once_and_the_frame_still_paints():
    class Broken(Widget):
        def render(self, surface):
            raise Boom("render")

    root = Painter()
    broken = Broken()
    root.add(broken)
    app = _app(Reporting, root)
    run_app(app, [lambda a: a.invalidate(), lambda a: root.merge_style("bg: red")])
    assert [str(e) for e in app.reported] == ["render"]
    assert app.terminal.frames, "the rest of the frame was painted"


def test_a_failing_render_stops_an_application_that_does_not_report():
    class Broken(Widget):
        def render(self, surface):
            raise Boom("render")

    with pytest.raises(Boom, match="render"):
        run_app(_app(root=Broken()))


def test_a_storm_of_failures_stops_the_application():
    root = Painter()
    app = _app(Reporting, root)

    async def on_key(event):
        raise Boom(event.key)

    root.on_key = on_key
    root.focus()
    keys = [KeyEvent(key=chr(ord("a") + i)) for i in range(ERROR_STORM_LIMIT + 1)]
    with pytest.raises(Boom):
        run_app(app, keys + [lambda a: None])
    assert len(app.reported) == ERROR_STORM_LIMIT
    assert len(app.logged) == ERROR_STORM_LIMIT + 1


def test_a_failure_while_reporting_stops_the_application():
    class Failing(Application):
        def report_error(self, error):
            raise Boom("the report itself")

    root = Painter()
    app = _app(Failing, root)

    async def on_key(event):
        raise Boom("first")

    root.on_key = on_key
    root.focus()
    with pytest.raises(Boom, match="first"):
        run_app(app, [KeyEvent(key="a")])

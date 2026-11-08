"""A held mouse button repeating: Turbo Vision's ``evMouseAuto``.

``Application.hold_mouse`` and what uses it -- the scroll bar's arrows and
track, a list's cursor following a drag, the panel's held marking and F3's
quarters.  The repeat's delays are made a few milliseconds so that holding
is quick to wait out.
"""

from __future__ import annotations

import pytest

from conftest import FakeTerminal, IDLE, Until, run_app
from navkit.application import Application
from navkit.events import KeyEvent, MouseClickEvent
from navkit.widget import Widget


@pytest.fixture(autouse=True)
def quick(monkeypatch):
    monkeypatch.setattr("navkit.application.REPEAT_DELAY", 0.02)
    monkeypatch.setattr("navkit.application.REPEAT_EVERY", 0.005)


def press(x, y, button="left"):
    return MouseClickEvent(x=x, y=y, button=button, action="press")


def move(x, y, button="left"):
    return MouseClickEvent(x=x, y=y, button=button, action="move")


def release(x, y):
    return MouseClickEvent(x=x, y=y, button="none", action="release")


class Holder(Widget):
    """Holds on a press, recording every step."""

    def __init__(self, moves=False, stop_after=None, **kw):
        super().__init__(**kw)
        self.steps: list[tuple[int, int, bool]] = []
        self.moves = moves
        self.stop_after = stop_after
        self.ended = 0

    async def on_mouse_click(self, event):
        if event.action != "press":
            return False

        async def step(x, y, auto):
            self.steps.append((x, y, auto))
            if self.stop_after is not None and len(self.steps) >= self.stop_after:
                return False
            return None

        def done():
            self.ended += 1

        self.application.hold_mouse(self, event, step, moves=self.moves, done=done)
        return True


def holder_app(**kw):
    root = Widget()
    holder = root.add(Holder(x=0, y=0, width=10, height=5, **kw))
    return Application(root=root, terminal=FakeTerminal(80, 24)), holder


def test_a_held_button_repeats_until_it_is_released():
    app, holder = holder_app()
    seen = {}
    run_app(app, [press(2, 1), Until(lambda a: len(holder.steps) >= 3),
                  release(2, 1), lambda a: seen.update(n=len(holder.steps)),
                  Until(lambda a: True), lambda a: seen.update(later=len(holder.steps), capture=a.mouse_capture,
                                                              hold=a.mouse_hold)])
    assert holder.steps[0] == (2, 1, True)
    assert seen["later"] == seen["n"]
    assert seen["capture"] is None and seen["hold"] is None
    assert holder.ended == 1


def test_moves_step_only_when_asked_and_ticks_use_the_last_place():
    app, quiet = holder_app()
    run_app(app, [press(1, 1), move(30, 7), Until(lambda a: quiet.steps and quiet.steps[-1][:2] == (30, 7)),
                  release(30, 7)])
    assert all(auto for _, _, auto in quiet.steps)

    app, moving = holder_app(moves=True)
    run_app(app, [press(1, 1), move(4, 2), Until(lambda a: (4, 2, True) in moving.steps), release(4, 2)])
    assert (4, 2, False) in moving.steps


def test_a_step_returning_false_stops_the_ticks_but_keeps_the_capture():
    app, holder = holder_app(stop_after=2)
    seen = {}
    run_app(app, [press(1, 1), Until(lambda a: len(holder.steps) == 2), Until(lambda a: True),
                  lambda a: seen.update(capture=a.mouse_capture), release(1, 1)])
    assert len(holder.steps) == 2
    assert seen["capture"] is holder


def test_the_hold_ends_with_the_widget_or_the_capture():
    app, holder = holder_app()
    seen = {}

    def gone(a):
        holder.parent.remove(holder)
        seen["n"] = len(holder.steps)

    run_app(app, [press(1, 1), Until(lambda a: holder.steps), gone, Until(lambda a: True),
                  lambda a: seen.update(later=len(holder.steps), hold=a.mouse_hold)])
    assert seen["later"] == seen["n"] and seen["hold"] is None
    assert holder.ended == 1

    app, holder = holder_app()
    run_app(app, [press(1, 1), Until(lambda a: holder.steps), lambda a: a.release_mouse(),
                  lambda a: seen.update(n=len(holder.steps)), Until(lambda a: True),
                  lambda a: seen.update(later=len(holder.steps))])
    assert seen["later"] == seen["n"]


# -- the scroll bar -------------------------------------------------------------------------------


def bar_app(**kw):
    from navml.widgets.dialog.scroll_bar import ScrollBar

    root = Widget()
    bar = root.add(ScrollBar(x=0, y=0, width=1, height=12, **kw))

    async def on_scroll(event):
        bar.value = event.value
        return True

    root.on_scroll = on_scroll
    return Application(root=root, terminal=FakeTerminal(80, 24)), bar


def test_holding_a_scroll_bar_arrow_steps_until_the_release():
    app, bar = bar_app(maximum=100, page=10)
    seen = {}
    run_app(app, [press(0, 11), Until(lambda a: bar.value >= 4), release(0, 11),
                  lambda a: seen.update(n=bar.value), Until(lambda a: True),
                  lambda a: seen.update(later=bar.value)])
    assert seen["later"] == seen["n"] >= 4


def test_a_slipped_hand_pauses_the_arrow_and_a_cell_off_keeps_it():
    app, bar = bar_app(maximum=100, page=10)
    seen = {}
    run_app(app, [press(0, 11), move(1, 12), Until(lambda a: bar.value >= 3),
                  move(5, 11), lambda a: seen.update(n=bar.value), Until(lambda a: True),
                  lambda a: seen.update(later=bar.value), release(5, 11)])
    assert seen["later"] == seen["n"]


def test_holding_the_track_pages_until_the_thumb_reaches_the_pointer():
    app, bar = bar_app(maximum=100, page=10)
    seen = {}
    # Track cells 1..10; the pointer on cell 6 (y=7) is value 60's place.
    run_app(app, [press(0, 7), Until(lambda a: bar.thumb == 6), Until(lambda a: True),
                  lambda a: seen.update(value=bar.value), release(0, 7)])
    assert bar.value_at(5) < seen["value"] <= bar.value_at(6) + bar.page


# -- a list ---------------------------------------------------------------------------------------


def list_app(count=50, **kw):
    from navml.widgets.dialog.list_viewer import ListViewer

    root = Widget()
    box = root.add(ListViewer(x=0, y=0, width=20, height=10, items=[f"item {n}" for n in range(count)], **kw))
    # The terminal the list's own height, which a lone child is laid out to.
    return Application(root=root, terminal=FakeTerminal(20, 10)), box


def test_a_drag_in_a_list_moves_the_cursor_with_the_pointer():
    app, box = list_app()
    seen = {}
    run_app(app, [press(3, 2), lambda a: seen.update(pressed=box.cursor), move(3, 6),
                  lambda a: seen.update(moved=box.cursor), release(3, 6)])
    assert (seen["pressed"], seen["moved"]) == (1, 5)


def test_held_below_a_list_the_cursor_moves_on_every_fourth_tick():
    app, box = list_app()
    seen = {}

    def note(a):
        seen["cursor"], seen["ticks"] = box.cursor, a.mouse_hold.ticks

    run_app(app, [press(3, 8), move(3, 15), Until(lambda a: box.cursor >= 10), note, release(3, 15),
                  lambda a: seen.update(released=box.cursor), Until(lambda a: True),
                  lambda a: seen.update(later=box.cursor)])
    assert seen["later"] == seen["released"]
    assert seen["ticks"] >= 4 * (seen["cursor"] - 7)
    assert box.scroll <= box.cursor < box.scroll + box.rows


def test_a_list_that_does_not_follow_takes_the_press_alone():
    from navml.widgets.dialog.list_viewer import ListViewer

    class Still(ListViewer):
        follows_drag = False

    root = Widget()
    box = root.add(Still(x=0, y=0, width=20, height=10, items=[str(n) for n in range(30)]))
    app = Application(root=root, terminal=FakeTerminal(80, 24))
    seen = {}
    run_app(app, [press(3, 2), move(3, 6), lambda a: seen.update(cursor=box.cursor, capture=a.mouse_capture),
                  release(3, 6)])
    assert seen == {"cursor": 1, "capture": None}


# -- the panel ------------------------------------------------------------------------------------


@pytest.fixture
def many(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    for n in range(80):
        (tmp_path / f"file{n:02}").touch()
    return tmp_path


def row_place(panel, index):
    ox, oy = panel.offset()
    return ox + panel.x + 3, oy + panel.y + panel.inset + panel.header + index - panel.scroll


def test_marking_held_below_the_panel_goes_on_tagging_and_scrolling(many):
    from navigator.__main__ import Navigator

    app = Navigator(many, many, terminal=FakeTerminal(80, 24))
    seen = {}

    def start(a):
        panel = a.manager.left
        x, y = row_place(panel, 1)
        a.post_event(press(x, y, "middle"))
        below = panel.offset()[1] + panel.y + panel.height + 1
        a.post_event(move(x, below, "middle"))
        seen["panel"] = panel

    def note(a):
        seen["marked"] = sum(seen["panel"].is_marked(e) for e in seen["panel"].items)

    run_app(app, [IDLE, start, Until(lambda a: seen["panel"].cursor >= 40), note, release(0, 0)])
    panel = seen["panel"]
    assert seen["marked"] >= 40
    assert panel.scroll > 0


def test_with_drag_and_drop_off_a_left_drag_moves_the_panels_cursor(many, monkeypatch):
    from navigator.__main__ import Navigator
    from navigator.settings import SETTINGS

    monkeypatch.setattr(SETTINGS.file_manager, "drag_drop_columns", False)
    app = Navigator(many, many, terminal=FakeTerminal(80, 24))
    seen = {}

    def drag(a):
        panel = seen["panel"] = a.manager.left
        x, y = row_place(panel, 1)
        a.post_event(press(x, y))
        a.post_event(move(x, y + 4))

    run_app(app, [IDLE, drag, lambda a: seen.update(cursor=seen["panel"].cursor), release(0, 0)])
    assert seen["cursor"] == 5


def test_with_drag_and_drop_on_the_panel_does_not_follow(many):
    from navigator.__main__ import Navigator

    app = Navigator(many, many, terminal=FakeTerminal(80, 24))
    seen = {}

    def drag(a):
        panel = seen["panel"] = a.manager.left
        x, y = row_place(panel, 1)
        a.post_event(press(x, y))

    run_app(app, [IDLE, drag, Until(lambda a: True),
                  lambda a: seen.update(cursor=seen["panel"].cursor, hold=a.mouse_hold),
                  release(0, 0)])
    assert seen == {"panel": seen["panel"], "cursor": 1, "hold": None}


# -- F3 -------------------------------------------------------------------------------------------


def test_holding_a_quarter_of_f3_scrolls_and_follows_the_pointer(tmp_path, monkeypatch):
    from navigator.__main__ import Navigator
    from navigator.widgets.viewer.file_window import FileWindow

    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    (tmp_path / "text.txt").write_text("".join(f"line {n:03} " + "x" * 200 + "\n" for n in range(300)))
    app = Navigator(tmp_path, tmp_path, terminal=FakeTerminal(80, 24))
    seen = {}

    def window(a):
        w = a.shell.desktop.active_window
        return w if isinstance(w, FileWindow) else None

    def hold(a):
        viewer = seen["viewer"] = window(a).viewer
        ox, oy = viewer.offset()
        x, y = ox + viewer.x + viewer.width // 2, oy + viewer.y + viewer.height - 2
        seen["at"] = (x, y)
        a.post_event(press(x, y))

    def right(a):
        viewer = seen["viewer"]
        ox, _ = viewer.offset()
        seen["top"] = viewer.top
        a.post_event(move(ox + viewer.x + viewer.width - 2, seen["at"][1]))

    def unwrap(a):
        if window(a).viewer.wrap:
            a.post_event(KeyEvent("f2"))

    run_app(app, [KeyEvent("end"), KeyEvent("f3"), Until(lambda a: window(a) is not None), IDLE, unwrap,
                  hold, Until(lambda a: seen["viewer"].top > 3 * 210), right,
                  Until(lambda a: seen["viewer"].x_delta >= 3), release(0, 0),
                  lambda a: seen.update(left=seen["viewer"].x_delta), Until(lambda a: True),
                  lambda a: seen.update(later=seen["viewer"].x_delta)])
    assert not seen["viewer"].wrap
    assert seen["later"] == seen["left"]

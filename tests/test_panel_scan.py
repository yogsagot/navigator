"""A panel reads its directory on a thread: a slow one never stops the screen."""

from __future__ import annotations

import threading
import time
from pathlib import Path

import pytest

from conftest import LISTED, FakeTerminal, Until, run_app
from navkit.events import KeyEvent

from navigator.__main__ import Navigator
from navigator.lib.drives import listing as listing_module
from navigator.widgets.manager.panel import panel as panel_module


@pytest.fixture
def tree(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    (tmp_path / "slow").mkdir()
    (tmp_path / "slow" / "inside.txt").write_text("x")
    (tmp_path / "slow" / "deeper").mkdir()
    (tmp_path / "fast").mkdir()
    (tmp_path / "one.txt").write_text("1")
    return tmp_path


@pytest.fixture
def slow_dir(tree, monkeypatch):
    """Reading ``slow`` waits until released, as a dead mount would."""
    release = threading.Event()
    real = listing_module.scan_directory

    def scan(path, show_hidden, *args, **kwargs):
        if Path(path).name == "slow":
            release.wait(5)
        return real(path, show_hidden, *args, **kwargs)

    monkeypatch.setattr(listing_module, "scan_directory", scan)
    monkeypatch.setattr(panel_module, "SCAN_GRACE", 0.01)
    return release


def navigator(path) -> Navigator:
    return Navigator(path, path, terminal=FakeTerminal(80, 24))


def left(app):
    return app.manager.left


def go_to(name):
    """Put the left panel's cursor on *name*."""
    def action(app):
        panel = left(app)
        panel.cursor = [entry.name for entry in panel.items].index(name)
    return action


def row_text(app, panel, row: int) -> str:
    from navkit.screen import ScreenBuffer

    buffer = ScreenBuffer(panel.width, panel.height)
    panel.render(buffer)
    return "".join(buffer.get(x, row)[0] or " " for x in range(panel.width))


def test_a_slow_directory_says_so_and_the_screen_keeps_going(tree, slow_dir):
    app = navigator(tree)
    seen = {}
    ticks = []

    def look(a):
        panel = left(a)
        seen.update(scanning=panel.scanning, items=list(panel.items), selected=panel.selected,
                    row=row_text(a, panel, panel.inset + panel.header))

    def start_ticking(a):
        async def tick():
            ticks.append(time.monotonic())
        a.call_every(0.01, tick)

    run_app(app, [go_to("slow"), start_ticking, KeyEvent("enter"), lambda a: None,
                  Until(lambda a: left(a).scanning), look,
                  KeyEvent("enter"),  # nothing selected: nothing entered
                  lambda a: None, lambda a: slow_dir.set(),
                  Until(lambda a: not left(a).scanning),
                  lambda a: seen.update(after=[e.name for e in left(a).items],
                                        path=left(a).path, cursor=left(a).cursor)])
    assert seen["scanning"] is True
    assert seen["items"] == [] and seen["selected"] is None
    assert "Reading directory..." in seen["row"]
    assert seen["after"] == ["..", "deeper", "inside.txt"]
    assert seen["path"] == tree / "slow" and seen["cursor"] == 0
    assert len(ticks) >= 5  # the loop went on ticking while the read waited


def test_a_read_that_lands_after_the_panel_moved_on_is_dropped(tree, slow_dir):
    app = navigator(tree)
    seen = {}
    run_app(app, [go_to("slow"), KeyEvent("enter"), Until(lambda a: left(a).scanning),
                  # Back out before ``slow`` was read: the parent is fast.
                  lambda a: setattr(left(a), "path", tree),
                  Until(lambda a: not left(a).scanning),
                  lambda a: slow_dir.set(), lambda a: None, lambda a: None,
                  lambda a: seen.update(path=left(a).path,
                                        names=[e.name for e in left(a).items])])
    assert seen["path"] == tree
    assert "inside.txt" not in seen["names"] and "slow" in seen["names"]


def test_backing_out_of_a_slow_directory_lands_on_it(tree, slow_dir):
    # The cursor goes back to where it came from, as it does for a fast one.
    app = navigator(tree / "slow" / "deeper")
    seen = {}

    def hold(a):
        slow_dir.clear()

    run_app(app, [hold, KeyEvent("enter"),  # ".." from deeper: into slow
                  Until(lambda a: left(a).scanning), lambda a: slow_dir.set(),
                  Until(lambda a: not left(a).scanning),
                  lambda a: seen.update(name=left(a).selected.name)])
    assert seen["name"] == "deeper"


def test_a_slow_re_read_keeps_the_rows_and_the_cursor(tree, slow_dir):
    slow_dir.set()  # before the panels' first read, which is waited for
    app = navigator(tree / "slow")
    seen = {}

    def reread(a):
        slow_dir.clear()
        left(a).reload()

    run_app(app, [Until(lambda a: len(left(a).items) == 3), go_to("inside.txt"), reread,
                  lambda a: None, lambda a: None,
                  lambda a: seen.update(during=(left(a).scanning, len(left(a).items))),
                  lambda a: (tree / "slow" / "added.txt").write_text("+"),
                  lambda a: slow_dir.set(),
                  Until(lambda a: len(left(a).items) == 4),
                  lambda a: seen.update(name=left(a).selected.name)])
    assert seen["during"] == (False, 3)  # the same directory: its rows stay up
    assert seen["name"] == "inside.txt"


# -- the grace wait, only where it pays ----------------------------------------------------------------


@pytest.fixture
def graces(monkeypatch):
    """Every grace ``_rescan`` waited, in seconds (0 for none)."""
    import concurrent.futures

    waited = []
    real = concurrent.futures.Future.result

    def result(self, timeout=None):
        if threading.current_thread() is threading.main_thread() and timeout is not None:
            waited.append(timeout)
        return real(self, timeout)

    monkeypatch.setattr(concurrent.futures.Future, "result", result)
    return waited


def test_a_re_read_of_the_same_place_does_not_wait(tree, graces):
    app = navigator(tree)
    seen = {}

    def reread(a):
        graces.clear()
        left(a).reload()

    run_app(app, [
        Until(lambda a: len(left(a).items) > 1), reread, Until(lambda a: not left(a).scanning),
        lambda a: seen.update(re_read=list(graces)),
        lambda a: graces.clear(), go_to("fast"), KeyEvent("enter"),
        Until(lambda a: left(a).path.name == "fast" and not left(a).scanning),
        lambda a: seen.update(new=list(graces)),
    ])
    assert panel_module.SCAN_GRACE not in seen["re_read"]
    assert panel_module.SCAN_GRACE in seen["new"]  # the disk, somewhere new: worth the wait


def test_a_step_on_a_drive_a_round_trip_away_does_not_wait(tree, graces):
    from navigator.lib.drives import mount, unmount
    from navigator.lib.drives.memory import MemoryDrive

    class Far(MemoryDrive):
        quick_listing = False

        def scan(self, *args, **kwargs):
            time.sleep(0.2)
            return super().scan(*args, **kwargs)

    drive = mount(Far("far"))
    drive.make("/top/sub/x.txt", "x")
    app = navigator(tree)
    seen = {}

    def step(a):
        graces.clear()
        left(a).location = drive.location("/top")

    try:
        run_app(app, [
            step, lambda a: seen.update(scanning=left(a).scanning, waited=list(graces)),
            Until(lambda a: [e.name for e in left(a).items] == ["..", "sub"], timeout=5),
        ])
    finally:
        unmount(drive.site)
    assert seen["scanning"] is True and panel_module.SCAN_GRACE not in seen["waited"]


# -- Enter and Backspace work from the letters -------------------------------------------------------------


@pytest.fixture
def resolves_on_loop(monkeypatch):
    """The ``Path.resolve`` calls made on the loop from Enter, Backspace,
    paste or a drop."""
    import traceback

    found = []
    real = Path.resolve

    def resolve(self, *args, **kwargs):
        callers = {frame.name for frame in traceback.extract_stack()}
        if (threading.current_thread() is threading.main_thread()
                and callers & {"enter", "go_up", "_entered", "paste_files", "on_dropped"}):
            found.append(self)
        return real(self, *args, **kwargs)

    monkeypatch.setattr(Path, "resolve", resolve)
    return found


def test_enter_and_backspace_resolve_nothing_and_a_link_goes_where_it_points(tree, resolves_on_loop):
    (tree / "fast" / "inner").mkdir()
    (tree / "to_fast").symlink_to("fast")
    (tree / "slow" / "up_to_fast").symlink_to("../fast")
    app = navigator(tree)
    seen = {}
    run_app(app, [
        Until(lambda a: "to_fast" in [e.name for e in left(a).items]),
        go_to("to_fast"), KeyEvent("enter"), Until(lambda a: left(a).path == tree / "fast"), LISTED,
        go_to("inner"), KeyEvent("enter"), Until(lambda a: left(a).path == tree / "fast" / "inner"), LISTED,
        KeyEvent("backspace"), Until(lambda a: left(a).path == tree / "fast"), LISTED,
        lambda a: seen.update(cursor=left(a).selected.name),
        KeyEvent("backspace"), Until(lambda a: left(a).path == tree), LISTED,
        go_to("slow"), KeyEvent("enter"), Until(lambda a: "up_to_fast" in [e.name for e in left(a).items]),
        go_to("up_to_fast"), KeyEvent("enter"), Until(lambda a: left(a).path == tree / "fast"), LISTED,
    ])
    assert seen["cursor"] == "inner"
    assert resolves_on_loop == []

"""A panel reads its directory on a thread: a slow one never stops the screen."""

from __future__ import annotations

import threading
import time
from pathlib import Path

import pytest

from conftest import FakeTerminal, Until, run_app
from navkit.events import KeyEvent

from navigator.__main__ import Navigator
from navigator.widgets.manager.panel import panel as panel_module


@pytest.fixture
def tree(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.subshell.Subshell.start", lambda self, *a, **k: None)
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
    real = panel_module.scan_directory

    def scan(path, show_hidden):
        if Path(path).name == "slow":
            release.wait(5)
        return real(path, show_hidden)

    monkeypatch.setattr(panel_module, "scan_directory", scan)
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

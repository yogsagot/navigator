"""*Auto refresh panels*: a panel re-reads its directory when it changes on disk."""

from __future__ import annotations

import threading

import pytest

from conftest import FakeTerminal, Until, run_app

from navigator.__main__ import Navigator
from navigator.lib.system import dirwatch
from navigator.settings import SETTINGS
from navigator.widgets.manager.panel import panel as panel_module


@pytest.fixture
def tree(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    monkeypatch.setattr(panel_module, "REFRESH_DELAY", 0.05)
    (tmp_path / "one.txt").write_text("1")
    (tmp_path / "two.txt").write_text("2")
    (tmp_path / "sub").mkdir()
    return tmp_path


def navigator(path) -> Navigator:
    return Navigator(path, path, terminal=FakeTerminal(80, 24))


def names(panel) -> list[str]:
    return [entry.name for entry in panel.items]


def lists(name, side="left"):
    return Until(lambda app: name in names(getattr(app.manager, side)))


def lists_not(name, side="left"):
    return Until(lambda app: name not in names(getattr(app.manager, side)))


# -- the watcher ---------------------------------------------------------------


def wait_for(event: threading.Event) -> bool:
    return event.wait(2)


def test_a_new_file_and_a_deleted_one_are_heard(tmp_path):
    heard = threading.Event()
    watch = dirwatch.watch(tmp_path, heard.set)
    (tmp_path / "new.txt").write_text("x")
    assert wait_for(heard)
    heard.clear()
    (tmp_path / "new.txt").unlink()
    assert wait_for(heard)
    watch.cancel()


def test_reading_a_file_or_the_directory_is_not_a_change(tmp_path):
    (tmp_path / "old.txt").write_text("x")
    heard = threading.Event()
    watch = dirwatch.watch(tmp_path, heard.set)
    (tmp_path / "old.txt").read_text()
    list(tmp_path.iterdir())
    assert not heard.wait(0.3)
    watch.cancel()


def test_one_watch_per_directory_until_the_last_is_cancelled(tmp_path):
    first = dirwatch.watch(tmp_path, lambda: None)
    second = dirwatch.watch(tmp_path, lambda: None)
    assert dirwatch.watched() == [tmp_path]
    first.cancel()
    assert dirwatch.watched() == [tmp_path]
    second.cancel()
    second.cancel()  # twice is harmless
    assert dirwatch.watched() == []


def test_a_directory_that_cannot_be_watched_gets_a_watch_that_does_nothing(tmp_path):
    watch = dirwatch.watch(tmp_path / "missing", lambda: None)
    assert not watch.active
    watch.cancel()
    assert dirwatch.watched() == []


# -- the panel -----------------------------------------------------------------


def test_a_file_created_elsewhere_appears_and_the_cursor_stays(tree):
    app = navigator(tree)
    seen = {}

    def put_cursor(a):
        panel = a.manager.left
        panel.cursor = names(panel).index("two.txt")

    def look(a):
        seen["selected"] = a.manager.left.selected.name
        seen["right"] = names(a.manager.right)

    run_app(app, [put_cursor,
                  lambda a: (tree / "aaa.txt").write_text("new"), lists("aaa.txt"),
                  lists("aaa.txt", "right"), look])
    assert seen["selected"] == "two.txt"
    assert "aaa.txt" in seen["right"]


def test_a_file_deleted_elsewhere_goes(tree):
    app = navigator(tree)
    run_app(app, [lists("one.txt"), lambda a: (tree / "one.txt").unlink(), lists_not("one.txt")])


def test_the_panel_follows_the_directory_it_moved_to(tree):
    app = navigator(tree)
    watched = {}

    def into_sub(a):
        a.manager.left.path = tree / "sub"
        a.manager.right.path = tree / "sub"

    def look(a):
        watched["now"] = dirwatch.watched()

    run_app(app, [into_sub, look,
                  lambda a: (tree / "sub" / "inner.txt").write_text("x"), lists("inner.txt")])
    assert watched["now"] == [tree / "sub"]


def test_with_auto_refresh_off_nothing_is_watched(tree):
    SETTINGS.file_manager.auto_refresh = False
    app = navigator(tree)
    seen = {}

    def look(a):
        seen["watched"] = dirwatch.watched()

    run_app(app, [look])
    assert seen["watched"] == []


def test_turning_auto_refresh_off_stops_watching(tree):
    app = navigator(tree)
    seen = {}

    def turn_off(a):
        seen["before"] = dirwatch.watched()
        SETTINGS.file_manager.auto_refresh = False

    def look(a):
        seen["after"] = dirwatch.watched()

    run_app(app, [turn_off, look])
    assert seen["before"] == [tree]
    assert seen["after"] == []


def test_a_panel_taken_off_the_screen_stops_watching(tree):
    app = navigator(tree)
    seen = {}

    def close(a):
        panel = a.manager.left
        panel.parent.remove(panel)

    def look(a):
        seen["watched"] = dirwatch.watched()

    run_app(app, [close, look])
    # The right panel still shows the same directory.
    assert seen["watched"] == [tree]


def test_a_burst_of_changes_is_one_re_read(tree, monkeypatch):
    monkeypatch.setattr(panel_module, "REFRESH_DELAY", 0.2)
    app = navigator(tree)
    reads = []

    def count(a):
        panel = a.manager.left
        real = panel.reload
        monkeypatch.setattr(panel, "reload", lambda *args, **kw: (reads.append(1), real(*args, **kw)))

    def burst(a):
        for index in range(50):
            (tree / f"f{index}.txt").write_text("x")

    run_app(app, [count, burst, lists("f49.txt")])
    assert len(reads) <= 2


def test_the_application_stops_the_observer(tree):
    app = navigator(tree)
    run_app(app, [])
    assert dirwatch._OBSERVER is None

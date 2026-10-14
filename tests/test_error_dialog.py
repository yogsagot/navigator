"""Navigator's answer to a failure: the error box, or quitting, and ``errors.log``."""

from __future__ import annotations

import pytest

from conftest import FakeTerminal, Until, run_app
from navkit.events import KeyEvent, ResizeEvent

from navigator.lib.system import errorlog
from navigator.settings import SETTINGS
from navigator.widgets.shell.error_dialog import ErrorDialog


class Boom(Exception):
    pass


@pytest.fixture
def nav(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    monkeypatch.setattr("navigator.widgets.shell.console.Console.start", lambda self, argv=None: None)
    monkeypatch.setattr(errorlog, "PATH", tmp_path / "errors.log")
    SETTINGS.system.on_error = "dialog"
    return tmp_path


def navigator(path, **kwargs):
    from navigator.__main__ import Navigator

    return Navigator(path, path, terminal=FakeTerminal(80, 24), **kwargs)


async def failing():
    raise Boom("it broke")


BOX_UP = Until(lambda a: isinstance(a.modal, ErrorDialog))


def test_a_failure_opens_the_box_and_continue_carries_on(nav):
    app = navigator(nav)
    seen = []
    run_app(app, [lambda a: a.spawn(failing()), BOX_UP,
                  lambda a: seen.append(a.modal), KeyEvent("enter"), lambda a: None,
                  lambda a: seen.append(a.modal)])
    box, after = seen
    assert box.summary.text == "Boom: it broke"
    assert any("raise Boom" in line for line in box.trace.items)
    assert after is None, "Continue closed the box and Navigator went on"


def test_copy_puts_the_whole_traceback_on_the_clipboard(nav):
    app = navigator(nav)
    copied = []
    app.copy_to_clipboard = lambda text, primary=False: copied.append(text)
    run_app(app, [lambda a: a.spawn(failing()), BOX_UP,
                  lambda a: a.spawn(a.modal.on_copy_click(None)), lambda a: None])
    assert len(copied) == 1
    assert copied[0].startswith("Traceback (most recent call last):")
    assert copied[0].rstrip().endswith("Boom: it broke")


def test_quit_ends_navigator_raising_the_failure(nav):
    app = navigator(nav)
    with pytest.raises(Boom, match="it broke"):
        run_app(app, [lambda a: a.spawn(failing()), BOX_UP,
                      lambda a: a.spawn(a.modal.on_quit_click(None)), lambda a: None])
    assert (nav / "errors.log").read_text().count("Boom: it broke") == 1, "logged once"


def test_a_failure_while_the_box_is_up_ends_navigator(nav):
    app = navigator(nav)
    with pytest.raises(Boom, match="it broke"):
        run_app(app, [lambda a: a.spawn(failing()), BOX_UP,
                      lambda a: a.spawn(failing()), lambda a: None])


def test_crash_quits_with_the_failure(nav):
    SETTINGS.system.on_error = "crash"
    app = navigator(nav)
    with pytest.raises(Boom, match="it broke"):
        run_app(app, [lambda a: a.spawn(failing()), lambda a: None])
    assert "Boom: it broke" in (nav / "errors.log").read_text()


def test_the_flag_wins_over_the_setting(nav):
    app = navigator(nav, on_error="crash")
    with pytest.raises(Boom):
        run_app(app, [lambda a: a.spawn(failing()), lambda a: None])


def test_every_failure_is_logged_with_its_traceback(nav):
    app = navigator(nav)
    run_app(app, [lambda a: a.spawn(failing()), BOX_UP, KeyEvent("enter"), lambda a: None])
    log = (nav / "errors.log").read_text()
    assert log.startswith("=== ")
    assert "Traceback (most recent call last):" in log
    assert "Boom: it broke" in log


def test_system_setup_chooses_what_a_failure_does():
    from navigator.widgets.setup.system_setup_dialog import SystemSetupDialog

    SETTINGS.system.on_error = "dialog"
    box = SystemSetupDialog()
    assert box.on_error.value == 0
    box.on_error.value = 1
    assert box.accept()["on_error"] == "crash"


async def failing_long():
    raise Boom("x" * 300)


def test_long_lines_wrap_to_the_box_and_rewrap_when_it_changes(nav):
    app = navigator(nav)
    seen = {}

    def look(key):
        def act(a):
            trace = a.modal.trace
            seen[key] = (trace.inner_width, list(trace.items), trace.cursor)
        return act

    run_app(app, [lambda a: a.spawn(failing_long()), BOX_UP, look("wide"), ResizeEvent(70, 24),
                  lambda a: None, look("narrow")])
    for key in ("wide", "narrow"):
        width, rows, cursor = seen[key]
        assert all(len(row) <= width for row in rows), key
        assert "".join(r.strip() for r in rows).count("x" * 300) == 1, "nothing lost"
        assert cursor == len(rows) - 1, "still on the error line"
    assert len(seen["narrow"][1]) > len(seen["wide"][1])


def test_fold_breaks_at_a_space_else_mid_word_and_leaves_room_for_the_indent():
    from navigator.widgets.shell.error_dialog.error_dialog import fold

    assert fold("short", 10, 4) == [(0, 5)]
    line = "aaaa bbbb cccc"
    assert [line[s:e] for s, e in fold(line, 9, 2)] == ["aaaa bbbb", "cccc"]
    assert [line[s:e] for s, e in fold(line, 8, 2)] == ["aaaa", "bbbb", "cccc"]
    rows = fold("x" * 20, 8, 3)
    assert [e - s for s, e in rows] == [8, 5, 5, 2]


def test_the_traceback_is_highlighted_and_keeps_its_colours_when_folded(nav):
    app = navigator(nav)
    seen = {}

    def look(key):
        def act(a):
            trace = a.modal.trace
            seen[key] = (list(trace.items), list(trace.spans), a.modal)
            seen[key + " colours"] = (trace.style.fg,
                                      trace.part_style("token", classes=("generic", "error")).fg)
        return act

    run_app(app, [lambda a: a.spawn(failing_long()), BOX_UP, look("wide"), ResizeEvent(70, 24),
                  lambda a: None, look("narrow")])
    for key in ("wide", "narrow"):
        rows, spans, box = seen[key]
        assert len(rows) == len(spans)
        tokens = {(rows[i][s:e], classes) for i, row_spans in enumerate(spans) for s, e, classes in row_spans}
        assert ("Traceback (most recent call last):", ("generic", "traceback")) in tokens
        assert ("test_error_dialog.Boom", ("generic", "error")) in tokens
        assert any(c == ("name", "builtin") and t.startswith('"') for t, c in tokens), "the file names"
    # The exception is painted in the keyword's colour, not the text's.
    plain, error = seen["wide colours"]
    assert plain is not None and error is not None and error != plain

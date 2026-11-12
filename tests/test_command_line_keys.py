"""The command line's own keys: DN's ``TCommandLine`` overwrite mode (Ins with text on the line)."""

from __future__ import annotations

import pytest

from conftest import FakeTerminal, run_app
from navkit.events import KeyEvent, PasteEvent

from navigator.__main__ import Navigator
from navigator.settings import SETTINGS


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    (tmp_path / "a.txt").write_text("a")
    return Navigator(tmp_path, tmp_path, terminal=FakeTerminal(80, 24))


def typed(text):
    return [KeyEvent(c, c) for c in text]


def line(app, keys):
    seen = {}
    run_app(app, [*keys, lambda a: seen.update(value=a.shell.command_line.value, cursor=a.shell.command_line.cursor,
                                                block=a.shell.block_insert, marked=set(a.manager.left.marked))])
    return seen


def test_ins_toggles_overwrite_and_typing_replaces(app):
    seen = line(app, [*typed("abc"), KeyEvent("home"), KeyEvent("insert"), *typed("X")])
    assert (seen["value"], seen["cursor"], seen["block"]) == ("Xbc", 1, True)


def test_ins_again_inserts(app):
    seen = line(app, [*typed("abc"), KeyEvent("home"), KeyEvent("insert"), *typed("X"), KeyEvent("insert"),
                      *typed("Y")])
    assert (seen["value"], seen["block"]) == ("XYbc", False)


def test_overwrite_at_the_end_appends(app):
    seen = line(app, [*typed("ab"), KeyEvent("insert"), *typed("c")])
    assert seen["value"] == "abc"


def test_on_an_empty_line_ins_tags_instead(app):
    def on_file(a):
        panel = a.manager.left
        panel.cursor = [e.name for e in panel.items].index("a.txt")

    seen = line(app, [on_file, KeyEvent("insert")])
    assert "a.txt" in seen["marked"] and seen["block"] is False


def test_block_insert_cursor_swaps_the_shapes(app):
    SETTINGS.interface.block_insert_cursor = True
    seen = line(app, [*typed("ab"), KeyEvent("insert")])
    assert seen["block"] is False


def test_the_mode_outlives_a_cleared_line(app):
    seen = line(app, [*typed("ab"), KeyEvent("insert"), KeyEvent("escape"), *typed("ab"), KeyEvent("home"),
                      *typed("Z")])
    assert seen["value"] == "Zb"


def test_a_paste_still_inserts_in_overwrite(app):
    seen = line(app, [*typed("ab"), KeyEvent("home"), KeyEvent("insert"), PasteEvent("XY")])
    assert seen["value"] == "XYab"


def stops(app, text, start_key, key):
    """The caret after each press of *key* (Ctrl+Left or Right) on *text*, from *start_key*."""
    seen = []
    actions = [*typed(text), KeyEvent(start_key)]
    for _ in range(4):
        actions += [key, lambda a: seen.append(a.shell.command_line.cursor)]
    run_app(app, actions)
    return seen


def test_ctrl_left_stops_at_dn_s_separators(app):
    # ``kbCtrlLeft`` over ``Separators``: each ``/`` and the blank, not only blanks.
    assert stops(app, "cd /usr/local/bin", "end", KeyEvent("left", ctrl=True)) == [14, 8, 4, 0]


def test_ctrl_right_stops_at_dn_s_separators(app):
    assert stops(app, "cd /usr/local/bin", "home", KeyEvent("right", ctrl=True)) == [4, 8, 14, 17]


def test_dots_and_commas_end_words_too(app):
    assert stops(app, "a.b,c", "end", KeyEvent("left", ctrl=True))[:3] == [4, 2, 0]


def test_another_input_line_still_stops_only_at_blanks():
    from navkit.application import Application
    from navkit.widget import Widget
    from navml.widgets.dialog.input_line import InputLine

    root = Widget()
    field = InputLine(parent=root)
    app = Application(root, terminal=FakeTerminal())
    field.focus()
    seen = []
    run_app(app, [lambda a: setattr(field, "value", "cd /usr/local"), lambda a: setattr(field, "cursor", 13),
                  KeyEvent("left", ctrl=True), lambda a: seen.append(field.cursor)])
    assert seen == [3]

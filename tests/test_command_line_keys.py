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


CTRL_BACKSPACE = KeyEvent("backspace", ctrl=True)


def presses(app, text, count, before=()):
    seen = []
    actions = [*typed(text), *before]
    for _ in range(count):
        actions += [CTRL_BACKSPACE, lambda a: seen.append((a.shell.command_line.value, a.shell.command_line.cursor))]
    run_app(app, actions)
    return seen


def test_ctrl_backspace_deletes_the_word_and_then_its_separators(app):
    # DN's ``#127``: the word before the caret, then the separators before it.
    assert presses(app, "cd /usr/local", 3) == [("cd /usr", 7), ("cd", 2), ("", 0)]


def test_ctrl_backspace_after_a_separator_takes_the_separators(app):
    assert presses(app, "cd /usr/", 1) == [("cd /usr", 7)]


def test_ctrl_backspace_takes_a_selection_instead(app):
    assert presses(app, "cd /usr/local", 1, before=[KeyEvent("left", ctrl=True, shift=True)]) == [("cd /usr/", 8)]


def test_ctrl_backspace_on_an_empty_line_does_nothing(app):
    seen = {}
    run_app(app, [CTRL_BACKSPACE, lambda a: seen.update(value=a.shell.command_line.value,
                                                        cursor=a.manager.left.cursor)])
    assert seen == {"value": "", "cursor": 0}


def caret(app, keys):
    seen = {}
    run_app(app, [*keys, lambda a: seen.update(cursor=a.shell.command_line.cursor, value=a.shell.command_line.value,
                                                panel=a.manager.left.cursor)])
    return seen


def test_ctrl_d_steps_a_character_on(app):
    assert caret(app, [*typed("abc"), KeyEvent("home"), KeyEvent("d", ctrl=True)])["cursor"] == 1


def test_ctrl_d_stops_at_the_end(app):
    assert caret(app, [*typed("ab"), KeyEvent("d", ctrl=True)])["cursor"] == 2


def test_ctrl_f_steps_a_word_on(app):
    assert caret(app, [*typed("cd /usr/local"), KeyEvent("home"), KeyEvent("f", ctrl=True)])["cursor"] == 4


def test_ctrl_home_and_end_are_the_line_s_with_text_on_it(app):
    seen = caret(app, [*typed("abc"), KeyEvent("home", ctrl=True)])
    assert (seen["cursor"], seen["panel"]) == (0, 0)


def test_ctrl_end_on_a_line_with_text(app):
    seen = caret(app, [*typed("abc"), KeyEvent("home"), KeyEvent("end", ctrl=True)])
    assert (seen["cursor"], seen["panel"]) == (3, 0)


def test_with_the_line_empty_ctrl_end_is_the_panel_s(app):
    seen = caret(app, [KeyEvent("end", ctrl=True), KeyEvent("d", ctrl=True), KeyEvent("f", ctrl=True)])
    assert seen["panel"] == len(app.manager.left.items) - 1 and seen["value"] == ""


def test_ctrl_s_with_text_on_the_line_still_starts_quick_search(app):
    # DN's ^S stepped the caret back; here it is Quick search (asked for), a departure.
    seen = {}
    run_app(app, [*typed("ab"), KeyEvent("s", ctrl=True),
                  lambda a: seen.update(search=a.manager.left.quick_search, value=a.shell.command_line.value)])
    assert seen == {"search": "", "value": "ab"}


def copied(app, keys):
    from navigator.lib.file_ops.clip import CLIP

    seen = {}
    run_app(app, [*keys, KeyEvent("insert", ctrl=True),
                  lambda a: seen.update(clipboard=list(a.terminal.clipboard), clip=bool(CLIP))])
    return seen


def test_ctrl_ins_with_text_copies_the_line_not_the_files(app):
    # A departure: DN's panel always took Ctrl+Ins for the names (``_CtrlIns``).
    seen = copied(app, typed("echo hi"))
    assert [text for text, _ in seen["clipboard"]] == ["echo hi"] and seen["clip"] is False


def test_ctrl_ins_copies_the_line_s_selection(app):
    seen = copied(app, [*typed("echo hi"), KeyEvent("left", ctrl=True, shift=True)])
    assert [text for text, _ in seen["clipboard"]] == ["hi"]


@pytest.mark.parametrize("before, pasted, after", [("ls", "-la", "ls-la"), ("echo '", "hi there", "echo 'hi there")])
def test_a_paste_goes_on_as_pasted(app, before, pasted, after):
    # A departure: DN's Shift+Ins added ``cmInsertName``'s blanks.
    assert line(app, [*typed(before), PasteEvent(pasted)])["value"] == after


def test_a_double_click_on_the_line_selects_a_word(app):
    # navml's mouse kept: DN's double click opened Commands history (a departure).
    from navkit.events import DoubleClickEvent, MouseClickEvent

    seen = {}

    def double(a):
        line = a.shell.command_line
        x = line.prompt_width + 6  # inside ``world``
        a.spawn(line.on_double_click(DoubleClickEvent.of(MouseClickEvent(x, 0, "left", "press"))))

    run_app(app, [*typed("hello world"), double, lambda a: None,
                  lambda a: seen.update(selected=a.shell.command_line.selected_text, modal=a.modal)])
    assert seen == {"selected": "world", "modal": None}


def painted_row(line):
    from navkit.screen import ScreenBuffer

    buffer = ScreenBuffer(line.width, 1)
    line.render(buffer)
    return "".join(buffer.get(x, 0)[0] or " " for x in range(line.width))


def test_the_text_reaches_the_last_column(app):
    # DN painted to the row's end; the last column was never the line's here.
    seen = {}

    def fill(a):
        line = a.shell.command_line
        line.set_text("x" * (line.width - line.prompt_width))
        line.home()

    def look(a):
        line = a.shell.command_line
        seen.update(row=painted_row(line), first=line.first)

    run_app(app, [fill, lambda a: None, look])
    assert seen["row"][-1] == "x" and seen["first"] == 0


def test_the_caret_at_the_end_of_a_long_line_is_in_the_last_column(app):
    seen = {}

    def fill(a):
        line = a.shell.command_line
        line.set_text("x" * (line.width - line.prompt_width + 5))

    run_app(app, [fill, lambda a: None,
                  lambda a: seen.update(column=a.shell.command_line.caret_column(), width=a.shell.command_line.width)])
    assert seen["column"] == seen["width"] - 1

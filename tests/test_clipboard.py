"""The clipboard: OSC 52 both ways, the desktop's tools, and the input line's keys."""

from __future__ import annotations

import base64

import pytest

from conftest import FakeTerminal, awaited, mounted, run_app, settle
from navkit import clipboard
from navkit.application import Application
from navkit.capabilities import TerminalInfo
from navkit.events import DoubleClickEvent, KeyEvent, MouseClickEvent, PasteEvent
from navkit.terminal import InputParser, clipboard_osc, clipboard_query
from navkit.widget import Widget
from navml.widgets.dialog.input_line import InputLine


# -- OSC 52 ------------------------------------------------------------------


def test_a_copy_is_osc_52_with_the_text_in_base64():
    assert clipboard_osc("héllo") == "\x1b]52;c;" + base64.b64encode("héllo".encode()).decode() + "\x07"
    assert clipboard_osc("x", primary=True).startswith("\x1b]52;p;")
    assert clipboard_query() == "\x1b]52;c;?\x07"


def test_the_terminal_s_answer_is_a_paste_even_split_across_reads():
    reply = clipboard_osc("two\nlines").encode()
    parser = InputParser()
    assert parser.feed(reply[:6]) == []
    assert not parser.pending_escape  # a slow answer is not a lone ESC
    assert parser.feed(reply[6:]) == [PasteEvent("two\nlines")]


def test_an_answer_ended_by_st_is_read_too_and_what_follows_is_typed():
    events = InputParser().feed(b"\x1b]52;c;aGk=\x1b\\x")
    assert events[0] == PasteEvent("hi")
    assert events[1].key == "x"


def test_an_empty_answer_is_no_paste():
    assert InputParser().feed(b"\x1b]52;c;\x07") == []


def test_alt_bracket_still_types_when_no_answer_follows():
    parser = InputParser()
    assert parser.feed(b"\x1b]") == []
    [key] = parser.flush()
    assert (key.key, key.alt) == ("]", True)


@pytest.mark.parametrize("value, expected", [("", True), ("off", False), ("on", True)])
def test_navkit_clipboard_switches_osc_52(value, expected):
    info = TerminalInfo.detect({"TERM": "xterm-256color", "NAVKIT_CLIPBOARD": value})
    assert info.clipboard is expected


def test_the_linux_console_gets_no_osc_52():
    assert not TerminalInfo.detect({"TERM": "linux"}).clipboard


# -- the desktop's tools -------------------------------------------------------


def test_wayland_is_asked_before_x():
    which = lambda name: f"/usr/bin/{name}"
    env = {"WAYLAND_DISPLAY": "wayland-0", "DISPLAY": ":0"}
    assert clipboard.copy_command(env=env, which=which) == ["wl-copy"]
    assert clipboard.paste_command(primary=True, env=env, which=which) == [
        "wl-paste", "--no-newline", "--primary"]


def test_x_takes_whichever_tool_is_installed():
    env = {"DISPLAY": ":0"}
    only_xsel = lambda name: "/usr/bin/xsel" if name == "xsel" else None
    assert clipboard.copy_command(env=env, which=only_xsel) == ["xsel", "--clipboard", "--input"]
    assert clipboard.paste_command(env=env, which=only_xsel) == ["xsel", "--clipboard", "--output"]


def test_no_display_means_no_tool():
    assert clipboard.copy_command(env={}, which=lambda name: "/bin/true") is None


# -- the application -------------------------------------------------------------


def test_a_copy_goes_to_the_terminal():
    app = Application(Widget(), terminal=FakeTerminal())
    app.copy_to_clipboard("text")
    app.copy_to_clipboard("")  # nothing to copy is not a copy
    assert app.terminal.clipboard == [("text", False)]


def test_a_paste_asked_for_without_a_tool_asks_the_terminal():
    # FakeTerminal is not a tty, so no desktop tool is tried.
    app = Application(Widget(), terminal=FakeTerminal())
    run_app(app, [lambda a: a.request_clipboard(primary=True)])
    assert app.terminal.clipboard_queries == [True]


def test_a_private_clipboard_keeps_a_copy_from_the_terminal_and_pastes_it_back():
    root = Widget()
    field = InputLine(parent=root)
    app = Application(root, terminal=FakeTerminal())
    app.system_clipboard = False
    field.focus()
    run_app(app, [lambda a: a.copy_to_clipboard("kept"), lambda a: a.request_clipboard()])
    assert app.terminal.clipboard == [] and app.terminal.clipboard_queries == []
    assert field.value == "kept"


def test_the_private_primary_selection_is_its_own():
    root = Widget()
    field = InputLine(parent=root)
    app = Application(root, terminal=FakeTerminal())
    app.system_clipboard = False
    field.focus()
    run_app(app, [lambda a: a.copy_to_clipboard("clip"),
                  lambda a: a.copy_to_clipboard("sel", primary=True),
                  lambda a: a.request_clipboard(primary=True)])
    assert field.value == "sel"


def test_a_copy_made_with_the_system_clipboard_is_there_once_it_is_off():
    root = Widget()
    field = InputLine(parent=root)
    app = Application(root, terminal=FakeTerminal())
    field.focus()
    run_app(app, [lambda a: a.copy_to_clipboard("before"),
                  lambda a: setattr(a, "system_clipboard", False),
                  lambda a: a.request_clipboard()])
    assert app.terminal.clipboard == [("before", False)]
    assert field.value == "before"


# -- the input line --------------------------------------------------------------


def line(value: str = "hello big world") -> InputLine:
    widget = mounted(InputLine())
    widget.value = value
    settle()
    return widget


def press(x, action="press", button="left", **kw):
    return MouseClickEvent(x=x, y=0, button=button, action=action, **kw)


def test_a_drag_selects_and_becomes_the_primary_selection():
    widget = line()
    # Text starts in column 1, past the left arrow.
    awaited(widget.on_mouse_click(press(1 + 6)))
    awaited(widget.on_mouse_click(press(1 + 9, "move")))
    assert widget.selected_text == "big"
    awaited(widget.on_mouse_click(press(1 + 9, "release")))
    assert widget.application.terminal.clipboard == [("big", True)]


def test_a_click_without_a_drag_selects_nothing():
    widget = line()
    awaited(widget.on_mouse_click(press(3)))
    awaited(widget.on_mouse_click(press(3, "release")))
    assert widget.selected_text == ""
    assert widget.application.terminal.clipboard == []


def test_a_double_click_selects_the_word():
    widget = line()
    awaited(widget.on_double_click(DoubleClickEvent.of(press(1 + 7))))
    assert widget.selected_text == "big"


def test_ctrl_insert_copies_the_selection_or_else_the_whole_line():
    widget = line()
    awaited(widget.on_key(KeyEvent("insert", ctrl=True)))
    widget.anchor, widget.cursor = 0, 5
    awaited(widget.on_key(KeyEvent("insert", ctrl=True)))
    assert widget.application.terminal.clipboard == [
        ("hello big world", False), ("hello", False)]


def test_ctrl_c_copies_only_a_selection():
    widget = line()
    assert not awaited(widget.on_key(KeyEvent("c", ctrl=True)))
    widget.anchor, widget.cursor = 6, 9
    assert awaited(widget.on_key(KeyEvent("c", ctrl=True)))
    assert widget.application.terminal.clipboard == [("big", False)]


def test_shift_delete_cuts():
    widget = line()
    widget.anchor, widget.cursor = 5, 9
    awaited(widget.on_key(KeyEvent("delete", shift=True)))
    assert widget.value == "hello world"
    assert widget.application.terminal.clipboard == [(" big", False)]


@pytest.mark.parametrize("key", [KeyEvent("v", ctrl=True), KeyEvent("insert", shift=True)])
def test_ctrl_v_and_shift_insert_ask_for_the_clipboard(key, monkeypatch):
    widget = line()
    asked = []
    monkeypatch.setattr(widget.application, "request_clipboard",
                        lambda primary=False: asked.append(primary))
    awaited(widget.on_key(key))
    assert asked == [False]


def test_a_middle_click_asks_for_the_primary_selection(monkeypatch):
    widget = line()
    asked = []
    monkeypatch.setattr(widget.application, "request_clipboard",
                        lambda primary=False: asked.append(primary))
    awaited(widget.on_mouse_click(press(2, button="middle")))
    assert asked == [True]


def test_a_paste_replaces_the_selection_on_one_line():
    widget = line()
    widget.anchor, widget.cursor = 6, 9
    awaited(widget.on_paste(PasteEvent("small\nand")))
    assert widget.value == "hello small and world"


def test_a_paste_reaches_the_focused_line_when_the_application_declines_it():
    root = Widget()
    field = InputLine(parent=root)
    app = Application(root, terminal=FakeTerminal())
    field.focus()
    run_app(app, [PasteEvent("pasted")])
    assert field.value == "pasted"

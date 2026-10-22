"""Window numbers, Win+1 .. Win+9, and Interface's *Window strip* on the menu bar."""

from __future__ import annotations

from conftest import run_app, settle
from navkit.events import KeyEvent, MouseClickEvent
from navkit.reactive import unbind
from navkit.screen import ScreenBuffer
from navkit.terminal import InputParser
from navml.widgets import Window
from navml.widgets.desktop import Desktop
from navml.widgets.window_strip import WindowStrip
from navigator.settings import SETTINGS
from test_nav import navigator, tree  # noqa: F401 - fixtures


def super_key(digit: str) -> KeyEvent:
    return KeyEvent(digit, digit, super_=True)


def notes(title: str) -> Window:
    return Window(title=title, x=10, y=3, width=30, height=8)


def opener(*titles: str):
    def open_them(app):
        for title in titles:
            app.shell.desktop.open(notes(title))
    return open_them


def top_row(app) -> str:
    buffer = ScreenBuffer(80, 24)
    app.root.render_tree(buffer)
    return "".join(buffer.get(x, 0)[0] or " " for x in range(buffer.width))


# -- the Super key -----------------------------------------------------------


def test_a_kitty_super_key_is_named_super_and_types_nothing():
    parser = InputParser()
    (one,) = parser.feed(b"\x1b[49;9u")
    assert one.name == "super+1" and one.super_ and not one.is_printable
    *_, both = parser.feed(b"\x1b[49;13u")
    assert both.name == "ctrl+super+1"
    *_, plain = parser.feed(b"\x1b[49u")
    assert plain.name == "1" and plain.is_printable


def test_a_key_spec_may_name_super():
    from navkit.commands import parse_key

    assert parse_key("Super+Ctrl+1") == "ctrl+super+1"
    assert super_key("1").matches("super+1")


# -- numbers -----------------------------------------------------------------


def test_windows_take_the_lowest_free_number_and_keep_it_when_raised():
    desktop = Desktop(width=80, height=20)
    a, b, c = (desktop.open(notes(t)) for t in "abc")
    assert [w.number for w in (a, b, c)] == [1, 2, 3]
    desktop.activate(a)
    assert [w.number for w in (a, b, c)] == [1, 2, 3]
    b.close()
    assert b.number == 0
    d = desktop.open(notes("d"))
    assert d.number == 2
    assert desktop.window_numbered(2) is d and desktop.window_numbered(5) is None
    settle()
    assert list(desktop.open_windows) == [a, c, d]


def test_a_tenth_window_has_no_number():
    desktop = Desktop(width=80, height=20)
    windows = [desktop.open(notes(str(n))) for n in range(10)]
    assert [w.number for w in windows] == [*range(1, 10), 0]


def test_super_digit_brings_that_window_forward(tree):
    app = navigator(tree)
    run_app(app, [opener("Notes", "Todo"), super_key("1"), lambda a: None])
    assert app.manager.number == 1
    assert app.shell.desktop.active_window is app.manager
    assert app.manager._holds(app.focused)
    assert app.shell.command_line.value == ""


def test_super_digit_with_no_such_window_does_nothing(tree):
    app = navigator(tree)
    run_app(app, [opener("Notes"), super_key("7"), lambda a: None])
    assert app.shell.desktop.active_window.title == "Notes"
    assert app.shell.command_line.value == ""


def test_the_window_list_shows_the_numbers(tree):
    seen = []
    app = navigator(tree)
    run_app(app, [opener("Notes"), KeyEvent("0", "0", alt=True), lambda a: None,
                  lambda a: seen.append([a.modal.windows.row_text(i, w)
                                         for i, w in enumerate(a.modal.windows.items)]),
                  KeyEvent("escape")])
    assert seen == [[" 2 Notes", f" 1 {tree}"]]


# -- the strip ---------------------------------------------------------------


def test_the_strip_shows_numbers_by_default_and_can_be_turned_off(tree):
    app = navigator(tree)
    run_app(app, [opener("Notes"), lambda a: None])
    strip = app.shell.window_strip
    assert strip.visible and not strip.labels
    SETTINGS.interface.window_strip = "off"
    settle()
    assert not strip.visible
    assert " 1 " not in top_row(app)


def test_numbers_alone_kept_to_the_clock(tree):
    SETTINGS.interface.window_strip = "numbers"
    rows = []
    app = navigator(tree)
    run_app(app, [opener("Notes", "Todo"), lambda a: rows.append(top_row(a))])
    strip = app.shell.window_strip
    menu = app.shell.menu
    assert strip.visible and not strip.labels
    assert strip.x == menu.item_span(len(menu.entries()))[0] + 1
    assert strip.x + strip.width < app.shell.clock.x
    assert [(text, w) for _, text, w in strip.chips()] == [
        (" 1 ", app.manager), (" 2 ", strip.windows()[1]), (" 3 ", strip.windows()[2])]
    assert [start for start, _, _ in strip.chips()] == [strip.width - 9, strip.width - 6, strip.width - 3]
    clock = app.shell.clock.x
    assert rows[0][clock - 10:clock] == " 1  2  3  "


def test_full_chips_name_the_windows_and_the_top_one_is_selected(tree):
    SETTINGS.interface.window_strip = "full"
    app = navigator(tree)
    run_app(app, [opener("Notes"), lambda a: None])
    strip = app.shell.window_strip
    (_, first, _), (_, second, _) = strip.chips()
    assert first.startswith(" 1 test_") and second == " 2 Notes "
    selected = strip.part_style("chip", selected=True)
    plain = strip.part_style("chip")
    assert selected != plain


def test_names_are_cut_evenly_then_windows_counted_off(tree):
    SETTINGS.interface.window_strip = "full"
    app = navigator(tree)
    run_app(app, [opener("A long window title", "Another long title"), lambda a: None])
    strip = app.shell.window_strip
    unbind(strip, WindowStrip.width)
    strip.width = 20
    texts = [text for _, text, _ in strip.chips()]
    assert sum(map(len, texts)) <= 20 and len(texts) == 3
    assert all(text.startswith(f" {n} ") for n, text in enumerate(texts, 1))
    strip.width = 7
    assert [text for _, text, _ in strip.chips()] == [" 1 "]
    assert strip.hidden() == 2


def test_one_window_shows_no_strip(tree):
    SETTINGS.interface.window_strip = "numbers"
    app = navigator(tree)
    run_app(app, [lambda a: None])
    assert app.shell.window_strip.chips() == []


def test_a_click_on_a_chip_brings_its_window_forward(tree):
    SETTINGS.interface.window_strip = "numbers"
    app = navigator(tree)

    def click(a):
        strip = a.shell.window_strip
        start, _, _ = strip.chips()[0]
        a.post_event(MouseClickEvent(strip.x + start + 1, 0, "left", "press"))

    run_app(app, [opener("Notes"), click, lambda a: None])
    assert app.shell.desktop.active_window is app.manager


def test_the_strip_hides_with_the_menu_bar_and_the_windows(tree):
    SETTINGS.interface.window_strip = "numbers"
    app = navigator(tree)
    seen = []
    run_app(app, [opener("Notes"), KeyEvent("o", ctrl=True),
                  lambda a: seen.append(a.shell.window_strip.visible),
                  KeyEvent("o", ctrl=True),
                  lambda a: seen.append(a.shell.window_strip.visible)])
    assert seen == [False, True]
    SETTINGS.interface.hide_menu_bar = True
    settle()
    assert not app.shell.window_strip.visible


def test_alt_shift_f_key_brings_that_window_forward(tree):
    app = navigator(tree)
    run_app(app, [opener("Notes", "Todo"), KeyEvent("f2", alt=True, shift=True), lambda a: None])
    assert app.shell.desktop.active_window.title == "Notes"


def test_a_legacy_alt_shift_f_key_decodes_to_its_binding():
    (key,) = InputParser().feed(b"\x1b[1;4Q")
    assert key.name == "alt+shift+f2"


def test_a_digit_in_the_window_list_chooses_that_window(tree):
    app = navigator(tree)
    run_app(app, [opener("Notes", "Todo"), KeyEvent("0", "0", alt=True), lambda a: None,
                  KeyEvent("1", "1"), lambda a: None])
    assert app.modal is None
    assert app.shell.desktop.active_window is app.manager
    assert app.manager._holds(app.focused)


def test_a_digit_no_window_has_leaves_the_list_up(tree):
    app = navigator(tree)
    seen = []
    run_app(app, [opener("Notes"), KeyEvent("0", "0", alt=True), lambda a: None,
                  KeyEvent("7", "7"), lambda a: seen.append(type(a.modal).__name__),
                  KeyEvent("escape")])
    assert seen == ["WindowManagerDialog"]
    assert app.shell.desktop.active_window.title == "Notes"

"""*ASCII Chart*: DOS Navigator's ``TASCIIChart``, ``TTable`` and ``TReport`` (ASCIITAB.PAS)."""

from __future__ import annotations

import pytest

from conftest import FakeTerminal, run_app
from navkit.application import Application
from navkit.events import DoubleClickEvent, KeyEvent
from navkit.widget import Widget

from navigator.widgets.shell.ascii_chart import AsciiChart
from navigator.widgets.shell.ascii_chart import ascii_chart as module
from navigator.widgets.shell.char_table.char_table import glyph


@pytest.fixture(autouse=True)
def starts_on_p(monkeypatch):
    monkeypatch.setitem(module._last, "code", 112)


def run(*actions):
    """The chart, then *actions*; what it answered (``"open"`` if still up), and the chart."""
    app = Application(Widget(), terminal=FakeTerminal(80, 25))
    chart = AsciiChart()
    jobs = []
    run_app(app, [lambda a: jobs.append(a.spawn(chart.execute(a))), lambda a: None, *actions,
                  lambda a: None])
    job = jobs[0]
    return ("open" if job.cancelled() or not job.done() else job.result()), chart


def test_the_chart_shows_every_code_page_437_glyph():
    assert [glyph(c) for c in (1, 65, 0x7F, 0xB3, 0xDB)] == ["☺", "A", "⌂", "│", "█"]


def test_it_opens_on_p_and_reports_it():
    _, chart = run()
    assert chart.table.code == 112
    assert chart.report.text == "  Char: p Decimal: 112 Hex: 70"


def test_the_arrows_move_and_enter_takes_the_character():
    answer, _ = run(KeyEvent("right"), KeyEvent("down"), KeyEvent("enter"))
    assert answer == 112 + 1 + 32


def test_home_end_and_the_edges():
    answer, _ = run(KeyEvent("home"), KeyEvent("left"), KeyEvent("up"), KeyEvent("enter"))
    assert answer == 0
    answer, _ = run(KeyEvent("end"), KeyEvent("enter"))
    assert answer == 255


def test_a_character_typed_is_taken_at_once():
    answer, _ = run(KeyEvent("x", "x"))
    assert answer == ord("x")


def test_escape_takes_nothing():
    answer, _ = run(KeyEvent("escape"))
    assert answer is None


def test_a_double_click_takes_the_character_under_it():
    answer, chart = run(lambda a: a.spawn(chart_double_click(a)))
    assert answer == 2 * 32 + 1


async def chart_double_click(app):
    chart = app.modal
    await chart.table.on_double_click(DoubleClickEvent(x=1, y=2, button="left"))


def test_the_next_chart_opens_on_the_character_last_taken():
    run(KeyEvent("right"), KeyEvent("enter"))
    assert AsciiChart().table.code == 113


# -- Ctrl+B, Utilities > Character table: the command line -------------------------------------------


@pytest.fixture
def nav(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.subshell.Subshell.start", lambda self, *a, **k: None)
    monkeypatch.setattr("navigator.widgets.shell.console.Console.start", lambda self, argv=None: None)
    (tmp_path / "text.txt").write_text("abc\n")
    return tmp_path


def navigator(path):
    from navigator.__main__ import Navigator

    return Navigator(path, path, terminal=FakeTerminal(80, 24))


def test_ctrl_b_puts_the_character_picked_on_the_command_line(nav):
    app = navigator(nav)
    seen = []
    run_app(app, [KeyEvent("b", ctrl=True), lambda a: None,
                  lambda a: seen.append(a.modal.title if a.modal else None),
                  KeyEvent("right"), KeyEvent("enter"), lambda a: None])
    assert seen == ["ASCII Chart"]
    assert app.shell.command_line.value == "q"


def test_the_utilities_menu_item_runs_it(nav):
    from navigator.commands import AsciiTable

    app = navigator(nav)
    run_app(app, [lambda a: a.spawn(a.run_command(AsciiTable)), lambda a: None,
                  KeyEvent("x", "x"), lambda a: None])
    assert app.shell.command_line.value == "x"


def test_code_zero_puts_nothing(nav):
    app = navigator(nav)
    run_app(app, [KeyEvent("b", ctrl=True), lambda a: None, KeyEvent("home"),
                  KeyEvent("enter"), lambda a: None])
    assert app.shell.command_line.value == ""


def test_a_hidden_command_line_takes_no_character(nav):
    from navigator.commands import AsciiTable
    from navigator.settings import SETTINGS

    SETTINGS.interface.hide_command_line = True
    app = navigator(nav)
    seen = []
    run_app(app, [lambda a: seen.append(a.command_enabled(AsciiTable))])
    assert seen == [False]


def test_in_an_editor_ctrl_b_is_still_the_column_block_chord(nav):
    from navigator.settings import SETTINGS

    SETTINGS.interface.store_editor_position = False
    app = navigator(nav)
    seen = []

    def look(a):
        window = a.shell.desktop.active_window
        seen.append((a.modal is None, window.editor.vertical_blocks))

    run_app(app, [KeyEvent("end"), KeyEvent("f4"), lambda a: None,
                  KeyEvent("b", ctrl=True), KeyEvent("v", "v"), lambda a: None, look])
    assert seen == [(True, True)]

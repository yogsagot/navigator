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

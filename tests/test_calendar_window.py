"""Utilities > Calendar: TVDEMO's calendar window, a departure (DN had none)."""

from __future__ import annotations

import datetime

import pytest

from conftest import FakeTerminal, Until, run_app
from navkit.events import KeyEvent

from navigator.__main__ import Navigator


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.subshell.Subshell.start", lambda self, *a, **k: None)
    return Navigator(tmp_path, tmp_path, terminal=FakeTerminal(80, 24))


def calendar(app):
    from navigator.widgets.shell.calendar_window import CalendarWindow

    return next((w for w in app.shell.desktop.windows() if isinstance(w, CalendarWindow)), None)


def open_calendar(a):
    from navigator.widgets.shell.commands import OpenCalendar

    a.spawn(a.run_command(OpenCalendar))


def test_the_menu_opens_one_calendar_in_the_middle_on_today_and_its_keys_page_it(app):
    seen = {}

    def look(a):
        w = calendar(a)
        seen.update(rect=(w.x, w.y, w.width, w.height), focused=a.focused is w.month, day=w.month.day)

    run_app(app, [open_calendar, Until(lambda a: calendar(a) is not None), look,
                  KeyEvent("pagedown"), lambda a: None,
                  lambda a: seen.update(paged=calendar(a).month.day),
                  open_calendar, lambda a: None,
                  lambda a: seen.update(count=sum(1 for w in a.shell.desktop.windows() if w is calendar(a))),
                  KeyEvent("escape"), lambda a: None, lambda a: seen.update(gone=calendar(a) is None)])
    desktop_width = 80
    assert seen["rect"][2:] == (26, 13) and seen["rect"][0] == (desktop_width - 26) // 2
    assert seen["focused"] and seen["day"] == datetime.date.today()
    assert seen["paged"].month == (datetime.date.today().month % 12) + 1
    assert seen["count"] == 1 and seen["gone"]


def test_the_window_paints_the_month_and_the_weekdays(app):
    painted = {}

    def look(a):
        today = datetime.date.today()
        buffer = a._front
        text = "\n".join("".join(buffer.get(x, y)[0] or " " for x in range(buffer.width))
                         for y in range(buffer.height))
        painted.update(text=text, month=f"{today:%B} {today.year}")

    run_app(app, [open_calendar, Until(lambda a: calendar(a) is not None), lambda a: None, look])
    assert painted["month"] in painted["text"] and "Mo" in painted["text"] and "Calendar" in painted["text"]


def test_go_to_current_date_brings_today_back_from_a_click_or_alt_d(app):
    from navkit.events import MouseClickEvent

    seen = {}

    def click(a):
        button = calendar(a).today_button
        x, y = button.offset()
        x, y = x + button.x + 2, y + button.y
        a.post_event(MouseClickEvent(x, y, "left", "press"))
        a.post_event(MouseClickEvent(x, y, "left", "release"))

    run_app(app, [open_calendar, Until(lambda a: calendar(a) is not None),
                  KeyEvent("pagedown", ctrl=True), KeyEvent("tab"), lambda a: None,
                  lambda a: seen.update(away=calendar(a).month.day),
                  click, lambda a: None,
                  lambda a: seen.update(clicked=calendar(a).month.day, section=calendar(a).month.section,
                                        focused=a.focused is calendar(a).month),
                  KeyEvent("pagedown"), KeyEvent("d", "d", alt=True), lambda a: None,
                  lambda a: seen.update(alt=calendar(a).month.day, alt_focused=a.focused is calendar(a).month)])
    today = datetime.date.today()
    assert seen["away"] != today
    assert seen["clicked"] == today and seen["section"] == "days" and seen["focused"]
    assert seen["alt"] == today and seen["alt_focused"]


def test_today_keeps_its_mark_under_the_cursor(app):
    seen = {}

    def look(a):
        view = calendar(a).month
        seen.update(plain=view.part_style("day"), cursor=view.part_style("day", selected=True),
                    today=view.part_style("day", today=True),
                    both=view.part_style("day", selected=True, today=True))

    run_app(app, [open_calendar, Until(lambda a: calendar(a) is not None), lambda a: None, look])
    assert seen["both"] not in (seen["plain"], seen["cursor"], seen["today"])
    assert seen["both"].fg == seen["today"].fg and seen["both"].bg == seen["cursor"].bg

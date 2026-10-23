"""*Country support* (``[country]``): how a file's date and time are written."""

from __future__ import annotations

import os
import time
from datetime import datetime

import pytest

from conftest import FakeTerminal, mounted, run_app, settle
from navkit.events import KeyEvent
from navigator.__main__ import Navigator
from navigator.lib.appearance.scheme import default_scheme
from navigator.lib.config import country
from navigator.settings import SETTINGS, CountryData
from navigator.widgets import Panel
from navigator.widgets.file_ops.overwrite_query.overwrite_query import stamp as query_stamp
from navigator.widgets.setup.country_page import CountryPage
from navigator.widgets.shell.clock import clock as clock_module
from navigator.widgets.shell.clock import Clock
from navigator.widgets.shell.commands import CountrySetup

#: 17:05 on the 4th of March 2026, local time.
AFTERNOON = datetime(2026, 3, 4, 17, 5).timestamp()


@pytest.fixture
def quiet_console(monkeypatch):
    monkeypatch.setattr("navigator.widgets.shell.console.Console.start", lambda self, argv=None: None)


@pytest.mark.parametrize("order, text", [
    ("european", "04-03-2026 17:05"),
    ("us", "03/04/2026 17:05"),
    ("iso", "2026-03-04 17:05"),
])
def test_each_order_comes_with_its_separator_and_a_four_digit_year(order, text):
    SETTINGS.country.date_format = order
    assert country.stamp(AFTERNOON) == text


def test_european_and_24_hours_are_the_default():
    assert (CountryData.date_format.default, CountryData.time_format.default) == ("european", "24h")
    assert country.stamp(AFTERNOON) == "04-03-2026 17:05"


def test_a_custom_format_is_strftime_s_and_empty_is_european():
    SETTINGS.country.date_format = "custom"
    SETTINGS.country.custom_date = "%d %b %Y"
    assert country.date_text(AFTERNOON) == time.strftime("%d %b %Y", time.localtime(AFTERNOON))
    SETTINGS.country.custom_date = ""
    assert country.date_text(AFTERNOON) == "04-03-2026"


@pytest.mark.parametrize("hour, minute, text", [
    (0, 5, "12:05am"), (9, 30, "09:30am"), (12, 0, "12:00pm"), (17, 5, "05:05pm"), (23, 59, "11:59pm"),
])
def test_twelve_hours_are_dn_s_with_am_and_pm(hour, minute, text):
    SETTINGS.country.time_format = "12h"
    assert country.time_text(datetime(2026, 3, 4, hour, minute).timestamp()) == text


def test_the_stamp_s_width_follows_the_format():
    assert country.stamp_width() == 16
    SETTINGS.country.time_format = "12h"
    assert country.stamp_width() == 18
    SETTINGS.country.date_format = "custom"
    SETTINGS.country.custom_date = "%A %d %B %Y"
    # The longest weekday and month names are what it is measured by.
    widest = max(len(time.strftime("%A %d %B %Y", datetime(2000, m, d).timetuple()))
                 for m in range(1, 13) for d in range(22, 29))
    assert country.stamp_width() == widest + len(" 11:59pm")


def test_the_panel_s_date_column_is_as_wide_as_the_format(tmp_path):
    (tmp_path / "a").write_text("x")
    os.utime(tmp_path / "a", (AFTERNOON, AFTERNOON))
    panel = Panel(tmp_path, width=80, height=12)
    panel.stylesheet = default_scheme()
    panel = mounted(panel, size=(80, 12))
    panel.view_mode = "detailed"
    settle()
    widths = {key: width for key, _, width in panel.detail_columns}
    assert widths["date"] == 16
    SETTINGS.country.date_format = "us"
    SETTINGS.country.time_format = "12h"
    settle()
    widths = {key: width for key, _, width in panel.detail_columns}
    assert widths["date"] == 18
    entry = next(item for item in panel.items if item.name == "a")
    assert entry.display_date == "03/04/2026 05:05pm"


def test_the_overwrite_query_writes_its_dates_the_same_way():
    assert query_stamp(AFTERNOON) == "04-03-2026 (17:05)"
    SETTINGS.country.date_format = "iso"
    SETTINGS.country.time_format = "12h"
    assert query_stamp(AFTERNOON) == "2026-03-04 (05:05pm)"


def test_the_clock_takes_am_and_pm_in_twelve_hours(monkeypatch):
    monkeypatch.setattr(clock_module, "now", lambda: datetime(2026, 1, 1, 17, 5))
    clock = Clock()
    SETTINGS.country.time_format = "12h"
    assert clock.text() == "05:05pm"
    clock.blink = False
    assert clock.text() == "05 05pm"


def test_the_clock_widens_for_twelve_hours_and_keeps_to_the_corner(tmp_path, quiet_console):
    app = Navigator(tmp_path, tmp_path, terminal=FakeTerminal(80, 24))
    seen = []
    run_app(app, [
        lambda a: seen.append((a.shell.clock.x, a.shell.clock.width)),
        lambda a: setattr(SETTINGS.country, "time_format", "12h"),
        lambda a: seen.append((a.shell.clock.x, a.shell.clock.width)),
    ])
    assert seen == [(75, 5), (73, 7)]


def test_the_page_seeds_from_its_section_and_answers_for_it():
    section = CountryData()
    section.date_format, section.custom_date, section.time_format = "iso", "%Y%m%d", "12h"
    page = CountryPage(section=section)
    assert (page.date_format.value, page.time_format.value, page.custom_date.value) == (2, 0, "%Y%m%d")
    page.date_format.value = 3
    page.custom_date.value = " %d/%m/%y "
    page.time_format.value = 1
    assert page.first_day.value == 0
    page.first_day.value = 1
    assert page.accept() == {
        "date_format": "custom", "custom_date": "%d/%m/%y", "time_format": "24h", "first_day": "sunday"}


def test_the_page_s_example_follows_the_choices_before_ok():
    page = CountryPage(section=CountryData())
    assert page.example.text.startswith("Example: ")
    page.date_format.value = 2
    page.time_format.value = 0
    now = time.time()
    assert page.example.text == "Example: " + country.stamp_in(now, "%Y-%m-%d", True)


def test_ok_in_country_support_applies_and_saves(tmp_path, quiet_console):
    SETTINGS.path = tmp_path / "navigator.ini"
    app = Navigator(tmp_path, tmp_path, terminal=FakeTerminal(80, 24))

    def choose(a):
        a.modal.country.date_format.value = 1  # US
        a.modal.country.time_format.value = 0  # 12 hour

    run_app(app, [lambda a: a.spawn(a.run_command(CountrySetup)), lambda a: None, choose,
                  KeyEvent("enter"), lambda a: None])
    assert (SETTINGS.country.date_format, SETTINGS.country.time_format) == ("us", "12h")
    text = (tmp_path / "navigator.ini").read_text()
    assert "[country]" in text and "date_format = us" in text and "time_format = 12h" in text


@pytest.mark.parametrize("order, custom, typed", [
    ("us", "", "%m/%d/%Y"),
    ("iso", "", "%Y-%m-%d"),
    ("custom", "%d.%m.%y", "%d.%m.%y"),
    ("custom", "%d %b %Y", "%d-%m-%Y"),   # a name: no mask holds it
    ("custom", "%d-%m", "%d-%m-%Y"),      # no year
    ("custom", "%d/%m/%Y %d", "%d-%m-%Y"),  # a day twice
])
def test_a_date_is_typed_in_the_chosen_order_where_a_mask_can_hold_it(order, custom, typed):
    SETTINGS.country.date_format, SETTINGS.country.custom_date = order, custom
    assert country.typed_date_format() == typed


def test_navml_s_file_dialogs_write_dn_s_form_unless_told(tmp_path, quiet_console, monkeypatch):
    from navml.widgets.dialog.file_list import FileInfoPane, FileItem

    assert FileInfoPane.dn_stamp(AFTERNOON) == "04-03-26 17:05"
    monkeypatch.setattr(FileInfoPane, "stamp", FileInfoPane.__dict__["stamp"])
    Navigator(tmp_path, tmp_path, terminal=FakeTerminal(80, 24))
    SETTINGS.country.date_format = "iso"
    SETTINGS.country.time_format = "12h"
    pane = FileInfoPane()
    pane.item = FileItem("a.txt", False, 3, AFTERNOON)
    assert pane.lines()[1].endswith("2026-03-04 05:05pm")



def test_the_week_starts_on_monday_unless_sunday_is_chosen():
    assert CountryData.first_day.default == "monday" and country.first_weekday() == 0
    SETTINGS.country.first_day = "sunday"
    assert country.first_weekday() == 6


def test_a_dropped_calendar_starts_its_week_where_country_support_says(tmp_path, quiet_console, monkeypatch):
    from navml.widgets.dialog.date_button import Calendar, CalendarView

    monkeypatch.setattr(CalendarView, "default_first_weekday", CalendarView.__dict__["default_first_weekday"])
    assert Calendar().first_weekday == 0
    Navigator(tmp_path, tmp_path, terminal=FakeTerminal(80, 24))
    SETTINGS.country.first_day = "sunday"
    calendar = Calendar(None, datetime(2026, 10, 15).date())
    assert calendar.first_weekday == 6
    # October 2026 begins on a Thursday: the fifth column when Sunday is first.
    assert calendar.weeks()[0].index(datetime(2026, 10, 1).date()) == 4

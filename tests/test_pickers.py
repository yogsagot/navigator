"""The calendar and the clock face a date or time line's ``▐↓▌`` drops."""

from __future__ import annotations

import asyncio
import datetime

from navkit.events import KeyEvent, MouseClickEvent
from navkit.screen import ScreenBuffer

from navml.widgets.dialog.date_button import Calendar, DateButton
from navml.widgets.dialog.date_button.date_button import add_months
from navml.widgets.dialog.time_button import TimeButton, TimePicker

from conftest import FakeTerminal
from navkit.application import Application
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.date_field import DateField
from navml.widgets.dialog.time_field import TimeField


def keys(widget, *events):
    for event in events:
        assert asyncio.run(widget.on_key(event)) is True


class Picked:
    """A button stand-in that records what was chosen."""

    def __init__(self):
        self.chosen = []

    def pick(self, value):
        self.chosen.append(value)


# -- the calendar --------------------------------------------------------------------


def test_a_month_on_keeps_the_day_or_the_last_there_is():
    assert add_months(datetime.date(2026, 1, 31), 1) == datetime.date(2026, 2, 28)
    assert add_months(datetime.date(2024, 1, 31), 1) == datetime.date(2024, 2, 29)
    assert add_months(datetime.date(2026, 12, 15), 1) == datetime.date(2027, 1, 15)
    assert add_months(datetime.date(2026, 1, 15), -1) == datetime.date(2025, 12, 15)


def test_the_calendar_keys_move_by_day_week_month_and_year():
    calendar = Calendar(None, datetime.date(2026, 10, 1))
    keys(calendar, KeyEvent("right"), KeyEvent("down"))
    assert calendar.day == datetime.date(2026, 10, 9)
    keys(calendar, KeyEvent("pagedown"))
    assert calendar.day == datetime.date(2026, 11, 9)
    keys(calendar, KeyEvent("pageup", ctrl=True))
    assert calendar.day == datetime.date(2025, 11, 9)
    keys(calendar, KeyEvent("end"))
    assert calendar.day == datetime.date(2025, 11, 30)
    keys(calendar, KeyEvent("home"), KeyEvent("left"))
    assert calendar.day == datetime.date(2025, 10, 31)
    keys(calendar, KeyEvent("t", "t"))
    assert calendar.day == datetime.date.today()


def test_weeks_start_on_monday_and_the_month_fills_six_rows():
    calendar = Calendar(None, datetime.date(2026, 10, 15))
    weeks = calendar.weeks()
    assert len(weeks) == 6 and all(len(week) == 7 for week in weeks)
    # 1 October 2026 is a Thursday: the fourth column from Monday.
    assert weeks[0][:4] == [None, None, None, datetime.date(2026, 10, 1)]
    calendar.first_weekday = 6
    assert calendar.weeks()[0][4] == datetime.date(2026, 10, 1)


def test_the_calendar_paints_the_month_the_weekdays_and_the_days():
    calendar = Calendar(None, datetime.date(2026, 10, 15), width=Calendar.WIDTH, height=Calendar.HEIGHT)
    buffer = ScreenBuffer(Calendar.WIDTH, Calendar.HEIGHT)
    calendar.render(buffer)
    rows = ["".join(buffer.get(x, y)[0] or " " for x in range(Calendar.WIDTH)) for y in range(Calendar.HEIGHT)]
    assert "October 2026" in rows[1]
    assert rows[2].strip("│ ") == "Mo Tu We Th Fr Sa Su"
    assert rows[3].rstrip("│ ").endswith("1  2  3  4")


def test_enter_and_a_click_on_a_day_choose_it():
    button = Picked()
    calendar = Calendar(button, datetime.date(2026, 10, 15), width=Calendar.WIDTH, height=Calendar.HEIGHT)
    keys(calendar, KeyEvent("enter"))
    # Row 3 is the first week; Thursday's column holds the 1st.
    asyncio.run(calendar.on_mouse_click(MouseClickEvent(1 + 3 * 3 + 1, 3, "left")))
    assert button.chosen == [datetime.date(2026, 10, 15), datetime.date(2026, 10, 1)]


def test_a_click_on_an_arrow_or_the_wheel_turns_the_month():
    calendar = Calendar(None, datetime.date(2026, 10, 15), width=Calendar.WIDTH, height=Calendar.HEIGHT)
    asyncio.run(calendar.on_mouse_click(MouseClickEvent(Calendar.WIDTH - 3, 1, "left")))
    asyncio.run(calendar.on_mouse_click(MouseClickEvent(5, 5, "wheel_down")))
    assert calendar.day == datetime.date(2026, 12, 15)
    asyncio.run(calendar.on_mouse_click(MouseClickEvent(2, 1, "left")))
    assert calendar.day == datetime.date(2026, 11, 15)


# -- the clock face ------------------------------------------------------------------


def test_the_face_steps_and_wraps_the_number_picked():
    face = TimePicker(None, datetime.time(23, 59, 30))
    keys(face, KeyEvent("up"))
    assert face.values == (0, 59, 30)
    keys(face, KeyEvent("right"), KeyEvent("pageup"))
    assert face.values == (0, 9, 30)
    keys(face, KeyEvent("tab"), KeyEvent("down"))
    assert face.values == (0, 9, 29) and face.column == 2


def test_two_digits_set_a_number_and_go_on_to_the_next():
    face = TimePicker(None, datetime.time(0, 0, 0))
    keys(face, *(KeyEvent(c, c) for c in "0945"))
    assert face.values == (9, 45, 0) and face.column == 2
    # A number past the limit keeps only its second digit.
    keys(face, KeyEvent("home"), KeyEvent("3", "3"), KeyEvent("7", "7"))
    assert face.values[0] == 7


def test_without_seconds_there_are_two_numbers():
    face = TimePicker(None, datetime.time(10, 20, 30), seconds=False)
    assert face.values == (10, 20, 0) and face.columns == 2
    keys(face, KeyEvent("end"))
    assert face.column == 1
    assert TimePicker.width_for(False) < TimePicker.width_for(True)


def test_a_click_on_an_arrow_steps_its_number():
    face = TimePicker(None, datetime.time(10, 20, 30), width=16, height=5)
    asyncio.run(face.on_mouse_click(MouseClickEvent(7, 1, "left")))
    asyncio.run(face.on_mouse_click(MouseClickEvent(12, 3, "left")))
    assert face.values == (10, 21, 29) and face.column == 2


# -- the buttons in a dialog ---------------------------------------------------------


def run_dialog(steps):
    async def main():
        dialog = Dialog(modal_width=50, modal_height=12)
        date = DateField(parent=dialog, x=2, y=2, width=26, height=1, label_text="~D~ate", label_width=10)
        time = TimeField(parent=dialog, x=2, y=4, width=20, height=1, label_text="~T~ime", label_width=6)
        from navkit.widget import Widget

        app = Application(Widget(), terminal=FakeTerminal(width=80, height=24))
        task = asyncio.create_task(app.run_async())
        await asyncio.sleep(0.05)
        app.overlay(dialog)
        await asyncio.sleep(0.03)
        try:
            return await steps(app, dialog, date, time)
        finally:
            app.exit()
            await task

    return asyncio.run(main())


def test_alt_down_drops_the_picker_on_the_lines_value_and_enter_writes_it_back():
    async def steps(app, dialog, date, time):
        date.value = "28-02-2026"
        date.entry.focus()
        app.post_event(KeyEvent("down", alt=True))
        await asyncio.sleep(0.03)
        calendar = app.modal
        after_down = type(calendar).__name__
        opened_on = calendar.day
        app.post_event(KeyEvent("right"))
        app.post_event(KeyEvent("enter"))
        await asyncio.sleep(0.03)
        time.value = "garbage"
        time.entry.focus()
        app.post_event(KeyEvent("down", alt=True))
        await asyncio.sleep(0.03)
        face = app.modal
        for c in "081500":
            app.post_event(KeyEvent(c, c))
        app.post_event(KeyEvent("enter"))
        await asyncio.sleep(0.03)
        return after_down, opened_on, date.value, type(face).__name__, time.value, app.modal

    after_down, opened_on, date_text, face, time_text, modal = run_dialog(steps)
    assert after_down == "Calendar"
    assert opened_on == datetime.date(2026, 2, 28)
    assert date_text == "01-03-2026"
    assert face == "TimePicker" and time_text == "08:15:00"
    assert type(modal).__name__ == "Dialog"


def test_esc_leaves_the_line_as_it_was():
    async def steps(app, dialog, date, time):
        date.value = "01-01-2026"
        date.entry.focus()
        app.post_event(KeyEvent("down", alt=True))
        app.post_event(KeyEvent("pagedown"))
        app.post_event(KeyEvent("escape"))
        await asyncio.sleep(0.03)
        return date.value, type(app.modal).__name__

    assert run_dialog(steps) == ("01-01-2026", "Dialog")


def test_a_click_on_the_button_drops_it_where_it_fits():
    async def steps(app, dialog, date, time):
        button = date.picker
        dx, dy = button.offset()
        app.post_event(MouseClickEvent(dx + button.x + 1, dy + button.y, "left"))
        await asyncio.sleep(0.03)
        popup = app.modal
        line = date.entry
        lx, ly = line.offset()
        return type(popup).__name__, (popup.x, popup.y), (lx + line.x - 1, ly + line.y + 1)

    kind, where, under = run_dialog(steps)
    assert kind == "Calendar" and where == under


# -- the month and the year ---------------------------------------------------------


def test_tab_moves_to_the_month_and_the_year_and_left_and_right_step_them():
    calendar = Calendar(None, datetime.date(2026, 1, 31))
    keys(calendar, KeyEvent("tab"))
    assert calendar.section == "month"
    keys(calendar, KeyEvent("right"))
    assert calendar.day == datetime.date(2026, 2, 28)
    keys(calendar, KeyEvent("tab"), KeyEvent("left"), KeyEvent("left"))
    assert calendar.section == "year" and calendar.day == datetime.date(2024, 2, 28)
    keys(calendar, KeyEvent("tab", shift=True), KeyEvent("tab", shift=True))
    assert calendar.section == "days"


def test_the_month_and_the_year_are_painted_where_a_click_finds_them():
    calendar = Calendar(None, datetime.date(2026, 10, 15), width=Calendar.WIDTH, height=Calendar.HEIGHT)
    (mx, month), (yx, year) = calendar.title_spans()
    assert (month, year) == ("October", "2026") and yx == mx + len(month) + 1
    buffer = ScreenBuffer(Calendar.WIDTH, Calendar.HEIGHT)
    calendar.render(buffer)
    row = "".join(buffer.get(x, 1)[0] or " " for x in range(Calendar.WIDTH))
    assert row[mx:mx + len(month)] == "October" and row[yx:yx + 4] == "2026"


def run_calendar(steps):
    async def main():
        dialog = Dialog(modal_width=50, modal_height=14)
        date = DateField(parent=dialog, x=2, y=2, width=26, height=1, label_text="~D~ate", label_width=10)
        from navkit.widget import Widget

        app = Application(Widget(), terminal=FakeTerminal(width=80, height=24))
        task = asyncio.create_task(app.run_async())
        await asyncio.sleep(0.05)
        app.overlay(dialog)
        await asyncio.sleep(0.03)
        date.value = "15-10-2026"
        date.entry.focus()
        app.post_event(KeyEvent("down", alt=True))
        await asyncio.sleep(0.03)
        try:
            return await steps(app, app.modal, date)
        finally:
            app.exit()
            await task

    return asyncio.run(main())


def test_y_drops_the_years_typing_finds_one_and_a_pick_returns_to_the_days():
    async def steps(app, calendar, date):
        app.post_event(KeyEvent("y", "y"))
        await asyncio.sleep(0.03)
        years = app.modal
        opened = (type(years).__name__, years.selected, calendar.section)
        for c in "1985":
            app.post_event(KeyEvent(c, c))
        app.post_event(KeyEvent("enter"))
        await asyncio.sleep(0.03)
        picked = (app.modal is calendar, calendar.day, calendar.section)
        app.post_event(KeyEvent("enter"))
        await asyncio.sleep(0.03)
        return opened, picked, date.value

    opened, picked, value = run_calendar(steps)
    assert opened == ("HistoryList", "2026", "year")
    assert picked == (True, datetime.date(1985, 10, 15), "days")
    assert value == "15-10-1985"


def test_a_click_on_the_month_drops_the_months_on_the_one_shown():
    async def steps(app, calendar, date):
        (mx, _), _ = calendar.title_spans()
        cx, cy = calendar.offset()
        app.post_event(MouseClickEvent(cx + calendar.x + mx + 1, cy + calendar.y + 1, "left"))
        await asyncio.sleep(0.03)
        months = app.modal
        seen = (type(months).__name__, len(months.items), months.selected)
        for c in "mar":
            app.post_event(KeyEvent(c, c))
        app.post_event(KeyEvent("enter"))
        await asyncio.sleep(0.03)
        return seen, calendar.day, months.footer_text()

    (kind, count, selected), day, _ = run_calendar(steps)
    assert (kind, count, selected) == ("HistoryList", 12, "October")
    assert day == datetime.date(2026, 3, 15)


def test_esc_on_a_list_leaves_the_calendar_as_it_was():
    async def steps(app, calendar, date):
        app.post_event(KeyEvent("m", "m"))
        app.post_event(KeyEvent("down"))
        app.post_event(KeyEvent("escape"))
        await asyncio.sleep(0.03)
        return app.modal is calendar, calendar.day

    assert run_calendar(steps) == (True, datetime.date(2026, 10, 15))


# -- the masked line -----------------------------------------------------------------


def test_a_mask_comes_from_a_strftime_format():
    from navml.widgets.dialog.masked_line import mask_for

    assert mask_for("%d-%m-%Y") == "99-99-9999"
    assert mask_for("%H:%M:%S") == "99:99:99"
    assert mask_for("%y.%m.%d") == "99.99.99"
    import pytest

    with pytest.raises(ValueError):
        mask_for("%d %B")


def masked(value="", mask="99-99-9999"):
    from navml.widgets.dialog.masked_line import MaskedLine

    line = MaskedLine(width=13, height=1)
    line.mask = mask
    line.value = value
    return line


def test_digits_overwrite_their_places_and_step_over_the_separators():
    line = masked("01-10-2026")
    keys(line, *(KeyEvent(c, c) for c in "3112"))
    assert line.value == "31-12-2026" and line.cursor == 6
    keys(line, *(KeyEvent(c, c) for c in "20271"))
    # The last place keeps the caret, so a further digit overwrites it.
    assert line.value == "31-12-2021" and line.cursor == 9


def test_left_and_right_move_between_places_and_everything_else_is_refused():
    line = masked("01-10-2026")
    keys(line, KeyEvent("right"), KeyEvent("right"))
    assert line.cursor == 3
    keys(line, KeyEvent("left"))
    assert line.cursor == 1
    for event in (KeyEvent("a", "a"), KeyEvent("-", "-"), KeyEvent(" ", " "), KeyEvent("v", ctrl=True)):
        keys(line, event)
    assert (line.value, line.cursor) == ("01-10-2026", 1)
    keys(line, KeyEvent("left"), KeyEvent("left"))
    assert line.cursor == 0


def test_the_dialogs_keys_pass_through():
    line = masked("01-10-2026")
    for event in (KeyEvent("tab"), KeyEvent("tab", shift=True), KeyEvent("escape"),
                  KeyEvent("enter"), KeyEvent("d", alt=True)):
        assert asyncio.run(line.on_key(event)) is False


def test_an_empty_line_stays_empty_shows_its_separators_and_fills_on_a_digit():
    line = masked("")
    buffer = ScreenBuffer(13, 1)
    line.render(buffer)
    assert "".join(buffer.get(x, 0)[0] or " " for x in range(13)) == "   -  -      "
    keys(line, KeyEvent("right"), KeyEvent("5", "5"))
    assert line.value == " 5-  -    " and line.cursor == 3


def test_a_paste_is_refused():
    from navkit.events import PasteEvent

    line = masked("01-10-2026")
    assert asyncio.run(line.on_paste(PasteEvent("99-99-9999"))) is True
    assert line.value == "01-10-2026"


def test_typing_in_the_date_field_and_then_the_calendar_agree():
    async def steps(app, dialog, date, time):
        date.value = "01-10-2026"
        date.entry.focus()
        date.entry.select_all()
        for c in "15":
            app.post_event(KeyEvent(c, c))
        app.post_event(KeyEvent("down", alt=True))
        await asyncio.sleep(0.03)
        calendar = app.modal
        day = calendar.day
        app.post_event(KeyEvent("right"))
        app.post_event(KeyEvent("enter"))
        await asyncio.sleep(0.03)
        app.post_event(KeyEvent("0", "0"))
        await asyncio.sleep(0.03)
        return day, date.value

    day, value = run_dialog(steps)
    assert day == datetime.date(2026, 10, 15)
    # The pick put the caret back on the first place, so a digit overwrites it.
    assert value == "06-10-2026"


def test_backspace_and_delete_blank_the_place_under_the_caret_and_all_blank_is_empty():
    line = masked("01-10-2026")
    keys(line, KeyEvent("right"), KeyEvent("delete"))
    assert (line.value, line.cursor) == ("0 -10-2026", 1)
    keys(line, KeyEvent("left"), KeyEvent("backspace"))
    assert (line.value, line.cursor) == ("  -10-2026", 0)
    # Backspace steps back a place after blanking, so from the end it clears
    # the line backwards, over the separators, and stops on the first place.
    keys(line, KeyEvent("right"), KeyEvent("right"), KeyEvent("right"), KeyEvent("right"))
    assert line.cursor == 6
    keys(line, KeyEvent("backspace"))
    assert (line.value, line.cursor) == ("  -10- 026", 4)
    for _ in range(3):
        keys(line, KeyEvent("backspace"))
    assert (line.value, line.cursor) == ("  -  - 026", 0)
    keys(line, KeyEvent("right"), KeyEvent("right"), KeyEvent("right"), KeyEvent("right"),
         KeyEvent("right"), KeyEvent("right"), KeyEvent("right"))
    for _ in range(3):
        keys(line, KeyEvent("backspace"))
    assert line.value == ""
    keys(line, KeyEvent("delete"))
    assert line.value == ""


def test_without_a_stepping_button_up_and_down_step_the_run_as_a_number():
    line = masked("09-10-2026")
    keys(line, KeyEvent("right"), KeyEvent("up"))
    assert (line.value, line.cursor) == ("10-10-2026", 1)
    keys(line, KeyEvent("left"), KeyEvent("up"), KeyEvent("up"), KeyEvent("up"))
    # The tens: ten at a time, wrapping within the two digits, never into the month.
    assert line.value == "40-10-2026"
    keys(line, *[KeyEvent("up")] * 6)
    assert line.value == "00-10-2026"
    empty = masked("")
    keys(empty, KeyEvent("down"))
    assert empty.value == "90-  -    "


def test_a_date_steps_as_a_calendar_does():
    button = DateButton()

    def step(text, index, delta=1):
        return button.step(text, index, delta)

    assert step("31-10-2026", 1) == "01-11-2026"            # a day
    assert step("01-10-2026", 0, -1) == "21-09-2026"        # ten days back
    assert step("15-12-2026", 4) == "15-01-2027"            # a month
    assert step("31-01-2026", 4) == "28-02-2026"            # clamped
    assert step("15-03-2026", 3) == "15-01-2027"            # ten months
    assert step("29-02-2024", 9) == "28-02-2025"            # a year, clamped
    assert step("15-03-2026", 7) == "15-03-2126"            # a hundred years
    assert step("15-03-9999", 9) == "15-03-9999"            # past the last year: kept
    assert step("  -  -    ", 0) == datetime.date.today().strftime("%d-%m-%Y")
    assert step("15-03-2026", 2) is None                    # a separator


def test_a_time_steps_as_a_clock_does_and_wraps_round_the_day():
    button = TimeButton()

    def step(text, index, delta=1):
        return button.step(text, index, delta)

    assert step("23:59:30", 4) == "00:00:30"
    assert step("10:00:00", 6, -1) == "09:59:50"
    assert step("00:05:00", 0, -1) == "14:05:00"
    assert step("10:20:59", 7) == "10:21:00"
    assert len(step("garbage!", 0)) == 8


def test_plain_down_in_a_date_field_steps_rather_than_dropping_the_calendar():
    async def steps(app, dialog, date, time):
        date.value = "01-10-2026"
        date.entry.focus()
        date.entry.select_all()
        app.post_event(KeyEvent("down"))
        await asyncio.sleep(0.03)
        return type(app.modal).__name__, date.value

    # The caret is on the day's tens: ten days back, across into September.
    assert run_dialog(steps) == ("Dialog", "21-09-2026")


def test_pgup_and_pgdn_step_by_ten_times_the_place():
    line = masked("09-10-2026")
    keys(line, KeyEvent("pageup"))
    # The day's tens: a hundred, wrapping within the two digits.
    assert (line.value, line.cursor) == ("09-10-2026", 0)
    keys(line, KeyEvent("right"), KeyEvent("pageup"))
    assert line.value == "19-10-2026"
    keys(line, KeyEvent("pagedown"), KeyEvent("pagedown"))
    assert line.value == "99-10-2026"

    async def steps(app, dialog, date, time):
        date.value = "01-10-2026"
        date.entry.focus()
        date.entry.select_all()
        app.post_event(KeyEvent("right"))
        app.post_event(KeyEvent("pageup"))
        time.value = "10:00:00"
        await asyncio.sleep(0.03)
        after_date = date.value
        time.entry.focus()
        time.entry.select_all()
        for key in ("right", "right", "right", "pagedown"):
            app.post_event(KeyEvent(key))
        await asyncio.sleep(0.03)
        return after_date, time.value

    assert run_dialog(steps) == ("11-10-2026", "09:50:00")


def test_home_and_end_jump_to_the_first_and_the_last_place():
    line = masked("01-10-2026")
    keys(line, KeyEvent("end"))
    assert line.cursor == 9
    keys(line, KeyEvent("home"))
    assert line.cursor == 0
    clock = masked("10:20:30", "99:99:99")
    keys(clock, KeyEvent("end"), KeyEvent("up"))
    assert (clock.cursor, clock.value) == (7, "10:20:31")


def test_home_and_end_on_the_month_and_the_year():
    calendar = Calendar(None, datetime.date(2026, 3, 31))
    keys(calendar, KeyEvent("end"))
    assert calendar.day == datetime.date(2026, 3, 31)
    keys(calendar, KeyEvent("home"))
    assert calendar.day == datetime.date(2026, 3, 1)
    keys(calendar, KeyEvent("tab"), KeyEvent("end"))
    assert calendar.day == datetime.date(2026, 12, 1)
    keys(calendar, KeyEvent("home"))
    assert calendar.day == datetime.date(2026, 1, 1)
    calendar.day = datetime.date(2026, 6, 15)
    keys(calendar, KeyEvent("tab"), KeyEvent("end"))
    assert calendar.day == datetime.date(2026, 12, 31)
    keys(calendar, KeyEvent("home"))
    assert calendar.day == datetime.date(2026, 1, 1)


def test_home_and_end_in_the_year_list_go_to_its_ends():
    async def steps(app, calendar, date):
        app.post_event(KeyEvent("y", "y"))
        await asyncio.sleep(0.03)
        years = app.modal
        app.post_event(KeyEvent("end"))
        await asyncio.sleep(0.03)
        last = years.selected
        app.post_event(KeyEvent("home"))
        await asyncio.sleep(0.03)
        first = years.selected
        app.post_event(KeyEvent("enter"))
        await asyncio.sleep(0.03)
        return first, last, calendar.day

    first, last, day = run_calendar(steps)
    assert (first, last) == ("1926", "2126")
    assert day == datetime.date(1926, 10, 15)


def test_home_and_end_in_the_month_list_go_to_january_and_december():
    async def steps(app, calendar, date):
        app.post_event(KeyEvent("m", "m"))
        await asyncio.sleep(0.03)
        months = app.modal
        app.post_event(KeyEvent("end"))
        await asyncio.sleep(0.03)
        last = months.selected
        app.post_event(KeyEvent("home"))
        await asyncio.sleep(0.03)
        first = months.selected
        app.post_event(KeyEvent("enter"))
        await asyncio.sleep(0.03)
        return first, last, calendar.day

    first, last, day = run_calendar(steps)
    assert (first, last) == ("January", "December")
    assert day == datetime.date(2026, 1, 15)


# -- a click outside -----------------------------------------------------------------


def press(x, y, button="left"):
    return MouseClickEvent(x, y, button, "press")


def test_a_click_outside_the_calendar_closes_it_and_leaves_the_dialog():
    async def steps(app, calendar, date):
        dialog = _dialog_of(date)
        app.post_event(KeyEvent("pagedown"))
        # Inside the dialog, past the calendar.
        x, y = dialog.x + dialog.width - 3, dialog.y + 1
        app.post_event(press(x, y))
        await asyncio.sleep(0.03)
        first = app.modal is dialog, date.value
        # Outside everything: the dialog is the outermost and stays.
        app.post_event(press(0, 0))
        await asyncio.sleep(0.03)
        return first, app.modal is dialog

    assert run_calendar(steps) == ((True, "15-10-2026"), True)


def test_a_click_outside_a_list_over_the_calendar_closes_only_the_list():
    async def steps(app, calendar, date):
        app.post_event(KeyEvent("m", "m"))
        await asyncio.sleep(0.03)
        months = app.modal
        app.post_event(press(0, 0))
        await asyncio.sleep(0.03)
        return type(months).__name__, app.modal is calendar

    assert run_calendar(steps) == ("HistoryList", True)


def test_the_wheel_and_a_release_outside_dismiss_nothing():
    async def steps(app, calendar, date):
        app.post_event(MouseClickEvent(0, 0, "wheel_up", "press"))
        app.post_event(MouseClickEvent(0, 0, "left", "release"))
        await asyncio.sleep(0.03)
        return app.modal is calendar

    assert run_calendar(steps) is True


def _dialog_of(widget):
    while not isinstance(widget, Dialog):
        widget = widget.parent
    return widget


def test_a_dialog_cancels_on_a_click_outside_only_where_it_says_so():
    async def main():
        from navkit.widget import Widget

        outer = Dialog(modal_width=50, modal_height=14)
        inner = Dialog(modal_width=20, modal_height=6, close_on_outside_click=True)
        app = Application(Widget(), terminal=FakeTerminal(width=80, height=24))
        task = asyncio.create_task(app.run_async())
        await asyncio.sleep(0.05)
        try:
            app.overlay(outer)
            app.overlay(inner)
            await asyncio.sleep(0.03)
            app.post_event(press(0, 0))
            await asyncio.sleep(0.03)
            first = app.modal is outer, inner.result, inner.is_mounted
            app.post_event(press(0, 0))
            await asyncio.sleep(0.03)
            return first, app.modal is outer
        finally:
            app.exit()
            await task

    assert asyncio.run(main()) == ((True, None, False), True)


def test_the_small_dialogs_say_so_in_their_markup():
    from navigator.widgets.file_ops.mkdir_dialog import MkdirDialog

    assert MkdirDialog().close_on_outside_click is True
    assert Dialog().close_on_outside_click is False

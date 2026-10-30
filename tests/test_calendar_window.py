"""Utilities > Calendar: TVDEMO's calendar window, a departure (DN had none)."""

from __future__ import annotations

import datetime

import pytest

from conftest import FakeTerminal, Until, key_bar_hints, run_app
from navkit.events import KeyEvent

from navigator.__main__ import Navigator


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    return Navigator(tmp_path, tmp_path, terminal=FakeTerminal(80, 24))


def calendar(app):
    from navigator.widgets.shell.calendar_window import CalendarWindow

    return next((w for w in app.shell.desktop.windows() if isinstance(w, CalendarWindow)), None)


def weeks_of(day: datetime.date) -> int:
    """The Monday-first weeks *day*'s Gregorian month spans: what the window's grid paints."""
    import calendar as _calendar

    return len(_calendar.Calendar(0).monthdayscalendar(day.year, day.month))


def tall(day: datetime.date, spelled: bool = True) -> int:
    """The window's height on *day*'s Gregorian month: the frame, the month and weekday rows,
    its weeks, the row spelling the day, a blank, and the button with its shadow."""
    return 2 + 2 + weeks_of(day) + spelled + 1 + 2


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
    assert seen["rect"][2:] == (26, tall(datetime.date.today())) and seen["rect"][0] == (desktop_width - 26) // 2
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
    # The cursor's colours, underlined: today's own foreground on the cursor's
    # ground mixed two slots, which some palettes make the same colour.
    assert (seen["both"].fg, seen["both"].bg) == (seen["cursor"].fg, seen["cursor"].bg)
    assert seen["both"].underline


def test_ctrl_f12_opens_the_calendar_from_anywhere_and_the_menu_shows_it(app):
    from navml.widgets.menu.menu_box.menu_box import key_caption
    from navigator.widgets.shell.commands import OpenCalendar

    seen = {}

    def caption(a):
        item = next(i for i in a.shell.menu.utilities.children if getattr(i, "command", None) is OpenCalendar)
        seen.update(key=key_caption(item, a, a.manager.left))

    run_app(app, [caption, KeyEvent("f12", ctrl=True), Until(lambda a: calendar(a) is not None),
                  lambda a: seen.update(open=True)])
    assert seen["open"] and seen["key"] == "Ctrl-F12"


def test_the_calendar_menu_shows_the_keys_and_works_from_the_button(app):
    from navml.widgets.dialog.control.control import parse_shortcut
    from navml.widgets.menu.menu_box.menu_box import key_caption
    from navml.widgets.dialog.commands import NextYear

    seen = {}

    def look(a):
        w = calendar(a)
        seen["bar"] = [parse_shortcut(e.text)[0] for e in a.shell.menu.entries()]
        seen["keys"] = [key_caption(e, a, a.focused) for e in w.calendar_menu.entries() if hasattr(e, "command")]

    def from_the_button(a):
        w = calendar(a)
        w.today_button.focus()
        a.spawn(a.run_command(NextYear(), start=w.today_button))

    run_app(app, [open_calendar, Until(lambda a: calendar(a) is not None), look, from_the_button,
                  lambda a: None,
                  lambda a: seen.update(day=calendar(a).month.day, focused=a.focused is calendar(a).month)])
    assert "Calendar" in seen["bar"]
    assert seen["keys"] == ["PgUp", "PgDn", "Ctrl-PgUp", "Ctrl-PgDn", "M", "Y", "T", "C", "Esc"]
    today = datetime.date.today()
    assert seen["day"].year == today.year + 1 and seen["day"].month == today.month
    assert seen["focused"]


def test_a_right_click_on_a_day_moves_there_and_offers_the_menu(app):
    from navkit.events import MouseClickEvent
    from navml.widgets.dialog.control.control import parse_shortcut
    from navml.widgets.menu.popup_menu import PopupMenu

    seen = {}

    def popup(a):
        return next((c for c in a.root.children if isinstance(c, PopupMenu)), None)

    def click_a_day(a):
        w = calendar(a)
        month = w.month
        target = next(d for week in month.weeks() for d in week if d is not None and d != month.day)
        seen["target"] = target
        row = next(i for i, week in enumerate(month.weeks()) if target in week)
        column = month.weeks()[row].index(target)
        ox, oy = w.offset()
        x = ox + w.x + month.x + month.inset + 3 * column + 1
        y = oy + w.y + month.y + month.inset + 2 + row
        a.post_event(MouseClickEvent(x=x, y=y, button="right", action="press"))

    run_app(app, [open_calendar, Until(lambda a: calendar(a) is not None), click_a_day,
                  Until(lambda a: popup(a) is not None),
                  lambda a: seen.update(day=calendar(a).month.day,
                                        items=[parse_shortcut(e.text)[0] for e in popup(a).box.entries()
                                               if hasattr(e, "command")]),
                  KeyEvent("d", "d"), Until(lambda a: popup(a) is None),
                  lambda a: seen.update(after=calendar(a).month.day)])
    assert seen["day"] == seen["target"]
    assert seen["items"] == ["Previous month", "Next month", "Previous year", "Next year",
                             "Choose month...", "Choose year...", "Go to current date", "Swap calendars", "Close"]
    assert seen["after"] == datetime.date.today()


def test_the_window_spells_the_day_in_country_support_s_format(app):
    from navigator.settings import SETTINGS

    seen = []

    def spelled(a):
        month = calendar(a).month
        seen.append(month.date_format)

    run_app(app, [open_calendar, Until(lambda a: calendar(a) is not None), spelled,
                  lambda a: setattr(SETTINGS.country, "date_format", "iso"), lambda a: None, spelled])
    assert seen == ["%d-%m-%Y", "%Y-%m-%d"]


def test_the_window_s_week_follows_country_support(app):
    from navigator.settings import SETTINGS

    seen = []
    run_app(app, [open_calendar, Until(lambda a: calendar(a) is not None),
                  lambda a: seen.append(calendar(a).month.first_weekday),
                  lambda a: setattr(SETTINGS.country, "first_day", "sunday"), lambda a: None,
                  lambda a: seen.append(calendar(a).month.first_weekday)])
    assert seen == [0, 6]


def screen_rect(window):
    ox, oy = window.offset()
    return ox + window.x, oy + window.y, window.width, window.height


@pytest.mark.parametrize("hide_menu_bar", [False, True])
def test_a_click_on_the_clock_opens_the_calendar_just_under_it_and_another_closes_it(app, hide_menu_bar):
    from navkit.events import MouseClickEvent
    from navigator.settings import SETTINGS
    from navigator.widgets.shell.calendar_window.calendar_window import WIDTH

    SETTINGS.interface.hide_menu_bar = hide_menu_bar
    seen = {}

    def click(a):
        clock = a.shell.clock
        ox, oy = clock.offset()
        a.post_event(MouseClickEvent(ox + clock.x + 1, oy + clock.y, "left", "press"))
        a.post_event(MouseClickEvent(ox + clock.x + 1, oy + clock.y, "left", "release"))

    run_app(app, [click, Until(lambda a: calendar(a) is not None),
                  lambda a: seen.update(first=screen_rect(calendar(a))),
                  click, Until(lambda a: calendar(a) is None),
                  lambda a: seen.update(closed=calendar(a) is None),
                  click, Until(lambda a: calendar(a) is not None),
                  lambda a: seen.update(again=screen_rect(calendar(a)))])
    assert seen["first"] == (80 - WIDTH, 1, WIDTH, tall(datetime.date.today()))
    assert seen["closed"] and seen["again"] == seen["first"]


def test_the_clock_closes_a_calendar_the_menu_opened(app):
    def click(a):
        clock = a.shell.clock
        ox, oy = clock.offset()
        a.post_event(MouseClickEvent(ox + clock.x, oy + clock.y, "left", "press"))
        a.post_event(MouseClickEvent(ox + clock.x, oy + clock.y, "left", "release"))

    from navkit.events import MouseClickEvent

    seen = {}
    run_app(app, [open_calendar, Until(lambda a: calendar(a) is not None),
                  click, Until(lambda a: calendar(a) is None), lambda a: seen.update(closed=True)])
    assert seen["closed"]


def test_the_menu_still_opens_it_in_the_middle(app):
    seen = {}
    run_app(app, [open_calendar, Until(lambda a: calendar(a) is not None),
                  lambda a: seen.update(rect=screen_rect(calendar(a)))])
    assert seen["rect"][0] == (80 - 26) // 2 and seen["rect"][1] > 1


@pytest.mark.parametrize("keys", [[], [KeyEvent("tab")], [KeyEvent("tab", shift=True)]])
def test_esc_closes_the_window_from_the_days_the_month_or_the_year(app, keys):
    seen = {}
    run_app(app, [open_calendar, Until(lambda a: calendar(a) is not None), *keys,
                  lambda a: seen.update(section=calendar(a).month.section),
                  KeyEvent("escape"), lambda a: None, lambda a: seen.update(open=calendar(a) is not None)])
    assert seen["section"] == ["days", "month", "year"][len(keys) and (1 if not keys[0].shift else 2)]
    assert seen["open"] is False


@pytest.mark.parametrize("where", ["days", "month", "button"])
@pytest.mark.parametrize("key", [KeyEvent("t", "t"), KeyEvent("t", "T", shift=True)])
def test_t_jumps_to_today_from_anywhere_in_the_window(app, where, key):
    def move_keys(a):
        window = calendar(a)
        if where == "month":
            window.month.section = "month"
        elif where == "button":
            window.today_button.focus()

    seen = {}
    run_app(app, [open_calendar, Until(lambda a: calendar(a) is not None),
                  KeyEvent("pagedown", ctrl=True), move_keys, lambda a: None,
                  lambda a: seen.update(before=calendar(a).month.day),
                  key, lambda a: None,
                  lambda a: seen.update(after=calendar(a).month.day, section=calendar(a).month.section)])
    assert seen["before"] != datetime.date.today()
    assert seen["after"] == datetime.date.today() and seen["section"] == "days"


def painted(a) -> str:
    buffer = a._front
    return "\n".join("".join(buffer.get(x, y)[0] or " " for x in range(buffer.width)) for y in range(buffer.height))


def test_a_calendar_system_puts_the_month_in_it_and_pages_its_months_and_years(app):
    from navml.widgets.dialog.commands import SetCalendarSystem

    seen = {}

    def choose(a):
        w = calendar(a)
        w.month.day = datetime.date(2027, 3, 23)  # Purim 5787, 14 Adar II
        a.spawn(a.run_command(SetCalendarSystem("hebrew"), start=w.month))

    def look(name):
        return lambda a: seen.update({name: calendar(a).month.day})

    run_app(app, [open_calendar, Until(lambda a: calendar(a) is not None),
                  lambda a: seen.update(first=calendar(a).month.system),
                  choose, lambda a: None, lambda a: None,
                  lambda a: seen.update(system=calendar(a).month.system, text=painted(a),
                                        title=[text for _, text in calendar(a).month.title_spans()]),
                  KeyEvent("pagedown"), lambda a: None, look("paged"),
                  KeyEvent("end"), lambda a: None, look("end"),
                  KeyEvent("pagedown", ctrl=True), lambda a: None, look("year"),
                  lambda a: a.spawn(a.run_command(SetCalendarSystem("gregorian"), start=calendar(a).month)),
                  lambda a: None, lambda a: seen.update(back=calendar(a).month.system)])
    assert seen["first"] == "gregorian" and seen["system"] == "hebrew"
    assert seen["title"] == ["Adar II", "5787"] and "Adar II 5787" in seen["text"]
    # Under the Hebrew month, the Gregorian day in Country support's format.
    assert "23-03-2027" in seen["text"]
    # A page on is Nisan, End its 30th, and a year on Nisan 5788.
    assert seen["paged"] == datetime.date(2027, 4, 21) and seen["end"] == datetime.date(2027, 5, 7)
    assert seen["year"] == datetime.date(2028, 4, 26)  # 30 Nisan 5788; Passover is 11 April
    assert seen["back"] == "gregorian"


def test_the_menu_ticks_the_calendar_system_shown(app):
    from navml.widgets.dialog.commands import SetCalendarSystem

    seen = {}

    def look(a, name):
        w = calendar(a)
        seen[name] = [key for key in ("gregorian", "julian") if w.checks(SetCalendarSystem(key))]

    run_app(app, [open_calendar, Until(lambda a: calendar(a) is not None), lambda a: look(a, "first"),
                  lambda a: a.spawn(a.run_command(SetCalendarSystem("julian"), start=calendar(a).month)),
                  lambda a: None, lambda a: look(a, "julian"),
                  lambda a: seen.update(entries=len(calendar(a).system_menu.entries()))])
    assert seen["first"] == ["gregorian"] and seen["julian"] == ["julian"]
    assert seen["entries"] == 25


def test_the_month_list_of_a_hebrew_leap_year_holds_thirteen(app):
    seen = {}

    def hebrew(a):
        w = calendar(a)
        w.chosen = "hebrew"
        w.month.day = datetime.date(2027, 1, 1)

    def drop(a):
        seen["list"] = calendar(a).month.drop("month").items

    run_app(app, [open_calendar, Until(lambda a: calendar(a) is not None), hebrew, lambda a: None, drop])
    assert len(seen["list"]) == 13 and seen["list"][:2] == ["Tishri", "Heshvan"]


def test_auto_is_the_language_s_calendar_and_country_support_names_one(app):
    from navkit import i18n
    from navigator.settings import SETTINGS

    seen = []

    def look(a):
        seen.append(calendar(a).month.system)

    run_app(app, [open_calendar, Until(lambda a: calendar(a) is not None), look,
                  lambda a: setattr(i18n.LOCALE, "code", "he"), lambda a: None, look,
                  lambda a: setattr(SETTINGS.country, "calendar", "persian"), lambda a: None, look,
                  lambda a: setattr(SETTINGS.country, "calendar", "gregorian"), lambda a: None, look])
    assert seen == ["gregorian", "hebrew", "persian", "gregorian"]


def test_a_saved_desktop_keeps_the_calendar_system(app):
    from navigator.lib.config import desktop_state

    seen = {}

    async def again(a):
        data = desktop_state.snapshot(a.shell.desktop)
        seen["kept"] = next(w for w in data["windows"] if w.get("kind") == "calendar")
        calendar(a).close()
        made = await desktop_state.restore(a.shell.desktop, {"windows": [seen["kept"]]})
        seen["back"] = (made[0].chosen, made[0].month.system)

    run_app(app, [open_calendar, Until(lambda a: calendar(a) is not None),
                  lambda a: setattr(calendar(a), "chosen", "ethiopian"), lambda a: None,
                  lambda a: a.spawn(again(a)), Until(lambda a: "back" in seen)])
    assert seen["kept"]["calendar"] == "ethiopian"
    assert seen["back"] == ("ethiopian", "ethiopian")


def test_the_chinese_month_falls_back_to_the_gregorian_outside_the_tables_years(app):
    seen = {}

    def chinese(a):
        w = calendar(a)
        w.chosen = "chinese"
        w.month.day = datetime.date(2026, 9, 25)  # the Mid-Autumn Festival, 15th of the 8th month

    def look(name):
        return lambda a: seen.update({name: (calendar(a).month.calendar.key,
                                             [text for _, text in calendar(a).month.title_spans()])})

    run_app(app, [open_calendar, Until(lambda a: calendar(a) is not None), chinese, lambda a: None, look("in"),
                  lambda a: setattr(calendar(a).month, "day", datetime.date(1901, 2, 10)), lambda a: None,
                  look("before"),
                  KeyEvent("pagedown"), lambda a: None, look("back")])
    assert seen["in"] == ("chinese", ["Month 8", "2026"])
    assert seen["before"] == ("gregorian", ["February", "1901"])
    # A page on is March 1901, in the Chinese year 1901: its 1st month again.
    assert seen["back"][0] == "chinese"


@pytest.mark.parametrize("view, grid, row", [
    # The calendar alone: its month, nothing spelled under it.
    ("only", ["Adar II", "5787"], None),
    # The Gregorian month, the day spelled in the calendar.
    ("gregorian_grid", ["March", "2027"], "14 Adar II 5787"),
    # Its month, the Gregorian day spelled -- as it began.
    ("selected_grid", ["Adar II", "5787"], "23-03-2027"),
])
def test_the_view_says_which_calendar_is_the_month_and_which_spells_the_day(app, view, grid, row):
    from navml.widgets.dialog.commands import SetCalendarView

    seen = {}

    def choose(a):
        w = calendar(a)
        w.chosen = "hebrew"
        w.month.day = datetime.date(2027, 3, 23)
        a.spawn(a.run_command(SetCalendarView(view), start=w.month))

    def look(a):
        w = calendar(a)
        seen.update(title=[text for _, text in w.month.title_spans()], text=painted(a), width=w.width,
                    row=w.month.spelled() or None, size=(w.width, w.height), button=w.today_button.y,
                    other=w.other.visible, ticked=[key for key in ("only", "gregorian_grid", "selected_grid", "both")
                                                    if w.checks(SetCalendarView(key))])

    run_app(app, [open_calendar, Until(lambda a: calendar(a) is not None), choose, lambda a: None, lambda a: None,
                  look])
    assert seen["title"] == grid and seen["row"] == row
    if row is None:
        assert "23-03-2027" not in seen["text"] and "14 Adar II 5787" not in seen["text"]
    # March 2027 and Adar II 5787 both span five weeks.
    assert seen["size"] == (26, 12 if view == "only" else 13) and not seen["other"] and seen["ticked"] == [view]
    assert seen["button"] == (9 if view == "only" else 10)


def test_both_months_side_by_side_share_one_day_and_widen_the_window(app):
    from navml.widgets.dialog.commands import SetCalendarSystem, SetCalendarView

    seen = {}

    def choose(a):
        w = calendar(a)
        w.chosen = "hebrew"
        w.month.day = datetime.date(2027, 3, 23)
        a.spawn(a.run_command(SetCalendarView("both"), start=w.month))

    def look(name):
        def take(a):
            w = calendar(a)
            seen[name] = dict(left=[t for _, t in w.month.title_spans()], right=[t for _, t in w.other.title_spans()],
                              days=(w.month.day, w.other.day), width=w.width, height=w.height, x=w.x,
                              text=painted(a),
                              other=w.other.visible, focused=a.focused is w.other)
        return take

    def click_other(a):
        from navkit.events import MouseClickEvent

        other = calendar(a).other
        x, y = other.offset()
        x, y = x + other.x + 6 * 3 + 1, y + other.y + 4
        a.post_event(MouseClickEvent(x, y, "left", "press"))
        a.post_event(MouseClickEvent(x, y, "left", "release"))

    run_app(app, [open_calendar, Until(lambda a: calendar(a) is not None), choose, lambda a: None, lambda a: None,
                  look("both"),
                  KeyEvent("pagedown"), lambda a: None, lambda a: None, look("paged"),
                  click_other, lambda a: None, lambda a: None, look("clicked"),
                  KeyEvent("pagedown"), lambda a: None, lambda a: None, look("turned"),
                  lambda a: a.spawn(a.run_command(SetCalendarSystem("gregorian"), start=calendar(a).other)),
                  lambda a: None, lambda a: None, look("gregorian")])
    both = seen["both"]
    # The calendar first, the Gregorian beside it.
    assert both["left"] == ["Adar II", "5787"] and both["right"] == ["March", "2027"]
    assert both["days"] == (datetime.date(2027, 3, 23),) * 2 and both["width"] == 51 and both["other"]
    assert both["height"] == 12
    # Nothing spelled under either: the two grids say the day.
    assert "23-03-2027" not in both["text"] and "14 Adar II 5787" not in both["text"]
    # Kept on the desktop: 80 columns, so wholly on it.
    assert 0 <= both["x"] <= 80 - 51
    # The Hebrew month pages in Hebrew months, 14 Nisan; the Gregorian follows its day.
    paged = seen["paged"]
    assert paged["days"] == (datetime.date(2027, 4, 21),) * 2 and paged["right"] == ["April", "2027"]
    # A click puts the keys on the Gregorian month (its third Sunday, 18 April), whose page is a
    # Gregorian month.
    assert seen["clicked"]["focused"] and seen["clicked"]["days"][0] == datetime.date(2027, 4, 18)
    assert seen["turned"]["right"] == ["May", "2027"] and seen["turned"]["days"][0] == datetime.date(2027, 5, 18)
    # With the Gregorian chosen there is one month again, the keys on it.
    gregorian = seen["gregorian"]
    assert not gregorian["other"] and gregorian["width"] == 26 and not gregorian["focused"]


def test_a_saved_desktop_keeps_the_view_and_country_support_names_its_default(app):
    from navigator.lib.config import desktop_state
    from navigator.settings import SETTINGS

    seen = {}

    async def again(a):
        data = desktop_state.snapshot(a.shell.desktop)
        seen["kept"] = next(w for w in data["windows"] if w.get("kind") == "calendar")
        calendar(a).close()
        made = await desktop_state.restore(a.shell.desktop, {"windows": [seen["kept"]]})
        seen["back"] = (made[0].display, made[0].width, made[0].height)
        seen["size"] = made[0].size()[1]

    def default(a):
        w = calendar(a)
        seen["default"] = w.calendar_view()
        SETTINGS.country.calendar_view = "both"
        SETTINGS.country.calendar = "julian"

    run_app(app, [open_calendar, Until(lambda a: calendar(a) is not None), default, lambda a: None,
                  lambda a: seen.update(setting=(calendar(a).calendar_view(), calendar(a).width)),
                  lambda a: setattr(calendar(a), "display", "only"), lambda a: None,
                  lambda a: a.spawn(again(a)), Until(lambda a: "back" in seen)])
    assert seen["default"] == "selected_grid" and seen["setting"] == ("both", 51)
    assert seen["kept"]["view"] == "only" and seen["back"][:2] == ("only", 26)
    assert seen["back"][2] == seen["size"]


def test_the_grid_holds_only_the_month_s_weeks_and_the_window_follows_as_it_pages(app):
    seen = []

    def start(a):
        calendar(a).month.day = datetime.date(2026, 7, 15)  # five weeks; August has six

    def look(a):
        w = calendar(a)
        seen.append((w.month.rows(), w.height, w.today_button.y, w.y))

    run_app(app, [open_calendar, Until(lambda a: calendar(a) is not None), start, lambda a: None, look,
                  KeyEvent("pagedown"), lambda a: None, lambda a: None, look,
                  KeyEvent("pagedown"), lambda a: None, lambda a: None, look])
    (july, august, september) = seen
    assert july[:3] == (5, 13, 10) and august[:3] == (6, 14, 11) and september[:3] == (5, 13, 10)
    # The top edge stays put; the bottom moves.
    assert july[3] == august[3] == september[3]


def test_c_swaps_the_month_between_the_calendar_and_the_gregorian_and_the_key_bar_says_so(app):
    from navml.widgets.dialog.commands import SetCalendarView, SwapCalendars

    seen = {}

    def hebrew(a):
        w = calendar(a)
        w.chosen = "hebrew"
        w.month.day = datetime.date(2027, 3, 23)

    def look(name):
        def take(a):
            w = calendar(a)
            seen[name] = (w.calendar_view(), w.month.system, w.month.spelled(),
                          [h for h in key_bar_hints(a) if h[0] == "C"], a.command_enabled(SwapCalendars()))
        return take

    def view(key):
        return lambda a: a.spawn(a.run_command(SetCalendarView(key), start=calendar(a).month))

    run_app(app, [open_calendar, Until(lambda a: calendar(a) is not None), look("gregorian"),
                  hebrew, lambda a: None, look("hebrew"), lambda a: seen.update(bar=key_bar_hints(a)),
                  KeyEvent("c", "c"), lambda a: None, lambda a: None, look("swapped"),
                  KeyEvent("c", "C", shift=True), lambda a: None, lambda a: None, look("back"),
                  view("only"), lambda a: None, KeyEvent("c", "c"), lambda a: None, lambda a: None, look("only"),
                  view("both"), lambda a: None, KeyEvent("c", "c"), lambda a: None, lambda a: None, look("both")])
    # PgUp and PgDn, Ctrl with them, M and Y, each pair one hint, and T lead the bar; C after them.
    assert seen["bar"][:5] == [("PgUp/Dn", "Month"), ("^PgUp/Dn", "Year"), ("M/Y", "Choose"),
                               ("T", "Today"), ("C", "Gregorian")]
    # Nothing to swap with the Gregorian chosen: no hint, greyed.
    assert seen["gregorian"][3:] == ([], False)
    assert seen["hebrew"] == ("selected_grid", "hebrew", "23-03-2027", [("C", "Gregorian")], True)
    assert seen["swapped"] == ("gregorian_grid", "gregorian", "14 Adar II 5787", [("C", "Hebrew")], True)
    assert seen["back"][:2] == ("selected_grid", "hebrew")
    # The calendar alone becomes the Gregorian alone, still spelling nothing.
    assert seen["only"] == ("only", "gregorian", "", [("C", "Hebrew")], True)
    # Side by side there is nothing to swap.
    assert seen["both"][:2] == ("both", "hebrew") and seen["both"][3:] == ([], False)


def _languages() -> list[str]:
    from navkit.i18n import languages, register_package

    register_package("navml.locales")
    register_package("navigator.locales")
    return ["en", *sorted(code for code in languages() if code != "en")]


@pytest.mark.parametrize("code", _languages())
def test_the_calendar_s_key_bar_keeps_f1_and_f10_in_every_language(app, code):
    from navkit import i18n
    from navkit.bidi import display_width
    from navigator.widgets.shell.keybar.keybar import _label, _title

    seen = {}

    def look(a):
        row = a.shell.keybar._row()
        seen["keys"] = [key for key, _ in row]
        # Every item at its tightest: a blank before it, its key, a blank, its caption.
        seen["width"] = sum(1 + display_width(_label(key, item)) + 1 + display_width(_title(item)) for key, item in row)

    run_app(app, [open_calendar, Until(lambda a: calendar(a) is not None),
                  lambda a: setattr(i18n.LOCALE, "code", code), lambda a: setattr(calendar(a), "chosen", "hebrew"),
                  lambda a: None, look])
    assert {"PgUp/Dn", "^PgUp/Dn", "M/Y", "T", "C", "f1", "f10"} <= set(seen["keys"])
    assert seen["width"] <= 80, f"{code}: the calendar's key bar needs {seen['width']} columns"

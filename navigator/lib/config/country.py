"""How a date and a time are written: ``[country]``, DN's ``CountryInfo``.

DN read ``CountryInfo.DateFmt`` and ``TimeFmt`` wherever it put a file's
date on the screen -- the panels' columns, the overwrite query, the clock --
and so do these.  A 12-hour time is DN's: the hour with its leading zero and
``am``/``pm`` after it (``TClockView.FormatTimeStr``), spelled here rather
than by ``%p``, whose words are the C locale's and may be empty.
"""

from __future__ import annotations

import datetime
import time
from functools import lru_cache

from navkit.i18n import LOCALE, tr
from navkit.screen import char_width

from navml.widgets.dialog.masked_line import mask_for, spans

from navigator.settings import SETTINGS, CountryData

#: The ``strftime`` format of each preset order.
PRESETS: dict[str, str] = {"european": "%d-%m-%Y", "us": "%m/%d/%Y", "iso": "%Y-%m-%d"}


def date_format(section: CountryData | None = None) -> str:
    """The ``strftime`` format a date is written in: the preset's, or the
    custom one -- the European when that is left empty."""
    section = section or SETTINGS.country
    if section.date_format == "custom":
        return section.custom_date or PRESETS["european"]
    return PRESETS[section.date_format]


def typed_date_format(section: CountryData | None = None) -> str:
    """The format a date is *typed* in (File Attributes' masked line): the
    chosen one when it is day, month and year in digits, else the European.

    A mask holds digits in fixed places, so a custom format with a name in
    it (``%b``, ``%a``) or a directive twice cannot be typed into one.
    """
    format = date_format(section)
    directives = [directive.lower() for _, _, directive in spans(format)]
    try:
        mask_for(format)
    except ValueError:
        return PRESETS["european"]
    return format if sorted(directives) == ["d", "m", "y"] else PRESETS["european"]


def typed_time_format(section: CountryData | None = None) -> str:
    """The format a time is *typed* in (File Attributes' masked line), with
    the seconds: ``%H:%M:%S``, or ``%I:%M:%S%p`` in 12 hours."""
    return "%I:%M:%S%p" if twelve_hours(section) else "%H:%M:%S"


#: The day of the week each ``first_day`` is, as ``calendar`` counts.
WEEKDAYS = {"monday": 0, "sunday": 6, "saturday": 5}

#: What ``calendar = auto`` is in a language whose own calendar it is, by
#: language and region first (Taiwan's Chinese is the ROC's), then language;
#: any other language's is the Gregorian.
LANGUAGE_CALENDARS = {
    "he": "hebrew", "ar": "ummalqura", "zh": "chinese", "zh_TW": "roc", "ko": "korean", "vi": "vietnamese",
    "ja": "japanese", "th": "thai",
    "fa": "persian", "bn": "bengali", "ne": "nepali", "am": "ethiopian", "tr": "diyanet", "id": "mabims_id",
    "ms": "mabims_my", "my": "burmese", "bo": "tibetan", "dz": "tibetan", "km": "chhankitek", "lo": "chhankitek",
    "ps": "afghan", "prs": "afghan", "fa_AF": "afghan",
}


def first_weekday(section: CountryData | None = None) -> int:
    """The first column of a calendar, as ``calendar`` counts: 0 Monday,
    5 Saturday, 6 Sunday."""
    return WEEKDAYS.get((section or SETTINGS.country).first_day, 0)


def calendar_system(section: CountryData | None = None) -> str:
    """The calendar Utilities > Calendar shows its month in, a key of
    ``navml.calendars.SYSTEMS``: the chosen one, or for ``auto`` the
    language's -- read each call, so a bound value follows a change of
    language."""
    chosen = (section or SETTINGS.country).calendar
    if chosen != "auto":
        return chosen
    code = LOCALE.code.replace("-", "_")
    return LANGUAGE_CALENDARS.get(code) or LANGUAGE_CALENDARS.get(code.split("_")[0], "gregorian")


def calendar_view(section: CountryData | None = None) -> str:
    """What Utilities > Calendar shows of its calendar beside the Gregorian,
    one of ``CountryData.VIEWS``."""
    return (section or SETTINGS.country).calendar_view


def twelve_hours(section: CountryData | None = None) -> bool:
    return (section or SETTINGS.country).time_format == "12h"


def _date(when: time.struct_time, format: str) -> str:
    try:
        return time.strftime(format, when)
    except ValueError:
        # What the C library will not take (a lone ``%`` on some): the
        # European order rather than nothing at all.
        return time.strftime(PRESETS["european"], when)


def _time(when: time.struct_time, twelve: bool, separator: str = ":", seconds: bool = False) -> str:
    hour, minute = when.tm_hour, when.tm_min
    tail = f"{separator}{when.tm_sec:02d}" if seconds else ""
    if not twelve:
        return f"{hour:02d}{separator}{minute:02d}{tail}"
    return f"{(hour - 1) % 12 + 1:02d}{separator}{minute:02d}{tail}{'am' if hour < 12 else 'pm'}"


def format_date(when: time.struct_time) -> str:
    """*when*'s day in the chosen format, for a time already broken down."""
    return _date(when, date_format())


def format_time(when: time.struct_time, *, seconds: bool = False) -> str:
    """*when*'s ``hh:mm`` (``hh:mm:ss`` with *seconds*) in 24 hours, or with
    ``am``/``pm`` after it in 12."""
    return _time(when, twelve_hours(), seconds=seconds)


def date_text(mtime: float, section: CountryData | None = None) -> str:
    """*mtime*'s day in the chosen format."""
    return _date(time.localtime(mtime), date_format(section))


def time_text(mtime: float, section: CountryData | None = None, *, separator: str = ":") -> str:
    """*mtime*'s ``hh:mm`` in 24 hours, or ``hh:mmam``/``hh:mmpm`` in 12."""
    return _time(time.localtime(mtime), twelve_hours(section), separator)


def stamp(mtime: float, section: CountryData | None = None) -> str:
    """*mtime*'s date and time, a blank between: the panels' *Date* column."""
    return stamp_in(mtime, date_format(section), twelve_hours(section))


def last_used(when: float) -> str:
    """``Last used 28-10-2026 18:57`` for a history entry used at *when*;
    ``""`` for one from before the time was kept (0)."""
    return tr("Last used {time}").format(time=stamp(when)) if when else ""


def stamp_in(mtime: float, format: str, twelve: bool) -> str:
    """:func:`stamp` in a date *format* and hours not (yet) the settings'."""
    when = time.localtime(mtime)
    return f"{_date(when, format or PRESETS['european'])} {_time(when, twelve)}"


def stamp_width(section: CountryData | None = None) -> int:
    """The most columns :func:`stamp` takes in the chosen format.

    Read from the settings each call, so a computed calling it follows them;
    only the measuring is remembered.
    """
    return _stamp_width(date_format(section), twelve_hours(section))


@lru_cache(maxsize=16)
def _stamp_width(format: str, twelve: bool) -> int:
    # A week of every month: each month's and weekday's name, for a format
    # that spells them, and two-digit days and hours throughout.
    widest = 0
    for month in range(1, 13):
        for day in range(22, 29):
            when = datetime.datetime(2000, month, day, 23, 59).timetuple()
            text = f"{_date(when, format)} {_time(when, twelve)}"
            widest = max(widest, sum(char_width(char) for char in text))
    return widest


__all__ = ["PRESETS", "date_format", "date_text", "calendar_system", "calendar_view", "first_weekday", "format_date", "format_time", "stamp", "stamp_in", "stamp_width", "time_text", "twelve_hours",
           "typed_date_format", "typed_time_format"]

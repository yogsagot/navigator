"""Calendars other than the Gregorian: what a :class:`CalendarView` pages
through when told to, and spells the day under its cursor in.

Not DOS Navigator's, which had no calendar, nor TVDEMO's, whose month was
Gregorian only -- a departure, asked for with the Hebrew, Arabic, Chinese and
Japanese catalogues.  This first round holds the calendars that are pure
arithmetic, so they are exact without a table: Julian, Hebrew, Islamic (the
tabular one), Persian, Indian national (Śaka), Ethiopian and Coptic; and the
Chinese, which is astronomical and comes from the Hong Kong Observatory's
tables (the Korean and Vietnamese are computed by its rules in their own
time), Nepal's Bikram Sambat, published only as an almanac, and Saudi
Arabia's Umm al-Qura, which is computed and published as a
table, so they know only their tables' years (``CalendarSystem.span``).

**A day is a** :class:`datetime.date` **throughout**; a calendar only says
what that day is called in it.  Every conversion goes through the day's
ordinal, which is Reingold and Dershowitz's *fixed* day number (``R.D. 1`` is
the Gregorian 1 January 1), so their formulas from *Calendrical Calculations*
are written here unchanged.

**A month is numbered in the order of its year**, from 1: Hebrew Tishri is 1,
however the calendar itself counts Nisan first, so turning a page is adding
one to the month and carrying into the year, the same for every calendar.

Two are approximations of an observed or astronomical calendar, and say so in
their names or here: the **tabular Islamic** calendar may be a day off the
month a sighting of the moon or Saudi Arabia's Umm al-Qura table begins, and
the **Persian** one follows the 33-year leap rule, which agrees with Iran's
astronomical calendar from 1799 to 2256 and drifts outside it.
"""

from __future__ import annotations

import bisect
import calendar as _calendar
import datetime
import functools
import math
import re

from navkit.bidi import display_width as _width
from navkit.i18n import tr
from navkit.text import caption_runs

from navml import (
    badi_data,
    chinese_data,
    diyanet_data,
    korean_data,
    mabims_id_data,
    mabims_my_data,
    nepali_data,
    ummalqura_data,
    vietnamese_data,
)

#: A hotkey a language writes after its caption, as Japanese and Chinese do: ``暦(~H~)``.
_TRAILING_HOTKEY = re.compile(r"\s*[(（]~[^~]+~[)）]$")

#: The days a ``datetime.date`` can be.
FIRST, LAST = datetime.date.min.toordinal(), datetime.date.max.toordinal()
#: A day's Julian Day Number less its ``date`` ordinal.
ORDINAL_JDN = 1_721_425


def plain(caption: str) -> str:
    """*caption* without its hotkey, and without the brackets a hotkey written
    after it is in: ``~H~ebrew`` is ``Hebrew``, ``ヘブライ暦(~H~)`` ``ヘブライ暦``."""
    return "".join(run for run, _ in caption_runs(_TRAILING_HOTKEY.sub("", caption)))


def gregorian_month_names() -> list[str]:
    """The twelve months, January first, in the current language."""
    return [
        tr("January"), tr("February"), tr("March"), tr("April"), tr("May"), tr("June"),
        tr("July"), tr("August"), tr("September"), tr("October"), tr("November"),
        tr("December"),
    ]


def _date(fixed: int) -> datetime.date:
    if not FIRST <= fixed <= LAST:
        raise ValueError(f"day {fixed} is outside the years 1 to 9999")
    return datetime.date.fromordinal(fixed)


def _gregorian_fixed(year: int, month: int, day: int) -> int:
    """The fixed day of a Gregorian date, any year (0 and before included)."""
    leap = year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
    prior = year - 1
    return (365 * prior + prior // 4 - prior // 100 + prior // 400 + (367 * month - 362) // 12
            + (0 if month <= 2 else -1 if leap else -2) + day)


def _julian_leap(year: int) -> bool:
    return year % 4 == (0 if year > 0 else 3)


def _julian_fixed(year: int, month: int, day: int) -> int:
    """The fixed day of a Julian date; there is no year 0, -1 is 1 BC."""
    y = year + 1 if year < 0 else year
    return (JULIAN_EPOCH - 1 + 365 * (y - 1) + (y - 1) // 4 + (367 * month - 362) // 12
            + (0 if month <= 2 else -1 if _julian_leap(year) else -2) + day)


#: The Julian 1 January 1: two days before the Gregorian one.
JULIAN_EPOCH = _gregorian_fixed(0, 12, 30)


def _sunday_after(fixed: int) -> int:
    """The first Sunday after *fixed* (R.D. 0 was a Sunday)."""
    after = fixed + 7
    return after - after % 7


def orthodox_easter(year: int) -> datetime.date:
    """Easter of the Gregorian *year* as the Orthodox churches keep it: the
    Julian computus, on its Gregorian day."""
    shifted_epact = (14 + 11 * (year % 19)) % 30
    return _date(_sunday_after(_julian_fixed(year, 4, 19) - shifted_epact))


def easter(year: int) -> datetime.date:
    """Easter of the Gregorian *year* as the Western churches keep it."""
    century = year // 100 + 1
    shifted_epact = (14 + 11 * (year % 19) - (3 * century) // 4 + (5 + 8 * century) // 25) % 30
    if shifted_epact == 0 or (shifted_epact == 1 and 10 < year % 19):
        shifted_epact += 1
    return _date(_sunday_after(_gregorian_fixed(year, 4, 19) - shifted_epact))


class CalendarSystem:
    """One calendar: how a day is called in it, and how long its months are.

    A subclass gives :meth:`caption`, :meth:`from_fixed`, :meth:`to_fixed`,
    :meth:`months_in_year`, :meth:`days_in_month` and :meth:`month_names`;
    the rest is worked out from those.
    """

    #: Its name in ``[country] calendar`` and the window's menu.
    key = ""

    def caption(self) -> str:
        """Its name with a menu's hotkey marked, in the current language."""
        raise NotImplementedError

    def name(self) -> str:
        """Its name, in the current language."""
        return plain(self.caption())

    def from_fixed(self, fixed: int) -> tuple[int, int, int]:
        """The year, month (in year order) and day of the fixed day."""
        raise NotImplementedError

    def to_fixed(self, year: int, month: int, day: int) -> int:
        raise NotImplementedError

    def months_in_year(self, year: int) -> int:
        return 12

    def days_in_month(self, year: int, month: int) -> int:
        raise NotImplementedError

    def month_names(self, year: int) -> list[str]:
        """*year*'s months, in year order, in the current language."""
        raise NotImplementedError

    # -- what follows from those ---------------------------------------------

    def from_date(self, day: datetime.date) -> tuple[int, int, int]:
        return self.from_fixed(day.toordinal())

    def span(self) -> tuple[int, int]:
        """The first and last fixed day this calendar knows: every ``date``
        for one that is arithmetic, a table's years for one that is not."""
        return FIRST, LAST

    def holds(self, day: datetime.date) -> bool:
        first, last = self.span()
        return first <= day.toordinal() <= last

    def to_date(self, year: int, month: int, day: int) -> datetime.date:
        """The day, or ValueError when it is not one a ``date`` can be or
        this calendar knows."""
        fixed = self.to_fixed(year, month, day)
        first, last = self.span()
        if not first <= fixed <= last:
            raise ValueError(f"{self.key} knows no day {fixed}")
        return _date(fixed)

    def month_name(self, year: int, month: int) -> str:
        return self.month_names(year)[month - 1]

    def years(self) -> tuple[int, int]:
        """The first and last year a ``date`` reaches, the first no earlier
        than this calendar's year 1."""
        return max(1, self.from_fixed(FIRST)[0]), self.from_fixed(LAST)[0]

    def month_days(self, day: datetime.date) -> list[datetime.date]:
        """Every day of *day*'s month that a ``date`` can be."""
        year, month, _ = self.from_date(day)
        start = self.to_fixed(year, month, 1)
        first, last = self.span()
        days = range(start, start + self.days_in_month(year, month))
        return [datetime.date.fromordinal(fixed) for fixed in days if first <= fixed <= last]

    def add_months(self, day: datetime.date, months: int) -> datetime.date:
        """*day*, *months* on, on the same day of the month or the last one
        there is; ValueError past the years a ``date`` holds."""
        year, month, number = self.from_date(day)
        step = 1 if months > 0 else -1
        for _ in range(abs(months)):
            month += step
            if month > self.months_in_year(year):
                year, month = year + 1, 1
            elif month < 1:
                year -= 1
                month = self.months_in_year(year)
        return self.to_date(year, month, min(number, self.days_in_month(year, month)))

    def add_years(self, day: datetime.date, years: int) -> datetime.date:
        """*day*, *years* on: the same month by its name where the next year
        has one more or one fewer (Hebrew Adar), else its place, clamped."""
        year, month, number = self.from_date(day)
        target = year + years
        names, after = self.month_names(year), self.month_names(target)
        name = names[month - 1]
        month = after.index(name) + 1 if name in after else min(month, len(after))
        return self.to_date(target, month, min(number, self.days_in_month(target, month)))

    def day_label(self, day: datetime.date) -> int:
        """The number *day* is written with in its month: its place there for
        most calendars; the Tibetan, which skips and doubles day numbers,
        writes its own."""
        year, month, _ = self.from_date(day)
        return day.toordinal() - self.to_fixed(year, month, 1) + 1

    def year_text(self, day: datetime.date, short: bool = False) -> str:
        """*day*'s year as the calendar writes it -- its number for most, an
        era's name and year for one that counts by eras; *short*, a form for
        where the long one does not fit."""
        return str(self.from_date(day)[0])

    def year_label(self, year: int) -> str:
        """*year* in a list of years: its number, or its name and the number
        it is counted by for a calendar that writes it otherwise."""
        return str(year)

    def title(self, day: datetime.date, room: int) -> tuple[str, str]:
        """*day*'s month and year for a month's top row of *room* cells: the
        year written short when the long one does not fit."""
        year, month, _ = self.from_date(day)
        name, written = self.month_name(year, month), self.year_text(day)
        if _width(name) + 1 + _width(written) > room:
            written = self.year_text(day, short=True)
        return name, written

    def spell(self, day: datetime.date) -> str:
        """*day* written out: ``19 Heshvan 5787``."""
        year, month, _ = self.from_date(day)
        return tr("{day} {month} {year}").format(day=self.day_label(day), month=self.month_name(year, month),
                                                 year=self.year_text(day))

    def note(self, day: datetime.date) -> str:
        """What the day is in this calendar beyond its date -- a feast, for
        one that keeps them; ``""`` for most."""
        return ""


class Gregorian(CalendarSystem):
    key = "gregorian"

    def caption(self) -> str:
        return tr("~G~regorian")

    def from_fixed(self, fixed: int) -> tuple[int, int, int]:
        day = datetime.date.fromordinal(fixed)
        return day.year, day.month, day.day

    def to_fixed(self, year: int, month: int, day: int) -> int:
        return _gregorian_fixed(year, month, day)

    def days_in_month(self, year: int, month: int) -> int:
        return _calendar.monthrange(year, month)[1]

    def month_names(self, year: int) -> list[str]:
        return gregorian_month_names()

    def add_years(self, day: datetime.date, years: int) -> datetime.date:
        return self.add_months(day, 12 * years)


class Julian(CalendarSystem):
    """The Old Style, which the Orthodox churches of Jerusalem, Russia,
    Serbia, Georgia and Mount Athos keep: thirteen days behind until 2100."""

    key = "julian"

    def caption(self) -> str:
        return tr("~J~ulian")

    def from_fixed(self, fixed: int) -> tuple[int, int, int]:
        approx = (4 * (fixed - JULIAN_EPOCH) + 1464) // 1461
        year = approx - 1 if approx <= 0 else approx
        prior = fixed - _julian_fixed(year, 1, 1)
        correction = 0 if fixed < _julian_fixed(year, 3, 1) else 1 if _julian_leap(year) else 2
        month = (12 * (prior + correction) + 373) // 367
        return year, month, fixed - _julian_fixed(year, month, 1) + 1

    def to_fixed(self, year: int, month: int, day: int) -> int:
        return _julian_fixed(year, month, day)

    def days_in_month(self, year: int, month: int) -> int:
        if month == 2:
            return 29 if _julian_leap(year) else 28
        return 30 if month in (4, 6, 9, 11) else 31

    def month_names(self, year: int) -> list[str]:
        return gregorian_month_names()

    def note(self, day: datetime.date) -> str:
        notes = []
        if day == orthodox_easter(day.year):
            notes.append(tr("Easter (Orthodox)"))
        if day == easter(day.year):
            notes.append(tr("Easter (Western)"))
        return ", ".join(notes)


class Hebrew(CalendarSystem):
    """The Jewish calendar, fixed by Hillel II's rules: a year of twelve
    months, or of thirteen with Adar I before Adar II, seven times in nineteen
    years; it begins at Tishri, so Tishri is month 1 here."""

    key = "hebrew"

    #: Its 1 Tishri 1 (7 October 3761 BC, Julian).
    EPOCH = _julian_fixed(-3761, 10, 7)
    #: R&D's numbers, which begin at Nisan.
    NISAN, ADAR, ADAR_II, TISHRI = 1, 12, 13, 7

    def caption(self) -> str:
        return tr("~H~ebrew")

    @staticmethod
    def leap(year: int) -> bool:
        return (7 * year + 1) % 19 < 7

    @staticmethod
    def _elapsed(year: int) -> int:
        """Days from the epoch to the molad of Tishri, Tuesday-Thursday-Saturday
        postponed (the *molad zaken* and *lo ADU rosh*)."""
        months = (235 * year - 234) // 19
        parts = 12084 + 13753 * months
        days = 29 * months + parts // 25920
        return days + 1 if (3 * (days + 1)) % 7 < 3 else days

    def _new_year(self, year: int) -> int:
        """1 Tishri of *year*: a year 356 or 382 days long is put right."""
        ny0, ny1, ny2 = self._elapsed(year - 1), self._elapsed(year), self._elapsed(year + 1)
        correction = 2 if ny2 - ny1 == 356 else 1 if ny1 - ny0 == 382 else 0
        return self.EPOCH + ny1 + correction

    def _year_length(self, year: int) -> int:
        return self._new_year(year + 1) - self._new_year(year)

    def _last_day(self, year: int, month: int) -> int:
        """R&D's ``last-day-of-hebrew-month``, by Nisan's numbering."""
        length = self._year_length(year)
        if (month in (2, 4, 6, 10, 13) or (month == self.ADAR and not self.leap(year))
                or (month == 8 and length not in (355, 385)) or (month == 9 and length in (353, 383))):
            return 29
        return 30

    def _order(self, year: int) -> list[int]:
        """Nisan's numbers of *year*'s months, Tishri first."""
        last = self.ADAR_II if self.leap(year) else self.ADAR
        return [*range(self.TISHRI, last + 1), *range(self.NISAN, self.TISHRI)]

    def months_in_year(self, year: int) -> int:
        return 13 if self.leap(year) else 12

    def days_in_month(self, year: int, month: int) -> int:
        return self._last_day(year, self._order(year)[month - 1])

    def to_fixed(self, year: int, month: int, day: int) -> int:
        fixed = self._new_year(year) + day - 1
        for earlier in self._order(year)[: month - 1]:
            fixed += self._last_day(year, earlier)
        return fixed

    def from_fixed(self, fixed: int) -> tuple[int, int, int]:
        year = (98496 * (fixed - self.EPOCH)) // 35975351
        while self._new_year(year + 1) <= fixed:
            year += 1
        month, start = 1, self._new_year(year)
        while fixed >= start + self.days_in_month(year, month):
            start += self.days_in_month(year, month)
            month += 1
        return year, month, fixed - start + 1

    def month_names(self, year: int) -> list[str]:
        names = {
            1: tr("Nisan"), 2: tr("Iyyar"), 3: tr("Sivan"), 4: tr("Tammuz"), 5: tr("Av"), 6: tr("Elul"),
            7: tr("Tishri"), 8: tr("Heshvan"), 9: tr("Kislev"), 10: tr("Tevet"), 11: tr("Shevat"),
            12: tr("Adar I") if self.leap(year) else tr("Adar"), 13: tr("Adar II"),
        }
        return [names[month] for month in self._order(year)]

    def add_years(self, day: datetime.date, years: int) -> datetime.date:
        # Adar of a common year is Adar II in a leap one, where Purim is,
        # and Adar I or II back to Adar.
        year, month, number = self.from_date(day)
        target = year + years
        hebrew = self._order(year)[month - 1]
        if hebrew == self.ADAR and self.leap(year) and not self.leap(target):
            hebrew = self.ADAR
        elif hebrew == self.ADAR_II and not self.leap(target):
            hebrew = self.ADAR
        elif hebrew == self.ADAR and not self.leap(year) and self.leap(target):
            hebrew = self.ADAR_II
        month = self._order(target).index(hebrew) + 1
        return self.to_date(target, month, min(number, self.days_in_month(target, month)))


class Islamic(CalendarSystem):
    """The Hijri calendar by its arithmetic: twelve months of 30 and 29 days
    in turn, Dhu al-Hijja given a 30th eleven years in thirty.  A month that
    begins by sighting the moon, or by Saudi Arabia's Umm al-Qura table, may
    begin a day either side."""

    key = "islamic"

    #: 1 Muharram 1, Friday 16 July 622 (Julian).
    EPOCH = _julian_fixed(622, 7, 16)

    def caption(self) -> str:
        return tr("~I~slamic (tabular)")

    @staticmethod
    def leap(year: int) -> bool:
        return (14 + 11 * year) % 30 < 11

    def to_fixed(self, year: int, month: int, day: int) -> int:
        return self.EPOCH - 1 + (year - 1) * 354 + (3 + 11 * year) // 30 + 29 * (month - 1) + month // 2 + day

    def from_fixed(self, fixed: int) -> tuple[int, int, int]:
        year = (30 * (fixed - self.EPOCH) + 10646) // 10631
        prior = fixed - self.to_fixed(year, 1, 1)
        month = (11 * prior + 330) // 325
        return year, month, fixed - self.to_fixed(year, month, 1) + 1

    def days_in_month(self, year: int, month: int) -> int:
        if month == 12:
            return 30 if self.leap(year) else 29
        return 30 if month % 2 else 29

    def month_names(self, year: int) -> list[str]:
        return [
            tr("Muharram"), tr("Safar"), tr("Rabi' I"), tr("Rabi' II"), tr("Jumada I"), tr("Jumada II"),
            tr("Rajab"), tr("Sha'ban"), tr("Ramadan"), tr("Shawwal"), tr("Dhu'l-Qa'da"), tr("Dhu'l-Hijja"),
        ]


class TabledIslamic(Islamic):
    """A Hijri calendar whose months are a table of their first days rather
    than the tabular cycle: :attr:`data` holds ``FIRST_YEAR``, ``FIRST_MONTH``
    (1 when absent), ``MONTH_STARTS`` -- each month's first day, then the day
    after the last -- and ``PUBLISHED_LAST``, the last published month's first
    day, after which the months are computed (absent, all are published).  It
    knows no day outside the table (:meth:`span`)."""

    data: object = None

    @property
    def _first_month(self) -> int:
        return getattr(self.data, "FIRST_MONTH", 1)

    def span(self) -> tuple[int, int]:
        return self.data.MONTH_STARTS[0], self.data.MONTH_STARTS[-1] - 1

    def years(self) -> tuple[int, int]:
        return self.data.FIRST_YEAR, self.from_fixed(self.span()[1])[0]

    def _index(self, year: int, month: int) -> int:
        index = 12 * (year - self.data.FIRST_YEAR) + month - self._first_month
        if not 0 <= index < len(self.data.MONTH_STARTS) - 1:
            raise ValueError(f"the {self.key} table has no month {year}/{month}")
        return index

    def to_fixed(self, year: int, month: int, day: int) -> int:
        return self.data.MONTH_STARTS[self._index(year, month)] + day - 1

    def from_fixed(self, fixed: int) -> tuple[int, int, int]:
        first, last = self.span()
        if not first <= fixed <= last:
            raise ValueError(f"the {self.key} table knows no day {fixed}")
        index = bisect.bisect_right(self.data.MONTH_STARTS, fixed) - 1
        year, month = divmod(index + self._first_month - 1, 12)
        return self.data.FIRST_YEAR + year, month + 1, fixed - self.data.MONTH_STARTS[index] + 1

    def days_in_month(self, year: int, month: int) -> int:
        index = self._index(year, month)
        return self.data.MONTH_STARTS[index + 1] - self.data.MONTH_STARTS[index]

    def note(self, day: datetime.date) -> str:
        published_last = getattr(self.data, "PUBLISHED_LAST", None)
        if published_last is not None and day.toordinal() > published_last:
            year, month, _ = self.from_date(day)
            if self.to_fixed(year, month, 1) > published_last:
                return tr("Computed: the published calendar may differ by a day")
        return ""


class UmmAlQura(TabledIslamic):
    """Saudi Arabia's official Hijri calendar, whose months begin by a
    computed rule rather than the tabular cycle: the table R. H. van Gent
    keeps (``navml/ummalqura_data.py``, written by ``tools/umm_al_qura.py``),
    1 Muharram 1356 (14 March 1937) to the end of 1500 (16 November 2077).
    The tabular calendar puts two days in three of those years in another
    month or a day off."""

    key = "ummalqura"
    data = ummalqura_data

    def caption(self) -> str:
        return tr("Islamic (~U~mm al-Qura)")


class Diyanet(TabledIslamic):
    """Turkey's Hijri calendar, which its Presidency of Religious Affairs
    (Diyanet) publishes: R. H. van Gent's tabulation of it, 1318 to 1449 AH
    (1900 to 2027), then computed (``navml/diyanet_data.py``,
    ``tools/hijri_criteria.py``) by the rule it has kept since 2016, the
    Istanbul congress's -- the month begins when the crescent is 5 degrees
    high and 8 from the Sun at sunset somewhere on Earth before 0h UT, or
    later on the Americas' mainland if the conjunction came before dawn in
    New Zealand -- which gives 137 of its 140 months since."""

    key = "diyanet"
    data = diyanet_data

    def caption(self) -> str:
        return tr("Islamic (Di~y~anet, Turkey)")


class MabimsIndonesia(TabledIslamic):
    """Indonesia's Hijri calendar by the MABIMS criterion (Brunei, Indonesia,
    Malaysia and Singapore's): van Gent's tabulation, 1999 to 2015, then
    computed (``navml/mabims_id_data.py``) by its rule over Indonesia --
    altitude 2 degrees and elongation 3 or age 8 hours at sunset until 1442
    AH, which gives 96% of the published months, Neo-MABIMS (3 and 6.4)
    from 1443."""

    key = "mabims_id"
    data = mabims_id_data

    def caption(self) -> str:
        return tr("Islamic (~M~ABIMS, Indonesia)")


class MabimsMalaysia(TabledIslamic):
    """Malaysia's Hijri calendar by the MABIMS criterion: van Gent's
    tabulation, 1994 to 2015, then computed (``navml/mabims_my_data.py``)
    by its rule over Malaysia -- altitude 2 and elongation 3 degrees, or age
    8 hours, at sunset until 1442 AH, which gives every published month,
    Neo-MABIMS (altitude 3, elongation 6.4) from 1443.  Singapore's and
    Brunei's follow it but for a day now and then."""

    key = "mabims_my"
    data = mabims_my_data

    def caption(self) -> str:
        return tr("Islamic (MABIMS, Malay~s~ia)")


class Persian(CalendarSystem):
    """The Solar Hijri calendar of Iran and Afghanistan: six months of 31
    days, five of 30 and Esfand of 29, or 30 in a leap year -- here the
    33-year rule's eight, which Iran's astronomical one agrees with from 1178
    to 1634 (1799 to 2256)."""

    key = "persian"

    #: The years of a 33 that are leap.
    LEAP = frozenset({1, 5, 9, 13, 17, 22, 26, 30})
    #: 1 Farvardin 1404 is 21 March 2025, which the rule counts from.
    ANCHOR_YEAR, ANCHOR = 1404, _gregorian_fixed(2025, 3, 21)

    def caption(self) -> str:
        return tr("~P~ersian")

    def leap(self, year: int) -> bool:
        return year % 33 in self.LEAP

    def _leaps_through(self, year: int) -> int:
        """How many years up to and including *year* are leap (from year 0)."""
        cycles, rest = divmod(year, 33)
        return 8 * cycles + sum(1 for leap in self.LEAP if leap <= rest)

    def _new_year(self, year: int) -> int:
        return (self.ANCHOR + 365 * (year - self.ANCHOR_YEAR)
                + self._leaps_through(year - 1) - self._leaps_through(self.ANCHOR_YEAR - 1))

    def to_fixed(self, year: int, month: int, day: int) -> int:
        before = 31 * (month - 1) if month <= 7 else 186 + 30 * (month - 7)
        return self._new_year(year) + before + day - 1

    def from_fixed(self, fixed: int) -> tuple[int, int, int]:
        year = self.ANCHOR_YEAR + (fixed - self.ANCHOR) * 10000 // 3652422
        while self._new_year(year) > fixed:
            year -= 1
        while self._new_year(year + 1) <= fixed:
            year += 1
        into = fixed - self._new_year(year)
        if into < 186:
            return year, into // 31 + 1, into % 31 + 1
        return year, (into - 186) // 30 + 7, (into - 186) % 30 + 1

    def days_in_month(self, year: int, month: int) -> int:
        if month == 12:
            return 30 if self.leap(year) else 29
        return 31 if month <= 6 else 30

    def month_names(self, year: int) -> list[str]:
        return [
            tr("Farvardin"), tr("Ordibehesht"), tr("Khordad"), tr("Tir"), tr("Mordad"), tr("Shahrivar"),
            tr("Mehr"), tr("Aban"), tr("Azar"), tr("Dey"), tr("Bahman"), tr("Esfand"),
        ]


class Indian(CalendarSystem):
    """India's national calendar, of the Śaka era, the Gazette's since 1957:
    Chaitra begins on 22 March (21 in a Gregorian leap year), the next five
    months have 31 days and the last six 30."""

    key = "indian"

    def caption(self) -> str:
        return tr("In~d~ian national (Saka)")

    @staticmethod
    def leap(year: int) -> bool:
        return _calendar.isleap(year + 78) if year + 78 > 0 else (year + 78) % 4 == 0

    def _new_year(self, year: int) -> int:
        return _gregorian_fixed(year + 78, 3, 21 if self.leap(year) else 22)

    def days_in_month(self, year: int, month: int) -> int:
        if month == 1:
            return 31 if self.leap(year) else 30
        return 31 if month <= 6 else 30

    def to_fixed(self, year: int, month: int, day: int) -> int:
        start = self._new_year(year)
        for earlier in range(1, month):
            start += self.days_in_month(year, earlier)
        return start + day - 1

    def from_fixed(self, fixed: int) -> tuple[int, int, int]:
        year = datetime.date.fromordinal(fixed).year - 78
        if fixed < self._new_year(year):
            year -= 1
        month, start = 1, self._new_year(year)
        while fixed >= start + self.days_in_month(year, month):
            start += self.days_in_month(year, month)
            month += 1
        return year, month, fixed - start + 1

    def month_names(self, year: int) -> list[str]:
        return [
            tr("Chaitra"), tr("Vaishakha"), tr("Jyeshtha"), tr("Ashadha"), tr("Shravana"), tr("Bhadra"),
            tr("Ashvin"), tr("Kartika"), tr("Agrahayana"), tr("Pausha"), tr("Magha"), tr("Phalguna"),
        ]


class Coptic(CalendarSystem):
    """The Coptic Church's calendar, of the Era of the Martyrs: twelve months
    of thirty days and a thirteenth of five, or six before a Julian leap year."""

    key = "coptic"

    #: 1 Thout 1, 29 August 284 (Julian).
    EPOCH = _julian_fixed(284, 8, 29)

    def caption(self) -> str:
        return tr("~C~optic")

    @staticmethod
    def leap(year: int) -> bool:
        return year % 4 == 3

    def months_in_year(self, year: int) -> int:
        return 13

    def _coptic_fixed(self, year: int, month: int, day: int) -> int:
        return self.EPOCH - 1 + 365 * (year - 1) + year // 4 + 30 * (month - 1) + day

    def _coptic_date(self, fixed: int) -> tuple[int, int, int]:
        year = (4 * (fixed - self.EPOCH) + 1463) // 1461
        month = (fixed - self._coptic_fixed(year, 1, 1)) // 30 + 1
        return year, month, fixed + 1 - self._coptic_fixed(year, month, 1)

    def to_fixed(self, year: int, month: int, day: int) -> int:
        return self._coptic_fixed(year, month, day)

    def from_fixed(self, fixed: int) -> tuple[int, int, int]:
        return self._coptic_date(fixed)

    def days_in_month(self, year: int, month: int) -> int:
        if month == 13:
            return 6 if self.leap(year) else 5
        return 30

    def month_names(self, year: int) -> list[str]:
        return [
            tr("Thout"), tr("Paopi"), tr("Hathor"), tr("Koiak"), tr("Tobi"), tr("Meshir"), tr("Paremhat"),
            tr("Parmouti"), tr("Pashons"), tr("Paoni"), tr("Epip"), tr("Mesori"), tr("Nasie"),
        ]


class Ethiopian(Coptic):
    """Ethiopia's and Eritrea's calendar: the Coptic months under their Ge'ez
    names, its years counted from the Incarnation as Ethiopia reckons it."""

    key = "ethiopian"

    #: 1 Meskerem 1, 29 August 8 (Julian).
    ETHIOPIC_EPOCH = _julian_fixed(8, 8, 29)

    def caption(self) -> str:
        return tr("~E~thiopian")

    def to_fixed(self, year: int, month: int, day: int) -> int:
        return self._coptic_fixed(year, month, day) + self.ETHIOPIC_EPOCH - self.EPOCH

    def from_fixed(self, fixed: int) -> tuple[int, int, int]:
        return self._coptic_date(fixed + self.EPOCH - self.ETHIOPIC_EPOCH)

    def month_names(self, year: int) -> list[str]:
        return [
            tr("Meskerem"), tr("Tikimt"), tr("Hidar"), tr("Tahsas"), tr("Ter"), tr("Yekatit"), tr("Megabit"),
            tr("Miyazya"), tr("Ginbot"), tr("Sene"), tr("Hamle"), tr("Nehase"), tr("Pagume"),
        ]


class Chinese(CalendarSystem):
    """The Chinese lunisolar calendar (农历), as the Hong Kong Observatory
    publishes it for 1901 to 2099 (``navml/self.data.py``, written by
    ``tools/chinese_calendar.py``): a month begins on the day of the new moon
    in Beijing, and a year of thirteen repeats the number of the month its
    leap month follows -- the solar terms decide which.  There is no formula,
    so outside those years it knows no day (:meth:`span`).  A year is
    numbered by the Gregorian one its first month begins in, and named in the
    sexagenary cycle in its :meth:`note`."""

    key = "chinese"
    #: Its months: ``FIRST_YEAR`` and ``YEARS``, as ``tools/chinese_calendar.py`` writes them.
    data = chinese_data

    def __init__(self) -> None:
        self._starts = [start for start, _, _ in self.data.YEARS]
        last_start, leap, bits = self.data.YEARS[-1]
        self._end = last_start + sum(self._lengths(leap, bits)) - 1

    def caption(self) -> str:
        return tr("Chi~n~ese")

    @staticmethod
    def _lengths(leap: int, bits: int) -> list[int]:
        return [30 if bits >> i & 1 else 29 for i in range(13 if leap else 12)]

    def _year(self, year: int) -> tuple[int, int, int]:
        index = year - self.data.FIRST_YEAR
        if not 0 <= index < len(self.data.YEARS):
            raise ValueError(f"the {self.key} calendar here has no year {year}")
        return self.data.YEARS[index]

    def span(self) -> tuple[int, int]:
        return self._starts[0], self._end

    def years(self) -> tuple[int, int]:
        return self.data.FIRST_YEAR, self.data.FIRST_YEAR + len(self.data.YEARS) - 1

    def months_in_year(self, year: int) -> int:
        try:
            return 13 if self._year(year)[1] else 12
        except ValueError:
            return 12

    def days_in_month(self, year: int, month: int) -> int:
        _, leap, bits = self._year(year)
        return self._lengths(leap, bits)[month - 1]

    def to_fixed(self, year: int, month: int, day: int) -> int:
        start, leap, bits = self._year(year)
        return start + sum(self._lengths(leap, bits)[: month - 1]) + day - 1

    def from_fixed(self, fixed: int) -> tuple[int, int, int]:
        first, last = self.span()
        if not first <= fixed <= last:
            raise ValueError(f"the {self.key} calendar here knows no day {fixed}")
        index = bisect.bisect_right(self._starts, fixed) - 1
        start, leap, bits = self.data.YEARS[index]
        into = fixed - start
        for month, length in enumerate(self._lengths(leap, bits), 1):
            if into < length:
                return self.data.FIRST_YEAR + index, month, into + 1
            into -= length
        raise AssertionError("a day past its year's months")

    def number(self, year: int, month: int) -> tuple[int, bool]:
        """Month *month* of *year* (in year order) as the calendar numbers it,
        and whether it is the leap one."""
        leap = self._year(year)[1]
        if leap and month > leap:
            return month - 1, month == leap + 1
        return month, False

    def month_names(self, year: int) -> list[str]:
        regular = [
            tr("Month 1"), tr("Month 2"), tr("Month 3"), tr("Month 4"), tr("Month 5"), tr("Month 6"),
            tr("Month 7"), tr("Month 8"), tr("Month 9"), tr("Month 10"), tr("Month 11"), tr("Month 12"),
        ]
        try:
            leap = self._year(year)[1]
        except ValueError:
            return regular
        if leap:
            regular.insert(leap, tr("Leap {number}").format(number=leap, month=regular[leap - 1]))
        return regular

    def add_years(self, day: datetime.date, years: int) -> datetime.date:
        # The same month by its number; a leap one where the year has it
        # leap too, else the month it repeats.
        year, month, number = self.from_date(day)
        target = year + years
        counted, leap = self.number(year, month)
        target_leap = self._year(target)[1]
        month = counted + (1 if leap and target_leap == counted else 0) + (
            1 if target_leap and counted > target_leap else 0)
        return self.to_date(target, month, min(number, self.days_in_month(target, month)))

    def note(self, day: datetime.date) -> str:
        """The year's name in the sexagenary cycle and its animal, and the
        Spring Festival on New Year's day."""
        year, month, number = self.from_date(day)
        stems = [tr("Jiǎ"), tr("Yǐ"), tr("Bǐng"), tr("Dīng"), tr("Wù"), tr("Jǐ"), tr("Gēng"), tr("Xīn"),
                 tr("Rén"), tr("Guǐ")]
        branches = [tr("Zǐ"), tr("Chǒu"), tr("Yín"), tr("Mǎo"), tr("Chén"), tr("Sì"), tr("Wǔ"), tr("Wèi"),
                    tr("Shēn"), tr("Yǒu"), tr("Xū"), tr("Hài")]
        cycle = year - 4
        named = tr("{stem}-{branch}, year of the {animal}").format(
            stem=stems[cycle % 10], branch=branches[cycle % 12], animal=self.animals()[cycle % 12])
        if month == 1 and number == 1:
            return ", ".join((self.new_year(), named))
        return named

    def animals(self) -> list[str]:
        """The twelve animals of the branches, the Rat first."""
        return [tr("Rat"), tr("Ox"), tr("Tiger"), tr("Rabbit"), tr("Dragon"), tr("Snake"), tr("Horse"),
                tr("Goat"), tr("Monkey"), tr("Rooster"), tr("Dog"), tr("Pig")]

    def new_year(self) -> str:
        return tr("Spring Festival")


class Korean(Chinese):
    """Korea's lunisolar calendar (음력), the Chinese calendar's rules in Korea's
    standard time, so a month begins a day after China's when the new moon
    falls in the hour before Seoul's midnight (Seollal 1997 and 2027, a day
    after China's New Year).  Korea's astronomers publish no open table, so
    its months are computed (``navml/korean_data.py``, ``tools/lunisolar.py``,
    whose method gives the Hong Kong Observatory's months when reckoned in
    Beijing's time)."""

    key = "korean"
    data = korean_data

    def caption(self) -> str:
        return tr("~K~orean")

    def new_year(self) -> str:
        return tr("Seollal")


class Vietnamese(Chinese):
    """Vietnam's lunisolar calendar (âm lịch): the Chinese calendar until
    1968, then its rules in UTC+7, so Tết can fall a day before China's New
    Year -- or a month, as in 1985.  Computed like the Korean
    (``navml/vietnamese_data.py``); its zodiac has the Buffalo and the Cat
    where China's has the Ox and the Rabbit."""

    key = "vietnamese"
    data = vietnamese_data

    def caption(self) -> str:
        return tr("~V~ietnamese")

    def animals(self) -> list[str]:
        animals = super().animals()
        animals[1], animals[3] = tr("Buffalo"), tr("Cat")
        return animals

    def new_year(self) -> str:
        return tr("Tết")


class Japanese(Gregorian):
    """The Gregorian calendar as Japan has kept it since 1873, its years
    counted by the emperor's era (元号): Meiji, Taishō, Shōwa, Heisei, Reiwa,
    each beginning on the day it was proclaimed, so a month can hold two
    (January 1989: Shōwa 64 to the 7th, Heisei 1 from the 8th).  Before 1873
    Japan's calendar was lunisolar, which this is not, so it knows no day
    before it (:meth:`span`).  The first year of an era is written 1, not 元
    (*gannen*), as most software writes it."""

    key = "japanese"

    #: Each era's first day, and the Latin letter its year is written short with.
    ERAS = (
        (datetime.date(1868, 10, 23), "M"),
        (datetime.date(1912, 7, 30), "T"),
        (datetime.date(1926, 12, 25), "S"),
        (datetime.date(1989, 1, 8), "H"),
        (datetime.date(2019, 5, 1), "R"),
    )

    def caption(self) -> str:
        return tr("J~a~panese")

    def span(self) -> tuple[int, int]:
        return datetime.date(1873, 1, 1).toordinal(), LAST

    def years(self) -> tuple[int, int]:
        return 1873, 9999

    @staticmethod
    def _names() -> list[str]:
        return [tr("Meiji"), tr("Taishō"), tr("Shōwa"), tr("Heisei"), tr("Reiwa")]

    def era(self, day: datetime.date) -> tuple[str, str, int]:
        """*day*'s era's name, its letter, and the year of it."""
        index = max(i for i, (start, _) in enumerate(self.ERAS) if start <= day) if day >= self.ERAS[0][0] else 0
        start, letter = self.ERAS[index]
        return self._names()[index], letter, day.year - start.year + 1

    def year_text(self, day: datetime.date, short: bool = False) -> str:
        name, letter, year = self.era(day)
        return f"{letter}{year}" if short else tr("{era} {year}").format(era=name, year=year)

    def year_label(self, year: int) -> str:
        # The era the year ends in: 2019 is Reiwa 1.
        return tr("{label} ({year})").format(label=self.year_text(datetime.date(year, 12, 31)), year=year)

    def note(self, day: datetime.date) -> str:
        return self.year_text(day)


class Thai(Gregorian):
    """Thailand's solar calendar: the Gregorian months, its years those of
    the Buddhist Era (พ.ศ.), 543 more.  Before 1941 the Thai year began on
    1 April; here it begins in January throughout, as Thailand's has since."""

    key = "thai"

    def caption(self) -> str:
        return tr("~T~hai solar")

    def year_text(self, day: datetime.date, short: bool = False) -> str:
        year = day.year + 543
        return str(year) if short else tr("{year} BE").format(year=year)

    def year_label(self, year: int) -> str:
        return tr("{label} ({year})").format(label=self.year_text(datetime.date(year, 1, 1)), year=year)


class Minguo(Gregorian):
    """The Republic of China's calendar, Taiwan's official one: the Gregorian
    months, its years counted from 1912 (民國), and those before it back from
    then (民前, 1911 is 1 before)."""

    key = "roc"

    def caption(self) -> str:
        return tr("~R~OC (Minguo)")

    def year_text(self, day: datetime.date, short: bool = False) -> str:
        year = day.year - 1911
        if year >= 1:
            return str(year) if short else tr("ROC {year}").format(year=year)
        return f"-{1 - year}" if short else tr("{year} before ROC").format(year=1 - year)

    def year_label(self, year: int) -> str:
        return tr("{label} ({year})").format(label=self.year_text(datetime.date(year, 1, 1)), year=year)


class Bengali(CalendarSystem):
    """Bangladesh's Bengali calendar (বঙ্গাব্দ) as revised in 2019: the year
    begins on 14 April (Pohela Boishakh), its first six months have 31 days,
    Falgun 29 or 30 in a Gregorian leap year and the rest 30, so that 21
    February is always 8 Falgun, 26 March 12 Chaitra and 16 December 1 Poush.
    Kept by that rule throughout, before 2019 too; West Bengal's, which
    follows the sidereal sun, is not this."""

    key = "bengali"

    def caption(self) -> str:
        return tr("~B~engali (Bangladesh)")

    @staticmethod
    def _leap(year: int) -> bool:
        """Whether Falgun of *year* falls in a Gregorian leap year's February."""
        gregorian = year + 594
        return gregorian % 4 == 0 and (gregorian % 100 != 0 or gregorian % 400 == 0)

    def _new_year(self, year: int) -> int:
        return _gregorian_fixed(year + 593, 4, 14)

    def days_in_month(self, year: int, month: int) -> int:
        if month <= 6:
            return 31
        if month == 11:
            return 30 if self._leap(year) else 29
        return 30

    def to_fixed(self, year: int, month: int, day: int) -> int:
        return self._new_year(year) + sum(self.days_in_month(year, earlier) for earlier in range(1, month)) + day - 1

    def from_fixed(self, fixed: int) -> tuple[int, int, int]:
        year = datetime.date.fromordinal(fixed).year - 593
        if fixed < self._new_year(year):
            year -= 1
        month, start = 1, self._new_year(year)
        while fixed >= start + self.days_in_month(year, month):
            start += self.days_in_month(year, month)
            month += 1
        return year, month, fixed - start + 1

    def month_names(self, year: int) -> list[str]:
        return [
            tr("Boishakh"), tr("Joishtho"), tr("Asharh"), tr("Shrabon"), tr("Bhadro"), tr("Ashwin"),
            tr("Kartik"), tr("Ogrohayon"), tr("Poush"), tr("Magh"), tr("Falgun"), tr("Choitro"),
        ]


class Nepali(CalendarSystem):
    """Nepal's official calendar, Bikram Sambat (विक्रम संवत्): solar and
    sidereal, a month beginning with the Sun's entry into the next sign and
    lasting 29 to 32 days, the year with Baisakh in mid-April.  Its months
    are a table (``navml/nepali_data.py``, ``tools/bikram_sambat.py``): the
    almanac's as published, 1975 to 2083 BS, then computed by the rule that
    gives those, to 2156 BS -- which the :meth:`note` of such a day says, the
    almanac being free to differ by a day."""

    key = "nepali"

    def __init__(self) -> None:
        self._starts = [start for start, _ in nepali_data.YEARS]
        last_start, months = nepali_data.YEARS[-1]
        self._end = last_start + sum(months) - 1

    def caption(self) -> str:
        return tr("Nepa~l~i (Bikram Sambat)")

    def _year(self, year: int) -> tuple[int, tuple[int, ...]]:
        index = year - nepali_data.FIRST_YEAR
        if not 0 <= index < len(nepali_data.YEARS):
            raise ValueError(f"the Bikram Sambat table has no year {year}")
        return nepali_data.YEARS[index]

    def span(self) -> tuple[int, int]:
        return self._starts[0], self._end

    def years(self) -> tuple[int, int]:
        return nepali_data.FIRST_YEAR, nepali_data.FIRST_YEAR + len(nepali_data.YEARS) - 1

    def days_in_month(self, year: int, month: int) -> int:
        return self._year(year)[1][month - 1]

    def to_fixed(self, year: int, month: int, day: int) -> int:
        start, months = self._year(year)
        return start + sum(months[: month - 1]) + day - 1

    def from_fixed(self, fixed: int) -> tuple[int, int, int]:
        first, last = self.span()
        if not first <= fixed <= last:
            raise ValueError(f"the Bikram Sambat table knows no day {fixed}")
        index = bisect.bisect_right(self._starts, fixed) - 1
        start, months = nepali_data.YEARS[index]
        into = fixed - start
        for month, length in enumerate(months, 1):
            if into < length:
                return nepali_data.FIRST_YEAR + index, month, into + 1
            into -= length
        raise AssertionError("a day past its year's months")

    def month_names(self, year: int) -> list[str]:
        return [
            tr("Baisakh"), tr("Jestha"), tr("Asar"), tr("Shrawan"), tr("Bhadau"), tr("Asoj"),
            tr("Kartik"), tr("Mangsir"), tr("Poush"), tr("Magh"), tr("Falgun"), tr("Chait"),
        ]

    def note(self, day: datetime.date) -> str:
        if self.from_date(day)[0] > nepali_data.PUBLISHED_LAST:
            return tr("Computed: Nepal's almanac may differ by a day")
        return ""


class Badi(CalendarSystem):
    """The Badíʿ calendar of the Baháʼí Faith: nineteen months of nineteen
    days, and before the last the days of Ayyám-i-Há, four or five, so the
    year reaches the next Naw-Rúz -- here a month of its own, the 19th, and
    ʿAláʼ, the fast, the 20th.  Year 1 began at Naw-Rúz 1844.  Naw-Rúz was 21
    March until 171 BE; since 172 (2015) it is the day that holds the March
    equinox at Ṭihrán (``navml/badi_data.py``, ``tools/badi.py``: the World
    Centre's published days to 221 BE, computed after).  A Baháʼí day begins
    at sunset; a date here is the day that ends it, as the World Centre's
    tables give the Gregorian equivalent."""

    key = "badi"

    def caption(self) -> str:
        return tr("Badíʿ (Baháʼí)")

    def naw_ruz(self, year: int) -> int:
        """The first day of *year*, as an ordinal."""
        index = year - badi_data.FIRST_YEAR
        if index < 0:
            return _gregorian_fixed(year + 1843, 3, 21)
        if index >= len(badi_data.NAW_RUZ):
            raise ValueError(f"the Badíʿ table has no year {year}")
        return badi_data.NAW_RUZ[index]

    def span(self) -> tuple[int, int]:
        return _gregorian_fixed(1844, 3, 21), badi_data.NAW_RUZ[-1] - 1

    def years(self) -> tuple[int, int]:
        return 1, badi_data.FIRST_YEAR + len(badi_data.NAW_RUZ) - 2

    def months_in_year(self, year: int) -> int:
        return 20

    def days_in_month(self, year: int, month: int) -> int:
        if month == 19:
            return self.naw_ruz(year + 1) - self.naw_ruz(year) - 361
        return 19

    def to_fixed(self, year: int, month: int, day: int) -> int:
        return self.naw_ruz(year) + sum(self.days_in_month(year, m) for m in range(1, month)) + day - 1

    def from_fixed(self, fixed: int) -> tuple[int, int, int]:
        first, last = self.span()
        if not first <= fixed <= last:
            raise ValueError(f"the Badíʿ table knows no day {fixed}")
        year = datetime.date.fromordinal(fixed).year - 1843
        if fixed < self.naw_ruz(year):
            year -= 1
        into = fixed - self.naw_ruz(year)
        for month in range(1, 21):
            length = self.days_in_month(year, month)
            if into < length:
                return year, month, into + 1
            into -= length
        raise AssertionError("a day past its year's months")

    def month_names(self, year: int) -> list[str]:
        return [
            tr("Bahá"), tr("Jalál"), tr("Jamál"), tr("ʿAẓamat"), tr("Núr"), tr("Raḥmat"), tr("Kalimát"),
            tr("Kamál"), tr("Asmáʼ"), tr("ʿIzzat"), tr("Mashíyyat"), tr("ʿIlm"), tr("Qudrat"), tr("Qawl"),
            tr("Masáʼil"), tr("Sharaf"), tr("Sulṭán"), tr("Mulk"), tr("Ayyám-i-Há"), tr("ʿAláʼ"),
        ]

    def note(self, day: datetime.date) -> str:
        year, month, number = self.from_date(day)
        notes = [tr("Naw-Rúz")] if (month, number) == (1, 1) else []
        if year > badi_data.PUBLISHED_LAST:
            notes.append(tr("Computed: not yet published by the Baháʼí World Centre"))
        return ", ".join(notes)


class Burmese(CalendarSystem):
    """The Myanmar calendar (ME, Myanmar Era): lunisolar, its months from Tagu
    in April, a second Waso inserted in a *watat* year and a 30th day of
    Nayon in a big one.  Its rules are Yan Naing Aye's ("Modern Myanmar
    Calendrical Calculations", the ``ceMmDateTime`` library, MIT licence,
    copyright (c) 2018 Yan Naing Aye), ported here: the era's constants and
    the published exceptions, then arithmetic.  A year here runs from 1 Tagu;
    the Myanmar year number officially changes on New Year's Day after
    Thingyan, mid-April, which :meth:`note` marks.  ME 1 began in 639."""

    key = "burmese"
    SY = 1577917828.0 / 4320000.0
    LM = 1577917828.0 / 53433336.0
    MO = 1954168.050623
    #: The calendar's months in its own numbers, as each year has them: Tagu 1 ... Tabaung 12, the
    #: first Waso of a watat year 0, between Nayon and (the second) Waso.
    ORDER = (1, 2, 3, 0, 4, 5, 6, 7, 8, 9, 10, 11, 12)

    def caption(self) -> str:
        return tr("Burmese (Myanmar)")

    @staticmethod
    def _constants(year: int) -> tuple[float, float, float, int]:
        """The era's constants for *year* (``GetMyConst``): EI, WO, NM and EW."""
        if year >= 1312:
            ei, wo, nm, fme, wte = 3, -0.5, 8, {1377: 1}, {1344, 1345}
        elif year >= 1217:
            ei, wo, nm, fme, wte = 2, -1, 4, {1234: 1, 1261: -1}, {1263, 1264}
        elif year >= 1100:
            ei, wo, nm, fme, wte = 1.3, -0.85, -1, {1120: 1, 1126: -1, 1150: 1, 1172: -1, 1207: 1}, {1201, 1202}
        elif year >= 798:
            ei, wo, nm = 1.2, -1.1, -1
            fme = dict.fromkeys((813, 849, 851, 854, 927, 933, 936, 938, 949, 952, 963, 968, 1039), -1)
            wte = set()
        else:
            ei, wo, nm, wte = 1.1, -1.1, -1, set()
            fme = {205: 1, 246: 1, 471: 1, 572: -1, 651: 1, 653: 2, 656: 1, 672: 1, 729: 1, 767: -1}
        return ei, wo + fme.get(year, 0), nm, int(year in wte)

    def _watat(self, year: int) -> tuple[int, int]:
        """Whether *year* has an intercalary month, and its second Waso's full moon (``cal_watat``)."""
        ei, wo, nm, ew = self._constants(year)
        ta = (self.SY / 12 - self.LM) * (12 - nm)
        ed = math.fmod(self.SY * (year + 3739), self.LM)
        if ed < ta:
            ed += self.LM
        fm = round(self.SY * year + self.MO - ed + 4.5 * self.LM + wo)
        if ei >= 2:
            watat = int(ed >= self.LM - (self.SY / 12 - self.LM) * nm)
        else:
            watat = (year * 7 + 2) % 19 // 12
        return watat ^ ew, fm

    @functools.lru_cache(maxsize=256)
    def _year(self, year: int) -> tuple[int, int]:
        """*year*'s type (0 common, 1 little watat, 2 big watat) and its 1 Tagu as a JDN (``cal_my``)."""
        watat, fm2 = self._watat(year)
        back = 0
        while True:
            back += 1
            previous, fm1 = self._watat(year - back)
            if previous or back >= 3:
                break
        kind = (fm2 - fm1) % 354 // 31 + 1 if watat else 0
        return kind, fm1 + 354 * back - 102

    def _jdn(self, year: int, number: int, day: int) -> int:
        """``m2j``: the JDN of *day* of month *number* (the calendar's numbers) of *year*."""
        kind, tagu = self._year(year)
        b, c = kind // 2, 1 - (kind + 1) // 2
        late, number = number // 13, number % 13 + number // 13
        number += 4 - (number + 15) // 16 * 4 + (number + 12) // 16
        days = day + math.floor(29.544 * number - 29.26) - c * ((number + 11) // 16) * 30 + b * ((number + 12) // 16)
        days += late * (354 + (1 - c) * 30 + b)
        return days + tagu - 1

    def _months(self, year: int) -> tuple[int, ...]:
        return self.ORDER if self._year(year)[0] else self.ORDER[:3] + self.ORDER[4:]

    def months_in_year(self, year: int) -> int:
        return len(self._months(year))

    def _length(self, year: int, number: int) -> int:
        """``cal_mml``."""
        return 30 - number % 2 + (self._year(year)[0] // 2 if number == 3 else 0)

    def days_in_month(self, year: int, month: int) -> int:
        return self._length(year, self._months(year)[month - 1])

    def to_fixed(self, year: int, month: int, day: int) -> int:
        return self._jdn(year, self._months(year)[month - 1], 1) - ORDINAL_JDN + day - 1

    def from_fixed(self, fixed: int) -> tuple[int, int, int]:
        jdn = fixed + ORDINAL_JDN
        year = math.floor((jdn - 0.5 - self.MO) / self.SY)
        while self._year(year)[1] > jdn:
            year -= 1
        while self._year(year + 1)[1] <= jdn:
            year += 1
        for month, number in enumerate(self._months(year), 1):
            start = self._jdn(year, number, 1)
            if start <= jdn < start + self._length(year, number):
                return year, month, jdn - start + 1
        raise AssertionError("a day past its year's months")

    def years(self) -> tuple[int, int]:
        return 1, self.from_fixed(LAST)[0]

    def span(self) -> tuple[int, int]:
        return self._year(1)[1] - ORDINAL_JDN, LAST

    def month_names(self, year: int) -> list[str]:
        names = {
            1: tr("Tagu"), 2: tr("Kason"), 3: tr("Nayon"), 0: tr("First Waso"), 4: tr("Waso"), 5: tr("Wagaung"),
            6: tr("Tawthalin"), 7: tr("Thadingyut"), 8: tr("Tazaungmon"), 9: tr("Nadaw"), 10: tr("Pyatho"),
            11: tr("Tabodwe"), 12: tr("Tabaung"),
        }
        if self._year(year)[0]:
            names[4] = tr("Second Waso")
        return [names[number] for number in self._months(year)]

    def note(self, day: datetime.date) -> str:
        """Full moon and new moon (the sabbaths' phases), and Myanmar New Year's Day."""
        year, month, number = self.from_date(day)
        notes = []
        length = self.days_in_month(year, month)
        if number == 15:
            notes.append(tr("Full moon"))
        elif number == length:
            notes.append(tr("New moon"))
        jdn = day.toordinal() + ORDINAL_JDN
        for era_year in (year, year + 1):
            if jdn == round(self.SY * era_year + self.MO) + 1:
                notes.append(tr("Myanmar New Year's Day, {year} ME").format(year=era_year))
        return ", ".join(notes)


class Tibetan(CalendarSystem):
    """The Tibetan calendar of the Phugpa school (ཕུག་ལུགས), the one Tibet,
    Bhutan and the Tibetan diaspora keep: lunisolar, its days *tithis* named
    by the Moon's age, so a day number can be skipped or doubled and a leap
    month comes before the month of its number.  Pure arithmetic: Reingold
    and Dershowitz's (*Calendrical Calculations*, "The Tibetan Calendar").
    Its year is counted from 127 BC; :meth:`note` names it by element and
    animal and marks Losar, New Year's Day.  A day's place in its month is
    its column here, and :meth:`day_label` the number it is written with."""

    key = "tibetan"
    #: Its epoch, 7 December 127 BC (Gregorian), as a fixed day.
    EPOCH = _gregorian_fixed(-127, 12, 7)
    SUN = (0, 6 / 60, 10 / 60, 11 / 60)
    MOON = (0, 5 / 60, 10 / 60, 15 / 60, 19 / 60, 22 / 60, 24 / 60, 25 / 60)

    def caption(self) -> str:
        return tr("Tibetan (Phugpa)")

    @classmethod
    def _sun(cls, alpha: float) -> float:
        if alpha > 6:
            return -cls._sun(alpha - 6)
        if alpha > 3:
            return cls._sun(6 - alpha)
        if alpha == int(alpha):
            return cls.SUN[int(alpha)]
        return (alpha % 1) * cls._sun(math.ceil(alpha)) + (-alpha % 1) * cls._sun(math.floor(alpha))

    @classmethod
    def _moon(cls, alpha: float) -> float:
        if alpha > 14:
            return -cls._moon(alpha - 14)
        if alpha > 7:
            return cls._moon(14 - alpha)
        if alpha == int(alpha):
            return cls.MOON[int(alpha)]
        return (alpha % 1) * cls._moon(math.ceil(alpha)) + (-alpha % 1) * cls._moon(math.floor(alpha))

    def _fixed(self, year: int, month: int, leap_month: bool, day: int, leap_day: bool) -> int:
        """``fixed-from-tibetan``."""
        months = math.floor(804 / 65 * (year - 1) + 67 / 65 * month + (-1 if leap_month else 0) + 64 / 65)
        days = 30 * months + day
        mean = days * 11135 / 11312 - 30 + (0 if leap_day else -1) + 1071 / 1616
        solar = (days * 13 / 4824 + 2117 / 4824) % 1
        lunar = (days * 3781 / 105840 + 2837 / 15120) % 1
        return math.floor(self.EPOCH + mean - self._sun(12 * solar) + self._moon(28 * lunar))

    def _date(self, fixed: int) -> tuple[int, int, bool, int, bool]:
        """``tibetan-from-fixed``: year, month, leap month, day, leap day."""
        year = math.ceil((fixed - self.EPOCH) / (365 + 4975 / 18382)) - 1
        while self._fixed(year + 1, 1, False, 1, False) <= fixed:
            year += 1
        while self._fixed(year, 1, False, 1, False) > fixed:
            year -= 1
        month0 = 1
        while month0 < 12 and self._fixed(year, month0 + 1, False, 1, False) <= fixed:
            month0 += 1
        estimate = fixed - self._fixed(year, month0, False, 1, False)
        day0 = estimate - 2
        while self._fixed(year, month0, False, day0 + 1, False) <= fixed:
            day0 += 1
        leap_month = day0 > 30
        day = (day0 - 1) % 30 + 1
        # A leap month comes before the month of its number, so past day 30 of month0 is month0 + 1's.
        month = ((month0 - 1 if day > day0 else month0 + 1 if leap_month else month0) - 1) % 12 + 1
        if day > day0 and month0 == 1:
            year -= 1
        elif leap_month and month0 == 12:
            year += 1
        leap_day = fixed == self._fixed(year, month, leap_month, day, True)
        return year, month, leap_month, day, leap_day

    def _leap(self, year: int, month: int) -> bool:
        """Whether *year* has a leap month numbered *month* (``tibetan-leap-month?``)."""
        return self._date(self._fixed(year, month, True, 2, False))[1:3] == (month, True)

    @functools.lru_cache(maxsize=128)
    def _months(self, year: int) -> tuple[tuple[int, bool, int], ...]:
        """*year*'s months in order, each ``(number, leap, first day)``, the day after its last
        month closing it as ``(0, False, day)``."""
        months = []
        for number in range(1, 13):
            for leap in ((True, False) if self._leap(year, number) else (False,)):
                guess = self._fixed(year, number, leap, 1, False)
                start = next(day for day in range(guess - 2, guess + 3)
                             if self._date(day)[:3] == (year, number, leap))
                months.append((number, leap, start))
        months.append((0, False, self._months_start(year + 1)))
        return tuple(months)

    def _months_start(self, year: int) -> int:
        guess = self._fixed(year, 1, self._leap(year, 1), 1, False)
        return next(day for day in range(guess - 2, guess + 3) if self._date(day)[0] == year)

    def months_in_year(self, year: int) -> int:
        return len(self._months(year)) - 1

    def days_in_month(self, year: int, month: int) -> int:
        months = self._months(year)
        return months[month][2] - months[month - 1][2]

    def to_fixed(self, year: int, month: int, day: int) -> int:
        return self._months(year)[month - 1][2] + day - 1

    def from_fixed(self, fixed: int) -> tuple[int, int, int]:
        year = self._date(fixed)[0]
        months = self._months(year)
        if fixed < months[0][2]:
            year -= 1
            months = self._months(year)
        for index in range(len(months) - 1):
            if months[index][2] <= fixed < months[index + 1][2]:
                return year, index + 1, fixed - months[index][2] + 1
        raise AssertionError("a day past its year's months")

    def day_label(self, day: datetime.date) -> int:
        return self._date(day.toordinal())[3]

    def years(self) -> tuple[int, int]:
        return 1, self.from_fixed(LAST - 400)[0]

    def span(self) -> tuple[int, int]:
        return self._months_start(1), LAST - 400

    def month_names(self, year: int) -> list[str]:
        regular = [
            tr("Month 1"), tr("Month 2"), tr("Month 3"), tr("Month 4"), tr("Month 5"), tr("Month 6"),
            tr("Month 7"), tr("Month 8"), tr("Month 9"), tr("Month 10"), tr("Month 11"), tr("Month 12"),
        ]
        return [tr("Leap {number}").format(number=number, month=regular[number - 1]) if leap else regular[number - 1]
                for number, leap, _ in self._months(year)[:-1]]

    def note(self, day: datetime.date) -> str:
        """The year by element and animal, Losar, and a doubled or skipped day number."""
        year, month, place = self.from_date(day)
        gregorian = year - 127
        elements = [tr("Wood"), tr("Fire"), tr("Earth"), tr("Iron"), tr("Water")]
        animals = SYSTEMS["chinese"].animals()
        notes = []
        if (month, place) == (1, 1):
            # The year's first day -- of a doubled first month's first, the leap one, as in 2019.
            notes.append(tr("Losar"))
        _, _, _, number, leap_day = self._date(day.toordinal())
        if leap_day:
            notes.append(tr("Doubled day"))
        following = self._date(day.toordinal() + 1)[3]
        if following not in (number, number % 30 + 1):
            notes.append(tr("Day {number} is skipped").format(number=number % 30 + 1))
        notes.append(tr("{element} {animal} year").format(
            element=elements[(gregorian - 4) % 10 // 2], animal=animals[(gregorian - 4) % 12]))
        return ", ".join(notes)


class Afghan(Persian):
    """Afghanistan's Solar Hijri calendar: the Persian calendar's year and days
    (here its 33-year rule, Iran's equinox reckoning, which Afghanistan's
    follows but for a day now and then), with the months named after the
    signs of the zodiac (Hamal, Sawr, Jawza ...).  Afghanistan's official
    calendar since 1957; since 2021 its government keeps the lunar Hijri
    for its own business, the solar one still the calendar of daily life."""

    key = "afghan"

    def caption(self) -> str:
        return tr("A~f~ghan Solar Hijri")

    def month_names(self, year: int) -> list[str]:
        return [
            tr("Hamal"), tr("Sawr"), tr("Jawza"), tr("Saratan"), tr("Asad"), tr("Sonbola"),
            tr("Mizan"), tr("Aqrab"), tr("Qaws"), tr("Jadi"), tr("Dalw"), tr("Hut"),
        ]


class Chhankitek(CalendarSystem):
    """The lunisolar calendar of Cambodia, Thailand and Laos (Khmer ចន្ទគតិ,
    Chhankitek): months of 29 and 30 days by turns, a second Asadh in a
    leap-month (adhikamāsa) year and a 30-day Jesth in a leap-day one, both
    decided by the Sūrya Siddhānta's arithmetic as the Khmer almanac keeps
    it.  Ported from ThyrithSor's ``momentkh`` (MIT licence, copyright (c)
    2018 ThyrithSor): the year's quantities (*aharkun*, *avoman*, *bodithey*),
    then the months stepped from 1 Boss, 1 January 1900.  Thailand's and
    Laos's almanacs keep the same rules and part from Cambodia's only in an
    odd year's leap.  A year here runs from 1 Pisakh, numbered by the
    Buddhist Era it enters at Visakha Bochea, mid-Pisakh; :meth:`note` marks
    the full and new moons and the three great Buddhist holy days."""

    key = "chhankitek"
    #: The months' indices, as momentkh numbers them.
    MIGASIR, BOSS, MEAK, PHALKUN, CHEIT, PISAKH, JESTH, ASADH, SRAP, PHATRABOT, ASSOCH, KADEUK = range(12)
    PATHAMASADH, TUTIYASADH = 12, 13
    #: The months are stepped from this day, 1 Boss.
    EPOCH = _gregorian_fixed(1900, 1, 1)
    #: And to this one.
    END = _gregorian_fixed(2101, 1, 1)

    def caption(self) -> str:
        return tr("Khmer, Thai, La~o~ lunar")

    # -- momentkh's year quantities --------------------------------------------------------

    @staticmethod
    def _aharkun(be: int) -> int:
        return (be * 292207 + 499) // 800 + 4

    def _avoman(self, be: int) -> int:
        return (self._aharkun(be) * 11 + 25) % 692

    def _bodithey(self, be: int) -> int:
        aharkun = self._aharkun(be)
        return ((aharkun * 11 + 25) // 692 + aharkun + 29) % 30

    @staticmethod
    def _solar_leap(be: int) -> bool:
        return 800 - (be * 292207 + 499) % 800 <= 207

    def _leap_day_by_calculation(self, be: int) -> bool:
        avoman = self._avoman(be)
        if avoman == 0 and self._avoman(be - 1) == 137:
            return True
        if self._solar_leap(be):
            return avoman < 127
        if avoman == 137 and self._avoman(be + 1) == 0:
            return False
        return avoman < 138

    def _leap_month(self, be: int) -> bool:
        bodithey, following = self._bodithey(be), self._bodithey(be + 1)
        if bodithey == 25 and following == 5:
            return False
        return (bodithey == 24 and following == 6) or bodithey >= 25 or bodithey < 6

    @functools.lru_cache(maxsize=512)
    def _leap_type(self, be: int) -> int:
        """0 a common year, 1 a leap month's, 2 a leap day's (``getLeapType``)."""
        if self._leap_month(be):
            return 1
        if self._leap_day_by_calculation(be):
            return 2
        if self._leap_month(be - 1):
            previous = be - 1
            while True:
                if self._leap_day_by_calculation(previous):
                    return 2
                previous -= 1
                if not self._leap_month(previous):
                    return 0
        return 0

    def _length(self, index: int, be: int) -> int:
        leap = self._leap_type(be)
        if index == self.JESTH and leap == 2:
            return 30
        if index in (self.PATHAMASADH, self.TUTIYASADH):
            return 30 if leap == 1 else 0
        return 29 if index % 2 == 0 else 30

    def _next(self, index: int, be: int) -> int:
        if index == self.JESTH and self._leap_type(be) == 1:
            return self.PATHAMASADH
        if index == self.KADEUK:
            return self.MIGASIR
        if index == self.PATHAMASADH:
            return self.TUTIYASADH
        if index == self.TUTIYASADH:
            return self.SRAP
        return index + 1

    @staticmethod
    def _be(day: int) -> int:
        """``getMaybeBEYear``: the Buddhist Era of a day, by its Gregorian month alone."""
        date = datetime.date.fromordinal(day)
        return date.year + (543 if date.month <= 4 else 544)

    @functools.cached_property
    def _months(self) -> list[tuple[int, int]]:
        """Every month ``(first day, index)`` from the epoch to :data:`END`, stepped as momentkh steps them."""
        months, day, index = [], self.EPOCH, self.BOSS
        while day < self.END:
            months.append((day, index))
            be = self._be(day)
            day, index = day + self._length(index, be), self._next(index, be)
        months.append((day, index))
        return months

    @functools.cached_property
    def _years(self) -> dict[int, list[tuple[int, int]]]:
        """Each Buddhist year's months, from its Pisakh, with the next year's first day closing it."""
        starts = [i for i, (_, index) in enumerate(self._months) if index == self.PISAKH]
        years = {}
        for here, there in zip(starts, starts[1:]):
            first = self._months[here][0]
            years[datetime.date.fromordinal(first).year + 544] = self._months[here:there + 1]
        return years

    # -- the calendar --------------------------------------------------------------------

    def _year(self, year: int) -> list[tuple[int, int]]:
        if year not in self._years:
            raise ValueError(f"the Chhankitek table has no year {year}")
        return self._years[year]

    def span(self) -> tuple[int, int]:
        first, last = min(self._years), max(self._years)
        return self._years[first][0][0], self._years[last][-1][0] - 1

    def years(self) -> tuple[int, int]:
        return min(self._years), max(self._years)

    def months_in_year(self, year: int) -> int:
        return len(self._year(year)) - 1

    def days_in_month(self, year: int, month: int) -> int:
        months = self._year(year)
        return months[month][0] - months[month - 1][0]

    def to_fixed(self, year: int, month: int, day: int) -> int:
        return self._year(year)[month - 1][0] + day - 1

    def from_fixed(self, fixed: int) -> tuple[int, int, int]:
        first, last = self.span()
        if not first <= fixed <= last:
            raise ValueError(f"the Chhankitek table knows no day {fixed}")
        year = datetime.date.fromordinal(fixed).year + 544
        if fixed < self._years[year][0][0] if year in self._years else True:
            year -= 1
        months = self._years[year]
        for month in range(len(months) - 1):
            if months[month][0] <= fixed < months[month + 1][0]:
                return year, month + 1, fixed - months[month][0] + 1
        raise AssertionError("a day past its year's months")

    def index(self, year: int, month: int) -> int:
        """Month *month* of *year* (in year order) as momentkh numbers it."""
        return self._year(year)[month - 1][1]

    def month_names(self, year: int) -> list[str]:
        names = {
            self.PISAKH: tr("Pisakh"), self.JESTH: tr("Jesth"), self.ASADH: tr("Asadh"),
            self.PATHAMASADH: tr("Pathamasadh"), self.TUTIYASADH: tr("Tutiyasadh"), self.SRAP: tr("Srap"),
            self.PHATRABOT: tr("Phatrabot"), self.ASSOCH: tr("Assoch"), self.KADEUK: tr("Kadeuk"),
            self.MIGASIR: tr("Migasir"), self.BOSS: tr("Boss"), self.MEAK: tr("Meak"), self.PHALKUN: tr("Phalkun"),
            self.CHEIT: tr("Cheit"),
        }
        return [names[index] for _, index in self._year(year)[:-1]]

    def note(self, day: datetime.date) -> str:
        """Full and new moons, and the holy days.  In a year whose Asadh is
        doubled (2023, 2026), Thailand and Laos keep Magha Puja and Vesak a
        month later than Cambodia -- at the full moons of Phalkun and Jesth
        -- so both are named."""
        year, month, number = self.from_date(day)
        index = self.index(year, month)
        notes = []
        if number == 15:
            notes.append(tr("Full moon"))
            leap = self._leap_type(day.year + 544) == 1
            if index in (self.ASADH, self.TUTIYASADH):
                notes.append(tr("Asalha Puja"))
            elif not leap and index == self.MEAK:
                notes.append(tr("Magha Puja"))
            elif not leap and index == self.PISAKH:
                notes.append(tr("Vesak"))
            elif leap and index == self.MEAK:
                notes.append(tr("Magha Puja (Cambodia)"))
            elif leap and index == self.PHALKUN:
                notes.append(tr("Magha Puja (Thailand, Laos)"))
            elif leap and index == self.PISAKH:
                notes.append(tr("Vesak (Cambodia)"))
            elif leap and index == self.JESTH:
                notes.append(tr("Vesak (Thailand, Laos)"))
        elif number == self.days_in_month(year, month):
            notes.append(tr("New moon"))
        return ", ".join(notes)


#: Every calendar by its key, in the order a menu lists them.
SYSTEMS: dict[str, CalendarSystem] = {
    system.key: system
    for system in (Gregorian(), Julian(), Hebrew(), Islamic(), UmmAlQura(), Diyanet(), MabimsIndonesia(),
                   MabimsMalaysia(), Chinese(), Korean(), Vietnamese(),
                   Japanese(), Thai(), Minguo(), Burmese(), Chhankitek(), Tibetan(), Persian(), Afghan(), Indian(), Bengali(), Nepali(), Badi(), Ethiopian(),
                   Coptic())
}

#: The Gregorian, which a view is in unless told otherwise.
GREGORIAN = SYSTEMS["gregorian"]


def system(key: str) -> CalendarSystem:
    """The calendar named *key*, the Gregorian for one not known."""
    return SYSTEMS.get(key, GREGORIAN)


__all__ = ["GREGORIAN", "SYSTEMS", "CalendarSystem", "easter", "gregorian_month_names", "orthodox_easter",
           "plain", "system"]

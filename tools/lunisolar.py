#!/usr/bin/env python3
"""Compute the Korean and Vietnamese calendars, ``navml/korean_data.py`` and ``navml/vietnamese_data.py``.

    ./venv/bin/python tools/lunisolar.py             # verify the method, then write both
    ./venv/bin/python tools/lunisolar.py --verify    # only compare Beijing's months with the HKO table
    ./venv/bin/python tools/lunisolar.py --check     # exit 1 when a module is inconsistent

Korea's and Vietnam's lunisolar calendars are China's rules reckoned in their
own time: a month begins on the day of the new moon, the month holding the
winter solstice is the 11th, and in a year of thirteen months from solstice to
solstice the first with no major solar term (中氣, the Sun's longitude a
multiple of 30°) is the leap one.  A new moon or a term an hour from midnight
falls on another day in Seoul or Hanoi than in Beijing, so their calendars
part from China's a few times a century -- Vietnam's Tết of 1985 a month
before China's New Year, Korea's Seollal of 1997 a day after it.

Neither publishes a table the way the Hong Kong Observatory does, so these are
computed: the new moons by Meeus' series (*Astronomical Algorithms*, ch. 49,
good to seconds), the Sun's apparent longitude by his low-precision theory
(ch. 25, good to about 0.01°, a quarter of an hour), and ΔT by Espenak and
Meeus' polynomials.  **The method is checked first**: reckoned in Beijing's
time it must give the Hong Kong Observatory's months (``navml/chinese_data.py``)
for every year; the tool refuses to write anything otherwise.  An event within
:data:`MARGIN` of midnight in the time it is reckoned in is listed, since the
solar theory's error could move it to the next day.  Against the table the
check finds three years apart, 1906, 1917 and 1922, each with an event within
ten minutes of Beijing's midnight -- below the theory's precision, and before
1929 China's almanacs were computed by older methods besides.

The time each is reckoned in:

- **China**, for the check: Beijing's mean time (UTC+7:45:40) until 1929,
  UTC+8 since.
- **Vietnam**: China's, as the Chinese calendar it kept, until 1968, when the North's calendar moved to UTC+7 (the decree of 8 August 1967),
  which Vietnam has kept since.
- **Korea**: its standard time of the day -- UTC+8:30 from 1908 to 1911 and
  from 21 March 1954 to 9 August 1961, UTC+9 otherwise, and Seoul's mean
  time (UTC+8:28) before 1908.

``--check`` needs no network or computing: it says whether each module's years
follow one another, as ``tools/chinese_calendar.py --check`` does.
"""

from __future__ import annotations

import argparse
import datetime
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

#: Lunar years written: the Chinese table's.
FIRST_YEAR, LAST_YEAR = 1901, 2099
#: How near local midnight an event must be, in days, to be listed as uncertain:
#: the three years the check finds apart from the HKO table each had one within
#: ten minutes.
MARGIN = 10 / 1440
#: Vietnam's years before it are China's, the HKO table's own: its calendar
#: was until 1968, which 1967's last month already runs into.
VIETNAM_OWN = 1967
#: A Julian Day Number less this is a ``date``'s ordinal.
ORDINAL = 1_721_425


def d(degrees: float) -> float:
    return math.radians(degrees % 360)


# -- time ---------------------------------------------------------------------


def delta_t(year: float) -> float:
    """TT - UT in seconds (Espenak and Meeus, 1900-2150)."""
    if year < 1920:
        t = year - 1900
        return -2.79 + 1.494119 * t - 0.0598939 * t ** 2 + 0.0061966 * t ** 3 - 0.000197 * t ** 4
    if year < 1941:
        t = year - 1920
        return 21.20 + 0.84493 * t - 0.076100 * t ** 2 + 0.0020936 * t ** 3
    if year < 1961:
        t = year - 1950
        return 29.07 + 0.407 * t - t ** 2 / 233 + t ** 3 / 2547
    if year < 1986:
        t = year - 1975
        return 45.45 + 1.067 * t - t ** 2 / 260 - t ** 3 / 718
    if year < 2005:
        t = year - 2000
        return (63.86 + 0.3345 * t - 0.060374 * t ** 2 + 0.0017275 * t ** 3 + 0.000651814 * t ** 4
                + 0.00002373599 * t ** 5)
    if year < 2050:
        t = year - 2000
        return 62.92 + 0.32217 * t + 0.005589 * t ** 2
    return -20 + 32 * ((year - 1820) / 100) ** 2 - 0.5628 * (2150 - year)


def ut(jde: float) -> float:
    """A Julian Ephemeris Day as a Julian Day in UT."""
    year = 2000 + (jde - 2451545.0) / 365.25
    return jde - delta_t(year) / 86400


def local(jd_ut: float, hours: float) -> tuple[int, float]:
    """The ``date`` ordinal a UT instant falls on at UTC+*hours*, and how
    far it is from the nearer midnight, in days."""
    civil = jd_ut + 0.5 + hours / 24
    day = math.floor(civil)
    into = civil - day
    return day - ORDINAL, min(into, 1 - into)


# -- the moon ----------------------------------------------------------------


def new_moon(k: int) -> float:
    """The true new moon *k* lunations after 6 January 2000's, as a JDE (Meeus 49)."""
    T = k / 1236.85
    jde = (2451550.09766 + 29.530588861 * k + 0.00015437 * T ** 2 - 0.000000150 * T ** 3
           + 0.00000000073 * T ** 4)
    E = 1 - 0.002516 * T - 0.0000074 * T ** 2
    M = d(2.5534 + 29.10535670 * k - 0.0000014 * T ** 2 - 0.00000011 * T ** 3)
    Mp = d(201.5643 + 385.81693528 * k + 0.0107582 * T ** 2 + 0.00001238 * T ** 3 - 0.000000058 * T ** 4)
    F = d(160.7108 + 390.67050284 * k - 0.0016118 * T ** 2 - 0.00000227 * T ** 3 + 0.000000011 * T ** 4)
    O = d(124.7746 - 1.56375588 * k + 0.0020672 * T ** 2 + 0.00000215 * T ** 3)
    s = math.sin
    jde += (-0.40720 * s(Mp) + 0.17241 * E * s(M) + 0.01608 * s(2 * Mp) + 0.01039 * s(2 * F)
            + 0.00739 * E * s(Mp - M) - 0.00514 * E * s(Mp + M) + 0.00208 * E * E * s(2 * M)
            - 0.00111 * s(Mp - 2 * F) - 0.00057 * s(Mp + 2 * F) + 0.00056 * E * s(2 * Mp + M)
            - 0.00042 * s(3 * Mp) + 0.00042 * E * s(M + 2 * F) + 0.00038 * E * s(M - 2 * F)
            - 0.00024 * E * s(2 * Mp - M) - 0.00017 * s(O) - 0.00007 * s(Mp + 2 * M)
            + 0.00004 * s(2 * Mp - 2 * F) + 0.00004 * s(3 * M) + 0.00003 * s(Mp + M - 2 * F)
            + 0.00003 * s(2 * Mp + 2 * F) - 0.00003 * s(Mp + M + 2 * F) + 0.00003 * s(Mp - M + 2 * F)
            - 0.00002 * s(Mp - M - 2 * F) - 0.00002 * s(3 * Mp + M) + 0.00002 * s(4 * Mp))
    planets = (
        (299.77, 0.107408, 0.000325), (251.88, 0.016321, 0.000165), (251.83, 26.651886, 0.000164),
        (349.42, 36.412478, 0.000126), (84.66, 18.206239, 0.000110), (141.74, 53.303771, 0.000062),
        (207.14, 2.453732, 0.000060), (154.84, 7.306860, 0.000056), (34.52, 27.261239, 0.000047),
        (207.19, 0.121824, 0.000042), (291.34, 1.844379, 0.000040), (161.72, 24.198154, 0.000037),
        (239.56, 25.513099, 0.000035), (331.55, 3.592518, 0.000023),
    )
    for index, (base, rate, amplitude) in enumerate(planets):
        angle = base + rate * k - (0.009173 * T ** 2 if index == 0 else 0)
        jde += amplitude * s(d(angle))
    return jde


# -- the sun -----------------------------------------------------------------


def solar_longitude(jde: float) -> float:
    """The Sun's apparent longitude in degrees (Meeus 25, low precision)."""
    T = (jde - 2451545.0) / 36525
    L0 = 280.46646 + 36000.76983 * T + 0.0003032 * T ** 2
    M = d(357.52911 + 35999.05029 * T - 0.0001537 * T ** 2)
    C = ((1.914602 - 0.004817 * T - 0.000014 * T ** 2) * math.sin(M)
         + (0.019993 - 0.000101 * T) * math.sin(2 * M) + 0.000289 * math.sin(3 * M))
    omega = d(125.04 - 1934.136 * T)
    return (L0 + C - 0.00569 - 0.00478 * math.sin(omega)) % 360


def solar_term(jde: float, target: float) -> float:
    """The JDE near *jde* when the Sun's apparent longitude is *target*."""
    for _ in range(20):
        error = (target - solar_longitude(jde) + 180) % 360 - 180
        jde += error * 365.2422 / 360
        if abs(error) < 1e-7:
            break
    return jde


# -- the calendar --------------------------------------------------------------


class Reckoning:
    """A lunisolar calendar reckoned in a time that may change: *hours(jd_ut)*
    is the offset from UTC in force at that instant."""

    def __init__(self, hours) -> None:
        self.hours = hours
        self.uncertain: list[tuple[int, str]] = []

    def day(self, jde: float, what: str) -> int:
        instant = ut(jde)
        ordinal, margin = local(instant, self.hours(instant))
        if margin < MARGIN:
            self.uncertain.append((ordinal, f"{what} {datetime.date.fromordinal(ordinal)}: "
                                            f"{margin * 1440:.0f} minutes from midnight"))
        return ordinal

    def new_moons(self, first: int, last: int) -> list[int]:
        """The days new moons begin on, from the one on or before ordinal *first* to past *last*."""
        k = math.floor((first + ORDINAL - 2451550.09766) / 29.530588861) - 1
        days = []
        while True:
            day = self.day(new_moon(k), "new moon")
            if day > last and days and days[-1] > last:
                break
            days.append(day)
            k += 1
        while len(days) > 1 and days[1] <= first:
            days.pop(0)
        return days

    def major_term_days(self, first: int, last: int) -> set[int]:
        """The days a major solar term falls on, between ordinals *first* and *last*."""
        days = set()
        jde = first + ORDINAL - 20.0
        target = math.floor(solar_longitude(jde) / 30) * 30 + 30
        while True:
            jde = solar_term(jde + 15, target % 360)
            day = self.day(jde, f"term {target % 360:.0f}°")
            if day > last:
                return days
            days.add(day)
            target += 30

    def solstice(self, year: int) -> int:
        """The day of the December solstice of Gregorian *year*."""
        guess = datetime.date(year, 12, 21).toordinal() + ORDINAL
        return self.day(solar_term(guess, 270.0), "solstice")

    def months(self, first_year: int, last_year: int) -> list[tuple[int, int, bool]]:
        """Every month ``(first day, number, leap)`` from the 11th month of
        *first_year* - 1 to the 11th of *last_year* + 1."""
        out: list[tuple[int, int, bool]] = []
        for year in range(first_year - 1, last_year + 2):
            s1, s2 = self.solstice(year), self.solstice(year + 1)
            moons = self.new_moons(s1, s2)
            # The month holding each solstice; the sui runs from one to the other.
            m11 = max(day for day in moons if day <= s1)
            m11_next = max(day for day in moons if day <= s2)
            sui = [day for day in moons if m11 <= day <= m11_next]
            starts, after = sui[:-1], sui[1:]
            terms = self.major_term_days(m11, m11_next)
            leap_index = None
            if len(starts) == 13:
                for index in range(1, 13):
                    if not any(starts[index] <= term < after[index] for term in terms):
                        leap_index = index
                        break
            number = 11
            for index, start in enumerate(starts):
                if index == leap_index:
                    out.append((start, number, True))
                    continue
                if index:
                    number = number % 12 + 1
                out.append((start, number, False))
        return out


def years(months: list[tuple[int, int, bool]], first_year: int, last_year: int) -> list[tuple[int, int, int, int]]:
    """``(year, first day, leap month, length bits)`` per lunar year, as ``tools/chinese_calendar.py`` writes them."""
    found = []
    for index, (start, number, leap) in enumerate(months):
        if number != 1 or leap:
            continue
        year = datetime.date.fromordinal(start).year
        if not first_year <= year <= last_year:
            continue
        lengths, leap_month, j = [], 0, index
        while True:
            begin, num, is_leap = months[j]
            end = months[j + 1][0]
            if j > index and num == 1 and not is_leap:
                break
            lengths.append(end - begin)
            if is_leap:
                leap_month = num
            j += 1
        found.append((year, start, leap_month, sum(1 << i for i, n in enumerate(lengths) if n == 30)))
    return found


def chinese_years() -> list[tuple[int, int, int, int]]:
    from navml import chinese_data

    return [(chinese_data.FIRST_YEAR + i, start, leap, bits) for i, (start, leap, bits) in enumerate(chinese_data.YEARS)]


def _since(day: datetime.date) -> float:
    return day.toordinal() + ORDINAL - 0.5


def beijing(jd_ut: float) -> float:
    """China's: Beijing's mean time (116°25' E, UTC+7:45:40) until 1929, the
    120th meridian's (UTC+8) since -- Reingold and Dershowitz's rule."""
    return 1397 / 180 if jd_ut < _since(datetime.date(1929, 1, 1)) else 8.0


def vietnam(jd_ut: float) -> float:
    return beijing(jd_ut) if jd_ut < _since(datetime.date(1968, 1, 1)) else 7.0


KOREA = (
    (datetime.date(1908, 4, 1), 8.5),
    (datetime.date(1912, 1, 1), 9.0),
    (datetime.date(1954, 3, 21), 8.5),
    (datetime.date(1961, 8, 10), 9.0),
)


def korea(jd_ut: float) -> float:
    hours = 8 + 28 / 60
    for since, offset in KOREA:
        if jd_ut >= _since(since):
            hours = offset
    return hours


HEADER = '''# navml: generated by tools/lunisolar.py; do not edit.
"""{title}'s lunar years {first} to {last}, computed: {how}

``YEARS[n]`` is lunar year ``FIRST_YEAR + n``: the ordinal of its first day
(``datetime.date.toordinal()``), its leap month's number (0 if none), and its
months' lengths in year order as bits, the first month the lowest, a set bit
30 days and a clear one 29.
"""

FIRST_YEAR = {first}

YEARS: tuple[tuple[int, int, int], ...] = (
'''

MODULES = {
    "korean": ("Korea", korea, "Korea's standard time of each period (UTC+9; UTC+8:30 in 1908-1911 and "
               "1954-1961; Seoul's mean time before)."),
    "vietnamese": ("Vietnam", vietnam, "the Chinese calendar (the HKO table's years) until 1966, then\n"
                   "UTC+7, Vietnam's since 1968."),
}


def module_text(title: str, how: str, table: list[tuple[int, int, int, int]]) -> str:
    rows = "".join(f"    ({first}, {leap}, 0x{bits:04x}),  # {year}\n" for year, first, leap, bits in table)
    return HEADER.format(title=title, first=table[0][0], last=table[-1][0], how=how) + rows + ")\n"


def compute(hours) -> tuple[list[tuple[int, int, int, int]], list[tuple[int, str]]]:
    reckoning = Reckoning(hours)
    table = years(reckoning.months(FIRST_YEAR, LAST_YEAR), FIRST_YEAR, LAST_YEAR)
    return table, reckoning.uncertain


def near(table: list[tuple[int, int, int, int]], year: int, uncertain: list[tuple[int, str]]) -> list[str]:
    """The uncertain events from the month before lunar *year* to its end."""
    starts = {y: first for y, first, _, _ in table}
    begin, end = starts[year] - 31, starts.get(year + 1, starts[year] + 385)
    return [text for day, text in uncertain if begin <= day < end]


def verify() -> bool:
    """Whether Beijing's months, computed, are the Hong Kong Observatory's in
    every year but those where an event falls too near midnight to tell."""
    computed, uncertain = compute(beijing)
    published = {year: rest for year, *rest in chinese_years()}
    differ = [year for year, *rest in computed if published.get(year) != rest]
    unexplained = [year for year in differ if not near(computed, year, uncertain)]
    print(f"Beijing computed against the HKO table: {len(computed)} years, {len(differ)} differ")
    for year in differ:
        print(f"  {year}: {'; '.join(near(computed, year, uncertain)) or 'NO EVENT NEAR MIDNIGHT'}")
    return not unexplained


def check(name: str) -> int:
    path = ROOT / "navml" / f"{name}_data.py"
    namespace: dict = {}
    exec(path.read_text(encoding="utf-8"), namespace)
    first, table = namespace["FIRST_YEAR"], namespace["YEARS"]
    problems = []
    for index, (start, leap, bits) in enumerate(table):
        months = 13 if leap else 12
        length = sum(30 if bits >> i & 1 else 29 for i in range(months))
        if bits >> months or not 0 <= leap <= 12:
            problems.append(f"{first + index}: bad months")
        if index + 1 < len(table) and table[index + 1][0] - start != length:
            problems.append(f"{first + index}: its months are {length} days, the year {table[index + 1][0] - start}")
    for problem in problems:
        print(f"{path}: {problem}", file=sys.stderr)
    return 1 if problems else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="exit 1 when a module is inconsistent")
    parser.add_argument("--verify", action="store_true", help="only compare Beijing's months with HKO's")
    args = parser.parse_args()
    if args.check:
        return max(check(name) for name in MODULES)
    if not verify():
        print("the method does not give the HKO table; nothing written", file=sys.stderr)
        return 1
    if args.verify:
        return 0
    for name, (title, hours, how) in MODULES.items():
        table, uncertain = compute(hours)
        if name == "vietnamese":
            table = [row for row in chinese_years() if row[0] < VIETNAM_OWN] + \
                    [row for row in table if row[0] >= VIETNAM_OWN]
            first_own = next(first for year, first, _, _ in table if year == VIETNAM_OWN)
            uncertain = [(day, text) for day, text in uncertain if day >= first_own - 31]
        (ROOT / "navml" / f"{name}_data.py").write_text(module_text(title, how, table), encoding="utf-8")
        china = {year: rest for year, *rest in chinese_years()}
        apart = [year for year, *rest in table if china.get(year) != rest]
        print(f"wrote navml/{name}_data.py: {len(table)} years, {len(apart)} not China's: {apart}")
        print(f"  {len(dict(uncertain))} events within {MARGIN * 1440:.0f} minutes of midnight, "
              "where a published calendar could differ by a day:")
        for _, text in sorted(dict(uncertain).items()):
            print(f"    {text}")
    return max(check(name) for name in MODULES)


if __name__ == "__main__":
    sys.exit(main())

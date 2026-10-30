#!/usr/bin/env python3
"""Write the Badíʿ (Baháʼí) calendar's Naw-Rúz days, ``navml/badi_data.py``.

    ./venv/bin/python tools/badi.py           # verify the method, then write it
    ./venv/bin/python tools/badi.py --check   # exit 1 when it is inconsistent

The Badíʿ year is nineteen months of nineteen days and the days of
Ayyám-i-Há before the last, as many as reach the next Naw-Rúz -- so the
calendar is its Naw-Rúz days and arithmetic.  Until 171 BE Naw-Rúz was 21
March in the West.  Since 172 BE (2015) it is, by the Universal House of
Justice's message of 10 July 2014, "the day that the sun entereth the sign of
Aries ... even should this occur no more than one minute before sunset", as
determined at Ṭihrán: the day, from sunset to sunset, that holds the March
equinox there, written as the Gregorian day that ends it.

The World Centre published those days for 172 to 221 BE (*Badíʿ dates 172 to
221 BE*, prepared with HM Nautical Almanac Office's data; :data:`OFFICIAL`,
transcribed from it, its Ayyám-i-Há column agreeing), which are written as
published.  The years after, to 257 BE (2100), are computed -- the equinox by
Meeus' series (*Astronomical Algorithms*, ch. 27, good to a minute), sunset at
Ṭihrán by NOAA's algorithm (the Sun's centre 0.833° below the horizon, good to
a minute), ΔT as ``tools/lunisolar.py`` takes it -- and the method is checked
first: it must give every published year but one whose equinox is within
:data:`MARGIN` of sunset, where its minute's precision cannot tell.  It gives
49 of the 50; the 50th is 2026 (183 BE), the equinox half a minute after
sunset by the almanac and half a minute before by this.  A computed year
whose equinox is within :data:`MARGIN` of sunset is listed.

``--check`` needs no network or computing: it says whether every year is
365 or 366 days.
"""

from __future__ import annotations

import argparse
import datetime
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

from lunisolar import delta_t  # noqa: E402

MODULE = ROOT / "navml" / "badi_data.py"

#: Naw-Rúz, the day of March, 172 to 221 BE, as the World Centre's table gives it.
OFFICIAL = dict(zip(range(172, 222), (
    21, 20, 20, 21, 21, 20, 20, 21, 21, 20,   # 172-181
    20, 21, 21, 20, 20, 20, 21, 20, 20, 20,   # 182-191
    21, 20, 20, 20, 21, 20, 20, 20, 21, 20,   # 192-201
    20, 20, 21, 20, 20, 20, 21, 20, 20, 20,   # 202-211
    21, 20, 20, 20, 20, 20, 20, 20, 20, 20,   # 212-221
)))
#: The first year by the equinox, and the last written.
FIRST_ASTRONOMICAL, LAST_YEAR = 172, 257
#: Ṭihrán (Azadi Tower, WGS 84), and Iran's time.
LATITUDE, LONGITUDE, HOURS = 35.6997, 51.3381, 3.5
#: How near sunset an equinox is too near for this to tell, in days.
MARGIN = 1 / 1440


def gregorian_year(year: int) -> int:
    """The Gregorian year Naw-Rúz of Badíʿ *year* falls in."""
    return year + 1843


def march_equinox(year: int) -> float:
    """The March equinox of Gregorian *year* (2000-3000) as a JDE (Meeus 27)."""
    Y = (year - 2000) / 1000
    jde0 = 2451623.80984 + 365242.37404 * Y + 0.05169 * Y ** 2 - 0.00411 * Y ** 3 - 0.00057 * Y ** 4
    T = (jde0 - 2451545.0) / 36525
    W = math.radians(35999.373 * T - 2.47)
    dlambda = 1 + 0.0334 * math.cos(W) + 0.0007 * math.cos(2 * W)
    terms = (
        (485, 324.96, 1934.136), (203, 337.23, 32964.467), (199, 342.08, 20.186), (182, 27.85, 445267.112),
        (156, 73.14, 45036.886), (136, 171.52, 22518.443), (77, 222.54, 65928.934), (74, 296.72, 3034.906),
        (70, 243.58, 9037.513), (58, 119.81, 33718.147), (52, 297.17, 150.678), (50, 21.02, 2281.226),
        (45, 247.54, 29929.562), (44, 325.15, 31555.956), (29, 60.93, 4443.417), (18, 155.12, 67555.328),
        (17, 288.79, 4562.452), (16, 198.04, 62894.029), (14, 199.76, 31436.921), (12, 95.39, 14577.848),
        (12, 287.11, 31931.756), (12, 320.81, 34777.259), (9, 227.73, 1222.114), (8, 15.45, 16859.074),
    )
    S = sum(a * math.cos(math.radians(b + c * T)) for a, b, c in terms)
    return jde0 + 0.00001 * S / dlambda


def sunset(day: datetime.date) -> float:
    """Sunset at Ṭihrán on *day* as a Julian Day in UT (NOAA)."""
    jd = day.toordinal() + 1721424.5 + 0.5 - LONGITUDE / 360   # local noon, to start
    minutes = 18 * 60.0
    for _ in range(3):
        JC = (jd + minutes / 1440 - 2451545.0 - 0.5) / 36525
        L0 = (280.46646 + JC * (36000.76983 + 0.0003032 * JC)) % 360
        M = 357.52911 + JC * (35999.05029 - 0.0001537 * JC)
        e = 0.016708634 - JC * (0.000042037 + 0.0000001267 * JC)
        Mr = math.radians(M)
        C = (math.sin(Mr) * (1.914602 - JC * (0.004817 + 0.000014 * JC)) + math.sin(2 * Mr) * (0.019993 - 0.000101 * JC)
             + math.sin(3 * Mr) * 0.000289)
        omega = math.radians(125.04 - 1934.136 * JC)
        apparent = math.radians(L0 + C - 0.00569 - 0.00478 * math.sin(omega))
        obliquity = (23 + (26 + (21.448 - JC * (46.815 + JC * (0.00059 - JC * 0.001813))) / 60) / 60
                     + 0.00256 * math.cos(omega))
        eps = math.radians(obliquity)
        declination = math.asin(math.sin(eps) * math.sin(apparent))
        y = math.tan(eps / 2) ** 2
        L0r = math.radians(L0)
        equation = 4 * math.degrees(y * math.sin(2 * L0r) - 2 * e * math.sin(Mr) + 4 * e * y * math.sin(Mr) * math.cos(2 * L0r)
                                    - 0.5 * y * y * math.sin(4 * L0r) - 1.25 * e * e * math.sin(2 * Mr))
        lat = math.radians(LATITUDE)
        hour_angle = math.degrees(math.acos(math.cos(math.radians(90.833)) / (math.cos(lat) * math.cos(declination))
                                            - math.tan(lat) * math.tan(declination)))
        minutes = 720 - 4 * LONGITUDE - equation + 4 * hour_angle
    return day.toordinal() + 1721424.5 + minutes / 1440


def naw_ruz(year: int) -> tuple[datetime.date, float]:
    """Naw-Rúz of Badíʿ *year* by the equinox at Ṭihrán, and the equinox's
    distance from the sunset that decides it, in days."""
    jde = march_equinox(gregorian_year(year))
    equinox = jde - delta_t(gregorian_year(year) + 0.2) / 86400
    local = datetime.date.fromordinal(math.floor(equinox + 0.5 + HOURS / 24) - 1721425)
    dusk = sunset(local)
    return (local if equinox < dusk else local + datetime.timedelta(days=1)), equinox - dusk


HEADER = '''# navml: generated by tools/badi.py; do not edit.
"""The Badíʿ calendar's Naw-Rúz days by the equinox at Ṭihrán, {first} to {last} BE.

``NAW_RUZ[n]`` is the ordinal (``datetime.date.toordinal()``) of Naw-Rúz of
year ``FIRST_YEAR + n``; the last is the day after year {last}'s end.
Before ``FIRST_YEAR`` Naw-Rúz was 21 March.  To ``PUBLISHED_LAST`` they are
the World Centre's table's; after it, computed.
"""

FIRST_YEAR = {first}
PUBLISHED_LAST = {published_last}

NAW_RUZ: tuple[int, ...] = (
'''


def check() -> int:
    namespace: dict = {}
    exec(MODULE.read_text(encoding="utf-8"), namespace)
    days = namespace["NAW_RUZ"]
    problems = [f"{namespace['FIRST_YEAR'] + i}: {b - a} days" for i, (a, b) in enumerate(zip(days, days[1:]))
                if b - a not in (365, 366)]
    for problem in problems:
        print(f"{MODULE}: {problem}", file=sys.stderr)
    return 1 if problems else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="exit 1 when the module is inconsistent")
    args = parser.parse_args()
    if args.check:
        return check()
    computed = {year: naw_ruz(year) for year in range(FIRST_ASTRONOMICAL, LAST_YEAR + 2)}
    differ = [year for year, day in OFFICIAL.items() if computed[year][0] != datetime.date(gregorian_year(year), 3, day)]
    unexplained = [year for year in differ if abs(computed[year][1]) >= MARGIN]
    print(f"against the World Centre's table: {len(OFFICIAL) - len(differ)} of {len(OFFICIAL)} years; apart: "
          + ", ".join(f"{year} BE (equinox {computed[year][1] * 86400:+.0f} s from sunset)" for year in differ))
    if unexplained:
        print(f"apart by more than the method's precision: {unexplained}; nothing written", file=sys.stderr)
        return 1
    days = {year: datetime.date(gregorian_year(year), 3, day) for year, day in OFFICIAL.items()}
    published_last = max(OFFICIAL)
    for year, (day, margin) in computed.items():
        if year > published_last:
            days[year] = day
            if abs(margin) < MARGIN:
                print(f"  computed {year} BE ({day}): the equinox {abs(margin) * 86400:.0f} s "
                      f"{'before' if margin < 0 else 'after'} sunset -- the almanac may differ")
    rows = "".join(f"    {day.toordinal()},  # {year} BE, {day}\n" for year, day in sorted(days.items()))
    MODULE.write_text(HEADER.format(first=FIRST_ASTRONOMICAL, last=LAST_YEAR, published_last=published_last)
                      + rows + ")\n", encoding="utf-8")
    print(f"wrote {MODULE}: {FIRST_ASTRONOMICAL} to {LAST_YEAR} BE")
    return check()


if __name__ == "__main__":
    sys.exit(main())

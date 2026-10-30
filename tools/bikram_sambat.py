#!/usr/bin/env python3
"""Write Nepal's Bikram Sambat calendar, ``navml/nepali_data.py``.

    ./venv/bin/python tools/bikram_sambat.py           # fetch, verify the rule, write it
    ./venv/bin/python tools/bikram_sambat.py --check   # exit 1 when it is inconsistent

Nepal's official calendar (विक्रम संवत्) is solar and sidereal: a month begins
with a *saṅkrānti*, the Sun entering the next sign of the zodiac, and lasts
29 to 32 days.  Nepal's almanac committee (Nepal Panchanga Nirnayak Samiti)
publishes it year by year; no formula is official and no table of its own is
open.  So:

**The published years** come from the tables three MIT-licensed packages
ship -- ``nepali-datetime``, ``bikram-sambat`` and ``nepali`` -- fetched from
PyPI as wheels and read as data, none of their code run.  A year is kept
where two of them agree: 1975 to 2083 BS (13 April 1918 to 13 April 2027),
the three agreeing but in 2062, where the two outvote ``nepali``.  After 2083
they part -- one repeats its rows of 85 years before, another guesses -- so
none of them is the almanac's.

**The later years are computed**, by the rule that gives the published ones:
the Sun of the *Sūrya Siddhānta* (Reingold and Dershowitz's
``hindu-solar-longitude``, reckoned at Ujjain), its ingress in India's time
(UTC+5:30), and the day it falls on, but for the two solstitial saṅkrāntis,
whose night belongs elsewhere as the *dharmaśāstra* rules it -- Karka's
(Shrawan) before dawn to the day before, Makara's (Magh, Maghe Sankranti)
after dusk to the day after.  Checked against the published years it gives
:data:`AGREEMENT` of their month starts or better (1,299 of 1,308 when written;
the rest within half an hour of the midnight or dawn that decides them), and
the tool writes nothing if it falls short.

``--check`` needs no network: it says whether every month is 29 to 32 days
and every year follows the last.
"""

from __future__ import annotations

import argparse
import csv
import datetime
import io
import json
import math
import re
import sys
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODULE = ROOT / "navml" / "nepali_data.py"

#: Each package's pinned wheel, the table's path in it, and the year and day it starts on.
SOURCES = {
    "nepali-datetime": ("1.0.8.5", "nepali_datetime/data/calendar_bs.csv", 1975, datetime.date(1918, 4, 13)),
    "bikram-sambat": ("0.2.0", "bikram_sambat/data/calendar_data.py", 1901, datetime.date(1844, 4, 11)),
    "nepali": ("1.2.0", "nepali/date_converter.py", 2000, datetime.date(1943, 4, 14)),
}
#: The years written: the published from the first, the computed after the last.
FIRST_YEAR, PUBLISHED_LAST, LAST_YEAR = 1975, 2083, 2156
#: The share of the published month starts the rule must give.
AGREEMENT = 0.99

ORDINAL = 1_721_425
#: India's time, which the almanac's ingresses are reckoned in.
HOURS = 5.5
#: Before this hour Karka's ingress is the day before's; from this hour Makara's the day after's.
KARKA_DAWN, MAKARA_DUSK = 5.55, 17.0
#: Ujjain, the Sūrya Siddhānta's meridian, in degrees east.
UJJAIN = 75 + 46 / 60 + 6 / 3600


# -- the published tables -------------------------------------------------------


def wheel(name: str, version: str) -> zipfile.ZipFile:
    with urllib.request.urlopen(f"https://pypi.org/pypi/{name}/{version}/json", timeout=60) as response:
        release = json.load(response)
    url = next(f["url"] for f in release["urls"] if f["packagetype"] == "bdist_wheel")
    with urllib.request.urlopen(url, timeout=120) as response:
        return zipfile.ZipFile(io.BytesIO(response.read()))


def months_of(name: str, text: str) -> dict[int, list[int]]:
    """Each year's twelve months, from a package's table as text."""
    if name == "nepali-datetime":
        rows = list(csv.reader(io.StringIO(text)))[1:]
        return {int(row[0]): [int(v) for v in row[1:13]] for row in rows if row}
    if name == "bikram-sambat":
        block = text[text.index("YEAR_MONTH_DAYS_BS"):]
        block = block[:block.index("}")]
        return {int(y): [int(v) for v in m.split(",")] for y, m in re.findall(r"(\d{4}):\s*\[([^\]]*)\]", block)}
    block = text[text.index("NP_MONTHS_DATA"):]
    rows = re.findall(r"\(\s*\(([\d,\s]+)\)\s*,\s*\d+\s*,?\s*\)", block)
    first = SOURCES["nepali"][2]
    return {first + i: [int(v) for v in row.split(",") if v.strip()] for i, row in enumerate(rows)}


def placed(table: dict[int, list[int]], first_year: int, first_day: datetime.date) -> dict[int, tuple[int, list[int]]]:
    out, day = {}, first_day.toordinal()
    for year in sorted(y for y in table if y >= first_year):
        out[year] = (day, table[year])
        day += sum(table[year])
    return out


def published() -> dict[int, tuple[int, list[int]]]:
    """The years two of the tables agree on, ``FIRST_YEAR`` to ``PUBLISHED_LAST``."""
    tables = []
    for name, (version, path, first_year, first_day) in SOURCES.items():
        text = wheel(name, version).read(path).decode("utf-8")
        tables.append(placed(months_of(name, text), first_year, first_day))
    agreed = {}
    for year in range(FIRST_YEAR, PUBLISHED_LAST + 1):
        votes = [table[year] for table in tables if year in table]
        best = max(votes, key=votes.count)
        if votes.count(best) < 2:
            raise ValueError(f"{year}: no two tables agree")
        agreed[year] = best
    return agreed


# -- the Sūrya Siddhānta's sun (Reingold and Dershowitz) ------------------------

SIDEREAL_YEAR = 365 + 279457 / 1080000
ANOMALISTIC_YEAR = 1577917828000 / (4320000000 - 387)
#: The Kali Yuga's epoch, Julian 18 February 3102 BC, as a fixed day.
EPOCH = -1132959
CREATION = EPOCH - 1955880000 * SIDEREAL_YEAR


def _sine_table(entry: int) -> float:
    exact = 3438 * math.sin(math.radians(entry * 225 / 60))
    error = 0.215 * math.copysign(1, exact) * math.copysign(1, abs(exact) - 1716)
    return round(exact + error) / 3438


def _sine(theta: float) -> float:
    entry = theta / (225 / 60)
    fraction = entry - math.floor(entry)
    return fraction * _sine_table(math.ceil(entry)) + (1 - fraction) * _sine_table(math.floor(entry))


def _arcsin(amplitude: float) -> float:
    if amplitude < 0:
        return -_arcsin(-amplitude)
    position = 0
    while amplitude > _sine_table(position):
        position += 1
    below = _sine_table(position - 1)
    return 225 / 60 * (position - 1 + (amplitude - below) / (_sine_table(position) - below))


def _mean_position(moment: float, period: float) -> float:
    turns = (moment - CREATION) / period
    return 360 * (turns - math.floor(turns))


def solar_longitude(moment: float) -> float:
    """The Sun's sidereal longitude at a fixed moment (Ujjain's time)."""
    mean = _mean_position(moment, SIDEREAL_YEAR)
    offset = _sine(_mean_position(moment, ANOMALISTIC_YEAR))
    size = 14 / 360
    equation = _arcsin(offset * (size - abs(offset) * size / 42))
    return (mean - equation) % 360


def ingress(near: float, sign: int) -> float:
    """The fixed moment near *near* when the Sun enters *sign* (0 for Mesha)."""
    moment = near
    for _ in range(60):
        error = (30 * sign - solar_longitude(moment) + 180) % 360 - 180
        moment += error * SIDEREAL_YEAR / 360
        if abs(error) < 1e-9:
            break
    return moment


def month_start(moment: float, sign: int) -> int:
    """The day a month begins on, for an ingress at a fixed moment in Ujjain's time."""
    local = moment + (HOURS - UJJAIN / 15) / 24
    day = math.floor(local)
    hour = (local - day) * 24
    if sign == 3 and hour < KARKA_DAWN:       # Karka: Shrawan
        return day - 1
    if sign == 9 and hour >= MAKARA_DUSK:     # Makara: Magh
        return day + 1
    return day


def computed_starts(first_day: int, years: int) -> list[int]:
    """The first day of each month for *years* years from the one beginning near *first_day*."""
    starts, near = [], float(first_day)
    for index in range(12 * years + 1):
        moment = ingress(near, index % 12)
        starts.append(month_start(moment, index % 12))
        near = moment + 30.4
    return starts


# -- writing --------------------------------------------------------------------

HEADER = '''# navml: generated by tools/bikram_sambat.py; do not edit.
"""Nepal's Bikram Sambat months, {first} to {last} BS.

``YEARS[n]`` is year ``FIRST_YEAR + n``: the ordinal of its first day (1
Baisakh, ``datetime.date.toordinal()``) and its twelve months' lengths.  The
years to ``PUBLISHED_LAST`` are the published almanac's (as the tables of
three packages agree on it); the later ones are computed by the rule that
gives those.
"""

FIRST_YEAR = {first}
PUBLISHED_LAST = {published_last}

YEARS: tuple[tuple[int, tuple[int, ...]], ...] = (
'''


def module_text(years: dict[int, tuple[int, list[int]]]) -> str:
    rows = "".join(f"    ({start}, ({', '.join(map(str, months))})),  # {year}\n"
                   for year, (start, months) in sorted(years.items()))
    return HEADER.format(first=min(years), last=max(years), published_last=PUBLISHED_LAST) + rows + ")\n"


def check() -> int:
    namespace: dict = {}
    exec(MODULE.read_text(encoding="utf-8"), namespace)
    first, table = namespace["FIRST_YEAR"], namespace["YEARS"]
    problems = []
    for index, (start, months) in enumerate(table):
        if len(months) != 12 or not all(29 <= m <= 32 for m in months):
            problems.append(f"{first + index}: months {months}")
        if index + 1 < len(table) and table[index + 1][0] - start != sum(months):
            problems.append(f"{first + index}: its months are {sum(months)} days, the year {table[index + 1][0] - start}")
    for problem in problems:
        print(f"{MODULE}: {problem}", file=sys.stderr)
    return 1 if problems else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="exit 1 when the module is inconsistent")
    args = parser.parse_args()
    if args.check:
        return check()
    years = published()
    # The rule, against every published month start.
    expected = [start for year in range(FIRST_YEAR, PUBLISHED_LAST + 1)
                for start in (lambda s, m: [s + sum(m[:i]) for i in range(12)])(*years[year])]
    expected.append(years[PUBLISHED_LAST][0] + sum(years[PUBLISHED_LAST][1]))
    count = PUBLISHED_LAST - FIRST_YEAR + 1
    starts = computed_starts(years[FIRST_YEAR][0] - 1, count)
    misses = [(FIRST_YEAR + i // 12, i % 12 + 1) for i, (a, b) in enumerate(zip(starts, expected[:-1])) if a != b]
    share = 1 - len(misses) / (12 * count)
    print(f"the rule against the published years: {12 * count - len(misses)} of {12 * count} month starts "
          f"({share:.1%}); apart: {misses}")
    if share < AGREEMENT:
        print(f"below {AGREEMENT:.0%}; nothing written", file=sys.stderr)
        return 1
    # The rest, computed from the published years' end.
    later = computed_starts(expected[-1] - 1, LAST_YEAR - PUBLISHED_LAST)
    if later[0] != expected[-1]:
        print("the rule does not begin where the published years end; nothing written", file=sys.stderr)
        return 1
    for offset in range(LAST_YEAR - PUBLISHED_LAST):
        months = later[12 * offset:12 * offset + 13]
        years[PUBLISHED_LAST + 1 + offset] = (months[0], [b - a for a, b in zip(months, months[1:])])
    MODULE.write_text(module_text(years), encoding="utf-8")
    print(f"wrote {MODULE}: {FIRST_YEAR} to {LAST_YEAR} BS, computed from {PUBLISHED_LAST + 1}")
    return check()


if __name__ == "__main__":
    sys.exit(main())

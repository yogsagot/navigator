#!/usr/bin/env python3
"""Compute Hijri calendars that begin a month by a crescent-visibility criterion.

    ./venv/bin/python tools/hijri_criteria.py --verify   # each rule against its published months
    ./venv/bin/python tools/hijri_criteria.py            # verify, then write the modules
    ./venv/bin/python tools/hijri_criteria.py --check    # exit 1 when a module is inconsistent

Turkey's Diyanet and the MABIMS countries (Brunei, Indonesia, Malaysia,
Singapore) publish Hijri calendars whose months begin by a rule about the
crescent at sunset on the 29th -- how high above the horizon, how far from
the Sun -- reckoned over a region.  R. H. van Gent tabulates their past
months (``islamcalendar_dat.js``, which ``tools/umm_al_qura.py`` reads too);
no one publishes their future ones openly.  So this computes them with
``tools/moon.py``'s Moon and Sun, checks each rule against van Gent's months
first, and writes the published months as published and the rest computed.
"""

from __future__ import annotations

import argparse
import datetime
import math
import re
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import moon as M  # noqa: E402
from lunisolar import delta_t, new_moon  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
URL = "https://webspace.science.uu.nl/~gent0113/islam/addfiles/islamcalendar_dat.js"
MCJDN, ORDINAL = 2_400_000, 1_721_425
EARTH_RADIUS = 6378.14


def tt(jd_ut: float) -> float:
    year = 2000 + (jd_ut - 2451545.0) / 365.25
    return jd_ut + delta_t(year) / 86400


# -- the sky at a place -----------------------------------------------------------


def sun_altitude(jd_ut: float, lat: float, lon: float) -> float:
    jde = tt(jd_ut)
    ls, _ = M.sun(jde)
    _, eps = M.nutation(jde)
    ra, dec = M.equatorial(ls, 0.0, eps)
    hour = math.radians(M.sidereal(jd_ut) + lon - ra)
    phi, delta = math.radians(lat), math.radians(dec)
    return math.degrees(math.asin(math.sin(phi) * math.sin(delta) + math.cos(phi) * math.cos(delta) * math.cos(hour)))


def sunset(day: datetime.date, lat: float, lon: float, depression: float = 0.8333) -> float | None:
    """The JD (UT) of sunset at the place on its local *day*, or None if the Sun does not set."""
    jd = day.toordinal() + ORDINAL - 0.5 + (18 - lon / 15) / 24
    for _ in range(8):
        f = sun_altitude(jd, lat, lon) + depression
        slope = (sun_altitude(jd + 1 / 1440, lat, lon) + depression - f) * 1440
        if abs(slope) < 1e-6:
            return None
        step = f / slope
        jd -= max(-0.2, min(0.2, step))
        if abs(step) < 1e-5:
            return jd
    return jd


def crescent(jd_ut: float, lat: float, lon: float, topocentric: bool, refraction: bool) -> tuple[float, float]:
    """The Moon's altitude and its elongation from the Sun at an instant, in degrees."""
    jde = tt(jd_ut)
    lm, bm, distance = M.moon(jde)
    _, eps = M.nutation(jde)
    ra, dec = M.equatorial(lm, bm, eps)
    hour = math.radians(M.sidereal(jd_ut) + lon - ra)
    phi, delta = math.radians(lat), math.radians(dec)
    altitude = math.degrees(math.asin(math.sin(phi) * math.sin(delta) + math.cos(phi) * math.cos(delta) * math.cos(hour)))
    if topocentric:
        altitude -= math.degrees(math.asin(EARTH_RADIUS / distance)) * math.cos(math.radians(altitude))
    if refraction and altitude > -1:
        altitude += 1.02 / math.tan(math.radians(altitude + 10.3 / (altitude + 5.11))) / 60
    return altitude, M.elongation(jde)


# -- the rules ------------------------------------------------------------------------


def grid(lat0, lat1, lon0, lon1, step):
    lat = lat0
    while lat <= lat1 + 1e-9:
        lon = lon0
        while lon <= lon1 + 1e-9:
            yield lat, lon
            lon += step
        lat += step


REGIONS = {
    "earth": list(grid(-60, 60, -180, 175, 5)),
    "indonesia box": list(grid(-11, 6, 95, 141, 1)),
    #: Indonesia's territory, west to east: Sabang, the westernmost town, along Sumatra's west coast,
    #: Java, Nusa Tenggara, Kalimantan, Sulawesi, Maluku and Papua.
    "indonesia": [
        (5.89, 95.32), (5.55, 95.32), (4.14, 96.13), (2.96, 97.6), (-0.95, 100.35), (-3.8, 102.27),
        (-5.35, 102.2), (-5.43, 105.26), (-6.06, 105.88), (-7.03, 106.53), (-6.2, 106.8), (-7.8, 110.36),
        (-7.25, 112.75), (-8.65, 115.22), (-8.58, 116.1), (-10.17, 123.6), (-0.03, 109.33),
        (-1.27, 116.83), (-5.14, 119.42), (1.47, 124.84), (-3.7, 128.18), (-0.87, 131.25), (-2.53, 140.7),
        (-8.5, 140.4),
    ],
    "malaysia": list(grid(1, 7.5, 99.5, 119.5, 0.5)),
    #: The Americas' mainland, where the 2016 rule's exception looks: its west coast, north to south
    #: (the westernmost place at a latitude has the latest sunset), islands left out.
    "americas": [
        (65.6, -168.0), (64.5, -165.4), (60.8, -161.8), (58.7, -157.0), (55.9, -160.5), (57.0, -135.0),
        (54.3, -130.3), (50.0, -125.0), (45.0, -124.0), (40.4, -124.4), (35.0, -120.6), (30.0, -115.8),
        (25.0, -112.1), (20.0, -105.5), (15.0, -92.6), (10.0, -85.7), (5.0, -77.4), (0.0, -80.1),
        (-5.0, -81.1), (-10.0, -78.2), (-15.0, -75.5), (-20.0, -70.2), (-25.0, -70.5), (-30.0, -71.6),
        (-35.0, -72.2), (-40.0, -73.7), (-45.0, -74.5), (-50.0, -75.4), (-55.0, -71.0),
    ],
    "singapore": [(1.3521, 103.8198)],
    "jakarta": [(-6.2, 106.8)],
    "pelabuhan ratu": [(-7.03, 106.53)],
    "banda aceh": [(5.55, 95.32)],
    "kuala lumpur": [(3.14, 101.69)],
    "brunei": [(4.9031, 114.9398)],
}


class Rule:
    """A criterion: at sunset on the evening after the conjunction, somewhere
    in *region*, the Moon at least *altitude* high and *elongation* from the
    Sun (or *age* hours old, when given, as the alternative); the month begins
    the next day, else the day after."""

    def __init__(self, name, region, altitude, elongation, age=None, topocentric=True, refraction=False,
                 before_utc_midnight=False, age_alone=False, americas_exception=False):
        self.name, self.region = name, REGIONS[region]
        self.altitude, self.elongation, self.age = altitude, elongation, age
        self.topocentric, self.refraction = topocentric, refraction
        self.before_utc_midnight = before_utc_midnight
        #: Whether the age suffices without the altitude.
        self.age_alone = age_alone
        #: The 2016 congress's exception to *before_utc_midnight*: seen on the Americas' mainland after
        #: 0h UT still counts if the conjunction came before dawn (fajr) in New Zealand.
        self.americas_exception = americas_exception

    def seen(self, day: datetime.date, conjunction_ut: float) -> bool:
        if self._seen(self.region, day, conjunction_ut, self.before_utc_midnight):
            return True
        if self.americas_exception and conjunction_ut < self._nz_fajr(day):
            return self._seen(REGIONS["americas"], day, conjunction_ut, False)
        return False

    @staticmethod
    def _nz_fajr(day: datetime.date) -> float:
        """Dawn (the Sun 18 degrees below the horizon) at Wellington on the morning after *day*, as UT."""
        lat, lon = -41.29, 174.78
        morning = day + datetime.timedelta(days=1)
        jd = morning.toordinal() + ORDINAL - 0.5 + (5 - lon / 15) / 24
        for _ in range(8):
            f = sun_altitude(jd, lat, lon) + 18
            slope = (sun_altitude(jd + 1 / 1440, lat, lon) + 18 - f) * 1440
            jd -= max(-0.2, min(0.2, f / slope))
        return jd

    def _seen(self, region, day: datetime.date, conjunction_ut: float, before_utc_midnight: bool) -> bool:
        for lat, lon in region:
            dusk = sunset(day, lat, lon)
            if dusk is None or dusk <= conjunction_ut:
                continue
            if before_utc_midnight and dusk >= day.toordinal() + ORDINAL + 0.5:
                continue
            altitude, elongation = crescent(dusk, lat, lon, self.topocentric, self.refraction)
            if altitude >= self.altitude and elongation >= self.elongation:
                return True
            if self.age is not None and (self.age_alone or altitude >= self.altitude) \
                    and (dusk - conjunction_ut) * 24 >= self.age:
                return True
        return False

    def month_start(self, k: int) -> int:
        """The first day of the month after lunation *k*'s conjunction (ch. 49's numbering)."""
        jde = new_moon(k)
        conj = jde - delta_t(2000 + (jde - 2451545) / 365.25) / 86400
        # The first evening a place in the region may see it: the local date of the conjunction.
        lat, lon = self.region[len(self.region) // 2]
        day = datetime.date.fromordinal(math.floor(conj + 0.5 + lon / 360) - ORDINAL)
        return (day + datetime.timedelta(days=1 if self.seen(day, conj) else 2)).toordinal()


# -- the published months ------------------------------------------------------------


def published(name: str, source: str) -> list[int]:
    match = re.search(name + r"\s*=\s*new Array\(([^)]*)\)", source)
    return [int(v) + MCJDN - ORDINAL for v in re.findall(r"\d+", match[1])]


def lunation(day: int) -> int:
    """Ch. 49's number of the conjunction a month beginning on *day* follows."""
    return round((day + ORDINAL - 2451550.09766 - 1.5) / 29.530588861)


def compare(rule: Rule, starts: list[int]) -> list[tuple[datetime.date, int]]:
    """The published month starts the rule puts elsewhere, and by how many days."""
    apart = []
    for day in starts:
        got = rule.month_start(lunation(day))
        if got != day:
            apart.append((datetime.date.fromordinal(day), got - day))
    return apart


#: Each calendar: van Gent's array, its rules by era (from the first Hijri year a rule applies), the
#: era to verify against his months, and how much of it must agree.
CALENDARS = {
    "diyanet": dict(
        array="diyanet_dat",
        title="Turkey's Diyanet",
        rules=((0, Rule("2016 congress", "earth", 5, 8, before_utc_midnight=True, americas_exception=True)),),
        verify_from=datetime.date(2016, 9, 1), agreement=0.95,
    ),
    "mabims_id": dict(
        array="mabims_id_dat",
        title="Indonesia's MABIMS",
        rules=((0, Rule("MABIMS 2/3/8h", "indonesia", 2, 3, age=8)),
               (1443, Rule("Neo-MABIMS 3/6.4", "indonesia", 3, 6.4))),
        verify_from=datetime.date(1990, 1, 1), agreement=0.95,
    ),
    "mabims_my": dict(
        array="mabims_my_dat",
        title="Malaysia's MABIMS",
        rules=((0, Rule("MABIMS 2/3 or 8h", "malaysia", 2, 3, age=8, age_alone=True)),
               (1443, Rule("Neo-MABIMS 3/6.4", "malaysia", 3, 6.4))),
        verify_from=datetime.date(1990, 1, 1), agreement=0.99,
    ),
}
#: The last Hijri year computed: 1525 AH ends in 2101.
LAST_YEAR = 1525

HEADER = '''# navml: generated by tools/hijri_criteria.py; do not edit.
"""{title} Hijri months, {first_year}/{first_month} to {last_year}/12 AH.

``MONTH_STARTS[n]`` is the first day (``datetime.date.toordinal()``) of the
n-th month from ``FIRST_YEAR``/``FIRST_MONTH``; the last entry is the day
after the last month.  The months beginning on or before ``PUBLISHED_LAST``
are R. H. van Gent's tabulation of the published calendar; the later ones are
computed by its rule ({rules}).
"""

FIRST_YEAR = {first_year}
FIRST_MONTH = {first_month}
PUBLISHED_LAST = {published_last}

MONTH_STARTS: tuple[int, ...] = (
'''


def hijri_month(day: int) -> tuple[int, int]:
    """The Hijri year and month a month beginning on *day* is: the tabular one around it."""
    sys.path.insert(0, str(ROOT))
    from navml.calendars import SYSTEMS

    year, month, _ = SYSTEMS["islamic"].from_fixed(day + 14)
    return year, month


def rule_for(rules, year: int) -> Rule:
    return [rule for since, rule in rules if year >= since][-1]


def check(name: str) -> int:
    path = ROOT / "navml" / f"{name}_data.py"
    namespace: dict = {}
    exec(path.read_text(encoding="utf-8"), namespace)
    starts = namespace["MONTH_STARTS"]
    problems = [f"month {i}: {b - a} days" for i, (a, b) in enumerate(zip(starts, starts[1:])) if b - a not in (29, 30)]
    for problem in problems:
        print(f"{path}: {problem}", file=sys.stderr)
    return 1 if problems else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--verify", action="store_true", help="only compare the rules with the published months")
    parser.add_argument("--check", action="store_true", help="exit 1 when a module is inconsistent")
    parser.add_argument("--only", default="", help="only this calendar")
    args = parser.parse_args()
    if args.check:
        return max(check(name) for name in CALENDARS)
    with urllib.request.urlopen(URL, timeout=60) as response:
        source = response.read().decode("utf-8", errors="replace")
    status = 0
    for name, spec in CALENDARS.items():
        if args.only and args.only != name:
            continue
        starts = published(spec["array"], source)
        # The rule of each published month's era, against it.
        tested = [day for day in starts[:-1] if day >= spec["verify_from"].toordinal()]
        apart = [(datetime.date.fromordinal(day), rule_for(spec["rules"], hijri_month(day)[0]).month_start(lunation(day)) - day)
                 for day in tested]
        apart = [(day, by) for day, by in apart if by]
        share = 1 - len(apart) / len(tested)
        print(f"{name}: {len(tested) - len(apart)} of {len(tested)} published months from "
              f"{spec['verify_from']} ({share:.1%}); apart {apart}", flush=True)
        if share < spec["agreement"]:
            print(f"{name}: below {spec['agreement']:.0%}; not written", file=sys.stderr)
            status = 1
            continue
        if args.verify:
            continue
        # The published months, then the computed from the one after the last.
        months = list(starts)
        k = lunation(months[-1])
        while hijri_month(months[-1]) <= (LAST_YEAR, 12):
            k += 1
            year = hijri_month(months[-1])[0]
            months.append(rule_for(spec["rules"], year).month_start(k))
        first_year, first_month = hijri_month(months[0])
        last_year, _ = hijri_month(months[-2])
        rules = "; ".join(f"{rule.name}{f' from {since} AH' if since else ''}" for since, rule in spec["rules"])
        head = HEADER.format(title=spec["title"], first_year=first_year, first_month=first_month,
                             last_year=last_year, published_last=starts[-2], rules=rules)
        rows = "".join(f"    {day},  # {'/'.join(map(str, hijri_month(day)))} {datetime.date.fromordinal(day)}\n"
                       for day in months)
        (ROOT / "navml" / f"{name}_data.py").write_text(head + rows + ")\n", encoding="utf-8")
        print(f"wrote navml/{name}_data.py: {first_year}/{first_month} to {last_year}/12 AH, "
              f"computed from {datetime.date.fromordinal(starts[-1])}", flush=True)
        status = max(status, check(name))
    return status


if __name__ == "__main__":
    sys.exit(main())

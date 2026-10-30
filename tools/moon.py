"""The Moon's and the Sun's places, for the tools that compute calendars by
when a crescent can be seen (``tools/hijri_criteria.py``).

The Moon is Meeus' truncation of ELP-2000/82 (*Astronomical Algorithms*,
ch. 47: 60 terms in longitude and distance, 60 in latitude, good to about 10"
in longitude and 4" in latitude); the Sun is his low-precision theory (ch.
25, about 0.01°), nutation in longitude and obliquity by ch. 22's main terms,
sidereal time by ch. 12.  All take a Julian Ephemeris Day; ``ut`` converts.

``python tools/moon.py`` checks the Moon against the new moons of ch. 49 (an
independent series, which ``tools/lunisolar.py`` verified against the Hong
Kong Observatory's calendar): the instant the two longitudes meet must be
within :data:`CONJUNCTION_TOLERANCE` of it for every lunation 1900-2100.
"""

from __future__ import annotations

import math
import sys

#: How far apart, in days, the two theories' conjunctions may be.
CONJUNCTION_TOLERANCE = 2 / 1440

# D, M, M', F, Σl (1e-6 °), Σr (1e-3 km)
LONGITUDE_DISTANCE = (
    (0, 0, 1, 0, 6288774, -20905355), (2, 0, -1, 0, 1274027, -3699111), (2, 0, 0, 0, 658314, -2955968),
    (0, 0, 2, 0, 213618, -569925), (0, 1, 0, 0, -185116, 48888), (0, 0, 0, 2, -114332, -3149),
    (2, 0, -2, 0, 58793, 246158), (2, -1, -1, 0, 57066, -152138), (2, 0, 1, 0, 53322, -170733),
    (2, -1, 0, 0, 45758, -204586), (0, 1, -1, 0, -40923, -129620), (1, 0, 0, 0, -34720, 108743),
    (0, 1, 1, 0, -30383, 104755), (2, 0, 0, -2, 15327, 10321), (0, 0, 1, 2, -12528, 0),
    (0, 0, 1, -2, 10980, 79661), (4, 0, -1, 0, 10675, -34782), (0, 0, 3, 0, 10034, -23210),
    (4, 0, -2, 0, 8548, -21636), (2, 1, -1, 0, -7888, 24208), (2, 1, 0, 0, -6766, 30824),
    (1, 0, -1, 0, -5163, -8379), (1, 1, 0, 0, 4987, -16675), (2, -1, 1, 0, 4036, -12831),
    (2, 0, 2, 0, 3994, -10445), (4, 0, 0, 0, 3861, -11650), (2, 0, -3, 0, 3665, 14403),
    (0, 1, -2, 0, -2689, -7003), (2, 0, -1, 2, -2602, 0), (2, -1, -2, 0, 2390, 10056),
    (1, 0, 1, 0, -2348, 6322), (2, -2, 0, 0, 2236, -9884), (0, 1, 2, 0, -2120, 5751),
    (0, 2, 0, 0, -2069, 0), (2, -2, -1, 0, 2048, -4950), (2, 0, 1, -2, -1773, 4130),
    (2, 0, 0, 2, -1595, 0), (4, -1, -1, 0, 1215, -3958), (0, 0, 2, 2, -1110, 0),
    (3, 0, -1, 0, -892, 3258), (2, 1, 1, 0, -810, 2616), (4, -1, -2, 0, 759, -1897),
    (0, 2, -1, 0, -713, -2117), (2, 2, -1, 0, -700, 2354), (2, 1, -2, 0, 691, 0),
    (2, -1, 0, -2, 596, 0), (4, 0, 1, 0, 549, -1423), (0, 0, 4, 0, 537, -1117),
    (4, -1, 0, 0, 520, -1571), (1, 0, -2, 0, -487, -1739), (2, 1, 0, -2, -399, 0),
    (0, 0, 2, -2, -381, -4421), (1, 1, 1, 0, 351, 0), (3, 0, -2, 0, -340, 0),
    (4, 0, -3, 0, 330, 0), (2, -1, 2, 0, 327, 0), (0, 2, 1, 0, -323, 1165),
    (1, 1, -1, 0, 299, 0), (2, 0, 3, 0, 294, 0), (2, 0, -1, -2, 0, 8752),
)

# D, M, M', F, Σb (1e-6 °)
LATITUDE = (
    (0, 0, 0, 1, 5128122), (0, 0, 1, 1, 280602), (0, 0, 1, -1, 277693), (2, 0, 0, -1, 173237),
    (2, 0, -1, 1, 55413), (2, 0, -1, -1, 46271), (2, 0, 0, 1, 32573), (0, 0, 2, 1, 17198),
    (2, 0, 1, -1, 9266), (0, 0, 2, -1, 8822), (2, -1, 0, -1, 8216), (2, 0, -2, -1, 4324),
    (2, 0, 1, 1, 4200), (2, 1, 0, -1, -3359), (2, -1, -1, 1, 2463), (2, -1, 0, 1, 2211),
    (2, -1, -1, -1, 2065), (0, 1, -1, -1, -1870), (4, 0, -1, -1, 1828), (0, 1, 0, 1, -1794),
    (0, 0, 0, 3, -1749), (0, 1, -1, 1, -1565), (1, 0, 0, 1, -1491), (0, 1, 1, 1, -1475),
    (0, 1, 1, -1, -1410), (0, 1, 0, -1, -1344), (1, 0, 0, -1, -1335), (0, 0, 3, 1, 1107),
    (4, 0, 0, -1, 1021), (4, 0, -1, 1, 833), (0, 0, 1, -3, 777), (4, 0, -2, 1, 671),
    (2, 0, 0, -3, 607), (2, 0, 2, -1, 596), (2, -1, 1, -1, 491), (2, 0, -2, 1, -451),
    (0, 0, 3, -1, 439), (2, 0, 2, 1, 422), (2, 0, -3, -1, 421), (2, 1, -1, 1, -366),
    (2, 1, 0, 1, -351), (4, 0, 0, 1, 331), (2, -1, 1, 1, 315), (2, -2, 0, -1, 302),
    (0, 0, 1, 3, -283), (2, 1, 1, -1, -229), (1, 1, 0, -1, 223), (1, 1, 0, 1, 223),
    (0, 1, -2, -1, -220), (2, 1, -1, -1, -220), (1, 0, 1, 1, -185), (2, -1, -2, -1, 181),
    (0, 1, 2, 1, -177), (4, 0, -2, -1, 176), (4, -1, -1, -1, 166), (1, 0, 1, -1, -164),
    (4, 0, 1, -1, 132), (1, 0, -1, -1, -119), (4, -1, 0, -1, 115), (2, -2, 0, 1, 107),
)


def _centuries(jde: float) -> float:
    return (jde - 2451545.0) / 36525


def nutation(jde: float) -> tuple[float, float]:
    """Nutation in longitude and the true obliquity, in degrees (Meeus 22, main terms)."""
    T = _centuries(jde)
    omega = math.radians(125.04452 - 1934.136261 * T)
    L = math.radians(280.4665 + 36000.7698 * T)
    Lp = math.radians(218.3165 + 481267.8813 * T)
    dpsi = (-17.20 * math.sin(omega) - 1.32 * math.sin(2 * L) - 0.23 * math.sin(2 * Lp) + 0.21 * math.sin(2 * omega)) / 3600
    deps = (9.20 * math.cos(omega) + 0.57 * math.cos(2 * L) + 0.10 * math.cos(2 * Lp) - 0.09 * math.cos(2 * omega)) / 3600
    eps0 = 23.4392911 - (46.8150 * T + 0.00059 * T ** 2 - 0.001813 * T ** 3) / 3600
    return dpsi, eps0 + deps


def moon(jde: float) -> tuple[float, float, float]:
    """The Moon's apparent geocentric longitude and latitude (degrees) and distance (km)."""
    T = _centuries(jde)
    Lp = 218.3164477 + 481267.88123421 * T - 0.0015786 * T ** 2 + T ** 3 / 538841 - T ** 4 / 65194000
    D = 297.8501921 + 445267.1114034 * T - 0.0018819 * T ** 2 + T ** 3 / 545868 - T ** 4 / 113065000
    M = 357.5291092 + 35999.0502909 * T - 0.0001536 * T ** 2 + T ** 3 / 24490000
    Mp = 134.9633964 + 477198.8675055 * T + 0.0087414 * T ** 2 + T ** 3 / 69699 - T ** 4 / 14712000
    F = 93.2720950 + 483202.0175233 * T - 0.0036539 * T ** 2 - T ** 3 / 3526000 + T ** 4 / 863310000
    A1, A2, A3 = 119.75 + 131.849 * T, 53.09 + 479264.290 * T, 313.45 + 481266.484 * T
    E = 1 - 0.002516 * T - 0.0000074 * T ** 2
    r = math.radians
    sl = sr = sb = 0.0
    for d, m, mp, f, cl, cr in LONGITUDE_DISTANCE:
        angle = r(d * D + m * M + mp * Mp + f * F)
        scale = E ** abs(m)
        sl += cl * scale * math.sin(angle)
        sr += cr * scale * math.cos(angle)
    for d, m, mp, f, cb in LATITUDE:
        sb += cb * E ** abs(m) * math.sin(r(d * D + m * M + mp * Mp + f * F))
    sl += 3958 * math.sin(r(A1)) + 1962 * math.sin(r(Lp - F)) + 318 * math.sin(r(A2))
    sb += (-2235 * math.sin(r(Lp)) + 382 * math.sin(r(A3)) + 175 * math.sin(r(A1 - F)) + 175 * math.sin(r(A1 + F))
           + 127 * math.sin(r(Lp - Mp)) - 115 * math.sin(r(Lp + Mp)))
    dpsi, _ = nutation(jde)
    return (Lp + sl / 1e6 + dpsi) % 360, sb / 1e6, 385000.56 + sr / 1000


def sun(jde: float) -> tuple[float, float]:
    """The Sun's apparent longitude (degrees) and distance (AU) (Meeus 25, low precision)."""
    T = _centuries(jde)
    L0 = 280.46646 + 36000.76983 * T + 0.0003032 * T ** 2
    M = math.radians(357.52911 + 35999.05029 * T - 0.0001537 * T ** 2)
    e = 0.016708634 - 0.000042037 * T - 0.0000001267 * T ** 2
    C = ((1.914602 - 0.004817 * T - 0.000014 * T ** 2) * math.sin(M) + (0.019993 - 0.000101 * T) * math.sin(2 * M)
         + 0.000289 * math.sin(3 * M))
    nu = M + math.radians(C)
    R = 1.000001018 * (1 - e * e) / (1 + e * math.cos(nu))
    omega = math.radians(125.04 - 1934.136 * T)
    return (L0 + C - 0.00569 - 0.00478 * math.sin(omega)) % 360, R


def equatorial(longitude: float, latitude: float, obliquity: float) -> tuple[float, float]:
    """Right ascension and declination, in degrees."""
    lam, beta, eps = map(math.radians, (longitude, latitude, obliquity))
    ra = math.atan2(math.sin(lam) * math.cos(eps) - math.tan(beta) * math.sin(eps), math.cos(lam))
    dec = math.asin(math.sin(beta) * math.cos(eps) + math.cos(beta) * math.sin(eps) * math.sin(lam))
    return math.degrees(ra) % 360, math.degrees(dec)


def sidereal(jd_ut: float) -> float:
    """Greenwich mean sidereal time, in degrees (Meeus 12)."""
    T = (jd_ut - 2451545.0) / 36525
    return (280.46061837 + 360.98564736629 * (jd_ut - 2451545.0) + 0.000387933 * T * T - T ** 3 / 38710000) % 360


def elongation(jde: float) -> float:
    """The Moon's geocentric angular distance from the Sun, in degrees."""
    lm, bm, _ = moon(jde)
    ls, _ = sun(jde)
    return math.degrees(math.acos(math.cos(math.radians(bm)) * math.cos(math.radians(lm - ls))))


def conjunction(near: float) -> float:
    """The JDE near *near* when the Moon's longitude meets the Sun's."""
    jde = near
    for _ in range(30):
        lm, _, _ = moon(jde)
        ls, _ = sun(jde)
        error = (lm - ls + 180) % 360 - 180
        jde -= error / 12.19
        if abs(error) < 1e-7:
            break
    return jde


def verify() -> int:
    sys.path.insert(0, __file__.rsplit("/", 1)[0])
    from lunisolar import new_moon

    worst = 0.0
    for k in range(-1236, 1237):          # 1900 to 2100
        ch49 = new_moon(k)
        worst = max(worst, abs(conjunction(ch49) - ch49))
    print(f"conjunctions against ch. 49's new moons, 1900-2100: worst {worst * 1440:.2f} minutes apart")
    return 0 if worst < CONJUNCTION_TOLERANCE else 1


if __name__ == "__main__":
    sys.exit(verify())

"""navml.calendars: the arithmetic calendars a CalendarView can be in."""

from __future__ import annotations

import datetime
import random

import pytest

from navkit import i18n
from navkit.bidi import display_width
from navkit.i18n import languages, register_package
from navml.calendars import GREGORIAN, SYSTEMS, easter, orthodox_easter, system

D = datetime.date



def catalogues() -> None:
    """Both layers' catalogues, which the application registers when it
    starts (and every test begins without)."""
    register_package("navml.locales")
    register_package("navigator.locales")


#: Every language, read at collection.
catalogues()
LANGUAGES = ["en", *sorted(code for code in languages() if code != "en")]


@pytest.mark.parametrize(("key", "day", "expected"), [
    # Rosh Hashanah 5787; Purim 5786 (a common year's Adar) and 5787 (a leap
    # year's Adar II, its seventh month from Tishri).
    ("hebrew", D(2026, 9, 12), (5787, 1, 1)),
    ("hebrew", D(2026, 3, 3), (5786, 6, 14)),
    ("hebrew", D(2027, 3, 23), (5787, 7, 14)),
    ("hebrew", D(2026, 10, 30), (5787, 2, 19)),
    # Nowruz 1404 and 1405, and the last day of the leap year 1403.
    ("persian", D(2025, 3, 21), (1404, 1, 1)),
    ("persian", D(2026, 3, 21), (1405, 1, 1)),
    ("persian", D(2025, 3, 20), (1403, 12, 30)),
    # 1 Chaitra 1948, and 1946's in a Gregorian leap year.
    ("indian", D(2026, 3, 22), (1948, 1, 1)),
    ("indian", D(2024, 3, 21), (1946, 1, 1)),
    # Enkutatash: 11 September, 12 in the year before a Gregorian leap year.
    ("ethiopian", D(2026, 9, 11), (2019, 1, 1)),
    ("ethiopian", D(2027, 9, 12), (2020, 1, 1)),
    ("coptic", D(2026, 9, 11), (1743, 1, 1)),
    # The Orthodox Christmas.
    ("julian", D(2026, 1, 7), (2025, 12, 25)),
    # 1 Ramadan 1447, on the day Umm al-Qura began it; and 1 Muharram 1446,
    # a day after Umm al-Qura's 7 July -- the tabular calendar's day either side.
    ("islamic", D(2026, 2, 18), (1447, 9, 1)),
    ("islamic", D(2024, 7, 8), (1446, 1, 1)),
    # Bangladesh's Bengali calendar: Pohela Boishakh 1433, and the days the
    # 2019 revision fixed -- Victory Day 1 Poush, 21 February 8 Falgun, 26
    # March 12 Choitro -- in a common year and a leap one.
    ("bengali", D(2026, 4, 14), (1433, 1, 1)),
    ("bengali", D(2026, 12, 16), (1433, 9, 1)),
    ("bengali", D(2027, 2, 21), (1433, 11, 8)),
    ("bengali", D(2028, 2, 21), (1434, 11, 8)),
    ("bengali", D(2028, 3, 26), (1434, 12, 12)),
    # Umm al-Qura: 1 Muharram 1446, Eid al-Fitr 1446, 1 Ramadan 1447, and the
    # table's first and last months.
    ("ummalqura", D(2024, 7, 7), (1446, 1, 1)),
    ("ummalqura", D(2025, 3, 30), (1446, 10, 1)),
    ("ummalqura", D(2026, 2, 18), (1447, 9, 1)),
    ("ummalqura", D(1937, 3, 14), (1356, 1, 1)),
    ("ummalqura", D(2077, 11, 16), (1500, 12, 30)),
])
def test_known_days(key, day, expected):
    assert SYSTEMS[key].from_date(day) == expected
    assert SYSTEMS[key].to_date(*expected) == day


@pytest.mark.parametrize("key", list(SYSTEMS))
def test_every_day_it_knows_goes_there_and_back(key):
    calendar = SYSTEMS[key]
    first, last = calendar.span()
    rng = random.Random(key)
    days = [*range(first, first + 800), *range(last - 800, last + 1), *rng.sample(range(first, last), 5000)]
    for fixed in days:
        year, month, day = calendar.from_fixed(fixed)
        assert 1 <= month <= calendar.months_in_year(year)
        assert 1 <= day <= calendar.days_in_month(year, month)
        assert calendar.to_fixed(year, month, day) == fixed


@pytest.mark.parametrize("key", list(SYSTEMS))
def test_a_year_is_its_months(key):
    calendar = SYSTEMS[key]
    lowest, highest = calendar.years()
    for year in range(max(1, lowest, 2000 - 78), min(highest, 2099)):
        length = sum(calendar.days_in_month(year, month) for month in range(1, calendar.months_in_year(year) + 1))
        assert calendar.to_fixed(year + 1, 1, 1) - calendar.to_fixed(year, 1, 1) == length


@pytest.mark.parametrize("code", LANGUAGES)
@pytest.mark.parametrize("key", list(SYSTEMS))
def test_every_month_and_year_fits_between_the_arrows_in_every_language(key, code):
    # The title row has 16 cells between its arrows and a blank inside each:
    # the month's name, a blank, the year as the calendar writes it.
    catalogues()
    i18n.LOCALE.code = code
    calendar = SYSTEMS[key]
    years = {"hebrew": (5784, 5787), "chinese": (2025, 2033), "korean": (2025, 2033), "vietnamese": (2025, 2033),
             "japanese": (1989, 2019, 2026),
             "roc": (1900, 2026)}.get(key)
    for year in years or (calendar.from_date(D(2026, 6, 1))[0],):
        for month in range(1, calendar.months_in_year(year) + 1):
            for number in (1, calendar.days_in_month(year, month)):
                month_name, written = calendar.title(calendar.to_date(year, month, number), 16)
                assert display_width(f"{month_name} {written}") <= 16, (month_name, written)


def test_hebrew_leap_years_have_adar_i_and_ii():
    hebrew = SYSTEMS["hebrew"]
    assert hebrew.months_in_year(5787) == 13 and hebrew.months_in_year(5786) == 12
    assert hebrew.month_names(5787)[5:7] == ["Adar I", "Adar II"]
    assert hebrew.month_names(5786)[5] == "Adar"


def test_a_year_on_keeps_the_month_by_its_name():
    hebrew = SYSTEMS["hebrew"]
    # Purim in a common year, a year on, is Purim of Adar II.
    assert hebrew.add_years(D(2026, 3, 3), 1) == D(2027, 3, 23)
    assert hebrew.add_years(D(2027, 3, 23), 1) == hebrew.to_date(5788, 6, 14)
    # Tishri to Tishri.
    assert hebrew.from_date(hebrew.add_years(D(2026, 9, 12), 1)) == (5788, 1, 1)


def test_months_turn_through_a_thirteenth():
    ethiopian = SYSTEMS["ethiopian"]
    nehase = ethiopian.to_date(2018, 12, 30)
    assert ethiopian.from_date(ethiopian.add_months(nehase, 1)) == (2018, 13, 5)
    assert ethiopian.from_date(ethiopian.add_months(nehase, 2)) == (2019, 1, 30)
    assert GREGORIAN.add_months(D(2024, 1, 31), 1) == D(2024, 2, 29)


def test_past_the_years_a_date_holds_is_refused():
    with pytest.raises(ValueError):
        GREGORIAN.add_months(D(9999, 12, 1), 1)
    with pytest.raises(ValueError):
        SYSTEMS["hebrew"].add_years(D(1, 1, 1), -1)


def test_easter_both_ways_and_the_julian_notes_them():
    assert (easter(2026), orthodox_easter(2026)) == (D(2026, 4, 5), D(2026, 4, 12))
    assert easter(2025) == orthodox_easter(2025) == D(2025, 4, 20)
    assert easter(2024) == D(2024, 3, 31) and orthodox_easter(2024) == D(2024, 5, 5)
    julian = SYSTEMS["julian"]
    assert julian.note(D(2026, 4, 12)) == "Easter (Orthodox)"
    assert julian.note(D(2025, 4, 20)) == "Easter (Orthodox), Easter (Western)"
    assert julian.note(D(2026, 4, 13)) == ""


def test_a_day_is_spelled_and_an_unknown_key_is_the_gregorian():
    assert SYSTEMS["hebrew"].spell(D(2026, 10, 30)) == "19 Heshvan 5787"
    assert SYSTEMS["persian"].spell(D(2026, 10, 30)) == "8 Aban 1405"
    assert system("klingon") is GREGORIAN
    assert SYSTEMS["hebrew"].name() == "Hebrew" and SYSTEMS["hebrew"].caption() == "~H~ebrew"
    catalogues()
    i18n.LOCALE.code = "ja"
    assert SYSTEMS["hebrew"].name() == "ヘブライ暦"
    assert SYSTEMS["hebrew"].spell(D(2026, 10, 30)) == "5787年ヘシュバン19日"


@pytest.mark.parametrize(("day", "expected"), [
    # New Year's days, the first and last years the tables hold among them.
    (D(1901, 2, 19), (1901, 1, 1, False)),
    (D(2000, 2, 5), (2000, 1, 1, False)),
    (D(2026, 2, 17), (2026, 1, 1, False)),
    (D(2099, 1, 21), (2099, 1, 1, False)),
    # Leap months: the 2nd of 2023, the 6th of 2025, the 11th of 2033.
    (D(2023, 3, 22), (2023, 2, 1, True)),
    (D(2025, 7, 25), (2025, 6, 1, True)),
    (D(2033, 12, 22), (2033, 11, 1, True)),
    # The Mid-Autumn Festival of 2026.
    (D(2026, 9, 25), (2026, 8, 15, False)),
])
def test_chinese_known_days(day, expected):
    chinese = SYSTEMS["chinese"]
    # (year, month's number, day, leap)
    year, month, number = chinese.from_date(day)
    counted, leap = chinese.number(year, month)
    assert (year, counted, number, leap) == expected


def test_chinese_knows_only_the_tables_years():
    chinese = SYSTEMS["chinese"]
    first, last = chinese.span()
    assert D.fromordinal(first) == D(1901, 2, 19) and chinese.years() == (1901, 2099)
    assert chinese.holds(D(2026, 1, 1)) and not chinese.holds(D(1901, 2, 18))
    with pytest.raises(ValueError):
        chinese.from_date(D(1900, 6, 1))
    with pytest.raises(ValueError):
        chinese.add_years(D(2099, 6, 1), 1)


def test_chinese_leap_months_are_named_and_kept_a_year_on():
    chinese = SYSTEMS["chinese"]
    assert chinese.months_in_year(2025) == 13 and chinese.months_in_year(2026) == 12
    assert chinese.month_names(2025)[5:8] == ["Month 6", "Leap 6", "Month 7"]
    # The leap 6th of 2025 a year on is the 6th of 2026, which has no leap.
    assert chinese.from_date(chinese.add_years(D(2025, 7, 25), 1)) == (2026, 6, 1)
    # The 8th of 2025 (after its leap month) is the 8th of 2026 too.
    year, month, _ = chinese.from_date(chinese.add_years(D(2025, 9, 22), 1))
    assert chinese.number(year, month) == (8, False)


def test_chinese_years_are_named_in_the_cycle():
    chinese = SYSTEMS["chinese"]
    assert chinese.note(D(2026, 2, 17)) == "Spring Festival, Bǐng-Wǔ, year of the Horse"
    assert chinese.note(D(2025, 7, 25)) == "Yǐ-Sì, year of the Snake"
    assert chinese.note(D(1984, 6, 1)) == "Jiǎ-Zǐ, year of the Rat"


def test_the_chinese_table_is_consistent():
    import subprocess
    import sys
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent
    done = subprocess.run([sys.executable, "tools/chinese_calendar.py", "--check"], cwd=root,
                          capture_output=True, text=True)
    assert done.returncode == 0, done.stderr


def test_umm_al_qura_knows_only_its_table_s_years():
    ummalqura = SYSTEMS["ummalqura"]
    assert ummalqura.years() == (1356, 1500)
    assert not ummalqura.holds(D(1937, 3, 13)) and not ummalqura.holds(D(2077, 11, 17))
    with pytest.raises(ValueError):
        ummalqura.add_months(D(2077, 11, 1), 1)
    # Its months are the tabular calendar's names.
    assert ummalqura.month_names(1447) == SYSTEMS["islamic"].month_names(1447)


def test_the_umm_al_qura_table_is_consistent():
    import subprocess
    import sys
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent
    done = subprocess.run([sys.executable, "tools/umm_al_qura.py", "--check"], cwd=root,
                          capture_output=True, text=True)
    assert done.returncode == 0, done.stderr


@pytest.mark.parametrize(("day", "long", "short"), [
    (D(1989, 1, 7), "Shōwa 64", "S64"),
    (D(1989, 1, 8), "Heisei 1", "H1"),
    (D(2019, 4, 30), "Heisei 31", "H31"),
    (D(2019, 5, 1), "Reiwa 1", "R1"),
    (D(1912, 7, 30), "Taishō 1", "T1"),
    (D(1873, 1, 1), "Meiji 6", "M6"),
])
def test_japanese_years_are_counted_by_era(day, long, short):
    japanese = SYSTEMS["japanese"]
    assert (japanese.year_text(day), japanese.year_text(day, short=True)) == (long, short)


def test_japanese_eras_begin_with_the_gregorian_calendar_in_japan():
    japanese = SYSTEMS["japanese"]
    assert japanese.years() == (1873, 9999) and not japanese.holds(D(1872, 12, 31))
    # The year list names a year by the era it ends in.
    assert japanese.year_label(2019) == "Reiwa 1 (2019)"
    # Too long for the top row, the year is written short.
    assert japanese.title(D(2019, 9, 1), 16) == ("September", "R1")
    assert japanese.title(D(2019, 5, 1), 16) == ("May", "Reiwa 1")


def test_thai_and_roc_years():
    thai, roc = SYSTEMS["thai"], SYSTEMS["roc"]
    assert thai.year_text(D(2026, 1, 1)) == "2569 BE" and thai.year_label(2026) == "2569 BE (2026)"
    assert roc.year_text(D(2026, 1, 1)) == "ROC 115" and roc.year_text(D(1912, 1, 1)) == "ROC 1"
    assert roc.year_text(D(1911, 12, 31)) == "1 before ROC" and roc.year_text(D(1911, 1, 1), short=True) == "-1"
    # Their months and days are the Gregorian's.
    assert thai.from_date(D(2026, 10, 30)) == roc.from_date(D(2026, 10, 30)) == (2026, 10, 30)


def test_the_language_s_own_calendar():
    from navigator.lib.config import country
    from navigator.settings import CountryData

    section = CountryData()
    for code, calendar in (("ja", "japanese"), ("th", "thai"), ("bn_BD", "bengali"), ("zh_TW", "roc"),
                           ("zh_CN", "chinese"), ("ko", "korean"), ("vi_VN", "vietnamese"), ("ne", "nepali"), ("tr", "diyanet"), ("ms", "mabims_my"), ("id", "mabims_id"), ("my", "burmese"), ("bo", "tibetan"), ("km", "chhankitek"), ("fa_AF", "afghan"), ("fa", "persian"), ("lv", "gregorian")):
        i18n.LOCALE.code = code
        assert country.calendar_system(section) == calendar, code


@pytest.mark.parametrize(("key", "day", "china"), [
    # Where each parts from China's New Year: Vietnam's Tết of 1968 (the
    # North's, a day before), of 1985 (a month before) and of 2007; Korea's
    # Seollal of 1997 and 2027, a day after.
    ("vietnamese", D(1968, 1, 29), D(1968, 1, 30)),
    ("vietnamese", D(1985, 1, 21), D(1985, 2, 20)),
    ("vietnamese", D(2007, 2, 17), D(2007, 2, 18)),
    ("korean", D(1997, 2, 8), D(1997, 2, 7)),
    ("korean", D(2027, 2, 7), D(2027, 2, 6)),
])
def test_korean_and_vietnamese_new_years(key, day, china):
    calendar, chinese = SYSTEMS[key], SYSTEMS["chinese"]
    assert calendar.from_date(day)[1:] == (1, 1) and chinese.from_date(china)[1:] == (1, 1)
    assert chinese.from_date(day)[1:] != (1, 1)


def test_vietnam_kept_china_s_calendar_until_1967():
    from navml import chinese_data, vietnamese_data

    assert vietnamese_data.YEARS[:1967 - 1901] == chinese_data.YEARS[:1967 - 1901]


def test_korean_and_vietnamese_name_the_year_and_new_year():
    assert SYSTEMS["korean"].note(D(2027, 2, 7)) == "Seollal, Dīng-Wèi, year of the Goat"
    assert SYSTEMS["vietnamese"].note(D(2023, 6, 1)) == "Guǐ-Mǎo, year of the Cat"
    assert SYSTEMS["vietnamese"].note(D(2021, 6, 1)) == "Xīn-Chǒu, year of the Buffalo"
    assert SYSTEMS["vietnamese"].note(D(2026, 2, 17)).startswith("Tết, ")


def test_the_computed_tables_are_consistent():
    import subprocess
    import sys
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent
    done = subprocess.run([sys.executable, "tools/lunisolar.py", "--check"], cwd=root, capture_output=True, text=True)
    assert done.returncode == 0, done.stderr


@pytest.mark.parametrize(("day", "expected"), [
    # Nepali New Year 2082 and 2083, Maghe Sankranti 2083, and the table's first day.
    (D(2025, 4, 14), (2082, 1, 1)),
    (D(2026, 4, 14), (2083, 1, 1)),
    (D(2027, 1, 15), (2083, 10, 1)),
    (D(1918, 4, 13), (1975, 1, 1)),
])
def test_bikram_sambat_known_days(day, expected):
    assert SYSTEMS["nepali"].from_date(day) == expected


def test_bikram_sambat_says_which_years_are_computed():
    nepali = SYSTEMS["nepali"]
    assert nepali.years() == (1975, 2156)
    assert nepali.note(D(2026, 10, 30)) == ""
    assert nepali.note(D(2027, 6, 1)).startswith("Computed")
    assert all(29 <= nepali.days_in_month(2083, month) <= 32 for month in range(1, 13))


def test_the_bikram_sambat_table_is_consistent():
    import subprocess
    import sys
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent
    done = subprocess.run([sys.executable, "tools/bikram_sambat.py", "--check"], cwd=root,
                          capture_output=True, text=True)
    assert done.returncode == 0, done.stderr


@pytest.mark.parametrize(("year", "naw_ruz", "ayyam_i_ha"), [
    # From the World Centre's table: 2026 the close one (Naw-Rúz the 21st),
    # Ayyám-i-Há 25 February-1 March 2026 (five days) and 26 February-1
    # March 2027 (four).
    (172, D(2015, 3, 21), 4),
    (182, D(2025, 3, 20), 5),
    (183, D(2026, 3, 21), 4),
    (221, D(2064, 3, 20), 4),
    # Before 172 BE, 21 March in the West.
    (171, D(2014, 3, 21), 4),
    (1, D(1844, 3, 21), 4),
])
def test_badi_naw_ruz_and_ayyam_i_ha(year, naw_ruz, ayyam_i_ha):
    badi = SYSTEMS["badi"]
    assert badi.to_date(year, 1, 1) == naw_ruz
    assert badi.days_in_month(year, 19) == ayyam_i_ha
    assert badi.months_in_year(year) == 20 and badi.month_names(year)[18:] == ["Ayyám-i-Há", "ʿAláʼ"]


def test_badi_notes_naw_ruz_and_computed_years():
    badi = SYSTEMS["badi"]
    assert badi.note(D(2026, 3, 21)) == "Naw-Rúz"
    assert badi.note(D(2026, 6, 1)) == ""
    assert badi.note(D(2070, 6, 1)).startswith("Computed")
    assert badi.years() == (1, 257)


def test_the_badi_table_is_consistent():
    import subprocess
    import sys
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent
    done = subprocess.run([sys.executable, "tools/badi.py", "--check"], cwd=root, capture_output=True, text=True)
    assert done.returncode == 0, done.stderr


@pytest.mark.parametrize(("key", "day", "expected"), [
    # Malaysia's Awal Muharram 1443 (the first month by Neo-MABIMS) and 1 Ramadan
    # 1447, a day after Saudi Arabia's.
    ("mabims_my", D(2021, 8, 10), (1443, 1, 1)),
    ("mabims_my", D(2026, 2, 19), (1447, 9, 1)),
    ("ummalqura", D(2026, 2, 18), (1447, 9, 1)),
    # Turkey's: van Gent's table begins with Muharram 1318.
    ("diyanet", D(1900, 5, 1), (1318, 1, 1)),
])
def test_published_and_computed_hijri_months(key, day, expected):
    assert SYSTEMS[key].from_date(day) == expected


@pytest.mark.parametrize("key", ["diyanet", "mabims_id", "mabims_my"])
def test_a_criterion_calendar_says_which_months_are_computed(key):
    calendar = SYSTEMS[key]
    first, last = calendar.span()
    assert calendar.note(D.fromordinal(first)) == ""
    assert calendar.note(D.fromordinal(last)).startswith("Computed")
    assert calendar.years()[1] >= 1524
    assert calendar.month_names(1447) == SYSTEMS["islamic"].month_names(1447)


def test_the_criterion_tables_are_consistent():
    import subprocess
    import sys
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent
    done = subprocess.run([sys.executable, "tools/hijri_criteria.py", "--check"], cwd=root, capture_output=True,
                          text=True)
    assert done.returncode == 0, done.stderr


@pytest.mark.parametrize(("day", "expected", "note"), [
    # Myanmar New Year's Day 1386 and 1387 ME, and the full moons of Kason (Vesak), Waso and
    # Thadingyut in 2024.
    (D(2024, 4, 17), (1386, 1, 9), "Myanmar New Year's Day, 1386 ME"),
    (D(2025, 4, 17), (1387, 1, 20), "Myanmar New Year's Day, 1387 ME"),
    (D(2024, 5, 22), (1386, 2, 15), "Full moon"),
    (D(2024, 7, 20), (1386, 4, 15), "Full moon"),
    (D(2024, 10, 17), (1386, 7, 15), "Full moon"),
])
def test_burmese_known_days(day, expected, note):
    burmese = SYSTEMS["burmese"]
    assert burmese.from_date(day) == expected and burmese.note(day) == note


def test_burmese_years_are_354_384_or_385_days_with_a_second_waso_in_a_watat_year():
    burmese = SYSTEMS["burmese"]
    for year in range(1262, 1462):
        total = sum(burmese.days_in_month(year, m) for m in range(1, burmese.months_in_year(year) + 1))
        assert total in (354, 384, 385)
        assert (total > 354) == ("Second Waso" in burmese.month_names(year))


@pytest.mark.parametrize(("day", "year", "element_animal"), [
    # Losar 2019 (the first day of a doubled first month) to 2026.
    (D(2019, 2, 5), 2146, "Earth Pig"),
    (D(2020, 2, 24), 2147, "Iron Rat"),
    (D(2022, 3, 3), 2149, "Water Tiger"),
    (D(2024, 2, 10), 2151, "Wood Dragon"),
    (D(2026, 2, 18), 2153, "Fire Horse"),
])
def test_tibetan_losar(day, year, element_animal):
    tibetan = SYSTEMS["tibetan"]
    assert tibetan.from_date(day) == (year, 1, 1)
    assert tibetan.note(day) == f"Losar, {element_animal} year"


def test_tibetan_days_are_skipped_and_doubled():
    tibetan = SYSTEMS["tibetan"]
    start = D(2026, 1, 19)          # the 12th month of 2152
    labels = [tibetan.day_label(start + datetime.timedelta(days=i)) for i in range(30)]
    assert 13 not in labels and labels.count(25) == 2
    assert "Day 13 is skipped" in tibetan.note(D(2026, 1, 30))
    assert "Doubled day" in tibetan.note(D(2026, 2, 12))
    assert tibetan.month_names(2146)[:2] == ["Leap 1", "Month 1"]


@pytest.mark.parametrize(("day", "expected", "note"), [
    # Cambodia's and Thailand's holy days 2024-2025, all at the same full moons.
    (D(2024, 2, 24), (2567, 11, 15), "Full moon, Magha Puja"),
    (D(2024, 5, 22), (2568, 1, 15), "Full moon, Vesak"),
    (D(2024, 7, 20), (2568, 3, 15), "Full moon, Asalha Puja"),
    (D(2025, 5, 11), (2569, 1, 15), "Full moon, Vesak"),
    # In a year whose Asadh is doubled, Thailand and Laos keep them a month later: Cambodia's Visak
    # Bochea of 2023 on 4 May, Thailand's Visakha Bucha on 3 June; 2026's on 1 and 31 May.
    (D(2023, 5, 4), (2567, 1, 15), "Full moon, Vesak (Cambodia)"),
    (D(2023, 6, 3), (2567, 2, 15), "Full moon, Vesak (Thailand, Laos)"),
    (D(2026, 3, 3), (2569, 11, 15), "Full moon, Magha Puja (Thailand, Laos)"),
    (D(2026, 7, 29), (2570, 4, 15), "Full moon, Asalha Puja"),
])
def test_chhankitek_holy_days(day, expected, note):
    chhankitek = SYSTEMS["chhankitek"]
    assert chhankitek.from_date(day) == expected and chhankitek.note(day) == note


def test_chhankitek_years_double_asadh_or_lengthen_jesth():
    chhankitek = SYSTEMS["chhankitek"]
    assert chhankitek.month_names(2570)[2:4] == ["Pathamasadh", "Tutiyasadh"]
    for year in range(2445, 2643):
        total = sum(chhankitek.days_in_month(year, m) for m in range(1, chhankitek.months_in_year(year) + 1))
        assert total in (354, 355, 384)


def test_afghan_solar_hijri_is_the_persian_with_its_zodiac_months():
    afghan, persian = SYSTEMS["afghan"], SYSTEMS["persian"]
    assert afghan.from_date(D(2026, 10, 30)) == persian.from_date(D(2026, 10, 30)) == (1405, 8, 8)
    assert afghan.spell(D(2026, 10, 30)) == "8 Aqrab 1405"
    assert afghan.month_names(1405)[0] == "Hamal"

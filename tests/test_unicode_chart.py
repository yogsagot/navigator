"""The *Character Table*: every Unicode character, by block, category, Nerd set or name."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from conftest import IDLE, FakeTerminal, Until, run_app
from navkit.application import Application
from navkit.events import DoubleClickEvent, KeyEvent
from navkit.glyphs import GLYPHS_ASCII, GLYPHS_NERD, GLYPHS_UNICODE
from navkit.screen import ScreenBuffer, char_width
from navkit.widget import Widget

from navigator.lib.utilities import unicode_table
from navigator.widgets.shell.unicode_chart import UnicodeChart, pick_character
from navigator.widgets.shell.unicode_chart import unicode_chart as module

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def index():
    return unicode_table.build_index(nerd=True)


#: Waits for a search typed to be shown.
SEARCHED = Until(lambda a: a.modal is not None and a.modal.searched == a.modal.search.value.strip() != ""
                 and a.modal.grid.caption == "Search results", timeout=5.0)


@pytest.fixture(autouse=True)
def fresh(monkeypatch):
    monkeypatch.setattr(module, "_last", {"grouping": module.BLOCKS, "group": "block:Basic Latin", "code": 0x70})
    monkeypatch.setattr(module, "_indexes", {})


# -- the tables ------------------------------------------------------------------------------


def test_the_shipped_tables_are_current():
    result = subprocess.run([sys.executable, str(ROOT / "tools" / "unicode_tables.py"), "--check"],
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_blocks_name_where_a_character_is():
    assert unicode_table.block_of(0x2502) == "Box Drawing"
    assert unicode_table.block_of(0x41) == "Basic Latin"
    names = [c.name for c in unicode_table.block_categories()]
    assert "Box Drawing" in names and not any("Private Use" in n or "Surrogate" in n for n in names)


def test_a_block_newer_than_this_python_is_not_listed():
    """One ``Blocks.txt`` ships to every supported Python: the newest one's.
    On an older Python a block with nothing assigned yet stays out."""
    assert all(unicode_table.characters(c, None) for c in unicode_table.block_categories())


def test_a_block_lists_only_assigned_characters():
    latin = next(c for c in unicode_table.block_categories() if c.name == "Basic Latin")
    assert unicode_table.characters(latin, None) == list(range(0x80))
    greek = next(c for c in unicode_table.block_categories() if c.name == "Greek and Coptic")
    assert 0x378 not in unicode_table.characters(greek, None)  # unassigned


def test_categories_and_nerd_sets_wait_for_the_index(index):
    symbols = next(c for c in unicode_table.general_categories() if c.key == "Sm")
    assert unicode_table.characters(symbols, None) is None
    assert 0x2211 in unicode_table.characters(symbols, index)  # N-ARY SUMMATION
    awesome = next(c for c in unicode_table.nerd_categories() if c.key == "fa")
    assert 0xF07B in unicode_table.characters(awesome, index)


def test_the_search_finds_by_name_and_ranks_the_phrase_first(index):
    found = unicode_table.search("light vertical", index)
    assert 0x2502 in found[:3]
    assert unicode_table.search("arrow", index)[0] == 0x2191  # UPWARDS ARROW, the shortest


def test_a_code_or_a_character_typed_is_found_first(index):
    assert unicode_table.search("U+1F600", index)[0] == 0x1F600
    assert unicode_table.search("0x2502", index)[0] == 0x2502
    assert unicode_table.search("│", index) == [0x2502]


def test_nerd_names_are_searched_only_in_the_nerd_tier(index):
    assert unicode_table.search("nf-fa-folder", index)[0] == 0xF07B
    plain = unicode_table.build_index(nerd=False)
    assert unicode_table.search("nf-fa-folder", plain) == []
    assert unicode_table.name_of(0xF07B, index.nerd) == "nf-fa-folder"


def test_the_description(index):
    first, second = unicode_table.describe(0x2502, index.nerd)
    assert first == "U+2502  │  BOX DRAWINGS LIGHT VERTICAL"
    assert second == "So Symbol, other  ·  Dec 9474  ·  UTF-8 E2 94 82  ·  Box Drawing"
    assert "Font Awesome" in unicode_table.describe(0xF07B, index.nerd)[1]


def test_what_a_cell_draws():
    assert unicode_table.display(0x09) == "␉"
    assert unicode_table.display(0x301) == "◌́"
    assert unicode_table.display(0x200D) == "⬚"  # ZERO WIDTH JOINER
    assert unicode_table.display(0x41) == "A"


def test_a_cell_with_a_combining_mark_measures_as_its_base():
    assert char_width("◌́") == 1
    assert char_width("字") == 2


def test_recent_keeps_the_newest_first_and_is_capped(monkeypatch):
    monkeypatch.setattr(unicode_table, "RECENT_LIMIT", 3)
    for code in (1, 2, 3, 2, 4):
        unicode_table.remember(code)
    assert unicode_table.recent() == [4, 2, 3]


# -- the dialog ------------------------------------------------------------------------------


def run(*actions, glyphs=GLYPHS_UNICODE, size=(80, 25)):
    """The chart, then *actions*; what it answered (``"open"`` if still up), and the chart."""
    app = Application(Widget(), terminal=FakeTerminal(*size))
    chart = UnicodeChart(glyphs=glyphs)
    jobs = []
    run_app(app, [lambda a: jobs.append(a.spawn(chart.execute(a))), lambda a: None, *actions,
                  lambda a: None])
    job = jobs[0]
    return ("open" if job.cancelled() or not job.done() else job.result()), chart


def test_it_opens_on_p_in_basic_latin_and_describes_it():
    _, chart = run()
    assert chart.grid.code == 0x70
    assert chart.grid.caption == "Basic Latin"
    assert chart.info.text.startswith("U+0070  p  LATIN SMALL LETTER P")


def test_enter_takes_the_character_under_the_cursor():
    answer, _ = run(lambda a: a.modal.grid.focus(), KeyEvent("right"), KeyEvent("enter"))
    assert answer == "q"


def test_escape_takes_nothing():
    answer, _ = run(KeyEvent("escape"))
    assert answer is None


def test_typing_searches_and_enter_takes_the_first_found():
    answer, _ = run(lambda a: a.modal.grid.focus(), *[KeyEvent(c, c) for c in "upwards arrow"],
                    SEARCHED, KeyEvent("enter"))
    assert answer == "↑"


def test_the_results_are_the_first_group_and_clearing_the_line_drops_them():
    seen = []

    def look(a):
        chart = a.modal
        seen.append((chart.categories[0].kind, chart.grid.caption))

    run(*[KeyEvent(c, c) for c in "smiling"], SEARCHED, look,
        *[KeyEvent("backspace")] * 7, lambda a: None, look)
    assert seen[0] == ("found", "Search results")
    assert seen[1][0] == "recent"


def test_switching_to_categories_lists_the_general_categories():
    seen = []

    def look(a):
        seen.append([c.kind for c in a.modal.categories[:2]])

    run(lambda a: setattr(a.modal.grouping, "value", module.GENERAL), lambda a: None, look)
    assert seen == [["recent", "general"]]


def test_nerd_fonts_are_a_grouping_only_in_the_nerd_tier():
    assert len(UnicodeChart(glyphs=GLYPHS_UNICODE).grouping.items) == 2
    assert len(UnicodeChart(glyphs=GLYPHS_NERD).grouping.items) == 3


def test_a_double_click_takes_the_character_under_it():
    async def click(app):
        await app.modal.grid.on_double_click(DoubleClickEvent(x=1 + 3 * 2 + 1, y=2, button="left"))

    answer, chart = run(lambda a: a.spawn(click(a)))
    assert answer == chr(chart.grid.columns + 2)  # the second row, the third cell


def test_ctrl_c_copies_takes_nothing_and_remembers_it(monkeypatch):
    copied = []
    monkeypatch.setattr(Application, "copy_to_clipboard", lambda self, text, **k: copied.append(text))
    answer, _ = run(KeyEvent("c", ctrl=True))
    assert (answer, copied) == (None, ["p"])
    assert unicode_table.recent() == [0x70]


def test_the_next_chart_reopens_where_this_one_was_left():
    run(lambda a: a.modal.grid.focus(), KeyEvent("right"), KeyEvent("enter"))
    _, chart = run()
    assert chart.grid.code == 0x71


def test_a_wide_character_takes_two_columns_of_its_cell():
    _, chart = run(lambda a: a.modal.search.__setattr__("value", "U+5B57"), SEARCHED)
    grid = chart.grid
    surface = ScreenBuffer(grid.width, grid.height)
    grid.render(surface)
    assert surface.get(2, 1)[0] == "字" and surface.get(3, 1)[0] == ""


def test_the_ascii_tier_still_opens_ascii_chart():
    app = Application(Widget(), terminal=FakeTerminal(80, 25))
    jobs, seen = [], []
    run_app(app, [lambda a: jobs.append(a.spawn(pick_character(a, GLYPHS_ASCII))), lambda a: None,
                  lambda a: seen.append(a.modal.title), KeyEvent("enter"), lambda a: None])
    assert seen == ["ASCII Chart"]
    assert jobs[0].result() == "p"


# -- where it is opened from -----------------------------------------------------------------


@pytest.fixture
def nav(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    monkeypatch.setattr("navigator.widgets.shell.console.Console.start", lambda self, argv=None: None)
    (tmp_path / "text.txt").write_bytes(b"ab\n")
    return tmp_path


def navigator(path):
    from navigator.__main__ import Navigator

    return Navigator(path, path, terminal=FakeTerminal(80, 24))


def test_ctrl_b_puts_the_character_found_on_the_command_line(nav):
    app = navigator(nav)
    seen = []
    run_app(app, [KeyEvent("b", ctrl=True), lambda a: None,
                  lambda a: seen.append(a.modal.title if a.modal else None),
                  *[KeyEvent(c, c) for c in "black star"], SEARCHED, KeyEvent("enter"), lambda a: None])
    assert seen == ["Character Table"]
    assert app.shell.command_line.value == "★"


def test_ctrl_p_types_the_character_found_in_the_editor(nav):
    from navigator.settings import SETTINGS
    from navigator.widgets.editor.edit_window import EditWindow

    SETTINGS.interface.store_editor_position = False
    app = navigator(nav)
    run_app(app, [KeyEvent("end"), KeyEvent("f4"), IDLE, KeyEvent("p", ctrl=True), lambda a: None,
                  *[KeyEvent(c, c) for c in "U+1F600"], SEARCHED, KeyEvent("enter"), lambda a: None])
    window = app.shell.desktop.active_window
    assert isinstance(window, EditWindow)
    assert window.editor.document.encode() == "😀ab\n".encode()


def test_the_filter_narrows_the_groups_and_shows_the_first_left():
    seen = []

    def look(a):
        chart = a.modal
        seen.append(([c.kind for c in chart.categories], chart.grid.caption))

    def type_filter(a):
        a.modal.filter.focus()

    run(type_filter, *[KeyEvent(c, c) for c in "arrows"], lambda a: None, look)
    kinds, caption = seen[0]
    assert kinds[0] == "recent" and all(k == "block" for k in kinds[1:]) and len(kinds) > 2
    assert "Arrows" in caption


def test_the_filter_keeps_the_group_shown_when_it_matches():
    seen = []
    run(lambda a: a.modal.filter.focus(), *[KeyEvent(c, c) for c in "latin"], lambda a: None,
        lambda a: seen.append(a.modal.grid.caption))
    assert seen == ["Basic Latin"]


def test_x_empties_the_filter():
    seen = []

    async def press(a):
        await a.modal.clear_filter.press()

    run(lambda a: a.modal.filter.focus(), *[KeyEvent(c, c) for c in "zzz"], lambda a: None,
        lambda a: seen.append(len(a.modal.categories)), lambda a: a.spawn(press(a)), lambda a: None,
        lambda a: seen.append((a.modal.filter.value, len(a.modal.categories), a.modal.filter.focused)))
    assert seen[0] == 1
    assert seen[1][0] == "" and seen[1][1] > 100 and seen[1][2]


def test_escape_in_the_filter_empties_it_before_it_closes():
    seen = []
    answer, _ = run(lambda a: a.modal.filter.focus(), *[KeyEvent(c, c) for c in "zzz"], KeyEvent("escape"),
                    lambda a: seen.append((a.modal.filter.value, len(a.modal.categories) > 100)),
                    KeyEvent("escape"))
    assert seen == [("", True)]
    assert answer is None

"""Ctrl+F and Ctrl+R in the editor: the Find bar (a departure, after IntelliJ IDEA's), and
the regular expressions it brings to the search model."""

from __future__ import annotations

import pytest

from conftest import Until, run_app
from navkit.events import KeyEvent, MouseClickEvent

from navigator.lib.editor.document import Pos
from navigator.lib.editor.search import (
    SearchData,
    all_matches,
    find,
    find_in_line,
    line_matches,
    replacement,
    valid,
)

from test_editor import editor_window, files, quiet_console, screen, row_of, text_editor, typed  # noqa: F401


# -- the model ---------------------------------------------------------------------------


LINES = ["the cat", "scatter cat", "Cat dog"]


def test_a_regular_expression_matches_within_a_line():
    data = SearchData(text=r"c\w+r", regex=True)
    assert find(LINES, Pos(0, 0), data, backward=False) == (Pos(1, 1), Pos(1, 7))
    assert find_in_line("a.b", ".", 0, 3, case=False, whole=False, backward=False) == (1, 2)
    assert find_in_line("a.b", ".", 0, 3, case=False, whole=False, backward=False, regex=True) == (0, 1)


def test_a_bad_pattern_matches_nothing_and_is_not_valid():
    data = SearchData(text="(", regex=True)
    assert not valid(data)
    assert find(LINES, Pos(0, 0), data, backward=False) is None
    assert all_matches(LINES, data) == []
    assert valid(SearchData(text="("))


def test_an_empty_match_is_no_match():
    assert all_matches(LINES, SearchData(text="x*", regex=True)) == []
    assert all_matches(["ab"], SearchData(text="b*", regex=True)) == [(0, 1, 0, 2)]


def test_all_matches_counts_in_order_and_stops_at_the_limit():
    # (line, start, end_line, end): a one-line match ends on its own line.
    data = SearchData(text="cat")
    assert all_matches(LINES, data) == [(0, 4, 0, 7), (1, 1, 1, 4), (1, 8, 1, 11), (2, 0, 2, 3)]
    assert all_matches(LINES, data, limit=2) == [(0, 4, 0, 7), (1, 1, 1, 4)]
    assert all_matches(LINES, SearchData(text="cat", case=True, whole=True)) == [(0, 4, 0, 7), (1, 8, 1, 11)]
    assert line_matches("scatter cat", data) == [(1, 4), (8, 11)]


def test_a_replacement_fills_in_the_groups_of_a_pattern():
    data = SearchData(text=r"(\w)at", regex=True, new=r"<\1>")
    found = find(LINES, Pos(0, 0), data, backward=False)
    assert replacement(LINES, found, data) == "<c>"
    plain = SearchData(text="cat", new=r"<\1>")
    assert replacement(LINES, find(LINES, Pos(0, 0), plain, backward=False), plain) == r"<\1>"


# -- the bar -----------------------------------------------------------------------------


TEXT = b"one cat\ntwo Cat\ncat three\n"


@pytest.fixture(autouse=True)
def fresh_search(monkeypatch):
    from navigator.lib.editor import search

    data = search.SearchData()
    monkeypatch.setattr(search, "SEARCH", data)
    return data


def ctrl(letter: str) -> KeyEvent:
    return KeyEvent(letter, ctrl=True)


def counted(a) -> bool:
    bar = editor_window(a).find_bar
    return bar._matches is not None


def bar_of(a):
    return editor_window(a).find_bar


def test_ctrl_f_opens_the_bar_on_the_word_and_takes_the_keyboard(files):
    seen = {}
    _, editor = text_editor(files, TEXT, KeyEvent("right"), ctrl("f"), Until(counted),
                            lambda a: seen.update(value=bar_of(a).query.value,
                                                  focused=bar_of(a).query.entry.focused,
                                                  count=bar_of(a).count_text(),
                                                  query=editor_window(a).editor.highlight_query))
    assert seen["value"] == "one" and seen["focused"]
    assert seen["count"] == ("1/1", False)
    assert seen["query"].text == "one"


def test_typing_searches_from_where_the_bar_opened(files):
    seen = {}
    _, editor = text_editor(files, TEXT, KeyEvent("down"), ctrl("f"), *typed("ca"),
                            lambda a: seen.update(at=(editor_window(a).editor.line, editor_window(a).editor.col)),
                            *typed("t"), Until(counted),
                            lambda a: seen.update(count=bar_of(a).count_text()))
    # From line 1: "two Cat" first, case not matched.
    assert seen["at"] == (1, 6)
    assert (editor.line, editor.col) == (1, 7)
    assert seen["count"] == ("2/3", False)


def test_nothing_found_puts_the_cursor_back_and_says_so(files):
    seen = {}
    _, editor = text_editor(files, TEXT, KeyEvent("down"), KeyEvent("right"), ctrl("f"),
                            *typed("zebra"), Until(counted),
                            lambda a: seen.update(count=bar_of(a).count_text()))
    assert (editor.line, editor.col) == (1, 0)
    assert seen["count"] == ("No matches", True)


def test_enter_and_shift_f3_go_round_the_matches(files):
    seen = []
    note = lambda a: seen.append((editor_window(a).editor.line, editor_window(a).editor.col))  # noqa: E731
    text_editor(files, TEXT, ctrl("f"), *typed("cat"), note,
                KeyEvent("enter"), note, KeyEvent("enter"), note, KeyEvent("enter"), note,
                KeyEvent("f3", shift=True), note)
    assert seen == [(0, 7), (1, 7), (2, 3), (0, 7), (2, 3)]


def test_the_switches_narrow_the_search(files):
    seen = {}
    text_editor(files, TEXT, ctrl("f"), *typed("cat"), KeyEvent("c", alt=True), Until(counted),
                lambda a: seen.update(case=bar_of(a).count_text()),
                KeyEvent("c", alt=True), KeyEvent("r", alt=True), KeyEvent("backspace"), *typed("."),
                Until(counted), lambda a: seen.update(regex=bar_of(a).count_text()),
                *typed("("), lambda a: seen.update(bad=bar_of(a).count_text()))
    assert seen["case"] == ("1/2", False)
    assert seen["regex"] == ("1/3", False)
    assert seen["bad"] == ("Bad pattern", True)


def test_esc_closes_the_bar_then_the_window(files):
    seen = {}
    _, editor = text_editor(files, TEXT, ctrl("f"), *typed("cat"), KeyEvent("escape"),
                            lambda a: seen.update(visible=bar_of(a).visible,
                                                  focused=editor_window(a).editor.focused,
                                                  query=editor_window(a).editor.highlight_query),
                            ctrl("f"), lambda a: editor_window(a).editor.focus(),
                            KeyEvent("escape"),
                            lambda a: seen.update(again=bar_of(a).visible, window=editor_window(a)))
    assert not seen["visible"] and seen["focused"] and seen["query"] is None
    assert not seen["again"] and seen["window"] is not None


def test_the_bar_s_search_is_what_shift_f7_goes_on_with(files):
    _, editor = text_editor(files, TEXT, ctrl("f"), *typed("cat"), KeyEvent("escape"),
                            KeyEvent("f7", shift=True), lambda a: None)
    assert (editor.line, editor.col) == (1, 7)


def test_replace_one_at_a_time_each_its_own_undo(files):
    _, editor = text_editor(files, TEXT, ctrl("r"), *typed("cat"), KeyEvent("tab"), *typed("dog"),
                            KeyEvent("enter"), KeyEvent("enter"))
    assert editor.document.encode() == b"one dog\ntwo dog\ncat three\n"
    assert (editor.line, editor.col) == (2, 3)


def test_replace_all_is_one_undo_and_fills_in_groups(files):
    seen = {}
    _, editor = text_editor(files, TEXT, ctrl("r"), *typed(r"(\w)at"), KeyEvent("r", alt=True),
                            KeyEvent("tab"), *typed(r"[\1]"), KeyEvent("a", alt=True),
                            lambda a: seen.update(text=editor_window(a).editor.document.encode(),
                                                  notice=bar_of(a).count_text()),
                            KeyEvent("escape"), KeyEvent("z", ctrl=True))
    assert seen["text"] == b"one [c]\ntwo [C]\n[c] three\n"
    assert seen["notice"] == ("3 replaced", False)
    assert editor.document.encode() == TEXT


def test_every_match_on_screen_is_lit(files):
    seen = {}
    text_editor(files, TEXT, ctrl("f"), *typed("cat"), Until(counted),
                lambda a: seen.update(buffer=screen(a)))
    buffer = seen["buffer"]
    window_y = 2  # the editor's first row on a zoomed window under the menu bar
    row = row_of(buffer, window_y + 1)
    assert "two Cat" in row
    column = row.index("Cat")
    assert buffer.get(column, window_y + 1)[1].underline
    assert "1/3" in row
    assert "Aa W .*" in row


def test_clicking_a_switch_turns_it_on(files):
    seen = {}

    def click(a):
        bar = bar_of(a)
        ox, oy = bar.offset()
        x, y = ox + bar.x + 1 + max(4, bar.width - 29) + 4, oy + bar.y + 1
        a.post_event(MouseClickEvent(x=x, y=y, button="left", action="press"))
        a.post_event(MouseClickEvent(x=x, y=y, button="left", action="release"))

    text_editor(files, TEXT, ctrl("f"), *typed("cat"), click, lambda a: None,
                lambda a: seen.update(whole=bar_of(a).whole))
    assert seen["whole"]


def test_f7_still_opens_dn_s_dialog(files):
    from navigator.widgets.editor.find_dialog import FindDialog

    seen = {}
    text_editor(files, TEXT, KeyEvent("f7"), lambda a: None,
                lambda a: seen.update(modal=type(a.modal)), KeyEvent("escape"))
    assert seen["modal"] is FindDialog



# -- across lines (a departure on a departure: the bar's regex reaching over breaks) -------------


CODE = ["int f()", "{", "  return 1;", "}", "int g()", "{", "}"]


def test_only_a_pattern_that_says_so_crosses_lines():
    from navigator.lib.editor.search import crosses

    for text in (r"a\nb", "(?s)a.b", "(?ms)^a", r"x\r", "a\nb"):
        assert crosses(SearchData(text=text, regex=True)), text
    for text in (r"\s+", "[^x]*", "a.b", "plain"):
        assert not crosses(SearchData(text=text, regex=True)), text
    assert not crosses(SearchData(text=r"a\nb"))            # not a regex: a backslash and an n
    # \s+ stays within a line: what it found before, it finds now.
    assert all_matches(["a  ", "  b"], SearchData(text=r"\s+", regex=True)) == [(0, 1, 0, 3), (1, 0, 1, 2)]


def test_a_crossing_match_is_found_forward_and_backward():
    data = SearchData(text=r"\)\n\{", regex=True)
    assert find(CODE, Pos(0, 0), data, backward=False) == (Pos(0, 6), Pos(1, 1))
    assert find(CODE, Pos(1, 1), data, backward=False) == (Pos(4, 6), Pos(5, 1))
    assert find(CODE, Pos(4, 0), data, backward=True) == (Pos(0, 6), Pos(1, 1))
    assert find(CODE, Pos(0, 7), data, backward=True) is None   # one ending after the cursor is not before it


def test_caret_and_dollar_keep_meaning_a_lines_ends_when_crossing():
    data = SearchData(text=r"\)$\n^\{$", regex=True)
    assert all_matches(CODE, data) == [(0, 6, 1, 1), (4, 6, 5, 1)]
    assert all_matches(["ab", "cd"], SearchData(text=r"(?s)^c.", regex=True)) == [(1, 0, 1, 2)]


def test_whole_words_and_empty_matches_hold_across_a_break():
    assert all_matches(["ab", "cd"], SearchData(text=r"b\nc", regex=True, whole=True)) == []
    assert all_matches(["a", "b"], SearchData(text=r"a\nb", regex=True, whole=True)) == [(0, 0, 1, 1)]
    assert all_matches(["a", "b"], SearchData(text=r"(?s)x*", regex=True)) == []


def test_a_stream_scope_holds_a_crossing_match_only_wholly_inside():
    data = SearchData(text=r"\)\n\{", regex=True)
    inside = find(CODE, Pos(0, 0), data, backward=False,
                  bounds=lambda n: (0, len(CODE[n])) if n <= 2 else None)
    outside = find(CODE, Pos(0, 0), data, backward=False,
                   bounds=lambda n: (0, len(CODE[n])) if n == 0 else None)
    assert inside == (Pos(0, 6), Pos(1, 1)) and outside is None


def test_a_crossing_replacement_puts_in_the_texts_own_line_ending():
    data = SearchData(text=r"(\w+)\(\)\n\{", regex=True, new=r"\1() {\n  //")
    found = find(CODE, Pos(0, 0), data, backward=False)
    assert replacement(CODE, found, data, newline="\r\n") == "f() {\r\n  //"
    assert replacement(CODE, found, data) == "f() {\n  //"


def test_window_matches_reads_only_round_the_lines_shown():
    from navigator.lib.editor import search

    lines = [f"line {n}" for n in range(100_000)]
    seen = []
    real = search._joined

    def joined(part):
        seen.append(len(part))
        return real(part)

    search._joined = joined
    try:
        lit = search.window_matches(lines, 50_000, 50_020, SearchData(text=r"9\nline", regex=True))
    finally:
        search._joined = real
    assert seen == [21 + 2 * search.WINDOW_MARGIN]
    assert set(lit) <= set(range(50_000, 50_021)) and lit[50_009] == [(9, 11)]  # its "9" and the break after it


CROSSING = b"int f()\n{\n}\nint g()\n{\n}\n"


def test_the_bar_finds_counts_and_lights_a_match_across_a_break(files):
    seen = {}
    _, editor = text_editor(files, CROSSING, ctrl("f"), KeyEvent("r", alt=True), *typed(r"\)\n\{"),
                            Until(counted),
                            lambda a: seen.update(count=bar_of(a).count_text(),
                                                  first=editor_window(a).editor._found_columns(0),
                                                  second=editor_window(a).editor._found_columns(1)))
    assert seen["count"] == ("1/2", False)
    assert seen["first"] == (6, 8) and seen["second"] == (0, 1)   # the break's cell lit on the first line
    assert (editor.line, editor.col) == (1, 1)


def test_replace_and_all_join_lines_each_one_undo_step(files):
    _, editor = text_editor(files, CROSSING, ctrl("r"), KeyEvent("r", alt=True), *typed(r"\)\n\{"),
                            KeyEvent("tab"), *typed(") {"), KeyEvent("a", alt=True))
    assert editor.document.encode() == b"int f() {\n}\nint g() {\n}\n"
    _, editor = text_editor(files, CROSSING, ctrl("r"), KeyEvent("r", alt=True), *typed(r"\)\n\{"),
                            KeyEvent("tab"), *typed(") {"), KeyEvent("a", alt=True),
                            KeyEvent("escape"), KeyEvent("z", ctrl=True))
    assert editor.document.encode() == CROSSING

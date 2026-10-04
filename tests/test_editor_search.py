"""The editor's search, as a model: ``TFileEditor.Search``'s line-by-line rules (MICROED.PAS)."""

from __future__ import annotations

from navigator.editor.document import Pos
from navigator.editor.search import SearchData, find, find_in_line

LINES = ["the cat", "scatter cat", "Cat dog"]


def test_forward_finds_from_the_place_on_and_crosses_lines():
    data = SearchData(text="cat")
    assert find(LINES, Pos(0, 0), data, backward=False) == (Pos(0, 4), Pos(0, 7))
    assert find(LINES, Pos(0, 7), data, backward=False) == (Pos(1, 1), Pos(1, 4))


def test_without_case_upper_and_lower_are_one():
    data = SearchData(text="cat")
    assert find(LINES, Pos(1, 9), data, backward=False) == (Pos(2, 0), Pos(2, 3))
    data.case = True
    assert find(LINES, Pos(1, 9), data, backward=False) is None


def test_whole_words_need_a_break_on_either_side():
    data = SearchData(text="cat", whole=True)
    assert find(LINES, Pos(1, 0), data, backward=False) == (Pos(1, 8), Pos(1, 11))


def test_backward_finds_a_match_ending_at_or_before_the_place():
    data = SearchData(text="cat")
    assert find(LINES, Pos(1, 8), data, backward=True) == (Pos(1, 1), Pos(1, 4))
    assert find(LINES, Pos(1, 1), data, backward=True) == (Pos(0, 4), Pos(0, 7))
    assert find(LINES, Pos(0, 4), data, backward=True) is None


def test_a_line_outside_the_bounds_is_passed_over():
    data = SearchData(text="cat")
    only_last = lambda n: (0, len(LINES[n])) if n == 2 else None  # noqa: E731
    assert find(LINES, Pos(0, 0), data, backward=False, bounds=only_last) == (Pos(2, 0), Pos(2, 3))


def test_a_match_must_lie_inside_the_part_searched():
    assert find_in_line("abcabc", "abc", 1, 5, case=True, whole=False, backward=False) is None
    assert find_in_line("abcabc", "abc", 1, 6, case=True, whole=False, backward=False) == (3, 6)

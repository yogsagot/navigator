"""Paragraph formatting as a model: DOS Navigator's ``FormatBlock`` and ``SetFormat`` (EDITOR.PAS)."""

from __future__ import annotations

from navigator.editor.paragraph import fix_margins, format_lines

LINES = ["The quick brown fox  jumps over", "", "the lazy dog and keeps running far away."]


def lay(mode):
    return format_lines(LINES, mode, left=2, right=24, indent=5)


def test_left_fills_lines_from_the_left_margin_under_the_room():
    assert lay("left") == ["  The quick brown fox", "  jumps over the lazy",
                           "  dog and keeps running", "  far away."]


def test_right_ends_each_line_against_the_right_margin():
    assert all(len(line) == 24 for line in lay("right"))
    assert lay("right")[-1] == "               far away."


def test_center_puts_each_line_midway_from_the_left_margin():
    assert lay("center")[-1] == "        far away."


def test_justify_widens_every_line_but_the_last_and_indents_the_first():
    lines = lay("justify")
    assert lines[0] == "     The   quick   brown"  # the indent, then the full width
    assert all(len(line) == 24 for line in lines[:-1])
    assert lines[-1] == "  running far away."


def test_a_block_with_no_words_lays_out_as_nothing():
    assert format_lines(["", "   "], "left", left=0, right=10, indent=0) == []


def test_impossible_margins_are_put_right_as_set_format_did():
    assert fix_margins(30, 20, 5) == (0, 20, 5)
    assert fix_margins(-1, 1, 0) == (0, 2, 0)
    assert fix_margins(4, 40, 40) == (4, 40, 4)

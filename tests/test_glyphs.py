"""The glyph vocabularies: which characters a named set resolves to."""

from __future__ import annotations

import pytest

from navkit.glyphs import (
    ASCII_BOX,
    ASCII_JOINS,
    ASCII_MARKS,
    ASCII_SCROLLBAR,
    BOX_CHARSETS,
    BOX_JOINS,
    DOS_MARKS,
    DOS_SCROLLBAR,
    DOUBLE_BOX,
    GLYPHS_ASCII,
    GLYPHS_NERD,
    GLYPHS_UNICODE,
    ROUND_BOX,
    SINGLE_BOX,
    charset,
    joins,
    marks,
    scrollbar,
    tier_named,
)


@pytest.mark.parametrize("name", ["single", "double", "round", "ascii"])
def test_every_set_collapses_to_ascii_below_unicode(name):
    """Nothing above US-ASCII survives the bottom tier, whatever was asked for."""
    assert charset(name, GLYPHS_ASCII) == ASCII_BOX


@pytest.mark.parametrize(
    "name, expected",
    [
        ("single", SINGLE_BOX),
        ("double", DOUBLE_BOX),
        ("round", ROUND_BOX),
        ("ascii", ASCII_BOX),
    ],
)
def test_a_named_set_is_itself_once_unicode_is_available(name, expected):
    assert charset(name, GLYPHS_UNICODE) == expected


def test_a_nerd_font_adds_nothing_to_box_drawing():
    """The tier matters at the ASCII boundary and nowhere above it.

    Box drawing is ordinary Unicode; a Nerd Font earns its place on icons,
    which are the application's vocabulary rather than the kit's.
    """
    for name in ("single", "double", "round", "ascii"):
        assert charset(name, GLYPHS_NERD) == charset(name, GLYPHS_UNICODE)


def test_an_unknown_name_degrades_rather_than_raising():
    """A sheet is a file a person edits, so a typo must not stop the program."""
    assert charset("dotted", GLYPHS_UNICODE) == SINGLE_BOX
    assert charset("dotted", GLYPHS_ASCII) == ASCII_BOX


def test_every_set_is_six_characters():
    """``draw_box`` unpacks exactly six, so a short set would raise on a frame."""
    for name in ("single", "double", "round", "ascii"):
        assert len(charset(name, GLYPHS_UNICODE)) == 6


@pytest.mark.parametrize(
    "name, expected",
    [
        ("ascii", GLYPHS_ASCII),
        ("unicode", GLYPHS_UNICODE),
        ("utf8", GLYPHS_UNICODE),
        ("nerd", GLYPHS_NERD),
        ("  NERD  ", GLYPHS_NERD),
        ("nerd-font", GLYPHS_NERD),
    ],
)
def test_tier_named_reads_the_vocabulary(name, expected):
    assert tier_named(name) == expected


def test_tier_named_falls_back_on_a_name_it_cannot_read():
    """As with NAVKIT_COLORS: an unreadable environment is ignored, not fatal."""
    assert tier_named("lots", GLYPHS_UNICODE) == GLYPHS_UNICODE
    assert tier_named("", GLYPHS_NERD) == GLYPHS_NERD
    assert tier_named("wat") is None


# -- the widget library's vocabularies ---------------------------------------


def test_every_box_set_has_joins_that_match_it():
    """One table keyed by the frame's own name, so the two cannot disagree."""
    assert set(BOX_JOINS) == set(BOX_CHARSETS)
    assert all(len(chars) == 5 for chars in BOX_JOINS.values())


def test_a_double_frame_takes_double_joins():
    """The whole reason joins are keyed by the frame rather than standing alone."""
    assert joins("double") == "\u255f\u2562\u2564\u2567\u253c"
    assert joins("single") == "\u251c\u2524\u252c\u2534\u253c"


@pytest.mark.parametrize(
    "lookup, name, unicode_form, ascii_form",
    [
        (joins, "double", "\u255f\u2562\u2564\u2567\u253c", ASCII_JOINS),
        (scrollbar, "dos", DOS_SCROLLBAR, ASCII_SCROLLBAR),
        (marks, "dos", DOS_MARKS, ASCII_MARKS),
    ],
)
def test_every_vocabulary_degrades_at_the_same_boundary(
    lookup, name, unicode_form, ascii_form
):
    """The lower boundary is where a tier matters, exactly as for a box set."""
    assert lookup(name, GLYPHS_ASCII) == ascii_form
    assert lookup(name, GLYPHS_UNICODE) == unicode_form


@pytest.mark.parametrize("lookup, name", [(joins, "double"), (scrollbar, "dos"), (marks, "dos")])
def test_a_nerd_font_improves_on_none_of_them(lookup, name):
    """The third answer each new set owed, and it is the same one every time.

    Box drawing, block elements and geometric shapes are all ordinary Unicode.
    The Private Use Area carries icons, and an icon is a *replacement* for one
    of these rather than a better version of it -- a single-glyph check box
    would collapse three cells into one and move every caption beside it.
    """
    assert lookup(name, GLYPHS_NERD) == lookup(name, GLYPHS_UNICODE)


@pytest.mark.parametrize("lookup, fallback", [(joins, "single"), (scrollbar, "dos"), (marks, "dos")])
def test_an_unknown_name_answers_rather_than_raising(lookup, fallback):
    """The posture charset() already takes towards a name it cannot read."""
    assert lookup("nonsense") == lookup(fallback)


def test_the_marks_are_four_single_cells():
    """A cluster paints `[`, a mark and `]', so a wide mark would misalign it."""
    for chars in (DOS_MARKS, ASCII_MARKS):
        assert len(chars) == 4
        assert all(len(char) == 1 for char in chars)


def test_the_scrollbar_is_six_single_cells():
    """Up, down, left, right, track, thumb -- one cell each, in that order."""
    for chars in (DOS_SCROLLBAR, ASCII_SCROLLBAR):
        assert len(chars) == 6


def test_a_widget_reads_its_joins_from_the_border_it_already_has():
    from navkit.widget import Widget

    widget = Widget()
    assert widget.box_joins() == joins("single")
    widget.merge_style("border: double")
    assert widget.box_charset() == "\u2554\u2557\u255a\u255d\u2550\u2551"
    assert widget.box_joins() == joins("double")

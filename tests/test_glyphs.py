"""The glyph vocabulary: which character set a named border resolves to."""

from __future__ import annotations

import pytest

from navkit.glyphs import (
    ASCII_BOX,
    DOUBLE_BOX,
    GLYPHS_ASCII,
    GLYPHS_NERD,
    GLYPHS_UNICODE,
    ROUND_BOX,
    SINGLE_BOX,
    charset,
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

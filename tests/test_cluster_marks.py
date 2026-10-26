"""Check box and radio marks in each look and at each glyph tier."""

from __future__ import annotations

from dataclasses import replace

import pytest

from conftest import mounted, settle

from navkit.glyphs import GLYPHS_ASCII, GLYPHS_NERD, GLYPHS_UNICODE
from navkit.screen import ScreenBuffer

from navml.widgets.dialog.check_boxes import CheckBoxes
from navml.widgets.dialog.radio_buttons import RadioButtons


def paint(widget, *, look: str = "dos", tier: int = GLYPHS_NERD) -> list[str]:
    app = widget.application
    app.terminal.info = replace(app.terminal.info, glyphs=tier)
    app.marks = look
    settle()
    buffer = ScreenBuffer(widget.width, widget.height)
    widget.render(buffer)
    return [
        "".join(buffer.get(x, y)[0] for x in range(buffer.width)).rstrip()
        for y in range(buffer.height)
    ]


def three_boxes(height: int = 3) -> CheckBoxes:
    boxes = CheckBoxes(width=30, height=height)
    boxes.items = ["~O~ff", "O~n~", "~M~ixed"]
    boxes.value = 0b010
    boxes.mixed = 0b100
    return mounted(boxes, size=(30, height))


def two_radios() -> RadioButtons:
    radios = RadioButtons(width=30, height=2)
    radios.items = ["~O~ne", "~T~wo"]
    radios.value = 1
    return mounted(radios, size=(30, 2))


@pytest.mark.parametrize(
    "look, tier, rows",
    [
        ("dos", GLYPHS_UNICODE, ["[ ] Off", "[X] On", "[?] Mixed"]),
        ("brackets", GLYPHS_UNICODE, ["[ ] Off", "[✓] On", "[-] Mixed"]),
        ("brackets", GLYPHS_NERD, ["[ ] Off", "[✓] On", "[-] Mixed"]),
        ("boxes", GLYPHS_UNICODE, [" ☐  Off", " ☑  On", " ⊟  Mixed"]),
        ("boxes", GLYPHS_NERD, ["   Off", "   On", "   Mixed"]),
        ("boxes", GLYPHS_ASCII, ["[ ] Off", "[X] On", "[?] Mixed"]),
    ],
)
def test_check_boxes_draw_the_look_asked_for(look, tier, rows):
    assert paint(three_boxes(), look=look, tier=tier) == rows


@pytest.mark.parametrize(
    "look, tier, rows",
    [
        ("dos", GLYPHS_UNICODE, ["( ) One", "(•) Two"]),
        ("dos", GLYPHS_ASCII, ["( ) One", "(*) Two"]),
        ("brackets", GLYPHS_UNICODE, ["( ) One", "(●) Two"]),
        ("boxes", GLYPHS_UNICODE, [" ○  One", " ◉  Two"]),
        ("boxes", GLYPHS_NERD, ["   One", "   Two"]),
    ],
)
def test_radio_buttons_draw_the_look_asked_for(look, tier, rows):
    assert paint(two_radios(), look=look, tier=tier) == rows


@pytest.mark.parametrize("look", ["dos", "brackets", "boxes"])
def test_no_look_moves_a_caption_or_a_column(look):
    """Every mark is three cells, so the second column starts where it did:
    six cells past the widest caption of the first, as TCluster stepped."""
    rows = paint(three_boxes(height=2), look=look)
    assert rows[0][4:7] == "Off" and rows[0].index("Mixed") == 3 + 6 + 4
    assert rows[1][4:] == "On"


def test_a_stylesheet_look_wins_over_the_application_choice():
    boxes = three_boxes()
    boxes.merge_style("look: boxes")
    assert paint(boxes, look="dos", tier=GLYPHS_UNICODE)[1] == " \u2611  On"

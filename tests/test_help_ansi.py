"""A screenshot's ``.ans`` file: what ``tools/screenshot.py`` writes and
``navigator/lib/help/ansi.py`` reads back."""

from __future__ import annotations

from dataclasses import replace

import pytest

from navigator.lib.help import ansi
from navkit.capabilities import FULL, VGA_PALETTE
from navkit.screen import ScreenBuffer
from navkit.style import Style
from tools.screenshot import as_ansi

INFO = replace(FULL, palette=VGA_PALETTE)
GREY, WHITE, BLUE = (170, 170, 170), (255, 255, 255), (0, 0, 170)


def painted() -> ScreenBuffer:
    buffer = ScreenBuffer(8, 2)
    buffer.fill(0, 0, 8, 2, " ", Style(fg=15, bg=1))
    buffer.draw_text(0, 0, "ab", Style(fg=15, bg=7, bold=True, underline=True))
    buffer.draw_text(2, 0, "日", Style(fg=(1, 2, 3), bg=(4, 5, 6), italic=True, strike=True))
    buffer.draw_text(0, 1, "é", Style(fg=7, bg=1))
    return buffer


def test_what_the_tool_writes_reads_back_as_the_same_cells():
    buffer = painted()
    rows = ansi.read(as_ansi(buffer, INFO))
    assert [len(row) for row in rows] == [8, 8]
    assert rows[0][0] == ("a", Style(fg=WHITE, bg=GREY, bold=True, underline=True))
    # A wide character is written once and gets its second cell back.
    assert rows[0][2] == ("日", Style(fg=(1, 2, 3), bg=(4, 5, 6), italic=True, strike=True))
    assert rows[0][3][0] == ""
    # A mark stays on the cell it was combined onto.
    assert rows[1][0][0] == "é"
    assert [char for char, _ in rows[1]] == ["é"] + [" "] * 7


def test_reverse_and_dim_are_already_colours_in_the_file():
    buffer = ScreenBuffer(2, 1)
    buffer.draw_text(0, 0, "r", Style(fg=15, bg=1, reverse=True))
    buffer.draw_text(1, 0, "d", Style(fg=(200, 200, 200), bg=(0, 0, 0), dim=True))
    text = as_ansi(buffer, INFO)
    assert ";7;" not in text and "[0;2;" not in text
    (row,) = ansi.read(text)
    assert row[0][1] == Style(fg=(170, 0, 0), bg=WHITE)
    assert row[1][1] == Style(fg=(100, 100, 100), bg=(0, 0, 0))


def test_the_file_is_lines_of_runs_and_nothing_else():
    text = as_ansi(painted(), INFO)
    lines = text.split("\n")
    assert lines[-1] == "" and len(lines) == 3
    assert all(line.startswith("\x1b[0;") and line.endswith("\x1b[0m") for line in lines[:-1])
    # No cursor movement: every escape is an SGR.
    assert all(part.split("m", 1)[0].replace(";", "").isdigit() for part in text.split("\x1b[")[1:])


RUN = "\x1b[0;38;2;1;2;3;48;2;4;5;6m"


@pytest.mark.parametrize(
    "text",
    [
        "plain\n",  # no run, no reset
        f"{RUN}ab\n",  # a line that does not end with a reset
        f"ab{RUN}c\x1b[0m\n",  # text before the first run
        "\x1b[0;31;44mab\x1b[0m\n",  # palette colours
        "\x1b[1;38;2;1;2;3;48;2;4;5;6mab\x1b[0m\n",  # not starting with a reset
        "\x1b[0;38;2;1;2;3mab\x1b[0m\n",  # one colour only
        "\x1b[0;7;38;2;1;2;3;48;2;4;5;6mab\x1b[0m\n",  # an attribute the writer resolves
        "\x1b[0;38;2;1;2;300;48;2;4;5;6mab\x1b[0m\n",  # not a colour
        f"{RUN}a\x1b[2Cb\x1b[0m\n",  # a cursor movement
        f"{RUN}a\tb\x1b[0m\n",  # a control character
        f"{RUN}ab\x1b[0m\n{RUN}abc\x1b[0m\n",  # ragged rows
        f"{RUN}ab\x1b[0mcd\n",  # text after the reset
    ],
)
def test_anything_outside_the_grammar_is_refused(text):
    with pytest.raises(ValueError):
        ansi.read(text)

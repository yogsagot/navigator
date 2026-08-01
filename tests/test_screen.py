"""Painting into the screen buffer and diffing it against the last frame."""

from __future__ import annotations

import pytest

from navkit.screen import ScreenBuffer, char_width, render_diff
from navkit.style import RESET_SGR, Style

RED = Style(fg=1)
GREEN = Style(fg=2)


def text_of(buffer: ScreenBuffer, y: int) -> str:
    """Row *y* as a string, with wide-character continuations dropped."""
    return "".join(buffer.get(x, y)[0] for x in range(buffer.width))


def test_new_buffer_is_blank():
    buffer = ScreenBuffer(4, 2)
    assert text_of(buffer, 0) == "    "
    assert text_of(buffer, 1) == "    "


def test_draw_text_and_styles():
    buffer = ScreenBuffer(10, 1)
    assert buffer.draw_text(2, 0, "hi", RED) == 2
    assert text_of(buffer, 0) == "  hi      "
    assert buffer.get(2, 0)[1] is RED
    assert buffer.get(1, 0)[1] != RED


def test_draw_text_clips_at_the_right_edge():
    buffer = ScreenBuffer(3, 1)
    assert buffer.draw_text(0, 0, "abcdef") == 3
    assert text_of(buffer, 0) == "abc"


def test_draw_text_respects_max_width():
    buffer = ScreenBuffer(10, 1)
    assert buffer.draw_text(0, 0, "abcdef", max_width=3) == 3
    assert text_of(buffer, 0) == "abc       "


def test_drawing_out_of_bounds_is_silently_clipped():
    buffer = ScreenBuffer(3, 1)
    buffer.draw_text(-5, 0, "abc")
    buffer.draw_text(0, 99, "abc")
    buffer.set_cell(99, 99, "x")
    buffer.fill(-10, -10, 100, 100, "#")
    assert text_of(buffer, 0) == "###"


def test_get_out_of_bounds_returns_a_blank():
    assert ScreenBuffer(2, 2).get(50, 50)[0] == " "


@pytest.mark.parametrize(
    ("char", "expected"),
    [("a", 1), ("日", 2), ("", 0), ("\x00", 0), ("́", 0)],
)
def test_char_width(char, expected):
    assert char_width(char) == expected


def test_wide_characters_occupy_two_cells():
    buffer = ScreenBuffer(6, 1)
    buffer.draw_text(0, 0, "日本")
    assert [buffer.get(x, 0)[0] for x in range(5)] == ["日", "", "本", "", " "]


def test_wide_character_is_dropped_when_only_one_cell_is_left():
    buffer = ScreenBuffer(2, 1)
    buffer.draw_text(0, 0, "a日")
    # The trailing half would wrap onto the next line, so a blank is drawn.
    assert text_of(buffer, 0) == "a "


def test_wide_character_fits_when_the_row_ends_exactly():
    buffer = ScreenBuffer(3, 1)
    buffer.draw_text(0, 0, "a日")
    assert [buffer.get(x, 0)[0] for x in range(3)] == ["a", "日", ""]


def test_fill_rectangle():
    buffer = ScreenBuffer(5, 3)
    buffer.fill(1, 1, 3, 1, "#", RED)
    assert text_of(buffer, 0) == "     "
    assert text_of(buffer, 1) == " ### "
    assert buffer.get(1, 1)[1] is RED


def test_draw_box_single_and_double():
    buffer = ScreenBuffer(4, 3)
    buffer.draw_box(0, 0, 4, 3)
    assert text_of(buffer, 0) == "┌──┐"
    assert text_of(buffer, 1) == "│  │"
    assert text_of(buffer, 2) == "└──┘"

    buffer.draw_box(0, 0, 4, 3, double=True)
    assert text_of(buffer, 0) == "╔══╗"


def test_draw_box_fills_its_interior():
    buffer = ScreenBuffer(4, 3)
    buffer.draw_box(0, 0, 4, 3, fill="#")
    assert text_of(buffer, 1) == "│##│"


def test_draw_box_ignores_degenerate_sizes():
    buffer = ScreenBuffer(4, 3)
    buffer.draw_box(0, 0, 1, 3)
    assert text_of(buffer, 0) == "    "


def test_resize_clears():
    buffer = ScreenBuffer(4, 1)
    buffer.draw_text(0, 0, "abcd")
    buffer.resize(2, 2)
    assert (buffer.width, buffer.height) == (2, 2)
    assert text_of(buffer, 0) == "  "


def test_copy_from_is_independent():
    source = ScreenBuffer(3, 1)
    source.draw_text(0, 0, "abc")
    copy = ScreenBuffer(1, 1)
    copy.copy_from(source)
    source.draw_text(0, 0, "xyz")
    assert text_of(copy, 0) == "abc"


def test_first_frame_is_a_full_repaint():
    buffer = ScreenBuffer(4, 1)
    buffer.draw_text(0, 0, "hi")
    output = render_diff(None, buffer)
    assert output.startswith(RESET_SGR + "\x1b[H\x1b[2J")
    assert "h" in output and "i" in output


def test_identical_frames_produce_no_output():
    current = ScreenBuffer(4, 2)
    current.draw_text(0, 0, "hi")
    previous = ScreenBuffer(1, 1)
    previous.copy_from(current)
    assert render_diff(previous, current) == ""


def test_only_changed_cells_are_emitted():
    previous = ScreenBuffer(6, 2)
    current = ScreenBuffer(6, 2)
    current.copy_from(previous)
    current.set_cell(3, 1, "x", GREEN)
    assert render_diff(previous, current) == (
        "\x1b[2;4H" + GREEN.sgr() + "x" + RESET_SGR
    )


def test_adjacent_changes_do_not_repeat_the_cursor_move():
    previous = ScreenBuffer(6, 1)
    current = ScreenBuffer(6, 1)
    current.copy_from(previous)
    current.draw_text(1, 0, "ab", RED)
    output = render_diff(previous, current)
    assert output.count("H") == 1  # one cursor move for both cells
    assert output.count(RED.sgr()) == 1  # style selected once


def test_a_size_change_forces_a_full_repaint():
    previous = ScreenBuffer(4, 1)
    current = ScreenBuffer(8, 1)
    assert render_diff(previous, current).startswith(RESET_SGR + "\x1b[H\x1b[2J")


def test_style_change_alone_is_repainted():
    previous = ScreenBuffer(3, 1)
    previous.draw_text(0, 0, "a", RED)
    current = ScreenBuffer(3, 1)
    current.copy_from(previous)
    current.draw_text(0, 0, "a", GREEN)
    assert GREEN.sgr() in render_diff(previous, current)

# -- views --------------------------------------------------------------------


def test_a_view_shifts_what_is_painted_through_it():
    buffer = ScreenBuffer(10, 3)
    view = buffer.view(3, 1, 4, 2)
    view.draw_text(0, 0, "ab", RED)
    assert text_of(buffer, 0) == "          "
    assert text_of(buffer, 1) == "   ab     "


def test_a_view_reports_its_own_size():
    view = ScreenBuffer(10, 3).view(3, 1, 4, 2)
    assert (view.width, view.height) == (4, 2)


def test_a_view_clips_what_would_land_outside_it():
    buffer = ScreenBuffer(10, 1)
    buffer.draw_text(0, 0, "..........")
    view = buffer.view(3, 0, 4, 1)
    view.draw_text(0, 0, "abcdefgh")  # twice as much text as there is room
    assert text_of(buffer, 0) == "...abcd..."


def test_a_view_ignores_paint_at_negative_coordinates():
    buffer = ScreenBuffer(6, 1)
    buffer.draw_text(0, 0, "......")
    view = buffer.view(2, 0, 2, 1)
    view.draw_text(-2, 0, "xy")
    assert text_of(buffer, 0) == "......"


def test_a_view_of_a_view_intersects_both_clips():
    buffer = ScreenBuffer(12, 1)
    buffer.draw_text(0, 0, "............")
    inner = buffer.view(2, 0, 6, 1).view(1, 0, 3, 1)
    inner.draw_text(0, 0, "abcdef")
    assert text_of(buffer, 0) == "...abc......"


def test_a_view_clips_a_fill():
    buffer = ScreenBuffer(8, 3)
    buffer.view(2, 1, 3, 1).fill(0, 0, 99, 99, "#")
    assert text_of(buffer, 0) == "        "
    assert text_of(buffer, 1) == "  ###   "
    assert text_of(buffer, 2) == "        "


def test_a_view_reads_through_to_the_buffer():
    buffer = ScreenBuffer(6, 1)
    buffer.draw_text(4, 0, "z", RED)
    view = buffer.view(3, 0, 3, 1)
    assert view.get(1, 0) == ("z", RED)
    assert view.get(9, 0) == (" ", Style())  # outside the view


def test_a_wide_character_cannot_spill_out_of_a_view():
    buffer = ScreenBuffer(6, 1)
    buffer.draw_text(0, 0, "......")
    view = buffer.view(1, 0, 3, 1)
    # The last cell of the view has no room for the trailing half, so the
    # neighbour keeps its own content rather than being half overwritten.
    assert view.set_cell(2, 0, "漢") == 2
    assert text_of(buffer, 0) == "... .."  # the view's last cell went blank
    assert buffer.get(4, 0)[0] == "."  # and the neighbour is untouched


def test_a_wide_character_fits_inside_a_view_with_room():
    buffer = ScreenBuffer(6, 1)
    view = buffer.view(1, 0, 4, 1)
    assert view.set_cell(1, 0, "漢") == 2
    assert buffer.get(2, 0)[0] == "漢"
    assert buffer.get(3, 0)[0] == ""  # the continuation cell


def test_a_view_draws_a_box_in_its_own_coordinates():
    buffer = ScreenBuffer(8, 4)
    buffer.view(2, 1, 4, 3).draw_box(0, 0, 4, 3)
    assert text_of(buffer, 0) == "        "
    assert text_of(buffer, 1) == "  ┌──┐  "
    assert text_of(buffer, 3) == "  └──┘  "


# -- the row prefilter --------------------------------------------------------


def test_an_untouched_row_is_not_re_emitted():
    previous = ScreenBuffer(6, 3)
    current = ScreenBuffer(6, 3)
    current.draw_text(0, 1, "x")
    output = render_diff(previous, current)
    # Only row 2 is addressed, and only its one changed cell is sent.
    assert output.count("\x1b[") == 3  # position, style, final reset
    assert "\x1b[2;1H" in output
    assert "\x1b[1;1H" not in output and "\x1b[3;1H" not in output

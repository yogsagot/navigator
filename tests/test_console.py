"""The screen a child program paints on.

These tests are the mirror image of ``test_input_parser.py``: there, bytes
arriving from the user become events; here, bytes arriving from a program
become cells.
"""

from __future__ import annotations

import pytest

from navkit.console import ConsoleScreen, color_of, style_of
from navkit.screen import ScreenBuffer
from navkit.style import BLUE, BROWN, LIGHT_RED, RED, YELLOW, Style


def text_of(console: ConsoleScreen, row: int) -> str:
    """The characters on one row of a console, trailing blanks removed."""
    surface = console.surface
    return "".join(
        surface.get(x, row)[0] or " " for x in range(console.columns)
    ).rstrip()


def feed(data: bytes, columns: int = 20, lines: int = 4) -> ConsoleScreen:
    console = ConsoleScreen(columns, lines)
    console.feed(data)
    return console


# -- colours ---------------------------------------------------------------


def test_ansi_colours_keep_their_palette_index():
    # 33 is pyte's "brown", which is navkit's index 3 -- the name differs, the
    # register does not, and the register is what a pinned palette resolves.
    assert color_of("brown") == BROWN
    assert color_of("brightbrown") == YELLOW
    assert color_of("default") is None


def test_the_bright_magenta_background_typo_is_carried():
    # pyte 0.8.2 spells it "bfightmagenta" in BG_AIXTERM.  Without the typo in
    # the table, ESC [ 105 m would silently lose its colour.
    assert color_of("bfightmagenta") == color_of("brightmagenta")


def test_the_indexed_form_of_a_basic_colour_stays_an_index():
    # ESC [ 38;5;4 m and ESC [ 34 m ask for the same blue, and have to arrive
    # as the same thing, or a pinned palette would paint them differently.
    assert text_of(feed(b"\x1b[38;5;4mx"), 0) == "x"
    assert feed(b"\x1b[38;5;4mx").surface.get(0, 0)[1].fg == BLUE
    assert feed(b"\x1b[34mx").surface.get(0, 0)[1].fg == BLUE


def test_true_colour_becomes_a_triple():
    assert color_of("ff8000") == (255, 128, 0)
    assert feed(b"\x1b[38;2;255;128;0mx").surface.get(0, 0)[1].fg == (255, 128, 0)


def test_sgr_attributes_reach_the_style():
    console = feed(b"\x1b[1;4;7;31;44mx")
    assert console.surface.get(0, 0)[1] == Style(
        fg=RED, bg=BLUE, bold=True, underline=True, reverse=True,
        terminal_palette=True,
    )


def test_style_of_is_shared_between_identical_cells():
    console = feed(b"\x1b[91mabc")
    surface = console.surface
    assert surface.get(0, 0)[1].fg == LIGHT_RED
    # Memoised on the pyte cell, so a screenful of output holds one Style per
    # distinct appearance rather than one per cell.
    assert surface.get(0, 0)[1] is surface.get(2, 0)[1]


# -- decoding --------------------------------------------------------------


def test_text_and_newlines_land_where_they_should():
    console = feed(b"first\r\nsecond")
    assert text_of(console, 0) == "first"
    assert text_of(console, 1) == "second"


def test_a_sequence_split_across_two_feeds_is_still_decoded():
    console = ConsoleScreen(20, 4)
    console.feed(b"\x1b[3")
    console.feed(b"1mred")
    assert text_of(console, 0) == "red"
    assert console.surface.get(0, 0)[1].fg == RED


def test_a_utf8_character_split_across_two_feeds_is_still_decoded():
    console = ConsoleScreen(20, 4)
    console.feed(b"caf\xc3")
    console.feed(b"\xa9")
    assert text_of(console, 0) == "café"


def test_cursor_positioning_and_erase():
    console = feed(b"aaaa\x1b[1;2Hb\x1b[K")
    assert text_of(console, 0) == "ab"


def test_a_wide_character_occupies_two_cells():
    console = feed(b"\xe6\x97\xa5x")
    surface = console.surface
    assert surface.get(0, 0)[0] == "日"
    # The same stub navkit's own buffer uses, which is why the blit is a copy.
    assert surface.get(1, 0)[0] == ""
    assert surface.get(2, 0)[0] == "x"


def test_the_cursor_is_reported():
    console = feed(b"abc")
    assert console.cursor == (3, 0, False)
    console.feed(b"\x1b[?25l")
    assert console.cursor[2] is True


# -- the mirror ------------------------------------------------------------


def test_sync_reports_whether_anything_moved():
    console = ConsoleScreen(20, 4)
    console.feed(b"hello")
    assert console.sync() is True
    # Nothing arrived in between, so there is nothing to convert.
    assert console.sync() is False


def test_blit_into_paints_the_console_onto_another_surface():
    console = feed(b"\x1b[31mhi")
    target = ScreenBuffer(10, 3)
    console.blit_into(target, 1, 1)
    assert (target.get(1, 1)[0], target.get(2, 1)[0]) == ("h", "i")
    assert target.get(1, 1)[1].fg == RED
    # Painted where it was told to, and nowhere else.
    assert target.get(0, 0)[0] == " "


def test_resize_changes_the_screen_and_the_mirror():
    console = ConsoleScreen(20, 4)
    console.resize(10, 2)
    assert (console.columns, console.lines) == (10, 2)
    assert (console.surface.width, console.surface.height) == (10, 2)


def test_resize_refuses_to_vanish():
    console = ConsoleScreen(20, 4)
    console.resize(0, 0)
    assert (console.columns, console.lines) == (1, 1)


# -- scrollback ------------------------------------------------------------


def test_output_scrolled_off_the_top_can_be_paged_back_to():
    console = ConsoleScreen(20, 3, history=50)
    console.feed(b"".join(b"line%d\r\n" % n for n in range(12)))
    assert not console.scrolled_back
    on_screen = text_of(console, 0)

    console.prev_page()
    assert console.scrolled_back
    assert text_of(console, 0) != on_screen

    console.next_page()
    assert not console.scrolled_back


def test_new_output_snaps_the_view_back_to_the_bottom():
    console = ConsoleScreen(20, 3, history=50)
    console.feed(b"".join(b"line%d\r\n" % n for n in range(12)))
    console.prev_page()
    assert console.scrolled_back
    console.feed(b"more\r\n")
    assert not console.scrolled_back


# -- seeding ---------------------------------------------------------------


def test_seeding_gives_up_quietly_when_no_host_offers_the_screen(monkeypatch):
    from navkit import console as console_module

    monkeypatch.delenv("TMUX", raising=False)
    monkeypatch.delenv("KITTY_WINDOW_ID", raising=False)
    monkeypatch.setattr(console_module, "_capture_vcsa", lambda lines: None)
    assert console_module.seed_from_host(ConsoleScreen(20, 4)) is None


def test_seeding_feeds_what_a_host_did_offer(monkeypatch):
    from navkit import console as console_module

    monkeypatch.setattr(
        console_module, "_capture_tmux", lambda lines: b"old output\r\n"
    )
    console = ConsoleScreen(20, 4)
    assert console_module.seed_from_host(console) == "tmux"
    assert text_of(console, 0) == "old output"


# -- what a full-screen program needs --------------------------------------------


def test_the_alternate_screen_gives_the_output_back():
    console = feed(b"before\r\n")
    console.feed(b"\x1b[?1049h\x1b[2J\x1b[HFULLSCREEN")
    assert console.alternate
    assert "FULLSCREEN" in console.screen.display[0]
    console.feed(b"\x1b[?1049l")
    assert not console.alternate
    assert console.screen.display[0].rstrip() == "before"
    assert (console.cursor[0], console.cursor[1]) == (0, 1)


def test_the_alternate_screen_keeps_nothing_in_the_scrollback():
    console = feed(b"")
    console.feed(b"\x1b[?1049h" + b"\r\n".join(b"row%d" % n for n in range(30)))
    assert len(console.screen.history.top) == 0


def test_a_query_is_answered_down_the_pty():
    console = feed(b"abc")
    answers = []
    console.respond = answers.append
    console.feed(b"\x1b[6n")
    assert answers == [b"\x1b[1;4R"]


def test_the_modes_a_program_turns_on_are_readable():
    console = feed(b"\x1b[?1h\x1b[?1002h\x1b[?1006h")
    assert console.application_cursor
    assert console.mouse_tracking == 1002
    assert console.mouse_sgr
    console.feed(b"\x1b[?1l\x1b[?1002l")
    assert not console.application_cursor
    assert console.mouse_tracking == 0


@pytest.mark.parametrize("sequence", [
    b"\x1b[?1;1000r",     # mc's XTRESTORE, which crashed set_margins
    b"\x1b[?5A",
    b"\x1b[?2m",
])
def test_a_private_form_pyte_does_not_know_is_dropped(sequence):
    console = feed(b"ab" + sequence + b"cd")
    assert console.screen.display[0].rstrip() == "abcd"


def test_an_xterm_modifier_setting_is_not_a_colour():
    # vim's `CSI > 4 ; 2 m' used to arrive as underline and bold.
    console = feed(b"\x1b[>4;2mx")
    style = console.surface.get(0, 0)[1]
    assert not style.bold and not style.underline


def test_a_sequence_that_breaks_pyte_does_not_break_the_console(monkeypatch):
    console = feed(b"")

    def boom(*args, **kwargs):
        raise RuntimeError("pyte")

    monkeypatch.setattr(console.screen, "bell", boom)
    console.feed(b"a\x07b")
    monkeypatch.undo()
    console.feed(b"later")
    assert "later" in console.screen.display[0]

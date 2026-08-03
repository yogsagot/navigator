"""What the terminal supports, and what the renderer does about it.

The colour tests are mostly about one decision: a palette index is left alone
so the user's own terminal theme still decides what `blue' looks like, while a
colour the terminal cannot name at all is quantised against a fixed reference.
Getting that backwards is what makes a greyscale scheme come back in colour.
"""

from __future__ import annotations

import io

import pytest

from navkit.capabilities import (
    ANSI,
    ANSI_BRIGHT,
    EXTENDED,
    FULL,
    MONOCHROME,
    TRUECOLOR,
    TerminalInfo,
)
from navkit.screen import ScreenBuffer, render_diff
from navkit.style import Style
from navkit.terminal import Terminal

# navkit numbers colours in ANSI order, not the DOS order the palettes use.
BLUE, CYAN, LIGHT_CYAN, WHITE = 4, 6, 14, 15


# -- detection --------------------------------------------------------------


@pytest.mark.parametrize(
    "env, expected",
    [
        ({"TERM": "xterm-256color", "COLORTERM": "truecolor"}, TRUECOLOR),
        ({"TERM": "xterm-256color", "COLORTERM": "24bit"}, TRUECOLOR),
        ({"TERM": "xterm-256color"}, EXTENDED),
        ({"TERM": "screen-256color"}, EXTENDED),
        ({"TERM": "xterm"}, ANSI_BRIGHT),
        ({"TERM": "linux"}, ANSI_BRIGHT),
        ({}, MONOCHROME),
        ({"TERM": "dumb"}, MONOCHROME),
        # NO_COLOR outranks any claim of support, per no-color.org.
        ({"TERM": "xterm-256color", "COLORTERM": "truecolor", "NO_COLOR": "1"}, MONOCHROME),
        # ...and the explicit override outranks NO_COLOR in turn.
        ({"NO_COLOR": "1", "TERM": "xterm", "NAVKIT_COLORS": "truecolor"}, TRUECOLOR),
        ({"TERM": "xterm", "NAVKIT_COLORS": "256"}, EXTENDED),
        ({"TERM": "xterm-256color", "NAVKIT_COLORS": "16"}, ANSI_BRIGHT),
        ({"TERM": "xterm-256color", "NAVKIT_COLORS": "mono"}, MONOCHROME),
        # An override that means nothing is ignored rather than fatal: it comes
        # from an environment, and a typo there must not stop the program.
        ({"TERM": "xterm-256color", "NAVKIT_COLORS": "lots"}, EXTENDED),
    ],
)
def test_detection_reads_the_environment(env, expected):
    assert TerminalInfo.detect(env, is_tty=True).colors == expected


def test_a_terminal_that_is_not_a_tty_gets_nothing():
    """Output going somewhere other than a terminal must stay plain.

    Not only colourless: the alternate screen, mouse reporting and bracketed
    paste all write escapes that are noise in a file or a pipe.
    """
    info = TerminalInfo.detect({"TERM": "xterm-256color"}, is_tty=False)
    assert info.colors == MONOCHROME
    assert not any((info.alt_screen, info.mouse, info.bracketed_paste, info.title))


def test_a_dumb_terminal_keeps_its_scrollback():
    info = TerminalInfo.detect({"TERM": "dumb"}, is_tty=True)
    assert not info.alt_screen and not info.mouse


# -- colour -----------------------------------------------------------------


@pytest.mark.parametrize("depth", [TRUECOLOR, EXTENDED, ANSI_BRIGHT])
def test_a_nameable_index_is_never_touched(depth):
    """The whole point of naming a colour rather than pinning it.

    A sheet saying `blue' must reach the terminal as its own blue, whatever
    the user themed it to -- quantising it against our reference table would
    replace their theme with ours.
    """
    info = TerminalInfo(colors=depth)
    for index in range(16):
        assert info.adapt(index) == index


def test_eight_colour_terminals_fold_the_bright_half():
    info = TerminalInfo(colors=ANSI)
    assert info.adapt(CYAN) == CYAN
    assert info.adapt(LIGHT_CYAN) == CYAN      # 14 -> 6, the same hue
    assert info.adapt(WHITE) == 7
    assert info.adapt(BLUE) == BLUE


def test_monochrome_drops_colour_rather_than_approximating_it():
    info = TerminalInfo(colors=MONOCHROME)
    assert info.adapt(BLUE) is None
    assert info.adapt((45, 202, 255)) is None
    assert info.sgr(Style(fg=BLUE, bg=WHITE)) == "\x1b[0m"


def test_bold_survives_a_downgrade():
    """Quantising is about colour; the other attributes are not its business."""
    style = Style(fg=(45, 202, 255), bold=True, underline=True)
    assert TerminalInfo(colors=MONOCHROME).adapt_style(style).bold
    assert TerminalInfo(colors=ANSI_BRIGHT).adapt_style(style).underline


def test_a_grey_stays_grey_when_quantised():
    """The case the whole arrangement exists for.

    Eight of DOS Navigator's palettes reprogram the VGA registers, and BW.PAL
    makes every one of them a grey -- its *blue* register holds a mid grey. So
    the theme records the exact `#rrggbb', and a sixteen-colour terminal has to
    land on a grey. Baking the DOS colour *name* into the sheet instead would
    have put a real blue here.
    """
    info = TerminalInfo(colors=ANSI_BRIGHT)
    greys = {0: 0, 57: 8, 85: 8, 113: 8, 170: 7, 255: 15}
    for level, expected in greys.items():
        assert info.adapt((level, level, level)) == expected, level


def test_quantising_to_256_avoids_the_themeable_indices():
    """Below 16 a terminal paints whatever it likes, so those are no target."""
    info = TerminalInfo(colors=EXTENDED)
    for rgb in ((45, 202, 255), (0, 0, 0), (255, 255, 255), (128, 64, 32)):
        assert info.adapt(rgb) >= 16


def test_an_extended_index_survives_a_drop_to_sixteen():
    # 45 is a bright cyan in the xterm cube; it has to land on one of ours.
    assert TerminalInfo(colors=ANSI_BRIGHT).adapt(45) == LIGHT_CYAN
    assert TerminalInfo(colors=EXTENDED).adapt(45) == 45


# -- and through the renderer -----------------------------------------------


def _painted(info):
    buffer = ScreenBuffer(1, 1)
    buffer.set_cell(0, 0, "x", Style(fg=(45, 202, 255), bg=(85, 85, 130)))
    return render_diff(None, buffer, info)


def test_the_renderer_emits_what_the_terminal_can_take():
    assert "38;2;45;202;255" in _painted(TerminalInfo(colors=TRUECOLOR))
    assert "38;5;" in _painted(TerminalInfo(colors=EXTENDED))
    assert "38;" not in _painted(TerminalInfo(colors=ANSI_BRIGHT))  # a plain 9x code
    assert "\x1b[0m" in _painted(TerminalInfo(colors=MONOCHROME))


def test_no_info_means_emit_what_the_style_says():
    """A caller rendering to a string has no terminal to ask."""
    assert "38;2;45;202;255" in _painted(None)
    assert _painted(None) == _painted(FULL)


# -- and the escapes the terminal sets up -----------------------------------


def _terminal(**flags):
    out = io.StringIO()
    return Terminal(
        input_stream=io.StringIO(), output_stream=out, info=TerminalInfo(**flags)
    ), out


def test_start_asks_only_for_what_is_supported():
    terminal, out = _terminal(alt_screen=False, mouse=False, bracketed_paste=False)
    terminal.start()
    written = out.getvalue()
    assert "?1049h" not in written      # alternate screen
    assert "?1000h" not in written      # mouse
    assert "?2004h" not in written      # bracketed paste
    assert "?7l" in written             # autowrap off is unconditional

    terminal.stop()
    restored = out.getvalue()[len(written):]
    # Nothing that was never turned on may be turned off either.
    assert "?1049l" not in restored and "?2004l" not in restored
    assert "?7h" in restored and "?25h" in restored


def test_start_asks_for_everything_when_it_can():
    terminal, out = _terminal()
    terminal.start()
    assert all(code in out.getvalue() for code in ("?1049h", "?1000h", "?2004h"))


def test_a_caller_may_decline_a_supported_feature():
    """`mouse=False' is a preference; the flag is a capability. Either vetoes."""
    out = io.StringIO()
    terminal = Terminal(
        input_stream=io.StringIO(), output_stream=out, mouse=False, info=FULL
    )
    assert not terminal.mouse
    terminal.start()
    assert "?1000h" not in out.getvalue()


def test_the_title_is_left_alone_when_it_would_go_nowhere():
    terminal, out = _terminal(title=False)
    terminal.set_title("Navigator")
    terminal.flush()
    assert out.getvalue() == ""

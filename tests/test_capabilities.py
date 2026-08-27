"""What the terminal supports, and what the renderer does about it.

The colour tests are mostly about one decision: what a colour the terminal
cannot name at all becomes, quantised against a fixed reference.  Getting that
backwards is what makes a greyscale scheme come back in colour.

An *index* is the other half.  Left unpinned it reaches the terminal untouched,
so the user's own theme decides what `blue' looks like; with a palette pinned it
means the colour that palette holds, which is what a transcribed DOS scheme is
actually asking for.  The test that matters most there is the one showing that
pinning changes nothing on a terminal that names only sixteen colours.
"""

from __future__ import annotations

import io

import pytest

from navkit.capabilities import (
    ANSI,
    VGA_PALETTE,
    ANSI_BRIGHT,
    EXTENDED,
    FULL,
    MONOCHROME,
    TRUECOLOR,
    TerminalInfo,
)
from navkit.glyphs import GLYPHS_ASCII, GLYPHS_NERD, GLYPHS_UNICODE
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
def test_a_nameable_index_is_never_touched_with_no_palette_pinned(depth):
    """The whole point of naming a colour rather than pinning it.

    With nothing pinned a sheet saying `blue' must reach the terminal as its
    own blue, whatever the user themed it to -- quantising it against our
    reference table would replace their theme with ours.
    """
    info = TerminalInfo(colors=depth)
    for index in range(16):
        assert info.adapt(index) == index


def test_a_pinned_index_means_the_colour_the_palette_holds():
    """What a transcribed DOS palette is actually asking for.

    `norton.nss' says `blue' because NORTON.PAL left the VGA registers alone,
    not because it wanted the terminal's opinion. Pinned, that reaches a
    capable terminal as the register value: #0000aa, and not the pale blue an
    IDE's own scheme might paint.
    """
    info = TerminalInfo(colors=TRUECOLOR, palette=VGA_PALETTE)
    assert info.adapt(BLUE) == (0, 0, 170)
    assert info.adapt(7) == (170, 170, 170)
    assert info.adapt(WHITE) == (255, 255, 255)


@pytest.mark.parametrize("depth", [ANSI_BRIGHT, ANSI])
def test_pinning_changes_nothing_a_sixteen_colour_terminal_could_show(depth):
    """The property that makes pinning safe to do by default.

    Resolving an index through the palette and quantising the result searches
    the very table the palette came from, so it hands back the index it started
    with. A terminal that can do no better is therefore asked for exactly what
    it was asked for before -- only a terminal that *can* do better sees a
    difference.
    """
    pinned = TerminalInfo(colors=depth, palette=VGA_PALETTE)
    plain = TerminalInfo(colors=depth)
    for index in range(16):
        assert pinned.adapt(index) == plain.adapt(index), index


def test_a_pinned_index_quantises_into_the_cube_on_256_colours():
    """Still no target below 16: those are the ones the terminal themes."""
    info = TerminalInfo(colors=EXTENDED, palette=VGA_PALETTE)
    assert all(info.adapt(index) >= 16 for index in range(16))
    assert info.adapt(BLUE) == 19            # #0000af, the nearest cube blue


def test_pinning_does_not_revive_colour_a_terminal_cannot_take():
    info = TerminalInfo(colors=MONOCHROME, palette=VGA_PALETTE)
    assert info.adapt(BLUE) is None
    assert info.sgr(Style(fg=BLUE, bg=WHITE)) == "\x1b[0m"


def test_pinning_is_about_indices_and_leaves_a_triple_alone():
    """A theme that reprograms the registers already says what it means."""
    grey = (57, 57, 57)
    assert TerminalInfo(colors=TRUECOLOR, palette=VGA_PALETTE).adapt(grey) == grey
    assert TerminalInfo(colors=ANSI_BRIGHT, palette=VGA_PALETTE).adapt(grey) == 8


@pytest.mark.parametrize(
    "env, default, expected",
    [
        # Nothing said: the caller's own answer stands, either way round.
        ({"TERM": "xterm"}, None, None),
        ({"TERM": "xterm"}, VGA_PALETTE, VGA_PALETTE),
        # ...and the variable outranks it, either way round.
        ({"TERM": "xterm", "NAVKIT_PALETTE": "dos"}, None, VGA_PALETTE),
        ({"TERM": "xterm", "NAVKIT_PALETTE": "vga"}, None, VGA_PALETTE),
        ({"TERM": "xterm", "NAVKIT_PALETTE": "terminal"}, VGA_PALETTE, None),
        ({"TERM": "xterm", "NAVKIT_PALETTE": "off"}, VGA_PALETTE, None),
        # A typo is ignored rather than fatal, as with NAVKIT_COLORS.
        ({"TERM": "xterm", "NAVKIT_PALETTE": "ega"}, VGA_PALETTE, VGA_PALETTE),
    ],
)
def test_the_environment_may_pin_the_palette_or_hand_it_back(env, default, expected):
    assert TerminalInfo.detect(env, palette=default).palette == expected


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


def test_the_colour_registers_are_rewritten_only_when_asked():
    """Opt-in, because it repaints colours outside this application's cells.

    It is the one thing that helps a terminal naming nothing but the sixteen,
    which is exactly the terminal a pinned palette cannot reach.
    """
    out = io.StringIO()
    terminal = Terminal(
        input_stream=io.StringIO(), output_stream=out,
        reprogram_palette=True, info=TerminalInfo(palette=VGA_PALETTE),
    )
    terminal.start()
    written = out.getvalue()
    assert written.count("\x1b]4;") == 16
    assert "\x1b]4;4;rgb:00/00/aa\x1b\\" in written

    terminal.stop()
    assert "\x1b]104" in out.getvalue()[len(written):]


def test_the_registers_are_left_alone_by_default():
    terminal, out = _terminal(palette=VGA_PALETTE)
    terminal.start()
    terminal.stop()
    assert "\x1b]4;" not in out.getvalue() and "\x1b]104" not in out.getvalue()


def test_reprogramming_needs_a_palette_to_program_with():
    """Nothing to say, so nothing is said -- and nothing is reset either."""
    out = io.StringIO()
    terminal = Terminal(
        input_stream=io.StringIO(), output_stream=out,
        reprogram_palette=True, info=TerminalInfo(),
    )
    assert not terminal.reprogram_palette
    terminal.start()
    terminal.stop()
    assert "\x1b]4;" not in out.getvalue() and "\x1b]104" not in out.getvalue()


def test_the_title_is_left_alone_when_it_would_go_nowhere():
    terminal, out = _terminal(title=False)
    terminal.set_title("Navigator")
    terminal.flush()
    assert out.getvalue() == ""


# -- the glyph tier -----------------------------------------------------------
#
# The character half of the same question the colour depth asks, and detected
# the same way: from the environment, conservatively, with one variable that
# overrides the guess.  What cannot be detected is the *font*, so the Nerd tier
# is granted only to terminals that ship the fallback themselves.


@pytest.mark.parametrize(
    "env, expected",
    [
        # A terminal that bundles a Nerd Font symbol fallback, by each of the
        # three routes it can be recognised through.
        ({"TERM": "xterm-kitty", "LANG": "en_US.UTF-8"}, GLYPHS_NERD),
        ({"TERM": "xterm-ghostty", "LANG": "en_US.UTF-8"}, GLYPHS_NERD),
        ({"TERM": "xterm-256color", "TERM_PROGRAM": "WezTerm",
          "LANG": "en_US.UTF-8"}, GLYPHS_NERD),
        ({"TERM": "screen-256color", "KITTY_WINDOW_ID": "1",
          "LANG": "en_US.UTF-8"}, GLYPHS_NERD),
        # ...and the variable a user sets to say so outright.
        ({"TERM": "xterm-256color", "NERD_FONT": "1",
          "LANG": "en_US.UTF-8"}, GLYPHS_NERD),
        # An ordinary terminal on a UTF-8 locale gets box drawing and no more.
        ({"TERM": "xterm-256color", "LANG": "en_US.UTF-8"}, GLYPHS_UNICODE),
        # A locale that is not UTF-8 cannot be sent box drawing at all.
        ({"TERM": "xterm-256color", "LANG": "en_US.ISO-8859-1"}, GLYPHS_ASCII),
        ({"TERM": "xterm-256color"}, GLYPHS_ASCII),
        # LC_ALL outranks LANG, as POSIX orders them.
        ({"TERM": "xterm-256color", "LC_ALL": "C",
          "LANG": "en_US.UTF-8"}, GLYPHS_ASCII),
        # A terminal that cannot be assumed to do anything gets nothing.
        ({"TERM": "dumb", "LANG": "en_US.UTF-8"}, GLYPHS_ASCII),
        # The override outranks every one of those, in both directions.
        ({"TERM": "dumb", "NAVKIT_GLYPHS": "nerd"}, GLYPHS_NERD),
        ({"TERM": "xterm-kitty", "LANG": "en_US.UTF-8",
          "NAVKIT_GLYPHS": "ascii"}, GLYPHS_ASCII),
        ({"TERM": "xterm-kitty", "LANG": "en_US.UTF-8",
          "NAVKIT_GLYPHS": "unicode"}, GLYPHS_UNICODE),
        # A typo is ignored rather than fatal, as with NAVKIT_COLORS.
        ({"TERM": "xterm-kitty", "LANG": "en_US.UTF-8",
          "NAVKIT_GLYPHS": "lots"}, GLYPHS_NERD),
    ],
)
def test_the_glyph_tier_is_read_from_the_environment(env, expected):
    assert TerminalInfo.detect(env, is_tty=True).glyphs == expected


@pytest.mark.parametrize(
    "env, default, expected",
    [
        # Nothing said: the caller's own answer stands.
        ({"TERM": "xterm", "LANG": "en_US.UTF-8"}, GLYPHS_NERD, GLYPHS_NERD),
        ({"TERM": "xterm", "LANG": "en_US.UTF-8"}, GLYPHS_ASCII, GLYPHS_ASCII),
        # ...and the variable outranks it, as it does for the palette.
        ({"TERM": "xterm", "NAVKIT_GLYPHS": "unicode"}, GLYPHS_NERD, GLYPHS_UNICODE),
    ],
)
def test_a_caller_may_state_the_glyph_tier_outright(env, default, expected):
    assert TerminalInfo.detect(env, glyphs=default).glyphs == expected


def test_a_multiplexer_hides_the_terminal_underneath():
    """A documented limit rather than a defect.

    Inside tmux ``TERM`` becomes ``screen-256color`` and the marker variables
    are not forwarded, so there is nothing left to recognise -- which is what
    ``NAVKIT_GLYPHS`` is for.
    """
    env = {"TERM": "screen-256color", "LANG": "en_US.UTF-8", "TMUX": "/tmp/sock"}
    assert TerminalInfo.detect(env).glyphs == GLYPHS_UNICODE
    assert TerminalInfo.detect(env | {"NAVKIT_GLYPHS": "nerd"}).glyphs == GLYPHS_NERD


def test_the_convenience_properties_follow_the_tier():
    assert TerminalInfo(glyphs=GLYPHS_NERD).nerd_font
    assert TerminalInfo(glyphs=GLYPHS_NERD).unicode
    assert not TerminalInfo(glyphs=GLYPHS_UNICODE).nerd_font
    assert TerminalInfo(glyphs=GLYPHS_UNICODE).unicode
    assert not TerminalInfo(glyphs=GLYPHS_ASCII).unicode


def test_everything_on_includes_the_top_glyph_tier():
    assert FULL.glyphs == GLYPHS_NERD

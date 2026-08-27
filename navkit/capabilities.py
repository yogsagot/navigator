"""What the terminal on the other end can actually do.

:class:`TerminalInfo` is a set of flags and the decisions that follow from
them.  It exists so that those decisions are made **once, at the edge**, rather
than being spread through the code that draws: a widget asks for the colour it
wants, a stylesheet records the colour the original asked for, and only the
last step before bytes reach the tty asks whether this terminal can express it.

That order matters for the themes in particular.  Eight of DOS Navigator's
eleven palettes reprogram the sixteen VGA colour registers, so the only honest
transcription of one is the exact ``#rrggbb`` it asked for -- ``BW.PAL`` is a
greyscale ramp whose *blue* register holds a grey, and writing ``blue`` in the
sheet would come back a real blue on any terminal.  Baking a sixteen-colour
approximation into the ``.nss`` at generation time would throw the original
away for good, and on a terminal that can show it, for nothing.  Keeping the
palette exact and quantising here gives the same result on a sixteen-colour
terminal and the right one everywhere else.

An *index* is the other half of the same question.  A sheet that says ``blue``
is not asking for whatever blue the terminal's own theme paints: it is the
transcription of a palette that left the VGA colour registers alone, and those
registers held values.  :attr:`TerminalInfo.palette` is where a caller says so.
Set it and an index resolves to the colour the adapter really held, before the
quantiser runs -- which costs nothing on a sixteen-colour terminal, where the
result quantises straight back to the index it came from, and is what makes a
theme look the same everywhere rather than only on terminals whose own palette
happens to resemble a VGA one.  Left unset -- the default, because the kit
knows nothing about DOS -- an index is passed through as it always was.

Detection is deliberately conservative.  A terminal that does not say it
supports more is assumed to do sixteen colours, because being downgraded on a
capable terminal is a disappointment and being upgraded on an incapable one is
a screenful of unreadable escape sequences.  ``NAVKIT_COLORS`` overrides the
guess when the guess is wrong.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, replace
from functools import lru_cache
from typing import Mapping

from navkit.glyphs import (
    GLYPHS_ASCII,
    GLYPHS_NERD,
    GLYPHS_UNICODE,
    tier_named,
)
from navkit.style import Color, Style

#: Colour depths, as the number of distinct colours the terminal can name.
#: Compared with ``>=`` throughout, so the exact values only have to be ordered.
MONOCHROME = 2
ANSI = 8
ANSI_BRIGHT = 16
EXTENDED = 256
TRUECOLOR = 1 << 24

#: The glyph tiers are re-exported here so that a caller reading one kind of
#: capability off this module can read the other from it too.  They are
#: defined in :mod:`navkit.glyphs`, with the character sets they govern.
__all__ = ["GLYPHS_ASCII", "GLYPHS_UNICODE", "GLYPHS_NERD", "TerminalInfo"]

#: Terminals that **bundle** a Nerd Font symbol fallback, so the icons render
#: whatever font the user configured.  That is a fact about the emulator
#: rather than a guess about the font, which is what makes it safe to act on;
#: every other terminal has to say so itself.
_NERD_TERM_PROGRAMS = ("wezterm", "ghostty")
_NERD_TERM_FRAGMENTS = ("kitty", "ghostty")
_NERD_MARKERS = ("KITTY_WINDOW_ID", "WEZTERM_PANE", "GHOSTTY_RESOURCES_DIR")

#: What ``NAVKIT_COLORS`` accepts, beyond a plain number.
_DEPTH_NAMES = {
    "mono": MONOCHROME,
    "monochrome": MONOCHROME,
    "none": MONOCHROME,
    "8": ANSI,
    "ansi": ANSI,
    "16": ANSI_BRIGHT,
    "256": EXTENDED,
    "truecolor": TRUECOLOR,
    "24bit": TRUECOLOR,
    "full": TRUECOLOR,
}

#: The sixteen ANSI colours as most terminals render them, in **navkit's**
#: index order -- which is ANSI's, where 1 is red and 4 is blue, and not the
#: DOS order the palettes are written in.  Only a reference for quantising: a
#: terminal's own theme decides what it really paints, which is exactly why an
#: index is left alone whenever the terminal can name it.
_ANSI_RGB = (
    (0, 0, 0), (170, 0, 0), (0, 170, 0), (170, 85, 0),
    (0, 0, 170), (170, 0, 170), (0, 170, 170), (170, 170, 170),
    (85, 85, 85), (255, 85, 85), (85, 255, 85), (255, 255, 85),
    (85, 85, 255), (255, 85, 255), (85, 255, 255), (255, 255, 255),
)

#: The same sixteen under the name that says what they *are*: the IBM VGA
#: adapter's default DAC.  A DOS palette that reprograms no register is asking
#: for exactly these.  ``tools/palconv.py`` carries them too, as the six-bit
#: values a ``.PAL`` stores and in DOS's index order; here they are widened
#: (``42 -> 170``, ``21 -> 85``, ``63 -> 255``) and in ANSI's.  One table
#: serves both jobs -- the reference the quantiser measures against, and the
#: meaning an index has when a caller pins one.
VGA_PALETTE = _ANSI_RGB

#: The 6x6x6 colour cube's per-channel levels, and the 24 greys after it.
_CUBE_LEVELS = (0, 95, 135, 175, 215, 255)


def _xterm_256() -> tuple[tuple[int, int, int], ...]:
    """The 256-colour palette: 16 system colours, a 6x6x6 cube, then greys."""
    colors = list(_ANSI_RGB)
    for r in _CUBE_LEVELS:
        for g in _CUBE_LEVELS:
            for b in _CUBE_LEVELS:
                colors.append((r, g, b))
    colors.extend((level, level, level) for level in range(8, 239, 10))
    return tuple(colors)


_XTERM_256 = _xterm_256()


def _distance(a: tuple[int, int, int], b: tuple[int, int, int]) -> int:
    """Squared "redmean" distance -- cheap, and much closer to the eye than RGB.

    Plain Euclidean distance in RGB puts a saturated blue and a mid grey nearer
    each other than either is to what they look like, which shows up as the
    wrong sixteen-colour approximation for exactly the dark blues these
    palettes are full of.
    """
    mean = (a[0] + b[0]) // 2
    dr, dg, db = a[0] - b[0], a[1] - b[1], a[2] - b[2]
    return (
        ((512 + mean) * dr * dr >> 8)
        + 4 * dg * dg
        + ((767 - mean) * db * db >> 8)
    )


@lru_cache(maxsize=4096)
def _nearest(rgb: tuple[int, int, int], count: int) -> int:
    """The index of the closest of the first *count* palette entries to *rgb*.

    Indices 0-15 are skipped when quantising into the 256-colour palette: what
    a terminal paints for those is its own theme's business, so picking one
    would make the result depend on something we cannot see.  The cube and the
    grey ramp are fixed, and are what the extended palette is for.
    """
    start = 16 if count > ANSI_BRIGHT else 0
    candidates = range(start, count)
    return min(candidates, key=lambda index: _distance(rgb, _XTERM_256[index]))


def rgb_of(color: Color) -> tuple[int, int, int]:
    """*color* as an ``(r, g, b)`` triple, resolving a palette index."""
    if isinstance(color, tuple):
        return color
    if 0 <= color < len(_XTERM_256):
        return _XTERM_256[color]
    return (0, 0, 0)


def _nerd_font(env: Mapping[str, str]) -> bool:
    """Whether Nerd Font glyphs can be expected to arrive as shapes.

    Two kinds of evidence, and neither is a guess about which font the user
    picked.  ``NERD_FONT`` is the de-facto variable a user already sets to say
    so; the rest name terminals that ship the symbol fallback themselves.

    A multiplexer hides all of it -- inside tmux or screen ``TERM`` becomes
    ``screen-256color`` and the marker variables are not forwarded -- so a
    session there reports Unicode and ``NAVKIT_GLYPHS=nerd`` is the answer.
    """
    if env.get("NERD_FONT", "").strip().lower() in ("1", "true", "yes"):
        return True
    if env.get("TERM_PROGRAM", "").strip().lower() in _NERD_TERM_PROGRAMS:
        return True
    term = env.get("TERM", "")
    if any(fragment in term for fragment in _NERD_TERM_FRAGMENTS):
        return True
    return any(env.get(marker) for marker in _NERD_MARKERS)


def _utf8(env: Mapping[str, str]) -> bool:
    """Whether the locale says this terminal is reading UTF-8.

    Most specific first, as POSIX orders them: ``LC_ALL`` overrides
    ``LC_CTYPE``, which overrides ``LANG``.
    """
    for name in ("LC_ALL", "LC_CTYPE", "LANG"):
        value = env.get(name, "")
        if value:
            return "utf-8" in value.lower() or "utf8" in value.lower()
    return False


@dataclass(frozen=True)
class TerminalInfo:
    """What this terminal supports, and what to do about it.

    Every field is a plain flag so that a caller may state one outright rather
    than discovering it -- ``TerminalInfo(colors=ANSI_BRIGHT)`` in a test, or
    :meth:`detect` in an application.
    """

    #: How many distinct colours the terminal can name.  One of the constants
    #: above; compared with ``>=``, never for equality.
    colors: int = ANSI_BRIGHT
    #: Whether ``\x1b[?1049h`` will be honoured.  False leaves the scrollback
    #: alone, which is what a pipe or a ``dumb`` terminal wants.
    alt_screen: bool = True
    #: Whether to ask for mouse reports at all.
    mouse: bool = True
    #: Whether to ask for bracketed paste, so a paste arrives as one event.
    bracketed_paste: bool = True
    #: Whether ``OSC 0`` sets something a user can see.
    title: bool = True
    #: What a palette index *means* -- sixteen ``(r, g, b)`` triples, or
    #: ``None`` to leave that to the terminal's own theme.  See :meth:`adapt`.
    #: A tuple rather than a list because this dataclass has to stay hashable.
    palette: tuple[tuple[int, int, int], ...] | None = None
    #: Which characters will arrive as shapes: one of the ``GLYPHS_*`` tiers,
    #: compared with ``>=``.  Unicode is the assumption when nobody has said
    #: otherwise, box drawing being safe on any terminal of the last thirty
    #: years that reads UTF-8.
    glyphs: int = GLYPHS_UNICODE

    @property
    def truecolor(self) -> bool:
        return self.colors >= TRUECOLOR

    @property
    def monochrome(self) -> bool:
        return self.colors < ANSI

    @property
    def nerd_font(self) -> bool:
        return self.glyphs >= GLYPHS_NERD

    @property
    def unicode(self) -> bool:
        return self.glyphs >= GLYPHS_UNICODE

    @classmethod
    def detect(
        cls,
        env: Mapping[str, str] | None = None,
        *,
        is_tty: bool = True,
        palette: tuple[tuple[int, int, int], ...] | None = None,
        glyphs: int | None = None,
    ) -> TerminalInfo:
        """Read the environment for what this terminal admits to.

        The rules, most specific first:

        - ``NAVKIT_COLORS`` wins outright, being the escape hatch for when the
          rest of this guesses wrong.  It takes a depth name or a number.
        - ``NO_COLOR`` set to anything means no colour, per no-color.org.
        - ``COLORTERM`` is the only reliable statement of truecolor support.
        - ``TERM`` carrying ``256color`` means the extended palette; ``dumb``
          or nothing at all means a terminal that cannot be assumed to do
          anything, and the interactive features are switched off with it.
        - Anything else gets sixteen colours, which has been safe since about
          1990 and is the conservative half of a guess that has to be made.

        *palette* is the caller's own answer to what an index means -- an
        application that transcribes a fixed palette states it here rather than
        discovering it, since no environment variable could say.
        ``NAVKIT_PALETTE`` overrides it either way: ``dos`` or ``vga`` pins the
        VGA registers, ``terminal`` (or ``none``, ``off``) hands the question
        back to the terminal's own theme.

        *glyphs* is the same arrangement for the character repertoire, and
        ``NAVKIT_GLYPHS`` (``ascii``, ``unicode``, ``nerd``) overrides it.  Left
        to itself the guess runs: a plain terminal gets ASCII, one of the
        emulators in :func:`_nerd_font` gets the Nerd tier, a UTF-8 locale gets
        Unicode, and anything else gets ASCII -- conservative in the same
        direction as the colour guess, since a missing glyph is a replacement
        box on every line of the frame.
        """
        env = os.environ if env is None else env
        plain = not is_tty or env.get("TERM", "") in ("", "dumb")

        colors = ANSI_BRIGHT
        if plain:
            colors = MONOCHROME
        elif env.get("COLORTERM", "").lower() in ("truecolor", "24bit"):
            colors = TRUECOLOR
        elif "256color" in env.get("TERM", ""):
            colors = EXTENDED

        if env.get("NO_COLOR"):
            colors = MONOCHROME
        override = env.get("NAVKIT_COLORS", "").strip().lower()
        if override:
            if override in _DEPTH_NAMES:
                colors = _DEPTH_NAMES[override]
            elif override.isdigit():
                colors = int(override)

        if glyphs is None:
            if plain:
                glyphs = GLYPHS_ASCII
            elif _nerd_font(env):
                glyphs = GLYPHS_NERD
            elif _utf8(env):
                glyphs = GLYPHS_UNICODE
            else:
                glyphs = GLYPHS_ASCII
        glyphs = tier_named(env.get("NAVKIT_GLYPHS", ""), glyphs)

        choice = env.get("NAVKIT_PALETTE", "").strip().lower()
        if choice in ("dos", "vga"):
            palette = VGA_PALETTE
        elif choice in ("terminal", "none", "off"):
            palette = None

        return cls(
            colors=colors,
            palette=palette,
            glyphs=glyphs,
            alt_screen=not plain,
            mouse=not plain,
            bracketed_paste=not plain,
            title=not plain,
        )

    def adapt(self, color: Color | None) -> Color | None:
        """*color* as the nearest thing this terminal can actually name.

        With no :attr:`palette` set, an index the terminal can name is returned
        untouched, so a sheet that says ``blue`` keeps whatever blue the user's
        own theme paints.  Only a colour it cannot name -- a truecolor triple
        on a sixteen-colour tty, a 256-palette index on an eight-colour one --
        is quantised, and then against a fixed reference.

        With a palette set, an index is first resolved to the colour that
        palette holds for it and then treated like any other triple.  On a
        sixteen-colour terminal that is a round trip: :func:`_nearest` searches
        the very table :data:`VGA_PALETTE` came from and hands back the index
        it started with.  So pinning only ever changes what a terminal that can
        do better is asked for, which is what makes it safe to do by default.
        """
        if color is None:
            return color
        if self.monochrome:
            return None
        if self.palette and isinstance(color, int) and 0 <= color < len(self.palette):
            color = self.palette[color]
        if self.colors >= TRUECOLOR:
            return color
        if isinstance(color, int) and color < min(self.colors, ANSI_BRIGHT):
            return color
        rgb = rgb_of(color)
        if self.colors >= EXTENDED:
            return _nearest(rgb, EXTENDED)
        nearest = _nearest(rgb, ANSI_BRIGHT)
        # An eight-colour terminal has no bright half; fold onto the base hue
        # rather than dropping to the nearest of eight, which would send a
        # bright yellow to brown by way of a much longer detour.
        return nearest if self.colors >= ANSI_BRIGHT else nearest % ANSI

    def adapt_style(self, style: Style) -> Style:
        """*style* with both its colours put through :meth:`adapt`."""
        fg, bg = self.adapt(style.fg), self.adapt(style.bg)
        if fg == style.fg and bg == style.bg:
            return style
        return replace(style, fg=fg, bg=bg)

    def sgr(self, style: Style) -> str:
        """The escape sequence selecting *style* on this terminal."""
        return _sgr(self, style)


@lru_cache(maxsize=2048)
def _sgr(info: TerminalInfo, style: Style) -> str:
    """Memoised because a frame asks for very few distinct styles, repeatedly."""
    return info.adapt_style(style).sgr()


#: Everything on, for a caller that has no terminal to ask -- rendering to a
#: string, a test, a buffer someone else will decide what to do with.
FULL = TerminalInfo(colors=TRUECOLOR, glyphs=GLYPHS_NERD)

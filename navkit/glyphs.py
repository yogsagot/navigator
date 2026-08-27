"""What the terminal's font can draw, and the character sets that follow.

The character half of :mod:`navkit.capabilities`.  Colour has one question --
how many colours can this terminal name -- and this is the other one: which
*characters* will actually arrive as shapes rather than as replacement boxes.

Three tiers, ordered, compared with ``>=`` exactly as the colour depths are:

``GLYPHS_ASCII``
    Nothing above US-ASCII can be relied on.  A pipe, a ``dumb`` terminal, or
    a locale that is not UTF-8.
``GLYPHS_UNICODE``
    The box-drawing and block ranges are safe.  This is what any terminal on a
    UTF-8 locale gets, and what the kit assumes when it has nobody to ask.
``GLYPHS_NERD``
    The Private Use Area carries the Nerd Font icon set.

The last of those cannot be *detected*, only argued about, and it is worth
being blunt about why.  No escape sequence reports the font a terminal is
using.  The usual trick -- print a glyph, ask for the cursor column with
``CSI 6n``, infer from how far it moved -- measures the terminal's own width
table and not whether the font has an outline for the codepoint, so on the
terminals where the answer is genuinely unknown it reports the same thing
either way.  :func:`navkit.capabilities.TerminalInfo.detect` therefore names
the terminals that *ship* a Nerd Font fallback and leaves everything else to
say so itself.

Box character sets are held here rather than in :mod:`navkit.screen` because
they are a vocabulary, and a vocabulary is what a stylesheet names.  ``screen``
takes the six characters and draws them; it never learns their names, which is
what keeps the buffer free of any runtime knowledge of capabilities.
"""

from __future__ import annotations

#: The glyph repertoires, as ordered tiers.  Compared with ``>=`` throughout,
#: so only their order is meaningful.
GLYPHS_ASCII = 1
GLYPHS_UNICODE = 2
GLYPHS_NERD = 3

#: What ``NAVKIT_GLYPHS`` and ``--glyphs`` accept.
GLYPH_NAMES = {
    "ascii": GLYPHS_ASCII,
    "unicode": GLYPHS_UNICODE,
    "utf8": GLYPHS_UNICODE,
    "utf-8": GLYPHS_UNICODE,
    "nerd": GLYPHS_NERD,
    "nerdfont": GLYPHS_NERD,
    "nerd-font": GLYPHS_NERD,
}

#: A box character set is six characters, in the order :meth:`Surface.draw_box`
#: unpacks them: top-left, top-right, bottom-left, bottom-right, horizontal,
#: vertical.
SINGLE_BOX = "┌┐└┘─│"
DOUBLE_BOX = "╔╗╚╝═║"
ROUND_BOX = "╭╮╰╯─│"
ASCII_BOX = "++++-|"

#: The sets a stylesheet may name in a ``border`` declaration.
BOX_CHARSETS = {
    "single": SINGLE_BOX,
    "double": DOUBLE_BOX,
    "round": ROUND_BOX,
    "ascii": ASCII_BOX,
}

#: What an unrecognised ``border`` value means.  A stylesheet comes from a file
#: a user edits, so a typo there degrades rather than stopping the program --
#: the same posture ``NAVKIT_COLORS`` takes towards a depth it cannot read.
DEFAULT_BOX = "single"


def charset(name: str, tier: int = GLYPHS_UNICODE) -> str:
    """The named box character set, degraded to what *tier* can render.

    Note that no tier above :data:`GLYPHS_UNICODE` changes the answer: box
    drawing is ordinary Unicode and a Nerd Font adds nothing to it.  The tier
    matters at the *lower* boundary, where every set collapses to
    :data:`ASCII_BOX` because nothing else would arrive as a shape.  Icons are
    where :data:`GLYPHS_NERD` earns its place, and they are the application's
    vocabulary rather than the kit's.
    """
    chars = BOX_CHARSETS.get(name, BOX_CHARSETS[DEFAULT_BOX])
    return ASCII_BOX if tier < GLYPHS_UNICODE else chars


def tier_named(name: str, default: int | None = None) -> int | None:
    """The tier *name* stands for, or *default* if it names nothing.

    Ignoring an unreadable name rather than raising is deliberate and matches
    :func:`navkit.capabilities.TerminalInfo.detect`: the name arrives from an
    environment variable or a command line, and a typo there must not stop the
    program from starting.
    """
    return GLYPH_NAMES.get(name.strip().lower(), default)

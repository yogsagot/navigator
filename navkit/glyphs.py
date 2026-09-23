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

The widget library's vocabularies -- frame joins, scrollbar characters, check
and radio marks -- sit beside the box sets for the same reason, and every one
of them answers the same three questions a box set does.  **The third answer is
the same for all of them: a Nerd Font improves on none of them.**  Every shape
here is box-drawing, block-element or geometric-shape, all of which
:data:`GLYPHS_UNICODE` already guarantees; the Private Use Area carries icons
and no better arrow, shade or tee.  The one case with a real candidate is a
check box, where ``nf-fa-check_square`` is a single glyph -- and it is refused
because it collapses three cells into one and would move every caption in a
cluster.  Icons remain the application's vocabulary, and
``navigator/icons.py`` records why they are the project's one deliberate
departure rather than a licence for more.
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

#: The frame a widget draws when nothing says otherwise, and what
#: :func:`charset` falls back to for a name it does not know.  A sheet can no
#: longer be the source of such a name -- ``Widget.border`` declares this
#: vocabulary, so ``border: dubble`` fails at its ``.nss`` line -- but
#: :func:`charset` is callable directly and still answers rather than raising,
#: the posture ``NAVKIT_COLORS`` takes towards a depth it cannot read.
DEFAULT_BOX = "single"

#: Where an inner rule meets a frame: left tee, right tee, top tee, bottom
#: tee, cross.  Keyed by the **frame's** name rather than standing alone,
#: because a tee has to line up with the corners around it -- a single divider
#: descending from a double top edge is ``╤`` and not ``┬``.  Every divider
#: DOS Navigator draws is single, which is what makes one table enough instead
#: of a matrix of frame against rule.
SINGLE_JOINS = "├┤┬┴┼"
DOUBLE_JOINS = "╟╢╤╧┼"
ROUND_JOINS = "├┤┬┴┼"
ASCII_JOINS = "+++++"

#: Parallel to :data:`BOX_CHARSETS`, one entry per key.  A widget reads it
#: through the same ``border`` property, so the two cannot disagree: there is
#: deliberately no ``joins`` declaration a sheet could set on its own, because
#: ``border: double`` with ``+`` tees is a bug and not a preference.
BOX_JOINS = {
    "single": SINGLE_JOINS,
    "double": DOUBLE_JOINS,
    "round": ROUND_JOINS,
    "ascii": ASCII_JOINS,
}

#: A scrollbar's six characters, in the order a scrollbar draws them: up,
#: down, left, right, track, thumb.  Turbo Vision keeps the same five in
#: ``TScrollBar.Chars`` and DOS Navigator inherits them unchanged -- CP437 30,
#: 31, 17, 16 for the arrows, 177 for the shaded track and 254 for the thumb.
DOS_SCROLLBAR = "▲▼◄►▒■"
ASCII_SCROLLBAR = "^v<>:#"

#: The sets a ``chars`` declaration may name on a scrollbar.
SCROLLBARS = {"dos": DOS_SCROLLBAR, "ascii": ASCII_SCROLLBAR}
DEFAULT_SCROLLBAR = "dos"

#: Four marks: check box off, check box on, radio off, radio on.  The brackets
#: around them are *not* here.  ``[ ]`` and ``( )`` are ASCII in the original
#: too and are fixed in the widget, which is how Turbo Vision spells them --
#: what varies between tiers is only what goes in the middle.
DOS_MARKS = " X \u2022"
ASCII_MARKS = " X *"

#: The sets a ``marks`` declaration may name on a cluster.
MARKS = {"dos": DOS_MARKS, "ascii": ASCII_MARKS}
DEFAULT_MARKS = "dos"


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


def joins(name: str, tier: int = GLYPHS_UNICODE) -> str:
    """The five tee characters that match the named box set.

    Takes the *frame's* name, not a name of its own, because the two have to
    agree: a single rule meeting a double frame is ``╤`` and a double frame
    drawn with ``+`` tees is simply wrong.  One argument makes that
    unexpressible.
    """
    chars = BOX_JOINS.get(name, BOX_JOINS[DEFAULT_BOX])
    return ASCII_JOINS if tier < GLYPHS_UNICODE else chars


def scrollbar(name: str, tier: int = GLYPHS_UNICODE) -> str:
    """The named scrollbar characters, degraded to what *tier* can render."""
    chars = SCROLLBARS.get(name, SCROLLBARS[DEFAULT_SCROLLBAR])
    return ASCII_SCROLLBAR if tier < GLYPHS_UNICODE else chars


def marks(name: str, tier: int = GLYPHS_UNICODE) -> str:
    """The named check and radio marks, degraded to what *tier* can render.

    Only the radio dot actually moves: ``X`` and the two blanks are ASCII in
    every set, which is why the ASCII form reads as a near-copy rather than as
    a fallback.  That is the original's doing -- CP437's check box was ``[X]``
    on a VGA text screen too.
    """
    chars = MARKS.get(name, MARKS[DEFAULT_MARKS])
    return ASCII_MARKS if tier < GLYPHS_UNICODE else chars


def tier_named(name: str, default: int | None = None) -> int | None:
    """The tier *name* stands for, or *default* if it names nothing.

    Ignoring an unreadable name rather than raising is deliberate and matches
    :func:`navkit.capabilities.TerminalInfo.detect`: the name arrives from an
    environment variable or a command line, and a typo there must not stop the
    program from starting.
    """
    return GLYPH_NAMES.get(name.strip().lower(), default)

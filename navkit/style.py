"""Cell styling.

A :class:`Style` is an immutable description of how a single screen cell looks.
It knows how to emit itself as an SGR escape sequence; nothing else in navkit
writes colour codes by hand.

The stylesheet library and its lookup engine will grow on top of this module;
for now this is only the value type they will resolve to.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

#: A colour is either a palette index (0-255) or a true-colour ``(r, g, b)``
#: triple.  Indices 0-7 are the classic ANSI colours, 8-15 their bright
#: variants -- the full palette DOS Navigator ever used.
type Color = int | tuple[int, int, int]

BLACK = 0
RED = 1
GREEN = 2
BROWN = 3
BLUE = 4
MAGENTA = 5
CYAN = 6
LIGHT_GRAY = 7
DARK_GRAY = 8
LIGHT_RED = 9
LIGHT_GREEN = 10
YELLOW = 11
LIGHT_BLUE = 12
LIGHT_MAGENTA = 13
LIGHT_CYAN = 14
WHITE = 15


def _color_sgr(color: Color, *, background: bool) -> str:
    """Return the SGR parameters selecting *color* as fore- or background."""
    if isinstance(color, tuple):
        r, g, b = color
        return f"{48 if background else 38};2;{r};{g};{b}"
    if 0 <= color <= 7:
        return str((40 if background else 30) + color)
    if 8 <= color <= 15:
        return str((100 if background else 90) + color - 8)
    return f"{48 if background else 38};5;{color}"


@dataclass(frozen=True, slots=True)
class Style:
    """How a cell is painted.  ``None`` means "the terminal's default"."""

    fg: Color | None = None
    bg: Color | None = None
    bold: bool = False
    dim: bool = False
    italic: bool = False
    underline: bool = False
    reverse: bool = False

    def derive(self, **changes) -> Style:
        """Return a copy of this style with *changes* applied."""
        return replace(self, **changes)

    def sgr(self) -> str:
        """Return the full escape sequence selecting this style.

        The sequence always starts with a reset, so it is self-contained: the
        renderer can emit it without knowing what was in effect before.
        """
        params = ["0"]
        if self.bold:
            params.append("1")
        if self.dim:
            params.append("2")
        if self.italic:
            params.append("3")
        if self.underline:
            params.append("4")
        if self.reverse:
            params.append("7")
        if self.fg is not None:
            params.append(_color_sgr(self.fg, background=False))
        if self.bg is not None:
            params.append(_color_sgr(self.bg, background=True))
        return "\x1b[" + ";".join(params) + "m"


#: The terminal's own colours -- what an unpainted cell looks like.
DEFAULT_STYLE = Style()

RESET_SGR = "\x1b[0m"
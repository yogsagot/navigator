"""Line drawing: DOS Navigator's ``DrawLine`` (``MICROED.PAS``).

The editor draws box lines a cell at a time.  A cell's character is chosen
from a 15-entry table by a four-bit mask of the arms it has -- up 1, right 2,
down 4, left 8, DN's ``1 shl Dir`` -- in one of four tables: single strokes
both ways, double both ways, or single one way and double the other, so a new
line meets an old one of the other weight with the right junction.

*Drawing* a cell gives it an arm towards each neighbour that reaches it (the
``…Contact`` sets), one back the way the pen came and one the way it goes.
*Erasing* blanks the cell and takes from each neighbour that is a junction --
three arms or four, DN's ``I in [7, 11, 13, 14, 15]`` -- the arm that pointed
into it; a straight line or a corner beside it is left as it stands.
"""

from __future__ import annotations

#: The four tables, by mask; index 0 is unused, as DN's strings were 1-based.
SINGLE = " │─└││┌├─┘─┴┐┤┬┼"            # ``Line00``: single both ways
DOUBLE = " ║═╚║║╔╠═╝═╩╗╣╦╬"            # ``Line11``: double both ways
SINGLE_V = " │═╘││╒╞═╛═╧╕╡╤╪"          # ``Line01``: single up and down, double across
DOUBLE_V = " ║─╙║║╓╟─╜─╨╖╢╥╫"          # ``Line10``: double up and down, single across

#: Which characters reach towards the cell beside them, in single strokes and in double.
UP_CONTACT = (frozenset("│├┼┤┌┬┐╞╪╡╒╤╕"), frozenset("║╠╬╣╔╦╗╟╫╢╓╥╖"))
DOWN_CONTACT = (frozenset("│├┼┤└┴┘╞╪╡╘╧╛"), frozenset("║╠╬╣╚╩╝╟╫╢╙╨╜"))
LEFT_CONTACT = (frozenset("─├┼┌└┬┴╟╫╓╙╥╨"), frozenset("═╠╬╔╚╦╩╞╪╒╘╤╧"))
RIGHT_CONTACT = (frozenset("─┤┼┐┘┬┴╢╫╖╜╥╨"), frozenset("═╣╬╗╝╦╩╡╪╕╛╤╧"))

#: The directions, as DN numbered them: up, right, down, left.
UP, RIGHT, DOWN, LEFT = range(4)


def _vertical(up: str, down: str, weight: int) -> int:
    """``GetV0``/``GetV1``: arms up and down to neighbours of *weight* that reach this cell."""
    return (1 if up in UP_CONTACT[weight] else 0) | (4 if down in DOWN_CONTACT[weight] else 0)


def _horizontal(left: str, right: str, weight: int) -> int:
    """``GetH0``/``GetH1``: arms left and right to neighbours of *weight* that reach this cell."""
    return (2 if right in RIGHT_CONTACT[weight] else 0) | (8 if left in LEFT_CONTACT[weight] else 0)


def drawn(
    up: str, right: str, down: str, left: str, *, double: bool, direction: int, came: int | None,
) -> str:
    """The character the pen leaves in a cell, moving *direction*, having come from *came*.

    The pen's weight sets the stroke along its way; across, a neighbour of the
    other weight is met with the mixed table when none of its own weight is.
    """
    own, other = (1, 0) if double else (0, 1)
    table = DOUBLE if double else SINGLE
    vertical = _vertical(up, down, own)
    horizontal = _horizontal(left, right, own)
    if direction in (RIGHT, LEFT):
        if not vertical:
            vertical = _vertical(up, down, other)
            if vertical:
                table = SINGLE_V if double else DOUBLE_V
    else:
        if not horizontal:
            horizontal = _horizontal(left, right, other)
            if horizontal:
                table = DOUBLE_V if double else SINGLE_V
    mask = vertical | horizontal | (1 << direction)
    if came is not None:
        mask |= 1 << came
    return table[mask]


def without_arm(char: str, arm: int) -> str | None:
    """``Modify``: a junction *char* less its *arm* (a mask bit), or None to leave it.

    Only a junction of three arms or four is changed, and only if it has the
    arm; one left with none is a blank.
    """
    for table in (SINGLE, SINGLE_V, DOUBLE_V, DOUBLE):
        index = table.find(char, 1)
        if index > 0:
            break
    else:
        return None
    if index not in (7, 11, 13, 14, 15):
        return None
    mask = index & ~arm
    if mask == index:
        return None
    return table[mask] if mask else " "

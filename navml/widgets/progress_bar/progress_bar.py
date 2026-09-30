"""A bar that fills as work gets done -- a component written in Python alone.

DOS Navigator's gauge, which ``StrGrd`` built as a *string* and
``TWhileView`` wrote as a line of text: ``█`` for the part done, ``▒`` for the
rest, in the dialog's static-text colour.  Here it is a widget, because a
string has a length and a widget has a width: the bar is as long as whatever
placed it says, and a box made wider takes its gauge with it.

Python alone for the reason ``CheckBoxes`` is: everything it has is a value
and everything it shows is painted, so a document would hold nothing but a
head.  The model is Textual's ``ProgressBar`` -- ``value`` out of ``total``
-- and the look is DOS Navigator's; the percentage and any count are for
whoever places the bar to write beside it, as ``TWhileView``'s were.
"""

from __future__ import annotations

from navkit.glyphs import DEFAULT_GAUGE, GAUGES, gauge
from navkit.reactive import computed, reactive
from navkit.screen import Surface
from navkit.stylesheet import StyleProperty
from navkit.widget import Widget


class ProgressBar(Widget):
    """``value`` out of ``total``, as a bar as wide as the widget."""

    #: How far the work has got, and how far it goes.  A total of 0 or less
    #: is work with nothing in it, which is done -- ``Percent(0, 0)`` was 100.
    value: int = reactive(0)
    total: int = reactive(0)

    #: Which characters the bar is drawn from.
    chars = StyleProperty(DEFAULT_GAUGE, values=tuple(GAUGES))

    #: The part done, so a sheet may colour it apart from the rest.  DOS
    #: Navigator drew both halves in one colour; the characters told them apart.
    parts = ("done",)

    @computed
    def fraction(self) -> float:
        """How much is done, from 0 to 1."""
        if self.total <= 0:
            return 1.0
        return min(1.0, max(0.0, self.value / self.total))

    @computed
    def percent(self) -> int:
        """DN's ``Percent``: whole percent, rounded down, so 100 means finished."""
        if self.total <= 0:
            return 100
        return min(100, max(0, self.value * 100 // self.total))

    def render(self, surface: Surface) -> None:
        if self.width < 1 or self.height < 1:
            return
        done_char, rest_char = gauge(self.chars, self.glyphs)
        if self.total <= 0:
            filled = self.width
        else:
            filled = min(self.width, max(0, self.value * self.width // self.total))
        for y in range(self.height):
            surface.fill(0, y, filled, 1, done_char, self.part_style("done"))
            surface.fill(filled, y, self.width - filled, 1, rest_char, self.style)

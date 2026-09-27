"""The arithmetic and the painting behind ``scroll_bar.nml``.

**It emits rather than being read.**  Everywhere else in this library a value
that changes is a reactive attribute and a reader binds to it; here the owner
has to be able to tell "the user dragged the bar" from "I moved the bar
because the list scrolled", and a single reactive cannot say which.  So a
gesture raises a :class:`ScrollEvent` carrying where the user asked to go, and
the owner decides -- which is the same division the rest of the library rests
on, read from the other side: a reactive carries what a thing *is*, an event
carries what just *happened*.

It is not focusable.  Turbo Vision's is not either: a scrollbar is a mouse
affordance beside a view that already has the keys.
"""

from __future__ import annotations

from dataclasses import dataclass

from navkit.events import Event, MouseClickEvent
from navkit.glyphs import DEFAULT_SCROLLBAR, SCROLLBARS, scrollbar
from navkit.screen import Surface
from navkit.stylesheet import StyleProperty
from navkit.widget import Widget


@dataclass(frozen=True, slots=True)
class ScrollEvent(Event):
    """The user asked to scroll somewhere.

    Carries the value because it has to: an event with no fields cannot say
    *where*, and unlike a click there is no second question whose answer is
    obvious.  Declared in this half because markup's ``event`` line declares a
    fieldless one.
    """

    value: int


class ScrollBar(Widget):
    """A bar showing where a view sits in something longer than itself."""

    emits = (ScrollEvent,)

    #: Which characters the arrows, track and thumb are drawn from.
    chars = StyleProperty(DEFAULT_SCROLLBAR, values=tuple(SCROLLBARS))

    #: ``[36]`` covers both of these in the original, which carries two slots
    #: for a scrollbar and not three.  They are separate here because a sheet
    #: that wants to tell them apart should be able to, and one that does not
    #: writes one rule naming both.
    parts = ("arrow", "thumb")

    @property
    def vertical(self) -> bool:
        return self.orientation != "horizontal"

    @property
    def length(self) -> int:
        """The bar's long side."""
        return self.height if self.vertical else self.width

    @property
    def track(self) -> int:
        """The cells between the two arrows."""
        return max(0, self.length - 2)

    @property
    def thumb(self) -> int:
        """Where the thumb sits along the track, in cells from its start."""
        if self.maximum <= 0 or self.track < 1:
            return 0
        return min(self.track - 1, self.value * (self.track - 1) // self.maximum)

    def _ask(self, value: int) -> int:
        return min(max(value, 0), max(0, self.maximum))

    async def scroll_to(self, value: int) -> bool:
        """Ask the owner to go to *value*.  It decides; this does not move."""
        return await self.emit(ScrollEvent(self._ask(value)))

    async def on_mouse_click(self, event: MouseClickEvent) -> bool:
        if event.is_wheel:
            step = -self.step if event.button == "wheel_up" else self.step
            return await self.scroll_to(self.value + step * 3)
        if event.action != "press" or event.button != "left":
            return False
        along = event.y if self.vertical else event.x
        if along <= 0:
            return await self.scroll_to(self.value - self.step)
        if along >= self.length - 1:
            return await self.scroll_to(self.value + self.step)
        cell = along - 1
        if cell < self.thumb:
            return await self.scroll_to(self.value - self.page)
        if cell > self.thumb:
            return await self.scroll_to(self.value + self.page)
        return True

    def render(self, surface: Surface) -> None:
        if self.length < 2 or self.width < 1 or self.height < 1:
            return
        chars = scrollbar(self.chars, self.glyphs)
        up, down, left, right, track, thumb = chars
        arrow_style, thumb_style = self.part_style("arrow"), self.part_style("thumb")
        first, last = (up, down) if self.vertical else (left, right)

        def put(along: int, char: str, style) -> None:
            if self.vertical:
                surface.set_cell(0, along, char, style)
            else:
                surface.set_cell(along, 0, char, style)

        put(0, first, arrow_style)
        put(self.length - 1, last, arrow_style)
        for cell in range(self.track):
            put(cell + 1, track, self.style)
        if self.maximum > 0:
            put(self.thumb + 1, thumb, thumb_style)

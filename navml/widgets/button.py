"""The handlers behind ``button.nml``.

This file never names the generated class.  ``class Button(Widget)`` is what a
Python-only component would say too, which is what lets a component gain or
lose its markup half without this file changing -- see *Why the generated base
is hidden* in ``navml/DESIGN.md``.  The base repeats the one the markup
declares, and :mod:`navml._merge` refuses the pair if the two disagree.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from navkit.events import Event, KeyEvent, MouseClickEvent
from navkit.reactive import reactive
from navkit.screen import Surface
from navkit.widget import Widget


@dataclass(frozen=True, slots=True)
class ClickEvent(Event):
    """The button was pressed, by whichever route.

    Declared here, beside the widget that emits it, rather than in navkit:
    navkit knows about terminal input and nothing a widget *means*.  navkit
    derives the handler name from the class -- ``ClickEvent`` -> ``on_click``
    -- so nothing is registered anywhere, and a document that uses a Button
    writes ``on_click:`` without importing this class at all.

    Carrying no fields is what lets two routes raise the same event: a mouse
    press and a keypress are the same click to whoever is listening, and the
    button is what knows they are.
    """


class Button(Widget):
    """A pressable box.

    The worked example of a component with an event of its own: two input
    routes, one thing they both mean.  Space and Enter arrive as keys and a
    left press arrives by position, and neither of those is what a listener
    cares about -- so both go through :meth:`press`, which emits one
    :class:`ClickEvent`.  A document using a Button writes ``on_click:`` and
    never learns which route fired.
    """

    #: What this widget emits, read through :func:`navkit.events.emitted`.
    #: The declaration is the public surface: navml's generator checks an
    #: ``on_click:`` line against it, and a reader sees it without reading
    #: :meth:`press`.
    emits = (ClickEvent,)

    #: Whether the button responds at all.  A *state*, so it is reactive
    #: rather than a signal -- which is the division the whole event
    #: mechanism rests on: reactive attributes carry what a thing *is*, an
    #: event carries what just *happened*.  Declared in this half rather than
    #: the markup's because nothing in ``button.nml`` reads it.
    enabled: bool = reactive(True)

    def __init__(self, text: str = "", **kwargs: Any) -> None:
        # The markup half's tree is built by this call, so every id is live
        # from the next line on.
        super().__init__(**kwargs)
        self.text = text

    async def press(self) -> bool:
        """Emit the click.  False if disabled, or if nothing claimed it."""
        if not self.enabled:
            return False
        return await self.emit(ClickEvent())

    async def on_key(self, event: KeyEvent) -> bool:
        if event.name in ("enter", "space"):
            return await self.press()
        return False

    async def on_mouse_click(self, event: MouseClickEvent) -> bool:
        if event.action == "press" and event.button == "left":
            return await self.press()
        return False

    def render(self, surface: Surface) -> None:
        surface.fill(0, 0, self.width, self.height, " ", self.style)

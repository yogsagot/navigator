"""The handlers behind ``button.nml``.

This file never names the generated class.  ``class Button(Control)`` is what a
Python-only component would say too, which is what lets a component gain or
lose its markup half without this file changing -- see *Why the generated base
is hidden* in ``navml/DESIGN.md``.  The base repeats the one the markup
declares, and :mod:`navml._merge` refuses the pair if the two disagree.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from navkit.events import Event, KeyEvent, MouseClickEvent
from navkit.screen import Surface
from navkit.style import Style

from navml.widgets.control import Control


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


class Button(Control):
    """A pressable box.

    The worked example of a component with an event of its own: three input
    routes, one thing they all mean.  Space and Enter arrive as keys, a left
    press arrives by position, and ``Alt+O`` arrives from a dialog that went
    looking for the letter -- and none of those is what a listener cares
    about, so all three go through :meth:`press`, which emits one
    :class:`ClickEvent`.  A document using a Button writes ``on_click:`` and
    never learns which route fired.

    **It is two rows tall and one column wider than its face.**  Turbo Vision
    draws a button's shadow one cell right and one cell down, and putting
    those cells inside the button's own rectangle rather than over whatever is
    behind it is what lets one be placed anywhere without its owner knowing.
    """

    #: What this widget emits, read through :func:`navkit.events.emitted`.
    #: The declaration is the public surface: navml's generator checks an
    #: ``on_click:`` line against it, and a reader sees it without reading
    #: :meth:`press`.
    emits = (ClickEvent,)

    #: The drop shadow, ``[46]`` in the original.  A part rather than a colour
    #: on the widget because it is painted *with* the button and is not the
    #: button: it takes whatever is behind it and darkens it.
    parts = ("shadow",)

    def __init__(self, text: str = "", **kwargs: Any) -> None:
        # The markup half's tree is built by this call, so every id is live
        # from the next line on.
        super().__init__(**kwargs)
        self.text = text

    async def press(self) -> bool:
        """Emit the click.  False if disabled, or if nothing claimed it."""
        if self.disabled:
            return False
        return await self.emit(ClickEvent())

    async def activate(self, letter: str = "") -> bool:
        """What ``Alt+O`` does: take the keyboard, then press.

        Both, and in that order, because the original does both -- a shortcut
        is a faster route to the same button rather than a way of pressing one
        without visiting it.
        """
        self.focus()
        return await self.press()

    async def on_key(self, event: KeyEvent) -> bool:
        if event.name in ("enter", "space"):
            return await self.press()
        return False

    async def on_mouse_click(self, event: MouseClickEvent) -> bool:
        # Up to `Control' first, which takes the keyboard and claims nothing;
        # a press on a button means both things and this is the order they
        # happen in.
        await super().on_mouse_click(event)
        if event.action == "press" and event.button == "left":
            return await self.press()
        return False

    @property
    def face(self) -> tuple[int, int]:
        """The width and height of the button itself, shadow excluded."""
        return max(0, self.width - 1), max(0, self.height - 1)

    def render(self, surface: Surface) -> None:
        width, height = self.face
        if width < 1 or height < 1:
            return
        style = self.style
        surface.fill(0, 0, width, height, " ", style)
        if width >= 2:
            surface.draw_text(0, 0, "[", style)
            surface.draw_text(width - 1, 0, "]", style)
        self._render_shadow(surface, width, height)

    def _render_shadow(self, surface: Surface, width: int, height: int) -> None:
        """Darken the cells one right and one below the face.

        Read-modify-write rather than a fill, because a shadow is *the thing
        behind it, darker* -- Turbo Vision darkens the attribute of whatever
        is there and keeps the character.  ``Surface.get`` is on the base
        class, so this works through a view like everything else.
        """
        shadow: Style = self.part_style("shadow")
        for y in range(height):
            char = surface.get(width, y)[0] or " "
            surface.set_cell(width, y, char, shadow)
        for x in range(1, width + 1):
            char = surface.get(x, height)[0] or " "
            surface.set_cell(x, height, char, shadow)

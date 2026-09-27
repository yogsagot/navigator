"""The status line: DOS Navigator's key hints, and what each one asks for now.

Turbo Vision's ``TStatusLine``, drawn the way ``TStatusLine.DrawSelect`` draws
it: the items packed from the left edge, each a space, its key in the
*Shortcut* colour, its caption, and a space -- `` F1 Help  F2 User  F3 View ``.
**The items are read off the bindings, not written here.**  Each function key
that asks for a command from where the keyboard is gets an item captioned with
that command's title, and a key nothing binds gets none, so the line closes up
round it the way the original's did round a key its status definition left
out.  An item whose command cannot run is greyed whole, key included, in the
status line's *Disabled* slot.

The original also swapped the whole line while Alt, Ctrl or Shift was held --
the ``-``, ``+`` and ``:`` items of ``StatusDef hcFilePanel``.  A terminal
reports no key releases, so a held modifier cannot be seen, and that half is
not attempted.
"""

from __future__ import annotations

from navkit.commands import Command, key_label
from navkit.events import MouseClickEvent
from navkit.screen import Surface
from navkit.widget import Widget

#: How many function keys the line looks for.
KEYS = 10


class KeyBar(Widget):
    """The status line across the bottom of the screen."""

    #: An item's key, and its caption.  Both take ``:disabled``, because Turbo
    #: Vision greys an unavailable item whole, its key included.
    parts = ("key", "label")

    def items(self) -> list[tuple[str, Command, int, int]]:
        """``(key, command, start, width)`` for each item, left to right.

        *width* counts the space either side, as ``DrawSelect`` advances by
        it; an item is left out unless its text, without those two spaces,
        ends before the right edge -- ``I + L < Size.X`` there, which lets the
        last item's trailing space fall off the end.
        """
        app = self.application
        bound = app.bindings() if app is not None else {}
        found, column = [], 0
        for index in range(KEYS):
            key = f"f{index + 1}"
            command = bound.get(key)
            if command is None or not command.title:
                continue
            width = len(key_label(key)) + 1 + len(command.title) + 2
            if column + width - 2 >= self.width:
                break
            found.append((key, command, column, width))
            column += width
        return found

    def render(self, surface: Surface) -> None:
        app = self.application
        surface.fill(0, 0, self.width, 1, " ", self.part_style("label"))
        for key, command, start, _width in self.items():
            disabled = app is not None and not app.command_enabled(command)
            label = self.part_style("label", disabled=disabled)
            name = key_label(key)
            surface.draw_text(start, 0, " ", label)
            surface.draw_text(
                start + 1, 0, name, self.part_style("key", disabled=disabled)
            )
            surface.draw_text(start + 1 + len(name), 0, f" {command.title} ", label)

    async def on_mouse_click(self, event: MouseClickEvent) -> bool:
        """A press on an item asks for its command, as the key would.

        Claimed wherever it lands, so that a click on a greyed item or on the
        empty end of the line does not fall through to what is behind it.
        """
        if event.action != "press" or event.button != "left":
            return False
        app = self.application
        for _key, command, start, width in self.items():
            if start <= event.x < start + width and app is not None:
                await app.run_command(command)
                break
        return True

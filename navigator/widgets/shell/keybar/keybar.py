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

**While Alt, Ctrl or Shift is held the whole line is that modifier's** --
the ``-``, ``+`` and ``:`` items of ``StatusDef hcFilePanel`` -- read off the
same bindings: every key bound with exactly the modifiers held, the function
keys first and in order, then the letters in the order the tables declare
them.  Each item shows the key alone, ``F6`` or ``B``, as the original did --
the row is what says which modifier is down.  The held set is
:attr:`Application.modifiers`, which is reactive, so the row swaps on the
press and swaps back on the release; only a terminal speaking the kitty
keyboard protocol reports either, and on any other the plain row is all there
is.
"""

from __future__ import annotations

from navkit.commands import Command, key_label, layer_key
from navkit.events import MouseClickEvent
from navkit.i18n import tr
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

        *key* is the binding's full spec -- ``"alt+f6"`` while Alt is held --
        and the item shows it without the modifiers.  *width* counts the space
        either side, as ``DrawSelect`` advances by it; an item is left out
        unless its text, without those two spaces, ends before the right edge
        -- ``I + L < Size.X`` there, which lets the last item's trailing space
        fall off the end.
        """
        found, column = [], 0
        for key, command in self._row():
            width = len(_shown(key)) + 1 + len(tr(command.title)) + 2
            if column + width - 2 >= self.width:
                break
            found.append((key, command, column, width))
            column += width
        return found

    def _row(self) -> list[tuple[str, Command]]:
        """The titled bindings for the modifiers held, in the line's order."""
        app = self.application
        if app is None:
            return []
        bound = app.bindings()
        held = app.modifiers
        keys = [layer_key(held, f"f{index + 1}") for index in range(KEYS)]
        if held:
            letters = {layer_key(held, chr(c)) for c in range(ord("a"), ord("z") + 1)}
            keys += [key for key in bound if key in letters]
        return [
            (key, bound[key])
            for key in keys
            if key in bound and bound[key].title
        ]

    def render(self, surface: Surface) -> None:
        app = self.application
        surface.fill(0, 0, self.width, 1, " ", self.part_style("label"))
        for key, command, start, _width in self.items():
            disabled = app is not None and not app.command_enabled(command)
            label = self.part_style("label", disabled=disabled)
            name = _shown(key)
            surface.draw_text(start, 0, " ", label)
            surface.draw_text(
                start + 1, 0, name, self.part_style("key", disabled=disabled)
            )
            surface.draw_text(start + 1 + len(name), 0, f" {tr(command.title)} ", label)

    async def on_mouse_click(self, event: MouseClickEvent) -> bool:
        """A press on an item asks for its command, as the key would.

        Claimed wherever it lands, so that a click on a greyed item or on the
        empty end of the line does not fall through to what is behind it.
        While a modifier is held the row is that modifier's, and so is what a
        click on it runs.
        """
        if event.action != "press" or event.button != "left":
            return False
        app = self.application
        for _key, command, start, width in self.items():
            if start <= event.x < start + width and app is not None:
                await app.run_command(command)
                break
        return True


def _shown(key: str) -> str:
    """How an item spells its key: ``"alt+f6"`` is ``F6``, as ``~F6~`` was."""
    return key_label(key.rsplit("+", 1)[-1])

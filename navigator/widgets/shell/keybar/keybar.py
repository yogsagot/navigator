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

**And the keys no table names** -- a list's Space, a mode's arrows, the keys a
popup takes for itself -- are hints the widgets give (:meth:`Widget.key_hints`),
asked from the focus out, the nearest first.  One labelled ``F2`` takes F2's
place in the plain row; the rest lead it, before the function keys -- they say
what the keyboard does now, and a file panel's ten function keys fill the line,
so the last of those give way to them.  A box never says
its keys in its own frame: they belong here, as DN's ``StatusDef`` put them
(a departure where DN said nothing at all, asked for).

**An item's tooltip is where its command sits in the menus** -- ``File > Make
directory`` for ``F7 MkDir`` -- read off the menu bar (:attr:`KeyBar.menu`,
the window's own menus included), so no caption is written twice.  A command
no menu offers shows its caption; a hint shows nothing more than it says.
A departure: DN had no tooltips.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from navkit.commands import Command, chain, key_label, layer_key
from navkit.events import MouseClickEvent
from navkit.i18n import tr
from navkit.screen import Surface
from navkit.tooltip import lines, plain
from navkit.widget import Widget
from navml.widgets.dialog.control.control import parse_shortcut

#: How many function keys the line looks for.
KEYS = 10


@dataclass(frozen=True)
class Hint:
    """A key the line names that runs no command of its own: a widget's
    :meth:`~navkit.widget.Widget.key_hints` entry.  ``title`` is shown as it
    is, already translated; the item is never greyed and a click does nothing."""

    title: str


class KeyBar(Widget):
    """The status line across the bottom of the screen."""

    #: An item's key, and its caption.  Both take ``:disabled``, because Turbo
    #: Vision greys an unavailable item whole, its key included.
    parts = ("key", "label")

    #: The menu bar whose entries name the items' commands in their tooltips;
    #: None for none.
    menu: Any = None

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
            width = len(_label(key, command)) + 1 + len(_title(command)) + 2
            if column + width - 2 >= self.width:
                break
            found.append((key, command, column, width))
            column += width
        return found

    def _row(self) -> list[tuple[str, Command | Hint]]:
        """The titled bindings for the modifiers held, in the line's order --
        with no modifier held, the hints too."""
        app = self.application
        if app is None:
            return []
        bound = app.bindings()
        held = app.modifiers
        keys = [layer_key(held, f"f{index + 1}") for index in range(KEYS)]
        if held:
            letters = {layer_key(held, chr(c)) for c in range(ord("a"), ord("z") + 1)}
            keys += [key for key in bound if key in letters]
            return [(key, bound[key]) for key in keys if key in bound and bound[key].title]
        hints = self.hints()
        slots = {key_label(key): key for key in keys}
        row: list[tuple[str, Command | Hint]] = [
            (label, Hint(title)) for label, title in hints.items() if label not in slots
        ]
        for key in keys:
            label = key_label(key)
            if label in hints:
                row.append((label, Hint(hints[label])))
            elif key in bound and bound[key].title:
                row.append((key, bound[key]))
        return row

    def hints(self) -> dict[str, str]:
        """Every widget's :meth:`~navkit.widget.Widget.key_hints` from the
        focus out, by label, the nearest first and winning a label twice given."""
        app = self.application
        found: dict[str, str] = {}
        if app is None:
            return found
        for widget in chain(app):
            for label, title in getattr(widget, "key_hints", lambda: ())():
                found.setdefault(label, title)
        return found

    def menu_hint(self) -> str:
        """The open menu's highlighted entry's hint, on one line, or ``""``:
        what Turbo Vision's ``THintStatusLine`` put on the status line while a
        menu was open (:meth:`MenuBar.hint`)."""
        menu = self.menu
        hint = getattr(menu, "hint", None)
        if hint is None:
            return ""
        return " -- ".join(line for line in plain(hint()).split("\n") if line)

    def render(self, surface: Surface) -> None:
        app = self.application
        surface.fill(0, 0, self.width, 1, " ", self.part_style("label"))
        hint = self.menu_hint()
        if hint:
            surface.draw_text(1, 0, hint, self.part_style("label"), max(0, self.width - 1))
            return
        for key, command, start, _width in self.items():
            hint = isinstance(command, Hint)
            disabled = not hint and app is not None and not app.command_enabled(command)
            label = self.part_style("label", disabled=disabled)
            name = _label(key, command)
            surface.draw_text(start, 0, " ", label)
            surface.draw_text(
                start + 1, 0, name, self.part_style("key", disabled=disabled)
            )
            surface.draw_text(start + 1 + len(name), 0, f" {_title(command)} ", label)

    def tooltip_at(self, x: int, y: int) -> str:
        """The item's command's place in the menus, ``File > Make directory``,
        else its caption, and why it is greyed while it is; nothing for a hint,
        between items, or while the bar shows an open menu's hint."""
        if self.menu_hint():
            return ""
        app = self.application
        for _key, command, start, width in self.items():
            if start <= x < start + width:
                if isinstance(command, Hint):
                    return ""
                path = self.menu.path_to(command) if self.menu is not None else []
                # A caption's ``...`` says a box opens, which a tooltip need not.
                names = (parse_shortcut(entry.text)[0].rstrip(".…").rstrip() for entry in path)
                where = " > ".join(names) if path else _title(command)
                reason = ""
                if app is not None and not app.command_enabled(command):
                    reason = app.command_disabled_reason(command)
                return lines(where, reason)
        return super().tooltip_at(x, y)

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
                if not isinstance(command, Hint):
                    await app.run_command(command)
                break
        return True


def _label(key: str, item: Command | Hint) -> str:
    """An item's key as shown: a hint's label as given, a binding's spelled."""
    return key if isinstance(item, Hint) else _shown(key)


def _title(item: Command | Hint) -> str:
    """An item's caption: a hint's is translated already."""
    return item.title if isinstance(item, Hint) else tr(item.title)


def _shown(key: str) -> str:
    """How an item spells its key: ``"alt+f6"`` is ``F6``, as ``~F6~`` was."""
    return key_label(key.rsplit("+", 1)[-1])

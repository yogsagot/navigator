"""The function key bar: F1 to F10, and what each one asks for right now.

DOS Navigator's status line, which is Turbo Vision's ``TStatusLine``: a row of
key captions that are also buttons.  **The captions are read off the bindings,
not written here.**  Each of the ten keys shows the title of the command it
would run from where the keyboard is -- the panel keys while a panel has it,
the application's own keys everywhere -- in the status line's *Disabled*
colour when that command cannot run, which today is every file operation not
yet written.  A key nothing binds shows its number alone.

The original also swapped the whole row while Alt, Ctrl or Shift was held.  A
terminal reports no key releases, so a held modifier cannot be seen, and that
half is not attempted.
"""

from __future__ import annotations

from navkit.commands import Command
from navkit.events import MouseClickEvent
from navkit.screen import Surface
from navkit.widget import Widget

#: How many function keys the bar shows.
KEYS = 10


class KeyBar(Widget):
    """The F1..F10 hint bar across the bottom of the screen."""

    #: The digit in front of each caption, and the caption.  Both take a
    #: ``:disabled`` state, because Turbo Vision greys an unavailable item
    #: whole, its key included.
    parts = ("number", "label")

    def slot_width(self) -> int:
        """Columns per key: the bar shared evenly, never narrower than three."""
        return max(3, self.width // KEYS)

    def commands(self) -> list[Command | None]:
        """What F1 to F10 ask for now, in order; None for an unbound key."""
        app = self.application
        bound = app.bindings() if app is not None else {}
        return [bound.get(f"f{index + 1}") for index in range(KEYS)]

    def render(self, surface: Surface) -> None:
        app = self.application
        surface.fill(0, 0, self.width, 1, " ", self.part_style("label"))
        slot = self.slot_width()
        for index, command in enumerate(self.commands()):
            column = index * slot
            if column >= self.width:
                break
            disabled = (
                command is not None
                and app is not None
                and not app.command_enabled(command)
            )
            number = str(index + 1)
            title = command.title if command is not None else ""
            surface.draw_text(
                column, 0, number, self.part_style("number", disabled=disabled)
            )
            surface.draw_text(
                column + len(number),
                0,
                title.ljust(slot - len(number)),
                self.part_style("label", disabled=disabled),
                slot - len(number),
            )

    async def on_mouse_click(self, event: MouseClickEvent) -> bool:
        """A press on a caption asks for its command, as the key would.

        Claimed whether or not it ran anything, so that a click on a greyed
        caption does not fall through to whatever is behind the bar.
        """
        if event.action != "press" or event.button != "left":
            return False
        index = event.x // self.slot_width()
        commands = self.commands()
        app = self.application
        if 0 <= index < len(commands) and commands[index] is not None and app:
            await app.run_command(commands[index])
        return True

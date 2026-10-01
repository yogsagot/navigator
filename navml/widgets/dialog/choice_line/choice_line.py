"""A line that is chosen into, never typed into.

Not Turbo Vision's: its dialogs had only the input line and its history.
This is the third shape a dialog needs once a value has to be one of a fixed
list -- a user, a group -- and a typo is not something to be told about on
OK but something that cannot happen.

**Every key it is offered drops the list**, Enter included, apart from the
ones that belong to the dialog around it: Tab and Shift+Tab move on, Esc
dismisses, Alt+letter is a shortcut, and Up and Down are left for a dialog
that moves between its lines with them -- one that does not leaves them
doing nothing, which a line that cannot be typed into loses nothing by.  A printable key also
starts the list's quick search with itself, so typing ``ro`` on the line
lands on ``root`` -- the free typing the line refuses, put where it can only
name something in the list.  A click drops it too, and a paste is refused.

It is an :class:`InputLine` underneath so that it looks like one, takes the
focus like one and is linked by the ``▐↓▌`` button like one; the button is
what drops the list (:attr:`History.choices`), and the line only asks it to.
"""

from __future__ import annotations

from navkit.events import DoubleClickEvent, KeyEvent, MouseClickEvent, PasteEvent

from navml.widgets.dialog.input_line import InputLine


class ChoiceLine(InputLine):
    """An input line whose text comes only from its button's list."""

    async def on_key(self, event: KeyEvent) -> bool:
        if self.inert or event.alt or event.matches("tab", "shift+tab", "escape", "up", "down"):
            return False
        self.drop(event.char if event.is_printable and event.char else "")
        return True

    def drop(self, typed: str = "") -> bool:
        """Drop the list, searching it for *typed*; False if there is none."""
        button = self.history
        window = button.open() if button is not None else None
        if window is None:
            return False
        if typed:
            window.search_for(typed)
        return True

    async def on_mouse_click(self, event: MouseClickEvent) -> bool:
        if self.inert or event.button != "left":
            return False
        if event.action == "press":
            self.focus()
            self.drop()
        return True

    async def on_double_click(self, event: DoubleClickEvent) -> bool:
        return not self.inert

    async def on_paste(self, event: PasteEvent) -> bool:
        return False

    def select_all(self) -> None:
        """Nothing to select: the text is never edited, so it is never marked."""
        self.cursor = 0

    def cursor_position(self) -> tuple[int, int] | None:
        """No caret: nothing typed here would land."""
        return None

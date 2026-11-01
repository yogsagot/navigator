"""The calculator's expression line: DN's ``TCalcLine``."""

from __future__ import annotations

from navkit.events import KeyEvent, PasteEvent

from navml.widgets.dialog.input_line import InputLine


class CalcLine(InputLine):
    """An input line that, holding a result *Evaluate* put in, lets a digit
    replace it and anything else go on from it (``ResultSelected``): ``*2``
    after an answer doubles it, ``7`` starts afresh.  A character the face
    has no use for (a space, ``$``, ``8`` in octal) is refused, typed or
    pasted."""

    result_selected = False
    #: The characters that may be typed; empty, anything (Classic, DN's).
    accepts: frozenset[str] = frozenset()

    def admits(self, text: str) -> bool:
        """Whether every character of *text* may go into the line."""
        return not self.accepts or all(char in self.accepts for char in text)

    async def on_key(self, event: KeyEvent) -> bool:
        if event.is_printable and event.char and not self.admits(event.char):
            return True
        if self.result_selected:
            self.result_selected = False
            if event.is_printable and event.char and not event.char.isdigit():
                self.anchor = None
                self.cursor = len(self.value)
        return await super().on_key(event)

    async def on_paste(self, event: PasteEvent) -> bool:
        """A paste with a character the face refuses is refused whole: a
        number's spaces are dropped (``1 000``), as the other faces' line
        takes none."""
        if self.accepts and not self.inert:
            text = "".join(event.text.split())
            if text and self.admits(text):
                self._replace_selection(text)
            return True
        return await super().on_paste(event)

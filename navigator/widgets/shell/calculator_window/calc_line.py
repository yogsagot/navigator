"""The calculator's expression line: DN's ``TCalcLine``."""

from __future__ import annotations

import re

from navkit.events import KeyEvent, PasteEvent

from navml.widgets.dialog.input_line import InputLine


class CalcLine(InputLine):
    """An input line that, holding a result *Evaluate* put in, lets a digit
    replace it and anything else go on from it (``ResultSelected``): ``*2``
    after an answer doubles it, ``7`` starts afresh.  A character the face
    has no use for (a space, ``$``, ``8`` in octal) is refused, typed or
    pasted.  The named operators in :attr:`words` may be typed letter by
    letter, though, and once whole get the spaces round them that the
    refused space cannot give: ``FF``, ``AND``, ``1`` is ``FF AND 1``."""

    result_selected = False
    #: The characters that may be typed; empty, anything (Classic, DN's).
    accepts: frozenset[str] = frozenset()
    #: Operators spelt out, typed beside :attr:`accepts`; one that ends
    #: another (``NAND``, ``AND``) comes first.
    words: tuple[str, ...] = ()

    def admits(self, text: str) -> bool:
        """Whether every character of *text* may go into the line."""
        return not self.accepts or all(char in self.accepts for char in text)

    def spelling(self, head: str) -> tuple[str, bool] | None:
        """The word *head* ends partway through, and whether it is whole --
        a whole word first, so ``ROR`` is not the ``R`` of another."""
        upper = head.upper()
        whole = next((word for word in self.words if upper.endswith(word)), None)
        if whole:
            return whole, True
        for word in self.words:
            if any(upper.endswith(word[:length]) for length in range(1, len(word))):
                return word, False
        return None

    def _type(self, char: str) -> bool:
        """*char* typed at the caret, or refused; a word it finishes spaced."""
        start = self.selection[0]
        head = self.value[:start] + char
        if not self.admits(char) and self.spelling(head) is None:
            return False
        self._replace_selection(char)
        spelt = self.spelling(head)
        if spelt and spelt[1]:
            word, before = spelt[0], head[: -len(spelt[0])].rstrip()
            head = (f"{before} " if before and not before.endswith("(") else before) + f"{word} "
            self.value = head + self.value[start + 1:].lstrip()
            self.cursor = len(head)
        return True

    async def on_key(self, event: KeyEvent) -> bool:
        if event.is_printable and event.char and self.accepts and not self.inert:
            if self.result_selected:
                self.result_selected = False
                if not event.char.isdigit():
                    self.anchor = None
                    self.cursor = len(self.value)
            self._type(event.char)
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
        takes none, but kept round a word (``FF and 1``)."""
        if self.accepts and not self.inert:
            parts = re.split(rf"\b({'|'.join(self.words)})\b", event.text, flags=re.I) if self.words else [event.text]
            numbers = ["".join(part.split()) for part in parts[::2]]
            if all(self.admits(part) for part in numbers):
                words = [f" {word.upper()} " for word in parts[1::2]]
                text = "".join(part + (words[index] if index < len(words) else "")
                               for index, part in enumerate(numbers))
                if text:
                    self._replace_selection(text)
            return True
        return await super().on_paste(event)

"""The calculator's expression line: DN's ``TCalcLine``."""

from __future__ import annotations

from navkit.events import KeyEvent

from navml.widgets.dialog.input_line import InputLine


class CalcLine(InputLine):
    """An input line that, holding a result *Evaluate* put in, lets a digit
    replace it and anything else go on from it (``ResultSelected``): ``*2``
    after an answer doubles it, ``7`` starts afresh."""

    result_selected = False

    async def on_key(self, event: KeyEvent) -> bool:
        if self.result_selected:
            self.result_selected = False
            if event.is_printable and event.char and not event.char.isdigit():
                self.anchor = None
                self.cursor = len(self.value)
        return await super().on_key(event)

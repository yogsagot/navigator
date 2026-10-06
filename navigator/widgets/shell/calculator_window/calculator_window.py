"""The calculator's behaviour: the indicator, *Evaluate*, *Copy*, and a
dialog's keys in a window (:mod:`navigator.calculator` does the sums)."""

from __future__ import annotations

from typing import Any

from navkit.events import Event, KeyEvent
from navkit.reactive import effect
from navml.history import HISTORY
from navml.widgets.dialog.commands import Cancel, Default, SelectNext, SelectPrevious
from navml.widgets.dialog.control.control import Control
from navml.widgets.window import Window

from navigator import calculator

#: The window's size and place, as ``dlgCalculator`` and ``R.Move(10, 5)``.
WIDTH, HEIGHT = 49, 15
X, Y = 10, 5


class CalculatorWindow(Window):
    """DN's calculator: one line in, five forms out."""

    def mounted(self) -> None:
        super().mounted()
        effect(self, CalculatorWindow._recalculate)

    def _recalculate(self) -> None:
        """``SetValues(Off)``: the indicator, from the line as it stands."""
        self.rows = self.indicator(self.line.value)

    @staticmethod
    def indicator(text: str) -> list[str]:
        """``TIndicator.Draw``'s five rows for *text*: *Error* alone in the
        middle when it cannot be worked out, *Overflow* for a form it is past."""
        try:
            value = calculator.evaluate(text)
        except calculator.CalcError:
            return ["", "", "Error", "", ""]
        forms = [calculator.radix(value, base) for base in (16, 2, 8)]
        return [calculator.decimal(value), *(form or "Overflow" for form in forms),
                calculator.exponent(value)]

    # -- what the buttons and keys do ---------------------------------------------------

    def evaluate(self) -> None:
        """``SetValues(On)``: the line becomes its value, selected, and what it
        was goes into the history."""
        try:
            value = calculator.evaluate(self.line.value)
        except calculator.CalcError:
            return
        HISTORY.add("calc", self.line.value.strip())
        self.line.value = calculator.decimal(value)
        self.line.select_all()
        self.line.result_selected = True
        self.line.focus()

    def copy_value(self) -> None:
        """``cmCopyClip``: the value in *Copy As*'s form on the clipboard --
        nothing for an error, or a form it overflows."""
        app = self.application
        try:
            value = calculator.evaluate(self.line.value)
        except calculator.CalcError:
            return
        text = calculator.shown(value, calculator.COPY_AS[self.copy_as.value])
        if text is not None and app is not None:
            app.copy_to_clipboard(text)

    def leave(self) -> None:
        """Esc and *Close*: the line into the history, as ``TCalcLine`` put it,
        and the window gone."""
        HISTORY.add("calc", self.line.value.strip())
        self.request_close()

    async def on_default(self, event: Default) -> bool:
        self.evaluate()
        return True

    async def on_cancel(self, event: Cancel) -> bool:
        self.leave()
        return True

    async def on_evaluate_button_click(self, event: Event) -> bool:
        self.evaluate()
        return True

    async def on_copy_button_click(self, event: Event) -> bool:
        self.copy_value()
        return True

    async def on_close_button_click(self, event: Event) -> bool:
        self.leave()
        return True

    async def on_select_next(self, event: SelectNext) -> bool:
        self._step(1)
        return True

    async def on_select_previous(self, event: SelectPrevious) -> bool:
        self._step(-1)
        return True

    def _step(self, by: int) -> None:
        """Tab within this window, wrapping, as a dialog's Tab stays in it."""
        order = [widget for widget in self.focusable() if widget is not self]
        if not order:
            return
        app = self.application
        focused = app.focused if app is not None else None
        index = order.index(focused) if focused in order else (-1 if by > 0 else 0)
        order[(index + by) % len(order)].focus()

    async def on_key(self, event: KeyEvent) -> bool:
        """Alt and a marked letter: that control, as a dialog's ``Alt+letter`` walk."""
        if event.alt and not event.ctrl and len(event.key) == 1 and event.key.isalpha():
            for control in self._controls(self):
                if control.shortcut_match(event.key):
                    return await control.activate(event.key)
        return await super().on_key(event)

    @classmethod
    def _controls(cls, widget: Any) -> list[Control]:
        found: list[Control] = []
        for child in widget.children:
            if not child.visible:
                continue
            if isinstance(child, Control):
                found.append(child)
            found.extend(cls._controls(child))
        return found

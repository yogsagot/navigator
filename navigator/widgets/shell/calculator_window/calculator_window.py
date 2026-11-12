"""The calculator's behaviour: its four faces and switching between them,
the classic indicator, the pads' keys, *Evaluate*, *Copy*, and a dialog's
keys in a window (:mod:`navigator.lib.utilities.calculator` does the sums).

*Classic* is DN's calculator.  *Simple*, *Scientific* and *Programming* are
a departure, asked for: each puts a pad of keys under the same line, which
they type into as the keyboard does -- the line is an expression, the pads a
quicker way of writing one -- with its value worked out under it.
"""

from __future__ import annotations

import contextlib
from typing import Any

from navkit.events import KeyEvent
from navkit.i18n import tr
from navkit.reactive import effect, peek, untracked
from navml.history import HISTORY
from navml.widgets.dialog.control.control import Control
from navml.widgets.window import Window

from navigator.lib.utilities import calculator
from navigator.lib.utilities.calculator import CLASSIC, CalcError, Context, Number
from navigator.settings import SETTINGS, CalculatorData, save_or_say
from navigator.widgets.shell.calculator_window.bit_grid import BitFlipped
from navigator.widgets.shell.calculator_window.commands import (
    CalculatorClassic,
    CalculatorProgramming,
    CalculatorScientific,
    CalculatorSimple,
    ToggleBitKeypad,
)
from navigator.widgets.shell.calculator_window.keypad import Key, PadPressed
from navigator.widgets.shell.calculator_window.keys import PADS

#: The four faces, in the strip's and the menu's order.
MODES = CalculatorData.MODES
#: Each face's window: *Classic* is ``dlgCalculator``'s two rows taller, for the strip.
#: All four fit an 80 by 24 screen's desktop of 21 rows.
SIZES = {"simple": (32, 20), "classic": (49, 17), "scientific": (62, 20), "programming": (62, 21)}
#: Where a new calculator opens: ``R.Move(10, 5)``, as DN put it.
X, Y = 10, 5
#: The programmer's bases and words, in their radio buttons' order.
RADIXES = {"hex": 16, "dec": 10, "oct": 8, "bin": 2}
WORDS = {"qword": 64, "dword": 32, "word": 16, "byte": 8}
#: How wide a value is written back into the line.
LINE_WIDTH = 40
#: The commands that choose a face, by face.
MODE_COMMANDS = {CalculatorSimple: "simple", CalculatorClassic: "classic",
                 CalculatorScientific: "scientific", CalculatorProgramming: "programming"}
#: What may be typed into the line, by face (Classic's takes anything, as
#: DN's did): Simple's digits and arithmetic; Scientific's also the names
#: of its functions and constants; Programming's the base's digits and the
#: word's symbols, and its named operators spelt out (:data:`WORDS_TYPED`).
#: No face but Classic takes a space.
_ARITHMETIC = "0123456789.+-*/%^()"
ACCEPTS = {"simple": frozenset(_ARITHMETIC),
           "scientific": frozenset(_ARITHMETIC + "!,ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz")}
#: Programming's symbols beside the base's digits.
_WORD_SYMBOLS = "+-*/%^()&|\\~<>"
#: Programming's operators that may be typed by name (AND, NOT, SHL, ROR...),
#: the longest first, so NAND is not taken for the AND it ends in.
WORDS_TYPED = tuple(sorted(calculator.WORD_OPERATORS, key=lambda word: (-len(word), word)))


def accepts(mode: str, radix: int) -> frozenset[str]:
    """What face *mode* lets the keyboard type in base *radix*."""
    if mode == "programming":
        digits = "0123456789ABCDEF"[:radix]
        return frozenset(digits + digits.lower() + _WORD_SYMBOLS)
    return ACCEPTS.get(mode, frozenset())


class CalculatorWindow(Window):
    """DN's calculator, and three faces with keys."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        setup = SETTINGS.calculator
        self.angle.value = CalculatorData.ANGLES.index(setup.angle)
        self.base.value = CalculatorData.RADIXES.index(setup.radix)
        self.word.value = CalculatorData.WORDS.index(setup.word)
        self.signed.value = int(setup.signed)
        self.bit_keypad = setup.bit_keypad
        #: The memory (``MS``, ``M+``, ``MR``), shared by the faces; None is empty.
        self.memory: Number | None = None
        #: The last value Enter or ``=`` gave: ``ANS``.
        self.answer: Number | None = None
        #: The programmer's switches as last seen, to tell a change of them.
        self._switches: tuple[int, int, bool] | None = None
        self.set_mode(setup.mode if setup.mode in MODES else "simple", focus=False, save=False)

    def mounted(self) -> None:
        super().mounted()
        effect(self, CalculatorWindow._recalculate)
        effect(self, CalculatorWindow._follow_strip)
        effect(self, CalculatorWindow._follow_switches)

    # -- the faces ----------------------------------------------------------------------

    def set_mode(self, mode: str, *, focus: bool = True, save: bool = True) -> None:
        """Show face *mode*: its controls, its pad and its size, the line's
        value carried over into or out of the programmer's base, and the
        keyboard in the line when *focus*."""
        carried = self._carry(self.mode, mode) if mode != self.mode else None
        self.mode = mode
        if carried is not None:
            self.line.value = carried
        self.mode_strip.value = MODES.index(mode)
        pad = PADS.get(mode)
        if pad is not None and self.pad.table is not pad:
            self.pad.second = self.pad.hyp = False
            self.pad.show(pad)
        self._follow_radix()
        self._show_marks()
        self.place()
        if focus:
            self.line.focus()
        if save:
            self._keep(mode=mode)

    def cycle_mode(self) -> None:
        """Ctrl+F6 with the calculator in front: the next face."""
        self.set_mode(MODES[(MODES.index(self.mode) + 1) % len(MODES)])

    def place(self) -> None:
        """The face's size, kept on the desktop: moved up and left as far as it must."""
        width, height = SIZES[self.mode]
        if self.parent is None:
            self.width, self.height = width, height
            return
        room_width, room_height = self._bounds()
        width, height = min(width, room_width), min(height, room_height)
        self.locate(min(self.x, max(0, room_width - width)), min(self.y, max(0, room_height - height)),
                    width, height)

    def _follow_strip(self) -> None:
        """A choice on the strip is a change of face; the keyboard stays on the strip."""
        mode = MODES[self.mode_strip.value]
        if mode != peek(self, CalculatorWindow.mode):
            self.set_mode(mode, focus=False)

    def _follow_switches(self) -> None:
        """The angle, base, word and sign kept as chosen; a change of the
        programmer's base, word or sign writes the line's value in the new."""
        angle = CalculatorData.ANGLES[self.angle.value]
        radix, word = CalculatorData.RADIXES[self.base.value], CalculatorData.WORDS[self.word.value]
        switches = (RADIXES[radix], WORDS[word], bool(self.signed.value & 1))
        before, self._switches = self._switches, switches
        if before is not None and before != switches and peek(self, CalculatorWindow.mode) == "programming":
            old = Context(radix=before[0], bits=before[1], signed=before[2], ans=self.answer)
            with contextlib.suppress(CalcError):
                value = calculator.evaluate(calculator.closed(peek(self.line, type(self.line).value)), old)
                self.line.value = calculator.in_base(calculator.wrap(value, switches[1], switches[2]), switches[0])
        self._follow_radix()
        self._keep(angle=angle, radix=radix, word=word, signed=switches[2])

    def _follow_radix(self) -> None:
        """The digits the programmer's base allows, on the pad and from the
        keyboard, and what else the face's line takes."""
        radix = self.context().radix if self.mode == "programming" else 16
        self.line.accepts = accepts(self.mode, radix)
        self.line.words = WORDS_TYPED if self.mode == "programming" else ()
        if self.pad.radix != radix:
            self.pad.radix = radix
            self.pad.refresh()

    def context(self, mode: str | None = None) -> Context:
        """What face *mode* (this one by default) reads its line in."""
        mode = mode or self.mode
        if mode == "classic":
            return CLASSIC
        if mode == "scientific":
            return Context(angle=CalculatorData.ANGLES[self.angle.value], ans=self.answer)
        if mode == "programming":
            return Context(radix=RADIXES[CalculatorData.RADIXES[self.base.value]],
                           bits=WORDS[CalculatorData.WORDS[self.word.value]],
                           signed=bool(self.signed.value & 1), ans=self.answer)
        return Context(ans=self.answer)

    def _carry(self, old: str, new: str) -> str | None:
        """The line for face *new*, from face *old*'s: a value into or out of
        the programmer's base; None to keep it as typed."""
        if (old == "programming") == (new == "programming") or not self.line.value.strip():
            return None
        try:
            value = calculator.evaluate(calculator.closed(self.line.value), self.context(old))
        except CalcError:
            return None
        if new == "programming":
            context = self.context(new)
            return calculator.in_base(calculator.wrap(int(value), context.bits, context.signed), context.radix)
        return self.written(value, new)

    def written(self, value: Number, mode: str | None = None) -> str:
        """*value* as face *mode* writes it into the line."""
        mode = mode or self.mode
        if mode == "programming":
            return calculator.in_base(value, self.context(mode).radix)
        if mode == "classic":
            return calculator.decimal(value)
        return calculator.fit(value, LINE_WIDTH)

    # -- what is shown --------------------------------------------------------------------

    def _recalculate(self) -> None:
        """``SetValues(Off)``: the face's value, from the line as it stands."""
        mode, text = self.mode, self.line.value
        if mode == "classic":
            self.rows = self.indicator(text)
            return
        context = self.context()
        try:
            value: Number | None = calculator.evaluate(calculator.closed(text), context)
        except CalcError:
            value = None
        if mode == "programming":
            self.forms = self.forms_of(value, context, self.bin_row.width)
            self.bit_grid.bits = context.bits or calculator.BITS
            self.bit_grid.value = 0 if value is None else int(value) & ((1 << self.bit_grid.bits) - 1)
        else:
            self.result = "" if value is None else calculator.fit(value, max(1, self.result_row.width))

    @staticmethod
    def indicator(text: str) -> list[str]:
        """``TIndicator.Draw``'s five rows for *text*: *Error* alone in the
        middle when it cannot be worked out, *Overflow* for a form it is past."""
        try:
            value = calculator.evaluate(text)
        except calculator.CalcError:
            return ["", "", tr("Error"), "", ""]
        forms = [calculator.radix(value, base) for base in (16, 2, 8)]
        return [calculator.decimal(value), *(form or tr("Overflow") for form in forms),
                calculator.exponent(value)]

    @staticmethod
    def forms_of(value: Number | None, context: Context, width: int) -> list[str]:
        """The programmer's four rows: hexadecimal, decimal, octal and binary,
        the three in two's complement in the word, in groups; the binary one's
        head cut off with ``…`` when it is wider than *width*."""
        if value is None:
            return ["", "", "", ""]
        bits = context.bits or calculator.BITS
        hexadecimal = calculator.grouped(calculator.radix(value, 16, bits) or "", 4)
        octal = calculator.grouped(calculator.radix(value, 8, bits) or "", 3)
        binary = calculator.grouped(calculator.radix(value, 2, bits) or "", 4)
        if len(binary) > width > 1:
            binary = "…" + binary[len(binary) - width + 1:]
        return [hexadecimal, calculator.decimal(value), octal, binary]

    def _show_marks(self) -> None:
        """Scientific's ``M``, ``2nd`` and ``hyp`` while they are on."""
        marks = ["M" if self.memory is not None else "", "2nd" if self.pad.second else "",
                 "hyp" if self.pad.hyp else ""]
        self.marks = "  ".join(mark for mark in marks if mark)

    # -- what the buttons and keys do ---------------------------------------------------

    def evaluate(self) -> None:
        """``SetValues(On)``: the line becomes its value, selected, and what it
        was goes into the history.  A pad's face says *Error* when there is none."""
        text = self.line.value
        try:
            if self.mode == "classic":
                value = calculator.evaluate(text)
            else:
                value = calculator.evaluate(calculator.closed(text), self.context())
        except calculator.CalcError:
            if self.mode in ("simple", "scientific"):
                self.result = tr("Error")
            return
        HISTORY.add("calc", text.strip())
        self.answer = value
        self.line.value = self.written(value)
        self.line.select_all()
        self.line.result_selected = True
        self.line.focus()

    def current_value(self) -> Number | None:
        """The line's value, or None when it has none."""
        text = self.line.value
        try:
            if self.mode == "classic":
                return calculator.evaluate(text)
            return calculator.evaluate(calculator.closed(text), self.context())
        except CalcError:
            return None

    def copy_value(self) -> None:
        """``cmCopyClip``: the value on the clipboard -- in *Copy As*'s form
        in *Classic*, the base it is typed in in *Programming* -- and nothing
        for an error, or a form it overflows."""
        app = self.application
        value = self.current_value()
        if value is None or app is None:
            return
        if self.mode == "classic":
            text = calculator.shown(value, calculator.COPY_AS[self.copy_as.value])
        elif self.mode == "programming":
            context = self.context()
            text = calculator.decimal(value) if context.radix == 10 else \
                calculator.radix(value, context.radix, context.bits or calculator.BITS)
        else:
            text = calculator.fit(value, LINE_WIDTH)
        if text is not None:
            app.copy_to_clipboard(text)

    def leave(self) -> None:
        """Esc and *Close*: the line into the history, as ``TCalcLine`` put it,
        and the window gone."""
        HISTORY.add("calc", self.line.value.strip())
        self.request_close()

    def press_key(self, key: Key) -> None:
        """What a pad's *key* does to the line, at its cursor."""
        action = key.action
        pad = self.pad
        if action in ("second", "hyp"):
            setattr(pad, action, not getattr(pad, action))
            pad.refresh()
            self._show_marks()
            return
        if action == "equals":
            self.evaluate()
        elif action == "memory":
            self._memory(key.arg)
        elif action == "bits":
            self.bit_keypad = not self.bit_keypad
            self._keep(bit_keypad=self.bit_keypad)
        else:
            self._edit(key)
        if pad.second or pad.hyp:
            # One key's worth, as a pocket calculator's.
            pad.second = pad.hyp = False
            pad.refresh()
        self._show_marks()

    def _edit(self, key: Key) -> None:
        line = self.line
        value, cursor = line.value, line.cursor
        if line.result_selected:
            # As ``TCalcLine``: a digit after an answer starts afresh, anything else goes on from it.
            line.result_selected = False
            value = "" if key.role == "digit" and key.action == "insert" else value
            cursor = len(value)
        elif line.anchor is not None and line.anchor != cursor:
            start, end = sorted((line.anchor, cursor))
            value, cursor = value[:start] + value[end:], start
        head, tail = value[:cursor], value[cursor:]
        action, arg = key.action, key.arg
        if action == "insert":
            head += arg
        elif action == "wrap":
            head = calculator.wrap_last(head, arg)
        elif action == "negate":
            head = calculator.negate_last(head)
        elif action == "percent":
            head = calculator.percent_last(head)
        elif action == "entry":
            head = calculator.drop_last_number(head)
        elif action == "back":
            head = head[:-1]
        elif action == "clear":
            head = tail = ""
        elif action == "exponent" and head[-1:].isdigit():
            head += "E"
        line.anchor = None
        line.value = head + tail
        line.cursor = len(head)

    def _memory(self, what: str) -> None:
        """``MC``, ``MR``, ``M+``, ``M−`` and ``MS``."""
        if what == "clear":
            self.memory = None
        elif what == "recall":
            if self.memory is not None:
                self._edit(Key("", "insert", self.written(self.memory)))
        else:
            value = self.current_value()
            if value is None:
                return
            if what == "store":
                self.memory = value
            else:
                self.memory = (self.memory or 0) + (value if what == "add" else -value)

    def flip_bit(self, bit: int) -> None:
        """A bit flipped on the grid: the line becomes the new value."""
        context = self.context()
        bits = context.bits or calculator.BITS
        word = (self.bit_grid.value ^ (1 << bit)) & ((1 << bits) - 1)
        self.line.value = calculator.in_base(calculator.wrap(word, bits, context.signed), context.radix)
        self.line.cursor = len(self.line.value)
        self.line.anchor = None

    def _keep(self, **values: Any) -> None:
        """*values* kept in ``[calculator]`` and saved, when they changed it.
        Read untracked: the effects that call this follow the window's
        controls, not the settings they write."""
        section = SETTINGS.calculator
        with untracked():
            changed = {key: value for key, value in values.items() if getattr(section, key) != value}
        if changed:
            section.update(changed)
            # Said once if the file will not take it (``save_or_say``).
            save_or_say("calculator", self.application)

    # -- events ----------------------------------------------------------------------------

    async def on_pad_pressed(self, event: PadPressed) -> bool:
        self.press_key(event.key)
        return True

    async def on_bit_flipped(self, event: BitFlipped) -> bool:
        self.flip_bit(event.bit)
        return True

    async def on_toggle_bit_keypad(self, event: ToggleBitKeypad) -> bool:
        self.bit_keypad = not self.bit_keypad
        self._keep(bit_keypad=self.bit_keypad)
        if self.bit_keypad:
            self.bit_grid.focus()
        else:
            self.line.focus()
        return True

    def enables(self, command: Any) -> bool:
        """*Bit toggling keypad* is the programmer's."""
        if isinstance(command, ToggleBitKeypad):
            return self.mode == "programming"
        return super().enables(command)

    def checks(self, command: Any) -> bool | None:
        """The *Calculator* menu ticks the face shown, and the bits while they are."""
        mode = MODE_COMMANDS.get(type(command))
        if mode is not None:
            return self.mode == mode
        if isinstance(command, ToggleBitKeypad):
            return self.bit_keypad
        return super().checks(command)

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

    # -- the right-click menu: ``ContextMenuHost``'s hooks, written out, as
    # the game window's are -- this half has one base, its markup's.

    def prepare_context(self, x: int, y: int) -> None:
        """Nothing to move to: the menu is the window's."""

    def context_point(self) -> tuple[int, int]:
        return self.line.x, self.line.y + 1

"""The calculator window's commands: its *Calculator* menu and keys.

Not DN's, whose calculator had one face: a departure, asked for.
"""

from __future__ import annotations

from navkit.commands import Command


class CalculatorSimple(Command):
    """*Simple*: a pocket calculator's keys under the line."""

    title = "Simple"


class CalculatorClassic(Command):
    """*Classic*: DOS Navigator's calculator, the line in five forms."""

    title = "Classic"


class CalculatorScientific(Command):
    """*Scientific*: functions, angles, memory and the last answer."""

    title = "Scientific"


class CalculatorProgramming(Command):
    """*Programming*: a word of 8 to 64 bits in four bases."""

    title = "Programming"


class CalculatorCopy(Command):
    """*Copy*: the value on the clipboard, in the form the face shows it."""

    title = "Copy"


class ToggleBitKeypad(Command):
    """*Bit toggling keypad*: the programmer's bits to flip in place of its keys."""

    title = "Bits"


__all__ = [
    "CalculatorClassic", "CalculatorCopy", "CalculatorProgramming", "CalculatorScientific", "CalculatorSimple",
    "ToggleBitKeypad",
]

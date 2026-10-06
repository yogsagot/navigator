"""Ctrl+F6's calculator: DOS Navigator's ``CCALC.PAS`` and the parser in ``PAR.PAS``.

**What it reads.**  Numbers as DN wrote them: ``12``, ``1.5``, ``.5``,
``1E+3``; hexadecimal as ``$FF``, ``0FFh`` (a digit first) or ``0x1F``;
binary ``101b`` or ``0b101``; octal ``17o``, or any number led by ``0``.
``PI``.  The operators ``+ - * / ^`` (a power), ``%`` (the remainder of two
whole numbers), ``& | \\`` (bitwise and, or, xor), ``~`` (bitwise not),
``<< >>``, the comparisons ``= == <> >< < > <= =< >= =>`` and ``&& || ^^``
(and, or, xor of truths) -- a comparison or a truth is 1 or 0.  The functions
``IF(c, a[, b])``, ``SIN COS TAN TG CTAN CTG COTAN ARCTAN SQR SQRT LN LG EXP
SIGN``, and ``RAD`` (radians to degrees) and ``GRAD`` (degrees to radians),
DN's names the wrong way round as they were.  Case does not matter; blanks
are dropped.

**A departure in precedence.**  DN's table (``Prior``) put ``^`` below ``*``
and ``/``, so ``2*3^2`` was 36, and ``+`` below ``-``.  Here the order is
arithmetic's and Python's: ``|| ^^ &&``, the comparisons, ``|``, ``\\``,
``&``, the shifts, ``+ -``, ``* / %``, a sign or ``~``, and ``^`` binding
tightest, from the right.

**The integer forms** (hexadecimal, binary, octal) are of the whole part, a
negative one in two's complement; DN's were 32 bits wide and said
*Overflow* past them, these are 64 -- a file's size no longer fits in 32.
"""

from __future__ import annotations

import math
import re
from decimal import Decimal
from typing import Any, Callable

#: How far the integer forms go: two's complement in this many bits.
BITS = 64

Number = int | float


class CalcError(ValueError):
    """What DN's indicator showed as *Error*."""


_TOKEN = re.compile(
    r"\s*(?:"
    r"(?P<number>\$[0-9A-Fa-f]+"
    r"|(?:\d+\.?\d*|\.\d+)[Ee][+-]?\d+(?![0-9A-Za-z])"
    r"|\.\d+|\d[0-9A-Za-z]*(?:\.\d*)?)"
    r"|(?P<name>[A-Za-z_][A-Za-z_0-9]*)"
    r"|(?P<op>\|\||&&|\^\^|==|<>|><|<=|=<|>=|=>|<<|>>|[-+*/^%&|\\~<>=(),])"
    r")"
)


def number(text: str) -> Number:
    """One of DN's numbers, as written."""
    upper = text.upper()
    try:
        if upper.startswith("$"):
            return int(upper[1:], 16)
        if upper.startswith("0X"):
            return int(upper[2:], 16)
        if "." not in upper and not re.search(r"E[+-]", upper):
            if upper.startswith("0B") and len(upper) > 2:
                return int(upper[2:], 2)
            if upper.endswith("H"):
                return int(upper[:-1], 16)
            if upper.endswith("B") and re.fullmatch(r"[01]+B", upper):
                return int(upper[:-1], 2)
            if upper.endswith("O"):
                return int(upper[:-1], 8)
            if upper.startswith("0") and len(upper) > 1:
                return int(upper, 8)
            if upper.isdigit():
                return int(upper)
        value = float(upper)
    except ValueError:
        raise CalcError(f"not a number: {text}") from None
    return value


def tokens(text: str) -> list[tuple[str, str]]:
    """*text* as ``(kind, text)`` pairs: ``number``, ``name`` or ``op``."""
    found: list[tuple[str, str]] = []
    at = 0
    text = text.rstrip()
    while at < len(text):
        match = _TOKEN.match(text, at)
        if match is None or match.end() == at:
            raise CalcError(f"unexpected {text[at:].strip()[:1]!r}")
        kind = match.lastgroup
        found.append((kind, match.group(kind)))
        at = match.end()
    return found


def _whole(value: Number) -> int:
    if isinstance(value, float):
        if not math.isfinite(value) or value != int(value):
            raise CalcError("a whole number is needed")
        return int(value)
    return value


def _truth(value: Number) -> int:
    return int(value != 0)


def _power(a: Number, b: Number) -> Number:
    if isinstance(a, int) and isinstance(b, int) and b >= 0:
        if b > 4096:
            raise CalcError("overflow")
        return a ** b
    try:
        result = float(a) ** float(b)
    except (OverflowError, ZeroDivisionError):
        raise CalcError("overflow") from None
    if isinstance(result, complex):
        raise CalcError("no real power")
    return result


def _divide(a: Number, b: Number) -> Number:
    if b == 0:
        raise CalcError("division by zero")
    result = a / b
    return int(result) if isinstance(a, int) and isinstance(b, int) and a % b == 0 else result


def _remainder(a: Number, b: Number) -> Number:
    a, b = _whole(a), _whole(b)
    if b == 0:
        raise CalcError("division by zero")
    return int(math.fmod(a, b))  # Pascal's ``mod``: the sign of the dividend


_OPERATORS: dict[str, tuple[int, Callable[[Number, Number], Number]]] = {
    "||": (1, lambda a, b: _truth(a) | _truth(b)),
    "^^": (2, lambda a, b: _truth(a) ^ _truth(b)),
    "&&": (3, lambda a, b: _truth(a) & _truth(b)),
    "=": (4, lambda a, b: int(a == b)),
    "==": (4, lambda a, b: int(a == b)),
    "<>": (4, lambda a, b: int(a != b)),
    "><": (4, lambda a, b: int(a != b)),
    "<": (4, lambda a, b: int(a < b)),
    ">": (4, lambda a, b: int(a > b)),
    "<=": (4, lambda a, b: int(a <= b)),
    "=<": (4, lambda a, b: int(a <= b)),
    ">=": (4, lambda a, b: int(a >= b)),
    "=>": (4, lambda a, b: int(a >= b)),
    "|": (5, lambda a, b: _whole(a) | _whole(b)),
    "\\": (6, lambda a, b: _whole(a) ^ _whole(b)),
    "&": (7, lambda a, b: _whole(a) & _whole(b)),
    "<<": (8, lambda a, b: _whole(a) << min(_whole(b), BITS)),
    ">>": (8, lambda a, b: _whole(a) >> _whole(b)),
    "+": (9, lambda a, b: a + b),
    "-": (9, lambda a, b: a - b),
    "*": (10, lambda a, b: a * b),
    "/": (10, _divide),
    "%": (10, _remainder),
}



def _function(name: str, args: list[Callable[[], Number]]) -> Number:
    if name == "IF":
        if not 2 <= len(args) <= 3:
            raise CalcError("IF takes two or three")
        if args[0]() != 0:
            return args[1]()
        return args[2]() if len(args) == 3 else 0
    if len(args) != 1:
        raise CalcError(f"{name} takes one")
    x = float(args[0]())
    try:
        if name == "RAD":
            return x * 180 / math.pi
        if name == "GRAD":
            return x * math.pi / 180
        if name == "SIN":
            return math.sin(x)
        if name == "COS":
            return math.cos(x)
        if name in ("TAN", "TG"):
            if math.cos(x) == 0:
                raise CalcError("no tangent")
            return math.tan(x)
        if name in ("CTAN", "CTG", "COTAN"):
            if math.sin(x) == 0:
                raise CalcError("no cotangent")
            return math.cos(x) / math.sin(x)
        if name == "ARCTAN":
            return math.atan(x)
        if name == "SQR":
            value = args[0]()
            return value * value
        if name == "SQRT":
            if x < 0:
                raise CalcError("no root")
            return math.sqrt(x)
        if name in ("LN", "LG"):
            if x <= 0:
                raise CalcError("no logarithm")
            return math.log(x) if name == "LN" else math.log10(x)
        if name == "EXP":
            return math.exp(x)
        if name == "SIGN":
            return (x > 0) - (x < 0)
    except OverflowError:
        raise CalcError("overflow") from None
    raise CalcError(f"no function {name}")


class _Parser:
    def __init__(self, text: str) -> None:
        self.tokens = tokens(text)
        self.at = 0

    def peek(self) -> tuple[str, str] | None:
        return self.tokens[self.at] if self.at < len(self.tokens) else None

    def take(self) -> tuple[str, str]:
        token = self.peek()
        if token is None:
            raise CalcError("the expression stops short")
        self.at += 1
        return token

    def expect(self, text: str) -> None:
        if self.take() != ("op", text):
            raise CalcError(f"{text!r} expected")

    def expression(self, floor: int = 0) -> Callable[[], Number]:
        left = self.unary()
        while True:
            token = self.peek()
            if token is None or token[0] != "op" or token[1] not in _OPERATORS:
                return left
            level, apply = _OPERATORS[token[1]]
            if level <= floor:
                return left
            self.take()
            right = self.expression(level)
            left = (lambda l, r, f: lambda: f(l(), r()))(left, right, apply)

    def unary(self) -> Callable[[], Number]:
        token = self.peek()
        if token in (("op", "-"), ("op", "+"), ("op", "~")):
            self.take()
            operand = self.unary()  # ``-2^2`` is -4, and ``--2`` is 2
            sign = token[1]
            if sign == "-":
                return lambda: -operand()
            if sign == "~":
                return lambda: ~_whole(operand())
            return operand
        return self.power()

    def power(self) -> Callable[[], Number]:
        base = self.atom()
        if self.peek() == ("op", "^"):
            self.take()
            exponent = self.unary()  # right to left, and ``2^-1`` is a half
            return lambda: _power(base(), exponent())
        return base

    def atom(self) -> Callable[[], Number]:
        kind, text = self.take()
        if kind == "number":
            value = number(text)
            return lambda: value
        if kind == "name":
            name = text.upper()
            if self.peek() == ("op", "("):
                self.take()
                args: list[Callable[[], Number]] = []
                if self.peek() != ("op", ")"):
                    while True:
                        args.append(self.expression())
                        if self.peek() == ("op", ","):
                            self.take()
                            continue
                        break
                self.expect(")")
                return lambda: _function(name, args)
            if name == "PI":
                return lambda: math.pi
            raise CalcError(f"no name {text}")
        if (kind, text) == ("op", "("):
            inner = self.expression()
            self.expect(")")
            return inner
        raise CalcError(f"unexpected {text!r}")


def evaluate(text: str) -> Number:
    """*text*'s value.  Raises :class:`CalcError` for anything DN called *Error*."""
    if not text.strip():
        return 0
    parser = _Parser(text)
    tree = parser.expression()
    if parser.peek() is not None:
        raise CalcError(f"unexpected {parser.peek()[1]!r}")
    try:
        value = tree()
    except (OverflowError, ValueError, ZeroDivisionError) as error:
        if isinstance(error, CalcError):
            raise
        raise CalcError(str(error)) from None
    if isinstance(value, float) and not math.isfinite(value):
        raise CalcError("overflow")
    return value


# -- showing it ----------------------------------------------------------------


def decimal(value: Number) -> str:
    """``Str(Value:0:20)`` without its trailing zeros: fixed, never ``1e+20``."""
    if isinstance(value, int):
        return str(value)
    if value == int(value) and abs(value) < 1e21:
        return str(int(value))
    text = format(Decimal(repr(value)), "f")
    return text.rstrip("0").rstrip(".") if "." in text else text


def radix(value: Number, base: int) -> str | None:
    """The whole part in *base* (16, 2 or 8), a negative one as :data:`BITS`
    bits of two's complement; None past them -- DN's *Overflow*."""
    whole = int(value)
    if not -(1 << (BITS - 1)) <= whole < (1 << BITS):
        return None
    if whole < 0:
        whole += 1 << BITS
    digits = {16: "x", 2: "b", 8: "o"}[base]
    return format(whole, digits).upper()


def exponent(value: Number) -> str:
    """``Str(Value)``: Turbo Pascal's own floating form, ``1.0000000000E+02``."""
    return f"{float(value):.10E}"


#: *Copy As*'s five, in the dialog's order.
COPY_AS = ("dec", "hex", "bin", "oct", "exp")


def shown(value: Number, form: str) -> str | None:
    """*value* as *Copy As*'s *form* puts it on the clipboard; None for an overflow."""
    if form == "dec":
        return decimal(value)
    if form == "exp":
        return exponent(value)
    return radix(value, {"hex": 16, "bin": 2, "oct": 8}[form])

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

**Contexts: not DN's.**  The calculator's other modes (Simple, Scientific,
Programming -- a departure, asked for) read the same language through a
:class:`Context`.  :data:`CLASSIC`, the default, is DN's calculator exactly.
Beside DN's names there are ``ASIN ACOS ATAN SINH COSH TANH ASINH ACOSH ATANH
ABS CBRT ROOT(x, n) LOG LOG2 FACT``, a postfix ``!``, the constant ``E`` and
the last answer ``ANS``; the word operators ``AND OR XOR NAND NOR MOD SHL SHR
SAR ROL ROR`` (infix) and ``NOT`` (prefix).  A context's ``angle`` is what the
trigonometric functions take and give, DN's ``ARCTAN`` among them.  A
programmer's context (``bits`` set) works in whole numbers only, ``/``
truncating, every result wrapped to the word in two's complement; there a bare
run of digits is read in its ``radix`` -- in sixteen, a run of ``0-9A-F``, so
``E`` is fourteen and ``101b`` is hexadecimal; ``$FF`` and ``0x1F`` still work.

The tape helpers at the end (:func:`negate_last`, :func:`wrap_last` ...) are
what the button pads do to the expression before the cursor.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from decimal import Decimal
from typing import Callable

#: How far the integer forms go: two's complement in this many bits.
BITS = 64

Number = int | float


class CalcError(ValueError):
    """What DN's indicator showed as *Error*."""


@dataclass(frozen=True)
class Context:
    """What an expression is read and worked out in, besides its text."""

    #: ``deg``, ``rad`` or ``grad``: what ``SIN``..``TAN`` take and ``ASIN``..``ATAN`` give.
    angle: str = "rad"
    #: The value of ``ANS``; None is 0.
    ans: "Number | None" = None
    #: The base a bare run of digits is read in: 16, 10, 8 or 2.
    radix: int = 10
    #: A programmer's word: whole numbers only, each result wrapped to this many bits.
    bits: int | None = None
    #: Whether the word is read as two's complement or unsigned.
    signed: bool = True


#: DN's calculator: radians, decimal, no word.
CLASSIC = Context()


_TOKEN = re.compile(
    r"\s*(?:"
    r"(?P<number>\$[0-9A-Fa-f]+"
    r"|(?:\d+\.?\d*|\.\d+)[Ee][+-]?\d+(?![0-9A-Za-z])"
    r"|\.\d+|\d[0-9A-Za-z]*(?:\.\d*)?)"
    r"|(?P<name>[A-Za-z_][A-Za-z_0-9]*)"
    r"|(?P<op>\|\||&&|\^\^|==|<>|><|<=|=<|>=|=>|<<|>>|[-+*/^%&|\\~<>=(),!])"
    r")"
)


#: The digits a bare number may have in each base other than ten.
_DIGITS = {16: re.compile(r"[0-9A-F]+"), 8: re.compile(r"[0-7]+"), 2: re.compile(r"[01]+")}

#: Names that are operators, as DN's symbols are, for the programmer's pad.
WORD_OPERATORS = frozenset({"AND", "OR", "XOR", "NAND", "NOR", "MOD", "SHL", "SHR", "SAR", "ROL", "ROR", "NOT"})


def number(text: str, radix: int = 10) -> Number:
    """One of DN's numbers, as written; a bare run of digits in *radix*."""
    upper = text.upper()
    if radix != 10:
        if _DIGITS[radix].fullmatch(upper):
            return int(upper, radix)
        if re.fullmatch(r"\d+", upper):
            raise CalcError(f"not a base {radix} number: {text}")
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
        word = match.group(kind)
        if kind == "name" and word.upper() in WORD_OPERATORS:
            kind, word = "op", word.upper()
        found.append((kind, word))
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


def _quotient(a: Number, b: Number) -> int:
    """A programmer's ``/``: the whole quotient, toward zero as C's."""
    a, b = _whole(a), _whole(b)
    if b == 0:
        raise CalcError("division by zero")
    whole = abs(a) // abs(b)
    return whole if (a < 0) == (b < 0) else -whole


def _remainder(a: Number, b: Number) -> Number:
    a, b = _whole(a), _whole(b)
    if b == 0:
        raise CalcError("division by zero")
    left = abs(a) % abs(b)
    return left if a >= 0 else -left  # Pascal's ``mod``: the sign of the dividend


def _factorial(value: Number) -> int:
    whole = _whole(value)
    if whole < 0:
        raise CalcError("no factorial")
    if whole > 1000:
        raise CalcError("overflow")
    return math.factorial(whole)


def wrap(value: Number, bits: int, signed: bool = True) -> int:
    """*value*'s whole part in a word of *bits*, read as two's complement when *signed*."""
    whole = _whole(value) & ((1 << bits) - 1)
    if signed and whole >= 1 << (bits - 1):
        whole -= 1 << bits
    return whole


def _rotate(a: Number, b: Number, bits: int, left: bool) -> int:
    word = _whole(a) & ((1 << bits) - 1)
    by = _whole(b) % bits
    if not left:
        by = (bits - by) % bits
    return ((word << by) | (word >> (bits - by))) & ((1 << bits) - 1)


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
    "OR": (5, lambda a, b: _whole(a) | _whole(b)),
    "NOR": (5, lambda a, b: ~(_whole(a) | _whole(b))),
    "\\": (6, lambda a, b: _whole(a) ^ _whole(b)),
    "XOR": (6, lambda a, b: _whole(a) ^ _whole(b)),
    "&": (7, lambda a, b: _whole(a) & _whole(b)),
    "AND": (7, lambda a, b: _whole(a) & _whole(b)),
    "NAND": (7, lambda a, b: ~(_whole(a) & _whole(b))),
    "<<": (8, lambda a, b: _whole(a) << min(_whole(b), BITS)),
    "SHL": (8, lambda a, b: _whole(a) << min(_whole(b), BITS)),
    ">>": (8, lambda a, b: _whole(a) >> _whole(b)),
    "SAR": (8, lambda a, b: _whole(a) >> _whole(b)),
    "+": (9, lambda a, b: a + b),
    "-": (9, lambda a, b: a - b),
    "*": (10, lambda a, b: a * b),
    "/": (10, _divide),
    "%": (10, _remainder),
    "MOD": (10, _remainder),
}


def _operators(context: Context) -> dict[str, tuple[int, Callable[[Number, Number], Number]]]:
    """:data:`_OPERATORS` with the ones a word's width decides, and a programmer's ``/``."""
    bits = context.bits or BITS
    found = dict(_OPERATORS)
    found["SHR"] = (8, lambda a, b: (_whole(a) & ((1 << bits) - 1)) >> _whole(b))
    found["ROL"] = (8, lambda a, b: _rotate(a, b, bits, True))
    found["ROR"] = (8, lambda a, b: _rotate(a, b, bits, False))
    if context.bits is not None:
        found["/"] = (10, _quotient)
    return found


#: A whole turn in each angle unit.
_TURN = {"deg": 360.0, "rad": 2 * math.pi, "grad": 400.0}


def _to_radians(x: float, angle: str) -> float:
    return x if angle == "rad" else x * 2 * math.pi / _TURN[angle]


def _from_radians(x: float, angle: str) -> float:
    return x if angle == "rad" else x * _TURN[angle] / (2 * math.pi)


def _exact_trig(name: str, x: float, angle: str) -> float | None:
    """SIN, COS or TAN of a whole quarter turn in degrees or grads, exactly:
    ``SIN(180)`` is 0, not 1.2E-16, and ``TAN(90)`` has no value."""
    if angle == "rad":
        return None
    quarter = _TURN[angle] / 4
    if x % quarter:
        return None
    step = int(x // quarter) % 4
    sine, cosine = (0.0, 1.0, 0.0, -1.0)[step], (1.0, 0.0, -1.0, 0.0)[step]
    if name == "SIN":
        return sine
    if name == "COS":
        return cosine
    if cosine == 0:
        raise CalcError("no tangent")
    return sine / cosine


def _trig(name: str, x: float, angle: str) -> float:
    exact = _exact_trig(name, x, angle)
    if exact is not None:
        return exact
    x = _to_radians(x, angle)
    if name == "SIN":
        return math.sin(x)
    if name == "COS":
        return math.cos(x)
    if math.cos(x) == 0:
        raise CalcError("no tangent")
    return math.tan(x)


def _function(name: str, args: list[Callable[[], Number]], context: Context) -> Number:
    if name == "IF":
        if not 2 <= len(args) <= 3:
            raise CalcError("IF takes two or three")
        if args[0]() != 0:
            return args[1]()
        return args[2]() if len(args) == 3 else 0
    if name == "ROOT":
        if len(args) != 2:
            raise CalcError("ROOT takes two")
        x, n = float(args[0]()), float(args[1]())
        if n == 0:
            raise CalcError("no root")
        if x < 0:
            if n != int(n) or int(n) % 2 == 0:
                raise CalcError("no root")
            return -((-x) ** (1 / n))
        return x ** (1 / n)
    if len(args) != 1:
        raise CalcError(f"{name} takes one")
    if name == "FACT":
        return _factorial(args[0]())
    if name == "ABS":
        return abs(args[0]())
    x = float(args[0]())
    angle = context.angle
    try:
        if name == "RAD":
            return x * 180 / math.pi
        if name == "GRAD":
            return x * math.pi / 180
        if name in ("SIN", "COS"):
            return _trig(name, x, angle)
        if name in ("TAN", "TG"):
            return _trig("TAN", x, angle)
        if name in ("CTAN", "CTG", "COTAN"):
            sine, cosine = _trig("SIN", x, angle), _trig("COS", x, angle)
            if sine == 0:
                raise CalcError("no cotangent")
            return cosine / sine
        if name in ("ARCTAN", "ATAN"):
            return _from_radians(math.atan(x), angle)
        if name in ("ASIN", "ACOS"):
            if not -1 <= x <= 1:
                raise CalcError(f"no {name.lower()}")
            return _from_radians(math.asin(x) if name == "ASIN" else math.acos(x), angle)
        if name == "SINH":
            return math.sinh(x)
        if name == "COSH":
            return math.cosh(x)
        if name == "TANH":
            return math.tanh(x)
        if name == "ASINH":
            return math.asinh(x)
        if name == "ACOSH":
            if x < 1:
                raise CalcError("no acosh")
            return math.acosh(x)
        if name == "ATANH":
            if not -1 < x < 1:
                raise CalcError("no atanh")
            return math.atanh(x)
        if name == "SQR":
            value = args[0]()
            return value * value
        if name == "SQRT":
            if x < 0:
                raise CalcError("no root")
            return math.sqrt(x)
        if name == "CBRT":
            root = abs(x) ** (1 / 3)
            if round(root) ** 3 == abs(x):
                root = round(root)  # 27 has 3 for its root, not 3.0000000000000004
            return math.copysign(root, x)
        if name in ("LN", "LG", "LOG", "LOG2"):
            if x <= 0:
                raise CalcError("no logarithm")
            return {"LN": math.log, "LOG2": math.log2}.get(name, math.log10)(x)
        if name == "EXP":
            return math.exp(x)
        if name == "SIGN":
            return (x > 0) - (x < 0)
    except OverflowError:
        raise CalcError("overflow") from None
    raise CalcError(f"no function {name}")


class _Parser:
    def __init__(self, text: str, context: Context) -> None:
        self.tokens = tokens(text)
        self.at = 0
        self.context = context
        self.operators = _operators(context)
        bits = context.bits
        #: A programmer's word: every result wrapped to it.
        self.fix: Callable[[Number], Number] = (
            (lambda value: wrap(value, bits, context.signed)) if bits is not None else (lambda value: value))

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
        fix = self.fix
        while True:
            token = self.peek()
            if token is None or token[0] != "op" or token[1] not in self.operators:
                return left
            level, apply = self.operators[token[1]]
            if level <= floor:
                return left
            self.take()
            right = self.expression(level)
            left = (lambda l, r, f: lambda: fix(f(l(), r())))(left, right, apply)

    def unary(self) -> Callable[[], Number]:
        token = self.peek()
        if token in (("op", "-"), ("op", "+"), ("op", "~"), ("op", "NOT")):
            self.take()
            operand = self.unary()  # ``-2^2`` is -4, and ``--2`` is 2
            sign, fix = token[1], self.fix
            if sign == "-":
                return lambda: fix(-operand())
            if sign in ("~", "NOT"):
                return lambda: fix(~_whole(operand()))
            return operand
        return self.power()

    def power(self) -> Callable[[], Number]:
        base = self.factorial()
        if self.peek() == ("op", "^"):
            self.take()
            exponent = self.unary()  # right to left, and ``2^-1`` is a half
            fix = self.fix
            return lambda: fix(_power(base(), exponent()))
        return base

    def factorial(self) -> Callable[[], Number]:
        operand = self.atom()
        while self.peek() == ("op", "!"):
            self.take()
            operand = (lambda inner: lambda: _factorial(inner()))(operand)
        return operand

    def atom(self) -> Callable[[], Number]:
        kind, text = self.take()
        context = self.context
        if kind == "name" and context.radix == 16 and _DIGITS[16].fullmatch(text.upper()):
            kind = "number"  # ``FF``, and ``E`` is fourteen
        if kind == "number":
            value = number(text, context.radix)
            if context.bits is not None:
                if isinstance(value, float):
                    raise CalcError("a whole number is needed")
                value = self.fix(value)
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
                fix = self.fix
                return lambda: fix(_function(name, args, context))
            if name == "PI":
                return lambda: math.pi
            if name == "E":
                return lambda: math.e
            if name == "ANS":
                ans = context.ans or 0
                return lambda: ans
            raise CalcError(f"no name {text}")
        if (kind, text) == ("op", "("):
            inner = self.expression()
            self.expect(")")
            return inner
        raise CalcError(f"unexpected {text!r}")


def evaluate(text: str, context: Context = CLASSIC) -> Number:
    """*text*'s value in *context*.  Raises :class:`CalcError` for anything DN called *Error*."""
    if not text.strip():
        return 0
    parser = _Parser(text, context)
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
    if context.bits is not None:
        value = wrap(value, context.bits, context.signed)
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


def radix(value: Number, base: int, bits: int = BITS) -> str | None:
    """The whole part in *base* (16, 2 or 8), a negative one as *bits* bits
    of two's complement; None past them -- DN's *Overflow*."""
    whole = int(value)
    if not -(1 << (bits - 1)) <= whole < (1 << bits):
        return None
    if whole < 0:
        whole += 1 << bits
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


def grouped(text: str, every: int) -> str:
    """*text* in groups of *every* characters from the right: ``1111 0000``."""
    head = len(text) % every
    groups = ([text[:head]] if head else []) + [text[at:at + every] for at in range(head, len(text), every)]
    return " ".join(groups)


def in_base(value: Number, radix: int) -> str:
    """*value* written so a context of *radix* reads it back: its whole part
    with a sign in 16, 8 or 2 (``-FF``), the decimal form in ten."""
    if radix == 10:
        return decimal(value)
    whole = int(value)
    return ("-" if whole < 0 else "") + format(abs(whole), {16: "X", 8: "o", 2: "b"}[radix])


def fit(value: Number, width: int) -> str:
    """*value* for a display *width* cells wide: the decimal form rid of a
    float's last-digit noise (``0.1+0.2`` is 0.3) and rounded to fit, else
    the exponent form."""
    if isinstance(value, float):
        value = float(f"{value:.15g}")
    text = decimal(value)
    if len(text) <= width:
        return text
    if isinstance(value, float) and len(str(int(abs(value)))) + (value < 0) + 2 <= width:
        for places in range(width, 0, -1):
            short = format(value, f".{places}f").rstrip("0").rstrip(".")
            if len(short) <= width:
                if abs(float(short) - value) <= abs(value) * 1e-6:
                    return short  # else too small for fixed places: ``1.5E-30``, not 0
                break
    for digits in range(max(0, width - 6), -1, -1):
        mantissa, power = format(float(value), f".{digits}E").split("E")
        if "." in mantissa:
            mantissa = mantissa.rstrip("0").rstrip(".")
        short = f"{mantissa}E{power}"
        if len(short) <= width:
            return short
    return format(float(value), ".0E")


# -- the tape: what the button pads do to the expression before the cursor -----


def _last_operand(text: str) -> int:
    """Where the operand *text* ends with starts: a number or name, or a
    bracketed group with the function before it, and any ``!`` after;
    ``len(text)`` when it ends with none."""
    at = len(text)
    while at and text[at - 1] == "!":
        at -= 1
    if at and text[at - 1] == ")":
        depth = 0
        for at in range(at - 1, -1, -1):
            depth += {")": 1, "(": -1}.get(text[at], 0)
            if depth == 0:
                break
        else:
            return len(text)
    while at and (text[at - 1].isalnum() or text[at - 1] in "._$"):
        at -= 1
    if (at >= 2 and text[at - 1] in "+-" and text[at - 2] in "Ee" and text[at:at + 1].isdigit()
            and _last_operand(text[:at - 1]) < at - 2):
        return _last_operand(text[:at - 1])  # ``1E+3`` is one number
    return at


def _unary_minus(text: str, at: int) -> bool:
    """Whether the ``-`` at *at* is a sign rather than a subtraction."""
    before = text[:at].rstrip()
    return not before or before[-1] in "(,+-*/^%&|\\~<>=" or before.upper().endswith(
        tuple(WORD_OPERATORS))


def negate_last(text: str) -> str:
    """±: the trailing operand with its sign changed, ``5+3`` to ``5+-3``,
    and back; a sign started when there is none."""
    start = _last_operand(text)
    if start and text[start - 1] == "-" and _unary_minus(text, start - 1):
        return text[:start - 1] + text[start:]
    return text[:start] + "-" + text[start:]


def drop_last_number(text: str) -> str:
    """CE: the trailing operand gone, ``12+34`` to ``12+``."""
    return text[:_last_operand(text)]


def wrap_last(text: str, template: str) -> str:
    """*template* (``SQRT({})``, ``{}^2``) applied to the trailing operand --
    always a number, a name or a bracketed group, so it needs no brackets of
    its own.  With no operand, a function's template is started (``SQRT(``)
    and any other does nothing."""
    start = _last_operand(text)
    if start == len(text):
        head = template.split("{}")[0]
        return text + head if head[:1].isalpha() else text
    return text[:start] + template.format(text[start:])


def percent_last(text: str) -> str:
    """%: the trailing operand as hundredths, ``50`` to ``(50/100)``."""
    start = _last_operand(text)
    return text if start == len(text) else text[:start] + f"({text[start:]}/100)"


def closed(text: str) -> str:
    """*text* with the brackets it left open closed, as a pad's ``=`` reads it."""
    return text + ")" * max(0, text.count("(") - text.count(")"))

"""The three button calculators' keys, row by row: data, which
:class:`~navigator.widgets.shell.calculator_window.keypad.Keypad` lays out.

The captions are mathematics' notation, the same in every language, so they
are not translated.  An operator goes in as the expression language spells
it (``*`` for ×), a function wraps the operand before the cursor or starts
its bracket (:func:`navigator.lib.utilities.calculator.wrap_last`).
"""

from __future__ import annotations

from navigator.widgets.shell.calculator_window.keypad import Key


def _digit(text: str) -> Key:
    return Key(text, "insert", text, role="digit")


def _operator(caption: str, text: str, ascii_caption: str = "") -> Key:
    return Key(caption, "insert", text, ascii=ascii_caption, role="operator")


def _wrap(caption: str, template: str, ascii_caption: str = "", **kwargs: Key) -> Key:
    return Key(caption, "wrap", template, ascii=ascii_caption, **kwargs)


DIVIDE = _operator("÷", "/", "/")
TIMES = _operator("×", "*", "*")
MINUS = _operator("−", "-", "-")
PLUS = _operator("+", "+")
EQUALS = Key("=", "equals", role="equals")
NEGATE = Key("±", "negate", ascii="+/-", role="digit")
POINT = _digit(".")
BACK = Key("⌫", "back", ascii="<-", role="control")
ENTRY = Key("CE", "entry", role="control")
CLEAR = Key("C", "clear", role="control")

#: A pocket calculator's, stood upright.
SIMPLE: list[list[Key]] = [
    [Key("%", "percent"), ENTRY, CLEAR, BACK],
    [_wrap("1/x", "1/{}"), _wrap("x²", "{}^2", "x^2"), _wrap("√", "SQRT({})", "sqrt"), DIVIDE],
    [_digit("7"), _digit("8"), _digit("9"), TIMES],
    [_digit("4"), _digit("5"), _digit("6"), MINUS],
    [_digit("1"), _digit("2"), _digit("3"), PLUS],
    [NEGATE, _digit("0"), POINT, EQUALS],
]


def _trig(name: str) -> Key:
    """SIN, and under 2nd, hyp and both its inverse, hyperbolic and inverse hyperbolic."""
    lower = name.lower()
    return _wrap(lower, f"{name}({{}})",
                 second=_wrap(f"a{lower}", f"A{name}({{}})"),
                 hyp=_wrap(f"{lower}h", f"{name}H({{}})"),
                 both=_wrap(f"a{lower}h", f"A{name}H({{}})"))


#: Wider than tall, so it fits an 80 by 24 screen's desktop.
SCIENTIFIC: list[list[Key]] = [
    [Key("2nd", "second", role="control"), _trig("SIN"), _trig("COS"), _trig("TAN"),
     Key("π", "insert", "PI", ascii="pi"), CLEAR, ENTRY, BACK],
    [Key("hyp", "hyp", role="control"), _wrap("x²", "{}^2", "x^2", second=_wrap("x³", "{}^3", "x^3")),
     _operator("xʸ", "^", "x^y"), _wrap("√", "SQRT({})", "sqrt", second=_wrap("∛", "CBRT({})", "cbrt")),
     _wrap("ʸ√x", "ROOT({},", "yrt"), _operator("(", "("), _operator(")", ")"), DIVIDE],
    [Key("Ans", "insert", "ANS"), _wrap("1/x", "1/{}"), _wrap("|x|", "ABS({})"), _wrap("n!", "{}!"),
     _digit("7"), _digit("8"), _digit("9"), TIMES],
    [Key("MC", "memory", "clear", role="control"), _wrap("log", "LOG({})", second=_wrap("log₂", "LOG2({})", "log2")),
     _wrap("ln", "LN({})", second=_wrap("eˣ", "EXP({})", "e^x")),
     _wrap("10ˣ", "10^{}", "10^x", second=_wrap("2ˣ", "2^{}", "2^x")),
     _digit("4"), _digit("5"), _digit("6"), MINUS],
    [Key("MR", "memory", "recall", role="control"), Key("M+", "memory", "add", role="control"),
     Key("M−", "memory", "subtract", ascii="M-", role="control"), Key("e", "insert", "E"),
     _digit("1"), _digit("2"), _digit("3"), PLUS],
    [Key("MS", "memory", "store", role="control"), _operator("mod", " MOD "), Key("EXP", "exponent"),
     Key("%", "percent"), NEGATE, _digit("0"), POINT, EQUALS],
]

#: The programmer's: hexadecimal digits, the word's operators, and the bits.
PROGRAMMING: list[list[Key]] = [
    [_digit("A"), _digit("B"), _digit("7"), _digit("8"), _digit("9"), DIVIDE,
     _operator("AND", " AND "), _operator("NAND", " NAND ")],
    [_digit("C"), _digit("D"), _digit("4"), _digit("5"), _digit("6"), TIMES,
     _operator("OR", " OR "), _operator("NOR", " NOR ")],
    [_digit("E"), _digit("F"), _digit("1"), _digit("2"), _digit("3"), MINUS,
     _operator("XOR", " XOR "), _operator("NOT", "NOT ")],
    [_operator("(", "("), _operator(")", ")"), NEGATE, _digit("0"), _operator("mod", " MOD "), PLUS,
     _operator("<<", " << "), _operator(">>", " >> ")],
    [_operator("ROL", " ROL "), _operator("ROR", " ROR "), _operator("SHR", " SHR "),
     Key("Bits", "bits", role="control"), ENTRY, BACK, Key("AC", "clear", role="control"), EQUALS],
]

#: Each button mode's pad.
PADS: dict[str, list[list[Key]]] = {"simple": SIMPLE, "scientific": SCIENTIFIC, "programming": PROGRAMMING}

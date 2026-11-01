"""Ctrl+F6: DOS Navigator's calculator (``CCALC.PAS``, ``PAR.PAS``)."""

from __future__ import annotations

import math

import pytest

from conftest import FakeTerminal, run_app
from navkit.events import KeyEvent

from navigator.__main__ import Navigator
from navigator.lib.utilities.calculator import CalcError, decimal, evaluate, exponent, radix, shown
from navml.history import HISTORY
from navigator.settings import SETTINGS


@pytest.mark.parametrize("text, value", [
    ("1+2*3", 7), ("(1+2)*3", 9), ("2*3^2", 18), ("2^3^2", 512), ("-2^2", -4), ("2^-1", 0.5),
    ("3-2-1", 0), ("10/4", 2.5), ("10/5", 2), ("7%3", 1), ("-7%3", -1), ("2*-3", -6),
    ("$FF", 255), ("0FFh", 255), ("0x1f", 31), ("101b", 5), ("0b101", 5), ("17o", 15), ("017", 15),
    ("1E+3", 1000), ("1.5e-2", 0.015), (".5", 0.5),
    ("5&3", 1), ("5|3", 7), ("5\\3", 6), ("~5", -6), ("1<<4", 16), ("256>>4", 16),
    ("2>1", 1), ("2<>2", 0), ("2=<2", 1), ("1&&0", 0), ("1||0", 1), ("1^^1", 0),
    ("IF(1,2,3)", 2), ("if(0,2,3)", 3), ("IF(0,2)", 0), ("sqrt(16)", 4), ("SQR(3)", 9),
    ("rad(pi)", 180), ("sign(-3)", -1), ("lg(1000)", 3), ("  1 +  1 ", 2), ("", 0),
])
def test_dns_operators_numbers_and_functions(text, value):
    assert evaluate(text) == pytest.approx(value)


@pytest.mark.parametrize("text", ["1/0", "sqrt(-1)", "ln(0)", "2 +", "(1", "1)", "abc", "08", "7%0",
                                  "1.5|1", "IF(1)", "10^5000.0"])
def test_what_dn_called_error(text):
    with pytest.raises(CalcError):
        evaluate(text)


def test_the_forms_the_indicator_shows():
    assert decimal(evaluate("1e20")) == "100000000000000000000"
    assert decimal(0.25) == "0.25" and decimal(3.0) == "3" and decimal(-12) == "-12"
    assert radix(255, 16) == "FF" and radix(5, 2) == "101" and radix(8, 8) == "10"
    assert radix(-1, 16) == "F" * 16 and radix(2.9, 16) == "2"
    assert radix(1 << 70, 16) is None
    assert exponent(123) == "1.2300000000E+02"
    assert shown(255, "hex") == "FF" and shown(255, "exp") == "2.5500000000E+02"


# -- the window ------------------------------------------------------------------------


@pytest.fixture
def place(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    return tmp_path


@pytest.fixture
def classic(place):
    """DN's face, which these tests were written against; Simple is the default."""
    SETTINGS.calculator.mode = "classic"
    return place


def navigator(path) -> Navigator:
    return Navigator(path, path, terminal=FakeTerminal(80, 24))


def calc(app):
    from navigator.widgets.shell.calculator_window import CalculatorWindow

    return next((w for w in app.shell.desktop.windows() if isinstance(w, CalculatorWindow)), None)


def typed(text: str) -> list[KeyEvent]:
    return [KeyEvent(c, c) for c in text]


def test_ctrl_f6_opens_one_calculator_where_dn_put_it_and_it_works_as_typed(classic):
    app = navigator(classic)
    seen = {}

    def look(a):
        w = calc(a)
        seen.update(rect=(w.x, w.y, w.width, w.height), focused=a.focused is w.line, rows=list(w.rows))

    run_app(app, [KeyEvent("f6", ctrl=True), lambda a: None, *typed("2+3*4"), lambda a: None, look,
                  KeyEvent("f6", ctrl=True), lambda a: None,
                  lambda a: seen.update(count=sum(1 for w in a.shell.desktop.windows()
                                                  if w is calc(a)))])
    # DN's 49 by 15 at (10, 5), two rows taller for the strip of faces, and
    # so up a row to stay on an 80 by 24 screen's desktop.
    assert seen["rect"] == (10, 4, 49, 17) and seen["focused"]
    assert seen["rows"] == ["14", "E", "1110", "16", "1.4000000000E+01"]
    assert seen["count"] == 1


def test_enter_puts_the_value_in_and_then_an_operator_goes_on_from_it_a_digit_starts_again(classic):
    app = navigator(classic)
    seen = {}
    run_app(app, [KeyEvent("f6", ctrl=True), lambda a: None, *typed("6*7"), KeyEvent("enter"), lambda a: None,
                  lambda a: seen.update(after=calc(a).line.value, selected=calc(a).line.selected_text),
                  *typed("+1"), lambda a: None, lambda a: seen.update(on=calc(a).line.value, row=calc(a).rows[0]),
                  KeyEvent("enter"), *typed("5"), lambda a: None, lambda a: seen.update(fresh=calc(a).line.value)])
    assert seen["after"] == seen["selected"] == "42"
    assert seen["on"] == "42+1" and seen["row"] == "43"
    assert seen["fresh"] == "5"
    assert HISTORY.entries("calc")[:2] == ["42+1", "6*7"]


def test_an_error_shows_error_and_esc_closes_keeping_the_line(classic):
    app = navigator(classic)
    seen = {}
    run_app(app, [KeyEvent("f6", ctrl=True), lambda a: None, *typed("1/0"), lambda a: None,
                  lambda a: seen.update(rows=list(calc(a).rows)), KeyEvent("escape"), lambda a: None,
                  lambda a: seen.update(gone=calc(a) is None)])
    assert seen["rows"] == ["", "", "Error", "", ""] and seen["gone"]
    assert HISTORY.entries("calc")[0] == "1/0"


def test_copy_as_hex_puts_the_hex_form_on_the_clipboard(classic):
    app = navigator(classic)
    copied = []
    app.copy_to_clipboard = lambda text, **kw: copied.append(text)
    run_app(app, [KeyEvent("f6", ctrl=True), lambda a: None, *typed("255"),
                  KeyEvent("h", alt=True), KeyEvent("c", alt=True), lambda a: None])
    assert copied == ["FF"]


def test_tab_stays_in_the_window(classic):
    app = navigator(classic)
    seen = []

    def where(a):
        w = calc(a)
        seen.append(w._holds(a.focused))

    run_app(app, [KeyEvent("f6", ctrl=True), lambda a: None,
                  *[step for _ in range(8) for step in (KeyEvent("tab"), where)]])
    assert all(seen) and len(seen) == 8


# -- the faces beside DN's (a departure, asked for) ----------------------------------------

from navigator.lib.utilities.calculator import (  # noqa: E402
    Context, closed, drop_last_number, fit, grouped, in_base, negate_last, percent_last, wrap, wrap_last,
)

DEG = Context(angle="deg")


@pytest.mark.parametrize("text, context, value", [
    ("sin(90)", DEG, 1), ("sin(180)", DEG, 0), ("cos(90)", DEG, 0), ("asin(1)", DEG, 90), ("atan(1)", DEG, 45),
    ("sin(100)", Context(angle="grad"), 1), ("sin(pi/2)", Context(), 1), ("arctan(1)", DEG, 45),
    ("sinh(0)", DEG, 0), ("acosh(1)", DEG, 0), ("abs(-3)", DEG, 3), ("cbrt(-27)", DEG, -3), ("root(32,5)", DEG, 2),
    ("log(100)", DEG, 2), ("log2(8)", DEG, 3), ("5!", DEG, 120), ("3!^2", DEG, 36), ("fact(4)", DEG, 24),
    ("e", DEG, 2.718281828), ("ans*2", Context(ans=21), 42), ("ans", Context(), 0),
    ("6 AND 3", DEG, 2), ("6 OR 3", DEG, 7), ("6 XOR 3", DEG, 5), ("7 MOD 3", DEG, 1), ("NOT 0", DEG, -1),
])
def test_the_scientific_names_and_the_word_operators(text, context, value):
    assert evaluate(text, context) == pytest.approx(value, abs=1e-9)


@pytest.mark.parametrize("text", ["tan(90)", "asin(2)", "(-1)!", "1.5!", "root(-4,2)"])
def test_scientific_errors(text):
    with pytest.raises(CalcError):
        evaluate(text, DEG)


def test_dns_names_are_untouched_by_the_default_context():
    assert evaluate("sin(90)") == pytest.approx(math.sin(90))
    assert evaluate("rad(pi)") == pytest.approx(180)


@pytest.mark.parametrize("text, context, value", [
    ("FF", Context(radix=16, bits=8, signed=False), 255), ("FF", Context(radix=16, bits=8), -1),
    ("7F+1", Context(radix=16, bits=8), -128), ("E", Context(radix=16, bits=64), 14),
    ("101b", Context(radix=16, bits=64), 0x101B), ("$10", Context(radix=2, bits=64), 16),
    ("101", Context(radix=2, bits=64), 5), ("17", Context(radix=8, bits=64), 15),
    ("7/2", Context(bits=64), 3), ("-7/2", Context(bits=64), -3),
    ("1 ROL 9", Context(bits=8, signed=False), 2), ("1 ROR 1", Context(bits=8, signed=False), 128),
    ("80 SHR 4", Context(radix=16, bits=8), 8), ("80 SAR 4", Context(radix=16, bits=8), -8),
    ("NOT 0", Context(bits=16, signed=False), 65535), ("5 NAND 3", Context(bits=8, signed=False), 254),
])
def test_the_programmers_word(text, context, value):
    assert evaluate(text, context) == value


@pytest.mark.parametrize("text, context", [("1.5", Context(bits=64)), ("8", Context(radix=8, bits=64)),
                                           ("2", Context(radix=2, bits=64)), ("7/0", Context(bits=64))])
def test_what_the_programmer_refuses(text, context):
    with pytest.raises(CalcError):
        evaluate(text, context)


def test_the_programmers_forms():
    assert wrap(255, 8) == -1 and wrap(255, 8, signed=False) == 255 and wrap(-1, 16, signed=False) == 65535
    assert radix(-1, 16, 8) == "FF" and grouped("11110000", 4) == "1111 0000" and grouped("377", 2) == "3 77"
    assert in_base(-255, 16) == "-FF" and in_base(5, 2) == "101" and in_base(2.5, 10) == "2.5"
    assert evaluate(in_base(-255, 16), Context(radix=16, bits=64)) == -255


def test_fit_rids_a_float_of_its_noise_and_fits_the_display():
    assert fit(0.1 + 0.2, 20) == "0.3" and fit(2 / 3, 10) == "0.66666667"
    assert fit(1e300, 20) == "1E+300" and fit(1.5e-30, 12) == "1.5E-30" and fit(10 ** 30, 16) == "1E+30"


@pytest.mark.parametrize("helper, text, result", [
    (negate_last, "5+3", "5+-3"), (negate_last, "5+-3", "5+3"), (negate_last, "", "-"),
    (negate_last, "2*(1+2)", "2*-(1+2)"), (negate_last, "1E+3", "-1E+3"),
    (drop_last_number, "12+34", "12+"), (drop_last_number, "SQRT(9)", ""),
    (percent_last, "200*50", "200*(50/100)"), (percent_last, "2+", "2+"), (closed, "SQRT(9", "SQRT(9)"),
])
def test_the_tape_helpers(helper, text, result):
    assert helper(text) == result


@pytest.mark.parametrize("text, template, result", [
    ("9", "SQRT({})", "SQRT(9)"), ("2+(1+3)", "{}^2", "2+(1+3)^2"), ("2+", "SQRT({})", "2+SQRT("),
    ("2+", "{}^2", "2+"), ("3", "1/{}", "1/3"), ("SIN(30)", "{}!", "SIN(30)!"),
])
def test_wrap_last(text, template, result):
    assert wrap_last(text, template) == result


def press(caption: str):
    """A callable pressing the pad's button showing *caption*, as a click would."""
    def action(a):
        button = next(b for b in calc(a).pad.buttons() if b.text == caption)
        a.spawn(button.press())
    return action


def test_ctrl_f6_opens_simple_and_its_keys_type_into_the_line(place):
    app = navigator(place)
    seen = {}

    def look(a):
        w = calc(a)
        seen.update(rect=(w.x, w.y, w.width, w.height), line=w.line.value, result=w.result,
                    focused=a.focused is w.line)

    run_app(app, [KeyEvent("f6", ctrl=True), lambda a: None, press("7"), press("×"), press("6"), lambda a: None,
                  look, press("="), lambda a: None,
                  lambda a: seen.update(after=calc(a).line.value, answer=calc(a).answer)])
    assert seen["rect"] == (10, 1, 32, 20) and seen["focused"]
    assert seen["line"] == "7*6" and seen["result"] == "42"
    assert seen["after"] == "42" and seen["answer"] == 42
    assert HISTORY.entries("calc")[0] == "7*6"


def test_simple_keys_apply_to_the_number_before_the_cursor(place):
    app = navigator(place)
    seen = []
    run_app(app, [KeyEvent("f6", ctrl=True), lambda a: None, *typed("2+9"), press("√"), lambda a: None,
                  lambda a: seen.append(calc(a).line.value), press("±"), lambda a: None,
                  lambda a: seen.append(calc(a).line.value), press("CE"), press("%"), lambda a: None,
                  lambda a: seen.append(calc(a).line.value), press("C"), lambda a: None,
                  lambda a: seen.append(calc(a).line.value)])
    assert seen == ["2+SQRT(9)", "2+-SQRT(9)", "2+-", ""]


def test_the_strip_the_menu_and_ctrl_f6_choose_the_face_and_it_is_kept(place):
    from navigator.widgets.shell.calculator_window.commands import CalculatorProgramming

    app = navigator(place)
    seen = []

    def look(a):
        w = calc(a)
        seen.append((w.mode, w.mode_strip.value, (w.width, w.height)))

    run_app(app, [KeyEvent("f6", ctrl=True), lambda a: None, KeyEvent("i", alt=True), lambda a: None, look,
                  lambda a: a.spawn(a.run_command(CalculatorProgramming)), lambda a: None, look,
                  KeyEvent("f6", ctrl=True), lambda a: None, look,
                  lambda a: seen.append(a.focused is calc(a).line)])
    assert seen[:3] == [("scientific", 2, (62, 20)), ("programming", 3, (62, 21)), ("simple", 0, (32, 20))]
    assert seen[3]
    assert SETTINGS.calculator.mode == "simple"


def test_the_value_crosses_into_and_out_of_the_programmers_base(place):
    SETTINGS.calculator.radix = "hex"
    app = navigator(place)
    seen = []

    def to(mode):
        return lambda a: calc(a).set_mode(mode)

    run_app(app, [KeyEvent("f6", ctrl=True), lambda a: None, *typed("200+55"), to("programming"), lambda a: None,
                  lambda a: seen.append((calc(a).line.value, list(calc(a).forms))),
                  lambda a: setattr(calc(a).base, "value", 1), lambda a: None,
                  lambda a: seen.append(calc(a).line.value), to("simple"), lambda a: None,
                  lambda a: seen.append(calc(a).line.value)])
    assert seen[0] == ("FF", ["FF", "255", "377", "1111 1111"])
    assert seen[1] == "255" and seen[2] == "255"
    assert SETTINGS.calculator.radix == "dec"


def test_a_byte_wraps_and_digits_past_the_base_are_refused(place):
    SETTINGS.calculator.mode, SETTINGS.calculator.word, SETTINGS.calculator.radix = "programming", "byte", "oct"
    app = navigator(place)
    seen = {}

    def look(a):
        w = calc(a)
        seen.update(line=w.line.value, forms=list(w.forms),
                    disabled=sorted(b.text for b in w.pad.buttons() if b.disabled))

    run_app(app, [KeyEvent("f6", ctrl=True), lambda a: None, *typed("177+1"), lambda a: None, look,
                  lambda a: seen.update(byte=seen["forms"]), *typed("+8"), lambda a: None, look])
    assert seen["byte"][:2] == ["80", "-128"]
    assert seen["line"] == "177+1+"
    assert seen["disabled"] == ["8", "9", "A", "B", "C", "D", "E", "F"]


@pytest.mark.parametrize("mode, radix, typed_text, line", [
    ("programming", "oct", "17 9$+2G", "17+2"),
    ("programming", "hex", "ff x&1", "ff&1"),
    ("programming", "bin", "102+1", "10+1"),
    ("simple", "dec", "2 + x3$", "2+3"),
    ("scientific", "dec", "sin( 90)#", "sin(90)"),
])
def test_each_face_refuses_what_its_line_has_no_use_for(place, mode, radix, typed_text, line):
    SETTINGS.calculator.mode, SETTINGS.calculator.radix = mode, radix
    app = navigator(place)
    seen = {}
    run_app(app, [KeyEvent("f6", ctrl=True), lambda a: None, *typed(typed_text), lambda a: None,
                  lambda a: seen.update(line=calc(a).line.value)])
    assert seen["line"] == line


def test_a_paste_loses_its_spaces_and_is_refused_whole_for_a_bad_character(place):
    from navkit.events import PasteEvent
    SETTINGS.calculator.mode, SETTINGS.calculator.radix = "programming", "oct"
    app = navigator(place)
    seen = []
    look = lambda a: seen.append(calc(a).line.value)  # noqa: E731
    paste = lambda text: lambda a: a.spawn(calc(a).line.on_paste(PasteEvent(text)))  # noqa: E731
    run_app(app, [KeyEvent("f6", ctrl=True), lambda a: None, paste("1 000"), lambda a: None, look,
                  paste("+19"), lambda a: None, look])
    assert seen == ["1000", "1000"]


def test_classic_takes_anything_as_dn_did(classic):
    app = navigator(classic)
    seen = {}
    run_app(app, [KeyEvent("f6", ctrl=True), lambda a: None, *typed("$FF + 1"), lambda a: None,
                  lambda a: seen.update(line=calc(a).line.value)])
    assert seen["line"] == "$FF + 1"


def test_the_bit_grid_flips_a_bit_into_the_line(place):
    SETTINGS.calculator.mode, SETTINGS.calculator.bit_keypad = "programming", True
    app = navigator(place)
    seen = {}
    run_app(app, [KeyEvent("f6", ctrl=True), lambda a: None, *typed("4"), lambda a: None,
                  lambda a: a.spawn(calc(a).bit_grid.flip(0)), lambda a: None,
                  lambda a: seen.update(line=calc(a).line.value, pad=calc(a).pad.visible,
                                        grid=calc(a).bit_grid.visible)])
    assert seen == {"line": "5", "pad": False, "grid": True}


def test_scientific_in_degrees_with_2nd_memory_and_ans(place):
    SETTINGS.calculator.mode = "scientific"
    app = navigator(place)
    seen = []
    look = lambda a: seen.append((calc(a).line.value, calc(a).result, calc(a).marks))  # noqa: E731
    run_app(app, [KeyEvent("f6", ctrl=True), lambda a: None, *typed("90"), press("sin"), lambda a: None, look,
                  press("2nd"), lambda a: None, look, press("asin"), lambda a: None, look,
                  KeyEvent("enter"), press("MS"), lambda a: None, look,
                  press("C"), press("MR"), press("+"), press("Ans"), lambda a: None, look])
    assert seen[0] == ("SIN(90)", "1", "")
    assert seen[1] == ("SIN(90)", "1", "2nd")
    assert seen[2] == ("ASIN(SIN(90))", "90", "")
    assert seen[3] == ("90", "90", "M")
    assert seen[4] == ("90+ANS", "180", "M")


def test_the_desktop_keeps_the_face(place):
    from navigator.lib.config import desktop_state

    SETTINGS.calculator.mode = "scientific"
    app = navigator(place)
    kept = {}
    run_app(app, [KeyEvent("f6", ctrl=True), lambda a: None, *typed("1+1"), lambda a: None,
                  lambda a: kept.update(desktop_state._window(calc(a)))])
    assert kept["kind"] == "calculator" and kept["mode"] == "scientific" and kept["expression"] == "1+1"

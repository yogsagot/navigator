"""Ctrl+F6: DOS Navigator's calculator (``CCALC.PAS``, ``PAR.PAS``)."""

from __future__ import annotations

import pytest

from conftest import FakeTerminal, run_app
from navkit.events import KeyEvent

from navigator.__main__ import Navigator
from navigator.calculator import CalcError, decimal, evaluate, exponent, radix, shown
from navml.history import HISTORY


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
    monkeypatch.setattr("navigator.subshell.Subshell.start", lambda self, *a, **k: None)
    return tmp_path


def navigator(path) -> Navigator:
    return Navigator(path, path, terminal=FakeTerminal(80, 24))


def calc(app):
    from navigator.widgets.shell.calculator_window import CalculatorWindow

    return next((w for w in app.shell.desktop.windows() if isinstance(w, CalculatorWindow)), None)


def typed(text: str) -> list[KeyEvent]:
    return [KeyEvent(c, c) for c in text]


def test_ctrl_f6_opens_one_calculator_where_dn_put_it_and_it_works_as_typed(place):
    app = navigator(place)
    seen = {}

    def look(a):
        w = calc(a)
        seen.update(rect=(w.x, w.y, w.width, w.height), focused=a.focused is w.line, rows=list(w.rows))

    run_app(app, [KeyEvent("f6", ctrl=True), lambda a: None, *typed("2+3*4"), lambda a: None, look,
                  KeyEvent("f6", ctrl=True), lambda a: None,
                  lambda a: seen.update(count=sum(1 for w in a.shell.desktop.windows()
                                                  if w is calc(a)))])
    assert seen["rect"] == (10, 5, 49, 15) and seen["focused"]
    assert seen["rows"] == ["14", "E", "1110", "16", "1.4000000000E+01"]
    assert seen["count"] == 1


def test_enter_puts_the_value_in_and_then_an_operator_goes_on_from_it_a_digit_starts_again(place):
    app = navigator(place)
    seen = {}
    run_app(app, [KeyEvent("f6", ctrl=True), lambda a: None, *typed("6*7"), KeyEvent("enter"), lambda a: None,
                  lambda a: seen.update(after=calc(a).line.value, selected=calc(a).line.selected_text),
                  *typed("+1"), lambda a: None, lambda a: seen.update(on=calc(a).line.value, row=calc(a).rows[0]),
                  KeyEvent("enter"), *typed("5"), lambda a: None, lambda a: seen.update(fresh=calc(a).line.value)])
    assert seen["after"] == seen["selected"] == "42"
    assert seen["on"] == "42+1" and seen["row"] == "43"
    assert seen["fresh"] == "5"
    assert HISTORY.entries("calc")[:2] == ["42+1", "6*7"]


def test_an_error_shows_error_and_esc_closes_keeping_the_line(place):
    app = navigator(place)
    seen = {}
    run_app(app, [KeyEvent("f6", ctrl=True), lambda a: None, *typed("1/0"), lambda a: None,
                  lambda a: seen.update(rows=list(calc(a).rows)), KeyEvent("escape"), lambda a: None,
                  lambda a: seen.update(gone=calc(a) is None)])
    assert seen["rows"] == ["", "", "Error", "", ""] and seen["gone"]
    assert HISTORY.entries("calc")[0] == "1/0"


def test_copy_as_hex_puts_the_hex_form_on_the_clipboard(place):
    app = navigator(place)
    copied = []
    app.copy_to_clipboard = lambda text, **kw: copied.append(text)
    run_app(app, [KeyEvent("f6", ctrl=True), lambda a: None, *typed("255"),
                  KeyEvent("h", alt=True), KeyEvent("c", alt=True), lambda a: None])
    assert copied == ["FF"]


def test_tab_stays_in_the_window(place):
    app = navigator(place)
    seen = []

    def where(a):
        w = calc(a)
        seen.append(w._holds(a.focused))

    run_app(app, [KeyEvent("f6", ctrl=True), lambda a: None,
                  *[step for _ in range(8) for step in (KeyEvent("tab"), where)]])
    assert all(seen) and len(seen) == 8

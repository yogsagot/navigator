"""Event value objects: naming, matching and modifiers."""

from __future__ import annotations

import pytest

from navkit.events import KeyEvent, MouseEvent


@pytest.mark.parametrize(
    ("event", "expected"),
    [
        (KeyEvent("a"), "a"),
        (KeyEvent("f10"), "f10"),
        (KeyEvent("q", ctrl=True), "ctrl+q"),
        (KeyEvent("x", alt=True), "alt+x"),
        (KeyEvent("tab", shift=True), "shift+tab"),
        (KeyEvent("up", ctrl=True, shift=True), "ctrl+shift+up"),
        (KeyEvent("del", ctrl=True, alt=True, shift=True), "ctrl+alt+shift+del"),
    ],
)
def test_names_list_modifiers_in_a_fixed_order(event, expected):
    assert event.name == expected


@pytest.mark.parametrize("spec", ["ctrl+q", "Ctrl+Q", "CTRL+q", " ctrl + q "])
def test_matches_is_forgiving_about_spelling(spec):
    assert KeyEvent("q", ctrl=True).matches(spec)


def test_matches_ignores_the_order_modifiers_are_written_in():
    assert KeyEvent("up", ctrl=True, shift=True).matches("shift+ctrl+up")


def test_matches_accepts_several_alternatives():
    event = KeyEvent("f10")
    assert event.matches("f10", "ctrl+q")
    assert event.matches("ctrl+q", "f10")
    assert not event.matches("f1", "escape")


def test_matches_distinguishes_modifiers():
    assert not KeyEvent("q").matches("ctrl+q")
    assert not KeyEvent("q", ctrl=True).matches("q")
    assert not KeyEvent("q", ctrl=True).matches("ctrl+alt+q")


@pytest.mark.parametrize(
    ("event", "printable"),
    [
        (KeyEvent("a", "a"), True),
        (KeyEvent("A", "A", shift=True), True),
        (KeyEvent("q", ctrl=True), False),
        (KeyEvent("x", "x", alt=True), False),
        (KeyEvent("f10"), False),
        (KeyEvent("enter", "\n"), False),
        (KeyEvent("tab", "\t"), False),
    ],
)
def test_is_printable(event, printable):
    assert event.is_printable is printable


def test_wheel_detection():
    assert MouseEvent(0, 0, "wheel_up").is_wheel
    assert MouseEvent(0, 0, "wheel_down").is_wheel
    assert not MouseEvent(0, 0, "left").is_wheel


def test_events_are_immutable():
    with pytest.raises(AttributeError):
        KeyEvent("a").key = "b"
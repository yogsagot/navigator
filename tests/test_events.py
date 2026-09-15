"""Event value objects: naming, matching, modifiers and handler names."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

import pytest

from navkit.events import (
    Event,
    KeyEvent,
    MouseEvent,
    PasteEvent,
    ResizeEvent,
    WakeEvent,
)


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

# -- handler names ---------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ClickEvent(Event):
    x: int = 0


@dataclass(frozen=True, slots=True)
class DoubleClickEvent(ClickEvent):
    pass


@dataclass(frozen=True, slots=True)
class SelectionChanged(Event):
    index: int = 0


@dataclass(frozen=True, slots=True)
class Renamed(Event):
    handler: ClassVar[str] = "on_something_else"


@pytest.mark.parametrize(
    ("event_class", "expected"),
    [
        (KeyEvent, "on_key"),
        (MouseEvent, "on_mouse"),
        (ResizeEvent, "on_resize"),
        (PasteEvent, "on_paste"),
        (WakeEvent, "on_wake"),
    ],
)
def test_the_events_that_predate_the_rule_obey_it(event_class, expected):
    # The derivation was read off these four, not imposed on them: each name
    # is the hook Application already declares.
    assert event_class.handler == expected


@pytest.mark.parametrize(
    ("event_class", "expected"),
    [
        (ClickEvent, "on_click"),
        (SelectionChanged, "on_selection_changed"),
        (Renamed, "on_something_else"),
    ],
)
def test_a_new_event_names_its_own_handler(event_class, expected):
    assert event_class.handler == expected


def test_a_subclass_does_not_inherit_the_handler_it_refines():
    # Otherwise a widget wanting only the plain click could not say so.
    assert DoubleClickEvent.handler == "on_double_click"
    assert issubclass(DoubleClickEvent, ClickEvent)


def test_deriving_a_handler_leaves_the_dataclass_alone():
    # @dataclass(slots=True) rebuilds the class; __init_subclass__ has to
    # survive that, and so do the value semantics every event relies on.
    assert ClickEvent.__slots__ == ("x",)
    assert ClickEvent(2) == ClickEvent(2)
    assert "handler" not in ClickEvent.__slots__

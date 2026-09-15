"""Event value objects: naming, matching, modifiers and handler names."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

import pytest

from navkit.events import (
    DoubleClickEvent,
    Event,
    KeyEvent,
    MouseClickEvent,
    PasteEvent,
    ResizeEvent,
    WakeEvent,
    emitted,
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
    assert MouseClickEvent(0, 0, "wheel_up").is_wheel
    assert MouseClickEvent(0, 0, "wheel_down").is_wheel
    assert not MouseClickEvent(0, 0, "left").is_wheel


def test_events_are_immutable():
    with pytest.raises(AttributeError):
        KeyEvent("a").key = "b"

# -- handler names ---------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ClickEvent(Event):
    x: int = 0


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
        (MouseClickEvent, "on_mouse_click"),
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
    # Otherwise a widget wanting only the plain press could not say so.
    # Asked of navkit's own refinement rather than a fixture: this is the
    # case the rule was written for, and the one both dispatch walks read.
    assert DoubleClickEvent.handler == "on_double_click"
    assert issubclass(DoubleClickEvent, MouseClickEvent)
    assert MouseClickEvent.handler == "on_mouse_click"


def test_deriving_a_handler_leaves_the_dataclass_alone():
    # @dataclass(slots=True) rebuilds the class; __init_subclass__ has to
    # survive that, and so do the value semantics every event relies on.
    assert ClickEvent.__slots__ == ("x",)
    assert ClickEvent(2) == ClickEvent(2)
    assert "handler" not in ClickEvent.__slots__


# -- what a widget declares it emits ---------------------------------------


class Sender:
    """Stands in for a widget: `emitted` only reads class attributes."""

    emits: tuple[type[Event], ...] = ()


def test_a_class_declaring_nothing_emits_nothing():
    assert emitted(Sender) == frozenset()


def test_emitted_unions_down_the_mro_rather_than_shadowing():
    # Where it parts company with declarations(): two declarations of one
    # attribute are two versions of the same thing, so the nearest wins --
    # but a subclass that emits something new is *adding*, so a derived
    # component keeps its base's events without naming them.
    class Base(Sender):
        emits = (ClickEvent,)

    class Derived(Base):
        emits = (SelectionChanged,)

    assert emitted(Base) == {ClickEvent}
    assert emitted(Derived) == {ClickEvent, SelectionChanged}


def test_a_subclass_that_adds_nothing_keeps_what_it_inherits():
    class Base(Sender):
        emits = (ClickEvent,)

    class Derived(Base):
        pass

    assert emitted(Derived) == {ClickEvent}


def test_the_declaration_names_the_handler_each_event_reaches():
    # What navml's generator asks: an `on_click:' line on this widget is
    # legal because the widget says it emits something that lands there.
    class Base(Sender):
        emits = (ClickEvent, SelectionChanged)

    assert {e.handler for e in emitted(Base)} == {"on_click", "on_selection_changed"}


# -- the double-click navkit synthesises -----------------------------------


def test_a_double_click_is_a_mouse_event_and_is_not_equal_to_one():
    """Both halves matter: it is a MouseClickEvent so that positional routing,
    coordinate translation and the modal reroute cost nothing, and it is not
    *equal* to one so that a test -- or a handler -- can tell them apart."""
    press = MouseClickEvent(3, 4, "left", "press")
    double = DoubleClickEvent.of(press)

    assert isinstance(double, MouseClickEvent)
    assert double != press
    assert (double.x, double.y, double.button, double.action) == (3, 4, "left", "press")


def test_translating_a_double_click_keeps_it_one():
    """``translated`` rebuilds through ``dataclasses.replace``, which keeps the
    subclass -- which is the whole of why modal routing needed no changes."""
    double = DoubleClickEvent.of(MouseClickEvent(3, 4, "left", "press"))
    moved = double.translated(-1, -2)

    assert type(moved) is DoubleClickEvent
    assert (moved.x, moved.y) == (2, 2)


def test_it_carries_the_modifiers_of_the_press_it_completed():
    press = MouseClickEvent(1, 1, "right", "press", ctrl=True, shift=True)
    double = DoubleClickEvent.of(press)

    assert (double.button, double.ctrl, double.alt, double.shift) == (
        "right", True, False, True,
    )

"""Terminal events.

Everything the outside world does to the application arrives as one of these:
keys, mouse actions, terminal resizes and bracketed pastes.  A widget's own
events -- "this button was pressed" -- are the same objects travelling the
other way, through :meth:`navkit.widget.Widget.announce`.  Events are
immutable value objects: handlers report that they consumed an event by
returning ``True``, never by mutating it.

Every event class knows the name of the handler that receives it.  It is
derived from the class name rather than registered anywhere -- strip a
trailing ``Event``, snake-case the rest, prefix ``on_`` -- so ``KeyEvent``
reaches ``on_key`` and a ``ClickEvent`` declared elsewhere reaches
``on_click`` without asking anybody.  The four events below already obeyed
that rule before it was written down.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
from typing import ClassVar

#: Splits a CamelCase name before each capital that is not the first.
_CAMEL = re.compile(r"(?<!^)(?=[A-Z])")


def handler_name(class_name: str) -> str:
    """The handler ``class_name`` is delivered to: ``KeyEvent`` -> ``on_key``."""
    stem = class_name[:-5] if class_name.endswith("Event") and len(class_name) > 5 else class_name
    return "on_" + _CAMEL.sub("_", stem).lower()


@dataclass(frozen=True, slots=True)
class Event:
    """Base class for everything the event loop dispatches.

    :attr:`handler` is the attribute name a dispatcher looks for -- on a
    widget, on one of its ancestors, or on the application.  A subclass gets
    its own rather than inheriting one, so ``DoubleClickEvent`` reaches
    ``on_double_click`` and not the ``on_click`` it refines; declare
    ``handler: ClassVar[str] = "on_whatever"`` in the class body to override.
    """

    #: Where this event is delivered.  Derived in ``__init_subclass__``.
    handler: ClassVar[str] = "on_event"

    def __init_subclass__(cls, **kwargs: object) -> None:
        # Not the zero-argument ``super()``: ``@dataclass(slots=True)``
        # *replaces* the class it decorates, and the ``__class__`` cell the
        # implicit form closes over still names the pre-slots ``Event``, which
        # no subclass of the new one is an instance of.  Naming the global
        # resolves it at call time, after the rebuild.
        super(Event, cls).__init_subclass__(**kwargs)  # noqa: UP008
        if "handler" not in cls.__dict__:
            cls.handler = handler_name(cls.__name__)


def _normalize(spec: str) -> str:
    """Canonicalise a key spec such as ``"Ctrl+F10"`` into ``"ctrl+f10"``."""
    parts = [p.strip().lower() for p in spec.split("+") if p.strip()]
    if not parts:
        return ""
    *mods, key = parts
    order = {"ctrl": 0, "alt": 1, "shift": 2}
    mods = sorted(set(mods), key=lambda m: order.get(m, 99))
    return "+".join([*mods, key])


@dataclass(frozen=True, slots=True)
class KeyEvent(Event):
    """A single key press.

    ``key`` is the canonical name of the key: a single character for printable
    keys (always lower case -- capitals are reported as ``shift`` plus the
    letter's ``char``), or a name such as ``"f10"``, ``"pagedown"``, ``"enter"``
    or ``"escape"``.  ``char`` carries the text the key produces, if any.
    """

    key: str
    char: str | None = None
    ctrl: bool = False
    alt: bool = False
    shift: bool = False

    @property
    def name(self) -> str:
        """The full key name including modifiers, e.g. ``"ctrl+alt+f5"``."""
        mods = []
        if self.ctrl:
            mods.append("ctrl")
        if self.alt:
            mods.append("alt")
        if self.shift:
            mods.append("shift")
        return "+".join([*mods, self.key])

    def matches(self, *specs: str) -> bool:
        """True if this key press is any of *specs* (``"ctrl+q"``, ``"f10"``)."""
        return any(self.name == _normalize(spec) for spec in specs)

    @property
    def is_printable(self) -> bool:
        """True if this key produced text that a text widget should insert."""
        return bool(self.char) and not self.ctrl and not self.alt and self.char >= " "


@dataclass(frozen=True, slots=True)
class MouseEvent(Event):
    """A mouse action at zero-based cell coordinates *x*, *y*.

    ``button`` is one of ``left``, ``middle``, ``right``, ``wheel_up``,
    ``wheel_down``, ``wheel_left``, ``wheel_right`` or ``none``; ``action`` is
    ``press``, ``release`` or ``move``.
    """

    x: int
    y: int
    button: str = "none"
    action: str = "press"
    ctrl: bool = False
    alt: bool = False
    shift: bool = False

    @property
    def is_wheel(self) -> bool:
        return self.button.startswith("wheel_")

    def translated(self, dx: int, dy: int) -> MouseEvent:
        """The same action, moved into another widget's coordinates."""
        return replace(self, x=self.x + dx, y=self.y + dy)


@dataclass(frozen=True, slots=True)
class ResizeEvent(Event):
    """The terminal window changed size."""

    width: int
    height: int


@dataclass(frozen=True, slots=True)
class PasteEvent(Event):
    """Text pasted while bracketed paste mode was active."""

    text: str


@dataclass(frozen=True, slots=True)
class WakeEvent(Event):
    """Internal: wakes the event loop so it can repaint or shut down."""
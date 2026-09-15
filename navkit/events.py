"""Terminal events.

Everything the outside world does to the application arrives as one of these:
keys, mouse actions, terminal resizes and bracketed pastes.  A widget's own
events -- "this button was pressed" -- are the same objects travelling the
other way, through :meth:`navkit.widget.Widget.emit`.  Events are
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


def emitted(cls: type) -> frozenset[type[Event]]:
    """Every event *cls* and its bases declare they emit.

    The counterpart of :func:`navkit.reactive.declarations` for events, and
    the one place a widget's emitted surface is answered for -- a reader, a
    type checker and navml's code generator all ask this rather than looking
    for ``emit`` calls.

    **It unions over the MRO rather than shadowing**, which is where it parts
    company with ``declarations()``: an override there replaces what it
    inherits, because two declarations of one name are two versions of the
    same attribute.  A subclass that emits something new is *adding* to what
    its base emits, never replacing it, so a derived component need not name
    its base's events to keep them.
    """
    found: set[type[Event]] = set()
    for klass in cls.__mro__:
        found.update(vars(klass).get("emits", ()))
    return frozenset(found)


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
class DoubleClickEvent(MouseEvent):
    """One button pressed twice at one cell, inside the double-click window.

    A statement about *input*, not about meaning.  navkit says the two presses
    happened close together in one place and never that the thing under them
    should open -- that is the application's, exactly as navkit says F10 was
    pressed and never that F10 quits.  The terminal reports no such thing
    itself: SGR gives ``press``, ``release`` and ``move``, so this is
    synthesised from two presses and a clock, the way a lone ``ESC`` becomes
    an escape key.  See *Double-click: a timer, not a meaning* in
    ``navkit/DESIGN.md``.

    It carries the press it completed -- same cell, same button, same
    modifiers, ``action`` still ``"press"`` -- so a handler filters by button
    the way one reading a plain press already does.

    Delivered to ``on_double_click`` and never to ``on_mouse``: the handler
    name is derived from the class and both dispatch walks read it.  A widget
    defining no ``on_double_click`` is skipped, and skipped is what "did not
    claim it" already means there, so the event falls outward to an ancestor
    exactly as an unhandled press does and nothing needs a stub.

    **A `MouseEvent`, so that routing costs nothing.**  :meth:`translated`
    rebuilds through :func:`~dataclasses.replace`, which keeps the subclass,
    so the inward coordinate shift, the hit test and the modal reroute all
    work on one of these without knowing it exists.  The price is that
    ``isinstance(event, MouseEvent)`` is true of it -- relied on in
    ``Application._handle``, and a trap anywhere that meant *only* a plain
    mouse action.
    """

    @classmethod
    def of(cls, press: MouseEvent) -> DoubleClickEvent:
        """The same press, re-raised as the double-click it completed."""
        return cls(
            x=press.x,
            y=press.y,
            button=press.button,
            action=press.action,
            ctrl=press.ctrl,
            alt=press.alt,
            shift=press.shift,
        )


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
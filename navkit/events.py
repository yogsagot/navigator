"""Terminal events.

Everything the outside world does to the application arrives as one of these:
keys, mouse actions, terminal resizes and bracketed pastes.  Events are
immutable value objects -- handlers report that they consumed an event by
returning ``True``, never by mutating it.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Event:
    """Base class for everything the event loop dispatches."""


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
"""navkit -- the Navigator application core.

The bottom layer of the project: an async application loop, an ANSI terminal,
a screen buffer and the widget base class.  It knows nothing about the markup
language in :mod:`navml` or about the file manager built on top of both.
"""

from navkit.application import Application
from navkit.events import (
    DoubleClickEvent,
    Event,
    KeyEvent,
    MouseClickEvent,
    PasteEvent,
    ResizeEvent,
    emitted,
)
from navkit.reactive import (
    Binding,
    CycleError,
    ReactiveError,
    bind,
    computed,
    declarations,
    dispose_effects,
    effect,
    flush_effects,
    is_bound,
    peek,
    reactive,
    unbind,
    untracked,
)
from navkit.screen import ScreenBuffer, Surface
from navkit.style import DEFAULT_STYLE, Style
from navkit.terminal import Terminal
from navkit.widget import Widget

__all__ = [
    "Application",
    "Binding",
    "CycleError",
    "DEFAULT_STYLE",
    "DoubleClickEvent",
    "Event",
    "KeyEvent",
    "MouseClickEvent",
    "PasteEvent",
    "ReactiveError",
    "ResizeEvent",
    "ScreenBuffer",
    "Surface",
    "Style",
    "Terminal",
    "Widget",
    "bind",
    "computed",
    "declarations",
    "dispose_effects",
    "effect",
    "emitted",
    "flush_effects",
    "is_bound",
    "peek",
    "reactive",
    "unbind",
    "untracked",
]
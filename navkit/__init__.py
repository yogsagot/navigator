"""navkit -- the Navigator application core.

The bottom layer of the project: an async application loop, an ANSI terminal,
a screen buffer and the widget base class.  It knows nothing about the markup
language in :mod:`navml` or about the file manager built on top of both.
"""

from navkit.application import Application
from navkit.events import (
    Event,
    KeyEvent,
    MouseEvent,
    PasteEvent,
    ResizeEvent,
)
from navkit.screen import ScreenBuffer
from navkit.style import DEFAULT_STYLE, Style
from navkit.terminal import Terminal
from navkit.widget import Widget

__all__ = [
    "Application",
    "DEFAULT_STYLE",
    "Event",
    "KeyEvent",
    "MouseEvent",
    "PasteEvent",
    "ResizeEvent",
    "ScreenBuffer",
    "Style",
    "Terminal",
    "Widget",
]
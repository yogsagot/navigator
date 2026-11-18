"""What ``help_window.nml`` cannot say: which page, the two commands that
name one, and Ctrl+F5's move and size."""

from __future__ import annotations

from typing import Any

from navkit.commands import Command
from navkit.events import KeyEvent
from navkit.i18n import tr
from navkit.reactive import bind, unbind
from navkit.widget import Widget
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.scroll_bar import ScrollEvent

from navigator.lib.help import pages
from navigator.widgets.help.commands import GoBack, GoToReference, HelpIndex, HelpOnHelp

#: The smallest Ctrl+F5 makes it: a line of a page and room for the title.
MIN_WIDTH, MIN_HEIGHT = 30, 6
#: What an arrow does to the corner (and, with Shift, to the size): Turbo
#: Vision's ``dmDragMove``/``dmDragGrow``, as ``navml``'s ``Window`` has them.
_MOVES = {"left": (-1, 0), "right": (1, 0), "up": (0, -1), "down": (0, 1)}

Rect = tuple[int, int, int, int]


def fit(rect: Rect, width: int, height: int) -> Rect:
    """*rect* (``x, y, width, height``) as it fits a screen *width* by
    *height*: no smaller than the minimum where there is the room, no larger
    than the screen, and all of it on the screen."""
    x, y, w, h = rect
    w = max(min(MIN_WIDTH, width), min(w, width))
    h = max(min(MIN_HEIGHT, height), min(h, height))
    return max(0, min(x, width - w)), max(0, min(y, height - h)), w, h


class HelpWindow(Dialog):
    """Help, opened on *topic* (``page.md#anchor``; the contents page by default)."""

    def __init__(self, topic: str = pages.CONTENTS, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        # ``Modal`` centres it; here it is where Ctrl+F5 put it, when it has.
        # Bound still, as a modal's geometry must be -- to ``placed``.
        unbind(self, Widget.x)
        unbind(self, Widget.y)
        self.x = bind(lambda me: me._corner(0))
        self.y = bind(lambda me: me._corner(1))
        #: While Ctrl+F5 has the keyboard: ``placed`` as it was, for Esc.
        self._key_move: tuple[Rect | None] | None = None
        self.viewer.show(topic)

    def toggle_zoom(self) -> None:
        self.zoomed = not self.zoomed

    # -- where it is ---------------------------------------------------------------

    def placed_size(self, width: int, height: int) -> tuple[int, int]:
        """The size ``placed`` asks for, as a screen *width* by *height* allows."""
        return fit(self.placed, width, height)[2:]

    def _corner(self, axis: int) -> int:
        parent = self.parent
        if parent is None:
            return 0
        if self.placed and not self.zoomed:
            return fit(self.placed, parent.width, parent.height)[axis]
        own, room = (self.width, parent.width) if axis == 0 else (self.height, parent.height)
        return max(0, (room - own) // 2)

    # -- the keyboard move/size mode: ``Window``'s, for a modal ---------------------

    @property
    def moving(self) -> bool:
        """Whether the keyboard is moving or sizing the window."""
        return self._key_move is not None

    def begin_move(self) -> None:
        """Ctrl+F5: arrows move, Shift+arrows size, Enter keeps it, Esc puts it back."""
        if self._key_move is not None or self.parent is None:
            return
        if self.zoomed:
            self.zoomed = False
        self._key_move = (self.placed,)
        # The keyboard stays on the page, which hands every key here: nearer
        # than this window's own table, whose Enter and Tab follow links.
        self.viewer.focus()
        self.viewer.key_taker = self._move_key

    def end_move(self, keep: bool = True) -> None:
        if self._key_move is None:
            return
        (before,), self._key_move = self._key_move, None
        self.viewer.key_taker = None
        if not keep:
            self.placed = before

    async def _move_key(self, event: KeyEvent) -> bool:
        if event.matches("enter"):
            self.end_move(keep=True)
        elif event.matches("escape"):
            self.end_move(keep=False)
        else:
            parent = self.parent
            x, y, width, height = self.x, self.y, self.width, self.height
            for name, (dx, dy) in _MOVES.items():
                if event.matches(name):
                    self.placed = fit((x + dx, y + dy, width, height), parent.width, parent.height)
                    break
                if event.matches(f"shift+{name}"):
                    # Sized from the corner: no further than the screen's edge.
                    grown = (x, y, min(width + dx, parent.width - x), min(height + dy, parent.height - y))
                    self.placed = fit(grown, parent.width, parent.height)
                    break
        # Everything else is swallowed, as a window's mode does.
        return True

    async def on_help_on_help(self, event: HelpOnHelp) -> bool:
        self.viewer.show(pages.HELP_ON_HELP)
        return True

    async def on_help_index(self, event: HelpIndex) -> bool:
        self.viewer.show(pages.CONTENTS)
        return True

    async def on_bar_scroll(self, event: ScrollEvent) -> bool:
        self.viewer.scroll_to(event.value)
        return True

    async def on_hbar_scroll(self, event: ScrollEvent) -> bool:
        self.viewer.scroll_sideways_to(event.value)
        return True

    def refusal(self, command: Command) -> str:
        viewer = self.viewer
        if isinstance(command, GoBack) and not viewer.history:
            return tr("This is the first page")
        if isinstance(command, GoToReference) and not 0 <= viewer.selected < len(viewer.links):
            return tr("No link is selected")
        return super().refusal(command)

    def key_hints(self) -> list[tuple[str, str]]:
        """``StatusDef hcHelp``'s items no function key carries; while Ctrl+F5
        has the keyboard, its keys instead."""
        if self._key_move is not None:
            arrows = "\u2190\u2191\u2192\u2193" if self.glyphs > 1 else "Arrows"
            return [(arrows, tr("Move")), ("Shift+" + arrows, tr("Size")), ("Enter", tr("Keep")), ("Esc", tr("Undo"))]
        return [("Tab", tr("Next topic")), ("Enter", tr("Go to reference"))]

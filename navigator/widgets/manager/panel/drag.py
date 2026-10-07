"""Dragging files out of a panel with the mouse: DOS Navigator's
``CM_DragDropper``, ``DragMover`` and ``TDragger`` (FLTOOLS.PAS).

With File Manager Setup's *Drag-and-drop* ticked (``fmoDragAndDrop``), a left
press on a row followed by a move with the button held picks up the tagged
files when the row is tagged, else the row's own file (never ``..``).  A
one-line label -- the name, or *N selected files* -- follows the pointer
with a shadow, as ``TDragger`` did, and the release drops them on what is
under it: a panel (its directory, or the directory row under the pointer) or
a directory tree (the directory under the pointer).  Dropping on the panel
dragged from counts only on one of its directory rows, as ``CM_Dropped``
refused the rest.  The drop is the :class:`Dropped` event, which the source
panel emits and its file manager answers by copying -- or moving, Shift held
at the release, as ``ShiftState`` said.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from navkit.events import Event
from navkit.screen import Surface
from navkit.widget import Widget


@dataclass(frozen=True, slots=True)
class Dropped(Event):
    """*entries*, dragged out of *source*, dropped on *target*: copy them there
    (``cmDropped``).  *panel* is the panel dropped on, if it was one."""

    source: Any
    entries: tuple[Any, ...]
    target: Path
    move: bool
    panel: Any = None


class DragLabel(Widget):
    """``TDragger``: what is being dragged, on one line under the pointer.

    Laid out by nobody but the drag: a resize would otherwise make it the
    size of the screen.
    """

    shadow = True
    dims_behind = False

    def __init__(self, text: str, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.text = f" {text} "
        self.width, self.height = len(self.text), 1

    def layout(self, width: int, height: int) -> None:
        pass

    def place(self, x: int, y: int, width: int, height: int) -> None:
        """At *x*, *y* on a screen *width* x *height*, kept on it whole."""
        self.x = max(0, min(x, width - self.width))
        self.y = max(0, min(y, height - 1))

    def render(self, surface: Surface) -> None:
        surface.draw_text(0, 0, self.text, self.style, self.width)


def label_for(entries: list[Any]) -> str:
    """The name, or ``N selected files`` (``dlSelectedFiles``)."""
    return entries[0].name if len(entries) == 1 else f"{len(entries)} selected files"


def drop_target(app: Any, x: int, y: int, source: Any) -> tuple[Path, Any] | None:
    """Where a drop at screen *x*, *y* puts the files, and the panel it is on.

    A panel takes them into the directory row under the pointer or else its
    own directory -- its own entries only into one of its directory rows; a
    directory tree into the directory under the pointer.  None for anything
    else, or a *Find:* listing, which is not a directory to copy into.
    """
    from navml.widgets.dialog.tree_view import TreeView

    from navigator.widgets.manager.panel.panel import Panel

    root = app.root
    widget = root.widget_at(x, y) if root is not None else None
    while widget is not None and not isinstance(widget, (Panel, TreeView)):
        widget = widget.parent
    if widget is None:
        return None
    ox, oy = widget.offset()
    index = widget.index_at(x - ox - widget.x, y - oy - widget.y)
    if isinstance(widget, TreeView):
        if index is None:
            return None
        where = widget.items[index].node.data
        return (Path(where), None) if isinstance(where, Path) else None
    if widget.found is not None or widget.error is not None:
        return None
    entry = widget.items[index] if index is not None else None
    if entry is not None and entry.is_dir:
        here = Path(widget.path)
        target = here.parent if entry.name == ".." else entry.path_in(here)
        return target, widget
    if widget is source:
        return None
    return Path(widget.path), widget

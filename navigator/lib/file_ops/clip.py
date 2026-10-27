"""Files waiting to be pasted: the panels' Ctrl+C/Ctrl+X, then Ctrl+V.

A departure: DOS Navigator's panel Ctrl+Ins (``_CtrlIns`` in ``FLPANELX.PAS``)
put the selection's names on the clipboard and remembered nothing.  Here the
same keys also remember the entries, *to copy* or *to move*, and a paste in
another directory runs F5's or F6's dialog on them -- the desktop file
managers' habit.  The clipboard gets each entry's full path, one a line.

One clip for the whole application, since a paste may go to another file
manager window.  Reactive, so every panel that shows a clipped entry repaints
when it changes; each field is replaced, never mutated.
"""

from __future__ import annotations

from typing import Any, Callable

from navkit.reactive import reactive


class FileClip:
    """What Ctrl+C or Ctrl+X left to paste, if anything."""

    #: Where the entries were listed when they were clipped: the dialog's
    #: *here*, whatever the panel has shown since.
    here: Any = reactive(None)
    #: The entries themselves, as the panel listed them.
    entries: tuple[Any, ...] = reactive(())
    #: Where each entry is, for a panel to know which of its rows to mark.
    locations: frozenset[Any] = reactive(frozenset())
    #: Ctrl+X's: the paste moves rather than copies.
    move: bool = reactive(False)

    def __init__(self) -> None:
        #: What went on the clipboard with them, so the application can tell
        #: its own copy from any other, which drops the clip.
        self.text = ""
        #: Called on every change: the application's ``invalidate``.  Not a
        #: widget's attributes, so a change here would otherwise mark the
        #: panels stale and ask for no frame (``Widget._reactive_changed``).
        self.listener: Callable[[], None] | None = None

    def _reactive_changed(self, name: str) -> None:
        if self.listener is not None:
            self.listener()

    def set(self, here: Any, entries: list[Any], locations: list[Any], *, move: bool) -> str:
        """Remember *entries* of *here*; the clipboard's text for them."""
        self.here = here
        self.entries = tuple(entries)
        self.locations = frozenset(locations)
        self.move = move
        self.text = "\n".join(str(location) for location in locations)
        return self.text

    def clear(self) -> None:
        if self.entries:
            self.here = None
            self.entries = ()
            self.locations = frozenset()
            self.move = False
        self.text = ""

    def __bool__(self) -> bool:
        return bool(self.entries)

    def holds(self, location: Any) -> bool:
        return location in self.locations


#: The application's one clip.
CLIP = FileClip()

"""Edits, and taking them back: ``TFileEditor``'s text and ``UndoInfo``.

Every change goes through :meth:`EditBuffer.insert` or :meth:`EditBuffer.delete`,
and each records what it did in the open *group*.  Undo takes back a whole
group and puts the cursor where the group began.  **Typing merges**: a run of
characters inserted one after another, or deleted by one Backspace or Del
after another, is one group, as DN's ``udInsChar``/``udDelChar`` records
merged -- so one undo takes back a word typed, not a letter.

**Modified is a save point, not a counter.**  DN counted edits (``UndoTimes``)
and cleared ``Modified`` when undo brought the count back to zero; here
:meth:`EditBuffer.mark_saved` remembers which group was on top, and the text
is modified whenever another one is.  An undo past the save point followed by a
new edit makes the saved state unreachable, and says so.

There is no redo, as there was none in DN.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from navigator.editor.document import Document, Pos, split_text


@dataclass
class Change:
    """One primitive edit: text inserted at a place, or taken out from it."""

    kind: str  # "insert" or "delete"
    at: Pos
    text: str


@dataclass
class Group:
    """Changes undone together, and where the cursor was before them."""

    before: tuple[int, int]
    merge: str | None = None
    changes: list[Change] = field(default_factory=list)


#: The save point when the saved text can no longer be reached by undoing.
_LOST = object()


class EditBuffer:
    """A document, the edits made to it, and whether it has changed since saved."""

    def __init__(self, document: Document | None = None):
        self.document = document if document is not None else Document()
        self.undo_stack: list[Group] = []
        self._open: Group | None = None
        self._saved: object = None  # the top group when last saved; None: empty stack
        #: Called after every primitive change, undo's included, with
        #: ``"insert"`` or ``"delete"`` and where it began and ended -- a
        #: delete's end being where the text it took out had ended.  What
        #: holds places in the text (a block) follows the edits through it.
        self.listeners: list[Callable[[str, Pos, Pos], None]] = []

    # -- grouping ----------------------------------------------------------------

    def begin(self, cursor: tuple[int, int], merge: str | None = None) -> None:
        """Start a group, or go on with the open one if *merge* says so.

        *merge* names a kind of edit that runs together -- ``"type"``,
        ``"back"``, ``"del"`` -- and the open group continues only while the
        same kind follows it and the save point is not the open group.
        """
        top = self.undo_stack[-1] if self.undo_stack else None
        if (merge is not None and top is not None and top is self._open
                and top.merge == merge and top is not self._saved):
            return
        self._open = Group(cursor, merge)
        self.undo_stack.append(self._open)

    def end(self) -> None:
        """Close the open group; the next edit starts another."""
        if self._open is None:
            return
        if not self._open.changes:
            self.undo_stack.remove(self._open)
            self._open = None
        elif self._open.merge is None:
            self._open = None

    def seal(self) -> None:
        """No later edit may merge into what is open: a cursor move does this."""
        self.end()
        self._open = None

    # -- the two edits -----------------------------------------------------------

    def insert(self, at: Pos, text: str) -> Pos:
        if not text:
            return at
        end = self.document.insert(at, text)
        self._record(Change("insert", at, text))
        self._tell("insert", at, end)
        return end

    def delete(self, start: Pos, end: Pos) -> str:
        if start == end:
            return ""
        if end < start:
            start, end = end, start
        text = self.document.delete(start, end)
        self._record(Change("delete", start, text))
        self._tell("delete", start, end)
        return text

    def _tell(self, kind: str, start: Pos, end: Pos) -> None:
        for listener in self.listeners:
            listener(kind, start, end)

    def _record(self, change: Change) -> None:
        if self._open is None:
            self._open = Group((change.at.line, 0))
            self.undo_stack.append(self._open)
        self._open.changes.append(change)

    # -- taking it back ----------------------------------------------------------

    @property
    def can_undo(self) -> bool:
        return any(group.changes for group in self.undo_stack)

    def undo(self) -> tuple[int, int] | None:
        """Take back the last group; return the cursor it began at, or None."""
        self.seal()
        while self.undo_stack and not self.undo_stack[-1].changes:
            self.undo_stack.pop()
        if not self.undo_stack:
            return None
        group = self.undo_stack.pop()
        document = self.document
        for change in reversed(group.changes):
            if change.kind == "insert":
                end = _end_of(change.at, change.text)
                document.delete(change.at, end)
                self._tell("delete", change.at, end)
            else:
                end = document.insert(change.at, change.text)
                self._tell("insert", change.at, end)
        if self._saved is group:
            self._saved = _LOST
        return group.before

    # -- saving ------------------------------------------------------------------

    @property
    def modified(self) -> bool:
        top = self.undo_stack[-1] if self.undo_stack else None
        return top is not self._saved

    def mark_saved(self) -> None:
        self.seal()
        self._saved = self.undo_stack[-1] if self.undo_stack else None


def _end_of(start: Pos, text: str) -> Pos:
    """Where *text* inserted at *start* ends."""
    lines, _ = split_text(text)
    if len(lines) == 1:
        return Pos(start.line, start.index + len(lines[0]))
    return Pos(start.line + len(lines) - 1, len(lines[-1]))

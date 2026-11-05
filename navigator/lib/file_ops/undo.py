"""File > Undo (Ctrl+Z): the session's file operations, taken back newest first.

Not DOS Navigator's, which had no undo outside its editors; a departure,
asked for.  What can be taken back: a copy (F5, a paste, a dropped *Copy
here*), a move (F6, a cut and paste, a dropped *Move here*), a rename
(Alt+F6, Shift+F6, Alt+A's batch), a delete to the Trash and F7's new
directory.  An erase for good, attributes and links are not.

The entries are plain records of what was done; the Manager does the
undoing, through the same workers that did the work (its questions, *As
root* and progress boxes with them).  Nothing here touches a disk.

* :class:`Moved` holds the largest piece of each source that went whole
  (``CopyJob.moved``): a directory renamed or made anew is one pair, the
  children of one merged into a directory already there one pair each.
  A file it replaced is gone for good; ``replaced`` counts them so the
  question can say so.
* :class:`Copied` holds what a copy made, each with its fingerprint
  (:mod:`navigator.lib.file_ops.uncopy`): only what is still as the copy
  left it is removed -- to the Trash on the disk, for good elsewhere.  A
  file it overwrote is gone for good; ``overwritten`` counts them.
* :class:`Trashed` holds the ``trash.Item``\\ s ``trash.move`` made; what the
  desktop's ``gio trash``/``kioclient`` took (a file system with no trash of
  its own) names nothing back and is not in it.
* :class:`MadeDirectory` is taken back only while the directory is empty:
  Undo never erases anything.

The history is the session's (:data:`UNDO`), shared by every file manager
window as the operations span them, at most :data:`LIMIT` deep.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from navkit.i18n import tr, tr_n

from navigator.lib.file_ops.filecopy import shown

#: How many operations the history keeps; the oldest goes first.
LIMIT = 50


def _common_parent(locations: list[Any]) -> Any | None:
    parents = {location.parent for location in locations}
    return next(iter(parents)) if len(parents) == 1 else None


@dataclass(frozen=True)
class Renamed:
    """Names changed in place -- Alt+F6, Shift+F6, or Alt+A's whole batch:
    ``(place, old, new)``, in the order they went."""

    pairs: tuple[tuple[Any, str, str], ...]

    def undo_pairs(self) -> list[tuple[Any, str, str]]:
        """What puts the names back: each new name to its old, the last first."""
        return [(place, new, old) for place, old, new in reversed(self.pairs)]

    def question(self) -> str:
        if len(self.pairs) == 1:
            _, old, new = self.pairs[0]
            return tr("Rename {new} back to {old}?").format(new=new, old=old)
        return tr_n("Give {n} file its old name back?", "Give {n} files their old names back?",
                    len(self.pairs))

    def undone(self) -> str:
        return tr("Renamed back")


@dataclass(frozen=True)
class Moved:
    """Entries moved: ``(source, dest)`` locations, in the order they went."""

    pairs: tuple[tuple[Any, Any], ...]
    #: Files the move replaced, which cannot come back.
    replaced: int = 0

    def undo_pairs(self) -> list[tuple[Any, Any]]:
        """Each destination back to its source, the last first."""
        return [(dest, source) for source, dest in reversed(self.pairs)]

    def question(self) -> str:
        sources = [source for source, _ in self.pairs]
        if len(sources) == 1:
            text = tr("Move {name} back to {where}?").format(
                name=sources[0].name, where=shown(sources[0].parent))
        else:
            parent = _common_parent(sources)
            if parent is not None:
                text = tr_n("Move {n} entry back to {where}?", "Move {n} entries back to {where}?",
                            len(sources), where=shown(parent))
            else:
                text = tr_n("Move {n} entry back where it was?", "Move {n} entries back where they were?",
                            len(sources))
        if self.replaced:
            text += "\n" + tr_n("The file it replaced cannot be brought back.",
                                "The {n} files it replaced cannot be brought back.", self.replaced)
        return text

    def undone(self) -> str:
        return tr("Moved back")


@dataclass(frozen=True)
class Copied:
    """What a copy made: ``(dest, fingerprint)``, in the order it went."""

    pairs: tuple[tuple[Any, Any], ...]
    #: Files the copy overwrote, which cannot come back.
    overwritten: int = 0

    @property
    def locations(self) -> list[Any]:
        return [dest for dest, _ in self.pairs]

    @property
    def to_trash(self) -> bool:
        """Whether taking it back moves to the Trash (the disk) or erases."""
        return all(location.is_local for location in self.locations)

    def question(self) -> str:
        made = self.locations
        n = len(made)
        if n == 1:
            text = tr("Remove {name}, copied to {where}?").format(
                name=made[0].name, where=shown(made[0].parent))
        else:
            parent = _common_parent(made)
            if parent is not None:
                text = tr_n("Remove the {n} entry copied to {where}?", "Remove the {n} entries copied to {where}?",
                            n, where=shown(parent))
            else:
                text = tr_n("Remove the {n} entry the copy made?", "Remove the {n} entries the copy made?", n)
        if self.to_trash:
            text += "\n" + tr_n("It goes to the Trash.", "They go to the Trash.", n)
        else:
            text += "\n" + tr_n("It is erased for good.", "They are erased for good.", n)
        if self.overwritten:
            text += "\n" + tr_n("The file it overwrote cannot be brought back.",
                                 "The {n} files it overwrote cannot be brought back.", self.overwritten)
        return text

    def undone(self) -> str:
        return tr("Copies removed")


@dataclass(frozen=True)
class Trashed:
    """Entries moved to the Trash: the ``trash.Item`` each became."""

    items: tuple[Any, ...]

    def question(self) -> str:
        if len(self.items) == 1:
            item = self.items[0]
            return tr("Restore {name} from the Trash?").format(
                name=item.original.name if item.original is not None else item.name)
        return tr_n("Restore {n} entry from the Trash?", "Restore {n} entries from the Trash?",
                    len(self.items))

    def undone(self) -> str:
        return tr("Restored from the Trash")


@dataclass(frozen=True)
class MadeDirectory:
    """F7's new directory."""

    location: Any

    def question(self) -> str:
        return tr("Remove the new directory {name}?").format(name=self.location.name)

    def undone(self) -> str:
        return tr("Directory removed")


Entry = Renamed | Copied | Moved | Trashed | MadeDirectory


class History:
    """What can be undone, newest last."""

    def __init__(self, limit: int = LIMIT) -> None:
        self.limit = limit
        self._entries: list[Entry] = []

    def push(self, entry: Entry) -> None:
        self._entries.append(entry)
        del self._entries[:-self.limit]

    def peek(self) -> Entry | None:
        return self._entries[-1] if self._entries else None

    def pop(self) -> Entry | None:
        return self._entries.pop() if self._entries else None

    def clear(self) -> None:
        self._entries.clear()

    def __len__(self) -> int:
        return len(self._entries)

    def __bool__(self) -> bool:
        return bool(self._entries)


#: The session's history.
UNDO = History()


__all__ = ["LIMIT", "UNDO", "Copied", "Entry", "History", "MadeDirectory", "Moved", "Renamed", "Trashed"]

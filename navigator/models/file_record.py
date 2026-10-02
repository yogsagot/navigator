"""What the File View History and File Edit History have in common.

DOS Navigator kept the two as ``TViewHistoryCol`` and ``TEditHistoryCol``
(``HISTRIES.PAS``): one record per file, newest first, the name's first
character a flag -- ``'+'`` pinned, ``' '`` not -- and at most
``MaxEditHistorySize`` (20) of them, the oldest unpinned going first
(``FreeLastUnmarked``).  This is that collection as a table: ``path`` is the
name without its flag, ``pinned`` the flag, and ``seq`` the order, larger
first.  The two models extend this class and declare the columns each record
had beside the name; the window rectangle every record carries is declared in
both, because a model's fields are its own document's.

**A file is its absolute path, case and all.**  DN upper-cased the name, which
on a POSIX file system would make two files one.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, TypeVar

from navkit.database import DATABASE, Model

#: ``MaxEditHistorySize``, which both collections were held to.
MAX_RECORDS = 20

R = TypeVar("R", bound="FileRecord")


def key_of(path: Path | str) -> str:
    """The name a file is recorded under: absolute, and nothing else changed."""
    return str(Path(path).absolute())


class FileRecord(Model):
    """A per-file history record: a path, a pin, an order, and the rest."""

    path: str
    pinned: bool
    seq: int

    @classmethod
    def ordered(cls: type[R]) -> list[R]:
        """Every record, newest first: the order the dialog lists them in."""
        return cls.query().order("-seq").all()

    @classmethod
    def find(cls: type[R], path: Path | str) -> R | None:
        return cls.get(path=key_of(path))

    @classmethod
    def store(cls, path: Path | str, **values: Any) -> None:
        """Put *path*'s record at the front with *values*, keeping its pin.

        ``StoreViewInfo``/``StoreEditInfo``: the old record goes, the new one
        is inserted first carrying the old one's flag, and past the limit the
        last unpinned record is freed.
        """
        with DATABASE.transaction():
            newest = cls.query().order("-seq").first()
            seq = 1 if newest is None else newest.seq + 1
            cls.upsert(path=key_of(path), seq=seq, **values)
            cls.where(pinned=False).order("-seq").offset(MAX_RECORDS).delete()

    @classmethod
    def toggle_pin(cls, path: str) -> None:
        """``TTHistList.SelectItem``: Space flips the ``'+'``."""
        record = cls.get(path=path)
        if record is not None:
            record.pinned = not record.pinned
            record.save()

    @classmethod
    def forget(cls, path: str) -> bool:
        """*Delete record*, which a pinned record refuses.  Whether it went."""
        return cls.where(path=path, pinned=False).delete() > 0

    @classmethod
    def swap(cls, first: str, second: str) -> None:
        """Shift+Up/Down: two records trade places in the list."""
        a, b = cls.get(path=first), cls.get(path=second)
        if a is None or b is None:
            return
        with DATABASE.transaction():
            a.seq, b.seq = b.seq, a.seq
            a.save()
            b.save()

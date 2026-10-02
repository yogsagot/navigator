"""What an input line remembers: Turbo Vision's ``HistList``, as DOS Navigator
changed it.

A store of string lists, one per *history id* -- ``"mkdir"``, ``"find"`` --
which a :class:`~navml.widgets.dialog.history.History` button names and every
input line sharing that id shares.  The rules are ``HISTLIST.PAS``'s:

* **Newest first**: an entry is inserted at the front.
* **No duplicates**: adding a string already there moves it to the front.
* **Twenty to a list** (``MaxHistorySize``), the oldest going first -- except
  **pinned** entries, which are never evicted.  That is DOS Navigator's
  addition: every string carried a trailing flag byte, ``' '`` or ``'+'``,
  and a string added again keeps the flag it had.
* **An empty string is never recorded.**

A module rather than a component, because a store paints nothing; it sits
beside :mod:`navml.commands` as the library's other support.  There is one
shared store, :data:`HISTORY`, as there was one ``HistoryBlock``, and a widget
may be handed another.

**The lists are kept in the database** -- the ``history`` table of
:class:`~navml.models.history_entry.HistoryEntry`, in
:data:`navkit.database.DATABASE` -- and each change is written as it is made.
That departs from DOS Navigator, which wrote ``DN.HIS`` once, on exit
(``SaveHistories``, ``DNUTIL.PAS``), so a crash lost the session's history;
here nothing is lost and two Navigators share one set of lists.  Until a
database file is opened it is ``:memory:``, which is what a test gets.
"""

from __future__ import annotations

from dataclasses import dataclass

from navml.models.history_entry import HistoryEntry

#: How many unpinned entries a list keeps: ``HistList.MaxHistorySize``.
MAX_ENTRIES = 20


@dataclass
class HistoryStore:
    """Every history list, by id."""

    #: How many unpinned entries each list keeps.
    limit: int = MAX_ENTRIES

    def entries(self, history_id: str) -> list[str]:
        """The list for *history_id*, newest first."""
        return HistoryEntry.texts(history_id)

    def add(self, history_id: str, text: str) -> None:
        """Remember *text* at the front of its list, as ``HistoryAdd`` does."""
        if not text:
            return
        HistoryEntry.remember(history_id, text, self.limit)

    def pin(self, history_id: str, text: str, pinned: bool = True) -> None:
        """Pin *text* against eviction, or release it.  Unknown text is ignored."""
        HistoryEntry.where(list_id=history_id, text=text).update(pinned=pinned)

    def is_pinned(self, history_id: str, text: str) -> bool:
        return HistoryEntry.where(
            list_id=history_id, text=text, pinned=True
        ).exists()

    def remove(self, history_id: str, text: str) -> None:
        """Forget *text*: ``DeleteHistoryStr``."""
        HistoryEntry.delete_where(list_id=history_id, text=text)

    def clear(self, history_id: str | None = None) -> None:
        """Forget one list, or every list: ``ClearHistory``."""
        if history_id is None:
            HistoryEntry.query().delete()
        else:
            HistoryEntry.delete_where(list_id=history_id)


#: The store every history button uses unless handed another.
HISTORY = HistoryStore()


__all__ = ["HISTORY", "MAX_ENTRIES", "HistoryStore"]

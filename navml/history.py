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
may be handed another.  It saves to and loads from plain data, so whoever owns
a configuration file decides where it lives.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

#: How many unpinned entries a list keeps: ``HistList.MaxHistorySize``.
MAX_ENTRIES = 20


@dataclass
class Entry:
    """One remembered string, and whether it is pinned against eviction."""

    text: str
    pinned: bool = False


@dataclass
class HistoryStore:
    """Every history list, by id."""

    #: How many unpinned entries each list keeps.
    limit: int = MAX_ENTRIES
    _lists: dict[str, list[Entry]] = field(default_factory=dict)

    def entries(self, history_id: str) -> list[str]:
        """The list for *history_id*, newest first."""
        return [entry.text for entry in self._lists.get(history_id, [])]

    def add(self, history_id: str, text: str) -> None:
        """Remember *text* at the front of its list, as ``HistoryAdd`` does."""
        if not text:
            return
        entries = self._lists.setdefault(history_id, [])
        pinned = False
        for entry in [e for e in entries if e.text == text]:
            pinned = pinned or entry.pinned
            entries.remove(entry)
        entries.insert(0, Entry(text, pinned))
        unpinned = [e for e in entries if not e.pinned]
        for entry in reversed(unpinned[self.limit:]):
            entries.remove(entry)

    def pin(self, history_id: str, text: str, pinned: bool = True) -> None:
        """Pin *text* against eviction, or release it.  Unknown text is ignored."""
        for entry in self._lists.get(history_id, []):
            if entry.text == text:
                entry.pinned = pinned

    def is_pinned(self, history_id: str, text: str) -> bool:
        return any(
            e.pinned for e in self._lists.get(history_id, []) if e.text == text
        )

    def remove(self, history_id: str, text: str) -> None:
        """Forget *text*: ``DeleteHistoryStr``."""
        entries = self._lists.get(history_id, [])
        entries[:] = [e for e in entries if e.text != text]

    def clear(self, history_id: str | None = None) -> None:
        """Forget one list, or every list: ``ClearHistory``."""
        if history_id is None:
            self._lists.clear()
        else:
            self._lists.pop(history_id, None)

    # -- keeping it --------------------------------------------------------------

    def to_data(self) -> dict[str, list[dict[str, Any]]]:
        """Every list as plain data, for whoever writes the configuration."""
        return {
            history_id: [{"text": e.text, "pinned": e.pinned} for e in entries]
            for history_id, entries in self._lists.items()
            if entries
        }

    def load_data(self, data: dict[str, list[Any]]) -> None:
        """Replace every list with *data*, as :meth:`to_data` wrote it.

        A bare string is taken as an unpinned entry, so a list written by hand
        need not spell the flag out.
        """
        self._lists = {
            history_id: [
                Entry(item, False) if isinstance(item, str)
                else Entry(str(item["text"]), bool(item.get("pinned", False)))
                for item in items
            ]
            for history_id, items in data.items()
        }


#: The store every history button uses unless handed another.
HISTORY = HistoryStore()


__all__ = ["HISTORY", "MAX_ENTRIES", "Entry", "HistoryStore"]

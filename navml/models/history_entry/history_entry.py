"""DOS Navigator's ``HistoryAdd`` rules, as statements over the history table."""

from __future__ import annotations

from navkit.database import DATABASE, Model


class HistoryEntry(Model):
    @classmethod
    def remember(cls, list_id: str, text: str, limit: int) -> None:
        """Put *text* at the front of *list_id*, keeping at most *limit* unpinned.

        One transaction: a repeat moves to the front and keeps its pin, and the
        oldest unpinned entries past *limit* go.
        """
        with DATABASE.transaction():
            newest = cls.where(list_id=list_id).order("-seq").first()
            seq = 1 if newest is None else newest.seq + 1
            cls.upsert(list_id=list_id, text=text, seq=seq)
            cls.where(list_id=list_id, pinned=False).order("-seq").offset(
                limit
            ).delete()

    @classmethod
    def texts(cls, list_id: str) -> list[str]:
        """The list, newest first."""
        return cls.where(list_id=list_id).order("-seq").values("text")

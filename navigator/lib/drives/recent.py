"""The connections the SSH link box has made, newest first
(:class:`~navigator.models.recent_link.RecentLink`).

A connection is a scheme, a host, a login, a port and a directory, and they
come back together: one row each, keyed by where it went -- the directory
is the last one opened there.  As long as Interface's *History size*, like
every list that remembers.
"""

from __future__ import annotations

from dataclasses import dataclass

from navkit.database import DATABASE

from navigator.models.recent_link import RecentLink


@dataclass(frozen=True)
class Recent:
    scheme: str
    host: str
    user: str = ""
    port: int = 0
    path: str = ""

    def text(self) -> str:
        """``user@host:port /path``, as the list shows it."""
        who = f"{self.user}@" if self.user else ""
        port = f":{self.port}" if self.port else ""
        return f"{who}{self.host}{port}" + (f"  {self.path}" if self.path else "")


def _limit() -> int:
    from navigator.settings import SETTINGS

    return max(1, SETTINGS.interface.history_size)


def recent(scheme: str | tuple[str, ...] | None = None) -> list[Recent]:
    """The connections made, newest first -- of *scheme* (or those schemes) alone, if given."""
    if isinstance(scheme, tuple):
        query = RecentLink.where(scheme__in=list(scheme))
    else:
        query = RecentLink.where(scheme=scheme) if scheme else RecentLink.where()
    rows = query.order("-seq").limit(_limit()).all()
    return [Recent(row.scheme, row.host, row.user, row.port, row.path) for row in rows]


def remember(link: Recent) -> None:
    """*link* first in the list, its directory the one given; the oldest past
    the list's length forgotten."""
    with DATABASE.transaction():
        newest = RecentLink.where().order("-seq").limit(1).all()
        seq = (newest[0].seq if newest else 0) + 1
        RecentLink.upsert(scheme=link.scheme, host=link.host, user=link.user, port=link.port,
                          path=link.path, seq=seq)
        for row in RecentLink.where().order("-seq").all()[_limit():]:
            row.delete()


def forget(link: Recent) -> None:
    RecentLink.where(scheme=link.scheme, host=link.host, user=link.user, port=link.port).delete()


__all__ = ["Recent", "forget", "recent", "remember"]

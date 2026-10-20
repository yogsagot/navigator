# navml: generated
"""The merged surface of ``navigator.models.recent_link.recent_link``."""

from typing import Any as _Any

from navkit.database import Query as _Query
from navkit.database import Model


class RecentLink(Model):
    id: int | None
    scheme: str
    host: str
    user: str
    port: int
    path: str
    seq: int
    def __init__(self, *, id: int | None = ..., scheme: str = ..., host: str = ..., user: str = ..., port: int = ..., path: str = ..., seq: int = ...) -> None: ...
    @classmethod
    def where(cls, **conditions: _Any) -> _Query[RecentLink]: ...
    @classmethod
    def query(cls) -> _Query[RecentLink]: ...
    @classmethod
    def all(cls) -> list[RecentLink]: ...
    @classmethod
    def get(cls, **conditions: _Any) -> RecentLink | None: ...
    @classmethod
    def count(cls, **conditions: _Any) -> int: ...
    @classmethod
    def delete_where(cls, **conditions: _Any) -> int: ...
    @classmethod
    def create(cls, *, scheme: str = ..., host: str = ..., user: str = ..., port: int = ..., path: str = ..., seq: int = ...) -> RecentLink: ...
    @classmethod
    def upsert(cls, *, scheme: str = ..., host: str = ..., user: str = ..., port: int = ..., path: str = ..., seq: int = ...) -> RecentLink: ...

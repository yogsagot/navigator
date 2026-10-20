# navml: generated
"""The merged surface of ``navigator.models.recent_char.recent_char``."""

from typing import Any as _Any

from navkit.database import Query as _Query
from navkit.database import Model


class RecentChar(Model):
    id: int | None
    code: int
    seq: int
    def __init__(self, *, id: int | None = ..., code: int = ..., seq: int = ...) -> None: ...
    @classmethod
    def where(cls, **conditions: _Any) -> _Query[RecentChar]: ...
    @classmethod
    def query(cls) -> _Query[RecentChar]: ...
    @classmethod
    def all(cls) -> list[RecentChar]: ...
    @classmethod
    def get(cls, **conditions: _Any) -> RecentChar | None: ...
    @classmethod
    def count(cls, **conditions: _Any) -> int: ...
    @classmethod
    def delete_where(cls, **conditions: _Any) -> int: ...
    @classmethod
    def create(cls, *, code: int = ..., seq: int = ...) -> RecentChar: ...
    @classmethod
    def upsert(cls, *, code: int = ..., seq: int = ...) -> RecentChar: ...

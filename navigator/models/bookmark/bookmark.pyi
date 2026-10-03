# navml: generated
"""The merged surface of ``navigator.models.bookmark.bookmark``."""

from typing import Any as _Any

from navkit.database import Query as _Query
from navkit.database import Model


class Bookmark(Model):
    id: int | None
    path: str
    seq: int
    label: str
    def __init__(self, *, id: int | None = ..., path: str = ..., seq: int = ..., label: str = ...) -> None: ...
    @classmethod
    def where(cls, **conditions: _Any) -> _Query[Bookmark]: ...
    @classmethod
    def query(cls) -> _Query[Bookmark]: ...
    @classmethod
    def all(cls) -> list[Bookmark]: ...
    @classmethod
    def get(cls, **conditions: _Any) -> Bookmark | None: ...
    @classmethod
    def count(cls, **conditions: _Any) -> int: ...
    @classmethod
    def delete_where(cls, **conditions: _Any) -> int: ...
    @classmethod
    def create(cls, *, path: str = ..., seq: int = ..., label: str = ...) -> Bookmark: ...
    @classmethod
    def upsert(cls, *, path: str = ..., seq: int = ..., label: str = ...) -> Bookmark: ...

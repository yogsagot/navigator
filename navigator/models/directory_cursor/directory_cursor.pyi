# navml: generated
"""The merged surface of ``navigator.models.directory_cursor.directory_cursor``."""

from typing import Any as _Any

from navkit.database import Query as _Query
from navkit.database import Model


class DirectoryCursor(Model):
    id: int | None
    path: str
    name: str
    used: float
    def __init__(self, *, id: int | None = ..., path: str = ..., name: str = ..., used: float = ...) -> None: ...
    @classmethod
    def where(cls, **conditions: _Any) -> _Query[DirectoryCursor]: ...
    @classmethod
    def query(cls) -> _Query[DirectoryCursor]: ...
    @classmethod
    def all(cls) -> list[DirectoryCursor]: ...
    @classmethod
    def get(cls, **conditions: _Any) -> DirectoryCursor | None: ...
    @classmethod
    def count(cls, **conditions: _Any) -> int: ...
    @classmethod
    def delete_where(cls, **conditions: _Any) -> int: ...
    @classmethod
    def create(cls, *, path: str = ..., name: str = ..., used: float = ...) -> DirectoryCursor: ...
    @classmethod
    def upsert(cls, *, path: str = ..., name: str = ..., used: float = ...) -> DirectoryCursor: ...

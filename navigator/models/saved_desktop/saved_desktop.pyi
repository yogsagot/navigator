# navml: generated
"""The merged surface of ``navigator.models.saved_desktop.saved_desktop``."""

from typing import Any as _Any

from navkit.database import Query as _Query
from navkit.database import Model


class SavedDesktop(Model):
    id: int | None
    name: str
    data: str
    def __init__(self, *, id: int | None = ..., name: str = ..., data: str = ...) -> None: ...
    @classmethod
    def where(cls, **conditions: _Any) -> _Query[SavedDesktop]: ...
    @classmethod
    def query(cls) -> _Query[SavedDesktop]: ...
    @classmethod
    def all(cls) -> list[SavedDesktop]: ...
    @classmethod
    def get(cls, **conditions: _Any) -> SavedDesktop | None: ...
    @classmethod
    def count(cls, **conditions: _Any) -> int: ...
    @classmethod
    def delete_where(cls, **conditions: _Any) -> int: ...
    @classmethod
    def create(cls, *, name: str = ..., data: str = ...) -> SavedDesktop: ...
    @classmethod
    def upsert(cls, *, name: str = ..., data: str = ...) -> SavedDesktop: ...

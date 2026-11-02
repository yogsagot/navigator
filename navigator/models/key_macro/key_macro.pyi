# navml: generated
"""The merged surface of ``navigator.models.key_macro.key_macro``."""

from typing import Any as _Any

from navkit.database import Query as _Query
from navkit.database import Model


class KeyMacro(Model):
    id: int | None
    slot: int
    keys: str
    def __init__(self, *, id: int | None = ..., slot: int = ..., keys: str = ...) -> None: ...
    @classmethod
    def where(cls, **conditions: _Any) -> _Query[KeyMacro]: ...
    @classmethod
    def query(cls) -> _Query[KeyMacro]: ...
    @classmethod
    def all(cls) -> list[KeyMacro]: ...
    @classmethod
    def get(cls, **conditions: _Any) -> KeyMacro | None: ...
    @classmethod
    def count(cls, **conditions: _Any) -> int: ...
    @classmethod
    def delete_where(cls, **conditions: _Any) -> int: ...
    @classmethod
    def create(cls, *, slot: int = ..., keys: str = ...) -> KeyMacro: ...
    @classmethod
    def upsert(cls, *, slot: int = ..., keys: str = ...) -> KeyMacro: ...

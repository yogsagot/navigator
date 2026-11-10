# navml: generated
"""The merged surface of ``navigator.models.window_bounds.window_bounds``."""

from typing import Any as _Any

from navkit.database import Query as _Query
from navkit.database import Model


class WindowBounds(Model):
    id: int | None
    kind: str
    zoomed: bool
    x: int
    y: int
    width: int
    height: int
    desk_width: int
    desk_height: int
    def __init__(self, *, id: int | None = ..., kind: str = ..., zoomed: bool = ..., x: int = ..., y: int = ..., width: int = ..., height: int = ..., desk_width: int = ..., desk_height: int = ...) -> None: ...
    @classmethod
    def where(cls, **conditions: _Any) -> _Query[WindowBounds]: ...
    @classmethod
    def query(cls) -> _Query[WindowBounds]: ...
    @classmethod
    def all(cls) -> list[WindowBounds]: ...
    @classmethod
    def get(cls, **conditions: _Any) -> WindowBounds | None: ...
    @classmethod
    def count(cls, **conditions: _Any) -> int: ...
    @classmethod
    def delete_where(cls, **conditions: _Any) -> int: ...
    @classmethod
    def create(cls, *, kind: str = ..., zoomed: bool = ..., x: int = ..., y: int = ..., width: int = ..., height: int = ..., desk_width: int = ..., desk_height: int = ...) -> WindowBounds: ...
    @classmethod
    def upsert(cls, *, kind: str = ..., zoomed: bool = ..., x: int = ..., y: int = ..., width: int = ..., height: int = ..., desk_width: int = ..., desk_height: int = ...) -> WindowBounds: ...

# navml: generated
"""The merged surface of ``navigator.models.view_record.view_record``."""

from typing import Any as _Any

from navkit.database import Query as _Query
from navigator.models.file_record import FileRecord


class ViewRecord(FileRecord):
    id: int | None
    path: str
    pinned: bool
    seq: int
    zoomed: bool
    x: int
    y: int
    width: int
    height: int
    desk_width: int
    desk_height: int
    mode: str
    wrap: bool
    filter: int
    highlight: bool
    top: int
    x_delta: int
    cursor: int
    def __init__(self, *, id: int | None = ..., path: str = ..., pinned: bool = ..., seq: int = ..., zoomed: bool = ..., x: int = ..., y: int = ..., width: int = ..., height: int = ..., desk_width: int = ..., desk_height: int = ..., mode: str = ..., wrap: bool = ..., filter: int = ..., highlight: bool = ..., top: int = ..., x_delta: int = ..., cursor: int = ...) -> None: ...
    @classmethod
    def where(cls, **conditions: _Any) -> _Query[ViewRecord]: ...
    @classmethod
    def query(cls) -> _Query[ViewRecord]: ...
    @classmethod
    def all(cls) -> list[ViewRecord]: ...
    @classmethod
    def get(cls, **conditions: _Any) -> ViewRecord | None: ...
    @classmethod
    def count(cls, **conditions: _Any) -> int: ...
    @classmethod
    def delete_where(cls, **conditions: _Any) -> int: ...
    @classmethod
    def create(cls, *, path: str = ..., pinned: bool = ..., seq: int = ..., zoomed: bool = ..., x: int = ..., y: int = ..., width: int = ..., height: int = ..., desk_width: int = ..., desk_height: int = ..., mode: str = ..., wrap: bool = ..., filter: int = ..., highlight: bool = ..., top: int = ..., x_delta: int = ..., cursor: int = ...) -> ViewRecord: ...
    @classmethod
    def upsert(cls, *, path: str = ..., pinned: bool = ..., seq: int = ..., zoomed: bool = ..., x: int = ..., y: int = ..., width: int = ..., height: int = ..., desk_width: int = ..., desk_height: int = ..., mode: str = ..., wrap: bool = ..., filter: int = ..., highlight: bool = ..., top: int = ..., x_delta: int = ..., cursor: int = ...) -> ViewRecord: ...

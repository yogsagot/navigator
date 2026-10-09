# navml: generated
"""The merged surface of ``navigator.models.edit_record.edit_record``."""

from typing import Any as _Any

from navkit.database import Query as _Query
from navigator.models.file_record import FileRecord


class EditRecord(FileRecord):
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
    line: int
    col: int
    top: int
    left: int
    overwrite: bool
    vertical_blocks: bool
    highlight: bool
    file_type: str
    marks: str
    def __init__(self, *, id: int | None = ..., path: str = ..., pinned: bool = ..., seq: int = ..., zoomed: bool = ..., x: int = ..., y: int = ..., width: int = ..., height: int = ..., desk_width: int = ..., desk_height: int = ..., line: int = ..., col: int = ..., top: int = ..., left: int = ..., overwrite: bool = ..., vertical_blocks: bool = ..., highlight: bool = ..., file_type: str = ..., marks: str = ...) -> None: ...
    @classmethod
    def where(cls, **conditions: _Any) -> _Query[EditRecord]: ...
    @classmethod
    def query(cls) -> _Query[EditRecord]: ...
    @classmethod
    def all(cls) -> list[EditRecord]: ...
    @classmethod
    def get(cls, **conditions: _Any) -> EditRecord | None: ...
    @classmethod
    def count(cls, **conditions: _Any) -> int: ...
    @classmethod
    def delete_where(cls, **conditions: _Any) -> int: ...
    @classmethod
    def create(cls, *, path: str = ..., pinned: bool = ..., seq: int = ..., zoomed: bool = ..., x: int = ..., y: int = ..., width: int = ..., height: int = ..., desk_width: int = ..., desk_height: int = ..., line: int = ..., col: int = ..., top: int = ..., left: int = ..., overwrite: bool = ..., vertical_blocks: bool = ..., highlight: bool = ..., file_type: str = ..., marks: str = ...) -> EditRecord: ...
    @classmethod
    def upsert(cls, *, path: str = ..., pinned: bool = ..., seq: int = ..., zoomed: bool = ..., x: int = ..., y: int = ..., width: int = ..., height: int = ..., desk_width: int = ..., desk_height: int = ..., line: int = ..., col: int = ..., top: int = ..., left: int = ..., overwrite: bool = ..., vertical_blocks: bool = ..., highlight: bool = ..., file_type: str = ..., marks: str = ...) -> EditRecord: ...

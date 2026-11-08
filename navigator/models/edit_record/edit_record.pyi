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
    used: float
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
    block: str
    block_hidden: bool
    highlight_line: bool | None
    highlight_column: bool | None
    auto_indent: bool | None
    justify_on_wrap: bool | None
    auto_brackets: bool | None
    left_margin: int | None
    right_margin: int | None
    paragraph: int | None
    insert_tabs: bool | None
    line_numbers: bool | None
    soft_wrap: bool | None
    def __init__(self, *, id: int | None = ..., path: str = ..., pinned: bool = ..., seq: int = ..., used: float = ..., zoomed: bool = ..., x: int = ..., y: int = ..., width: int = ..., height: int = ..., desk_width: int = ..., desk_height: int = ..., line: int = ..., col: int = ..., top: int = ..., left: int = ..., overwrite: bool = ..., vertical_blocks: bool = ..., highlight: bool = ..., file_type: str = ..., marks: str = ..., block: str = ..., block_hidden: bool = ..., highlight_line: bool | None = ..., highlight_column: bool | None = ..., auto_indent: bool | None = ..., justify_on_wrap: bool | None = ..., auto_brackets: bool | None = ..., left_margin: int | None = ..., right_margin: int | None = ..., paragraph: int | None = ..., insert_tabs: bool | None = ..., line_numbers: bool | None = ..., soft_wrap: bool | None = ...) -> None: ...
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
    def create(cls, *, path: str = ..., pinned: bool = ..., seq: int = ..., used: float = ..., zoomed: bool = ..., x: int = ..., y: int = ..., width: int = ..., height: int = ..., desk_width: int = ..., desk_height: int = ..., line: int = ..., col: int = ..., top: int = ..., left: int = ..., overwrite: bool = ..., vertical_blocks: bool = ..., highlight: bool = ..., file_type: str = ..., marks: str = ..., block: str = ..., block_hidden: bool = ..., highlight_line: bool | None = ..., highlight_column: bool | None = ..., auto_indent: bool | None = ..., justify_on_wrap: bool | None = ..., auto_brackets: bool | None = ..., left_margin: int | None = ..., right_margin: int | None = ..., paragraph: int | None = ..., insert_tabs: bool | None = ..., line_numbers: bool | None = ..., soft_wrap: bool | None = ...) -> EditRecord: ...
    @classmethod
    def upsert(cls, *, path: str = ..., pinned: bool = ..., seq: int = ..., used: float = ..., zoomed: bool = ..., x: int = ..., y: int = ..., width: int = ..., height: int = ..., desk_width: int = ..., desk_height: int = ..., line: int = ..., col: int = ..., top: int = ..., left: int = ..., overwrite: bool = ..., vertical_blocks: bool = ..., highlight: bool = ..., file_type: str = ..., marks: str = ..., block: str = ..., block_hidden: bool = ..., highlight_line: bool | None = ..., highlight_column: bool | None = ..., auto_indent: bool | None = ..., justify_on_wrap: bool | None = ..., auto_brackets: bool | None = ..., left_margin: int | None = ..., right_margin: int | None = ..., paragraph: int | None = ..., insert_tabs: bool | None = ..., line_numbers: bool | None = ..., soft_wrap: bool | None = ...) -> EditRecord: ...

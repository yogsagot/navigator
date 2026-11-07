# navml: generated
"""The merged surface of ``navigator.models.directory_settings.directory_settings``."""

from typing import Any as _Any

from navkit.database import Query as _Query
from navkit.database import Model


class DirectorySettings(Model):
    id: int | None
    path: str
    subdirs: bool
    view_mode: str
    sort_mode: str
    sort_reverse: bool
    file_mask: str
    show_hidden: bool
    columns: str
    display: str
    def __init__(self, *, id: int | None = ..., path: str = ..., subdirs: bool = ..., view_mode: str = ..., sort_mode: str = ..., sort_reverse: bool = ..., file_mask: str = ..., show_hidden: bool = ..., columns: str = ..., display: str = ...) -> None: ...
    @classmethod
    def where(cls, **conditions: _Any) -> _Query[DirectorySettings]: ...
    @classmethod
    def query(cls) -> _Query[DirectorySettings]: ...
    @classmethod
    def all(cls) -> list[DirectorySettings]: ...
    @classmethod
    def get(cls, **conditions: _Any) -> DirectorySettings | None: ...
    @classmethod
    def count(cls, **conditions: _Any) -> int: ...
    @classmethod
    def delete_where(cls, **conditions: _Any) -> int: ...
    @classmethod
    def create(cls, *, path: str = ..., subdirs: bool = ..., view_mode: str = ..., sort_mode: str = ..., sort_reverse: bool = ..., file_mask: str = ..., show_hidden: bool = ..., columns: str = ..., display: str = ...) -> DirectorySettings: ...
    @classmethod
    def upsert(cls, *, path: str = ..., subdirs: bool = ..., view_mode: str = ..., sort_mode: str = ..., sort_reverse: bool = ..., file_mask: str = ..., show_hidden: bool = ..., columns: str = ..., display: str = ...) -> DirectorySettings: ...

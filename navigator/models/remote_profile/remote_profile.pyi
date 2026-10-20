# navml: generated
"""The merged surface of ``navigator.models.remote_profile.remote_profile``."""

from typing import Any as _Any

from navkit.database import Query as _Query
from navkit.database import Model


class RemoteProfile(Model):
    id: int | None
    name: str
    scheme: str
    host: str
    port: int
    user: str
    path: str
    seq: int
    def __init__(self, *, id: int | None = ..., name: str = ..., scheme: str = ..., host: str = ..., port: int = ..., user: str = ..., path: str = ..., seq: int = ...) -> None: ...
    @classmethod
    def where(cls, **conditions: _Any) -> _Query[RemoteProfile]: ...
    @classmethod
    def query(cls) -> _Query[RemoteProfile]: ...
    @classmethod
    def all(cls) -> list[RemoteProfile]: ...
    @classmethod
    def get(cls, **conditions: _Any) -> RemoteProfile | None: ...
    @classmethod
    def count(cls, **conditions: _Any) -> int: ...
    @classmethod
    def delete_where(cls, **conditions: _Any) -> int: ...
    @classmethod
    def create(cls, *, name: str = ..., scheme: str = ..., host: str = ..., port: int = ..., user: str = ..., path: str = ..., seq: int = ...) -> RemoteProfile: ...
    @classmethod
    def upsert(cls, *, name: str = ..., scheme: str = ..., host: str = ..., port: int = ..., user: str = ..., path: str = ..., seq: int = ...) -> RemoteProfile: ...

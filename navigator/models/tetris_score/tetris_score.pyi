# navml: generated
"""The merged surface of ``navigator.models.tetris_score.tetris_score``."""

from typing import Any as _Any

from navkit.database import Query as _Query
from navkit.database import Model


class TetrisScore(Model):
    id: int | None
    style: str
    name: str
    start: int
    end: int
    score: int
    seq: int
    def __init__(self, *, id: int | None = ..., style: str = ..., name: str = ..., start: int = ..., end: int = ..., score: int = ..., seq: int = ...) -> None: ...
    @classmethod
    def where(cls, **conditions: _Any) -> _Query[TetrisScore]: ...
    @classmethod
    def query(cls) -> _Query[TetrisScore]: ...
    @classmethod
    def all(cls) -> list[TetrisScore]: ...
    @classmethod
    def get(cls, **conditions: _Any) -> TetrisScore | None: ...
    @classmethod
    def count(cls, **conditions: _Any) -> int: ...
    @classmethod
    def delete_where(cls, **conditions: _Any) -> int: ...
    @classmethod
    def create(cls, *, style: str = ..., name: str = ..., start: int = ..., end: int = ..., score: int = ..., seq: int = ...) -> TetrisScore: ...
    @classmethod
    def upsert(cls, *, style: str = ..., name: str = ..., start: int = ..., end: int = ..., score: int = ..., seq: int = ...) -> TetrisScore: ...

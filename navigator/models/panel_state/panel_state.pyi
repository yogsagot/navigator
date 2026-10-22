# navml: generated
"""The merged surface of ``navigator.models.panel_state.panel_state``."""

from typing import Any as _Any

from navkit.database import Query as _Query
from navkit.database import Model


class PanelState(Model):
    id: int | None
    side: str
    show_hidden: bool
    show_info: bool
    def __init__(self, *, id: int | None = ..., side: str = ..., show_hidden: bool = ..., show_info: bool = ...) -> None: ...
    @classmethod
    def where(cls, **conditions: _Any) -> _Query[PanelState]: ...
    @classmethod
    def query(cls) -> _Query[PanelState]: ...
    @classmethod
    def all(cls) -> list[PanelState]: ...
    @classmethod
    def get(cls, **conditions: _Any) -> PanelState | None: ...
    @classmethod
    def count(cls, **conditions: _Any) -> int: ...
    @classmethod
    def delete_where(cls, **conditions: _Any) -> int: ...
    @classmethod
    def create(cls, *, side: str = ..., show_hidden: bool = ..., show_info: bool = ...) -> PanelState: ...
    @classmethod
    def upsert(cls, *, side: str = ..., show_hidden: bool = ..., show_info: bool = ...) -> PanelState: ...

# navml: generated
"""The merged surface of ``navml.widgets.label``.

``label`` is a markup-only component, so there is no ``label.py`` at all and
this stub is the only thing a type checker can see for the module name.
"""

from typing import Any as _Any

from navkit.screen import Surface
from navkit.widget import Widget as _Widget

__all__: list[str]

class Label(_Widget):
    text: str
    align: str
    def __init__(self, **kwargs: _Any) -> None: ...
    def layout(self, width: int, height: int) -> None: ...
    def render(self, surface: Surface) -> None: ...

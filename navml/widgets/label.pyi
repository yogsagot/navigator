# navml: generated
"""The merged surface of ``navml.widgets.label``.

``label`` is a markup-only component, so there is no ``label.py`` at all and
this stub is the only thing a type checker can see for the module name.
"""

from typing import Any as _Any

from navkit.screen import Surface

from navml.component import Component as _Component

__all__: list[str]

class Label(_Component):
    text: str
    align: str
    def __init__(self, **kwargs: _Any) -> None: ...
    def render(self, surface: Surface) -> None: ...

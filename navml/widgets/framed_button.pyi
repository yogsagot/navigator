# navml: generated
"""The merged surface of ``navml.widgets.framed_button``."""

from typing import Any

from navkit.screen import Surface

from navml.widgets.button import Button
from navml.widgets.label import Label

class FramedButton(Button):
    hint_text: str
    hint: Label
    def __init__(self, **kwargs: Any) -> None: ...
    def layout(self, width: int, height: int) -> None: ...
    def render(self, surface: Surface) -> None: ...

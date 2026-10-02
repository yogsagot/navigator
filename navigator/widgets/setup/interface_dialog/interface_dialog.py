"""What OK means in *Interface Setup*: the ``[interface]`` section's new values."""

from __future__ import annotations

from typing import Any

from navml.widgets.dialog.dialog import Dialog

from navigator.settings import SETTINGS, InterfaceData


class InterfaceDialog(Dialog):
    """The screen's furniture: DN's ``TInterfaceData.Options``, one box a bit."""

    def __init__(self, section: InterfaceData | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.section = section or SETTINGS.interface
        self.options.value = self.section.to_bits(InterfaceData.OPTIONS)

    def accept(self) -> dict[str, Any]:
        return InterfaceData.from_bits(InterfaceData.OPTIONS, self.options.value)

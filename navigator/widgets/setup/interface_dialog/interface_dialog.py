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
        self.history_size.value = f"{self.section.history_size:03d}"

    def accept(self) -> dict[str, Any]:
        values = InterfaceData.from_bits(InterfaceData.OPTIONS, self.options.value)
        # A blank place counts as nought; a list kept to nothing keeps one.
        text = self.history_size.value.replace(" ", "0")
        values["history_size"] = max(1, int(text)) if text.isdigit() else self.section.history_size
        return values

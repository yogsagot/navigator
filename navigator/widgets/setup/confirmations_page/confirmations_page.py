"""What OK means in *Confirmations*: the ``[confirmations]`` section's new values."""

from __future__ import annotations

from typing import Any


from navkit.widget import Widget

from navigator.settings import SETTINGS, ConfirmsData


class ConfirmationsPage(Widget):
    """Which operations ask first: DN's ``Confirms`` word, one box a bit."""

    def __init__(self, section: ConfirmsData | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.section = section or SETTINGS.confirmations
        self.options.value = self.section.to_bits(ConfirmsData.OPTIONS)
        self.options.tooltips = ConfirmsData.tooltips(ConfirmsData.OPTIONS)

    def accept(self) -> dict[str, Any]:
        return ConfirmsData.from_bits(ConfirmsData.OPTIONS, self.options.value)

"""What OK means in *Startup*: the ``[startup]`` section's new values."""

from __future__ import annotations

from typing import Any

from navml.widgets.dialog.dialog import Dialog

from navigator.settings import SETTINGS, StartupData


class StartupDialog(Dialog):
    """DN's ``TStartupData``: its Load, Unload and Slice words, a cluster each."""

    def __init__(self, section: StartupData | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.section = section or SETTINGS.startup
        self.startup.value = self.section.to_bits(StartupData.STARTUP)
        self.shutdown.value = self.section.to_bits(StartupData.SHUTDOWN)
        self.timeslicing.value = self.section.to_bits(StartupData.TIMESLICING)

    def accept(self) -> dict[str, Any]:
        return {
            **StartupData.from_bits(StartupData.STARTUP, self.startup.value),
            **StartupData.from_bits(StartupData.SHUTDOWN, self.shutdown.value),
            **StartupData.from_bits(StartupData.TIMESLICING, self.timeslicing.value),
        }

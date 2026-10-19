"""What OK means in *Information Panel Setup*: the ``[drive_info]`` section's new values."""

from __future__ import annotations

from typing import Any


from navkit.widget import Widget

from navigator.settings import SETTINGS, DriveInfoData


class DriveInfoPage(Widget):
    """What Ctrl+L's panel shows: DN's ``DriveInfoData`` word, one box a bit."""

    def __init__(self, section: DriveInfoData | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.section = section or SETTINGS.drive_info
        self.options.value = self.section.to_bits(DriveInfoData.OPTIONS)

    def accept(self) -> dict[str, Any]:
        return DriveInfoData.from_bits(DriveInfoData.OPTIONS, self.options.value)

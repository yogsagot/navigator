"""What OK means in *File Manager Setup*: the ``[file_manager]`` section's new values."""

from __future__ import annotations

from typing import Any

from navml.widgets.dialog.dialog import Dialog

from navigator.settings import SETTINGS, FMSetupData


class FMSetupDialog(Dialog):
    """DN's ``TFMSetup``: Options, Show, Quick, TagChar and DIZ."""

    def __init__(self, section: FMSetupData | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.section = section or SETTINGS.file_manager
        self.behavior.value = self.section.to_bits(FMSetupData.BEHAVIOR)
        self.display.value = self.section.to_bits(FMSetupData.DISPLAY)
        self.quick_search.value = FMSetupData.QUICK_SEARCH.index(self.section.quick_search)
        self.tag_sign.value = self.section.tag_sign
        self.description_files.value = self.section.description_files

    def accept(self) -> dict[str, Any]:
        return {
            **FMSetupData.from_bits(FMSetupData.BEHAVIOR, self.behavior.value),
            **FMSetupData.from_bits(FMSetupData.DISPLAY, self.display.value),
            "quick_search": FMSetupData.QUICK_SEARCH[self.quick_search.value],
            # DN's line held one character; an empty one keeps the old sign.
            "tag_sign": self.tag_sign.value.strip()[:1] or self.section.tag_sign,
            "description_files": self.description_files.value.strip(),
        }

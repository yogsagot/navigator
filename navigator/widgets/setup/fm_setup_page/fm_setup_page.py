"""What OK means in *File Manager Setup*: the ``[file_manager]`` section's new values."""

from __future__ import annotations

from typing import Any


from navkit.widget import Widget

from navigator.settings import SETTINGS, FMSetupData

#: *Right button*'s choices, in the order the radio buttons list them.
RIGHT_BUTTON = ("menu", "select")


class FMSetupPage(Widget):
    """DN's ``TFMSetup``: Options, Show and TagChar, and the right button."""

    def __init__(self, section: FMSetupData | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.section = section or SETTINGS.file_manager
        self.behavior.value = self.section.to_bits(FMSetupData.BEHAVIOR)
        self.display.value = self.section.to_bits(FMSetupData.DISPLAY)
        self.tag_sign.value = self.section.tag_sign
        self.right_button.value = RIGHT_BUTTON.index(self.section.right_button)

    def accept(self) -> dict[str, Any]:
        return {
            **FMSetupData.from_bits(FMSetupData.BEHAVIOR, self.behavior.value),
            **FMSetupData.from_bits(FMSetupData.DISPLAY, self.display.value),
            # DN's line held one character; an empty one keeps the old sign.
            "tag_sign": self.tag_sign.value.strip()[:1] or self.section.tag_sign,
            "right_button": RIGHT_BUTTON[self.right_button.value],
        }

"""What OK means in *File Manager Setup*: the ``[file_manager]`` section's new
values.  Its check boxes and radio buttons say what they edit (``key:``);
the tag character and the Miller column width are read here."""

from __future__ import annotations

from typing import Any

from navigator.widgets.setup.settings_page import SettingsPage

#: The narrowest *Miller column width* takes: ``miller_view.MIN_WIDTH``.
MIN_WIDTH = 12


class FMSetupPage(SettingsPage):
    """DN's ``TFMSetup``: Options, Show and TagChar, and the right button."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.tag_sign.value = self.section.tag_sign
        self.tag_sign.tooltip = self.section.tooltip("tag_sign")
        self.miller_width.value = str(self.section.miller_width)
        self.miller_width.tooltip = self.section.tooltip("miller_width")

    def accept(self) -> dict[str, Any]:
        return {
            **super().accept(),
            # One character, or the one it had.
            "tag_sign": self.tag_sign.value.strip()[:1] or self.section.tag_sign,
            "miller_width": self._miller_width(),
        }

    def _miller_width(self) -> int:
        try:
            return max(MIN_WIDTH, int(self.miller_width.value.strip()))
        except ValueError:
            return self.section.miller_width

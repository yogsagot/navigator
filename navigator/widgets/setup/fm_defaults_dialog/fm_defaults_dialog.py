"""What OK means in *Panel Defaults*: the ``[panel_defaults]`` section's new values."""

from __future__ import annotations

from typing import Any

from navml.widgets.dialog.dialog import Dialog

from navigator.settings import SETTINGS, PanelDefaultsData


class FMDefaultsDialog(Dialog):
    """DN's ``TPanelDefaultsData``: Sort, Show and LeftPanel."""

    def __init__(self, section: PanelDefaultsData | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.section = section or SETTINGS.panel_defaults
        self.sort_by.value = PanelDefaultsData.SORT_BY.index(self.section.sort_by)
        self.display.value = self.section.to_bits(PanelDefaultsData.DISPLAY)
        self.left_panel.value = PanelDefaultsData.LEFT_PANEL.index(self.section.left_panel)

    def accept(self) -> dict[str, Any]:
        return {
            "sort_by": PanelDefaultsData.SORT_BY[self.sort_by.value],
            **PanelDefaultsData.from_bits(PanelDefaultsData.DISPLAY, self.display.value),
            "left_panel": PanelDefaultsData.LEFT_PANEL[self.left_panel.value],
        }

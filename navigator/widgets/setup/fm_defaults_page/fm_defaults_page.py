"""What OK means in *Panel Defaults*: the ``[panel_defaults]`` section's new values."""

from __future__ import annotations

from typing import Any

from navkit.reactive import bind
from navkit.widget import Widget

from navigator.settings import SETTINGS, PanelDefaultsData
from navigator.widgets.manager.manager.manager import sort_radio_captions


class FMDefaultsPage(Widget):
    """DN's ``TPanelDefaultsData``: Sort, Show and LeftPanel, and the panel mode."""

    def __init__(self, section: PanelDefaultsData | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.section = section or SETTINGS.panel_defaults
        # Each order's caption ends in the way it runs, following the box.
        self.sort_by.items = bind(lambda _o: sort_radio_captions(bool(self.reverse.value), self.glyphs))
        self.sort_by.value = PanelDefaultsData.SORT_BY.index(self.section.sort_by)
        self.reverse.value = 1 if self.section.sort_reverse else 0
        self.display.value = self.section.to_bits(PanelDefaultsData.DISPLAY)
        self.left_panel.value = PanelDefaultsData.LEFT_PANEL.index(self.section.left_panel)
        self.view_mode.value = PanelDefaultsData.VIEW_MODE.index(self.section.view_mode)

    def accept(self) -> dict[str, Any]:
        return {
            "sort_by": PanelDefaultsData.SORT_BY[self.sort_by.value],
            "sort_reverse": bool(self.reverse.value),
            **PanelDefaultsData.from_bits(PanelDefaultsData.DISPLAY, self.display.value),
            "left_panel": PanelDefaultsData.LEFT_PANEL[self.left_panel.value],
            "view_mode": PanelDefaultsData.VIEW_MODE[self.view_mode.value],
        }

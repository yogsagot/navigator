"""What OK means in *Panel Options*: one panel's order, boxes and file mask."""

from __future__ import annotations

from typing import Any

from navml.widgets.dialog.dialog import Dialog

from navigator.settings import PanelDefaultsData


class PanelSetupDialog(Dialog):
    """DN's ``Setup``'s record: ``Sort``, ``Show`` and ``S``, for one panel."""

    def __init__(self, panel: Any = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        if panel is not None:
            self.sort_by.value = PanelDefaultsData.SORT_BY.index(panel.sort_mode)
            self.display.value = sum(
                1 << index for index, name in enumerate(PanelDefaultsData.DISPLAY) if panel.shows(name)
            )
            self.mask.value = panel.file_mask

    def accept(self) -> tuple[str, frozenset[str], str]:
        """``(sort, display, mask)``, as :meth:`Panel.set_options` takes them."""
        shown = frozenset(
            name for index, name in enumerate(PanelDefaultsData.DISPLAY)
            if self.display.value & (1 << index)
        )
        return PanelDefaultsData.SORT_BY[self.sort_by.value], shown, self.mask.value

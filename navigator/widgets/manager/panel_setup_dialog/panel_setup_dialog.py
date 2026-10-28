"""What OK means in *Panel Options*: one panel's order, boxes and file mask."""

from __future__ import annotations

from typing import Any

from navkit.reactive import bind
from navml.widgets.dialog.dialog import Dialog

from navigator.settings import PanelDefaultsData
from navigator.widgets.manager.manager.manager import sort_radio_captions


class PanelSetupDialog(Dialog):
    """DN's ``Setup``'s record: ``Sort``, ``Show`` and ``S``, for one panel,
    and the direction of its order."""

    def __init__(self, panel: Any = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        # The same eight boxes as *New Manager defaults*, for one panel: the
        # settings' docs say what each shows.
        self.display.tooltips = PanelDefaultsData.tooltips(PanelDefaultsData.DISPLAY)
        if panel is not None:
            # Each order's caption ends in the way it runs, following the box.
            self.sort_by.items = bind(lambda _o: sort_radio_captions(bool(self.reverse.value), panel.glyphs))
            self.sort_by.value = PanelDefaultsData.SORT_BY.index(panel.sort_mode)
            self.reverse.value = 1 if panel.sort_reverse else 0
            self.display.value = sum(
                1 << index for index, name in enumerate(PanelDefaultsData.DISPLAY) if panel.shows(name)
            )
            self.mask.value = panel.file_mask

    def accept(self) -> tuple[str, frozenset[str], str, bool]:
        """``(sort, display, mask, reverse)``, as :meth:`Panel.set_options` takes them."""
        shown = frozenset(
            name for index, name in enumerate(PanelDefaultsData.DISPLAY)
            if self.display.value & (1 << index)
        )
        return (PanelDefaultsData.SORT_BY[self.sort_by.value], shown, self.mask.value,
                bool(self.reverse.value))

"""What OK means in *Highlight groups*: the ``[highlight_groups]`` section's new masks."""

from __future__ import annotations

from typing import Any

from navml.widgets.dialog.dialog import Dialog

from navigator.filetypes import CUSTOM
from navigator.settings import SETTINGS, HighlightGroupsData


def tidy(mask: str) -> str:
    """*mask* as ``SetHighlightGroups`` kept it: blanks dropped (``DelSpaces``),
    and no empty pattern between, before or after the ``;``-separated ones."""
    return ";".join(pattern for pattern in mask.replace(" ", "").split(";") if pattern)


class HighlightDialog(Dialog):
    """Which files each colour group takes: DN's ``CustomMask1``..``5``, one line a mask."""

    def __init__(self, section: HighlightGroupsData | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.section = section or SETTINGS.highlight_groups
        for key in CUSTOM:
            getattr(self, key).value = getattr(self.section, key)

    def accept(self) -> dict[str, Any]:
        return {key: tidy(getattr(self, key).value) for key in CUSTOM}

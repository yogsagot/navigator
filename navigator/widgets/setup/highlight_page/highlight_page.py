"""What OK means in *Highlight groups*: the ``[highlight_groups]`` section's new masks."""

from __future__ import annotations

from typing import Any


from navkit.i18n import tr
from navkit.widget import Widget

from navigator.lib.appearance.filetypes import CUSTOM
from navigator.settings import SETTINGS, HighlightGroupsData


def tidy(mask: str) -> str:
    """*mask* as ``SetHighlightGroups`` kept it: blanks dropped (``DelSpaces``),
    and no empty pattern between, before or after the ``;``-separated ones."""
    return ";".join(pattern for pattern in mask.replace(" ", "").split(";") if pattern)


class HighlightPage(Widget):
    """Which files each colour group takes: DN's ``CustomMask1``..``5``, one line a mask."""

    def __init__(self, section: HighlightGroupsData | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.section = section or SETTINGS.highlight_groups
        for key in CUSTOM:
            line = getattr(self, key)
            line.value = getattr(self.section, key)
            line.tooltip = tr("The files a row takes this group's colour for: patterns separated by ;, "
                              "such as *.png;*.jpg, whatever their case")

    def accept(self) -> dict[str, Any]:
        return {key: tidy(getattr(self, key).value) for key in CUSTOM}

"""What OK means in *Highlight groups*: the ``[highlight_groups]`` section's new masks."""

from __future__ import annotations

from typing import Any


from navkit.i18n import tr

from navigator.lib.appearance.filetypes import CUSTOM
from navigator.widgets.setup.settings_page import SettingsPage


def tidy(mask: str) -> str:
    """*mask* as ``SetHighlightGroups`` kept it: blanks dropped (``DelSpaces``),
    and no empty pattern between, before or after the ``;``-separated ones."""
    return ";".join(pattern for pattern in mask.replace(" ", "").split(";") if pattern)


class HighlightPage(SettingsPage):
    """Which files each colour group takes: DN's ``CustomMask1``..``5``, one line a mask."""

    def __init__(self, **kwargs: Any) -> None:
        # Each line says which mask it edits (``key:``); the tooltip is the
        # page's own, one for all five, rather than each setting's name.
        super().__init__(**kwargs)
        for key in CUSTOM:
            getattr(self, key).tooltip = tr("The files a row takes this group's colour for: patterns separated by ;, "
                              "such as *.png;*.jpg, whatever their case")

    def accept(self) -> dict[str, Any]:
        return {key: tidy(value) for key, value in super().accept().items()}

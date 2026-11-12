"""What OK means in *Viewer file types*: ``[viewer]``'s render switches and
masks -- the rest of ``[viewer]`` is *Editor/Viewer*'s, the two merged."""

from __future__ import annotations

from typing import Any


from navigator.widgets.setup.settings_page import SettingsPage

#: The formats with a switch, by the name their settings share
#: (``render_<name>``, ``<name>_masks``) -- the page's rows, top to bottom.
FORMATS = ("markdown", "rst", "html", "pdf", "images", "tables", "structured")

#: ``images``' masks are ``image_masks``, ``tables``' ``table_masks``.
MASKS = {"images": "image_masks", "tables": "table_masks"}


def masks_of(name: str) -> str:
    return MASKS.get(name, f"{name}_masks")


class ViewerTypesPage(SettingsPage):
    """The seven render switches with their masks, and SQLite's masks: each
    says what it edits (``key:``); the masks are tidied here."""

    def accept(self) -> dict[str, Any]:
        values = super().accept()
        for name in [*map(masks_of, FORMATS), "database_masks"]:
            values[name] = _masks(values[name])
        return values


def _masks(text: str) -> str:
    """A ``;``-list as typed, blanks around each mask let go; empty is none."""
    return ";".join(part.strip() for part in text.split(";") if part.strip())

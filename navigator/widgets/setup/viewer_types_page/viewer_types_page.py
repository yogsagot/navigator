"""What OK means in *Viewer file types*: ``[viewer]``'s render switches and
masks -- the rest of ``[viewer]`` is *Editor/Viewer*'s, the two merged."""

from __future__ import annotations

from typing import Any

from navkit.widget import Widget

from navigator.settings import SETTINGS, ViewerDefaultsData

#: The formats with a switch, by the name their settings share
#: (``render_<name>``, ``<name>_masks``) -- the page's rows, top to bottom.
FORMATS = ("markdown", "rst", "html", "pdf", "images", "tables", "structured")

#: ``images``' masks are ``image_masks``, ``tables``' ``table_masks``.
MASKS = {"images": "image_masks", "tables": "table_masks"}


def masks_of(name: str) -> str:
    return MASKS.get(name, f"{name}_masks")


class ViewerTypesPage(Widget):
    """The seven render switches with their masks, and SQLite's masks."""

    def __init__(self, section: ViewerDefaultsData | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.section = section or SETTINGS.viewer
        for name in FORMATS:
            box, line = getattr(self, name), getattr(self, f"{name}_masks")
            box.value = 1 if getattr(self.section, f"render_{name}") else 0
            box.tooltips = [self.section.tooltip(f"render_{name}")]
            line.value = getattr(self.section, masks_of(name))
            line.tooltip = self.section.tooltip(masks_of(name))
        self.database_masks.value = self.section.database_masks
        self.database_masks.tooltip = self.section.tooltip("database_masks")

    def accept(self) -> dict[str, Any]:
        values: dict[str, Any] = {}
        for name in FORMATS:
            values[f"render_{name}"] = bool(getattr(self, name).value & 1)
            values[masks_of(name)] = _masks(getattr(self, f"{name}_masks").value)
        values["database_masks"] = _masks(self.database_masks.value)
        return values


def _masks(text: str) -> str:
    """A ``;``-list as typed, blanks around each mask let go; empty is none."""
    return ";".join(part.strip() for part in text.split(";") if part.strip())

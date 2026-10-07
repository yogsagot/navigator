"""What OK means in *Column Defaults*: the ``[column_defaults]`` section's new values."""

from __future__ import annotations

from typing import Any

from navml.widgets.dialog.dialog import Dialog

from navigator.settings import SETTINGS, ColumnDefaultsData


class ColumnDefaultsDialog(Dialog):
    """The columns a new listing shows: DN's ``ColumnsDefaults`` words, one box a bit."""

    def __init__(self, section: ColumnDefaultsData | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.section = section or SETTINGS.column_defaults
        self.disk.value = self.section.to_bits(ColumnDefaultsData.DISK)
        self.find.value = self.section.to_bits(ColumnDefaultsData.FIND)

    def accept(self) -> dict[str, Any]:
        return {**ColumnDefaultsData.from_bits(ColumnDefaultsData.DISK, self.disk.value),
                **ColumnDefaultsData.from_bits(ColumnDefaultsData.FIND, self.find.value)}

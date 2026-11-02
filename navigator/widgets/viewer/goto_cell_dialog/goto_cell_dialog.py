"""What OK means in *Go to Cell Number*: a column and a row, either may be None."""

from __future__ import annotations

from typing import Any

from navml.widgets.dialog.dialog import Dialog

from navigator.lib.viewer.table import parse_cell


class GotoCellDialog(Dialog):
    """F6 in the spreadsheet: the cell to go to, seeded with *cell*."""

    def __init__(self, cell: str = "A1", **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.cell.value = cell
        self.cell.entry.select_all()

    def accept(self) -> Any:
        """``(column, row)`` from :func:`~navigator.lib.viewer.table.parse_cell`,
        or None for a line that names no cell -- DN's ``GotoCell`` did
        nothing then either."""
        return parse_cell(self.cell.value)

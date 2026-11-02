"""What *Find* in the spreadsheet opens on and answers: DN's ``SearchData``,
kept for the session as its typed constant was."""

from __future__ import annotations

from typing import Any

from navml.widgets.dialog.dialog import Dialog

from navigator.lib.viewer.table import CellSearch

#: ``SearchData``: what was last asked for.
LAST: CellSearch | None = None


class SheetFindDialog(Dialog):
    """The pattern, string or value, case and whole words."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        last = LAST
        if last is not None:
            self.pattern.value = last.text
            self.search_as.value = self.search_as.sel = 1 if last.as_value else 0
            self.options.value = (1 if last.case else 0) | (2 if last.whole else 0)
        self.pattern.entry.select_all()

    def accept(self) -> CellSearch | None:
        global LAST
        if not self.pattern.value:
            return None
        LAST = CellSearch(self.pattern.value, as_value=self.search_as.value == 1,
                          case=bool(self.options.value & 1), whole=bool(self.options.value & 2))
        return LAST

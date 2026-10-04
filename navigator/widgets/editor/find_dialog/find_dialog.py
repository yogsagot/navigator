"""What OK and *Change all* mean in *Find* and *Replace*: ``StartSearch``'s ``ExecResource``.

The dialog opens on :data:`navigator.editor.search.SEARCH` -- what the last
one was set to -- with the text to find replaced by the word at the cursor,
as ``StartSearch`` put it there.  OK writes the record back and answers
``"ok"``; *Change all* (``cmYes``) answers ``"all"``; Cancel, None.
"""

from __future__ import annotations

from typing import Any

from navkit.events import Event

from navml.widgets.dialog.dialog import Dialog

from navigator.editor import search
from navigator.editor.search import SearchData


class FindDialog(Dialog):
    """*Find* or, with *replace*, *Replace*: the search to run."""

    def __init__(self, *, word: str = "", data: SearchData | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.row.visible = False
        self.message.visible = False
        #: The record written back on OK: :data:`search.SEARCH` unless told
        #: otherwise, looked up now rather than bound when the class was made.
        self.data = data if data is not None else search.SEARCH
        data = self.data
        self.text.value = word
        self.text.entry.select_all()
        self.new.value = data.new or ""
        self.options.value = data.case | data.whole << 1 | data.prompt << 2
        self.direction.value = self.direction.sel = int(data.backward)
        self.scope.value = self.scope.sel = int(data.selected)
        self.origin.value = self.origin.sel = int(data.from_cursor)

    @property
    def buttons_row(self) -> tuple[Any, ...]:
        return (self.pick, self.all, self.abandon, self.helper)

    def _store(self) -> None:
        data = self.data
        data.text = self.text.value
        data.new = self.new.value if self.replace else None
        bits = self.options.value
        data.case, data.whole = bool(bits & 1), bool(bits & 2)
        if self.replace:
            data.prompt = bool(bits & 4)
        data.backward = self.direction.value == 1
        data.selected = self.scope.value == 1
        data.from_cursor = self.origin.value == 1

    def accept(self) -> str:
        self._store()
        return "ok"

    async def on_pick_click(self, event: Event) -> bool:
        self.record_history()
        self.close(self.accept())
        return True

    async def on_all_click(self, event: Event) -> bool:
        self.record_history()
        self._store()
        self.close("all")
        return True

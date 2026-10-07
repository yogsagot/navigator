"""What *Search* in the dBase viewer opens on and answers: DN's
``SearchRec``, kept for the session as its typed constant was."""

from __future__ import annotations

from typing import Any

from navml.widgets.dialog.dialog import Dialog

#: ``SearchRec``: what was last asked for.
LAST: dict[str, Any] = {"text": "", "case": False, "all_fields": False, "direction": 0}


class DBSearchDialog(Dialog):
    """The text, the case, the scope and the direction."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.message.visible = False
        self.text.value = LAST["text"]
        self.text.entry.select_all()
        self.options.value = 1 if LAST["case"] else 0
        self.scope.value = self.scope.sel = 1 if LAST["all_fields"] else 0
        self.direction.value = self.direction.sel = LAST["direction"]

    def accept(self) -> dict[str, Any] | None:
        if not self.text.value:
            return None
        LAST.update(text=self.text.value, case=bool(self.options.value & 1),
                    all_fields=self.scope.value == 1, direction=self.direction.value)
        return dict(LAST)

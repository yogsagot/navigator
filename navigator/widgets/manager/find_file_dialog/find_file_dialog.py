"""What OK means in *Find File*: a :class:`~navigator.filefind.FindRequest`.

The dialog opens as it was last left -- DN kept ``FindRec`` and
``AdvanceSearchData`` in its configuration; here they last the session.
"""

from __future__ import annotations

from typing import Any

from navkit.events import Event
from navml.widgets.dialog.dialog import Dialog

from navigator import filefind

#: The last answers: the four boxes as bits, the scope, and *Advanced
#: search*'s lines and kinds, as typed.
_session: dict[str, Any] = {
    "options": 4,  # *Recursive search*
    "scope": filefind.SCOPES.index("directory"),
    "advanced": {"after": "", "before": "", "greater": "", "less": "", "kinds": 0},
}


class FindFileDialog(Dialog):
    """DN's ``dlgFileFind``: what to look for, how, and where."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.row.visible = False
        self.message.visible = False
        self.options.value = _session["options"]
        self.scope.value = _session["scope"]
        self.limits = dict(_session["advanced"])

    @property
    def buttons_row(self) -> tuple[Any, ...]:
        return (self.pick, self.advanced, self.abandon)

    def accept(self) -> filefind.FindRequest:
        options = self.options.value
        _session["options"] = options
        _session["scope"] = self.scope.value
        _session["advanced"] = dict(self.limits)
        kinds = frozenset(
            name for index, name in enumerate(filefind.KINDS) if self.limits["kinds"] & (1 << index)
        )
        return filefind.FindRequest(
            mask=self.mask.value.replace(" ", "") or filefind.filetypes.ALL_FILES,
            text=self.text.value,
            advanced=bool(options & 1),
            case=bool(options & 2),
            recursive=bool(options & 4),
            words=bool(options & 8),
            scope=filefind.SCOPES[self.scope.value],
            limits=filefind.Advanced(
                after=filefind.parse_time(self.limits["after"]),
                before=filefind.parse_time(self.limits["before"]),
                greater=filefind.parse_size(self.limits["greater"]),
                less=filefind.parse_size(self.limits["less"]),
                kinds=kinds,
            ),
        )

    async def on_pick_click(self, event: Event) -> bool:
        self.record_history()
        self.close(self.accept())
        return True

    async def on_advanced_click(self, event: Event) -> bool:
        self.spawn(self.ask_advanced())
        return True

    async def ask_advanced(self) -> None:
        """*Advanced...*: the limits, and *Advanced search* ticked once they are set."""
        from navigator.widgets.manager.advanced_search_dialog import AdvancedSearchDialog

        answer = await AdvancedSearchDialog(self.limits).execute(self.application)
        if answer is not None:
            self.limits = answer
            self.options.value |= 1

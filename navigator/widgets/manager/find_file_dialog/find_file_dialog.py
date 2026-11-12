"""What OK means in *Find File*: a :class:`~navigator.lib.file_ops.filefind.FindRequest`
-- or, in *Replace in Files* (*replacing*), a
:class:`~navigator.lib.file_ops.filereplace.ReplaceRequest`.

The dialog opens as it was last left -- DN kept ``FindRec`` and
``AdvanceSearchData`` in its configuration; here they last the session.
"""

from __future__ import annotations

from typing import Any

from navkit.events import Event
from navkit.i18n import tr
from navml.widgets.dialog.dialog import Dialog

from navigator.lib.file_ops import filefind
#: The last answers: the five boxes as bits, the scope, and *Advanced
#: search*'s lines and kinds, as typed.
_session: dict[str, Any] = {
    "options": 4,  # *Recursive search*
    "scope": filefind.SCOPES.index("directory"),
    "advanced": {"after": "", "before": "", "greater": "", "less": "", "kinds": 0},
}

#: Replace in files' own, so that what it was last left at is not Find's.
_replace_session: dict[str, Any] = {key: (dict(value) if isinstance(value, dict) else value)
                                    for key, value in _session.items()}


class FindFileDialog(Dialog):
    """DN's ``dlgFileFind``: what to look for, how, and where."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        session = self.session
        self.options.value = session["options"]
        self.scope.value = session["scope"]
        self.limits = dict(session["advanced"])

    @property
    def session(self) -> dict[str, Any]:
        """Where this dialog's answers are kept: Find's, or Replace in files'."""
        return _replace_session if self.replacing else _session

    def accept(self) -> Any:
        options = self.options.value
        session = self.session
        session["options"] = options
        session["scope"] = self.scope.value
        session["advanced"] = dict(self.limits)
        kinds = frozenset(
            name for index, name in enumerate(filefind.KINDS) if self.limits["kinds"] & (1 << index)
        )
        request = filefind.FindRequest(
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
            regex=bool(options & 16),
        )
        if not self.replacing:
            return request
        from navigator.lib.file_ops.filereplace import ReplaceRequest

        return ReplaceRequest(request, self.replacement.value)

    def close_refusal(self) -> str | None:
        """Why OK cannot close the dialog: no text to replace, a pattern or
        a replacement that does not compile -- or None.

        Not ``refusal``: that is navkit's ``Widget.refusal(command)``, which
        ``enables()`` asks for every command a key here runs."""
        from navigator.lib.file_ops import filereplace

        if self.replacing and not self.text.value:
            return tr("Type the text to replace")
        request = filefind.FindRequest(text=self.text.value, case=bool(self.options.value & 2),
                                       words=bool(self.options.value & 8), regex=bool(self.options.value & 16))
        return filereplace.check(filereplace.ReplaceRequest(request, self.replacement.value if self.replacing else ""))

    async def on_pick_click(self, event: Event) -> bool:
        reason = self.close_refusal()
        if reason is not None:
            self.spawn(self.refuse(reason))
            return True
        self.record_history()
        self.close(self.accept())
        return True

    async def refuse(self, reason: str) -> None:
        from navml.widgets.dialog.control import escape_caption

        await Dialog(title=tr("Error"), prompt=escape_caption(reason), buttons="ok").execute(self.application)

    async def ask_advanced(self) -> None:
        """*Advanced...*: the limits, and *Advanced search* ticked once they are set."""
        from navigator.widgets.manager.advanced_search_dialog import AdvancedSearchDialog

        answer = await AdvancedSearchDialog(self.limits).execute(self.application)
        if answer is not None:
            self.limits = answer
            self.options.value |= 1

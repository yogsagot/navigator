"""What the box does: the replacement kept up with every key in the preview,
and OK only when it changes a target and spoils none.  The two lines are
kept for the session, as Multi-rename's rule is."""

from __future__ import annotations

from typing import Any, Sequence

from navkit.i18n import tr_n
from navkit.reactive import effect
from navml.widgets.dialog.dialog import Dialog

from navigator.lib.file_ops import filelink

#: The last search and replacement accepted, offered again next time.
_session: dict[str, str] = {"search": "", "replace": ""}


class RelinkDialog(Dialog):
    """*links* are ``(link, target)``: each link's location and what it holds now."""

    def __init__(self, links: Sequence[tuple[Any, str]] = (), **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.links = list(links)
        self.rows: list[filelink.Retarget] = []
        self.search.value = _session["search"]
        self.replace.value = _session["replace"]
        self.search.entry.select_all()

    def mounted(self) -> None:
        super().mounted()
        effect(self, RelinkDialog._follow)

    def _follow(self) -> None:
        """The preview and the line under it, from the two lines as they are."""
        self.rows = filelink.replaced(self.links, self.search.value, self.replace.value)
        self.preview.items = self.rows
        wrong = sum(1 for row in self.rows if row.problem not in ("", "unchanged"))
        if wrong:
            self.status.text = tr_n("{n} target cannot be given", "{n} targets cannot be given", wrong)
        else:
            changed = sum(1 for row in self.rows if not row.problem)
            self.status.text = tr_n("{n} link to change", "{n} links to change", changed)

    def valid(self) -> bool:
        """OK only with a target changed and none spoilt."""
        return (any(not row.problem for row in self.rows)
                and all(row.problem in ("", "unchanged") for row in self.rows))

    def accept(self) -> list[filelink.Retarget]:
        """The rows that change, the two lines kept for next time."""
        _session["search"], _session["replace"] = self.search.value, self.replace.value
        return [row for row in self.rows if not row.problem]

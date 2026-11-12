"""What *Columns Setup* answers: the columns ticked, *Brief*, or *Full*."""

from __future__ import annotations

from typing import Any

from navkit.i18n import tr
from navml.widgets.dialog.dialog import Dialog

#: The boxes' columns, in their order (``Panel.DETAIL_ORDER``).
COLUMNS = ("size", "attributes", "links", "owner", "date")
#: An archive's boxes: DN's ``dlgArcParms``, its original and packed sizes
#: and ratio, then the rest.
ARCHIVE_COLUMNS = ("size", "packed", "ratio", "attributes", "owner", "date")
#: What *Full* shows, each panel showing those of them its listing has:
#: every column but *Links*.  DN's ``GetFullFlags`` was size, date and time
#: (and packed and ratio in an archive); attributes and the owner stay as the
#: POSIX facts a full listing gives, and the link count, ``ls -l``'s least
#: read figure, is left for its box -- a departure only in what it adds.
ALL_COLUMNS = (frozenset(COLUMNS) | frozenset(ARCHIVE_COLUMNS)) - {"links"}


class ColumnsDialog(Dialog):
    """``CM_SetShowParms``'s dialog for one panel: ``("columns", set)``,
    ``("brief",)`` or ``("full",)``."""

    def __init__(self, columns: frozenset[str] = frozenset(COLUMNS), listing: bool = False,
                 archive: bool = False, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        # In an archive the boxes are ``dlgArcParms``'.  A *Find:* listing's
        # are a directory's: DN's last box, the path, is a footer line here.
        if archive and not listing:
            self.keys_shown = ARCHIVE_COLUMNS
            self.show.items = [tr("~O~riginal size"), tr("Pa~c~ked size"), tr("~R~atio"), tr("~A~ttributes"),
                               tr("O~w~ner"), tr("~D~ate")]
            self.show.height = len(ARCHIVE_COLUMNS)
        else:
            self.keys_shown = COLUMNS
        self.show.value = sum(1 << index for index, key in enumerate(self.keys_shown) if key in columns)
        self._kept = frozenset(columns) - set(self.keys_shown)

    @property
    def buttons_row(self) -> tuple[Any, ...]:
        return (self.pick, self.abandon, self.brief, self.full)

    def accept(self) -> tuple[str, frozenset[str]]:
        ticked = {key for index, key in enumerate(self.keys_shown) if self.show.value & (1 << index)}
        return "columns", frozenset(ticked) | self._kept


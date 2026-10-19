"""What *Settings* opens on and what OK means: every section's new values."""

from __future__ import annotations

from typing import Any

from navkit.reactive import bind, unbind
from navkit.widget import Widget
from navml.widgets.dialog.dialog import Dialog

from navigator.settings import SETTINGS

#: Each page by its id, and the ``navigator.ini`` sections it answers for.
#: One section's page answers its values; *Editor/Viewer*'s answers two,
#: by section name.
PAGES: dict[str, tuple[str, ...]] = {
    "system": ("system",),
    "startup": ("startup",),
    "interface": ("interface",),
    "confirmations": ("confirmations",),
    "savers": ("savers",),
    "editor_viewer": ("editor", "viewer"),
    "file_manager": ("file_manager",),
    "drive_info": ("drive_info",),
    "panel_defaults": ("panel_defaults",),
    "column_defaults": ("column_defaults",),
    "highlight_groups": ("highlight_groups",),
}

#: The dialog's width with its tabs down the left.
LEFT_WIDTH = 80

#: Every section the dialog answers for, in page order.
SECTIONS: tuple[str, ...] = tuple(name for names in PAGES.values() for name in names)


class SettingsDialog(Dialog):
    """Every setup page, opened on the one named by *tab*."""

    def __init__(self, tab: str = "system", side: str | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        # Read as it opens: Interface's choice applies the next time.  Down
        # the left, four columns wider -- a whole 80-column screen -- so a
        # page keeps the width it was laid out in beside the column of tabs.
        self.tabs.side = side or SETTINGS.interface.settings_tabs
        if self.tabs.side == "left":
            self.modal_width = LEFT_WIDTH
            self._buttons_under_pages()
        self.tabs.select(self.tabs.index_of(self.page(tab)))

    def _buttons_under_pages(self) -> None:
        """OK and Cancel centred under the pages rather than the whole box,
        which down the left begins past the column of tabs and its rule.  The
        column follows its captions, and so does this, through a language
        change."""
        tabs, row = self.tabs, self.row
        unbind(row, Widget.x)
        unbind(row, Widget.width)
        row.x = bind(lambda r: tabs.x + tabs.column + 1)
        row.width = bind(lambda r: max(0, tabs.x + tabs.width - r.x))

    def page(self, tab: str) -> Widget:
        if tab not in PAGES:
            raise KeyError(f"no settings page {tab!r}; there are {', '.join(PAGES)}")
        return getattr(self, tab)

    def accept(self) -> dict[str, dict[str, Any]]:
        answer: dict[str, dict[str, Any]] = {}
        for tab, sections in PAGES.items():
            values = self.page(tab).accept()
            answer.update(values if len(sections) > 1 else {sections[0]: values})
        return answer

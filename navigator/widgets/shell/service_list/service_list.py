"""The list inside Utilities > Services: a row per systemd unit, under column titles.

A :class:`~navigator.widgets.shell.process_list.ColumnList`, as Process list's
is: *Unit* (*Service* for OpenRC), *State* (systemd's active and sub state,
``active/running``; OpenRC's ``started``, ``crashed``...) and *Start-up* (the
unit file's state -- enabled, static, masked -- or OpenRC's runlevels) keep their widths;
*Description* takes what is left.  A click on a title sorts by it, and typing
goes to the window's *Filter* line, both as Process list's.
"""

from __future__ import annotations

from typing import Any

from navkit.i18n import tr
from navkit.style import Style
from navml.widgets.dialog.commands import QuickSearch

from navigator.lib.system import services
from navigator.widgets.shell.process_list import ColumnList

#: The fixed columns' widths; the description has the rest.
UNIT_WIDTH = 32
STATE_WIDTH = 18
STARTUP_WIDTH = 10


class ServiceList(ColumnList):
    """Units: name, whether it runs, how it starts, and what it is."""

    WIDTHS = (UNIT_WIDTH, STATE_WIDTH, STARTUP_WIDTH, None)
    SORTS = ("name", "active", "startup", "description")

    keys = {"ctrl+s": QuickSearch}

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.sort = "name"
        #: The first column's title: a *Unit* of systemd's, a *Service* of OpenRC's.
        self.noun = "unit"

    def titles(self) -> tuple[str, ...]:
        first = tr("Unit") if self.noun == "unit" else tr("Service")
        return (first, tr("State"), tr("Start-up"), tr("Description"))

    def cells(self, row: services.Unit) -> list[tuple[str, bool]]:
        state = f"{row.active}/{row.sub}" if row.sub else row.active
        return [(row.name, False), (state, False), (row.startup, False), (row.description, False)]

    def row_text(self, index: int, item: Any) -> str:
        return item.name

    def row_tooltip(self, index: int, item: Any) -> str:
        """The whole name and description: either may be cut in its column."""
        return "\n".join(part for part in (item.name, item.description) if part)

    def row_style(self, index: int, item: Any) -> Style:
        classes = []
        if item.failed:
            classes.append("failed")
        elif item.running:
            classes.append("running")
        else:
            classes.append("inactive")
        if item.masked:
            classes.append("masked")
        return self.part_style("row", classes=tuple(classes), selected=self.row_selected(index))

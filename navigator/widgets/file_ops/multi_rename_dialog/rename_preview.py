"""Multi-rename's preview: each file's name as it is and as it will be."""

from __future__ import annotations

from typing import Any

from navkit import glyphs as glyphs_module
from navkit.i18n import tr

from navml.widgets.dialog.list_viewer import ListViewer

from navigator.lib.file_ops import multirename


def problem_text(problem: str | None) -> str:
    """What :func:`navigator.lib.file_ops.multirename.plan` found wrong, in words."""
    if problem == multirename.EMPTY:
        return tr("The new name is empty")
    if problem == multirename.SLASH:
        return tr("A name cannot hold a /")
    if problem == multirename.DOTS:
        return tr("A name cannot be . or ..")
    if problem == multirename.TWICE:
        return tr("Two files would get this name")
    if problem == multirename.TAKEN:
        return tr("A file of that name is already there")
    return ""


class RenamePreview(ListViewer):
    """The plan's rows: ``old → new``, a ``!`` before one that cannot be
    done, the cursor's problem in the footer."""

    def row_text(self, index: int, item: Any) -> str:
        arrow = "→" if self.glyphs > glyphs_module.GLYPHS_ASCII else "->"
        mark = "!" if item.problem else " "
        half = max(4, (self.inner_width - 4) // 2)
        old = item.item.name
        if len(old) > half:
            old = old[:half - 1] + glyphs_module.ellipsis(self.glyphs)[:1]
        new = item.new if item.changed else ""
        return f"{mark}{old:<{half}} {arrow if item.changed else ' '} {new}"

    def footer_text(self) -> str:
        row = self.selected
        return problem_text(row.problem) if row is not None else ""

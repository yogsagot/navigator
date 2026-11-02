"""The *Change link targets* preview: each link, what it holds and what it will."""

from __future__ import annotations

from typing import Any

from navkit import glyphs as glyphs_module
from navkit.i18n import tr

from navml.widgets.dialog.list_viewer import ListViewer


def problem_text(problem: str) -> str:
    """What :func:`navigator.lib.file_ops.filelink.replaced` found wrong, in words."""
    if problem == "empty":
        return tr("The new target is empty")
    if problem == "nul":
        return tr("A target cannot hold a NUL character")
    return ""


class RelinkPreview(ListViewer):
    """``name: old → new``, a ``!`` before a row that cannot be done, the
    cursor's target in full in the footer."""

    def row_text(self, index: int, item: Any) -> str:
        arrow = "→" if self.glyphs > glyphs_module.GLYPHS_ASCII else "->"
        changed = item.problem != "unchanged"
        mark = "!" if changed and item.problem else " "
        tail = f" {arrow} {item.new}" if changed and not item.problem else ""
        return f"{mark}{item.link.name}: {item.old}{tail}"

    def footer_text(self) -> str:
        row = self.selected
        if row is None:
            return ""
        return problem_text(row.problem) or (row.new if row.problem != "unchanged" else row.old)

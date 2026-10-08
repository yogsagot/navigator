"""The boxes' text, from what :func:`navigator.sysinfo.gather` read."""

from __future__ import annotations

from typing import Any

from navkit import glyphs

from navml.widgets.dialog.dialog import Dialog

from navigator.sysinfo import SystemFacts, lines


class SystemInfoDialog(Dialog):
    """DN's ``SystemInfo``: four boxes and OK."""

    def __init__(self, facts: SystemFacts | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.message.visible = False
        self.facts = facts or SystemFacts()

    def mounted(self) -> None:
        """Fill the boxes once mounted, when the glyph tier is the terminal's."""
        super().mounted()
        marker = glyphs.ellipsis(self.glyphs)
        for name in ("board", "disks", "memory", "other"):
            box = getattr(self, name)
            box.text = lines(getattr(self.facts, name), box.width, marker)

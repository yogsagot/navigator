"""The boxes' text, from what :func:`navigator.sysinfo.gather` read."""

from __future__ import annotations

from typing import Any

from navml.widgets.dialog.dialog import Dialog

from navigator.sysinfo import SystemFacts, lines


class SystemInfoDialog(Dialog):
    """DN's ``SystemInfo``: four boxes and OK."""

    def __init__(self, facts: SystemFacts | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.message.visible = False
        facts = facts or SystemFacts()
        for name in ("board", "disks", "memory", "other"):
            box = getattr(self, name)
            box.text = lines(getattr(facts, name), box.width)

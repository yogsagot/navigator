"""What OK means in *Communications*: the ``[remote]`` section's new values,
and ``[system] desktop_vfs`` and ``notifications`` -- each control says which
it edits (``key:``), and :class:`SettingsPage` seeds and collects them."""

from __future__ import annotations

from typing import Any

from navigator.widgets.setup.settings_page import SettingsPage


class CommunicationsPage(SettingsPage):
    """``[remote]``: keep-alives, how long to wait, idle connections, and
    what a changed file fetched from a server does; and ``[system]``'s
    *Desktop integration* and *Notify*.  Answers both sections by name."""

    def accept(self) -> dict[str, Any]:
        values = super().accept()
        # A connection that may wait no time at all could never be made.
        values["remote"]["timeout"] = max(1, values["remote"]["timeout"])
        return values

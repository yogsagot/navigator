"""What OK means in *Communications*: the ``[remote]`` section's new values,
and ``[system] desktop_vfs``."""

from __future__ import annotations

from typing import Any

from navkit.widget import Widget

from navigator.settings import DESKTOP_VFS, SETTINGS, RemoteData, SystemData


def _number(text: str, keep: int) -> int:
    text = text.replace(" ", "0")
    return int(text) if text.isdigit() else keep


class CommunicationsPage(Widget):
    """``[remote]``: keep-alives, how long to wait, idle connections, and
    what a changed file fetched from a server does; and ``[system]``'s
    *Desktop integration*.  Answers both sections by name."""

    def __init__(self, section: RemoteData | None = None, system: SystemData | None = None,
                 **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.section = section or SETTINGS.remote
        self.system = system or SETTINGS.system
        self.desktop_vfs.value = DESKTOP_VFS.index(self.system.desktop_vfs)
        self.keepalive.value = f"{self.section.keepalive:03d}"
        self.keepalive.tooltip = self.section.tooltip("keepalive")
        self.timeout.value = f"{self.section.timeout:03d}"
        self.timeout.tooltip = self.section.tooltip("timeout")
        self.idle_disconnect.value = f"{self.section.idle_disconnect:03d}"
        self.idle_disconnect.tooltip = self.section.tooltip("idle_disconnect")
        self.refresh.value = f"{self.section.refresh:03d}"
        self.refresh.tooltip = self.section.tooltip("refresh")
        self.upload_changed.value = RemoteData.UPLOAD.index(self.section.upload_changed)
        self.upload_changed.tooltip = self.section.tooltip("upload_changed")

    def accept(self) -> dict[str, dict[str, Any]]:
        section = self.section
        return {
            "remote": {
                "keepalive": _number(self.keepalive.value, section.keepalive),
                "timeout": max(1, _number(self.timeout.value, section.timeout)),
                "idle_disconnect": _number(self.idle_disconnect.value, section.idle_disconnect),
                "refresh": _number(self.refresh.value, section.refresh),
                "upload_changed": RemoteData.UPLOAD[self.upload_changed.value],
            },
            "system": {"desktop_vfs": DESKTOP_VFS[self.desktop_vfs.value]},
        }

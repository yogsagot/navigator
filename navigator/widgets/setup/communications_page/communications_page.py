"""What OK means in *Communications*: the ``[remote]`` section's new values."""

from __future__ import annotations

from typing import Any

from navkit.widget import Widget

from navigator.settings import SETTINGS, RemoteData


def _number(text: str, keep: int) -> int:
    text = text.replace(" ", "0")
    return int(text) if text.isdigit() else keep


class CommunicationsPage(Widget):
    """``[remote]``: keep-alives, how long to wait, idle connections, and
    what a changed file fetched from a server does."""

    def __init__(self, section: RemoteData | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.section = section or SETTINGS.remote
        self.keepalive.value = f"{self.section.keepalive:03d}"
        self.timeout.value = f"{self.section.timeout:03d}"
        self.idle_disconnect.value = f"{self.section.idle_disconnect:03d}"
        self.refresh.value = f"{self.section.refresh:03d}"
        self.upload_changed.value = RemoteData.UPLOAD.index(self.section.upload_changed)

    def accept(self) -> dict[str, Any]:
        section = self.section
        return {
            "keepalive": _number(self.keepalive.value, section.keepalive),
            "timeout": max(1, _number(self.timeout.value, section.timeout)),
            "idle_disconnect": _number(self.idle_disconnect.value, section.idle_disconnect),
            "refresh": _number(self.refresh.value, section.refresh),
            "upload_changed": RemoteData.UPLOAD[self.upload_changed.value],
        }

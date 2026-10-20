"""*Saved links*' list: a ``ListViewer`` that leaves Ctrl+Up and Ctrl+Down
to the dialog, which moves the focused link with them -- the list would take
them for Up and Down."""

from __future__ import annotations

from navkit.events import KeyEvent

from navml.widgets.dialog.list_viewer import ListViewer


class LinkList(ListViewer):
    """The links, one a row."""

    async def on_key(self, event: KeyEvent) -> bool:
        if event.ctrl and event.key in ("up", "down"):
            return False
        return await super().on_key(event)


__all__ = ["LinkList"]

"""What ``help_window.nml`` cannot say: which page, and the two commands
that name one."""

from __future__ import annotations

from typing import Any

from navkit.commands import Command
from navkit.i18n import tr
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.scroll_bar import ScrollEvent

from navigator.lib.help import pages
from navigator.widgets.help.commands import GoBack, GoToReference, HelpIndex, HelpOnHelp


class HelpWindow(Dialog):
    """Help, opened on *topic* (``page.md#anchor``; the contents page by default)."""

    def __init__(self, topic: str = pages.CONTENTS, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.viewer.show(topic)

    def toggle_zoom(self) -> None:
        self.zoomed = not self.zoomed

    async def on_help_on_help(self, event: HelpOnHelp) -> bool:
        self.viewer.show(pages.HELP_ON_HELP)
        return True

    async def on_help_index(self, event: HelpIndex) -> bool:
        self.viewer.show(pages.CONTENTS)
        return True

    async def on_bar_scroll(self, event: ScrollEvent) -> bool:
        self.viewer.scroll_to(event.value)
        return True

    def refusal(self, command: Command) -> str:
        viewer = self.viewer
        if isinstance(command, GoBack) and not viewer.history:
            return tr("This is the first page")
        if isinstance(command, GoToReference) and not 0 <= viewer.selected < len(viewer.links):
            return tr("No link is selected")
        return super().refusal(command)

    def key_hints(self) -> list[tuple[str, str]]:
        """``StatusDef hcHelp``'s items no function key carries."""
        return [("Tab", tr("Next topic")), ("Enter", tr("Go to reference"))]

"""The frame and the following behind ``quick_viewer.nml``.

**It follows the active panel**, as ``SendLocated`` made DOS Navigator's do:
every move of the panel's cursor sends the file under it here, and a file
already showing is left where it was scrolled to (``cmLoadViewFile`` compared
the names).  A directory, ``..`` or a file that will not open shows nothing,
which is what ``ReadFile`` failing left on DN's screen.

**The file is opened on a thread**, since the cursor moves on every key and a
file on a dead mount, or one of ``/proc``'s that is read whole, would stop the
panel with it.  Only the file the cursor is on when an opening lands is shown.

**The keys that move are the viewer's**; F3, F4 and the rest stay the file
panel's, whose status line DN kept showing while the quick view was up.
"""

from __future__ import annotations

from pathlib import Path

from navkit.screen import Surface
from navkit.stylesheet import StyleProperty
from navkit.glyphs import BOX_CHARSETS
from navkit.widget import Widget

from navml.background import Background, Outcome
from navml.widgets.dialog.scroll_bar import ScrollEvent

from navigator.viewer import ViewSource

#: Where the quick view opens its files.
_OPENER = Background("nav-quick", workers=2)


class QuickViewer(Widget):
    """Ctrl+Q: a panel-shaped view of the file under the other panel's cursor."""

    #: Single while the keyboard is elsewhere, double while it is in here --
    #: a panel's rule, set in the sheet.
    border = StyleProperty("single", values=tuple(BOX_CHARSETS))

    #: The file's name across the top frame.
    parts = ("title",)

    #: The file asked for last; an opening of any other lands on nothing.
    _wanted: Path | None = None

    def show(self, path: Path | None) -> None:
        """Show *path*, unless it is already showing; nothing for anything but a file."""
        viewer = self.viewer
        path = Path(path) if path is not None else None
        if path is not None and viewer.path == path and viewer.source is not None:
            self._wanted = path
            return
        self._wanted = path
        if path is None:
            viewer.close_file()
            return
        _OPENER.run(self, ViewSource, path,
                    done=lambda outcome, path=path: self._opened(path, outcome))

    def _opened(self, path: Path, outcome: Outcome) -> None:
        try:
            source = outcome.result()
        except OSError:
            # Not a file -- a directory, a device -- or not readable.
            if self._wanted == path:
                self.viewer.close_file()
            return
        if self._wanted != path:
            source.close()  # the cursor has moved on
            return
        self.viewer.open(path, source=source)

    async def on_bar_scroll(self, event: ScrollEvent) -> bool:
        self.viewer.seek(event.value)
        return True

    def title_text(self) -> str:
        path = self.viewer.path
        if path is None:
            return ""
        room = max(4, self.width - 4 - 2 * self.title_margin)
        name = path.name
        if len(name) > room:
            name = name[: room - 3] + "..."
        return f" {name} "

    def render(self, surface: Surface) -> None:
        if self.width < 2 or self.height < 2:
            return
        surface.draw_box(0, 0, self.width, self.height, self.style,
                         charset=self.box_charset(), fill=" ")
        title = self.title_text()
        if title:
            surface.draw_text(max(1, (self.width - len(title)) // 2), 0, title,
                              self.part_style("title"))

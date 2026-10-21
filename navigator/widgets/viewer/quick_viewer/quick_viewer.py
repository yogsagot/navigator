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
from typing import Any

from navkit.screen import Surface
from navkit.stylesheet import StyleProperty
from navkit.glyphs import BOX_CHARSETS
from navkit.widget import Widget

from navml.background import Background, Outcome
from navml.widgets.dialog.scroll_bar import ScrollEvent

from navigator.widgets.viewer.commands import SwitchMarkdown

from navigator.lib.viewer import ViewSource

#: Where the quick view opens its files.
_OPENER = Background("nav-quick", workers=2)


def _open_head(origin: Any) -> tuple[Any, ViewSource]:
    """On the opener's thread: *origin*'s head fetched, and a source on it."""
    from navigator.lib.drives import usefile

    use = usefile.fetch_head(origin)
    try:
        return use, ViewSource(use.local_for(origin))
    except BaseException:
        usefile.discard(use)
        raise


def _discard_later(use: Any) -> None:
    """A fetched head deleted, off the loop where there is one."""
    import asyncio

    from navigator.lib.drives import usefile

    try:
        asyncio.get_running_loop().run_in_executor(None, usefile.discard, use)
    except RuntimeError:
        usefile.discard(use)


class QuickViewer(Widget):
    """Ctrl+Q: a panel-shaped view of the file under the other panel's cursor."""

    #: Single while the keyboard is elsewhere, double while it is in here --
    #: a panel's rule, set in the sheet.
    border = StyleProperty("single", values=tuple(BOX_CHARSETS))

    #: The file's name across the top frame.
    parts = ("title",)

    #: The file asked for last; an opening of any other lands on nothing.
    _wanted: Any = None
    #: What was fetched for the file on another drive showing now, if any.
    _use: Any = None

    def show(self, path: Any) -> None:
        """Show *path*, unless it is already showing; nothing for anything but a file.

        A :class:`~navigator.lib.drives.Location` on another drive has its
        first megabyte fetched (``usefile.fetch_head``) and that shown."""
        from navigator.lib.drives import Location

        if isinstance(path, Location) and not path.is_local:
            self._show_elsewhere(path)
            return
        if isinstance(path, Location):
            path = path.local
        self._let_go()
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

    def _show_elsewhere(self, origin: Any) -> None:
        if self._wanted == origin and self.viewer.source is not None:
            return
        self._wanted = origin
        _OPENER.run(self, _open_head, origin, done=lambda outcome, origin=origin: self._fetched(origin, outcome))

    def _fetched(self, origin: Any, outcome: Outcome) -> None:
        try:
            use, source = outcome.result()
        except OSError:
            if self._wanted == origin:
                self._let_go()
                self.viewer.close_file()
            return
        if self._wanted != origin:
            source.close()
            _discard_later(use)
            return
        self._let_go()
        self._use = use
        self.viewer.open(use.local_for(origin), source=source)

    def _let_go(self) -> None:
        use, self._use = self._use, None
        if use is not None:
            _discard_later(use)

    def unmounting(self) -> None:
        self._let_go()
        super().unmounting()

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

    async def on_switch_markdown(self, event: SwitchMarkdown) -> bool:
        """Shift+F4: a Markdown file rendered, or its source, as in F3."""
        if self.viewer.mode == "text" and self.viewer.can_render:
            self.viewer.toggle_markdown()
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

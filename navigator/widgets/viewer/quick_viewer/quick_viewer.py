"""The frame and the following behind ``quick_viewer.nml``.

**It follows the active panel**, as ``SendLocated`` made DOS Navigator's do:
every move of the panel's cursor sends the file under it here, and a file
already showing is left where it was scrolled to (``cmLoadViewFile`` compared
the names).  A directory, ``..`` or a file that will not open shows nothing,
which is what ``ReadFile`` failing left on DN's screen.

**The file is opened on a thread**, since the cursor moves on every key and a
file on a dead mount, or one of ``/proc``'s that is read whole, would stop the
panel with it.  Only the file the cursor is on when an opening lands is shown.

**With the keyboard in here, the keys are the viewer's**, ``StatusDef
hcView``'s: F2 wrap, F4 hex and dump, F5 go to, F6 filter, F7 and the
searches again, Shift+F5 Save as and Shift+F6 the encoding, handled by
``viewer_host`` as in the F3 window.  A key hcView did not list still reaches
the panels (a departure; the markup's ``keys:`` says why).  While the panel
has the keyboard, every key is the panel's, as DN's status line was.

**Viewer setup's *Hex mode* and *Wrap lines* apply each time Ctrl+Q turns the
view on** (:meth:`QuickViewer.fresh`): ``ViewInsert`` made a new
``THFileViewer`` then, opened by ``ViOpt``, and ``SwitchView`` freed it when
it went.  Moving to another file keeps the mode, as one viewer kept its
``ViewMode`` across ``cmLoadViewFile``.

**A file the user may not read is shown as root only while root access is
open already** -- from an *As root* answered elsewhere, within ``[system]
root_timeout`` (a departure; :mod:`navigator.lib.system.elevate`).  Moving the
cursor never asks for a password; otherwise it shows nothing, as before.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from navkit.commands import Command
from navkit.i18n import tr
from navkit.screen import Surface
from navkit.stylesheet import StyleProperty
from navkit.bidi import display_width, reveal
from navkit.glyphs import BOX_CHARSETS, hidden_mark
from navkit.widget import Widget

from navml.background import Background, Outcome
from navml.widgets.dialog.scroll_bar import ScrollEvent

from navigator.settings import SETTINGS
from navigator.widgets.viewer.commands import (
    AddFilter,
    ChooseEncoding,
    ContinueSearch,
    GotoAddress,
    HexMode,
    ReverseSearch,
    SaveViewAs,
    SearchAgain,
    SearchFor,
    SetViewFilter,
    SetViewMode,
    Unwrap,
)
from navigator.widgets.viewer.commands import SwitchRendered

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


def _host() -> Any:
    """``navigator.widgets.viewer.viewer_host``, imported at first use."""
    from navigator.widgets.viewer import viewer_host

    return viewer_host


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

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        # The F3 window's menu greys nearly all of itself here, and its *Close*
        # would close the file manager: this one's own instead.
        self.viewer.context_menu = self.context_menu
        # And the keyboard stays with the panel, as the console's menu leaves
        # it with the command line: *Close quick view* taken with the keyboard
        # in here would hand it to the panel put back (``switch_view``).
        self.viewer.context_focus = False

    def context_menu(self) -> Any:
        """The quick view's right-click menu -- a departure, asked for, as every
        context menu is: the file in the full viewer (the panel's F3, on the
        same file), *Markup view*, and Ctrl+Q's way back to the panel."""
        from navkit.i18n import tr
        from navml.widgets.menu.context_menu import ContextMenu

        from navigator.widgets.manager.commands import QuickView, View

        if self.viewer.source is None:
            return None
        menu = ContextMenu()
        menu.add_item(tr("~V~iew"), View)
        menu.add_item(tr("~M~arkup view"), SwitchRendered)
        menu.add_line()
        menu.add_item(tr("~C~lose quick view"), QuickView)
        return menu

    def fresh(self) -> None:
        """Ctrl+Q turned the view on: DN's new ``THFileViewer``, in hex if
        Viewer setup's *Hex mode* says, wrapped if *Wrap lines* does
        (``ViOpt``), with no filter and no code page (``UseXLat := Off``).
        Whether the markup is rendered is each file's, as it opens."""
        viewer = self.viewer
        viewer.set_mode("hex" if SETTINGS.viewer.hex_mode else "text")
        viewer.wrap = SETTINGS.viewer.wrap_lines
        viewer.set_filter(0)
        if viewer.encoding != "utf-8":
            viewer.set_encoding("utf-8")

    #: The commands that need a file shown.
    _VIEW_COMMANDS = (AddFilter, ChooseEncoding, ContinueSearch, GotoAddress, HexMode, ReverseSearch,
                      SaveViewAs, SearchAgain, SearchFor, Unwrap)

    def refusal(self, command: Command) -> str:
        """Nothing shown, nothing to act on; and *Save as* of a file from
        another drive would write only the first megabyte fetched of it."""
        if isinstance(command, self._VIEW_COMMANDS) and self.viewer.source is None:
            return tr("Nothing is open")
        if isinstance(command, SaveViewAs) and self._use is not None:
            return tr("Only the start of the file was read")
        host = _host()
        if isinstance(command, host.COMMANDS):
            return host.refusal(self, command) or super().refusal(command)
        return super().refusal(command)

    def checks(self, command: Command) -> bool | None:
        checked = _host().checks(self, command)
        return checked if checked is not None else super().checks(command)

    # -- the view commands (``viewer_host``, written out: one base) ------------
    #
    # ``viewer_host`` is imported where it is used: the desktop places a quick
    # view at start, and its dialogs (and the editor's commands) wait for a key.

    async def on_unwrap(self, event: Unwrap) -> bool:
        self.viewer.toggle_wrap()
        return True

    async def on_hex_mode(self, event: HexMode) -> bool:
        self.viewer.cycle_mode()
        return True

    async def on_add_filter(self, event: AddFilter) -> bool:
        self.viewer.cycle_filter()
        return True

    async def on_set_view_mode(self, event: SetViewMode) -> bool:
        self.viewer.set_mode(event.mode)
        return True

    async def on_set_view_filter(self, event: SetViewFilter) -> bool:
        self.viewer.set_filter(event.filter)
        return True

    async def on_goto_address(self, event: GotoAddress) -> bool:
        self.spawn(_host().goto_address(self))
        return True

    async def on_save_view_as(self, event: SaveViewAs) -> bool:
        self.spawn(_host().save_as(self))
        return True

    async def on_choose_encoding(self, event: ChooseEncoding) -> bool:
        self.spawn(_host().choose_encoding(self))
        return True

    async def on_search_for(self, event: SearchFor) -> bool:
        self.spawn(_host().search_for(self))
        return True

    async def on_continue_search(self, event: ContinueSearch) -> bool:
        self.spawn(_host().search_again(self, reverse=False))
        return True

    async def on_search_again(self, event: SearchAgain) -> bool:
        self.spawn(_host().search_again(self, reverse=False))
        return True

    async def on_reverse_search(self, event: ReverseSearch) -> bool:
        self.spawn(_host().search_again(self, reverse=True))
        return True

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

    def _opened(self, path: Path, outcome: Outcome, *, as_root: bool = False) -> None:
        from navigator.lib.system.elevate import ELEVATION, refused

        try:
            source = outcome.result()
        except OSError as error:
            if self._wanted == path and not as_root and refused(error) and ELEVATION.running:
                from navigator.widgets.file_ops.as_root import root_source

                # Through the helper open already, a chunk at a time, as F3's
                # *As root* reads; never copied to the disk.
                _OPENER.run(self, root_source, path,
                            done=lambda outcome, path=path: self._opened(path, outcome, as_root=True))
                return
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

    async def on_hbar_scroll(self, event: ScrollEvent) -> bool:
        """The bottom bar was worked: the column the rows start at."""
        self.viewer.x_delta = max(0, event.value)
        return True

    async def on_switch_rendered(self, event: SwitchRendered) -> bool:
        """Shift+F3: a Markdown, reST, HTML or PDF file rendered, or its source, as in F3."""
        if self.viewer.mode == "text" and self.viewer.can_render:
            self.viewer.toggle_rendered()
        return True

    def title_text(self) -> str:
        path = self.viewer.path
        if path is None:
            return ""
        room = max(4, self.width - 4 - 2 * self.title_margin)
        name = reveal(path.name, hidden_mark(self.glyphs))
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
            surface.draw_text(max(1, (self.width - display_width(title)) // 2), 0, title,
                              self.part_style("title"))

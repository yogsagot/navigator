"""The handlers behind ``file_window.nml``: the viewer's commands.

The keys that *move* are ``FileViewer``'s own and reach it first along the
focus path; what is here is what the key bar names -- the switches, and the
two dialogs.  Both dialogs are started, never awaited, for the reason
``Manager.on_make_directory`` gives: a handler that waits on a dialog holds the
only consumer of the queue the dialog's keys arrive on.
"""

from __future__ import annotations

from pathlib import Path, PurePosixPath
from typing import Any

from navkit.commands import Command
from navkit.events import DoubleClickEvent, MouseClickEvent
from navkit.i18n import tr
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.scroll_bar import ScrollEvent
from navml.widgets.window import Window

import navigator.lib.viewer as viewer_model
from navigator.widgets.viewer.commands import (
    AddFilter,
    ChooseEncoding,
    SaveViewAs,
    CloseViewer,
    ContinueSearch,
    GotoAddress,
    HexMode,
    ReverseSearch,
    SearchAgain,
    SearchFor,
    SetViewFilter,
    SetViewMode,
    SwitchRendered,
    Unwrap,
)
from navigator.widgets.editor.commands import ChooseFileType, SetFileType, SwitchHiddenChars, SwitchHighLight
from navigator.widgets.editor.file_type_menu import choose_file_type, fill_file_types
from navigator.widgets.editor.option_items import viewer_items
from navigator.lib.config.file_history import place_window, window_values
from navigator.models.view_record import ViewRecord
from navigator.lib.system.progress import run_with_progress
from navigator.lib.viewer import SearchJob, ViewSearch
from navigator.settings import SETTINGS
from navigator.widgets.viewer.file_viewer.file_viewer import FILTER_TAGS, MODES


class FileWindow(Window):
    """A file in a viewer window: F3, and File > View > As Text / As Hex.

    Raises ``OSError`` from the constructor if *path* cannot be read, so the
    caller can say so before a window that shows nothing is opened.  Given
    the *source*, a ``ViewSource`` opened on a thread (``open_viewer``), the
    window opens nothing itself.
    """

    def __init__(self, path: Path | str, *, mode: str | None = None, source: Any = None,
                 **kwargs: Any) -> None:
        super().__init__(**kwargs)
        # Seeded, never bound: the viewer navigates both.  No mode asked for
        # is the Editor/Viewer setup's *Hex mode*.
        if mode is None:
            mode = "hex" if SETTINGS.viewer.hex_mode else "text"
        self.viewer.open(path, source=source)
        self.viewer.mode = mode
        self.viewer.wrap = SETTINGS.viewer.wrap_lines
        if mode == "hex":
            self.viewer.cursor = 0
        # ``TWindow.Init(R, FileName, 0)``: the title is the whole name.
        self.title = str(self.viewer.path)
        self.info.tooltip = self.viewer.info_tooltip()
        fill_file_types(self.view_menu_file_type, self)
        self.options.items = viewer_items(self.viewer)

    def take_keyboard(self) -> None:
        # Not from ``mounted()``: that runs inside ``Desktop.open``'s ``add()``,
        # before ``activate`` has saved which panel the window below had, so
        # closing this one would hand the keyboard to the left panel.
        self.viewer.focus()

    def list_name(self) -> str:
        """Window > List's line: DN's ``dlViewFile``, ``View - `` and the name."""
        return tr("View - {path}").format(path=self.viewer.path)

    def short_name(self) -> str:
        """The window strip's: the file's name alone."""
        return PurePosixPath(str(self.viewer.path)).name

    # -- the File View History -------------------------------------------------

    def remember_history(self) -> None:
        """``StoreViewInfo``: this file's record, as the viewer is now."""
        viewer = self.viewer
        if not SETTINGS.interface.track_viewing or viewer.path is None:
            return
        if getattr(self, "use_set", None) is not None or viewer.remote:
            return  # a file on another drive: no place here to come back to
        ViewRecord.store(
            viewer.path,
            **window_values(self),
            mode=viewer.mode,
            wrap=viewer.wrap,
            filter=viewer.filter,
            highlight=viewer.syntax_highlight,
            file_type=viewer.file_type,
            rendered="on" if viewer.rendered else "off",
            top=viewer.top,
            x_delta=viewer.x_delta,
            cursor=viewer.cursor,
        )

    def recall_history(self, *, keep_mode: bool = False) -> None:
        """``ViewFile``: put the window and the viewer back as the record says.

        Called once the window is on its desktop, whose size the rectangle is
        scaled to.  A file with no record gets one now.  The rectangle, scroll
        and cursor come back only under *Store viewer position*.  A position
        past the end of a file that has since shrunk starts it from the top, as
        DN's ``fPos+fBufPos > FileSize`` did.  With *keep_mode* -- As Text / As Hex
        asked for one -- the record's mode gives way.
        """
        viewer = self.viewer
        if not SETTINGS.interface.track_viewing or viewer.path is None or viewer.remote:
            return
        record = ViewRecord.find(viewer.path)
        if record is None:
            self.remember_history()
            return
        if not keep_mode and record.mode in MODES:
            viewer.mode = record.mode
        viewer.wrap = record.wrap
        viewer.syntax_highlight = record.highlight
        viewer.file_type = record.file_type
        if record.rendered in ("on", "off"):
            viewer.rendered = record.rendered == "on"
        if 0 <= record.filter < len(FILTER_TAGS):
            viewer.filter = record.filter
        # *Store viewer position*: without it the file opens from the top, in
        # the window it was given.
        if not SETTINGS.interface.store_viewer_position:
            return
        place_window(self, record)
        fits = record.top <= viewer.size
        viewer.x_delta = record.x_delta if fits and viewer.mode == "text" else 0
        viewer.cursor = min(record.cursor, max(0, viewer.size - 1)) if fits else 0
        viewer.seek(record.top if fits else 0)

    def close(self) -> None:
        # ``TFileViewer.Valid(cmClose)``: the record is written on the way out.
        if self.parent is not None:
            self.remember_history()
        super().close()
        use = getattr(self, "use_set", None)
        if use is not None:
            import asyncio

            from navigator.lib.drives import usefile

            self.use_set = None
            asyncio.get_running_loop().run_in_executor(None, usefile.discard, use)

    async def on_close_viewer(self, event: CloseViewer) -> bool:
        """F3 again: Midnight Commander's way out, beside DN's Esc."""
        self.close()
        return True

    # -- the switches ----------------------------------------------------------

    async def on_unwrap(self, event: Unwrap) -> bool:
        self.viewer.toggle_wrap()
        return True

    async def on_switch_high_light(self, event: SwitchHighLight) -> bool:
        """View > *Syntax highlight*: the editor's ``cmSwitchHighLight``, which
        DN's viewer did not have."""
        self.viewer.syntax_highlight = not self.viewer.syntax_highlight
        return True

    async def on_switch_rendered(self, event: SwitchRendered) -> bool:
        """Shift+F4, View > *Markup view*: a departure, DN's viewer had none."""
        self.viewer.toggle_rendered()
        return True

    async def on_switch_hidden_chars(self, event: SwitchHiddenChars) -> bool:
        """View > *Hidden characters*: a departure, as the editor's."""
        self.viewer.show_hidden = not self.viewer.show_hidden
        return True

    async def on_set_file_type(self, event: SetFileType) -> bool:
        """View > *File type*."""
        self.set_file_type(event.file_type)
        return True

    async def on_choose_file_type(self, event: ChooseFileType) -> bool:
        """Ctrl+Shift+H: the same menu in a box of its own."""
        self.spawn(self._choose_file_type())
        return True

    async def _choose_file_type(self) -> None:
        file_type = await choose_file_type(self)
        if file_type is not None:
            self.set_file_type(file_type)

    def set_file_type(self, file_type: str) -> None:
        """The text coloured as *file_type*, highlighting switched on for a
        language, and the choice kept in the view history straight away."""
        viewer = self.viewer
        viewer.file_type = file_type
        if file_type:
            viewer.syntax_highlight = True
        self.remember_history()

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

    def checks(self, command: Command) -> bool | None:
        """The *View* menu ticks the mode, the filter and wrapping in force."""
        if isinstance(command, SetViewMode):
            return self.viewer.mode == command.mode
        if isinstance(command, SetViewFilter):
            return self.viewer.filter == command.filter
        if isinstance(command, Unwrap):
            return self.viewer.wrap
        if isinstance(command, SwitchHighLight):
            return self.viewer.syntax_highlight
        if isinstance(command, SwitchHiddenChars):
            return self.viewer.show_hidden
        if isinstance(command, SwitchRendered):
            return self.viewer.rendered
        if isinstance(command, SetFileType):
            return self.viewer.file_type == command.file_type
        return super().checks(command)

    def refusal(self, command: Command) -> str:
        """F5 is hex and dump only, and F2 text only, as ``Draw`` switched them.
        *Markup view* is text only too, and wants a file no bigger than
        ``RENDER_LIMIT``; while it renders, Wrap and Hidden
        characters have nothing to act on."""
        text_only = tr("Only in the text view")
        if isinstance(command, GotoAddress):
            return tr("Only in the hex and dump views") if self.viewer.mode == "text" else ""
        if isinstance(command, SwitchRendered):
            if self.viewer.mode != "text":
                return text_only
            return "" if self.viewer.can_render else tr("Not a markup file, or too big to render")
        if isinstance(command, (Unwrap, SwitchHiddenChars)) and self.viewer.rendering:
            return tr("Not while the markup is rendered")
        if isinstance(command, (Unwrap, SwitchHighLight, SwitchHiddenChars, SetFileType, ChooseFileType)):
            return "" if self.viewer.mode == "text" else text_only
        if isinstance(command, (ContinueSearch, ReverseSearch, SearchAgain)):
            return "" if viewer_model.last_search is not None else tr("Nothing has been searched for yet")
        return super().refusal(command)

    async def on_bar_scroll(self, event: ScrollEvent) -> bool:
        """The scroll bar was worked: its value is a byte offset, snapped to a row."""
        self.viewer.seek(event.value)
        return True

    async def on_mouse_click(self, event: MouseClickEvent) -> bool:
        """A press on ``{Markdown}`` after the info line switches it."""
        mark = self.md_mark
        if (event.action == "press" and event.button == "left" and mark.width
                and event.y == mark.y and mark.x <= event.x < mark.x + mark.width
                and self.enables(SwitchRendered())):
            self.viewer.toggle_rendered()
            return True
        return await super().on_mouse_click(event)

    async def on_double_click(self, event: DoubleClickEvent) -> bool:
        """A double click on the ``[<=>]`` at the info line's start toggles wrap."""
        if event.y == self.height - 1 and 1 <= event.x < 6 and self.viewer.mode == "text":
            self.viewer.toggle_wrap()
            return True
        return await super().on_double_click(event)

    # -- goto ------------------------------------------------------------------

    async def on_goto_address(self, event: GotoAddress) -> bool:
        self.spawn(self.goto_address())
        return True

    async def goto_address(self) -> None:
        from navigator.widgets.viewer.goto_dialog import GotoDialog

        address = await GotoDialog().execute(self.application)
        if address is None:
            return
        viewer = self.viewer
        address = min(max(0, address), max(0, viewer.size - 1))
        viewer.cursor = address
        viewer.seek(address)
        viewer.cursor = address
        viewer.follow_cursor()

    # -- searching -------------------------------------------------------------

    # -- File > Save as and Encoding -------------------------------------------------

    async def on_save_view_as(self, event: SaveViewAs) -> bool:
        self.spawn(self.save_as())
        return True

    async def on_choose_encoding(self, event: ChooseEncoding) -> bool:
        self.spawn(self.choose_encoding())
        return True

    async def choose_encoding(self) -> None:
        """Shift+F6: ``LoadXlatTable`` -- the code pages in a box, the one in
        use marked.  DN offered its ``XLT\\*.XLT`` files and Shift+F6 again
        put the table away; here *UTF-8* is that, first in the box."""
        from navml.widgets.menu.popup_menu import PopupMenu
        from navml.widgets.menu.sub_menu import SubMenu

        viewer = self.viewer
        codecs = [codec for codec, _ in viewer_model.ENCODINGS]
        menu = SubMenu()
        items = [menu.add_item(caption) for _, caption in viewer_model.ENCODINGS]
        title = tr("Encoding")
        width, height = PopupMenu.measure(menu, self.application, self, title)
        ox, oy = self.offset()
        x = ox + self.x + max(0, (self.width - width) // 2)
        y = oy + self.y + max(0, (self.height - height) // 2)
        box = PopupMenu(menu, x, y, current=codecs.index(viewer.encoding), behind=self,
                        title=title)
        chosen = await box.execute(self.application)
        if chosen is not None:
            viewer.set_encoding(codecs[items.index(chosen)])

    async def save_as(self) -> None:
        """Shift+F5: ``cmSaveAll`` -- *Save File As*, and the file written
        there through the encoding, as DN wrote it through its ``Xlat``
        table: a file read in a code page is written in UTF-8.  On a thread,
        and the panels showing where it went look again (``cmRereadDir``)."""
        import asyncio

        from navml.widgets.dialog.file_dialog import FileDialog

        viewer = self.viewer
        source = viewer.source
        app = self.application
        if source is None or viewer.path is None:
            return
        dialog = FileDialog(
            title=tr("Save File As"), label=tr("~S~ave File As"), history_id="edit_save",
            directory=viewer.path.parent, hidden=SETTINGS.system.show_hidden,
        )
        # A URL, or a place in an archive, goes as typed: to that drive.
        dialog.raw = lambda text: "://" in text or "#/" in text
        name = await dialog.execute(app)
        if not name:
            return
        from navigator.lib.drives import Location, drive_of

        place = Location.parse(name)
        if not place.is_local:
            reach = getattr(getattr(app, "shell", None), "reach", None)
            if reach is None or not await reach(place):
                return

        def there() -> bool:
            try:
                return drive_of(place).lexists(place)
            except OSError:
                return False

        target: Any = place.local if place.is_local else place
        if await asyncio.to_thread(there):
            answer = await Dialog(title=tr("Warning"),
                                  prompt=tr("File {name}\nalready exists.\nOK to overwrite it?").format(name=target.name),
                                  buttons="yes-no").execute(app)
            if answer is not True:
                return
        try:
            # A file read across a network is written from its drive, whole.
            data = source if viewer.remote else source.path
            try:
                await asyncio.to_thread(viewer_model.save_as, data, target, viewer.encoding)
            except OSError as error:
                from navigator.lib.system.elevate import ELEVATION, refused

                message = tr("Cannot write {path}: {error}").format(path=target, error=error.strerror or error)
                # Refused permission on the disk: *As root* (a departure;
                # :mod:`navigator.lib.system.elevate`).
                if not (place.is_local and refused(error) and await asyncio.to_thread(ELEVATION.available)):
                    raise
                from navigator.widgets.file_ops.as_root import ask_as_root

                if not await ask_as_root(app, message):
                    return
                await asyncio.to_thread(viewer_model.save_as, data, target, viewer.encoding, as_root=True)
        except OSError as error:
            await Dialog(title=tr("Error"),
                         prompt=tr("Cannot write {path}: {error}").format(path=target, error=error.strerror or error),
                         buttons="ok").execute(app)
            return
        finally:
            if place.outer is not None:
                from navigator.lib.drives import archive

                await asyncio.to_thread(archive.release_unheld, place.outer)
        from navigator.widgets.editor.edit_window.edit_window import FileSaved

        await self.emit(FileSaved(target))

    async def on_search_for(self, event: SearchFor) -> bool:
        self.spawn(self.search_for())
        return True

    async def on_continue_search(self, event: ContinueSearch) -> bool:
        self.spawn(self.search_again(reverse=False))
        return True

    async def on_search_again(self, event: SearchAgain) -> bool:
        self.spawn(self.search_again(reverse=False))
        return True

    async def on_reverse_search(self, event: ReverseSearch) -> bool:
        self.spawn(self.search_again(reverse=True))
        return True

    async def search_for(self) -> None:
        """F7: ask, remember the answer for every viewer, and look."""
        from navigator.widgets.viewer.viewer_find_dialog import ViewerFindDialog

        search = await ViewerFindDialog(last=viewer_model.last_search).execute(self.application)
        if search is None:
            return
        viewer_model.last_search = search
        # A new search starts from the view rather than from the last hit.
        self.viewer.hit = None
        await self.search(search, search.backward)

    async def search_again(self, *, reverse: bool) -> None:
        """Shift+F7 and Ctrl+L the same way, Ctrl+F7 the other: DN's ``ContinueSearch``."""
        search = viewer_model.last_search
        if search is None:
            return
        await self.search(search, search.backward != reverse)

    async def search(self, search: ViewSearch, backward: bool) -> None:
        """Look for *search* from the hit, or from the view, and show what is found.

        Run on a thread, because a gigabyte is not searched between two frames;
        the loop keeps painting -- the clock keeps ticking -- while it looks.
        A search still going after ``navigator.lib.system.progress.PROGRESS_DELAY`` puts up *Search
        Progress*, and *Stop* in it ends the search where it is.
        """
        viewer = self.viewer
        source = viewer.source
        if source is None:
            return
        if viewer.hit is not None:
            start = viewer.hit[0] + (0 if backward else 1)
        elif viewer.mode == "text":
            start = viewer.top
        else:
            start = viewer.cursor
        pattern, span = search.compile(viewer.encoding)
        job = SearchJob()
        job.position = start
        total = source.size

        def make_box() -> Any:
            from navigator.widgets.viewer.search_progress import SearchProgress

            return SearchProgress(total=total, position=job.position)

        def refresh(box: Any) -> None:
            box.position = job.position

        found = await run_with_progress(
            self.application,
            lambda: source.find(pattern, start, backward=backward, span=span, job=job),
            job, make_box, refresh,
        )
        if job.stopped:
            # DN's -2: stopped, so nothing is said about finding nothing.
            return
        if found is None:
            await Dialog(
                title=tr("Search"), prompt=tr("Search string not found"), buttons="ok"
            ).execute(self.application)
            return
        viewer.show_hit(*found)

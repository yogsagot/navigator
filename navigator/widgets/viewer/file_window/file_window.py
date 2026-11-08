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
    FilterLines,
    FollowEnd,
    GotoAddress,
    HexMode,
    ReverseSearch,
    SearchAgain,
    SearchFor,
    SetViewFilter,
    SetViewMode,
    SwitchRendered,
    Unwrap,
    ViewAsTree,
    WriteModify,
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

#: How often *Follow end* looks at the file's size, in seconds.
FOLLOW_TICK = 0.5


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
        #: Bytes stored into a copy from another drive whose upload failed or
        #: was declined: closing asks to upload before the copy is deleted.
        self.unsent = False
        # Seeded, never bound: the viewer navigates both.  No mode asked for
        # is the Editor/Viewer setup's *Hex mode*.
        if mode is None:
            mode = "hex" if SETTINGS.viewer.hex_mode else "text"
        self.viewer.open(path, source=source)
        # Typing in hex types over bytes here, never in a quick view.
        self.viewer.hex_editing = True
        self.viewer.mode = mode
        self.viewer.wrap = SETTINGS.viewer.wrap_lines
        if mode == "hex":
            self.viewer.cursor = 0
        # ``TWindow.Init(R, FileName, 0)``: the title is the whole name.
        self.title = str(self.viewer.path)
        self.info.tooltip = self.viewer.info_tooltip()
        fill_file_types(self.view_menu_file_type, self)
        self.options.items = viewer_items(self.viewer)
        #: *Follow end*'s ticker while it follows, and whether a look at the
        #: size (or a scan of what was added) is still on a thread.
        self._follow_timer: Any = None
        self._follow_busy = False

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

    def unmounting(self) -> None:
        super().unmounting()
        self._stop_following()

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
        self.request_close()
        return True

    # -- hex editing ---------------------------------------------------------------

    def must_ask(self) -> bool:
        """``TFileViewer.Valid(cmClose)`` ran ``WriteModify``: bytes typed over
        in hex and not stored ask first -- and bytes stored into a copy from
        another drive that did not go back there."""
        return self.viewer.edited or self.unsent

    async def ask_to_close(self) -> bool:
        """DN's ``dlViewQuery``: store, lose, or stay open.  Bytes stored
        whose upload failed ask to upload instead
        (:func:`~navigator.widgets.drives.use_file.offer_upload`)."""
        use = getattr(self, "use_set", None)
        if not self.viewer.edited and use is not None:
            from navigator.widgets.drives.use_file import offer_upload

            return await offer_upload(self.application, use)
        answer = await Dialog(
            title=tr("Warning"),
            prompt=tr("Information was modified. Save changes?"),
            buttons="yes-no-cancel",
        ).execute(self.application)
        if answer is None:
            return False
        if answer is True:
            return await self.store()
        return True

    async def on_write_modify(self, event: WriteModify) -> bool:
        self.spawn(self.store())
        return True

    async def store(self) -> bool:
        """Shift+F2, ``WriteModify``: the bytes typed over written into the
        file, on a thread; True once they are.  A refusal on the disk offers
        *As root* (a departure; :mod:`navigator.lib.system.elevate`); a file
        fetched from another drive goes back there, as the editor's F2 puts
        it; the panels showing it look again (DN's ``RereadDirectory``)."""
        import asyncio

        viewer = self.viewer
        source = viewer.source
        app = self.application
        if source is None or not viewer.edited:
            return True
        edits = dict(source.edits)
        use = getattr(self, "use_set", None)
        place: Any = use.copies[0].origin if use is not None else getattr(source, "origin", source.path)
        try:
            try:
                await asyncio.to_thread(viewer_model.store_edits, source, edits)
            except viewer_model.FileChanged:
                raise
            except OSError as error:
                from navigator.lib.system.elevate import ELEVATION, refused

                if not (not viewer.remote and use is None and refused(error)
                        and await asyncio.to_thread(ELEVATION.available)):
                    raise
                from navigator.widgets.file_ops.as_root import ask_as_root

                message = tr("Could not write to file {path}: {error}").format(
                    path=place, error=error.strerror or error)
                if not await ask_as_root(app, message):
                    return False
                await asyncio.to_thread(viewer_model.store_edits, source, edits, as_root=True)
        except viewer_model.FileChanged:
            await Dialog(title=tr("Error"),
                         prompt=tr("{path} has changed since it was opened. Nothing was written.").format(path=place),
                         buttons="ok").execute(app)
            return False
        except OSError as error:
            await Dialog(title=tr("Error"),
                         prompt=tr("Could not write to file {path}: {error}").format(
                             path=place, error=error.strerror or error),
                         buttons="ok").execute(app)
            return False
        viewer.edits_stored(edits)
        if use is not None:
            # Stored only once they are there: a failed or declined upload
            # keeps the window asking, its copy kept.
            from navigator.widgets.drives.use_file import put_back

            self.unsent = not await put_back(app, use, ask=False)
            if self.unsent:
                return False
        from navigator.widgets.editor.edit_window.edit_window import FileSaved

        await self.emit(FileSaved(place))
        return True

    # -- Follow end and Filter lines ---------------------------------------------
    #
    # Departures, asked for: ``tail -f`` and ``grep`` in the viewer.  DN's took
    # a file's size once and hid characters, never lines.

    async def on_follow_end(self, event: FollowEnd) -> bool:
        """Ctrl+T: follow the end of the file as it grows, or stop."""
        viewer = self.viewer
        if viewer.follow:
            viewer.follow = False
            self._stop_following()
            return True
        viewer.follow = True
        if viewer.filtering:
            viewer.lines_grew()
        else:
            viewer.to_end()
        if self._follow_timer is None and self.application is not None:
            self._follow_timer = self.application.call_every(FOLLOW_TICK, self._follow_tick)
        return True

    def follow_refusal(self) -> str:
        """Why *Follow end* is greyed, or "": a file with a size to look at
        again, read here and not from a copy, no bytes typed over, not rendered."""
        viewer = self.viewer
        source = viewer.source
        if viewer.follow:
            return ""
        if source is None or not source.can_follow:
            return tr("This file has no size to follow")
        if getattr(self, "use_set", None) is not None:
            return tr("Not for a copy fetched from elsewhere")
        if viewer.edited:
            return tr("Not while bytes typed over are not stored")
        if viewer.rendering or viewer.showing_picture:
            return tr("Not while the markup is rendered")
        return ""

    def _stop_following(self) -> None:
        timer, self._follow_timer = self._follow_timer, None
        if timer is not None:
            timer.cancel()

    async def _follow_tick(self) -> None:
        """Every ``FOLLOW_TICK``: the size looked at again -- on a thread for a
        file across a network or read as root -- and, grown, the end shown and
        a filter read on over what was added."""
        import asyncio

        viewer = self.viewer
        source = viewer.source
        if not viewer.follow or source is None:
            # Scrolled back up, or the file let go: following is over.
            self._stop_following()
            return
        if self._follow_busy:
            return
        self._follow_busy = True
        try:
            try:
                if viewer.remote:
                    result = source.refresh(await asyncio.to_thread(source.stat_size))
                else:
                    result = source.refresh()
            except OSError:
                return  # gone for a moment (a log rotated): looked at next tick
            if viewer.source is not source:
                return
            viewer.resized(result)
            scan = viewer.lines
            if scan is None or result == "same":
                return
            from navigator.lib.viewer import lines

            if result == "shrank":
                scan = lines.LineScan(scan.pattern, viewer.encoding)
            await asyncio.to_thread(lines.scan, scan, source, source.size)
            if viewer.source is source and viewer.lines is not None:
                if scan is not viewer.lines:
                    viewer.show_lines(scan)
                else:
                    viewer.lines_grew()
        finally:
            self._follow_busy = False

    async def on_filter_lines(self, event: FilterLines) -> bool:
        self.spawn(self.filter_lines())
        return True

    async def filter_lines(self) -> None:
        """Ctrl+G: ask for the pattern, opened on the last one, and show the
        lines matching it.  An empty line puts the whole file back."""
        from navigator.lib.viewer import lines
        from navigator.widgets.viewer.filter_lines_dialog import FilterLinesDialog

        viewer = self.viewer
        last = viewer.lines.pattern if viewer.lines is not None else lines.last_pattern
        pattern = await FilterLinesDialog(last=last).execute(self.application)
        if pattern is None:
            return
        if pattern == "":
            # OK on an empty line: the filter taken off.
            viewer.leave_lines()
            return
        lines.last_pattern = pattern
        await self.show_lines(pattern)

    async def show_lines(self, pattern: Any) -> None:
        """The file scanned for *pattern* on a thread -- *Search Progress*
        after a moment, Stop in it showing nothing -- and its lines shown."""
        from navigator.lib.viewer import lines

        viewer = self.viewer
        source = viewer.source
        if source is None:
            return
        scan = lines.LineScan(pattern, viewer.encoding)
        total = source.size

        def make_box() -> Any:
            from navigator.widgets.viewer.search_progress import SearchProgress

            return SearchProgress(total=total, position=scan.position)

        def refresh(box: Any) -> None:
            box.position = scan.position

        try:
            await run_with_progress(self.application, lambda: lines.scan(scan, source, total),
                                    scan, make_box, refresh)
        except OSError as error:
            await Dialog(title=tr("Error"), prompt=tr("Cannot read the file: {error}").format(
                error=error.strerror or error), buttons="ok").execute(self.application)
            return
        if scan.stopped or viewer.source is not source:
            return
        if not scan.shown:
            await Dialog(title=tr("Filter lines"), prompt=tr("No lines match"),
                         buttons="ok").execute(self.application)
            return
        viewer.show_lines(scan)

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
        """Shift+F3, View > *Markup view*: a departure, DN's viewer had none.
        On a CSV or TSV, the database window on it in this one's place; on
        a JSON, YAML, TOML or XML file, the tree of its data."""
        if self.shows_table():
            self.spawn(self.as_table())
        elif self.shows_tree():
            self.spawn(self.as_tree())
        else:
            self.viewer.toggle_rendered()
        return True

    def shows_table(self) -> bool:
        """Whether Shift+F3 turns this file into a spreadsheet (``[viewer] table_masks``)."""
        from navigator.lib.viewer.table import is_table

        return self.viewer.path is not None and not self.viewer.remote and is_table(self.viewer.path.name)

    def shows_tree(self) -> bool:
        """Whether Shift+F3 shows this file's data as a tree
        (``[viewer] structured_masks``): a file on the disk, or a copy of one
        fetched from elsewhere."""
        from navigator.lib.viewer.structured import kind_by_name

        viewer = self.viewer
        return viewer.path is not None and not viewer.remote and kind_by_name(viewer.path.name) is not None

    async def on_view_as_tree(self, event: ViewAsTree) -> bool:
        """View > *Data tree*: the tree for any file on the disk -- read as
        its name or its first bytes say (``structured.kind_for``), so an HTML
        page too, whose Shift+F3 is the Markup view's."""
        from navigator.lib.viewer.structured import kind_for

        viewer = self.viewer
        if viewer.source is None or viewer.path is None:
            return True
        try:
            head = viewer.source.read(0, 64)
        except OSError:
            head = b""
        self.spawn(self.as_tree(kind_for(viewer.path.name, head)))
        return True

    async def as_tree(self, kind: str | None = None) -> None:
        """The structured view of this file -- read as *kind*, else as its
        name says -- where this window is; bytes typed in hex are asked about
        first.  A file that is not what it was read as is said so, and the
        text goes to the line the parser stopped on."""
        from navigator.lib.viewer.structured import ParseFailed
        from navigator.widgets.viewer.db_window.db_window import take_place
        from navigator.widgets.viewer.struct_window.struct_window import failure_text, open_tree

        viewer, desktop = self.viewer, self.desktop
        if desktop is None or viewer.source is None:
            return
        if self.must_ask() and not await self.ask_to_close():
            return
        try:
            window = await open_tree(desktop, viewer.source.path, kind)
        except ParseFailed as error:
            if error.offset is not None:
                viewer.set_mode("text")
                viewer.seek(error.offset)
            await Dialog(title=tr("Not a tree"), prompt=failure_text(error), buttons="ok").execute(self.application)
            return
        except OSError as error:
            await Dialog(title=tr("Error"), prompt=tr("Cannot read the file: {error}").format(
                error=error.strerror or error), buttons="ok").execute(self.application)
            return
        take_place(window, self)
        window.title = self.title
        window.use_set = getattr(self, "use_set", None)
        self.use_set = None
        viewer.edited = False
        self.close()

    async def as_table(self) -> None:
        """The database window on this CSV, at the row the view's top is in,
        where this window is; bytes typed in hex are asked about first."""
        from navigator.widgets.viewer.db_window.db_window import open_csv, take_place

        viewer, desktop = self.viewer, self.desktop
        if desktop is None or viewer.source is None:
            return
        if self.must_ask() and not await self.ask_to_close():
            return
        offset = viewer.top if viewer.mode == "text" else viewer.cursor
        try:
            window = await open_csv(desktop, viewer.source.path)
        except OSError as error:
            await Dialog(title=tr("Error"), prompt=tr("Cannot read the file: {error}").format(
                error=error.strerror or error), buttons="ok").execute(self.application)
            return
        if offset:
            import asyncio

            source = window.csv.source
            await asyncio.to_thread(source.wait)
            window.viewer.go(record=source.row_at(offset))
        take_place(window, self)
        window.title = self.title
        window.use_set = getattr(self, "use_set", None)
        self.use_set = None
        viewer.edited = False
        self.close()

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
        if isinstance(command, FollowEnd):
            return self.viewer.follow
        if isinstance(command, FilterLines):
            return self.viewer.filtering
        return super().checks(command)

    def refusal(self, command: Command) -> str:
        """F5 is hex and dump only, and F2 text only, as ``Draw`` switched them.
        *Markup view* is text only too, and wants a file no bigger than
        ``RENDER_LIMIT`` -- a picture, a terminal that draws it
        (``FileViewer.render_refusal``); while it renders, Wrap and Hidden
        characters have nothing to act on.  Shift+F2's *Store* waits for a
        byte typed over in hex."""
        if isinstance(command, WriteModify):
            return "" if self.viewer.edited else tr("Nothing has been typed over in hex")
        text_only = tr("Only in the text view")
        if isinstance(command, GotoAddress):
            return tr("Only in the hex and dump views") if self.viewer.mode == "text" else ""
        if isinstance(command, SwitchRendered) and self.viewer.filtering:
            return tr("Not while lines are filtered")
        if isinstance(command, SwitchRendered):
            if self.shows_table() or self.shows_tree():
                return ""
            if self.viewer.mode != "text":
                return text_only
            return self.viewer.render_refusal()
        if isinstance(command, FollowEnd):
            return self.follow_refusal()
        if isinstance(command, ViewAsTree):
            if self.viewer.remote:
                return tr("Not for a file read across a network")
            return "" if self.viewer.source is not None else tr("Nothing is open")
        if isinstance(command, FilterLines):
            if self.viewer.mode != "text":
                return text_only
            if self.viewer.rendering or self.viewer.showing_picture:
                return tr("Not while the markup is rendered")
            return ""
        if isinstance(command, (Unwrap, SwitchHiddenChars)) and self.viewer.filtering:
            return tr("Not while lines are filtered")
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

    async def on_hbar_scroll(self, event: ScrollEvent) -> bool:
        """The bottom bar was worked (a departure, as the editor's): its value
        is the column the rows start at."""
        self.viewer.x_delta = max(0, event.value)
        return True

    async def on_mouse_click(self, event: MouseClickEvent) -> bool:
        """A press on ``{Markdown}`` after the info line switches it."""
        mark = self.md_mark
        if (event.action == "press" and event.button == "left" and mark.width
                and event.y == mark.y and mark.x <= event.x < mark.x + mark.width
                and self.enables(SwitchRendered())):
            if self.shows_tree():
                self.spawn(self.as_tree())
            else:
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
        put the table away; here *UTF-8* is that, first in the box.  The code
        pages are a submenu a group (``encoding_menu``), and the box opens with
        the one in use dropped and selected."""
        from navml.widgets.menu.popup_menu import PopupMenu
        from navml.widgets.menu.sub_menu import SubMenu

        from navigator.lib import codepages
        from navigator.widgets import encoding_menu

        viewer = self.viewer
        menu = SubMenu()
        filled = encoding_menu.fill(menu, [viewer_model.ENCODINGS[0]], codepages.ONE_BYTE)
        title = tr("Encoding")
        width, height = PopupMenu.measure(menu, self.application, self, title)
        ox, oy = self.offset()
        x = ox + self.x + max(0, (self.width - width) // 2)
        y = oy + self.y + max(0, (self.height - height) // 2)
        index, at = filled.places.get(viewer.encoding, (0, -1))
        box = PopupMenu(menu, x, y, current=index, behind=self, title=title,
                        submenu=(index, at) if at >= 0 else None)
        chosen = filled.key_of(await box.execute(self.application))
        if chosen is not None:
            viewer.set_encoding(chosen)

    async def save_as(self) -> None:
        """Shift+F5: ``cmSaveAll``, DN's ``SaveFile`` -- *Save File As*.

        A file read in a code page asks first, as DN asked about its ``Xlat``
        table (``dlViewSaveXlat``): *Yes* writes it in UTF-8, *No* as its
        bytes are.  Esc there saves nothing, a departure: DN's Yes/No box took
        Esc for No and went on writing, and a box put away should not write a
        file.  A file already there is ``dlED_OverQuery``: *Yes* replaces it,
        *Append* adds to its end, Cancel writes nothing.  At most the size the
        file had when the save began is copied, as DN read up to its ``Sz``.
        On a thread, and the panels showing where it went look again
        (``cmRereadDir``)."""
        import asyncio

        from navml.widgets.dialog.file_dialog import FileDialog

        viewer = self.viewer
        source = viewer.source
        app = self.application
        if source is None or viewer.path is None:
            return
        codec = viewer.encoding
        if codec != "utf-8":
            name = dict(viewer_model.ENCODINGS)[codec].split()[0]
            translate = await Dialog(title=tr("Confirmation"),
                                     prompt=tr("Save the file translated\nfrom {encoding} to UTF-8?").format(encoding=name),
                                     buttons="yes-no-cancel").execute(app)
            if translate is None:
                return
            if translate is False:
                codec = "utf-8"
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
        append = False
        if await asyncio.to_thread(there):
            query = Dialog(title=tr("Warning"),
                           prompt=tr("File {name}\nalready exists.\nOK to overwrite it?").format(name=target.name),
                           buttons="yes-no-cancel")
            query.no.text = tr("A~p~pend")
            answer = await query.execute(app)
            if answer is None:
                return
            append = answer is False
        limit = viewer.size
        try:
            # A file read across a network is written from its drive, whole.
            data = source if viewer.remote else source.path
            try:
                await asyncio.to_thread(viewer_model.save_as, data, target, codec,
                                        append=append, limit=limit)
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
                await asyncio.to_thread(viewer_model.save_as, data, target, codec, as_root=True,
                                        append=append, limit=limit)
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

        search = await ViewerFindDialog(last=viewer_model.last_search,
                                        encoding=self.viewer.encoding).execute(self.application)
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
        """Look for *search* from the hit while it shows, else from the view
        (DN's ``SearchX := FilePos+BufPos`` once scrolled away; hex from its
        cursor, which is drawn and which a hit puts on it), and show what is
        found -- or say *Search string not found* in DN's ``mfError`` box.

        Run on a thread, because a gigabyte is not searched between two frames;
        the loop keeps painting -- the clock keeps ticking -- while it looks.
        A search still going after ``navigator.lib.system.progress.PROGRESS_DELAY`` puts up *Search
        Progress*, and *Stop* in it ends the search where it is.
        """
        viewer = self.viewer
        source = viewer.source
        if source is None:
            return
        if viewer.hit_showing():
            start = viewer.hit[0] + (0 if backward else 1)
        elif viewer.mode == "text":
            start = viewer.top
        else:
            start = viewer.cursor
        pattern, span = search.compile(viewer.encoding)
        job = SearchJob()
        job.position = start
        total = source.size
        # The bytes typed over in hex, as they are now: the thread's own copy.
        edits = dict(source.edits)

        def make_box() -> Any:
            from navigator.widgets.viewer.search_progress import SearchProgress

            return SearchProgress(total=total, position=job.position)

        def refresh(box: Any) -> None:
            box.position = job.position

        found = await run_with_progress(
            self.application,
            lambda: source.find(pattern, start, backward=backward, span=span, job=job, edits=edits),
            job, make_box, refresh,
        )
        if job.stopped:
            # DN's -2: stopped, so nothing is said about finding nothing.
            return
        if found is None:
            await Dialog(
                title=tr("Error"), prompt=tr("Search string not found"), buttons="ok"
            ).execute(self.application)
            return
        viewer.show_hit(*found)

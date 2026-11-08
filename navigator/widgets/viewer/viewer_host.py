"""The view commands, for whatever holds a ``FileViewer`` as ``host.viewer``.

DN's ``TFileViewer.HandleEvent`` (``FVIEWER.PAS``) handled these itself --
``cmUnWrap``, ``cmHexMode``, ``cmAddFilter``, ``cmGotoCell``, ``cmSearchFor``,
``cmContinueSearch``/``cmReverseSearch``, ``cmLoadXlatTable`` and ``cmSaveAll``
-- so the F3 window and the Ctrl+Q quick view, both a ``TFileViewer``, had
them alike.  Here they are functions both hosts' handlers call
(``FileWindow`` and ``QuickViewer``): the viewer has the keys that move, and
whoever holds it the ones the status line names, with the dialogs they open.
Functions, not a mixin, because a component's hand-written half has exactly
one base, its markup's (``ContextMenuHost``'s ``open_on_click`` is the same
shape, for ``InputLine``).

The handlers start these, never await them, for the reason
``Manager.on_make_directory`` gives: a handler that waits on a dialog holds
the only consumer of the queue the dialog's keys arrive on.
"""

from __future__ import annotations

from typing import Any

from navkit.commands import Command
from navkit.i18n import tr
from navml.widgets.dialog.dialog import Dialog

import navigator.lib.viewer as viewer_model
from navigator.lib.system.progress import run_with_progress
from navigator.lib.viewer import SearchJob, ViewSearch
from navigator.settings import SETTINGS
from navigator.widgets.editor.commands import SwitchHighLight
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


async def goto_address(host: Any) -> None:
    from navigator.widgets.viewer.goto_dialog import GotoDialog

    address = await GotoDialog().execute(host.application)
    if address is None:
        return
    viewer = host.viewer
    address = min(max(0, address), max(0, viewer.size - 1))
    viewer.cursor = address
    viewer.seek(address)
    viewer.cursor = address
    viewer.follow_cursor()


async def choose_encoding(host: Any) -> None:
    """Shift+F6: ``LoadXlatTable`` -- the code pages in a box, the one in
    use marked.  DN offered its ``XLT\\*.XLT`` files and Shift+F6 again
    put the table away; here *UTF-8* is that, first in the box.  The code
    pages are a submenu a group (``encoding_menu``), and the box opens with
    the one in use dropped and selected."""
    from navml.widgets.menu.popup_menu import PopupMenu
    from navml.widgets.menu.sub_menu import SubMenu

    from navigator.lib import codepages
    from navigator.widgets import encoding_menu

    viewer = host.viewer
    menu = SubMenu()
    filled = encoding_menu.fill(menu, [viewer_model.ENCODINGS[0]], codepages.ONE_BYTE)
    title = tr("Encoding")
    width, height = PopupMenu.measure(menu, host.application, host, title)
    ox, oy = host.offset()
    x = ox + host.x + max(0, (host.width - width) // 2)
    y = oy + host.y + max(0, (host.height - height) // 2)
    index, at = filled.places.get(viewer.encoding, (0, -1))
    box = PopupMenu(menu, x, y, current=index, behind=host, title=title,
                    submenu=(index, at) if at >= 0 else None)
    chosen = filled.key_of(await box.execute(host.application))
    if chosen is not None:
        viewer.set_encoding(chosen)


async def save_as(host: Any) -> None:
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

    viewer = host.viewer
    source = viewer.source
    app = host.application
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

    await host.emit(FileSaved(target))


async def search_for(host: Any) -> None:
    """F7: ask, remember the answer for every viewer, and look."""
    from navigator.widgets.viewer.viewer_find_dialog import ViewerFindDialog

    search = await ViewerFindDialog(last=viewer_model.last_search,
                                    encoding=host.viewer.encoding).execute(host.application)
    if search is None:
        return
    viewer_model.last_search = search
    # A new search starts from the view rather than from the last hit.
    host.viewer.hit = None
    await find(host, search, search.backward)


async def search_again(host: Any, *, reverse: bool) -> None:
    """Shift+F7 and Ctrl+L the same way, Ctrl+F7 the other: DN's ``ContinueSearch``."""
    search = viewer_model.last_search
    if search is None:
        return
    await find(host, search, search.backward != reverse)


async def find(host: Any, search: ViewSearch, backward: bool) -> None:
    """Look for *search* from the hit while it shows, else from the view
    (DN's ``SearchX := FilePos+BufPos`` once scrolled away; hex from its
    cursor, which is drawn and which a hit puts on it), and show what is
    found -- or say *Search string not found* in DN's ``mfError`` box.

    Run on a thread, because a gigabyte is not searched between two frames;
    the loop keeps painting -- the clock keeps ticking -- while it looks.
    A search still going after ``navigator.lib.system.progress.PROGRESS_DELAY`` puts up *Search
    Progress*, and *Stop* in it ends the search where it is.
    """
    viewer = host.viewer
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
        host.application,
        lambda: source.find(pattern, start, backward=backward, span=span, job=job, edits=edits),
        job, make_box, refresh,
    )
    if job.stopped:
        # DN's -2: stopped, so nothing is said about finding nothing.
        return
    if found is None:
        await Dialog(
            title=tr("Error"), prompt=tr("Search string not found"), buttons="ok"
        ).execute(host.application)
        return
    viewer.show_hit(*found)


#: The commands :func:`refusal` and :func:`checks` answer for.
COMMANDS = (AddFilter, ChooseEncoding, ContinueSearch, GotoAddress, HexMode, ReverseSearch, SaveViewAs,
            SearchAgain, SearchFor, SetViewFilter, SetViewMode, SwitchHighLight, Unwrap)


def checks(host: Any, command: Command) -> bool | None:
    """The *View* menu ticks the mode, the filter, wrapping and highlighting in force."""
    viewer = host.viewer
    if isinstance(command, SetViewMode):
        return viewer.mode == command.mode
    if isinstance(command, SetViewFilter):
        return viewer.filter == command.filter
    if isinstance(command, Unwrap):
        return viewer.wrap
    if isinstance(command, SwitchHighLight):
        return viewer.syntax_highlight
    return None


def refusal(host: Any, command: Command) -> str:
    """F5 is hex and dump only, and F2 text only, as ``Draw`` switched them;
    while lines are filtered or the markup renders, Wrap has nothing to act
    on.  The searches again want one made first."""
    viewer = host.viewer
    text_only = tr("Only in the text view")
    if isinstance(command, GotoAddress):
        return tr("Only in the hex and dump views") if viewer.mode == "text" else ""
    if isinstance(command, Unwrap) and viewer.filtering:
        return tr("Not while lines are filtered")
    if isinstance(command, Unwrap) and viewer.rendering:
        return tr("Not while the markup is rendered")
    if isinstance(command, (Unwrap, SwitchHighLight)):
        return "" if viewer.mode == "text" else text_only
    if isinstance(command, (ContinueSearch, ReverseSearch, SearchAgain)):
        return "" if viewer_model.last_search is not None else tr("Nothing has been searched for yet")
    return ""

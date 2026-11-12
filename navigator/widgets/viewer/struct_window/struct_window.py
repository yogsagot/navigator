"""The handlers behind ``struct_window.nml``: F3's structured view.

A departure, asked for: DOS Navigator's viewer showed bytes and lines only.
The model is :mod:`navigator.lib.viewer.structured`; the tree is
:class:`~navigator.widgets.viewer.struct_window.data_tree.DataTree`.  Opened
by :func:`open_tree` -- Shift+F3 in the text viewer (``FileWindow.as_tree``)
or F3 under ``[viewer] render_structured`` -- and back to the text by
Shift+F3 here, each in the other's place (``db_window.take_place``).
"""

from __future__ import annotations

import asyncio
from pathlib import Path, PurePosixPath
from typing import Any

from navkit.commands import Command
from navkit.i18n import tr
from navkit.text import escape_caption
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.tree_view import ChosenEvent
from navml.widgets.window import Window

from navigator.lib.viewer import structured
from navigator.widgets.viewer.commands import (
    ContinueSearch,
    CopyPath,
    CopyValue,
    ExpandAll,
    SearchAgain,
    SearchFor,
    ViewTreeAsText,
)
from navigator.widgets.viewer.struct_window.data_tree import root_node

#: What the window list calls each format.
FORMAT_NAMES = {"html": "HTML", "json": "JSON", "jsonl": "JSON", "yaml": "YAML", "toml": "TOML", "xml": "XML", "plist": "plist"}


class StructWindow(Window):
    """A document's data as a tree: *root* (the parsed file's root node),
    read from *path* as *kind*."""

    def __init__(self, root: structured.Node, path: Path | str, kind: str, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.path = Path(path)
        self.kind = kind
        self.tree.root = root_node(root)
        self.title = str(self.path)
        #: The copy of a file fetched from another drive, let go with the window.
        self.use_set: Any = None
        #: The last thing searched for here, and in which case.
        self._looked_for: tuple[str, bool] | None = None
        self._searching: asyncio.Task | None = None

    def list_name(self) -> str:
        """Window > List's line: ``Data - `` and the name, as a viewer's is ``View - ``."""
        return tr("{format} View - {path}").format(format=FORMAT_NAMES.get(self.kind, ""), path=self.path)

    def short_name(self) -> str:
        return PurePosixPath(str(self.path)).name

    def close(self) -> None:
        super().close()
        use, self.use_set = self.use_set, None
        if use is not None:
            from navigator.lib.drives import usefile

            asyncio.get_running_loop().run_in_executor(None, usefile.discard, use)

    # -- the tree's keys -------------------------------------------------------------

    async def on_chosen(self, event: ChosenEvent) -> bool:
        """Enter on a branch opens or closes it; on a value, nothing."""
        node = event.node
        if node is not None and node.data is not None and node.data.container:
            self.tree.toggle(node)
        return True

    async def on_expand_all(self, event: ExpandAll) -> bool:
        if not self.tree.expand_all():
            self.spawn(self._say(tr("Too many nodes to open at once: open the branches one by one"),
                                 tr("Expand all")))
        return True

    # -- copying -----------------------------------------------------------------------

    async def on_copy_path(self, event: CopyPath) -> bool:
        """Ctrl+Ins: the cursor's path to the clipboard."""
        text = self.tree.path_text()
        if text and self.application is not None:
            self.application.copy_to_clipboard(text)
        return True

    async def on_copy_value(self, event: CopyValue) -> bool:
        """Ctrl+Shift+C: the cursor's value to the clipboard, a branch as text."""
        node = self.tree.selected_data
        if node is not None and self.application is not None:
            self.application.copy_to_clipboard(node.value())
        return True

    # -- searching ----------------------------------------------------------------------

    async def on_search_for(self, event: SearchFor) -> bool:
        self.spawn(self.search_for())
        return True

    async def on_continue_search(self, event: ContinueSearch) -> bool:
        self.spawn(self.search_again())
        return True

    async def on_search_again(self, event: SearchAgain) -> bool:
        self.spawn(self.search_again())
        return True

    async def search_for(self) -> None:
        """F7: the viewer's *Find* box -- text, case, direction -- over the
        keys and the values, from the cursor on.  The text: a tree has no
        bytes, so what the *Hex* line made (``ViewSearch.data``) is not
        looked for here."""
        import navigator.lib.viewer as viewer_model
        from navigator.widgets.viewer.viewer_find_dialog import ViewerFindDialog

        search = await ViewerFindDialog(last=viewer_model.last_search).execute(self.application)
        if search is None:
            return
        viewer_model.last_search = search
        await self.search(search.what, case=search.case, backward=search.backward)

    async def search_again(self) -> None:
        import navigator.lib.viewer as viewer_model

        search = viewer_model.last_search
        if search is not None:
            await self.search(search.what, case=search.case, backward=search.backward)

    async def search(self, needle: str, *, case: bool = False, backward: bool = False) -> None:
        """The next node whose key or value holds *needle* -- every branch
        looked in, open or not -- shown, its branches opened; on a thread,
        since a large document has nodes by the million."""
        root = self.tree.root
        if root is None or not needle:
            return
        after = self.tree.selected_data
        found = await asyncio.to_thread(structured.find, root.data, after, needle, case=case,
                                        backward=backward, stopped=lambda: self.parent is None)
        if self.parent is None:
            return
        if found is None:
            await self._say(tr("Search string not found"), tr("Search"))
            return
        self.tree.show(found)

    async def _say(self, prompt: str, title: str | None = None) -> None:
        await Dialog(title=tr("Error") if title is None else title, prompt=prompt,
                     buttons="ok").execute(self.application)

    # -- back to the text -----------------------------------------------------------------

    async def on_view_tree_as_text(self, event: ViewTreeAsText) -> bool:
        self.spawn(self.as_text())
        return True

    async def as_text(self) -> None:
        """Shift+F3: F3's text view of the same file in this window's place,
        on the cursor's line when the format said where it is (YAML)."""
        from navigator.lib.config.file_history import open_viewer
        from navigator.widgets.viewer.db_window.db_window import take_place

        desktop = self.desktop
        if desktop is None:
            return
        node = self.tree.selected_data
        offset = node.offset if node is not None else None
        try:
            window = await open_viewer(desktop, self.path, "text")
        except OSError as error:
            await self._say(tr("Cannot read the file: {error}").format(error=error.strerror or error))
            return
        if window is None:
            return
        take_place(window, self)
        window.title = self.title
        window.use_set, self.use_set = self.use_set, None
        if offset is not None:
            window.viewer.seek(offset)
        self.close()

    # -- greying -------------------------------------------------------------------------

    def refusal(self, command: Command) -> str:
        if isinstance(command, (CopyPath, CopyValue)) and self.tree.selected_data is None:
            return tr("Nothing is under the cursor")
        if isinstance(command, (ContinueSearch, SearchAgain)):
            import navigator.lib.viewer as viewer_model

            return "" if viewer_model.last_search is not None else tr("Nothing has been searched for yet")
        return super().refusal(command)


def read_tree(path: Path, kind: str) -> structured.Node:
    """*path* read and parsed as *kind*: on a thread.  Raises ``OSError``,
    and :class:`~navigator.lib.viewer.structured.ParseFailed`."""
    with open(path, "rb") as stream:
        data = stream.read(structured.STRUCT_LIMIT + 1)
    if len(data) > structured.STRUCT_LIMIT:
        raise structured.ParseFailed(
            tr("Too big to show as a tree: more than {size} MiB").format(size=structured.STRUCT_LIMIT >> 20))
    return structured.parse(data, kind)


async def open_tree(desktop: Any, path: Path | str, kind: str | None = None) -> StructWindow:
    """The structured view of *path* opened on *desktop*, zoomed, read as
    *kind* (else as its name says).  Raises ``OSError`` and ``ParseFailed``."""
    path = Path(path)
    kind = kind or structured.kind_by_name(path) or "json"
    root = await asyncio.to_thread(read_tree, path, kind)
    window = desktop.open(StructWindow(root, path, kind))
    if not window.zoomed:
        window.toggle_zoom()
    window.tree.focus()
    return window


def failure_text(error: structured.ParseFailed) -> str:
    """A parse error as a box says it: *Line 12, column 4: expected ','*."""
    if error.line:
        return tr("Line {line}, column {column}: {message}").format(
            line=error.line, column=error.column, message=escape_caption(error.message))
    return escape_caption(error.message)

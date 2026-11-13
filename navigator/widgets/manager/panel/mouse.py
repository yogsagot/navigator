"""The right and middle buttons, the context menu, dragging entries out, and pressing the info
lines.

A mixin of :class:`Panel` (``navkit.widget.Mixin``): methods only; its state,
keys and the listing are in ``panel.py``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from navkit.application import REPEAT_EVERY
from navkit.commands import key_label
from navkit.events import MouseClickEvent
from navkit.i18n import tr, tr_n

from navml.widgets.menu.commands import ShowContextMenu
from navml.widgets.menu.context_menu import ContextMenu
from navml.widgets.menu.context_menu.context_menu import open_on_click, open_on_key

from navigator.lib.drives.listing import DirEntry
from navigator.settings import SETTINGS
from navigator.widgets.manager.panel.drag import Dropped
from navigator.widgets.manager.panel.helpers import _archive_file

if TYPE_CHECKING:
    from navigator.widgets.manager.panel.panel import Panel as _Base
else:
    from navkit.widget import Mixin as _Base


class Mouse(_Base):
    """The right and middle buttons, the context menu, dragging entries out, and pressing the info"""

    # -- the right button -----------------------------------------------------
    #
    # File Manager Setup's *Right button*: the context menu (the default; see
    # ``ContextMenuHost``), or DOS Navigator's own use of it, which selected.

    def claims_middle_click(self, x: int, y: int) -> bool:
        """A row is the middle button's: it tags there (VTE pastes instead, see navkit)."""
        return not self.inert and self.index_at(x, y) is not None

    @staticmethod
    def _right_selects() -> bool:
        return SETTINGS.file_manager.right_button == "select"

    def _right_marking(self, event: MouseClickEvent) -> bool:
        """DN's right button: a press toggles the row's tag, and a drag gives
        every row it passes the same one.  The middle button always does this.

        ``FLPANELX.PAS``: ``MSelect`` when the right button is down,
        ``SelectFlag := not Selected`` from the row pressed, and the loop
        applying it to each row the pointer crosses; past the top or the
        bottom of the rows the list scrolls a row at a time, as it did.
        ``..`` is never tagged.
        """
        app = self.application
        if event.action == "press":
            if self.inert:
                return False
            self.quick_search = None
            index = self.index_at(event.x, event.y)
            if index is None:
                return True
            entry = self.items[index]
            if app is not None and app.focused is not self:
                self.focus()
            self.cursor = index
            flag = not self.is_marked(entry)
            self._tag_rows(index, index, flag)
            self._right_mark = (flag, index)
            if app is not None:
                # Held, it goes on: every move, and past the top or the bottom
                # every tick too, as DN's loop on evMouseMove+evMouseAuto did
                # with ``RepeatDelay := 0``.
                async def mark(x: int, y: int, auto: bool) -> None:
                    self._right_marking_at(x, y)

                def done() -> None:
                    self._right_mark = None

                app.hold_mouse(self, event, mark, delay=REPEAT_EVERY, moves=True, done=done)
            else:
                self._right_mark = None
            return True
        # A press of another button while marking, which the hold does not
        # take: the marking stays the hold's.
        return self._right_mark is not None

    def _right_marking_at(self, x: int, y: int) -> None:
        """The held right button at *x*, *y*: every row from the last one to
        the one under the pointer gets the flag, or one more past an edge."""
        if self._right_mark is None:
            return
        flag, last = self._right_mark
        index = self.index_at(x, y)
        if index is None:
            row = y - self.inset - self.header
            if row < 0 and last > 0:
                index = last - 1
            elif row >= self.rows and last < len(self.items) - 1:
                index = last + 1
            else:
                return
        if index != last:
            step = 1 if index > last else -1
            self._tag_rows(last + step, index, flag)
            self.cursor = index
            self._right_mark = (flag, index)

    def _shift_select(self, index: int) -> bool:
        """Shift+ or Ctrl+left click: tag every row from the cursor to the one clicked.

        A departure, asked for: DN's left button only moved the cursor.  The
        range takes both ends and adds to whatever was tagged (``..`` never),
        the cursor goes to the row clicked, and no drag starts.  Ctrl is the
        same because VTE (xfce4-terminal) never reports Shift+click.  A
        Ctrl+click on the cursor's own row tags nothing, and the tags before
        a Ctrl+click are kept in ``_before_range`` so that a Ctrl+double click
        (DN's Insert name) can put them back.
        """
        app = self.application
        if app is not None and app.focused is not self:
            self.focus()
        start = self.cursor if 0 <= self.cursor < len(self.items) else index
        if start != index or self._before_range is None or self._before_range[0] != index:
            # A second press on the row just clicked keeps the first's note,
            # which is what a double click puts back.
            self._before_range = (index, self.marked)
        if start != index:
            self._tag_rows(start, index, True)
        self.cursor = index
        return True

    def _tag_rows(self, first: int, last: int, flag: bool) -> None:
        """Tag (*flag*) or untag every row from *first* to *last*, either way round."""
        low, high = min(first, last), max(first, last)
        keys = {item.key for item in self.items[low:high + 1] if item.name != ".."}
        if keys:
            self.marked = (self.marked | keys) if flag else (self.marked - keys)

    # -- the context menu -------------------------------------------------------
    #
    # ``ContextMenuHost``'s hooks and handlers, written out as ``InputLine``'s
    # are: a component's hand-written half has one base, its markup's.

    async def on_context_menu(self, event: Any) -> bool:
        """Declined while the right button selects, which the press did;
        else the cursor to the click and the menu at the pointer."""
        if self._right_selects():
            return False
        return open_on_click(self, event)

    async def on_show_context_menu(self, command: ShowContextMenu) -> bool:
        """The Menu key or Shift+F10: the menu at :meth:`context_point`."""
        return open_on_key(self)

    def prepare_context(self, x: int, y: int) -> None:
        """The cursor to the row clicked, as a left click puts it; the tags
        stay, and the menu acts on them when there are any."""
        self.quick_search = None
        index = self.index_at(x, y)
        if index is not None:
            self.cursor = index

    def context_point(self) -> tuple[int, int]:
        """Under the cursor's row, a little way in from its name."""
        row = self.cursor - self.scroll + self.inset + self.header
        if self.view_mode == "list":
            for first, left, width in self.list_columns:
                if first <= self.cursor < first + self.rows:
                    return left + 2, self.cursor - first + self.inset + self.header + 1
        return 3, min(max(row + 1, 0), max(0, self.height - 1))

    def context_menu(self) -> ContextMenu:
        """The File menu's everyday operations, for what the click is on.

        What an operation acts on is DN's ``GetSelection``: the tagged
        entries when there are any, else the one at the cursor.  So *View*
        and *Edit* are offered for a file with nothing tagged, the copy, move,
        link, erase and attribute operations for any selection, *Count
        directory length* for a directory, and *Make directory* and the
        selection's three always.  Whoever runs the File menu -- ``Manager``
        -- runs these, from this panel, and greys what does not apply.
        Built each time, so its captions follow the language.
        """
        from navigator.widgets.manager.commands import (
            ArcTest,
            ChangeAttributes,
            ChangeInactive,
            Copy,
            CountLength,
            CutToClipboard,
            Delete,
            Edit,
            EditLinkTarget,
            ExtractArchive,
            ExtractTo,
            GoToFile,
            InvertSelection,
            LinkAbsolute,
            LinkRelative,
            MakeDirectory,
            MakeLink,
            MountImage,
            OpenWith,
            PasteFromClipboard,
            PutInClipboard,
            RenameMove,
            RestoreTrash,
            SelectAll,
            SelectGroup,
            ShowHardLinks,
            UnmountImage,
            UnselectGroup,
            View,
        )
        from navigator.widgets.shell.commands import InsertName, InsertPath

        menu = ContextMenu()
        entry = self.selected
        tagged = bool(self.marked)
        on_parent = entry is None or entry.name == ".."
        if self.found is not None and not on_parent:
            # A *Find:* listing's Enter and Shift+Enter -- a departure, asked
            # for: DN had them on no menu.
            menu.add_item(tr("Go to ~f~ile"), GoToFile, "Enter")
            menu.add_item(tr("Show in ~o~ther panel"), ChangeInactive)
            menu.add_line()
        if (tagged or not on_parent) and self.location.site.scheme == "trash" and self.location.is_root:
            # The Trash (not DN's): what it is there for.
            menu.add_item(tr("Restore from Tras~h~"), RestoreTrash)
            menu.add_line()
        if not tagged and not on_parent and not entry.is_dir:
            # ``w``, not the File menu's ``v``: *Invert selection* has that here.
            menu.add_item(tr("Vie~w~"), View)
            menu.add_item(tr("~E~dit"), Edit)
            # The desktop's applications (``gio``, KIO): not DN's, and only
            # where there are some to open it in.
            from navigator.lib.system import desktop

            if desktop.program() is not None and desktop.graphical():
                menu.add_item(tr("Ope~n~ with..."), OpenWith)
            menu.add_line()
        if tagged or not on_parent:
            menu.add_item(tr("~C~opy..."), Copy)
            menu.add_item(tr("~R~ename/Move..."), RenameMove)
            menu.add_item(tr("Create link~s~..."), MakeLink)
            if any(item.is_link for item in (self.marked_entries if tagged else [entry])):
                # File > Symlinks' three, only where there is a link to change.
                menu.add_item(tr("Edit lin~k~ target..."), EditLinkTarget)
                menu.add_item(tr("Make relative"), LinkRelative)
                menu.add_item(tr("Make absolute"), LinkAbsolute)
            if not tagged and not on_parent and not entry.is_dir and entry.nlink > 1 and self.found is None:
                # A file with other names: File > Links' *Show hard links*.
                menu.add_item(tr("Show hard links"), ShowHardLinks)
            menu.add_item(tr("~D~elete"), Delete)
            menu.add_item(tr("File ~A~ttributes..."), ChangeAttributes)
            menu.add_line()
        # The clipboard's three, a departure as the keys are; theirs are
        # ``by_key`` too, so named here.
        if tagged or not on_parent:
            menu.add_item(tr("Cop~y~ to clipboard"), PutInClipboard, key_label("ctrl+c"))
            menu.add_item(tr("Cut to c~l~ipboard"), CutToClipboard, key_label("ctrl+x"))
        menu.add_item(tr("Paste from clip~b~oard"), PasteFromClipboard, key_label("ctrl+v"))
        menu.add_line()
        # The archive's own two in one, and Shift+F2 on an archive outside one
        # -- a departure, asked for, as the menu is.  ``x`` for both: an
        # archive panel offers no *Extract archive*.
        if self.location.outer is not None:
            menu.add_item(tr("E~x~tract to..."), ExtractTo, "Shift-F2")
            menu.add_item(tr("Test arc~h~ive"), ArcTest)
            menu.add_line()
        elif any(_archive_file(item) for item in (self.marked_entries if tagged else [entry])):
            menu.add_item(tr("E~x~tract archive..."), ExtractArchive, "Shift-F2")
            menu.add_line()
        # Disk images (Enter's, ``udisks.attach_image``): not DN's.  The one at
        # the cursor is mounted if it is not, else -- or with the panel in one --
        # unmounted; never both for one image.
        from navigator.lib.system import udisks

        if self.image_here():
            menu.add_item(tr("Unmount image"), UnmountImage)
            menu.add_line()
        elif not tagged and self.image_file() is not None and udisks.program() is not None:
            menu.add_item(tr("Mount image"), MountImage)
            menu.add_line()
        if entry is not None and entry.is_dir:
            menu.add_item(tr("Count directory len~g~th"), CountLength)
        menu.add_item(tr("~M~ake directory"), MakeDirectory)
        menu.add_line()
        # Their keys are bound as ``by_key`` commands, which these are not, so
        # no live key is found: the keypad's, as the Panel menu writes them.
        menu.add_item(tr("Select grou~p~..."), SelectGroup, key_label("kp_plus"))
        menu.add_item(tr("~U~nselect group..."), UnselectGroup, key_label("kp_minus"))
        menu.add_item(tr("In~v~ert selection"), InvertSelection, key_label("kp_multiply"))
        menu.add_item(tr("Select all files"), SelectAll)
        # Ctrl+Enter and Ctrl+Shift+Enter, which DN had on no menu -- a
        # departure, asked for; the shell answers them.
        menu.add_line()
        menu.add_item(tr("~I~nsert name"), InsertName)
        menu.add_item(tr("Insert pa~t~h"), InsertPath)
        return menu

    def _dragging(self, event: MouseClickEvent) -> bool:
        """``DragMover``: the label follows the pointer, and the release drops."""
        from navigator.widgets.manager.panel.drag import TRASH, DragLabel, Dropped, drop_target, label_for

        drag, app = self._drag, self.application
        assert drag is not None
        ox, oy = self.offset()
        x, y = event.x + ox + self.x, event.y + oy + self.y
        label = drag["label"]
        if event.action == "move":
            if app is None:
                return True
            if label is None:
                # Given by an info line (``DragCurrent``...), else the row's.
                entries = drag["entries"] or self._drag_entries(drag["index"])
                if not entries:
                    self._drag = None
                    app.release_mouse()
                    return True
                drag["entries"] = entries
                label = drag["label"] = app.overlay(DragLabel(drag.get("text") or label_for(entries)))
            root = app.root
            label.place(x, y, root.width, root.height)
            return True
        # The release: the label goes, and the files go where it was dropped.
        self._drag = None
        if label is None or app is None:
            return True
        label.parent.remove(label)
        where = drop_target(app, x, y, self)
        if where == TRASH:
            self.spawn(self.emit(Dropped(self, tuple(drag["entries"]), None, False, trash=True)))
        elif where is not None:
            target, panel = where
            self.spawn(self.emit(Dropped(self, tuple(drag["entries"]), target, event.shift, panel,
                                           x=x, y=y)))
        return True

    def info_part_at(self, x: int, y: int) -> str | None:
        """The info line part under *x*, *y* (``current-file``,
        ``selected-files``, ``totals``, ``free-space``), ``"divider"`` for the
        divider row over them, or None."""
        index = self.info_line_at(x, y)
        if index is not None:
            return self._info_lines[index][1]
        if (self.info_height and SETTINGS.file_manager.info_divider
                and self.inset <= x < self.inset + self.inner_width
                and y == self.height - self.inset - self.info_height):
            return "divider"
        return None

    def _info_press(self, event: MouseClickEvent, part: str) -> bool:
        """``TInfoView.HandleEvent``: a press on the divider scrolls down while
        held -- tagging each row with the tagging button, DN's right one -- and
        one on *Current file*, *Selected* or *Totals* drags the cursor's file,
        the tagged ones or every one (``DragCurrent``/``DragSelected``/
        ``DragTotals``).  True when the press was the info lines'."""
        from navkit.application import REPEAT_EVERY

        app = self.application
        tagging = event.button == "middle" or (event.button == "right" and self._right_selects())
        if part == "divider":
            if event.button != "left" and not tagging:
                return False
            if not self.focus_within:
                # DN's ``GetState(sfActive+sfSelected)``: the press only selects.
                self.focus()
                return True
            if not self.items or app is None:
                return True
            current = self.selected
            flag = current is not None and not self.is_marked(current)

            async def step(x: int, y: int, auto: bool) -> None:
                if tagging:
                    self._tag_rows(self.cursor, self.cursor, flag)
                self.move_cursor(1)

            app.hold_mouse(self, event, step, delay=REPEAT_EVERY)
            if tagging:
                self._tag_rows(self.cursor, self.cursor, flag)
            self.move_cursor(1)
            return True
        if part not in ("current-file", "selected-files", "totals") or event.button != "left":
            return False
        if not SETTINGS.file_manager.drag_drop_columns or app is None:
            return False
        if part == "current-file":
            entry = self.selected
            entries = [] if entry is None or entry.name == ".." else [entry]
            text = None
        elif part == "selected-files":
            entries, text = list(self.marked_entries), None
        else:
            entries = [entry for entry in self.items if entry.name != ".."]
            text = tr_n("{n} file", "{n} files", len(entries))
        if entries:
            self._drag = {"index": None, "label": None, "entries": entries, "text": text}
            app.capture_mouse(self)
        return True

    def _drag_entries(self, index: int) -> list[DirEntry]:
        """``CM_DragDropper``'s files: the tagged ones when the row is tagged,
        else the row's own -- never ``..``."""
        if not 0 <= index < len(self.items):
            return []
        entry = self.items[index]
        if self.is_marked(entry):
            return self.marked_entries
        return [] if entry.name == ".." else [entry]

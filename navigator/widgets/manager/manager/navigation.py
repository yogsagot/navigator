"""Where the panels go: history, quick directories, remembered directories, bookmarks,
Change directory, Equalize panels.

A mixin of :class:`Manager` (``navkit.widget.Mixin``): methods only; its state,
keys and ``checks`` are in ``manager.py``.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import TYPE_CHECKING, Any

from navkit.i18n import tr

from navml.widgets.dialog.dialog import Dialog

from navigator.widgets.manager.commands import (
    ChangeDirectory,
    Delete,
    GoParent,
    GoToTreeDirectory,
    Rescan,
    JumpToDirectory,
    QuickChange,
    ToggleTree,
)

from navml.widgets.dialog.commands import QuickSearch

from navigator.widgets.manager.panel import Panel
from navigator.lib.drives import Location, drive_of
from navigator.lib.drives.location import shown
from navigator.settings import SETTINGS
from navigator.widgets.manager.manager.helpers import DELETE_BOOKMARK_KEY, EDIT_LINKS, LABEL_BOOKMARK_KEY, MOVE_BOOKMARK_KEYS, _move_keys, _remembered_tooltip, bookmark_menu, link_section

if TYPE_CHECKING:
    from navigator.widgets.manager.manager import Manager as _Base
else:
    from navkit.widget import Mixin as _Base


class Navigation(_Base):
    """Where the panels go: history, quick directories, remembered directories, bookmarks,"""

    # -- where the panels have been, and the quick directories ----------------------

    async def _go_to(self, panel: Panel, place: str, *, focus: bool = True) -> None:
        """*panel* to *place* (``cmChangeDirectory``), or why not.

        *place* is a directory's text as the histories keep it: a path, or a
        URL on another drive -- which, not open yet, is connected first.
        """
        target = Location.parse(str(place))
        if not target.is_local:
            # Not open yet: the shell connects (and asks what it must).
            reach = getattr(getattr(self.application, "shell", None), "reach", None)
            if reach is None or not await reach(target):
                return

        def there() -> bool:
            try:
                return drive_of(target).is_dir(target)
            except OSError:
                return False

        if not await asyncio.to_thread(there):
            await Dialog(title=tr("Error"), prompt=tr("Directory {place} is not there").format(place=place), buttons="ok"
                         ).execute(self.application)
            return
        panel.location = target
        if focus:
            panel.focus()

    async def on_jump_to_directory(self, event: JumpToDirectory) -> bool:
        """Alt+J: fzf over zoxide's directories and the panels' history (a
        departure), and the active panel to the one chosen -- connected first
        if it is on another drive, as Alt+Backspace's are."""
        shell = getattr(self.application, "shell", None)
        if shell is not None:
            panel = self.active_panel
            self.spawn(shell.jump_directory(lambda place: self.spawn(self._go_to(panel, place))))
        return True

    async def dir_history(self, panel: Panel) -> None:
        """Alt+Backspace: ``DirHistoryMenu`` -- the directories the panels have
        been to (Interface's *Track directories*, else DN's ``dlSetDirHistory``),
        and *panel* to the one chosen.  An empty history asks nothing."""
        from navml.history import HISTORY
        from navigator.widgets.manager.dir_history_dialog import DirHistoryDialog
        from navigator.widgets.manager.dir_history_dialog.dir_history_dialog import HISTORY_ID

        app = self.application
        if not SETTINGS.interface.track_directories:
            await Dialog(title=tr("Error"), prompt=tr('Set the interface option\n"Track directories" ON first'),
                         buttons="ok").execute(app)
            return
        if not HISTORY.entries(HISTORY_ID):
            return
        place = await DirHistoryDialog().execute(app)
        if place:
            await self._go_to(panel, place)

    # The quick directories are the bookmarks: DN's nine ``DirsToChange``
    # slots and its drive letters' box became one list (``navigator.lib.config.bookmarks``).

    async def on_quick_change(self, event: QuickChange) -> bool:
        """Alt+*N*: ``DoChange(DirsToChange[N])`` -- the *N*-th bookmark, with no
        box between; there being none that far, nothing is done."""
        from navigator.lib.config.bookmarks import bookmarks

        rows = bookmarks()
        if 0 < event.slot <= len(rows):
            self.spawn(self._go_to(self.active_panel, rows[event.slot - 1].path))
        return True

    async def store_quick_dir(self, panel: Panel, slot: int) -> None:
        """Alt+Shift+*N*: DN's ``dlPromptForQDir``, then the panel's directory
        bookmarked at place *N* (``place_bookmark``), so Alt+*N* comes back to it."""
        from navigator.lib.config.bookmarks import place_bookmark

        prompt = tr("Store this directory\nas bookmark {slot}?").format(slot=slot)
        if await self._ask_yes_no(prompt, tr("Confirm")) is not True:
            return
        place_bookmark(panel.location, slot)
        panel.invalidate()

    async def remember_directory(self, panel: Panel) -> None:
        """Panel > *Remember for this directory*: *panel*'s directory keeps
        what it is shown with, a box asking whether those below do too; or,
        remembered already, forgets it (``directory_settings``)."""
        from navigator.widgets.manager.remember_directory_dialog import RememberDirectoryDialog

        if panel.remembers_here:
            panel.forget_here()
            return
        answer = await RememberDirectoryDialog(str(panel.location)).execute(self.application)
        if answer is not None:
            panel.remember_here(answer["subdirs"])

    async def remembered_directories(self, panel: Panel) -> None:
        """Panel > *Remembered directories*: every directory with a record in
        a box over *panel*, placed as the bookmarks' is; Enter takes *panel*
        there, Del forgets one and opens the box again without it."""
        from navml.widgets.dialog.control.control import escape_caption
        from navml.widgets.menu.popup_menu import PopupMenu
        from navml.widgets.menu.sub_menu import SubMenu

        from navigator.lib.config import directory_settings

        app = self.application
        if app is None:
            return
        keep = 0
        home = str(Path.home())
        while True:
            rows = directory_settings.records()
            if not rows:
                await Dialog(title=tr("Remembered directories"),
                             prompt=tr("No directory has settings of its own"), buttons="ok").execute(app)
                return
            menu = SubMenu()
            for row in rows:
                shown = row.path
                if shown == home or shown.startswith(home + "/"):
                    shown = "~" + shown[len(home):]
                item = menu.add_item(escape_caption(shown))
                if row.subdirs:
                    item.key = tr("and below")
                item.tooltip = _remembered_tooltip(row)
            title = tr("Remembered directories")
            width, _ = PopupMenu.measure(menu, app, self, title)
            ox, oy = panel.offset()
            x = ox + panel.x + (panel.width - width) // 2
            y = oy + panel.y + 1
            box = PopupMenu(menu, x, y, current=min(keep, len(rows) - 1), behind=self, title=title,
                            hints=(("Del", tr("Forget")),), keys=(DELETE_BOOKMARK_KEY,))
            chosen = await box.execute(app)
            if box.pressed == DELETE_BOOKMARK_KEY:
                keep = box.selected
                if 0 <= keep < len(rows):
                    directory_settings.forget(rows[keep].path)
                    # A panel shown with it now is shown with what it falls back to.
                    for side in (self.left, self.right):
                        if side.remembered == rows[keep].path:
                            side.settle_directory()
                continue
            if chosen is None:
                return
            place = rows[menu.entries().index(chosen)].path
            if "://" in place:
                await self._go_to(panel, place)
                return
            panel.path = Path(place)
            panel.focus()
            return

    def _tree_menu(self) -> Any:
        """Ctrl+T's tree, right-clicked -- a departure, asked for, as every
        context menu is: where Enter goes, the tree read again, its quick
        search, and Ctrl+T's way back to the panel."""
        from navml.widgets.dialog.commands import QuickSearch
        from navml.widgets.menu.context_menu import ContextMenu

        menu = ContextMenu()
        menu.add_item(tr("~G~o to directory"), GoToTreeDirectory, "Enter")
        menu.add_item(tr("~R~e-read"), Rescan)
        menu.add_item(tr("Quick s~e~arch"), QuickSearch)
        menu.add_line()
        menu.add_item(tr("~C~lose tree"), ToggleTree)
        return menu

    async def on_rescan(self, event: Rescan) -> bool:
        found = self.active_panel.found
        if self.tree.focused:
            self.tree.reload()
        elif found is not None and found.command is not None:
            # A panelized command's listing is read again by running it again.
            self.spawn(self.panelize(self.active_panel, found.command))
        else:
            self.active_panel.reload()
        return True

    async def on_change_directory(self, event: ChangeDirectory) -> bool:
        # Started, not awaited, for the reason ``on_make_directory`` gives.
        self.spawn(self.change_directory(search=event.search))
        return True

    async def _change_side(self, side: str, focus: bool) -> None:
        """``ChangeDrvLeft``/``ChangeDrvRight``: the box for *side*'s panel --
        hidden or behind a view, it is asked first and the side changes only
        on a choice (``if S = '' then Exit``); the keyboard goes there only
        with *focus* (Shift held).  In Miller columns, the column browsed."""
        if self.miller_mode:
            await self.choose_bookmark(self.active_panel, focus=focus)
            return
        panel = self.left if side == "left" else self.right
        await self.choose_bookmark(panel, side=side, focus=focus)

    def bring_side(self, side: str) -> Panel:
        """*side*'s panel, showing: Alt+F1 and Alt+F2 change a panel, so one
        hidden by Ctrl+F1/F2 comes back, and the tree or quick view standing in
        its place gives way, as DN's ``_ChangeDrive`` replaced a drive that
        was not a disk.  In Miller columns, the column being browsed."""
        if self.miller_mode:
            return self.active_panel
        panel = self.left if side == "left" else self.right
        if self.hidden_side == side:
            self.show_side(side)
        if self.replaced is panel:
            self.switch_view(self.replacement)
        return panel

    async def choose_bookmark(self, panel: Panel, *, side: str | None = None, focus: bool = True) -> None:
        """The bookmarks in a box over *panel*, and *panel* goes where it says.

        DOS Navigator's ``SelectDrive``, placed as ``_ChangeDrive`` placed it:
        centred on the panel, one row under its top edge, with the panel's own
        entry selected.  The last entry adds the panel's directory, or removes
        it if it is bookmarked already; removing one opens the box again,
        without it, so several can go in a row.  A bookmark whose directory is
        gone -- a drive no longer mounted -- is greyed.

        Ctrl+Up and Ctrl+Down move the selected bookmark one place, and the
        box opens again with it still selected (DN's drive letters had an
        order of their own; this list has only the one its user gives it).
        F2 asks for the selected one's label, shown in place of its path, and
        Del removes it -- asked first while Confirmations' *Delete bookmark*
        is ticked (``_confirm_delete_bookmark``); *Remove this folder*, an
        entry chosen by name, never asks.

        Below the bookmarks, what is mounted now and not bookmarked
        (``mounted_places``), read each time the box opens; those entries are
        only places to go, and the three keys pass them by.

        *side* (Alt+F1/F2) is the side *panel* is on: hidden, or standing
        behind a view, it is shown or given back only once the box chose
        somewhere to go (``bring_side``), the box opening over the window
        meanwhile.  *focus* gives *panel* the keyboard when it moves.
        """
        from navml.widgets.menu.popup_menu import PopupMenu
        from navml.widgets.menu.sub_menu import SubMenu

        from navigator.lib.drives import profiles as link_profiles

        from navigator.lib.config.bookmarks import (
            add_bookmark, bookmarks, find_bookmark, key_of, label_bookmark, mounted_places,
            move_bookmark, remove_bookmark,
        )
        from navigator.widgets.manager.bookmark_label_dialog import BookmarkLabelDialog

        app = self.application
        if app is None:
            return

        def bring() -> None:
            # The box chose somewhere to go: the side shown, its panel back.
            if side is not None:
                self.bring_side(side)

        keep: int | None = None
        #: Where in the *Link* list to open again, after a key acted on it.
        reopen: int | None = None
        while True:
            rows = bookmarks()
            marked = {row.path for row in rows}

            def look(rows: list[Any] = rows) -> tuple[list[Path], set[str]]:
                # The mounts, and which places are there to go to, on a
                # thread: a dead network mount answers ``is_dir`` in minutes.
                mounts = mounted_places()
                places = [row.path for row in rows] + [str(path) for path in mounts]
                # A place on another drive is not looked for: that would
                # connect to it, for a box only opened to choose.
                return mounts, {place for place in places
                                if "://" in place or Path(place).is_dir()}

            found, present = await asyncio.to_thread(look)
            mounts = [path for path in found if key_of(path) not in marked]
            here = find_bookmark(panel.location)
            menu, toggle = bookmark_menu(rows, here is not None, mounts, present)
            links = link_section(menu, before=toggle, glyphs=self.glyphs)
            # The Trash (not DN's), under *Link*, before the line above the toggle.
            entries = menu.entries()
            trash_item = menu.add_item(tr("~T~rash"), before=entries[entries.index(toggle) - 1])
            # Nothing inside an archive is a place to come back to.
            toggle.disabled = panel.location.outer is not None
            if toggle.disabled:
                toggle.tooltip = tr("A place inside an archive cannot be bookmarked")
            else:
                # Which folder: the panel's, which the box does not otherwise name.
                toggle.tooltip = str(panel.location)
            link_menu = next(entry for entry in menu.entries() if isinstance(entry, SubMenu))
            # Entry by entry, where each one goes; None for a line and the toggle.
            places = [row.path for row in rows] + ([None] if rows and mounts else [])
            places += [key_of(path) for path in mounts]
            current = keep if keep is not None else next(
                (index for index, place in enumerate(places) if place == key_of(panel.location)),
                0,
            )
            # The layout settles in this batch's effects; a side just brought
            # back has to be where it will be before the box is placed by it.
            self.panels.arrange()
            title = tr("Bookmarks")
            # The keys the box takes on a bookmark, for the key bar, as the
            # *Link* list gives its own -- a departure, asked for.
            hints = (("F2", tr("Label")), ("Del", tr("Delete")), (_move_keys(self.glyphs), tr("Move"))) if rows else ()
            width, _ = PopupMenu.measure(menu, app, self, title)
            anchor = panel
            if side is not None:
                anchor = self if self.hidden_side == side else self.side_view(side)
            ox, oy = anchor.offset()
            x = ox + anchor.x + (anchor.width - width) // 2
            y = oy + anchor.y + 1
            submenu = None
            if reopen is not None:
                submenu = (menu.entries().index(link_menu), min(reopen, max(0, len(link_menu.entries()) - 1)))
            box = PopupMenu(menu, x, y, current=current, behind=self, title=title, hints=hints, submenu=submenu,
                            keys=(*MOVE_BOOKMARK_KEYS, LABEL_BOOKMARK_KEY, DELETE_BOOKMARK_KEY))
            chosen = await box.execute(app)
            reopen = None
            if box.pressed is not None and id(chosen) in links:
                # A key on the *Link* list: on its profile, and the box opens
                # again on the list, where the key was pressed.
                reopen = await self._profile_key(box.pressed, links[id(chosen)], chosen, link_menu)
                keep = menu.entries().index(link_menu)
                continue
            if box.pressed == DELETE_BOOKMARK_KEY:
                keep = box.selected
                if 0 <= keep < len(rows) and await self._confirm_delete_bookmark(rows[keep]):
                    remove_bookmark(rows[keep].path)
                    keep = min(keep, max(0, len(rows) - 2))
                continue
            if box.pressed == LABEL_BOOKMARK_KEY:
                keep = box.selected
                if 0 <= keep < len(rows):
                    dialog = BookmarkLabelDialog()
                    dialog.entry.value = rows[keep].label
                    dialog.entry.entry.select_all()
                    label = await dialog.execute(app)
                    if label is not None:
                        label_bookmark(rows[keep].path, label)
                continue
            if box.pressed is not None:
                keep = box.selected
                if 0 <= keep < len(rows):
                    by = -1 if box.pressed == "ctrl+up" else 1
                    if move_bookmark(rows[keep].path, by):
                        keep += by
                continue
            if chosen is None:
                return
            if chosen is trash_item:
                bring()
                await self.open_trash(panel, focus=focus)
                return
            if id(chosen) in links:
                bring()
                profile = links[id(chosen)]
                shell = getattr(self.application, "shell", None)
                if shell is not None:
                    if profile == EDIT_LINKS:
                        await shell.edit_links(panel)
                    elif isinstance(profile, str):  # *New ... link*, for that protocol
                        await shell.navy_link(panel, scheme=profile)
                    else:
                        await shell.go_remote(panel, link_profiles.location_of(profile))
                return
            if chosen is toggle:
                if here is None:
                    add_bookmark(panel.location)
                    return
                remove_bookmark(panel.location)
                keep = min(current, max(0, len(rows) - 2))
                continue
            place = places[menu.entries().index(chosen)]
            bring()
            if "://" in place:
                await self._go_to(panel, place, focus=focus)
                return
            panel.path = Path(place)
            if focus:
                panel.focus()
            return

    async def _confirm_delete_bookmark(self, row: Any) -> bool:
        """Whether Del may delete *row*: at once with Confirmations' *Delete
        bookmark* unticked, else when ``DeleteBookmarkDialog`` is answered
        *Yes* -- whose *Don't ask again* unticks it, saved, as Alt+X's does
        *Exit confirmation*."""
        if not SETTINGS.confirmations.delete_bookmark:
            return True
        from navigator.widgets.manager.delete_bookmark_dialog import DeleteBookmarkDialog

        answer = await DeleteBookmarkDialog(row.label or row.path).execute(self.application)
        if not answer:
            return False
        if not answer["ask_again"]:
            # A file that cannot be written only means the question comes back next time.
            SETTINGS.confirmations.delete_bookmark = False
            try:
                SETTINGS.save(section="confirmations")
            except OSError:
                pass
        return True

    async def _profile_key(self, key: str, profile: Any, item: Any, link_menu: Any) -> int:
        """One of the bookmarks' keys on an entry of the *Link* list: F2 edits
        the profile (the SSH link box, saving rather than connecting), Del
        removes it, unasked, as it removes a bookmark, and Ctrl+Up/Down move it.
        *New connection* takes none of them.  Answers where in the list to
        stand when the box opens again."""
        from navigator.lib.drives import profiles

        entries = link_menu.entries()
        index = entries.index(item) if item in entries else 0
        if profile is None or isinstance(profile, str):
            return index  # a *New ... link* takes no keys
        if key == DELETE_BOOKMARK_KEY:
            await asyncio.to_thread(profiles.remove, profile.name)
            return index
        if key == LABEL_BOOKMARK_KEY:
            from navigator.widgets.drives.connect_dialog import ConnectDialog, ConnectRequest

            request = ConnectRequest(profile.scheme, profile.host, profile.user, profile.port, profile.path,
                                     profile.name, True)
            # Kept, not connected: no need of the protocol's package to edit one.
            answer = await ConnectDialog(request, editing=True).execute(self.application)
            if answer is not None:
                await asyncio.to_thread(profiles.replace, profile.name, answer.name or profile.name,
                                        answer.scheme, answer.host, answer.user, answer.port, answer.path)
            return index
        by = -1 if key == "ctrl+up" else 1
        if await asyncio.to_thread(profiles.move, profile.name, by):
            return index + by
        return index

    def equalize_panels(self) -> None:
        """Alt+=: the passive panel on the active panel's directory -- shown,
        if it was hidden or stood behind the tree or the quick view, as
        Alt+F1/Alt+F2 bring theirs.  The keyboard stays where it was."""
        panel = self.active_panel
        if panel.found is not None:
            return
        side = "right" if panel is self.left else "left"
        other = self.bring_side(side)
        other.leave_found()
        other.location = panel.location
        panel.focus()

    async def change_directory(self, *, search: str = "") -> None:
        """Alt+T: *Choose Directory*, and the active panel goes where it says.

        The panel that asked, remembered before the dialog takes the keyboard:
        while it is up the focus is in the dialog, and which panel was active
        is no longer something the focus can say.
        """
        from navigator.widgets.tree.change_dir_dialog import ChangeDirDialog

        panel = self.active_panel
        chosen = await ChangeDirDialog(start=shown(panel.location), hidden=panel.show_hidden,
                                       made=self._made_in, search=search).execute(self.application)
        if chosen is not None:
            # A ``root:`` directory the user may read is the disk's own again.
            panel.location = panel._plain_where_readable(Location.of(chosen))
            panel.focus()

    def _made_in(self, base: Any, name: str) -> None:
        """Alt+T's *MkDir* made *name* in *base*: a panel showing *base* looks
        again with its cursor on it, as F7's does (``a/b`` on ``a``)."""
        where = Location.of(base)
        key = Path(name).parts[0]
        for panel in (self.left, self.right):
            if panel.found is None and Location.of(panel.location) == where:
                panel.reload(key=key)

    async def on_go_parent(self, event: GoParent) -> bool:
        line = self._command_line()
        if event.by_key and line is not None and line.holds_backspace():
            # The Backspace held (or tapped on) to clear the line: swallowed,
            # not a climb up the tree with every repeat.
            return True
        self.active_panel.go_up()
        return True

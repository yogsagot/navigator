"""What stands in for a panel: the directory tree (Ctrl+T), the quick view (Ctrl+Q) and
the info panel (Ctrl+L), with the effects that keep them following it; zooming.

A mixin of :class:`Manager` (``navkit.widget.Mixin``): methods only; its state,
keys and ``checks`` are in ``manager.py``.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import TYPE_CHECKING, Any

from navkit.reactive import untracked

from navml.commands import ZoomWindow

from navigator.lib.drives import Location
from navigator.lib.drives.location import shown
from navigator.settings import SETTINGS

if TYPE_CHECKING:
    from navigator.widgets.manager.manager import Manager as _Base
else:
    from navkit.widget import Mixin as _Base


class Views(_Base):
    """What stands in for a panel: the directory tree (Ctrl+T), the quick view (Ctrl+Q) and"""

    async def on_zoom_window(self, event: ZoomWindow) -> bool:
        """Alt+Z with the quick view selected: ``TDoubleWindow``'s ``cmZoom``.

        ``if LSelected and (LType = dtView) then SwitchRight``: the side the
        view follows is hidden, which shrinks the window to the view, and the
        command, left uncleared, went on to ``TWindow``'s zoom, so the view
        fills the desktop.  Again, the panel comes back.

        A departure on the way back: DN's second Alt+Z grew a window that was
        zoomed already and then unzoomed it to the shrunk rectangle; here the
        zoom is undone first and the side shown after, so the window gets back
        the rectangle it had before the first.  Anywhere else -- a panel, the
        tree, the information panel, the quick view without the keyboard --
        it goes on to the desktop and zooms the window.
        """
        if not self._quick_selected():
            return False
        followed = "right" if self.is_quick(self.side_view("left")) else "left"
        if self.hidden_side == followed:
            self.show_side(followed)
            return True
        if self.hidden_side is not None:
            return False
        self.hide_side(followed)
        self.toggle_zoom()
        self._view_zoom = (self.x, self.y, self.width, self.height)
        return True

    def _quick_selected(self) -> bool:
        """Whether the quick view stands in a panel's place with the keyboard."""
        return self.is_quick(self.replacement) and self._quick.focus_within

    def _unzoom_view(self) -> None:
        """Undo the zoom Alt+Z put on top of hiding the followed side, while
        the window is still as it left it; else leave the window be."""
        rect, self._view_zoom = self._view_zoom, None
        if rect is not None and self.zoomed and rect == (self.x, self.y, self.width, self.height):
            self.toggle_zoom()

    async def on_tree_chosen(self, event: Any) -> bool:
        """Enter in the tree: the panel goes there now, not after the pause --
        a ``root:`` directory the user may read as the disk's own again."""
        panel = self.active_panel
        panel.location = panel._plain_where_readable(Location.of(event.node.data))
        return True

    def toggle_tree(self) -> None:
        """Ctrl+T: ``SwitchView(dtTree)``."""
        self.switch_view(self.tree)

    @property
    def quick(self) -> Any:
        """Ctrl+Q's quick view (``QuickViewer``), hidden at the end of the
        panels' row until :meth:`switch_view` moves it beside the panel it
        replaces -- made the first time it is wanted.  The viewer behind it is
        a tenth of the modules Navigator loads, and most sessions never press
        Ctrl+Q.  :meth:`is_quick` asks about it without making it."""
        if self._quick is None:
            from navigator.widgets.viewer.quick_viewer import QuickViewer

            quick = QuickViewer()
            # Its title keeps clear of the window icons, as a panel's does.
            quick.title_margin = 5
            quick.visible = False
            self.panels.add(quick)
            self._quick = quick
        return self._quick

    def is_quick(self, view: Any) -> bool:
        """Whether *view* is the quick view -- never making one to compare."""
        return view is not None and view is self._quick

    def toggle_quick_view(self) -> None:
        """Ctrl+Q: ``SwitchView(dtView)``, and the view loads the file under the cursor."""
        self.switch_view(self.quick)

    def switch_view(self, view: Any) -> None:
        """DOS Navigator's ``SwitchView``: *view* in the passive panel's place, or out of it.

        The **passive** panel gives way to *view*, in its place, and the
        keyboard stays with the active one.  Asking again for the view that is
        showing puts the panel back -- and gives it the keyboard if the view
        had it, as the original re-selected the panel it restored.  Asking for
        the *other* view swaps it in where the first one stood, and the
        keyboard goes back to the active panel, as ``SwitchView`` selected it.

        **With a side hidden**, ``SwitchView``'s order: *view* on the hidden
        side shows that side, the view still in it, the keyboard unmoved
        (``SwitchRight``/``SwitchLeft``); *view* showing is put away, and the
        hidden other side stays hidden; anything else shows the hidden side
        first, then puts *view* in the passive place as ever.
        """
        hidden = self.hidden_side
        if hidden is not None and self.side_view(hidden) is view:
            self.show_side(hidden)
            return
        if hidden is not None and self.replacement is not view:
            # The view takes the passive side's place, which may be the
            # hidden one: both sides come back first.
            self.show_side(hidden)
        current, replaced = self.replacement, self.replaced
        if current is view:
            had_keys = view.focus_within
            view.visible = False
            replaced.visible = True
            self.replacement = self.replaced = None
            if had_keys:
                replaced.focus()
            self.panels.invalidate()
            return
        active = self.active_panel
        had_keys = False
        if current is not None:
            had_keys = current.focus_within
            current.visible = False
            passive = replaced
        else:
            passive = self.passive_panel
        row = self.panels.children
        row.remove(view)
        row.insert(row.index(passive), view)
        if view is self.tree:
            view.set_show_hidden(active.show_hidden)
            view.show(shown(active.location))
        passive.visible = False
        view.visible = True
        self.replaced, self.replacement = passive, view
        if had_keys:
            active.focus()
        if self.is_quick(view):
            # A new THFileViewer each time, as ViewInsert made: ViOpt's.
            self.quick.fresh()
            self._quick_view_follows_panel()
        if view is self.info:
            self._info_follows_panel()
            self._info_follows_cursor()
        self.panels.invalidate()

    def _focus_replacement(self) -> None:
        replacement = self.replacement
        (self._quick.viewer if self.is_quick(replacement) else replacement).focus()

    def _info_follows_panel(self) -> None:
        """The information panel describes the active panel's directory, read
        again whenever the panel is (``cmRereadInfo``)."""
        if self.replacement is not self.info:
            return
        panel = self.active_panel
        location, entries, _ = panel.location, panel.items, panel.reload_token
        found = panel.found
        with untracked():
            if found is None:
                self.info.show(location, entries)
            else:
                self.info.show_listing(found, entries)

    def reread_info(self) -> None:
        """``cmRereadInfo``: the information panel, if it is up, reads its
        directory and disk again -- a save elsewhere still changed the free space."""
        self._info_follows_panel()

    def _info_follows_cursor(self) -> None:
        """The information panel's *Current file* is whatever the active
        panel's cursor is on -- apart from :meth:`_info_follows_panel`, so a
        move does not read the disk's facts again."""
        if self.replacement is not self.info:
            return
        panel = self.active_panel
        entry = panel.selected
        location = None if entry is None else panel.entry_location(entry)
        with untracked():
            self.info.show_file(entry, location)

    def _quick_view_follows_panel(self) -> None:
        """The quick view shows whatever the active panel's cursor is on: ``SendLocated``."""
        if not self.is_quick(self.replacement):
            return
        panel = self.active_panel
        entry = panel.selected
        path = None if entry is None or entry.is_dir else shown(panel.entry_location(entry))
        with untracked():
            self.quick.show(path)

    def _tree_follows_panel(self) -> None:
        """The tree's cursor goes wherever the active panel goes: ``cmChangeTree``."""
        if self.tree_replaces is None:
            return
        location, hidden = self.active_panel.location, self.active_panel.show_hidden
        place = location if not location.is_local else location.local
        with untracked():
            self.tree.set_show_hidden(hidden)
            # Compared with what was asked, not where it landed: that is
            # resolved on a thread (``show_path``), never here on the loop.
            if self.tree.asked != place:
                self.tree.show(place)

    def _panel_follows_tree(self) -> None:
        """A cursor at rest in a focused tree takes the panel with it.

        DOS Navigator's ``NeedLocated``: every move restarts the wait, and the
        panel moves only once the cursor has stayed put for ``LOCATE_DELAY``.
        Only under File Manager Setup's *Auto change directory*
        (``fmoAutoChangeDir``), as DN set ``NeedLocated`` only then.
        """
        path, focused = self.tree.selected_path, self.tree.focused
        with untracked():
            if self._follow is not None:
                self._follow.cancel()
                self._follow = None
            app = self.application
            if (
                self.tree_replaces is None or not focused or path is None
                or app is None or not app.is_running
                or not SETTINGS.file_manager.auto_change_dir
            ):
                return
            self._follow = self.spawn(self._follow_later(path))

    async def _follow_later(self, path: Path) -> None:
        await asyncio.sleep(self.LOCATE_DELAY)
        if self.tree.focused and self.tree.selected_path == path:
            self.active_panel.location = Location.of(path)

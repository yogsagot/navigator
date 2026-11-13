"""The active panel's options: filter, columns, branch view, setup, sort, select group.

A mixin of :class:`Manager` (``navkit.widget.Mixin``): methods only; its state,
keys and ``checks`` are in ``manager.py``.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

from navkit.i18n import tr

from navigator.widgets.manager.commands import SelectGroup
from navigator.widgets.manager.panel import Panel
from navigator.lib.drives import Location, drive_of
from navigator.widgets.manager.manager.helpers import sort_order_captions, sort_orders

if TYPE_CHECKING:
    from navigator.widgets.manager.manager import Manager as _Base
else:
    from navkit.widget import Mixin as _Base


class PanelOptions(_Base):
    """The active panel's options: filter, columns, branch view, setup, sort, select group."""

    async def advanced_filter(self, panel: Panel) -> None:
        """Alt+Del: ``CM_AdvancedFilter`` -- the *Filter* box over *panel*'s
        extensions, again after each *Show* or *Hide*, on the mask it was on,
        until *Close* (:mod:`navigator.lib.file_ops.advfilter`).  The extensions are the
        directory's whatever the mask hides, read on a thread through the
        panel's drive (an archive, another drive, ``root:``) -- or a listing's
        own, or the ones listed if the drive cannot be read; none at all, and
        there is nothing to ask."""
        from navigator.lib.file_ops.advfilter import combine, extensions
        from navigator.widgets.manager.filter_dialog import FilterDialog

        def read_all(location: Location, hidden: bool) -> list[Any]:
            return drive_of(location).scan(location, hidden, "name", free=False)[0]

        app = self.application
        cursor = 0
        while app is not None:
            if panel.found is not None:
                entries = list(panel.found.entries)
            else:
                try:
                    entries = await asyncio.to_thread(read_all, panel.location, panel.show_hidden)
                except OSError:  # DriveGone too: what is shown is what there is
                    entries = list(panel.items)
            masks = extensions(entries)
            if len(masks) < 2:
                return
            answer = await FilterDialog(masks, cursor).execute(app)
            if answer is None:
                return
            show, chosen, cursor = answer
            panel.set_file_mask(combine(panel.file_mask, chosen, show))

    async def setup_columns(self, panel: Panel) -> None:
        """Alt+K: ``CM_SetShowParms``, *panel*'s columns.

        OK shows the detailed mode with the columns ticked -- with none, the
        names alone, as DN's ``ShowFlags`` of 0 was its brief panel.  *Brief*
        is the list mode (``cmYes``); *Full* every column (``GetFullFlags``).
        A choice is the panel's own, as ``ShowFlags`` was.
        """
        from navigator.widgets.manager.columns_dialog import ColumnsDialog
        from navigator.widgets.manager.columns_dialog.columns_dialog import ALL_COLUMNS

        answer = await ColumnsDialog(panel.shown_columns, panel.found is not None,
                                     archive=panel.location.outer is not None).execute(self.application)
        if answer is None:
            return
        if answer[0] == "brief":
            panel.view_mode = "list"
            return
        if answer[0] == "full":
            panel.shown_columns = ALL_COLUMNS
            panel.view_mode = "detailed"
            return
        columns = answer[1]
        panel.shown_columns = columns
        panel.view_mode = "detailed" if columns else "list"

    async def directory_branch(self, panel: Panel) -> None:
        """Panel > Directory Branch: ``CM_Branch`` -- every file in the panel's
        directory and every one below it, directories left out, as a listing
        titled ``Branch:`` and the directory (DN's ``dlBranch``).  Searched as
        Alt+F7 searches, so a long walk shows its box and Esc stops it."""
        from navigator.lib.file_ops.filefind import FindRequest

        if panel.found is not None:
            return  # ``CM_Branch`` acted on a disk alone
        request = FindRequest(recursive=True, scope="directory", directories=False)
        await self._search_into(panel, request, tr("Branch: {path}").format(path=panel.title_location))

    async def panel_setup(self, panel: Panel) -> None:
        """Alt+S: ``cmPanelSetup``, DN's ``Setup`` -- *Panel Options* for *panel*,
        and its answer becomes that panel's own (:meth:`Panel.set_options`)."""
        from navigator.widgets.manager.panel_setup_dialog import PanelSetupDialog

        answer = await PanelSetupDialog(panel).execute(self.application)
        if answer is not None:
            panel.set_options(*answer)

    async def on_select_group(self, event: SelectGroup) -> bool:
        # Started, not awaited, for the reason ``on_make_directory`` gives.
        self.spawn(self.select_group(select=True, invert=event.invert))
        return True

    async def select_group(self, *, select: bool, invert: bool) -> None:
        """Gray ``+``/``-``: ask for a mask, then tag or untag what it matches.

        The panel is taken before the dialog is, for the reason
        :meth:`change_directory` gives.
        """
        from navigator.widgets.manager.select_dialog import SelectDialog

        panel = self.active_panel
        answer = await SelectDialog(select=select, invert=invert).execute(self.application)
        if answer is not None:
            mask, except_mask = answer
            panel.select_group(mask, select=select, invert=except_mask)

    async def choose_sort(self, panel: Panel) -> None:
        """``CM_SortBy``'s box, on the mode the panel has (``Menu^.Default``);
        a choice re-sorts it.

        Centred on the panel, a departure: DN put it at the panel's top left
        corner, over the first names rather than the middle of the listing
        the eye is on.  DN's *Group* is *Type* here, as in the *New Manager
        defaults*, and so its hot key is Y.

        Each mode is offered twice, a departure (DN had no descending order):
        its own direction first -- what the hot key picks, and plain -- then
        reversed, with the arrow of the way it then runs where a menu shows a
        key (:func:`sort_orders`), as Alt+S's captions have with *Reverse
        order* ticked.
        The order the panel has is ticked, and the box opens on it.
        """
        from navml.widgets.menu.popup_menu import PopupMenu
        from navml.widgets.menu.sub_menu import SubMenu

        menu = SubMenu()
        orders = sort_orders()
        here = (panel.sort_mode, panel.sort_reverse)
        items = []
        for (mode, reverse), caption in zip(orders, sort_order_captions()):
            item = menu.add_item(caption, key=panel.direction_arrow(mode, True) if reverse else "")
            item.ticked = (mode, reverse) == here
            items.append(item)
        title = tr("Sort by")
        width, height = PopupMenu.measure(menu, self.application, self, title)
        ox, oy = panel.offset()
        x = ox + panel.x + (panel.width - width) // 2
        y = oy + panel.y + (panel.height - height) // 2
        box = PopupMenu(menu, x, y, current=orders.index(here) if here in orders else 0, behind=self,
                        title=title)
        chosen = await box.execute(self.application)
        if chosen is None:
            return
        panel.sort_by(*orders[items.index(chosen)])

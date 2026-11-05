"""The handlers behind ``service_window.nml``.

The units are read on a thread (:func:`navigator.lib.system.services.gather`,
through ``Background``) when the window opens, on Ctrl+R, when *User units*
or *All types* changes, after anything is done to a unit, and every
``[services] refresh`` seconds -- a tick is let go while a read is under way
or a box is up.  Only the newest read is listed, and the cursor stays on the
unit it was on, by name.  The filter and the sort change what is shown, never
what was read.

**Doing something to a unit** runs ``systemctl --no-ask-password VERB`` as
the user first; polkit's refusal (``EPERM``) is offered *As root*, as a
refused file step is, and done by the root helper's ``systemctl`` -- never for
a user unit, whose manager is the user's own.  **F3 follows the journal** in
the viewer: :mod:`navigator.widgets.shell.service_window.journal_window`.
**Enter in the list is handled here** (*Details*), so the list's
``ChosenEvent`` does not walk up to the screen, which would take it for a
directory.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from navkit.bidi import display_width
from navkit.events import ContextMenuEvent, Event, KeyEvent
from navkit.i18n import tr, tr_n
from navkit.reactive import effect, peek
from navkit.text import caption_runs
from navml.background import Background, Outcome
from navml.commands import CloseWindow
from navml.widgets.dialog.commands import QuickSearch, SelectNext, SelectPrevious
from navml.widgets.dialog.control import escape_caption
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.list_viewer import ListViewer
from navml.widgets.dialog.tree_view import ChosenEvent
from navml.widgets.menu.commands import ShowContextMenu
from navml.widgets.menu.context_menu import ContextMenu
from navml.widgets.menu.context_menu.context_menu import open_on_click, open_on_key
from navml.widgets.window import Window

from navigator.lib.system import services
from navigator.lib.system.elevate import ELEVATION, refused
from navigator.widgets.manager.commands import Rescan
from navigator.widgets.shell.commands import (
    DisableService, EditUnitFile, EnableService, FilterServices, MaskService, ReloadService, RestartService, ServiceAllTypes,
    ServiceDetails, ServiceJournal, ServiceSortActive, ServiceSortDescription, ServiceSortFileState,
    ServiceSortName, ServiceUserUnits, ServiceVerb, StartService, StopService, UnmaskService,
)
from navigator.widgets.shell.process_list import SortChosen

#: Where the window reads the units.
_READER = Background("nav-services", workers=1)

#: Each sort command's key.
_SORTS = ((ServiceSortName, "name"), (ServiceSortActive, "active"), (ServiceSortFileState, "file_state"),
          (ServiceSortDescription, "description"))

#: The verbs asked about first: what takes a running unit away.
_ASKED = frozenset({"stop", "mask"})


def _refresh() -> float:
    """``[services] refresh``: seconds between reads, 0 for none."""
    from navigator.settings import SETTINGS

    try:
        return max(0.0, float(SETTINGS.services.refresh))
    except (AttributeError, TypeError, ValueError):
        return 3.0


def _discard_unused(override: Path) -> None:
    """The editor on *override* closed: the ``<unit>.d`` directory F4 made for
    it removed, on a thread, if the override was never saved and nothing else
    was put there.  As the user, else through root access while it is still
    open (``[system] root_timeout``) -- never asked for again to tidy up; an
    empty directory left behind is harmless."""

    def discard() -> None:
        directory = override.parent
        try:
            if override.exists() or any(directory.iterdir()):
                return
        except OSError:
            return
        try:
            directory.rmdir()
        except OSError as error:
            if not refused(error) or not ELEVATION.running:
                return
            try:
                ELEVATION.call("rmdir", path=str(directory))
            except OSError:
                pass
            finally:
                ELEVATION.release()

    asyncio.get_running_loop().run_in_executor(None, discard)


class ServiceWindow(Window):
    """systemd's units in a window of their own."""

    def __init__(self, user: bool = False, all_types: bool = False, sort: str = "name",
                 descending: bool = False, **kwargs: Any) -> None:
        """*user* ticks *User units*, *all_types* ticks *All types*; *sort* is
        one of :data:`~navigator.lib.system.services.SORTS`, *descending* its way round."""
        super().__init__(**kwargs)
        self.user = user
        self.all_types = all_types
        self.sort = sort if sort in services.SORTS else "name"
        self.descending = descending
        self._found: list[services.Unit] = []
        #: What the shown units were read for, ``(user, all_types)``.
        self._read_for: tuple[bool, bool] | None = None
        self._error = ""
        self._reads = 0
        self._reading = False
        self._ticker: Any = None
        #: The unit files F4 opened, by path: saving one runs daemon-reload.
        self._editing: dict[str, services.Unit] = {}

    @staticmethod
    def caption_width(text: str) -> int:
        """How many cells *text* takes drawn as a caption, its ``~`` marks gone."""
        return sum(display_width(run) for run, _ in caption_runs(text))

    @property
    def user(self) -> bool:
        """Whether *User units* is ticked: ``systemctl --user``."""
        return bool(self.user_box.value & 1)

    @user.setter
    def user(self, value: bool) -> None:
        self.user_box.value = 1 if value else 0

    @property
    def all_types(self) -> bool:
        """Whether *All types* is ticked: every unit, not services alone."""
        return bool(self.types_box.value & 1)

    @all_types.setter
    def all_types(self, value: bool) -> None:
        self.types_box.value = 1 if value else 0

    def mounted(self) -> None:
        super().mounted()
        self.units.filter_line = self.filter
        self.filter.rows = self.units
        # A symbol, not a word: set here because a markup literal is translated.
        self.clear_filter.text = "X"
        effect(self, ServiceWindow._follow_view)
        app = self.application
        seconds = _refresh()
        if app is not None and seconds > 0:
            self._ticker = app.call_every(seconds, self._tick)

    def unmounting(self) -> None:
        if self._ticker is not None:
            self._ticker.cancel()
            self._ticker = None
        super().unmounting()

    def take_keyboard(self) -> None:
        # Not from ``mounted()``, for the reason ``TreeWindow`` gives.
        self.units.focus()

    def _follow_view(self) -> None:
        """*User units* or *All types* changed -- a read for them -- or the
        filter typed: list again."""
        wanted = (bool(self.user_box.value & 1), bool(self.types_box.value & 1))
        self.filter.value  # noqa: B018 -- what this effect follows
        if wanted != self._read_for:
            self.reload()
        else:
            self._show()

    # -- reading ----------------------------------------------------------------------

    def reload(self) -> None:
        """Read the units again, on a thread; only the newest read is listed."""
        self._reads += 1
        self._reading = True
        wanted = (self.user, self.all_types)
        _READER.run(self, services.gather, *wanted,
                    done=lambda outcome, n=self._reads: self._read(n, wanted, outcome))

    async def _tick(self) -> None:
        """The clock's read -- let go while one is under way or a box is up."""
        app = self.application
        if self._reading or app is None or app.modal is not None:
            return
        self.reload()

    def _read(self, read: int, wanted: tuple[bool, bool], outcome: Outcome) -> None:
        if read != self._reads:
            return
        self._reading = False
        self._read_for = wanted
        try:
            self._found = outcome.result()
            self._error = ""
        except OSError as error:
            self._found = []
            self._error = error.strerror or str(error)
        self._show()

    def _show(self) -> None:
        """List what was read, keeping the cursor on the unit it was on.

        The list's items and cursor are peeked: ``_follow_view`` calls this,
        and an effect that read them would run again at every cursor move.
        """
        listing = self.units
        items = peek(listing, ListViewer.items)
        cursor = peek(listing, ListViewer.cursor)
        current = items[cursor].name if 0 <= cursor < len(items) else None
        text = peek(self.filter, type(self.filter).value)
        picked = [unit for unit in self._found if services.matches(unit, text)]
        shown = services.ordered(picked, self.sort, self.descending)
        listing.sort = self.sort
        listing.descending = self.descending
        listing.items = shown
        listing.cursor = next((index for index, unit in enumerate(shown) if unit.name == current), 0)
        if self._error:
            summary = self._error
        elif text.strip():
            summary = tr_n("{shown} of {count} unit match the filter", "{shown} of {count} units match the filter",
                           len(self._found), shown=f"{len(picked):,}", count=f"{len(self._found):,}")
        else:
            running = sum(1 for unit in self._found if unit.running)
            failed = sum(1 for unit in self._found if unit.failed)
            summary = tr_n("{count} unit, {running} running, {failed} failed",
                           "{count} units, {running} running, {failed} failed", len(self._found),
                           count=f"{len(self._found):,}", running=f"{running:,}", failed=f"{failed:,}")
        self.status.text = escape_caption(summary)

    # -- sorting and the boxes ----------------------------------------------------------

    def _sort_by(self, by: str) -> None:
        """Sort *by* that; already so, the other way round."""
        if self.sort == by:
            self.descending = not self.descending
        else:
            self.sort, self.descending = by, False
        self._show()

    async def on_sort_chosen(self, event: SortChosen) -> bool:
        self._sort_by(event.by)
        return True

    async def on_service_sort_name(self, command: ServiceSortName) -> bool:
        self._sort_by("name")
        return True

    async def on_service_sort_active(self, command: ServiceSortActive) -> bool:
        self._sort_by("active")
        return True

    async def on_service_sort_file_state(self, command: ServiceSortFileState) -> bool:
        self._sort_by("file_state")
        return True

    async def on_service_sort_description(self, command: ServiceSortDescription) -> bool:
        self._sort_by("description")
        return True

    async def on_service_user_units(self, command: ServiceUserUnits) -> bool:
        self.user = not self.user
        return True

    async def on_service_all_types(self, command: ServiceAllTypes) -> bool:
        self.all_types = not self.all_types
        return True

    async def on_filter_services(self, command: FilterServices) -> bool:
        """F4, Ctrl+S or the menu's *Filter*: the keyboard to the filter line, its text picked."""
        self.filter.focus()
        self.filter.select_all()
        return True

    async def on_quick_search(self, command: QuickSearch) -> bool:
        """The list's own Ctrl+S, which it has no search for: the filter's."""
        return await self.on_filter_services(FilterServices())

    async def on_clear_filter_click(self, event: Event) -> bool:
        self.filter.value = ""
        self.filter.cursor = 0
        self.filter.focus()
        return True

    async def on_rescan(self, event: Rescan) -> bool:
        self.reload()
        return True

    def checks(self, command: Any) -> bool | None:
        """The *Services* menu ticks the sort in force and the two boxes."""
        for kind, by in _SORTS:
            if isinstance(command, kind):
                return self.sort == by
        if isinstance(command, ServiceUserUnits):
            return self.user
        if isinstance(command, ServiceAllTypes):
            return self.all_types
        return super().checks(command)

    # -- what can be done to the one under the cursor -------------------------------------

    @property
    def selected(self) -> services.Unit | None:
        return self.units.selected

    def allows(self) -> bool:
        """Whether there is a unit under the cursor -- what the buttons' ``disabled`` follows."""
        return self.selected is not None

    def refusal(self, command: Any) -> str:
        if isinstance(command, (ServiceVerb, ServiceJournal, ServiceDetails, EditUnitFile)):
            return "" if self.selected is not None else tr("The cursor is on no unit")
        return super().refusal(command)

    async def on_chosen(self, event: ChosenEvent) -> bool:
        """Enter or a double click on a row: its details."""
        await self.on_service_details(ServiceDetails())
        return True

    async def on_service_details(self, command: ServiceDetails) -> bool:
        unit = self.selected
        if unit is not None:
            self.spawn(self._details(unit))
        return True

    async def _details(self, unit: services.Unit) -> None:
        """What ``systemctl status`` says of *unit*, in a box."""
        try:
            text = await asyncio.to_thread(services.details, unit)
        except OSError as error:
            await self._say(error)
            return
        rows = text.splitlines() or [unit.name]
        desktop = self.parent
        screen_width = desktop.width if desktop is not None else 80
        screen_height = desktop.height if desktop is not None else 25
        width = max(40, min(max(display_width(row) for row in rows) + 4, screen_width - 4))
        room = width - 4
        tall = sum(max(1, -(-display_width(row) // room)) for row in rows)
        await Dialog(title=unit.name, buttons="ok", prompt=escape_caption("\n".join(rows)), modal_width=width,
                     modal_height=min(tall + 6, max(10, screen_height - 2))).execute(self.application)

    async def on_service_journal(self, command: ServiceJournal) -> bool:
        unit = self.selected
        if unit is not None:
            from navigator.widgets.shell.service_window.journal_window import open_journal

            self.spawn(open_journal(self, unit))
        return True

    # -- F4: the unit's file in the editor -------------------------------------------------

    async def on_edit_unit_file(self, command: EditUnitFile) -> bool:
        unit = self.selected
        if unit is not None:
            self.spawn(self._edit(unit))
        return True

    async def _edit(self, unit: services.Unit) -> None:
        """*unit*'s file in an editor window: the administrator's own as it
        is, a package's through a drop-in override (``systemctl edit``'s
        ``<unit>.d/override.conf``), a new one seeded with the package's file
        commented out.  Read as the user -- unit files are everyone's to read
        -- and a save refused permission is offered *As root* by the editor."""
        from navigator.lib.config.file_history import open_editor

        try:
            fragment = await asyncio.to_thread(services.unit_file, unit)
            path, vendor = services.edit_target(unit, fragment)
            seed = ""
            made = False
            if vendor is not None:
                made = await self._override_dir(unit, path.parent)
                if made is None:
                    return
                if not await asyncio.to_thread(path.exists):
                    original = await asyncio.to_thread(vendor.read_text, errors="replace")
                    seed = services.override_text(unit, vendor, original)
            window = await open_editor(self.parent, path, new=bool(seed))
        except OSError as error:
            await self._say(error)
            return
        if window is None:
            return
        if seed:
            window.editor.insert_text(seed)
            window.editor.go_to_line(services.OVERRIDE_LINE)
        if made:
            window.after_close = lambda: _discard_unused(path)
        self._editing[str(path)] = unit

    async def _override_dir(self, unit: services.Unit, directory: Path) -> bool | None:
        """*directory*, the drop-in's, made if need be -- as root, after asking,
        where the user may not.  True when it was made now, False when it was
        there already, None -- said or declined -- when it is not there."""
        if await asyncio.to_thread(directory.is_dir):
            return False
        try:
            await asyncio.to_thread(directory.mkdir, parents=True)
            return True
        except FileExistsError:
            return False
        except OSError as error:
            if not (refused(error) and not unit.user and await asyncio.to_thread(ELEVATION.available)):
                await self._say(error)
                return None
        from navigator.widgets.file_ops.as_root import ask_as_root

        message = tr("{unit} is the package's: it is overridden in {path}, which only root may create.").format(
            unit=unit.name, path=directory)
        if not await ask_as_root(self.application, escape_caption(message), title=tr("Services")):
            return None

        def as_root() -> None:
            try:
                ELEVATION.call("makedirs", path=str(directory))
            finally:
                ELEVATION.release()

        try:
            await asyncio.to_thread(as_root)
        except OSError as failure:
            await self._say(failure)
            return None
        return True

    def unit_file_saved(self, path: Path) -> None:
        """``Shell.on_file_saved``: a file was written.  One F4 opened from
        here has systemd read its unit files again, or the edit would not
        count until the next boot."""
        unit = self._editing.get(str(path))
        if unit is not None:
            self.spawn(self._daemon_reload(unit))

    async def _daemon_reload(self, unit: services.Unit) -> None:
        """``systemctl daemon-reload`` for *unit*'s manager; refused, as root --
        at once if root access is already open (the file was most likely just
        saved through it), else after asking."""
        try:
            await asyncio.to_thread(services.daemon_reload, unit.user)
        except OSError as error:
            if not (refused(error) and not unit.user and await asyncio.to_thread(ELEVATION.available)):
                await self._say(error)
                return
            if not ELEVATION.running:
                from navigator.widgets.file_ops.as_root import ask_as_root

                message = tr("{unit}'s file was saved, but systemd cannot be told to read it again: {error}").format(
                    unit=unit.name, error=error.strerror or error)
                if not await ask_as_root(self.application, escape_caption(message), title=tr("Services")):
                    return

            def as_root() -> None:
                try:
                    ELEVATION.call("daemon_reload")
                finally:
                    ELEVATION.release()

            try:
                await asyncio.to_thread(as_root)
            except OSError as failure:
                await self._say(failure)
                return
        self.reload()

    async def on_service_verb(self, command: ServiceVerb) -> bool:
        """F5, F6, F7, F8, Ctrl+E, Ctrl+D and the menu's: ``systemctl VERB``."""
        unit = self.selected
        if unit is not None and command.verb in services.VERBS:
            self.spawn(self._act(unit, command.verb))
        return True

    # Each command's class is its own handler's name; they share one.
    on_start_service = on_restart_service = on_reload_service = on_stop_service = on_service_verb
    on_enable_service = on_disable_service = on_mask_service = on_unmask_service = on_service_verb

    async def _act(self, unit: services.Unit, verb: str) -> None:
        """*verb* done to *unit*, asked about first if it stops it; refused,
        offered as root; failed, said in a box.  Read again either way."""
        if verb in _ASKED:
            question = (tr("Stop {unit}?") if verb == "stop" else tr("Mask {unit}? It will not start at all until unmasked."))
            answer = await Dialog(title=tr("Services"), buttons="yes-no",
                                  prompt=escape_caption(question.format(unit=unit.name))).execute(self.application)
            if answer is not True:
                return
        try:
            await asyncio.to_thread(services.act, unit, verb)
        except OSError as error:
            if refused(error) and not unit.user and await asyncio.to_thread(ELEVATION.available):
                await self._act_as_root(unit, verb, error)
            else:
                await self._say(error)
        self.reload()

    async def _act_as_root(self, unit: services.Unit, verb: str, error: OSError) -> None:
        from navigator.widgets.file_ops.as_root import ask_as_root

        message = tr("Cannot {verb} {unit}: {error}").format(verb=verb, unit=unit.name,
                                                             error=error.strerror or error)
        if not await ask_as_root(self.application, escape_caption(message)):
            return

        def as_root() -> None:
            try:
                ELEVATION.call("systemctl", verb=verb, unit=unit.name)
            finally:
                ELEVATION.release()

        try:
            await asyncio.to_thread(as_root)
        except OSError as failure:
            await self._say(failure)

    async def _say(self, error: OSError) -> None:
        await Dialog(title=tr("Services"), buttons="ok",
                     prompt=escape_caption(error.strerror or str(error))).execute(self.application)

    # -- the buttons --------------------------------------------------------------------

    async def on_start_button_click(self, event: Event) -> bool:
        return await self.on_service_verb(StartService())

    async def on_stop_button_click(self, event: Event) -> bool:
        return await self.on_service_verb(StopService())

    async def on_journal_button_click(self, event: Event) -> bool:
        return await self.on_service_journal(ServiceJournal())

    async def on_edit_button_click(self, event: Event) -> bool:
        return await self.on_edit_unit_file(EditUnitFile())

    async def on_close_button_click(self, event: Event) -> bool:
        self.request_close()
        return True

    # -- the right-click menu: ``ContextMenuHost``'s hooks, written out, as
    # ``ProcessWindow``'s are.

    def prepare_context(self, x: int, y: int) -> None:
        """A right click on a row puts the list's cursor there."""
        index = self.units.row_at(y - self.units.y)
        if index is not None and self.units.x <= x < self.units.x + self.units.width:
            self.units.cursor = index

    def context_menu(self) -> ContextMenu:
        """The *Services* menu's entries, built each time so its captions follow the language."""
        menu = ContextMenu()
        menu.add_item(tr("~J~ournal"), ServiceJournal)
        menu.add_item(tr("Edit unit file"), EditUnitFile)
        menu.add_item(tr("Detai~l~s..."), ServiceDetails)
        menu.add_line()
        menu.add_item(tr("S~t~art"), StartService)
        menu.add_item(tr("Restart"), RestartService)
        menu.add_item(tr("Rel~o~ad"), ReloadService)
        menu.add_item(tr("Sto~p~..."), StopService)
        menu.add_line()
        menu.add_item(tr("Ena~b~le"), EnableService)
        menu.add_item(tr("D~i~sable"), DisableService)
        menu.add_item(tr("~M~ask..."), MaskService)
        menu.add_item(tr("Unmas~k~"), UnmaskService)
        menu.add_line()
        menu.add_item(tr("~R~e-read"), Rescan)
        menu.add_item(tr("~C~lose"), CloseWindow)
        return menu

    def context_point(self) -> tuple[int, int]:
        """Under the list's cursor row."""
        view = self.units
        return view.x + 2, view.y + view.inset + view.header + max(0, view.cursor - view.scroll) + 1

    async def on_context_menu(self, event: ContextMenuEvent) -> bool:
        return open_on_click(self, event)

    async def on_show_context_menu(self, command: ShowContextMenu) -> bool:
        return open_on_key(self)

    # -- Tab and Alt+letter ---------------------------------------------------------------

    async def on_select_next(self, event: SelectNext) -> bool:
        self._step(1)
        return True

    async def on_select_previous(self, event: SelectPrevious) -> bool:
        self._step(-1)
        return True

    def _step(self, by: int) -> None:
        """Tab within this window, wrapping, as a dialog's Tab stays in it."""
        order = [widget for widget in self.focusable() if widget is not self]
        if not order:
            return
        app = self.application
        focused = app.focused if app is not None else None
        index = order.index(focused) if focused in order else (-1 if by > 0 else 0)
        order[(index + by) % len(order)].focus()

    async def on_key(self, event: KeyEvent) -> bool:
        """Alt and a marked letter: that control, as a dialog's ``Alt+letter`` walk."""
        if event.alt and not event.ctrl and len(event.key) == 1 and event.key.isalpha():
            for control in (self.filter_caption, self.user_box, self.types_box, self.start_button,
                            self.stop_button, self.journal_button, self.edit_button, self.close_button):
                if control.shortcut_match(event.key):
                    return await control.activate(event.key)
        return await super().on_key(event)

"""The Utilities and Options boxes: SmartPad, calculator, calendar, ASCII table, system information,
environment, the game, the screen saver, the setup dialogs and key bindings, file managers, the
history of viewed and edited files, Open..., and the windows of Disk and Utilities.

A mixin of :class:`Shell` (``navkit.widget.Mixin``): methods only; its state,
keys and ``checks`` are in ``shell.py``.
"""

from __future__ import annotations

import asyncio
import os
import random
from pathlib import Path
from typing import TYPE_CHECKING, Any

from navkit.i18n import tr

from navml.widgets.dialog.dialog import Dialog

from navigator.commands import OpenSmartpad
from navigator.widgets.manager.commands import Calculator, EditNamed
from navigator.widgets.shell.commands import (
    Game,
    OpenCalendar,
    OpenTrash,
    EmptyTrash,
    About,
    NewManager,
    OpenTreeWindow,
    OpenUsageWindow,
    OpenVolumesWindow,
    OpenProcessWindow,
    OpenServiceWindow,
    OpenMonitorWindow,
)
from navigator.settings import SETTINGS
from navigator.widgets.manager.manager import Manager

if TYPE_CHECKING:
    from navigator.widgets.shell.shell import Shell as _Base
else:
    from navkit.widget import Mixin as _Base


class Utilities(_Base):
    """The Utilities and Options boxes: SmartPad, calculator, calendar, ASCII table, system information,"""

    async def system_info(self) -> None:
        """Utilities > System Information: the machine read on a thread
        (:func:`navigator.lib.system.sysinfo.gather`), then DN's dialog."""
        import asyncio

        from navigator.lib.system.sysinfo import gather
        from navigator.widgets.shell.system_info_dialog import SystemInfoDialog

        facts = await asyncio.to_thread(gather)
        await SystemInfoDialog(facts).execute(self.application)

    async def edit_environment(self) -> None:
        """Utilities > Edit environment: ``EditDOSEvironment`` over Navigator's
        own variables; OK makes what changed so there (``navigator.lib.system.environ``)
        and in the console's shell, unseen (``Subshell.set_environment``)."""
        import os

        from navigator.lib.system.environ import apply, changes
        from navigator.widgets.shell.environment_dialog import EnvironmentDialog

        before = dict(os.environ)
        after = await EnvironmentDialog(before).execute(self.application)
        if after is None:
            return
        found = changes(before, after)
        apply(found)
        self.console.subshell.set_environment(found)

    async def on_open_smartpad(self, event: OpenSmartpad) -> bool:
        """Alt+Q, ≡ > *SmartPad (TM)*: ``OpenSmartpad`` (``navigator.lib.utilities.smartpad``)."""
        from navigator.lib.utilities.smartpad import open_smartpad

        if self.console_visible:
            self.toggle_console()
        self.spawn(open_smartpad(self.desktop))
        return True

    # -- Ctrl+F6: the calculator ----------------------------------------------------

    async def on_calculator(self, event: Calculator) -> bool:
        """Ctrl+F6, Utilities > *Calculator*: ``InsertCalc`` -- the one calculator
        window, brought forward if it is open, else opened where DN put it, in
        the face it last had.  Already in front, the next face: a departure,
        for terminals that send no Ctrl+digit."""
        from navigator.widgets.shell.calculator_window import CalculatorWindow
        from navigator.widgets.shell.calculator_window.calculator_window import X, Y

        if self.console_visible:
            self.toggle_console()
        desktop = self.desktop
        for window in desktop.windows():
            if isinstance(window, CalculatorWindow):
                if window is desktop.active_window:
                    window.cycle_mode()
                else:
                    desktop.activate(window)
                return True
        window = desktop.open(CalculatorWindow())
        window.x, window.y = X, Y
        window.place()
        window.take_keyboard()
        window.line.focus()
        return True

    # -- Utilities > Calendar --------------------------------------------------------

    async def on_open_calendar(self, event: OpenCalendar) -> bool:
        """Utilities > *Calendar*: TVDEMO's calendar window, a departure (DN had
        none) -- the one window, brought forward if it is open, else opened in
        the middle of the desktop on today.  From a click on the clock it goes
        to the top right corner, its top edge on the screen's second row, just
        under the clock; a click on the clock while it is open closes it."""
        from navigator.widgets.shell.calendar_window import CalendarWindow

        if self.console_visible:
            self.toggle_console()
        desktop = self.desktop
        for window in desktop.windows():
            if isinstance(window, CalendarWindow):
                if event.under_clock:
                    window.close()
                else:
                    desktop.activate(window)
                return True
        window = desktop.open(CalendarWindow())
        # As wide as the months its *View* shows.
        width, height = window.size()
        width, height = min(width, desktop.width), min(height, desktop.height)
        if event.under_clock:
            # Screen row 1 in the desktop's rows: 0 under a docked menu bar,
            # 1 when the desktop has the top row too.
            top = desktop.offset()[1] + desktop.y
            x, y = desktop.width - width, max(0, 1 - top)
        else:
            x, y = (desktop.width - width) // 2, (desktop.height - height) // 2
        x, y = max(0, x), max(0, min(y, desktop.height - height))
        window.locate(x, y, width, height)
        window.take_keyboard()
        return True

    async def ascii_table(self) -> None:
        """The character table, then the character picked on the command line.

        *ASCII Chart* in the ASCII glyph tier, the *Character Table* in any
        other (:func:`~navigator.widgets.shell.unicode_chart.pick_character`).
        DN put it back as a key press (``PutEvent``), which reached the
        command line wherever the panels had the keyboard; here it goes into
        the line directly.  A NUL is no key, and nothing.  The character is
        the one the chart shows (``│`` for 179), the line being Unicode.
        """
        from navigator.widgets.shell.unicode_chart import pick_character

        char = await pick_character(self.application, self.glyphs)
        if char and char != "\x00":
            self.command_line.insert(char)

    # -- file managers --------------------------------------------------------

    @property
    def active_manager(self) -> Manager | None:
        """The file manager nearest the top of the desktop, or None if none is open.

        What a command meaning "the file manager" asks for, now that Manager >
        New can open several: the one the user last had in front, whatever
        other window -- a tree window, say -- is in front of it.
        ``manager`` stays the first one, kept for whoever asks what it was.
        """
        for window in reversed(self.desktop.windows()):
            if isinstance(window, Manager):
                return window
        return None

    async def on_new_manager(self, event: NewManager) -> bool:
        """Ctrl+F3: ``OpenWindow``.  Another file manager, filling the desktop.

        DOS Navigator asked for a drive first and opened both panels on that
        drive's current directory.  One root has no drive to ask for, so both
        panels open where the file manager in front is -- or where Navigator was
        started, with none open.
        """
        current = self.active_manager
        start = current.active_panel.location if current is not None else Path.cwd()
        self.desktop.open(Manager(start, start)).apply_left_panel()
        return True

    def show_manager_side(self, side: str) -> None:
        """Ctrl+F1 / Ctrl+F2 from the console: the file manager back, *side* alone.

        DOS Navigator's user screen turned ``cmHideLeft`` into
        ``cmPostHideLeft`` and closed: the double window then showed the left
        side and hid the right.  So Ctrl+F1 from a left-only file manager shows
        the console, and Ctrl+F1 again brings the left side back as it was.
        """
        manager = self.active_manager
        manager.show_only(side)
        if self.console_visible:
            self.toggle_console()
        self.desktop.activate(manager)

    async def on_about(self, event: About) -> bool:
        """≡ > About: started, not awaited -- a handler never waits on a dialog."""
        from navigator.widgets.about_dialog import AboutDialog

        self.spawn(AboutDialog().execute(self.application))
        return True

    # -- Options: the setup dialogs ------------------------------------------------

    async def settings(self, tab: str = "system") -> None:
        """Options > Settings, opened on page *tab*: every section it shows
        that OK changed is applied and saved, as :meth:`setup` does."""
        from navigator.lib.config import language
        from navigator.widgets.setup.settings_dialog import SettingsDialog
        from navigator.widgets.setup.settings_dialog.settings_dialog import SECTIONS

        before = SETTINGS.interface.language
        direction = SETTINGS.interface.direction
        depth = SETTINGS.appearance.colors
        glyphs = SETTINGS.appearance.glyphs
        marks = SETTINGS.appearance.marks
        dim = SETTINGS.appearance.dim_modal
        await self.setup(SettingsDialog(tab=tab), *SECTIONS)
        # And *Dim behind dialogs*, over a session's --no-dim-modal: the next
        # dialog's background is painted as it says.
        if SETTINGS.appearance.dim_modal != dim:
            self.application.dim_modal = SETTINGS.appearance.dim_modal
            self.application.invalidate()
        # The same for the colour depth, over a session's --colors.
        if SETTINGS.appearance.colors != depth:
            self.application.use_color_depth(SETTINGS.appearance.colors)
        # And the glyph tier, over a session's --glyphs: frames, marks, arrows
        # and the panels' icon gutter change on the next frame.
        if SETTINGS.appearance.glyphs != glyphs:
            self.application.use_glyphs(SETTINGS.appearance.glyphs)
        # And the check marks, over a session's --marks; every cluster on the
        # screen redraws, as it reads the application's choice.
        if SETTINGS.appearance.marks != marks:
            self.application.marks = SETTINGS.appearance.marks
            self.application.invalidate()
        # Only a change: Cancel, or OK on the same choice, leaves a session's
        # --language standing.  Every caption bound to it follows this batch.
        if SETTINGS.interface.language != before:
            language.apply(SETTINGS.interface.language)
            self.application.invalidate()
        # And the direction, over a session's --direction: the screen mirrors
        # or stops mirroring on the next frame.
        if SETTINGS.interface.direction != direction:
            self.application.direction = SETTINGS.interface.direction

    async def key_bindings(self) -> None:
        """Options > Configuration > Key bindings: the dialog over every key
        table as bound now; OK binds what it answers and writes
        ``keybindings.ini`` (on a thread).  A file that cannot be written is
        said so, and the keys stay bound for this session."""
        import asyncio

        from navigator.lib.config import keybindings
        from navigator.widgets.setup.key_bindings_dialog import KeyBindingsDialog

        app = self.application
        found = keybindings.sections(type(app))
        answer = await KeyBindingsDialog(found).execute(app)
        if answer is None:
            return
        keybindings.apply(found, answer)
        try:
            await asyncio.to_thread(keybindings.write, found, answer)
        except OSError as error:
            from navml.widgets.dialog.dialog import Dialog

            await Dialog(
                title=tr("Error"),
                prompt=tr("Cannot save the key bindings: {error}").format(error=error.strerror or error),
                buttons="ok",
            ).execute(app)

    async def on_game(self, event: Game) -> bool:
        """≡ > Game: ``TGameWindow`` -- the one game window, brought forward if
        it is open, else opened in the middle of the desktop (``ofCentered``)."""
        from navigator.widgets.game.game_window import GameWindow
        from navigator.widgets.game.game_window.game_window import HEIGHT, WIDTH

        if self.console_visible:
            self.toggle_console()
        desktop = self.desktop
        for window in desktop.windows():
            if isinstance(window, GameWindow):
                desktop.activate(window)
                return True
        window = desktop.open(GameWindow())
        width, height = min(WIDTH, desktop.width), min(HEIGHT, desktop.height)
        window.locate(max(0, (desktop.width - width) // 2), max(0, (desktop.height - height) // 2), width, height)
        window.glass.focus()
        return True

    async def on_open_trash(self, event: OpenTrash) -> bool:
        """Disk > Trash, and the trash can's double click: the file manager's
        active panel on the Trash (not DN's -- ``OpenTrash``'s docstring)."""
        manager = self.active_manager
        if manager is None:
            return False
        if self.console_visible:
            self.toggle_console()
        self.desktop.activate(manager)
        self.spawn(manager.open_trash())
        return True

    async def on_empty_trash(self, event: EmptyTrash) -> bool:
        manager = self.active_manager
        if manager is None:
            return False
        self.spawn(manager.empty_trash())
        return True

    async def rest(self, *, asked: bool = False) -> None:
        """``InsertIdler``: one of the selected savers, at random, until a key.

        A built-in one is :class:`ScreenSaver` over everything; an external
        one runs on the console as a command does, until it exits.  With
        none selected DN did nothing; ≡ > Screen rest, *asked*, brings
        *Star flight* then, a departure -- a menu item that did nothing
        looked broken.
        """
        import shlex

        from navigator.lib.appearance import savers
        from navigator.widgets.shell.screen_saver import KINDS, ScreenSaver

        app = self.application
        if app is None or self.resting:
            return
        names = SETTINGS.savers.names() or (["star_flight"] if asked else [])
        if not names:
            return
        name = random.choice(names)
        self.resting = True
        try:
            if name in KINDS:
                await ScreenSaver(name).execute(app)
            else:
                path = savers.savers_dir() / name
                if path.is_file() and not self.console.busy:
                    self.run_command(shlex.quote(str(path)), typed=False)
        finally:
            self.resting = False

    async def setup(self, dialog: Any, *sections: str) -> None:
        """Run a setup *dialog*, then apply what it accepted and save it.

        DN's ``ExecResource`` and ``cmUpdateConfig`` in one: the values are
        assigned to :data:`SETTINGS`, whose bindings repaint whatever shows
        them, and each section is written back to ``navigator.ini`` -- that
        section alone, over whatever the file holds now.  A dialog over one
        section answers that section's values; over several, a dict of them
        by section name, and of those only the sections whose values OK
        changed are assigned and written.  A file that cannot be written is
        said so, and the values stay applied for this session.
        """
        answer = await dialog.execute(self.application)
        if answer is None:
            return
        changes = answer if len(sections) > 1 else {sections[0]: answer}
        if len(sections) > 1:
            sections = tuple(
                name for name in sections
                if changes[name].items() - SETTINGS.section(name).values().items()
            )
        for name in sections:
            SETTINGS.section(name).update(changes[name])
        try:
            for name in sections:
                SETTINGS.save(section=name)
        except OSError as error:
            from navml.widgets.dialog.dialog import Dialog

            await Dialog(
                title=tr("Error"),
                prompt=tr("Cannot save the settings: {error}").format(error=error.strerror or error),
                buttons="ok",
            ).execute(self.application)

    # -- the directory tree window --------------------------------------------

    # -- File View History, File Edit History ---------------------------------

    async def file_history(self, kind: str) -> None:
        """``ViewHistoryMenu``/``EditHistoryMenu``: pick a file, open it as it was left.

        With the Interface option off the list is not shown, and DN's
        ``dlSetViewHistory``/``dlSetEditHistory`` says why; an empty history
        shows nothing at all, as ``Count = 0`` did.
        """
        from navml.widgets.dialog.dialog import Dialog

        from navigator.lib.config.file_history import open_editor, open_viewer
        from navigator.models.edit_record import EditRecord
        from navigator.models.view_record import ViewRecord
        from navigator.widgets.shell.file_history_dialog import FileHistoryDialog

        viewing = kind == "view"
        tracking = SETTINGS.interface.track_viewing if viewing else SETTINGS.interface.track_editing
        if not tracking:
            option = tr("Track viewing history") if viewing else tr("Track editing history")
            await Dialog(
                title=tr("Error"),
                prompt=tr('Set the interface option\n"{option}" ON first').format(option=option),
                buttons="ok",
            ).execute(self.application)
            return
        model = ViewRecord if viewing else EditRecord
        if not model.count():
            return
        title = tr("File View History") if viewing else tr("File Edit History")
        path = await FileHistoryDialog(model, title=title).execute(self.application)
        if path is None:
            return
        try:
            if viewing:
                await open_viewer(self.desktop, path)
            else:
                await open_editor(self.desktop, path)
        except OSError as error:
            await Dialog(
                title=tr("Cannot view file") if viewing else tr("Cannot edit file"),
                prompt=f"{path}: {error.strerror or error}",
                buttons="ok",
            ).execute(self.application)

    # -- File > View > Open..., File > Edit > Open... ---------------------------

    async def on_edit_named(self, event: EditNamed) -> bool:
        """Shift+F4 outside the panels -- in a viewer, the sheet or the data
        tree: DN's ``cmXEditFile``, on every status line.  The file manager
        in front asks (``Manager.edit_named``): a relative name is its active
        panel's, and the editor opens on its desktop.  With no manager open
        there is no panel to name a file from, and nothing is done."""
        manager = self.active_manager
        if manager is not None:
            manager.spawn(manager.edit_named())
        return True

    async def open_chosen(self, kind: str) -> None:
        """A file chosen in a file box, viewed or edited -- not DN's.

        The box opens on the active panel's directory when that is on the
        disk, else where Navigator was started, and lists dot-files as that
        panel does.  A name typed that is not there yet is a new file to the
        editor, as Shift+F4's is, and said so by the viewer.  With *Internal
        viewer* (*editor*) off the file goes to ``$PAGER`` (``$EDITOR``), as
        Shift+F4's does -- not through ``viewers.ini``/``editors.ini``, whose
        macros name the file at the panel's cursor rather than this one.
        """
        import errno
        import shlex

        from navml.widgets.dialog.dialog import Dialog
        from navml.widgets.dialog.file_dialog import FileDialog

        from navigator.lib.config.file_history import open_editor, open_viewer

        viewing = kind == "view"
        manager = self.active_manager
        panel = manager.active_panel if manager is not None else None
        directory = panel.path if panel is not None and panel.location.is_local else None
        hidden = panel.show_hidden if panel is not None else SETTINGS.system.show_hidden
        name = await FileDialog(
            title=tr("View file") if viewing else tr("Edit file"),
            label=tr("~F~ile name"),
            history_id="view_open" if viewing else "edit_open",
            directory=directory,
            hidden=hidden,
            ok_text=tr("~O~pen"),
        ).execute(self.application)
        if not name:
            return
        path = Path(name)
        internal = SETTINGS.system.internal_viewer if viewing else SETTINGS.system.internal_editor
        if not internal:
            if viewing and not await asyncio.to_thread(path.exists):
                await Dialog(title=tr("Cannot view file"), prompt=f"{path.name}: {os.strerror(errno.ENOENT)}",
                             buttons="ok").execute(self.application)
                return
            variable, fallback = ("PAGER", "less") if viewing else ("EDITOR", "vi")
            program = os.environ.get(variable, "").strip() or fallback
            self.run_command(f"{program} {shlex.quote(str(path))}")
            return
        try:
            if viewing:
                await open_viewer(self.desktop, path)
            else:
                await open_editor(self.desktop, path, new=not await asyncio.to_thread(path.exists))
        except OSError as error:
            await Dialog(
                title=tr("Cannot view file") if viewing else tr("Cannot edit file"),
                prompt=f"{path.name}: {error.strerror or error}",
                buttons="ok",
            ).execute(self.application)

    async def on_open_tree_window(self, event: OpenTreeWindow) -> bool:
        """Disk > Directory tree: a tree window, opened on the active panel's directory."""
        from navigator.widgets.tree.tree_window import TreeWindow

        manager = self.active_manager
        panel = manager.active_panel if manager is not None else None
        if panel is None:
            self.desktop.open(TreeWindow())
        else:
            start = panel.path if panel.location.is_local else None
            self.desktop.open(TreeWindow(start=start, hidden=panel.show_hidden))
        return True

    async def on_open_process_window(self, event: OpenProcessWindow) -> bool:
        from navigator.widgets.shell.process_window import ProcessWindow

        self.desktop.open(ProcessWindow())
        return True

    async def on_open_service_window(self, event: OpenServiceWindow) -> bool:
        """Utilities > Services: the system's services in a window."""
        from navigator.widgets.shell.service_window import ServiceWindow

        self.desktop.open(ServiceWindow())
        return True

    async def on_open_monitor_window(self, event: OpenMonitorWindow) -> bool:
        """Utilities > System monitor: the processors, the memory and the sensors in a window."""
        from navigator.widgets.shell.monitor_window import MonitorWindow

        self.desktop.open(MonitorWindow())
        return True

    async def on_open_volumes_window(self, event: OpenVolumesWindow) -> bool:
        """Disk > Volumes: the mounted volumes in a window."""
        from navigator.widgets.shell.volumes_window import VolumesWindow

        self.desktop.open(VolumesWindow())
        return True

    async def on_open_usage_window(self, event: OpenUsageWindow) -> bool:
        """Disk > Directory sizes: what takes the room under the active panel's
        directory -- on whatever drive it is -- in a window."""
        from navigator.widgets.shell.usage_window import UsageWindow

        manager = self.active_manager
        panel = manager.active_panel if manager is not None else None
        self.desktop.open(UsageWindow(start=panel.location if panel is not None else None, manager=manager))
        return True

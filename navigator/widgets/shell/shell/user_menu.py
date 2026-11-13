"""F2's user menu (navigator.lib.config.usermenu): finding, editing and running it.

A mixin of :class:`Shell` (``navkit.widget.Mixin``): methods only; its state,
keys and ``checks`` are in ``shell.py``.
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any

from navkit.i18n import tr

from navml.widgets.dialog.dialog import Dialog

from navigator.widgets.shell.commands import LocalMenuFileEdit, MenuFileEdit
from navigator.lib.config.associations import EDITORS
from navigator.settings import SETTINGS

if TYPE_CHECKING:
    from navigator.widgets.shell.shell import Shell as _Base
else:
    from navkit.widget import Mixin as _Base


class UserMenu(_Base):
    """F2's user menu (navigator.lib.config.usermenu): finding, editing and running it."""

    # -- F2: the user menu (navigator.lib.config.usermenu) ------------------------------------

    async def on_menu_file_edit(self, event: MenuFileEdit) -> bool:
        from navigator.lib.config.associations import MENU

        self.spawn(self.edit_associations(MENU))
        return True

    async def on_local_menu_file_edit(self, event: LocalMenuFileEdit) -> bool:
        from navigator.lib.config.usermenu import LOCAL_NAME

        self.spawn(self.edit_menu_file(self._menu_directory() / LOCAL_NAME))
        return True

    def _menu_directory(self) -> Path:
        """Where a local menu is looked for from: the active panel's directory."""
        return Path(self._command_directory() or Path.cwd())

    def _menu_panels(self) -> tuple[Any, Any]:
        """The active panel and the passive one if it is showing, as ``cmGetUserParams``."""
        manager = self.active_manager
        if manager is None:
            return None, None
        active, passive = manager.active_panel, manager.passive_panel
        # In Miller columns the passive panel is the active one: there is none.
        return active, (passive if passive.visible and passive is not active else None)

    @staticmethod
    def _menu_side(panel: Any, list_file: str = "-", use: Any = None) -> Any:
        """*panel* as the macros see it.  On another drive the directory is
        the one its files were fetched into (*use*, ``UseFile``), or -- for a
        caption, before anything is fetched -- the place's own name."""
        from navigator.lib.config.usermenu import Side

        if panel is None:
            return Side()
        entry = panel.selected
        if not panel.location.is_local:
            name = entry.name if entry is not None and not entry.is_dir else None
            if use is not None:
                return Side.of(use.directory, name, list_file)
            return Side.of(str(panel.location), name, list_file)
        if entry is None:
            return Side.of(Path(panel.path), None, list_file)
        # A *Find:* listing's entry is in a directory of its own.
        path = entry.path_in(Path(panel.path))
        return Side.of(path.parent, entry.name, list_file)

    async def edit_menu_file(self, path: Path) -> None:
        """A menu or ``.ini`` file in an editor, made by saving if it is not there yet.

        DN's ``EditFile(True, ...)`` for ``cmMenuFileEdit``, ``cmEditHGL``,
        ``cmExternalEditors``... (``DNUTIL.PAS:1952``): as F4 does, with
        *Internal editor* off ``editors.ini`` decides by the file's name, its
        macros naming this file, else ``$EDITOR`` (``vi``) on the console.
        """
        from navigator.lib.config.file_history import open_editor

        if not SETTINGS.system.internal_editor:
            import shlex

            from navigator.lib.config.usermenu import Side
            from navigator.widgets.editor.external import save_before_external

            async def ask() -> bool:
                return await save_before_external(self.application, [path])

            side = Side.of(path.parent, path.name, "-")
            if await self.run_associated(EDITORS, path.name, cwd=path.parent, side=side, before=ask):
                return
            if not await ask():
                return
            program = os.environ.get("EDITOR", "").strip() or "vi"
            self.run_command(f"{program} {shlex.quote(str(path))}")
            return
        if self.console_visible:
            self.toggle_console()
        try:
            await open_editor(self.desktop, path, new=True)
        except OSError as error:
            await Dialog(title=tr("Error"), prompt=tr("Cannot edit {path}: {error}").format(path=path, error=error.strerror or error),
                         buttons="ok").execute(self.application)

    async def user_menu(self, want_global: bool = False) -> None:
        """``ExecUserMenu``: the menu in a box in the middle of the screen, and
        the item chosen run in the console.

        The local ``.navigator-menu.ini`` -- the active panel's directory's, or
        the nearest above it -- else the global ``menu.ini``; F2 in the box changes between them,
        F4 edits the one shown, and a caption's own F-key, which outranks
        both, chooses its item.  Neither file: ``dlMNUNotFound``.
        """
        import asyncio

        from navml.widgets.menu.popup_menu import PopupMenu
        from navml.widgets.menu.sub_menu import SubMenu

        from navigator.lib.config.usermenu import caption, find_menu, global_menu, parse, preview

        app = self.application
        if app is None:
            return
        # A panel on another drive has no local menu to look for.
        remote = self._front_remote() is not None
        while True:
            found = await asyncio.to_thread(find_menu, self._menu_directory(), want_global or remote)
            if found is None:
                await Dialog(title=tr("Error"), prompt=tr("File {name} not found").format(name=global_menu()),
                             buttons="ok").execute(app)
                return
            path, is_global = found
            try:
                text = await asyncio.to_thread(path.read_text, encoding="utf-8", errors="replace")
                menu = parse(text, path, is_global)
            except (OSError, ValueError) as error:
                reason = error.strerror if isinstance(error, OSError) and error.strerror else error
                await Dialog(title=tr("Error"), prompt=tr("Cannot read {path}: {error}").format(path=path, error=reason),
                             buttons="ok").execute(app)
                return
            active, passive = (self._menu_side(panel) for panel in self._menu_panels())
            box_menu = SubMenu()
            items: dict[int, Any] = {}
            fkeys: dict[str, Any] = {}

            def fill(into: Any, entries: list[Any]) -> None:
                for entry in entries:
                    if entry.children:
                        fill(into.add_submenu(caption(entry, active, passive)), entry.children)
                    elif entry.is_line:
                        into.add_line()
                    else:
                        item = into.add_item(caption(entry, active, passive))
                        # What it will run, the panels' macros in (``preview``).
                        item.tooltip = preview(menu.commands(entry), active, passive)
                        items[id(item)] = entry
                        if entry.fkey:
                            fkeys.setdefault(entry.fkey, entry)

            fill(box_menu, menu.items)
            if not items:
                return
            # Which menu this is -- a departure, asked for: DN told the two
            # apart by its status line -- and that status line's two items
            # (``hcLUserMenu``/``hcGUserMenu``) on the key bar.
            if is_global:
                title, other = tr("User menu (global)"), tr("Local menu")
            else:
                title, other = tr("User menu (local)"), tr("Global menu")
            box = PopupMenu(box_menu, behind=self, keys=tuple(dict.fromkeys([*fkeys, "f2", "f4"])),
                            title=title, hints=(("F2", other), ("F4", tr("Edit"))))
            width, height = PopupMenu.measure(box_menu, app, self, title)
            box.at = ((app.root.width - width) // 2, (app.root.height - height) // 2)
            chosen = await box.execute(app)
            pressed = box.pressed
            if pressed in fkeys:
                entry = fkeys[pressed]
            elif pressed == "f2":
                want_global = not is_global
                continue
            elif pressed == "f4":
                await self.edit_menu_file(path)
                return
            elif chosen is None:
                return
            else:
                entry = items.get(id(chosen))
                if entry is None:
                    return
            await self.run_menu_item(menu, entry)
            return

    async def run_menu_item(self, menu: Any, entry: Any) -> None:
        """An item's lines, run as :meth:`run_commands` runs them."""
        await self.run_commands(menu.commands(entry))

    async def run_commands(self, commands: Any, *, cwd: Path | None = None, uses: list[Any] = (),
                           side: Any = None) -> None:
        """A user menu item's lines -- or an ``.ini`` entry's
        (:mod:`navigator.lib.config.associations`) -- its parameters asked first if it
        wants them, run in the console as a script the shell sources.

        ``%1`` and ``%2`` are files listing each panel's tagged names, or the
        one at its cursor (``GetUserParams``); they, and the script, are kept
        under fixed names in Navigator's own temporary directory
        (:func:`navigator.lib.system.tempdir.private_dir`), as DN's ``$DN$.BAT`` and
        ``$$$DN$$.LST`` were in its swap directory.

        *side* stands for the active panel in the macros (``!.!`` and the
        like): the file an Options edit names, which is not the panel's.
        """
        import asyncio
        import shlex

        from navigator.lib.system.tempdir import private_dir
        from navigator.lib.config.usermenu import script_text
        from navigator.widgets.shell.menu_params_dialog import MenuParamsDialog

        app = self.application
        params = ""
        if commands.asks:
            answer = await MenuParamsDialog(commands.title, commands.default).execute(app)
            if answer is None:
                return
            params = answer
        if not commands.lines:
            return
        active_panel, passive_panel = self._menu_panels()

        def names(panel: Any) -> list[str] | None:
            if panel is None:
                return None
            marked = panel.marked_entries
            if marked:
                return [entry.name for entry in marked]
            return [panel.selected.name] if panel.selected is not None else []

        lists = (names(active_panel), names(passive_panel))
        given, uses = list(uses), []
        for panel in (active_panel, passive_panel):
            use = None
            if panel is not None and not panel.location.is_local:
                use = await self._use_panel_files(panel)
                if use is False:
                    return
            uses.append(use)

        # A window's script and lists are its own (``-N``), as it may still
        # be reading them when the next item writes the console's.
        window = commands.window if not commands.panelize else None
        written: list[Path] = []
        shown: list[str] = []

        def write() -> Path:
            directory = private_dir()
            suffix = ""
            if window is not None:
                number = 1
                while (directory / f"usermenu-{number}.sh").exists():
                    number += 1
                suffix = f"-{number}"
            files = []
            for name, listed in zip((f"active{suffix}.lst", f"passive{suffix}.lst"), lists):
                if listed is None:
                    files.append("-")
                    continue
                target = directory / name
                written.append(target)
                target.write_text("".join(f"{line}\n" for line in listed), encoding="utf-8",
                                  errors="surrogateescape")
                files.append(str(target))
            script = directory / f"usermenu{suffix}.sh"
            written.append(script)
            active = side if side is not None else self._menu_side(active_panel, files[0], uses[0])
            passive = self._menu_side(passive_panel, files[1], uses[1])
            text = script_text(commands, active, passive, str(script), params)
            shown.append("; ".join(text.splitlines()))
            script.write_text(text, encoding="utf-8", errors="surrogateescape")
            return script

        try:
            script = await asyncio.to_thread(write)
        except OSError as error:
            await Dialog(title=tr("Error"), prompt=tr("Cannot write the menu's script: {error}").format(error=error.strerror or error),
                         buttons="ok").execute(app)
            return
        fetched = [*given, *(use for use in uses if use is not None)]
        if cwd is None and uses and uses[0] is not None:
            cwd = uses[0].directory
        if commands.panelize:
            # ``<|``: the script's output is the active panel's listing.
            await self._panelize(f". {shlex.quote(str(script))}", fetched)
            return
        if window is not None:
            self.run_in_window(f". {shlex.quote(str(script))}", cwd=cwd, zoomed=window.zoomed,
                               modal=window.modal, closes=window.closes, uses=fetched, cleanup=written,
                               title=shown[0] if shown else None)
            return
        elsewhere = {"cwd": cwd, "uses": fetched} if cwd is not None or fetched else {}
        self.run_command(f". {shlex.quote(str(script))}", typed=False, **elsewhere)

    async def _use_panel_files(self, panel: Any) -> Any:
        """``UseFile`` for *panel* on another drive: its tagged files -- or
        the one at its cursor -- fetched into a directory of their own.  None
        with no file to fetch, False when the fetch failed or was stopped."""
        from navigator.widgets.drives.use_file import materialize

        entries = panel.marked_entries or ([panel.selected] if panel.selected is not None else [])
        files = [panel.entry_location(entry) for entry in entries if not entry.is_dir]
        if not files:
            return None
        use = await materialize(self.application, files)
        return use if use is not None else False

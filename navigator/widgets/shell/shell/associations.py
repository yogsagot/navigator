"""What Enter, F3/F4 and Quick run do with a file: extensions.ini, viewers.ini, editors.ini,
quickrun.ini, the desktop's applications and Open with.

A mixin of :class:`Shell` (``navkit.widget.Mixin``): methods only; its state,
keys and ``checks`` are in ``shell.py``.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import TYPE_CHECKING, Any

from navkit.i18n import tr

from navml.widgets.dialog.dialog import Dialog

from navigator.lib.drives import Location
from navigator.widgets.shell.commands import EditHGL, EditMacros, QuickRun
from navigator.lib.config.associations import EXTENSIONS, HIGHLIGHT, QUICK_RUN
from navigator.settings import SETTINGS

if TYPE_CHECKING:
    from navigator.widgets.shell.shell import Shell as _Base
else:
    from navkit.widget import Mixin as _Base


class Associations(_Base):
    """What Enter, F3/F4 and Quick run do with a file: extensions.ini, viewers.ini, editors.ini,"""

    # -- extensions.ini, viewers.ini, editors.ini, quickrun.ini ----------------

    async def on_open_file(self, event: Any) -> bool:
        """Enter on a file that is not itself a program: ``ExecFile`` -- what
        ``extensions.ini`` says for its name (DN's ``DN.EXT``), else the
        desktop's application for it (:meth:`open_on_desktop`), else nothing."""
        if self.console.busy:
            return True
        if isinstance(event.path, Location) and not event.path.is_local:
            self.spawn(self._open_elsewhere(event.path))
        else:
            self.spawn(self._open_here(Path(event.path)))
        return True

    async def _open_here(self, path: Path) -> None:
        if not await self.run_associated(EXTENSIONS, path.name):
            await self.open_on_desktop(path)

    @staticmethod
    def desktop_opens() -> bool:
        """Whether Enter on a file ``extensions.ini`` has nothing for opens it
        in the desktop's application: *Pass other files to desktop* on, and
        ``gio``, KIO or ``xdg-open`` and a display to open it on."""
        from navigator.lib.system import desktop

        return SETTINGS.file_manager.open_unassociated and desktop.opener() is not None and desktop.graphical()

    async def open_on_desktop(self, path: Path) -> bool:
        """*path* opened in the desktop's default application for its type
        (``gio open``, ``kioclient exec``, else ``xdg-open``) -- not DN's, where a file
        ``DN.EXT`` had no line for did nothing; nor here with *Pass other
        files to desktop* off.  A failure is said.  True when it was handed over."""
        from navigator.lib.system import desktop
        from navml.widgets.dialog.control import escape_caption

        if not self.desktop_opens():
            return False
        try:
            await asyncio.to_thread(desktop.open_file, path)
        except OSError as error:
            await Dialog(title=tr("Error"), buttons="ok", prompt=tr("Cannot open {path}: {error}").format(
                path=escape_caption(str(path)), error=escape_caption(error.strerror or str(error)),
            )).execute(self.application)
            return False
        return True

    async def open_with(self, origin: Location) -> None:
        """File > *Open with*: the applications the desktop has for *origin*'s
        type, in a box, the default first and marked, and the file opened in
        the one chosen (``gio launch``, ``kstart``).  Under them, as GNOME's
        and Xfce's have it, *Other applications* (every other installed one,
        :func:`~navigator.lib.system.desktop.other_applications`), *Set
        default* (the same two layers again: the one chosen becomes what the
        type opens in, and nothing is opened) and *Command...*: a command line
        of the user's own (:meth:`open_with_command`).  Not DN's.

        A file on another drive is typed by its name, and fetched
        (``UseFile``) only once an application is chosen: nothing waits for a
        desktop application, so what it changes is not sent back.
        """
        import mimetypes

        from navigator.lib.system import desktop
        from navml.widgets.dialog.control import escape_caption
        from navml.widgets.menu.popup_menu import PopupMenu
        from navml.widgets.menu.sub_menu import SubMenu

        app = self.application
        try:
            if origin.is_local:
                mime = await asyncio.to_thread(desktop.content_type, Path(origin.local))
            else:
                mime = mimetypes.guess_type(origin.name)[0] or ""
            apps = await asyncio.to_thread(desktop.applications, mime)
            others = await asyncio.to_thread(desktop.other_applications, apps)
        except OSError as error:
            await Dialog(title=tr("Open with"), buttons="ok",
                         prompt=escape_caption(error.strerror or str(error))).execute(app)
            return
        box_menu = SubMenu()
        #: Each application's item: the application, and whether it is set as the default.
        chosen_of: dict[int, tuple[Any, bool]] = {}
        self._fill_open_with(box_menu, apps, others, chosen_of, setting=False)
        if apps or others:
            box_menu.add_line()
        defaults = box_menu.add_submenu(tr("Set ~d~efault"))
        self._fill_open_with(defaults, apps, others, chosen_of, setting=True)
        defaults.disabled = not mime or not (apps or others)
        command = box_menu.add_item(tr("~C~ommand..."))
        title = tr("Open with ({type})").format(type=mime) if mime else tr("Open with")
        box = PopupMenu(box_menu, behind=self, title=title)
        width, height = PopupMenu.measure(box_menu, app, self, title)
        box.at = ((app.root.width - width) // 2, (app.root.height - height) // 2)
        chosen = await box.execute(app)
        if chosen is command:
            await self.open_with_command(origin)
            return
        if chosen is None or id(chosen) not in chosen_of:
            return
        application, setting = chosen_of[id(chosen)]
        if setting:
            try:
                await asyncio.to_thread(desktop.set_default, mime, application)
            except OSError as error:
                await Dialog(title=tr("Set default"), buttons="ok",
                             prompt=escape_caption(error.strerror or str(error))).execute(app)
                return
            self.toast(tr("{name} now opens {type}").format(name=application.name, type=mime),
                       title=tr("Set default"))
            return
        path: Path
        if origin.is_local:
            path = Path(origin.local)
        else:
            from navigator.widgets.drives.use_file import materialize

            use = await materialize(app, [origin])
            if use is None:
                return
            path = use.local_for(origin) or use.directory / origin.name
        try:
            await asyncio.to_thread(desktop.launch, application, path)
        except OSError as error:
            await Dialog(title=tr("Open with"), buttons="ok",
                         prompt=escape_caption(error.strerror or str(error))).execute(app)

    @staticmethod
    def _fill_open_with(menu: Any, apps: list[Any], others: list[Any],
                        chosen_of: dict[int, tuple[Any, bool]], *, setting: bool) -> None:
        """*Open with*'s layers into *menu*: the type's own applications (the
        default marked), then *Other applications* in a box of their own;
        each item recorded in *chosen_of* with *setting*."""
        from navml.widgets.dialog.control import escape_caption

        for each in apps:
            name = escape_caption(each.name)
            caption = tr("{name} (default)").format(name=name) if each.default else name
            chosen_of[id(menu.add_item(caption))] = (each, setting)
        if not others:
            return
        if apps:
            menu.add_line()
        other = menu.add_submenu(tr("~O~ther applications"))
        other.filterable = True
        other.centred = True
        other.footer = tr("Type to filter")
        for each in others:
            chosen_of[id(other.add_item(escape_caption(each.name)))] = (each, setting)

    @staticmethod
    def open_with_history(name: str) -> str:
        """The history *Open with*'s command line keeps for a file called
        *name*: one per extension, case aside (``open_with.png``), and one
        for the names that have none (``open_with``)."""
        extension = Path(name).suffix.lower().lstrip(".")
        return f"open_with.{extension}" if extension else "open_with"

    @staticmethod
    def open_with_line(text: str) -> str:
        """*text* as the line that runs: the user menu's language, so ``!.!``
        and the rest are put in; with no ``!`` macro in it, the file's name
        goes on the end (``gimp`` runs ``gimp !.!``)."""
        return text if "!" in text else f"{text} !.!"

    async def open_with_command(self, origin: Location) -> bool:
        """*Open with*'s *Command...*: a command line asked -- its history the
        file's extension's own (:meth:`open_with_history`) -- and run in the
        console as an ``extensions.ini`` entry is (:meth:`run_commands`):
        the user menu's macros work, and a file on another drive is fetched
        first and sent back once the command ends.  True once it ran."""
        from navigator.lib.config.usermenu import commands_of
        from navigator.widgets.shell.edit_line_dialog import EditLineDialog

        box = EditLineDialog("", history=self.open_with_history(origin.name),
                             caption=tr("~C~ommand (!.! is the file; else it goes at the end)"))
        # After construction: the markup's own *Edit History* is bound in ``__init__``.
        box.title = tr("Open with")
        text = await box.execute(self.application)
        text = (text or "").strip()
        if not text or self.console.busy:
            return False
        await self.run_commands(commands_of([self.open_with_line(text)]))
        return True

    async def _open_elsewhere(self, origin: Location) -> None:
        """Enter on a file on another drive: ``UseFile``, then what
        ``extensions.ini`` says for it, run beside the local copy -- which
        goes back up if the program changed it."""
        from navigator.lib.drives import usefile
        from navigator.widgets.drives.use_file import materialize

        use = await materialize(self.application, [origin])
        if use is None:
            return
        if await self.run_associated(EXTENSIONS, origin.name, cwd=use.directory, uses=[use]):
            return
        # The desktop's application on the copy, which stays: nothing waits
        # for it to be done, so nothing is sent back either.
        if not await self.open_on_desktop(use.local_for(origin) or use.directory / origin.name):
            await asyncio.to_thread(usefile.discard, use)

    async def on_quick_run(self, event: QuickRun) -> bool:
        """Ctrl+Shift+F1 .. F10: ``QuickExecExternal`` -- ``quickrun.ini``'s
        ``[F1]`` .. ``[F10]`` (DN's ``DN.XRN``); a key with no section does nothing."""
        if not self.console.busy:
            self.spawn(self.run_associated(QUICK_RUN, key=f"F{event.number}"))
        return True

    async def run_associated(self, file_name: str, name: str | None = None, *,
                             key: str | None = None, cwd: Path | None = None,
                             uses: list[Any] = (), side: Any = None, before: Any = None) -> bool:
        """Run what *file_name* (one of :mod:`navigator.lib.config.associations`' four)
        has for the file called *name*, or for *key*; False when it has
        nothing, so the caller does what it did without one.

        One entry runs at once; several are offered in a menu in the middle
        of the screen, their captions' macros put in, and Esc runs none (and
        still answers True: the file had something).  A file that will not
        read, or is not an ``.ini``, is said so.
        """
        import asyncio

        from navigator.lib.config import associations
        app = self.application
        if app is None:
            return False
        try:
            groups = await asyncio.to_thread(associations.read, file_name)
        except (OSError, ValueError) as error:
            reason = error.strerror if isinstance(error, OSError) and error.strerror else error
            await Dialog(title=tr("Error"), prompt=tr("Cannot read {path}: {error}").format(path=file_name, error=reason),
                         buttons="ok").execute(app)
            return True
        group = (associations.for_key(groups, key) if key is not None
                 else associations.for_file(groups, name or ""))
        if group is None:
            return False
        if before is not None and not await before():
            # *before* said no (a changed editor window kept): nothing runs.
            return True
        action = group.actions[0]
        if len(group.actions) > 1:
            action = await self.choose_action(group.actions)
            if action is None:
                return True
        elsewhere = {"cwd": cwd, "uses": uses} if cwd is not None or uses else {}
        if side is not None:
            elsewhere["side"] = side
        await self.run_commands(action.commands, **elsewhere)
        return True

    async def choose_action(self, actions: Any, title: str | None = None) -> Any:
        """A ``PopupMenu`` of *actions*' captions, as F2's box is shown: the one chosen, or None.

        *title* is the box's, "Choose action" unless given."""
        from navml.widgets.menu.popup_menu import PopupMenu
        from navml.widgets.menu.sub_menu import SubMenu

        from navigator.lib.config.usermenu import expand

        app = self.application
        active, passive = (self._menu_side(panel) for panel in self._menu_panels())
        box_menu = SubMenu()
        chosen_of = {id(box_menu.add_item(expand(action.caption, active, passive, quote=False))): action
                     for action in actions}
        title = title or tr("Choose action")
        box = PopupMenu(box_menu, behind=self, title=title)
        width, height = PopupMenu.measure(box_menu, app, self, title)
        box.at = ((app.root.width - width) // 2, (app.root.height - height) // 2)
        chosen = await box.execute(app)
        return chosen_of.get(id(chosen)) if chosen is not None else None

    async def on_edit_hgl(self, event: EditHGL) -> bool:
        self.spawn(self.edit_associations(HIGHLIGHT))
        return True

    async def on_edit_macros(self, event: EditMacros) -> bool:
        from navigator.lib.config.associations import MACROS

        self.spawn(self.edit_associations(MACROS))
        return True

    async def edit_associations(self, file_name: str) -> None:
        """Options > Quick run file edit, Extension file edit, Viewers or
        Editors: the file in an editor, written first from its template
        (:func:`navigator.lib.config.associations.seed`) should it have gone since
        Navigator started."""
        import asyncio

        from navigator.lib.config import associations
        path = associations.path_of(file_name)
        try:
            await asyncio.to_thread(associations.seed, file_name)
        except OSError as error:
            await Dialog(title=tr("Error"), prompt=tr("Cannot write {path}: {error}").format(path=path, error=error.strerror or error),
                         buttons="ok").execute(self.application)
            return
        await self.edit_menu_file(path)

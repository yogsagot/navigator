"""Options > Colors: the palette changed, stored and loaded, and the desktop's background.

A mixin of :class:`Shell` (``navkit.widget.Mixin``): methods only; its state,
keys and ``checks`` are in ``shell.py``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
import asyncio
from pathlib import Path

from navkit.i18n import tr
from navkit.stylesheet import StylesheetError

from navml.widgets.dialog.dialog import Dialog

from navigator.widgets.shell.commands import ShowBackground

if TYPE_CHECKING:
    from navigator.widgets.shell.shell import Shell as _Base
else:
    from navkit.widget import Mixin as _Base


class Colors(_Base):
    """Options > Colors: the palette changed, stored and loaded, and the desktop's background."""

    # -- the palette ------------------------------------------------------------------

    async def _palette_base(self) -> tuple[list[tuple[str, str]], dict[str, str]] | None:
        """The theme's sheets, read on a thread, and every entry's variables
        as the theme alone gives them -- what a palette is the difference
        from.  None, said so, if the theme cannot be read."""
        import asyncio

        from navigator.lib.appearance.palette import entry_values
        from navigator.lib.appearance.scheme import scheme_from, theme_sources

        try:
            sources = await asyncio.to_thread(theme_sources, self.theme)
        except (OSError, LookupError) as error:
            await self._palette_failed(tr("Cannot read the theme: {error}").format(error=getattr(error, 'strerror', None) or error))
            return None
        return sources, entry_values(scheme_from(sources).variables)

    async def _palette_failed(self, prompt: str) -> None:
        await Dialog(title=tr("Error"), prompt=prompt, buttons="ok").execute(self.application)

    async def _keep_palette(self, sources: list[tuple[str, str]], palette: dict[str, str]) -> None:
        """*palette* (what differs from the theme) painted and kept as
        ``palette.nss`` -- DN's ``cmUpdateConfig`` after its palette changed."""
        import asyncio

        from navigator.lib.appearance.palette import render_palette, save_palette
        from navigator.lib.appearance.scheme import palette_source, scheme_from

        self.stylesheet = scheme_from(sources, palette_source(render_palette(palette, "palette")))
        try:
            await asyncio.to_thread(save_palette, palette, self.theme)
        except OSError as error:
            await self._palette_failed(tr("Cannot save the palette: {error}").format(error=error.strerror or error))

    async def change_colors(self) -> None:
        """Options > Colors: ``ChangeColors`` -- the dialog over the palette as
        it is, every change painted as it is made; OK keeps it, Cancel puts
        the screen back as it was."""
        from navigator.lib.appearance.palette import differences, entry_values, render_palette
        from navigator.lib.appearance.scheme import palette_source, scheme_from
        from navigator.widgets.setup.colors_dialog import ColorsDialog

        base = await self._palette_base()
        if base is None:
            return
        sources, theme = base
        before = self.stylesheet

        def apply(values: dict[str, str]) -> None:
            text = render_palette(differences(theme, values), "palette")
            try:
                self.stylesheet = scheme_from(sources, palette_source(text))
            except StylesheetError:
                pass  # a value the sheet refuses: the screen stays as it was

        answer = await ColorsDialog(entry_values(before.variables), apply).execute(self.application)
        if answer is None:
            self.stylesheet = before
            return
        await self._keep_palette(sources, differences(theme, answer))

    async def store_colors(self) -> None:
        """Options > Store palette: ``StoreColors`` -- every entry's colours
        and attributes written as a sheet, named in a file box opened on the
        user's themes (DN's ``COLORS\\*.PAL``), whose name ``--theme`` then
        takes.  A file that is there is asked about first."""
        import asyncio

        from navml.widgets.dialog.file_dialog import FileDialog

        from navigator.lib.appearance.palette import entry_values, render_palette, user_themes, write_sheet

        directory = user_themes()
        try:
            await asyncio.to_thread(directory.mkdir, parents=True, exist_ok=True)
        except OSError as error:
            await self._palette_failed(tr("Cannot make {path}: {error}").format(path=directory, error=error.strerror or error))
            return
        name = await FileDialog(title=tr("Store Color Palette"), label=tr("~F~ile name"), history_id="colors",
                                directory=directory, wildcard="*.nss").execute(self.application)
        if not name:
            return
        path = Path(name)
        if not path.suffix:
            path = path.with_suffix(".nss")
        if await asyncio.to_thread(path.exists):
            answer = await Dialog(title=tr("Warning"),
                                  prompt=tr("File {name}\nalready exists.\nOK to overwrite it?").format(name=path.name),
                                  buttons="yes-no").execute(self.application)
            if answer is not True:
                return
        text = render_palette(entry_values(self.stylesheet.variables), f"{path.stem} -- a palette stored by Navigator")
        try:
            await asyncio.to_thread(write_sheet, path, text)
        except OSError as error:
            await self._palette_failed(tr("Cannot write {path}: {error}").format(path=path, error=error.strerror or error))

    async def load_colors(self) -> None:
        """Options > Load palette: ``LoadColors`` -- a sheet picked in a file
        box (the user's themes if there are any, else the ones Navigator
        ships), its colours put over the theme and kept as the palette, as
        DN's ``LoadPalFromFile`` replaced the one in ``DN.CFG``.  One that does
        not parse is said so and changes nothing.  With *Preview palette*
        ticked the box paints each file the cursor stops on; cancelling it
        puts the screen back as it was."""
        import asyncio

        from navigator.lib.appearance.palette import differences, entry_values, user_themes
        from navigator.lib.appearance.scheme import THEMES, scheme_from
        from navigator.widgets.setup.palette_file_dialog import PaletteFileDialog

        def start() -> Path:
            mine = user_themes()
            return mine if any(mine.glob("*.nss")) else THEMES

        base = await self._palette_base()
        if base is None:
            return
        sources, theme = base
        before = self.stylesheet

        def preview(shown: tuple[Path, str] | None) -> None:
            if shown is None:
                self.stylesheet = before
                return
            path, text = shown
            try:
                self.stylesheet = scheme_from(sources, (str(path), text))
            except StylesheetError:
                pass  # not a palette: the screen stays as it was

        directory = await asyncio.to_thread(start)
        name = await PaletteFileDialog(title=tr("Load Color Palette"), label=tr("~F~ile name"), history_id="colors",
                                       directory=directory, wildcard="*.nss", ok_text=tr("~O~pen"),
                                       preview=preview).execute(self.application)
        self.stylesheet = before
        if not name:
            return
        path = Path(name)
        try:
            text = await asyncio.to_thread(path.read_text, encoding="utf-8")
        except (OSError, UnicodeError) as error:
            await self._palette_failed(tr("Cannot read {path}: {error}").format(path=path, error=getattr(error, 'strerror', None) or error))
            return
        try:
            loaded = scheme_from(sources, (str(path), text))
        except StylesheetError as error:
            await self._palette_failed(tr("Not a palette:\n{error}").format(error=error))
            return
        await self._keep_palette(sources, differences(theme, entry_values(loaded.variables)))

    async def on_show_background(self, event: ShowBackground) -> bool:
        """Window > *Background operation*: a box sent away put back up --
        the one there is, or the one chosen from a list of them all."""
        from navigator.lib.system.background import BACKGROUND

        if len(BACKGROUND.jobs) > 1:
            self.spawn(self.choose_background())
        else:
            BACKGROUND.recall()
        return True

    async def choose_background(self) -> None:
        """Every operation in the background in a box, oldest first, as the
        menu bar's mark lists them: what each was started on and how far it
        is, or that it waits.  The cursor starts on one with a question,
        else on the newest; the one chosen has its box back."""
        from navml.widgets.dialog.control import escape_caption
        from navml.widgets.menu.popup_menu import PopupMenu
        from navml.widgets.menu.sub_menu import SubMenu

        from navigator.lib.system.background import BACKGROUND

        app = self.application
        jobs = BACKGROUND.jobs
        box_menu = SubMenu()
        chosen_of = {}
        for number, entry in enumerate(jobs, 1):
            if entry.asking:
                line = tr("{operation}: waiting for an answer").format(operation=entry.subject)
            else:
                line = tr("{operation}: {percent}% done").format(operation=entry.subject, percent=entry.percent)
            # Numbered for a key each, as DN's lists of windows were.
            hotkey = f"~{number}~ " if number < 10 else "  "
            chosen_of[id(box_menu.add_item(hotkey + escape_caption(line)))] = entry
        waiting = [index for index, entry in enumerate(jobs) if entry.asking]
        title = tr("Background operations")
        box = PopupMenu(box_menu, behind=self, title=title, current=waiting[0] if waiting else len(jobs) - 1)
        width, height = PopupMenu.measure(box_menu, app, self, title)
        box.at = ((app.root.width - width) // 2, (app.root.height - height) // 2)
        chosen = await box.execute(app)
        entry = chosen_of.get(id(chosen)) if chosen is not None else None
        # It may have ended while the box was up.
        if entry is not None and entry in BACKGROUND.jobs:
            BACKGROUND.recall(entry)

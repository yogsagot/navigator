"""The command line: its prompt and directory, following the front panel, recalling commands,
inserting names, and which keys a running program keeps.

A mixin of :class:`Shell` (``navkit.widget.Mixin``): methods only; its state,
keys and ``checks`` are in ``shell.py``.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from navkit.events import KeyEvent
from navkit.reactive import untracked

from navml.history import HISTORY

from navigator.lib.drives import DriveGone, Location, drive_of
from navigator.lib.system.title import window_title
from navigator.lib.appearance import filetypes
from navigator.lib.config.associations import HIGHLIGHT
from navigator.settings import SETTINGS
from navigator.widgets.manager.manager import Manager
from navigator.widgets.shell.shell.helpers import _escape

if TYPE_CHECKING:
    from navigator.widgets.editor.edit_window import FileSaved
    from navigator.widgets.shell.shell import Shell as _Base
else:
    from navkit.widget import Mixin as _Base


class CommandLineMixin(_Base):
    """The command line: its prompt and directory, following the front panel, recalling commands,"""

    def _size_histories(self) -> None:
        """Interface's *History size* is how long every input-line list grows.

        navml's store keeps DN's 20 unless told otherwise, and knows nothing of
        Navigator's settings, so it is told from here.
        """
        HISTORY.limit = max(1, SETTINGS.interface.history_size)

    def _use_highlight_groups(self) -> None:
        """*Highlight groups*' masks put in force, and every panel read again
        when they changed: ``SetHighlightGroups``' ``cmPanelReread``, since a
        row's colour and its place under *Group* both come from them.

        ``filetypes`` knows nothing of Navigator's settings, so it is told from here.
        """
        section = SETTINGS.highlight_groups
        masks = {key: getattr(section, key) for key in filetypes.CUSTOM}
        # What this shell last saw rather than what ``use_masks`` answers: the
        # masks are the process's, and another shell may have put them in force.
        seen, self._highlight_masks = self._highlight_masks, masks
        filetypes.use_masks(masks)
        with untracked():
            if seen is not None and seen != masks and self.desktop is not None:
                for window in self.desktop.windows():
                    if isinstance(window, Manager):
                        for panel in window.all_panels:
                            panel.reload()

    def _choose_clipboard(self) -> None:
        """System Setup's *Use system clipboard*: the desktop's, or Navigator's own.

        navkit's application knows nothing of Navigator's settings either.
        """
        app = self.application
        if app is not None:
            app.system_clipboard = SETTINGS.system.system_clipboard

    def _front_location(self) -> Location | None:
        """Where the active panel is in the file manager in front, if one is open."""
        window = self.desktop.active_window
        manager = window if isinstance(window, Manager) else self.active_manager
        return manager.active_panel.location if manager is not None else None

    def _front_directory(self) -> Path | None:
        """The active panel's directory in the file manager in front, if one is
        open and it is on the local disk: the shell cannot follow a panel onto
        another drive, and stays in the last local directory it was in."""
        where = self._as_the_shell_sees(self._front_location())
        return where.local if where is not None and where.is_local else None

    def _front_remote(self) -> Location | None:
        """The active panel's place in front when it is on another drive."""
        where = self._as_the_shell_sees(self._front_location())
        return where if where is not None and not where.is_local else None

    def _as_the_shell_sees(self, where: Location | None) -> Location | None:
        """*where*, or its own place on the disk if it is ``root:`` and the
        console's shell is root's: that shell can be there, so the command
        line shows its prompt, follows the panel there and runs there."""
        if where is not None and self.console.root:
            from navigator.lib.drives import root

            return root.on_disk(where)
        return where

    @staticmethod
    def _remote_name(where: Location) -> str:
        """What the prompt and the title call a place on another drive: its
        drive's ``GetDir``."""
        try:
            return drive_of(where).get_dir(where)
        except DriveGone:
            return str(where)

    def _follow_panel(self) -> None:
        """Keep the idle shell where the panel is, so its prompt names that directory."""
        where = self._front_directory()
        if where is not None:
            self.console.subshell.sync(where)

    def _name_window(self) -> None:
        """Keep the terminal's title on the directory the prompt names."""
        remote = self._front_remote()
        if remote is not None:
            application = self.application
            if application is not None:
                application.title = window_title(None, self.console.root).replace(
                    " — ", f" {self._remote_name(remote)} — ", 1)
            return
        where = self._front_directory()
        if where is None:
            where = self.console.subshell.cwd or self.console.cwd
        title = window_title(Path(where) if where is not None else None, self.console.root)
        application = self.application
        if application is not None:
            application.title = title

    def _command_directory(self) -> Path | None:
        """Where a command runs: the active panel's directory -- or, with the
        panel on another drive, where the shell last was on the disk."""
        manager = self.active_manager
        if manager is not None:
            where = self._as_the_shell_sees(manager.active_panel.location)
            if where is not None and where.is_local:
                return where.local
        return self.console.subshell.cwd or self.console.cwd

    @property
    def program_has_keys(self) -> bool:
        """A command is running on the console and the console holds the keyboard.

        DOS Navigator was not running at all while a command was: the program
        had every key.  So every command this screen handles steps aside --
        F10 is ``htop``'s and ``mc``'s way out, Enter, Home and End are the
        program's -- and a disabled command's key falls through to the
        console, which sends it on.  The application asks the same question,
        so Ctrl+O -- ``mc``'s panel toggle, ``nano``'s Write Out -- goes to the
        program as well, and the way back to the panels is to leave it.

        Or a command in a window of its own is running and has the keyboard
        (``TerminalView``): it gets every key the same way, but for the ones
        that bring another window forward, which it declines itself.
        """
        if self.console.busy and self.console.focused:
            return True
        from navigator.widgets.shell.terminal_view import TerminalView

        app = self.application
        focused = app.focused if app is not None else None
        return isinstance(focused, TerminalView) and focused.busy

    async def on_new_view(self, event: Any) -> bool:
        """Window > *New view* with no editor in front: nothing to do -- here
        only so it is greyed with a reason (:meth:`refusal`); an editor's
        window, nearer the keyboard, takes it first."""
        return True

    def _editor_has_keys(self) -> bool:
        """Whether the keyboard is with a widget that edits text of its own.

        An editor wants Enter, Home, End and Tab for itself, and would lose
        them to a command line with text on it -- the application's table is
        asked before the tree.  DN's command line lived in the file panel's
        window and never met the editor's keys.
        """
        app = self.application
        if app is None or app.focused is None:
            return False
        widget = app.focused
        while widget is not None:
            if widget.edits_text:
                return True
            widget = widget.parent
        return False

    async def on_file_saved(self, event: FileSaved) -> bool:
        """``FileChanged`` (``MICROED.PAS:1298``): every panel showing the saved
        file's directory re-reads, and so does every information panel
        (``cmRereadInfo``) and every tree's count for that directory
        (``cmRereadTree``).

        ``highlight.ini`` saved colours every open text again by its new rules.
        A file to land on gets the cursor (``FileSaved.land``).
        """
        from navigator.lib.config import associations
        from navigator.widgets.editor.file_editor import FileEditor
        from navigator.widgets.tree.directory_tree import DirectoryTree
        from navigator.widgets.viewer.file_viewer import FileViewer

        directory = event.path.parent
        rules = event.path == associations.path_of(HIGHLIGHT)
        for window in self.desktop.windows():
            if isinstance(window, Manager):
                for panel in window.all_panels:
                    if panel.location == Location.of(directory):
                        panel.reload(key=event.path.name if event.land else None)
                window.reread_info()
        pending = [self.desktop]
        while pending:
            widget = pending.pop()
            if isinstance(widget, DirectoryTree):
                widget.file_changed(directory)
            pending.extend(widget.children)
        for window in self.desktop.windows():
            # Utilities > Services: a unit file it opened, saved -- daemon-reload.
            saved = getattr(window, "unit_file_saved", None)
            if saved is not None:
                saved(event.path)
        if rules:
            pending = [self.desktop]
            while pending:
                widget = pending.pop()
                if isinstance(widget, (FileEditor, FileViewer)):
                    widget.rehighlight()
                pending.extend(widget.children)
        return True

    # -- the panel and the command line ----------------------------------------

    def _panel_entry(self) -> tuple[Location, Any] | None:
        """The active panel's directory and the entry under its cursor, if any."""
        manager = self.active_manager
        if manager is None:
            return None
        panel = manager.active_panel
        entry = panel.selected
        return (panel.location, entry) if entry is not None else None

    def _insert_entry(self, *, whole: bool) -> None:
        """``_CtrlEnter``: the entry's name -- or path -- onto the command line.

        On ``..`` it is the directory the panel shows, whole and ending in
        ``/``, as DOS Navigator's ended in a backslash.
        """
        found = self._panel_entry()
        if found is None:
            return
        directory, entry = found
        if entry.name == "..":
            text = _escape(str(directory).rstrip("/")) + "/"
        elif whole:
            text = _escape(str(entry.path_in(directory)))
        else:
            text = _escape(entry.name)
        self.command_line.insert_name(text)

    def _search_with_the_line_hidden(self, event: KeyEvent) -> bool:
        """With the command line hidden, a character (not ``\\``) typed with
        Shift and without Ctrl starts the active panel's quick search with it
        -- DN's ``TFilePanel`` test ``ShiftState and 3 <> 0`` and ``not
        CommandLine^.GetState(sfVisible)``.  Anything else is still taken by
        nobody."""
        if not (event.is_printable and event.shift) or event.ctrl or event.alt or event.super_:
            return False
        if event.char == "\\":
            return False
        manager = self.active_manager
        if manager is None or manager._aside_focused():
            return False
        panel = manager.active_panel
        if not panel.focus_within:
            return False
        panel.start_quick_search()
        panel._search_key(event)
        return True

    async def on_previous_command(self, event: Any) -> bool:
        """Shift+Up from the panels: the command history, as the line's own
        Ctrl+E -- DN's Shift test handing ``kbUp`` to the line.  A hidden line
        takes nothing (``ouiHideCmdline``); an auto-hidden empty one shows with
        the command recalled, as typing would show it."""
        if not SETTINGS.interface.hide_command_line:
            self.command_line.recall(+1)
        return True

    async def on_next_command(self, event: Any) -> bool:
        """Shift+Down from the panels: as :meth:`on_previous_command`, Ctrl+X's way."""
        if not SETTINGS.interface.hide_command_line:
            self.command_line.recall(-1)
        return True

    async def on_copy_command_line(self, event: Any) -> bool:
        """Ctrl+Shift+Ins from the panels: the whole line onto the clipboard
        (``kbCtrlIns`` with Shift, the line's ``cmPutInClipboard``)."""
        text = self.command_line.value
        if text and self.command_line.visible and self.application is not None:
            self.application.copy_to_clipboard(text)
        return True

    async def on_insert_side_directory(self, event: Any) -> bool:
        """Ctrl+[ / Ctrl+]: ``cmGetName`` asked of the left (or right) side, the
        answer ending in ``/`` onto the line (``cmInsertName``).

        The Ctrl+T tree standing there answers the directory under its
        cursor, as a panel tree did; anything else -- the panel, hidden or
        not, or the quick view or information panel in its place -- the
        side's panel's directory.  A departure there: DN's quick view
        answered nothing, an empty name.
        """
        manager = self.active_manager
        if manager is None:
            return True
        from navigator.lib.drives.location import shown

        side = "right" if event.side == "right" else "left"
        view = manager.side_view(side)
        if view is manager.tree and manager.tree.selected_path is not None:
            where = manager.tree.selected_path
        else:
            where = (manager.left if side == "left" else manager.right).location
        text = str(shown(where)).rstrip("/")
        self.command_line.insert_name(_escape(text) + "/" if text else "/")
        return True

    def cursor_position(self) -> tuple[int, int] | None:
        """The command line's caret, when the keys that fell this far go there.

        Asked because the widget holding the keyboard -- a panel, the idle
        console -- has no caret of its own, and what it declines is what
        reaches :meth:`on_key` and so the command line.
        """
        line = self.command_line
        if not line.visible:
            return None
        if self.console.busy and self.console.focused:
            # A program has the keys, and has hidden its cursor or been
            # scrolled away from: nothing typed now reaches the line.
            return None
        position = line.cursor_position()
        if position is None:
            return None
        x, y = position
        return line.x + x, line.y + y

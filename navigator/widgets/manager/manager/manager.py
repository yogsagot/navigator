"""The handlers behind ``manager.nml``.

The file manager window.  What the document says is the two panels, their
geometry and the keys; what is left here is the logic -- what the commands
do, which panel is active, and where the panels open.

This file never names the generated class.  ``class Manager(..., Window)`` is
the base the markup's ``Manager(Window):`` head asks for, after the mixins the
methods are split into by feature, one module each beside this one
(``navkit.widget.Mixin``).  What stays here is the state, the keys, the
constructor, ``checks``/``refusal`` and which panel is active.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from navkit.i18n import tr
from navkit.reactive import computed, effect, reactive, untracked

from navml.commands import ZoomWindow
from navml.widgets.window import Window

from navigator.widgets.shell.commands import CopyCommandLine, InsertSideDirectory, NextCommand, PreviousCommand
from navigator.widgets.manager.commands import (
    AlternateEdit,
    ArchiveFiles,
    ArcTest,
    ChangeAttributes,
    ClearClipboard,
    Copy,
    CutToClipboard,
    Delete,
    DeleteSingle,
    DirBranch,
    DiskInfo,
    FindDuplicates,
    Edit,
    ExtractArchive,
    ExtractTo,
    OpenArchive,
    GoInto,
    GoParent,
    GoRoot,
    HideInactive,
    HideLeft,
    HideRight,
    InvertSelection,
    SelectAll,
    MakeDirectory,
    MakeLink,
    MountImage,
    EditLinkTarget,
    LinkAbsolute,
    LinkRelative,
    SelectBrokenLinks,
    SelectBadNames,
    ShowHardLinks,
    MoveSeparator,
    PasteFromClipboard,
    PrintFile,
    PutInClipboard,
    QuickRename,
    QuickView,
    RenameMove,
    ScrollNames,
    SelectGroup,
    SelectSimilar,
    UnselectSimilar,
    SwitchPanel,
    ChangeInactive,
    EnterWithoutArchive,
    GoToFile,
    CompareDir,
    DiffFiles,
    FastRename,
    FindFile,
    ReplaceInFiles,
    ReadFileList,
    Panelize,
    MultiRename,
    Undo,
    RestoreTrash,
    SetupColumns,
    JumpToDirectory,
    ListOfDirs,
    QuickChange,
    StoreQuickDir,
    RememberDirectory,
    SwapPanels,
    EqualizePanels,
    ToggleHidden,
    ToggleInfoLines,
    ToggleMark,
    ToggleMiller,
    ToggleShowMode,
    ToggleTree,
    UnmountImage,
    UnselectGroup,
    UuDecode,
    UuEncode,
    SplitCombine,
    CalculateChecksums,
    VerifyChecksums,
    EncryptFiles,
    DecryptFiles,
    ConvertText,
    OpenWith,
)

from navml.widgets.dialog.commands import QuickSearch

from navigator.widgets.manager.panel import Panel
from navigator.widgets.manager.panel.panel import DirEntry
from navigator.lib.config import panel_state
from navigator.lib.drives import DriveGone, Location, drive_of
from navigator.lib.drives import trash as trash_drive
from navigator.lib.file_ops.clip import CLIP
from navigator.lib.file_ops.undo import UNDO
from navigator.lib.drives.location import shown
from navigator.settings import SETTINGS
from navigator.widgets.manager.manager.helpers import _at_root, _disk_only, _is_archive

from navigator.widgets.manager.manager.encoding import Encoding
from navigator.widgets.manager.manager.archives import Archives
from navigator.widgets.manager.manager.listings import Listings
from navigator.widgets.manager.manager.navigation import Navigation
from navigator.widgets.manager.manager.panel_options import PanelOptions
from navigator.widgets.manager.manager.renaming import Renaming
from navigator.widgets.manager.manager.undo_trash import UndoTrash
from navigator.widgets.manager.manager.compare import Compare
from navigator.widgets.manager.manager.copying import Copying
from navigator.widgets.manager.manager.erasing import Erasing
from navigator.widgets.manager.manager.directories import Directories
from navigator.widgets.manager.manager.links import Links
from navigator.widgets.manager.manager.opening import Opening
from navigator.widgets.manager.manager.sides import Sides
from navigator.widgets.manager.manager.views import Views


#: What works only on the local disk: greyed out while the active panel is on
#: another drive (:mod:`navigator.lib.drives`).  Empty now -- every command
#: asks the drive, or works on a fetched copy -- and the place a new command
#: that cannot goes, until it is taught to.  What a drive cannot do at all is
#: its capabilities' to grey (``enables``).
_LOCAL_ONLY: tuple[type, ...] = ()


#: What means nothing in Miller columns (Alt+F12): the other panel, a side
#: to hide, swap or stand in for, the divider, the view modes and footer of
#: one column, and the listings that are no directory.  Greyed there.
_NOT_IN_MILLER: tuple[type, ...] = (
    SwapPanels, HideLeft, HideRight, HideInactive, ToggleTree, QuickView, DiskInfo, EqualizePanels,
    CompareDir, DiffFiles, MoveSeparator, ChangeInactive, ToggleShowMode, ToggleInfoLines, SetupColumns, FindFile,
    DirBranch, ReadFileList, Panelize, ScrollNames, FindDuplicates, ReplaceInFiles, ShowHardLinks,
    MountImage, UnmountImage,
)


class Manager(Encoding, Archives, Listings, Navigation, PanelOptions, Renaming, UndoTrash, Compare,
              Copying, Erasing, Directories, Links, Opening, Sides, Views, Window):
    """The file manager: two panels, in a window on the desktop."""

    #: The panels' frames are this window's frame.
    framed = False

    #: Handled here and bound to no key, but listed in Key bindings so one can
    #: be given: Ctrl+C, DN's for *Compare directories*, is the clipboard's.
    keyless_commands = (CompareDir, DiffFiles, SplitCombine, CalculateChecksums, VerifyChecksums, EncryptFiles, DecryptFiles,
                        ConvertText, EditLinkTarget, LinkRelative, LinkAbsolute, SelectBrokenLinks, SelectBadNames, ShowHardLinks)

    #: The Gray keys, merged with the markup's ``keys:`` block, which names a
    #: command and cannot construct one.  Each says ``by_key``, so it steps
    #: aside while the command line has text; Shift+Gray ``+``/``-`` open the
    #: dialog with *Except mask* ticked, as DN's ``ShiftState and 3 <> 0``
    #: did, and Ctrl+Gray ``*`` inverts the directories too (``kbCtrlGAst``).
    #:
    #: **And the plain ``+``, ``-`` and ``*``**, Midnight Commander's rule.
    #: Only a terminal that reports the keypad on its own -- the kitty
    #: protocol, or application keypad mode honoured -- can tell Gray ``+``
    #: from the other one, and VTE (xfce4-terminal, GNOME Terminal) and
    #: PyCharm's JediTerm send a bare ``+`` for both.  Binding the character
    #: too makes the keys work everywhere; what it costs is starting a command
    #: with one of the three from the panel, and after any other character
    #: they type as usual.
    keys = {
        # Ins, the line's overwrite toggle while the line holds text (``by_key``).
        "insert": ToggleMark(by_key=True),
        "plus": SelectGroup(by_key=True),
        "-": UnselectGroup(by_key=True),
        "*": InvertSelection(by_key=True),
        "kp_plus": SelectGroup(by_key=True),
        "kp_minus": UnselectGroup(by_key=True),
        "kp_multiply": InvertSelection(by_key=True),
        "shift+kp_plus": SelectGroup(invert=True, by_key=True),
        "shift+kp_minus": UnselectGroup(invert=True, by_key=True),
        "ctrl+kp_multiply": InvertSelection(directories=True, by_key=True),
        #: DN's ``SelectExt``/``SelecType``: entries like the cursor's, by name
        #: (Alt; Alt+Shift those not), type (Ctrl) or extension (Ctrl+Shift).
        #: The bare characters too, for the terminals above that send them.
        **{f"{mods}{key}": (SelectSimilar if key in ("kp_plus", "plus") else UnselectSimilar)(by=by, invert=invert)
           for mods, by, invert in (("alt+", "name", False), ("alt+shift+", "name", True),
                                    ("ctrl+", "type", False), ("ctrl+shift+", "extension", False))
           for key in ("kp_plus", "kp_minus", "plus", "-")},
        #: With Num Lock on, a terminal may report Ctrl+Gray ``*`` as the
        #: plain ``*`` with Ctrl (kitty's ``CSI 42;5u``), as the bare keys above.
        "ctrl+*": InvertSelection(directories=True, by_key=True),
        #: A departure, asked for: every file and directory at once.
        "ctrl+a": SelectAll(),
        #: DN's ``fmoBackGoesBack``: Backspace goes up while the command line
        #: is empty, Shift+Backspace whatever it holds -- both only under that
        #: setting -- and Ctrl+PgUp always.
        "backspace": GoParent(by_key=True),
        "shift+backspace": GoParent(backspace=True),
        "ctrl+pageup": GoParent(),
        # ``kbCtrlBSlsh``: ``ChangeRoot``.
        "ctrl+\\": GoRoot,
        # ``$1A1B``/``$1B1D``: the left and right sides' directories onto the
        # command line (the Shell's).  Here, not in the markup, which cannot
        # name a bracket key.  Ctrl+[ is Esc's byte, and arrives as itself
        # only under the kitty keyboard protocol; Ctrl+] arrives anywhere.
        # DN's panel handed these to the command line with Shift held: its
        # history, and the whole line onto the clipboard.  A terminal that
        # keeps the Insert keys for itself (VTE, Ghostty) never sends the last.
        "shift+up": PreviousCommand,
        "shift+down": NextCommand,
        "ctrl+shift+insert": CopyCommandLine(),
        "ctrl+[": InsertSideDirectory(side="left"),
        "ctrl+]": InsertSideDirectory(side="right"),
        #: DN's ``_CtrlPgDn``; on a file it opens it as an archive (a departure).
        "ctrl+pagedown": GoInto(),
        #: ``_CtrlPgDn`` with Shift in a *Find:* listing: ``cmChangeInactive``.
        "ctrl+shift+pagedown": ChangeInactive(),
        #: DN's quick directories: Alt+1 .. Alt+9 go, Alt+Shift+1 .. 9 store,
        #: Alt+Shift+0 lists them.  A terminal without the kitty protocol
        #: sends Alt with the shifted character, so a US layout's ``!`` ..
        #: ``(`` and ``)`` are bound too.
        **{f"alt+{n}": QuickChange(slot=n) for n in range(1, 10)},
        **{f"alt+shift+{n}": StoreQuickDir(slot=n) for n in range(1, 10)},
        **{f"alt+{sign}": StoreQuickDir(slot=n) for n, sign in enumerate("!@#$%^&*(", 1)},
        "alt+shift+0": ListOfDirs(),
        "alt+)": ListOfDirs(),
        #: DN's ``fmoDelErase``: Del deletes while the command line is empty,
        #: and edits the line otherwise; Shift+Del is the menu's single delete.
        "delete": Delete(by_key=True),
        "shift+delete": DeleteSingle(by_key=True),
        #: The clipboard's keys, each the command line's while it has text:
        #: the paths copied there, and the entries kept to paste
        #: (:mod:`navigator.lib.file_ops.clip`).  Esc forgets them.
        "ctrl+c": PutInClipboard(by_key=True),
        "ctrl+insert": PutInClipboard(by_key=True),
        "ctrl+x": CutToClipboard(by_key=True),
        "ctrl+delete": CutToClipboard(by_key=True),
        "ctrl+v": PasteFromClipboard(by_key=True),
        "shift+insert": PasteFromClipboard(by_key=True),
        "escape": ClearClipboard(by_key=True),
        #: File > Undo (not DN's), the line's while it has text.
        "ctrl+z": Undo(by_key=True),
        #: Scrolling a name too long for its column; the list mode's panel
        #: takes these first and moves a column instead.
        "left": ScrollNames(-1),
        "right": ScrollNames(1),
        #: DN's ``kbAltLeft``/``kbAltRight``: the divider a column along.
        "alt+left": MoveSeparator(-1),
        "alt+right": MoveSeparator(1),
    }

    #: How long the tree's cursor has to rest before the panel follows it:
    #: DOS Navigator's thirty ticks of the 18.2 Hz timer (``NeedLocated``).
    LOCATE_DELAY = 30 / 18.2

    #: The panel something else stands in for -- the directory tree (Ctrl+T)
    #: or the quick view (Ctrl+Q) -- and that something, or None for both
    #: while the two panels are showing.  One side at a time is ever not a
    #: panel -- a departure: DN's ``LType``/``RType`` were a side each, and a
    #: view taking a side while another view held the keyboard took the
    #: opposite one's place (DBLWND.PAS:541-556), so a tree and a quick view
    #: could stand together with no panel showing.  Kept to one, asked about:
    #: ``active_panel`` and every command reaching it need a panel showing,
    #: and one pair is what the saved desktop and the follow effects read.
    #: Reactive, so ``active_panel`` and the follow effects move with them.
    replaced: Any = reactive(None)
    replacement: Any = reactive(None)

    #: The panel that last held the keyboard.  What ``active_panel`` answers
    #: while neither does -- Ctrl+O has given the keyboard to the console, or
    #: a dialog has it -- since the panel the user left active is still the
    #: one a command means.
    _last_panel: Any = reactive(None)

    #: The side Ctrl+F1 or Ctrl+F2 has hidden -- ``"left"``, ``"right"`` --
    #: or None while both are showing.  DOS Navigator's ``LVisible`` and
    #: ``RVisible``, of which at most one was ever false.
    hidden_side: Any = reactive(None)

    #: The left side's share of the window's width, or None for the even
    #: split, the odd column to the right.  DOS Navigator's ``TSeparator``
    #: kept the same thing as ``OldX``/``OldW``, so a window resized or zoomed
    #: keeps its proportion rather than its column.
    split: Any = reactive(None)

    #: The narrowest the divider leaves a side: its two frame columns and one
    #: cell between them.  DN's ``(P.X >= 1) and (P.X < Owner^.Size.X-2)``.
    MIN_SIDE = 3

    def __init__(self, left: Path, right: Path, **kwargs):
        """Build the window, then seed where the panels open.

        ``super().__init__()`` is the generated half, so the whole tree exists
        from the next line on -- which is the contract the merge rests on.

        **Where the panels open is seeded rather than bound.**  A markup
        property line compiles to a binding, a bound attribute is read-only
        until something unbinds it, and
        :meth:`~navigator.widgets.manager.panel.Panel.enter` assigns ``path`` every
        time the user descends a directory.  So a property a widget
        *navigates* can be given a starting value by its parent and cannot be
        bound to one.
        """
        super().__init__(**kwargs)
        self.left.path = left
        self.right.path = right
        # Hidden files and the footer as each side was left (``panel_state``).
        panel_state.recall(self)
        self.tree.visible = False
        self.tree.menu = self._tree_menu
        #: Ctrl+Q's quick view, made the first time it is wanted (:attr:`quick`).
        self._quick: Any = None
        self.info.visible = False
        self.miller.visible = False
        #: The side that was active when Miller columns took the panels'
        #: place, and gets the directory browsed when they give it back.
        self._miller_side = "left"
        #: The pending "panel, follow the tree" -- cancelled by every move.
        self._follow: asyncio.Task[Any] | None = None
        #: What hiding a side set aside: the rectangle and ``zoomed`` before,
        #: the rectangle after, and the two sides' widths, for growing back.
        self._collapse: dict[str, Any] | None = None
        #: The rectangle Alt+Z zoomed the window to after hiding the panel the
        #: quick view follows (``on_zoom_window``), or None.
        self._view_zoom: tuple[int, int, int, int] | None = None
        #: While the divider is held: the column the pointer took it at,
        #: counted from the right side's left edge (DN's ``B``).
        self._divider: int | None = None
        #: File > Undo: where the first thing put back now is (:meth:`undo`).
        self._undo_landing: Location | None = None
        #: What each side last showed of what ``panel_state`` keeps; None
        #: until the first look, which only records it.
        self._kept_state: dict[str, dict[str, Any]] | None = None

    def mounted(self) -> None:
        super().mounted()
        effect(self, Manager.place_divider)
        effect(self, Manager._remember_panel)
        effect(self, Manager._keep_panel_state)
        effect(self, Manager._tree_follows_panel)
        effect(self, Manager._panel_follows_tree)
        effect(self, Manager._quick_view_follows_panel)
        effect(self, Manager._info_follows_panel)
        effect(self, Manager._info_follows_cursor)

    def _keep_panel_state(self) -> None:
        """Hidden files, the footer, the view mode and the order, kept for the
        next file manager on that side (``panel_state``) as each changes --
        by key, menu, dialog, a column title or Ctrl+U.  The first run only
        notes them, so opening a file manager writes nothing."""
        kept = {side: panel_state.kept_values(getattr(self, side)) for side in ("left", "right")}
        last, self._kept_state = self._kept_state, kept
        if last is None:
            return
        with untracked():
            for side, values in kept.items():
                if values != last[side]:
                    panel_state.remember(self, side)

    # -- commands ------------------------------------------------------------
    #
    # The keys are the markup's ``keys:`` block.  Alt+X is not among them: a
    # way out of Navigator cannot live on a window the user can close, so it
    # is the application's.

    async def on_switch_panel(self, event: SwitchPanel) -> bool:
        if self.miller_mode:
            self.miller.switch_focus()
        else:
            self.switch_panel()
        return True

    async def on_hide_left(self, event: HideLeft) -> bool:
        await self.toggle_side("left")
        return True

    async def on_move_separator(self, event: MoveSeparator) -> bool:
        sides = self._sides()
        if len(sides) == 2:
            self.move_divider_to(sides[1].x + event.step)
        return True

    async def count_length(self, panel: Panel) -> None:
        """Alt+G: ``CountLen``, each directory's bytes into its size column.

        The directory at the cursor -- ``..`` standing for the one listed --
        and every tagged one, counted on a thread (:mod:`navigator.lib.file_ops.dirlength`)
        under *Counting directory length* if it takes a while -- the bytes,
        files and directories met so far, and when there are several, which
        one and what is in it beside the total (``CountProgress``).  Nothing is done with the cursor on a
        file and nothing tagged.  Esc there stops
        it: what was counted before keeps its count, and the rest stays
        ``DIR``, as DN's ``Abort`` left them.
        """
        from navigator.lib.file_ops.dirlength import CountJob, count_dir_length
        from navigator.lib.system.progress import SLOW_PROGRESS_DELAY, run_with_progress
        from navigator.widgets.file_ops.count_progress import CountProgress

        app = self.application
        here = panel.location
        entries = [entry for entry in panel.marked_entries if entry.is_dir]
        current = panel.selected
        if current is not None and current.is_dir and current not in entries:
            entries.insert(0, current)
        if app is None or not entries:
            return
        if panel.found is not None:
            # ``..`` leads back out of a *Find:* listing; it has no length.
            entries = [entry for entry in entries if entry.name != ".."]
            if not entries:
                return
        targets = [(entry, shown(here if entry.name == ".." else panel.entry_location(entry)))
                   for entry in entries]
        job = CountJob()

        def count() -> list[tuple[Any, int]]:
            done = []
            for entry, path in targets:
                job.current = str(path)
                size = count_dir_length(path, job)
                if size is None:
                    break
                done.append((entry, size))
            return done

        def refresh(box: CountProgress) -> None:
            box.directory = job.current
            box.here_size = job.here_size
            box.here_files = job.here_files
            box.here_directories = job.here_directories
            box.size = job.position
            box.files = job.files
            box.directories = job.directories

        counted = await run_with_progress(
            app, count, job, lambda: CountProgress(several=len(targets) > 1),
            refresh, delay=SLOW_PROGRESS_DELAY,
        )
        panel.set_lengths(counted)

    #: The last command panelized, offered again in the box (the session's).
    last_panelized = ""

    def refusal(self, command: Any) -> str:
        """Why the active panel cannot do *command* now, ``""`` when it can.

        Tagging and the quick search are the active panel's, and not while
        the tree or the quick view standing beside it has the keyboard -- those
        are not a listing.  Asked of a menu too, where neither has it and the
        panel is meant.  A refusal of a key that falls through to the command
        line (``by_key``) says so, though no menu asks it that way."""
        if isinstance(command, ZoomWindow):
            # The handler is here now, so this answers for the desktop's too.
            if self._quick_selected() or self.zoomable:
                return ""
            return tr("This window cannot be zoomed")
        panel = self.active_panel

        def unless(condition: bool, reason: str) -> str:
            return "" if condition else reason

        def gone() -> str:
            return tr("The connection to this panel's drive is closed")

        aside = tr("Only in a file panel, not beside it")
        nothing = tr("No files are tagged, and the cursor is on none")
        typed = tr("The command line holds text: the key edits it")
        read_only = tr("This drive cannot be written to")
        not_found = tr("Not in a Find listing")
        if isinstance(command, Edit) and self.info.focus_within:
            # ``TDiskInfo``'s ``cmEditFile``: the information file it shows, or nothing.
            return unless(self.info.info_path is not None, tr("No DirInfo or File_ID.DIZ here"))
        # The history is the session's, whatever the panel shows.
        if isinstance(command, Undo):
            if command.by_key and self._command_line_has_text():
                return typed
            return unless(bool(UNDO), tr("Nothing to undo"))
        if isinstance(command, RememberDirectory):
            from navigator.lib.config import directory_settings

            if directory_settings.mode() == "off":
                return tr("File Manager Setup's Remember directory settings is Off")
            if panel.found is not None:
                return tr("A Find listing is no directory to remember")
            return unless(directory_settings.rememberable(panel.location),
                          tr("A place inside an archive cannot be remembered"))
        if isinstance(command, JumpToDirectory):
            shell = getattr(self.application, "shell", None)
            return shell.fuzzy_refusal() if shell is not None else tr("fzf is not installed, or the shell is not bash or zsh")
        if isinstance(command, OpenWith):
            from navigator.lib.system import desktop

            entry = panel.selected
            if entry is None or entry.is_dir or entry.name == "..":
                return tr("The cursor is not on a file")
            if desktop.program() is None:
                return tr("Neither GIO nor KIO is installed")
            return unless(desktop.graphical(), tr("No graphical desktop to open it on"))
        if isinstance(command, (EncryptFiles, DecryptFiles)):
            from navigator.lib.file_ops import encrypt

            if not encrypt.available():
                return tr("Neither gpg nor age is installed")
            chosen = self.selection(panel)
            if not chosen:
                return nothing
            if isinstance(command, DecryptFiles):
                return unless(any(entry.is_dir or encrypt.suffix_tool(entry.name) for entry in chosen),
                              tr("No encrypted file is tagged or at the cursor"))
            return ""
        if isinstance(command, ConvertText):
            return "" if self.selection(panel) else nothing
        if isinstance(command, ToggleMiller):
            # A *Find:* listing is no directory to open columns on.
            return unless(self.miller_mode or panel.found is None, not_found)
        if self.miller_mode and isinstance(command, _NOT_IN_MILLER):
            return tr("Not in Miller columns (Alt-F12)")
        if isinstance(command, _LOCAL_ONLY) and not panel.location.is_local:
            return _disk_only(panel)
        if isinstance(command, MakeLink) and not panel.location.is_local:
            # A link on another drive is made there, where it can be.
            try:
                if not panel.drive.can("symlink"):
                    return tr("This drive cannot hold links")
            except DriveGone:
                return gone()
        if isinstance(command, (EditLinkTarget, LinkRelative, LinkAbsolute)):
            if self._aside_focused():
                return aside
            try:
                drive = panel.drive
            except DriveGone:
                return gone()
            if not (drive.can("symlink") and drive.can("rename")):
                return tr("This drive cannot hold links")
            return unless(bool(self.selected_links(panel)), tr("No symbolic link is selected"))
        if isinstance(command, ShowHardLinks):
            if self._aside_focused():
                return aside
            if panel.found is not None:
                return not_found
            if not panel.location.is_local:
                return _disk_only(panel)
            entry = panel.selected
            if entry is None or entry.name == ".." or entry.is_dir:
                return tr("No file at the cursor")
            return unless(entry.nlink > 1, tr("The file has no other names"))
        if isinstance(command, SelectBrokenLinks):
            if self._aside_focused():
                return aside
            return unless(any(entry.is_stale_link for entry in panel.items), tr("No broken links here"))
        if isinstance(command, SelectBadNames):
            if self._aside_focused():
                return aside
            return unless(bool(self.bad_names(panel)), tr("No bad names here"))
        if isinstance(command, (Copy, RenameMove, Delete, DeleteSingle, MakeDirectory, QuickRename, FastRename,
                                MultiRename)):
            try:
                drive = panel.drive
            except DriveGone:
                return gone()
            if isinstance(command, (RenameMove, Delete, DeleteSingle, MakeDirectory, QuickRename, FastRename)) \
                    and not drive.can("write"):
                return read_only
        if isinstance(command, (ExtractTo, ArcTest)):
            return unless(panel.location.outer is not None, tr("Only inside an archive"))
        if isinstance(command, GoInto):
            return unless(not self._aside_focused(), aside)
        if isinstance(command, OpenArchive):
            if panel.location.outer is not None:
                return tr("Not from inside an archive")
            return unless(panel.archive_candidate() is not None, tr("No file at the cursor"))
        if isinstance(command, MountImage):
            from navigator.lib.system import udisks

            if _at_root(panel):
                return _disk_only(panel)
            if panel.image_file() is None:
                return tr("No disk image at the cursor")
            return unless(udisks.program() is not None, tr("udisksctl (udisks2) is not installed"))
        if isinstance(command, UnmountImage):
            return unless(bool(panel.image_here()), tr("Not in a mounted disk image"))
        if isinstance(command, ExtractArchive):
            if panel.location.outer is not None:
                return ""  # *Extract to...*'s, which is enabled throughout an archive
            return unless(any(_is_archive(entry) for entry in self.selection(panel)),
                          tr("No archive is tagged or at the cursor"))
        if isinstance(command, ArchiveFiles):
            if not self.selection(panel):
                return nothing
            return unless(self._archive_place(panel, self.selection(panel)) is not None,
                          tr("Neither panel's directory can be written to"))
        if isinstance(command, (Edit, AlternateEdit)) and not panel.location.is_local:
            # An editor's F2 puts the file back: not into a drive that takes nothing.
            try:
                return unless(panel.drive.can("write"), read_only)
            except DriveGone:
                return gone()
        if isinstance(
            command, (ToggleMark, SelectGroup, UnselectGroup, InvertSelection, SelectAll, QuickSearch,
                      SelectSimilar, UnselectSimilar)
        ):
            if getattr(command, "by_key", False) and self._command_line_has_text():
                # Disabled, so the key falls through and types its character.
                return typed
            return unless(not self._aside_focused(), aside)
        if isinstance(command, EnterWithoutArchive):
            if self._command_line_has_text():
                # Falls through to the line run in a window, as DN's Enter ran the line first.
                return typed
            return unless(not self._aside_focused(), aside)
        if isinstance(command, (GoRoot, PreviousCommand, NextCommand, CopyCommandLine)):
            return unless(not self._aside_focused(), aside)
        if isinstance(command, GoParent):
            if command.by_key and self._command_line_has_text():
                # Disabled, so Backspace falls through and edits the line.
                return typed
            if (command.by_key or command.backspace) and not SETTINGS.file_manager.bs_upper_dir:
                # File Manager Setup's *BS upper dir* off: neither Backspace
                # goes up (DN's Shift test sat inside it); Ctrl+PgUp still does.
                return tr("File Manager Setup's BS upper dir is off")
            return unless(not self._aside_focused(), aside)
        if isinstance(command, (PutInClipboard, CutToClipboard, PasteFromClipboard, ClearClipboard)):
            if command.by_key and self._command_line_has_text():
                # Disabled, so the key is the line's: copy, paste, history.
                # Ctrl+Ins then copies the line's selection, or the whole line --
                # a departure: DN's panel always took it (``_CtrlIns``), and only
                # Ctrl+Shift+Ins, the line's either way, copied its text.
                return typed
            if self._aside_focused():
                return aside
            if isinstance(command, (PutInClipboard, CutToClipboard)):
                return unless(bool(self.selection(panel)), nothing)
            if not CLIP:
                return tr("The file clipboard is empty")
            if isinstance(command, PasteFromClipboard):
                if panel.found is not None:
                    # DN's ``TFindDrive.CopyFilesInto`` did nothing: no one place to paste into.
                    return tr("Not in a Find listing")
                try:
                    return unless(panel.drive.can("write"), read_only)
                except DriveGone:
                    return gone()
            return ""
        if isinstance(command, (Delete, DeleteSingle)) and command.by_key:
            if self._command_line_has_text():
                # Disabled, so Del deletes a character and Shift+Del cuts.
                return typed
            if isinstance(command, Delete) and not SETTINGS.file_manager.del_erases:
                # File Manager Setup's *Del erases* off: F8 still does.
                return tr("File Manager Setup's Del erases is off")
        if self._tree_takes(command):
            return self._tree_refusal(command)
        if isinstance(command, DeleteSingle):
            entry = panel.selected
            if self._aside_focused():
                return aside
            return unless(entry is not None and entry.name != "..", tr("The cursor is on no file"))
        if isinstance(command, (Copy, RenameMove, MakeLink, Delete, ChangeAttributes, PrintFile)):
            # DN's ``GetSelection`` answering nil: nothing tagged and the
            # cursor on ``..``, or a listing that is not a panel's.
            if self._aside_focused():
                return aside
            return unless(bool(self.selection(panel)), nothing)
        if isinstance(command, StoreQuickDir):
            # ``Drive^.DriveType <> dtDisk``: a listing is not a directory to
            # keep, nor is a place in an archive.
            if panel.found is not None:
                return not_found
            return unless(panel.location.outer is None, tr("Not inside an archive"))
        if isinstance(command, DirBranch):
            # ``CM_Branch`` acted on a disk's directory alone.
            return unless(panel.found is None, not_found)
        if isinstance(command, FindDuplicates):
            # Any drive: the walk and the reads go through it (``duplicates``).
            return unless(panel.found is None, not_found)
        if isinstance(command, MakeDirectory):
            # ``TFindDrive.MakeDir`` made nothing: a *Find:* listing has no
            # directory to make one in.
            return unless(panel.found is None, not_found)
        if isinstance(command, Panelize):
            # ``$SHELL -c`` runs as the user: not in a ``root:`` panel's directory.
            return "" if panel.location.is_local else _disk_only(panel)
        if isinstance(command, MultiRename):
            if self._aside_focused():
                return aside
            return unless(bool(self.selection(panel)), nothing)
        if isinstance(command, RestoreTrash):
            # The Trash's own items only: one inside a trashed directory has no place of its own to go back to.
            if not self.shows_trash:
                return tr("Only in the Trash")
            return unless(bool(self.selection(panel)), nothing)
        if isinstance(command, ReadFileList):
            entry = panel.selected
            return unless(entry is not None and not entry.is_dir, tr("The cursor is not on a file"))
        if isinstance(command, EqualizePanels):
            # A *Find:* listing has no one directory to send the other side to.
            return unless(panel.found is None, not_found)
        if isinstance(command, (ChangeInactive, GoToFile)):
            entry = panel.selected
            if panel.found is None:
                return tr("Only in a Find listing")
            # ``ChangeInactive`` on ``..`` leaves the listing, as Shift+Enter there did in DN.
            on_file = entry is not None and (entry.name != ".." or isinstance(command, ChangeInactive))
            return unless(on_file, tr("The cursor is on no file"))
        if isinstance(command, QuickRename):
            # One entry: the one tagged, else the cursor's.
            return unless(self._rename_candidate(panel) is not None,
                          tr("Tag one file, or put the cursor on one"))
        if isinstance(command, CalculateChecksums):
            if self._aside_focused():
                return aside
            return unless(bool(self.selection(panel)), nothing)
        if isinstance(command, VerifyChecksums):
            if self._aside_focused():
                return aside
            return unless(any(not entry.is_dir for entry in self.selection(panel)),
                          tr("No checksum file is tagged or at the cursor"))
        if isinstance(command, (UuEncode, UuDecode, SplitCombine)):
            # DN's ``PF^.Attr and Directory = 0``: the file at the cursor.
            entry = panel.selected
            return unless(entry is not None and not entry.is_dir, tr("The cursor is not on a file"))
        if isinstance(command, CompareDir):
            # Two directories, compared: a *Find:* listing is not one -- a
            # departure: DN's ``CM_CompareDirs`` compared any two panels'
            # files, a find drive's too; here ``dircompare`` (and the
            # recursive *Window*) reads directories.
            return unless(self.left.found is None and self.right.found is None, not_found)
        if isinstance(command, DiffFiles):
            return unless(self._diff_pair() is not None,
                          tr("Tag two files, or put the cursor on a file with a namesake in the other panel"))
        if isinstance(command, SwitchPanel):
            # With one side hidden there is no other one for Tab to go to.
            return unless(self.hidden_side is None, tr("The other panel is hidden"))
        if isinstance(command, ScrollNames):
            # The plain arrows are the command line's under *Use arrows*.
            if self._aside_focused():
                return aside
            if self._command_line_has_text() and SETTINGS.file_manager.use_arrows:
                return typed
            return unless(panel.can_scroll_names(command.step), tr("No name is cut to scroll"))
        return super().refusal(command)

    def checks(self, command: Any) -> bool | None:
        """Ctrl+H is ticked in the menu while the active panel shows its
        dot-files, Alt+I while it shows its footer, *Remember for this
        directory* while its directory has a record of its own."""
        if isinstance(command, ToggleHidden):
            return self.active_panel.show_hidden
        if isinstance(command, ToggleInfoLines):
            return self.active_panel.show_info
        if isinstance(command, RememberDirectory):
            panel = self.active_panel
            _ = panel.remembered  # read for the dependency
            return panel.remembers_here
        if isinstance(command, ToggleMiller):
            return self.miller_mode
        return super().checks(command)

    def _aside_focused(self) -> bool:
        """Whether the keyboard is in something beside the listing -- the tree,
        the quick view, the information panel, or the file Miller columns
        preview -- not a panel.  DN's ``TDiskInfo`` handled none of a panel's
        commands, so F5/F6/F8 there did nothing."""
        return (self.tree.focused or (self._quick is not None and self._quick.focused)
                or self.info.focus_within
                or self.miller.file_preview_focused())

    #: What DN's panel tree (``TTreePanel.HandleEvent``) did itself, on the
    #: directory under its cursor: F5/F6 ``CopyDir``, F7 ``MkDirectory``,
    #: F8/Del ``EraseDir``.
    _TREE_OWN = (Copy, RenameMove, MakeDirectory, Delete)

    def _tree_takes(self, command: Any) -> bool:
        """Whether *command* is one the Ctrl+T tree, holding the keyboard, does itself."""
        return self.tree.focused and isinstance(command, self._TREE_OWN)

    def _tree_refusal(self, command: Any) -> str:
        """Why the tree cannot do *command* now: its root is not copied, moved
        or erased (``if ScrollBar^.Value < 1 then Exit``)."""
        tree = self.tree
        if tree.selected_path is None:
            return tr("The cursor is on no directory")
        if not isinstance(command, MakeDirectory) and tree.selected_node is tree.root:
            return tr("Not the tree's root")
        return ""

    def _tree_entry(self) -> tuple[Any, Any] | None:
        """The directory under the tree's cursor as a file operation takes it:
        ``(where it is listed, its entry)``, or None if it is gone."""
        from navigator.lib.drives.listing import DirEntry, entry_at

        path = self.tree.selected_path
        if path is None:
            return None
        if isinstance(path, Location) and not path.is_local:
            try:
                info = drive_of(path).stat(path)
            except (OSError, DriveGone):
                return None
            entry = DirEntry(path.name, True, 0, info.st_mode, info.st_mtime, False, None,
                             getattr(info, "st_uid", 0), getattr(info, "st_gid", 0), None,
                             getattr(info, "st_nlink", 1))
            return path.parent, entry
        local = path.local if isinstance(path, Location) else Path(path)
        entry = entry_at(local)
        return (Location.of(local.parent), entry) if entry is not None else None

    def _command_line(self) -> Any:
        """The command line of the screen this window is on, or None."""
        widget = self.parent
        while widget is not None:
            line = getattr(widget, "command_line", None)
            if line is not None:
                return line
            widget = widget.parent
        return None

    def _command_line_has_text(self) -> bool:
        """Whether the command line of the screen this window is on holds
        anything -- a blank included, as for Space.  ``False`` with none, and
        for a hidden one (``ouiHideCmdline``): DN's took no keys, so the
        panel had them all, whatever the line held."""
        line = self._command_line()
        return line is not None and not SETTINGS.interface.hide_command_line and bool(line.value)

    # -- copying and moving ------------------------------------------------------

    def selection(self, panel: Panel) -> list[Any]:
        """DN's ``GetSelection``: the tagged entries, or else the one under the cursor.

        Empty when nothing is tagged and the cursor is on ``..``, which is
        never a thing to copy.
        """
        marked = panel.marked_entries
        if marked:
            return marked
        entry = panel.selected
        if entry is None or entry.name == "..":
            return []
        return [entry]

    #: Whether the last :meth:`_may_as_root` put the question and was told no.
    _as_root_declined = False

    @computed
    def shows_trash(self) -> bool:
        """Whether the active panel lists the Trash's own items, at its root:
        what *Restore from Trash* acts on, and when File shows it."""
        location = self.active_panel.location
        return trash_drive.is_trash(location) and location.is_root

    @computed
    def active_panel(self) -> Panel:
        """Whichever panel has the keyboard, or had it last.

        **Last, not "the left one"**, while the focus is somewhere else --
        the console after Ctrl+O, a dialog.  DOS Navigator's active panel
        stayed active while its user screen was up, and a command typed then
        ran in *its* directory; answering "left" whenever neither panel held
        the keyboard sent the shell back to the left panel's directory the
        moment the console was shown.  While the tree stands in for one
        panel, the other is the active one whether or not it holds the
        keyboard: it is the one the tree steers.
        """
        current = self.miller.current
        if current is not None:
            # Miller columns: the column being browsed, whatever has the keyboard.
            return current
        replaced = self.replaced
        if replaced is not None:
            return self.right if replaced is self.left else self.left
        if self.right.focused:
            return self.right
        if self.left.focused:
            return self.left
        return self._last_panel or self.left

    @computed
    def passive_panel(self) -> Panel:
        """The panel that is not the active one, showing or not.

        While the tree or the quick view stands in for it, it is the panel
        they stand in for: its directory is still where DN's ``cmPushFirstName``
        would have pointed a copy.

        In Miller columns there is no other panel: it is the active one, so
        F5 and F6 offer the directory browsed (Ctrl+C/Ctrl+V go between two).
        """
        if self.miller_mode:
            return self.active_panel
        return self.right if self.active_panel is self.left else self.left

    @computed
    def miller_mode(self) -> bool:
        """Whether Miller columns stand in the two panels' place (Alt+F12)."""
        return self.miller.current is not None

    @property
    def all_panels(self) -> tuple[Panel, ...]:
        """Both panels, and every Miller column while they show: what a
        change on the disk or a drive closing must reach."""
        return (self.left, self.right, *self.miller.columns())

    # -- the directory tree ----------------------------------------------------

    @computed
    def tree_replaces(self) -> Any:
        """The panel the directory tree stands in for, or None while there is none."""
        return self.replaced if self.replacement is self.tree else None

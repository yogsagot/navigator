"""The file manager's commands: what ``Manager`` handles, and DOS Navigator's
panel keys that nothing handles yet.

The key bar commands carry DOS Navigator's own captions as their titles --
the file panel's status line, ``StatusDef hcFilePanel`` in ``DN.DNR`` --
because the key bar is where they are read.  A command nobody handles is a
disabled one, so the key bar shows the unwritten ones in the status line's
*Disabled* colour until they exist.  That is the original behaving as it did
whenever a command was unavailable, not a placeholder look.  ``Rescan`` is the
tree window's Ctrl+R too.
"""

from __future__ import annotations

from dataclasses import dataclass

from navkit.commands import Command

# Shared with the editor, which answers it too; named here as well for the
# key table and the menu that bind it.
from navigator.commands import PrintFile  # noqa: F401 -- re-exported


class UserMenu(Command):
    title = "User"


class View(Command):
    title = "View"


class OpenWith(Command):
    """File > *Open with*: the file at the cursor in one of the desktop's
    applications for its type, chosen from a box (``gio`` or KIO).  Not DN's."""

    title = "Open with"


class AlternateView(Command):
    """Alt+F3, File > Alternate view: DOS Navigator's ``cmIntFileView`` --
    the viewer *Internal viewer* does not pick: ``viewers.ini``'s, or the
    window."""


class ViewAsText(Command):
    """File > View > As Text: ``cmViewText``, the viewer opened in text mode."""


class ViewAsHex(Command):
    """File > View > As Hex: ``cmViewHex``, the viewer opened in hex mode."""


class ViewAsDataBase(Command):
    """File > View > As DataBase: ``cmViewDBF``, the dBase viewer."""


class Edit(Command):
    title = "Edit"


class AlternateEdit(Command):
    """Alt+F4 (and Ctrl+K, not DN's: many window managers close the terminal
    on Alt+F4), File > Alternate edit: DOS Navigator's ``cmIntFileEdit``, as
    :class:`AlternateView` for the editor -- but with *Internal editor* on and
    nothing in ``editors.ini``, a box of the console editors installed, run in
    a window of their own (a departure: DN's was the editor window, F4's)."""


class Copy(Command):
    title = "Copy"


class RenameMove(Command):
    title = "Ren"


class MakeLink(Command):
    """Shift+F5: a symbolic link to each selected entry.  A departure.

    DOS Navigator had no such command -- DOS had no links -- and the key was
    ``cmPanelLongCopy``'s, *Split/combine*, which spread a file too big for
    one floppy across several and is not ported.
    """

    title = "SymLnk"


class ChangeAttributes(Command):
    """Alt+E: *File Attributes*, DN's ``cmSetFAttr``, read for Linux.

    The mode bits, owner, group and modification time of the selection -- a
    departure in what it edits, since DN's were the four DOS attributes.
    On the key bar's Alt row, which ``StatusDef hcFilePanel``'s never was --
    and which, at 80 columns, now closes before *Exit*.
    """

    title = "Attr"


class MakeDirectory(Command):
    title = "MkDir"


@dataclass(frozen=True, slots=True)
class Delete(Command):
    """F8, ``cmPanelErase``: the selection, after the Delete dialog asks.

    Del too, DN's ``fmoDelErase``, on by default, which erased only while
    ``CmdLine.Str`` was empty.  *by_key* is that Del, as it is for
    :class:`GoParent`'s Backspace: with text on the line it steps aside and
    the key deletes a character there.
    """

    title = "Del"
    by_key: bool = False


class SwitchPanel(Command):
    """Tab: move the keyboard to the other panel."""


class Rescan(Command):
    """Ctrl+R: read the active panel's directory again."""

    title = "Re-read"


class ChangeDirectory(Command):
    """Alt+T: choose a directory from a tree, and send the active panel there.

    DOS Navigator's ``cmChangeDir``, Panel > Change directory.  Untitled, as
    ``StatusDef hcFilePanel`` left Alt-T off its Alt row.
    """


class HideLeft(Command):
    """Ctrl+F1: hide the left side of the file manager, or show it again.

    DOS Navigator's ``cmHideLeft``, Manager > Show/hide left panel.  Untitled,
    as ``StatusDef hcFilePanel`` left Ctrl-F1 off its Ctrl row.
    """


class HideRight(Command):
    """Ctrl+F2: hide the right side of the file manager, or show it again.

    DOS Navigator's ``cmHideRight``, Manager > Show/hide right panel.
    """


class SwapPanels(Command):
    """Ctrl+U: the two sides change places.

    DOS Navigator's ``cmSwapPanels``, Manager > Swap panels.
    """


class ToggleMiller(Command):
    """Alt+F12: the file manager's two panels become Miller columns, or back.

    Not DOS Navigator's -- a departure, asked for: Finder's column browser
    (``navigator/widgets/manager/miller``).  Manager > Miller columns.
    """


class EqualizePanels(Command):
    """Alt+=: the passive panel goes to the active panel's directory.

    Not DOS Navigator's -- 1.51 had no such command, a departure; Midnight
    Commander's ``Alt+I`` (*Sync panels*), on a free key since Alt+I is the
    footer here.  Panel > Same directory in other panel.
    """


class HideInactive(Command):
    """Ctrl+P: hide the side without the keyboard, or show it again.

    DOS Navigator's ``cmSwitchOther``, Manager > Show/hide inactive panel.
    """


class GoToTreeDirectory(Command):
    """The Ctrl+T tree's right-click *Go to directory*: what Enter in it does,
    the active panel to the directory at the cursor.  Not bound: Enter is the
    tree's own (``TreeView.choose``)."""

    title = "Go to directory"


class ToggleTree(Command):
    """Ctrl+T: the passive panel becomes a directory tree, or a panel again.

    DOS Navigator's ``cmDirTree``, Manager > Directory tree.
    """

    title = "Tree"


# The file panel's modifier rows: the ``-`` (Alt), ``+`` (Ctrl) and ``:``
# (Shift) items of ``StatusDef hcFilePanel``, each titled as the original
# captioned it and none handled yet, so the key bar shows them greyed while the
# modifier is held.  The DOS Navigator command each stands for is named beside
# it.


class SortBy(Command):
    """Alt+B, ``cmSortBy``."""

    title = "Sort"


class ChangeDrive(Command):
    """Alt+C, ``cmChangeDrive``: the bookmarks, for the active panel.

    DOS Navigator's drive letters; ``navigator/lib/config/bookmarks.py`` has the
    departure.
    """

    title = "Drive"


class ChangeLeft(Command):
    """Alt+F1, ``cmChangeLeft``: the bookmarks, for the left panel.

    Untitled, as ``StatusDef hcFilePanel`` left Alt-F1 off its Alt row.
    """


class ChangeRight(Command):
    """Alt+F2, ``cmChangeRight``: the bookmarks, for the right panel."""


class PanelSetup(Command):
    """Alt+S, ``cmPanelSetup``."""

    title = "Setup"


class MakeList(Command):
    """Alt+L, ``cmMakeList``."""

    title = "List"


class FastRename(Command):
    """Alt+F6, ``cmFastRename``."""

    title = "Ren"


class QuickRename(Command):
    """Shift+F6, File > Quick rename: one entry's new name, asked in a box.

    A departure, asked for: Alt+F6's rename without the in-place line, for
    the menu -- and none of F6's *Rename/Move* (targets, masks, modes).
    Enabled while the selection is one entry.
    """

    title = "Ren"


class FindFile(Command):
    """Alt+F7, ``cmFindFile``."""

    title = "Find"


class Calculator(Command):
    """Ctrl+F6, ``cmCalculator``."""

    title = "Calc"


class DiskInfo(Command):
    """Ctrl+L, ``cmDiskInfo``."""

    title = "Info"


class QuickView(Command):
    """Ctrl+Q, ``cmQuickView``."""

    title = "Preview"


class ToggleMark(Command):
    """Insert: tag the file under the cursor, or untag it, and step down.

    DN handled ``kbIns`` in ``TFilePanel.HandleEvent`` rather than through a
    command; it is one here so the key lives in a key table like the rest.
    """


@dataclass(frozen=True, slots=True)
class GoParent(Command):
    """Ctrl+PgUp, ``_CtrlPgUp``: the parent directory, the cursor on the one
    just left.

    Backspace too, DN's ``kbBack`` under ``fmoBackGoesBack``, which ran
    ``_CtrlPgUp`` when ``CmdLine.Str`` was empty or Shift was held
    (``ShiftState and 3 <> 0``) and otherwise left the key to the command
    line.  *by_key* is that Backspace, as it is for :class:`SelectGroup`:
    with text on the line it steps aside.  Ctrl+PgUp and Shift+Backspace never
    do.
    """

    by_key: bool = False


@dataclass(frozen=True, slots=True)
class ScrollNames(Command):
    """Left and Right in the simple and the detailed modes: scroll every name
    in the active panel a cell along, so a name cut short can be read to its
    end.  Not DN's -- its names were 8.3 and always fitted.

    *step* is -1 for Left and 1 for Right.  Like Backspace's
    :class:`GoParent`, the key steps aside while the command line has text,
    and it does when there is nothing to scroll that way, so the caret moves.
    """

    step: int = 1


@dataclass(frozen=True, slots=True)
class MoveSeparator(Command):
    """Alt+Left and Alt+Right: the divider between the two sides a column along.

    DOS Navigator's ``kbAltLeft``/``kbAltRight`` in ``TDoubleWindow.HandleCommand``,
    which moved the ``TSeparator``; no ``cm*`` of its own.  *step* is -1 for
    Left and 1 for Right.  Nothing happens while a side is hidden.
    """

    step: int = 1


@dataclass(frozen=True, slots=True)
class SelectGroup(Command):
    """Gray ``+``, ``cmPanelSelect``: tag every file a mask matches.

    *invert* is Shift held, which opened DN's dialog with *Except mask*
    already ticked (``SelectFiles``'s ``XORs``).  *by_key* says the Gray key
    sent it rather than the menu: the key is also a character, and with text
    on the command line it types there instead (a departure -- DN's panel
    always took it).
    """

    invert: bool = False
    by_key: bool = False


@dataclass(frozen=True, slots=True)
class UnselectGroup(Command):
    """Gray ``-``, ``cmPanelUnselect``: untag everything a mask matches.

    The fields are :class:`SelectGroup`'s.
    """

    invert: bool = False
    by_key: bool = False


@dataclass(frozen=True, slots=True)
class InvertSelection(Command):
    """Gray ``*``, ``cmPanelInvertSel``: tag what is untagged, and untag the rest.

    *directories* is Ctrl held (``kbCtrlGAst``), which took directories in
    too; the plain key and the menu leave them as they are.  *by_key* is
    :class:`SelectGroup`'s.
    """

    directories: bool = False
    by_key: bool = False


class ToggleShowMode(Command):
    """Ctrl+Y, ``cmToggleShowMode``."""

    title = "Show"


class CountLength(Command):
    """Alt+G: the bytes under the directory at the cursor and the tagged ones.

    DOS Navigator's ``cmCountLen``, Panel > Count directory length.
    """


class UuEncode(Command):
    """Ctrl+F7, File > UU Encode: the file at the cursor, UU-encoded.

    DOS Navigator's ``cmUUEncodeFile`` (``UuEncode``, UUCODE.PAS).
    """


class UuDecode(Command):
    """Ctrl+F8, File > UU Decode: the files UU-encoded in the file at the cursor.

    DOS Navigator's ``cmUUDecodeFile`` (``UuDecode``, UUCODE.PAS).
    """


class CalculateChecksums(Command):
    """File > Checksums > Calculate: the tagged files' digests, in one list or
    a list beside each (:mod:`navigator.lib.file_ops.checksum`).

    **A departure**, asked for: DOS Navigator had no checksums, so there is
    no ``cm*`` to name it after.  Not bound: the key is the user's to give.
    """


class VerifyChecksums(Command):
    """File > Checksums > Verify: the files the tagged lists -- or the one at
    the cursor -- name, hashed again and checked.

    **A departure**, asked for, as :class:`CalculateChecksums` is.  Not bound.
    """


class DirHistory(Command):
    """Alt+Backspace, Panel > History of directories: where the panels have been.

    DOS Navigator's ``cmDirHistory`` (``DirHistoryMenu``).
    """


class ListOfDirs(Command):
    """Alt+Shift+0, Panel > Quick dirs: the bookmarks box for the active panel.

    DOS Navigator's ``cmListOfDirs`` (``DoQuickChange``), which listed its
    quick directories; they are the bookmarks here.
    """


@dataclass(frozen=True, slots=True)
class QuickChange(Command):
    """Alt+1 .. Alt+9: the active panel to bookmark *slot*, no box.

    DOS Navigator's ``cmQuickChange1`` .. ``cmQuickChange9``.
    """

    slot: int = 1


@dataclass(frozen=True, slots=True)
class StoreQuickDir(Command):
    """Alt+Shift+1 .. Alt+Shift+9: the active panel's directory bookmarked at
    place *slot*, asked first (``dlPromptForQDir``)."""

    slot: int = 1


class AdvancedFilter(Command):
    """Alt+Del, Panel > Advanced filter: show or hide files by extension.

    DOS Navigator's ``cmAdvFilter`` (``CM_AdvancedFilter``).
    """


class SetupColumns(Command):
    """Alt+K, Panel > Setup columns: which columns the panel shows.

    DOS Navigator's ``cmSetupColumns`` (``CM_SetShowParms``).
    """


class DirBranch(Command):
    """Panel > Directory Branch: every file below the directory, in one listing.

    DOS Navigator's ``cmDirBranch`` (``CM_Branch``, ``OpenDirectory``).  Its
    Ctrl+H is Navigator's hidden-files key, so it has the menu alone.
    """


class ReadFileList(Command):
    """Alt+V, Panel > Read file list: the list file at the cursor as a listing.

    DOS Navigator's ``cmPanelMakeList`` (``TFindDrive.InitList``).
    """


class Panelize(Command):
    """Alt+O, Panel > Panelize command: what a command prints, as a listing.

    A departure: Midnight Commander's *External panelize*; DOS Navigator had
    no command of its own for it (:mod:`navigator.lib.file_ops.panelize`).
    """


class MultiRename(Command):
    """Alt+M, Panel > Multi-rename: the tagged files renamed by a pattern.

    A departure: Total Commander's *Multi-Rename Tool* (its Ctrl+M is Enter
    in a terminal); DOS Navigator's group rename was F6's ``*``/``?`` mask
    (:mod:`navigator.lib.file_ops.multirename`).
    """


class UndoMultiRename(Command):
    """Panel > Undo multi-rename: the last batch's names put back.

    A departure, with :class:`MultiRename`; kept for the session only.
    """


class RestoreTrash(Command):
    """File > Restore from Trash: what is selected in the Trash put back where it came from.

    Not DOS Navigator's: its undelete was the *Reanimator*
    (:mod:`navigator.lib.drives.trash`).
    """


class ChangeInactive(Command):
    """Shift+Enter in a *Find:* listing: the other panel goes to the file.

    DOS Navigator's ``cmChangeInactive``, ``cmFindGotoFile`` sent to the
    passive panel.
    """

    title = "Show in other panel"


class GoToFile(Command):
    """Enter in a *Find:* listing, as a command for the right-click menu: the
    found file's own directory, the cursor on it -- DN's ``GotoFile``.  Not
    bound: Enter is the panel's own (``Panel.choose``)."""

    title = "Go to file"


class CompareDir(Command):
    """Panel > Compare directories: tag what each panel has that the other
    lacks or has older.

    DOS Navigator's ``cmCompareDir``.  Its Ctrl+C is not bound: that key is
    kept for copying to the clipboard.
    """


class DiffFiles(Command):
    """File > Compare files: two files side by side, line against line.

    **A departure**: DOS Navigator compared files only to tell whether they
    were the same (``CompareFiles``, behind *Compare directories*), so the
    name is not its.  Not bound: the key is the user's to give.
    """

    title = "Compare"


@dataclass(frozen=True, slots=True)
class SetSyncAction(Command):
    """In the *Synchronize* window, what is done with the row under the
    cursor: ``right`` or ``left`` (copied that way), ``skip``, ``delete``, or
    ``default`` for what its status suggests.  Total Commander's keys, as the
    window is its."""

    action: str = "default"


@dataclass(frozen=True, slots=True)
class SetAllSyncActions(Command):
    """In the *Synchronize* window, every row that allows it copied one way:
    ``right`` or ``left``; ``default`` gives each its own back."""

    action: str = "default"


class Synchronize(Command):
    """F5 in the *Synchronize* window: do what its rows say."""

    title = "Sync"


class ToggleHidden(Command):
    """Ctrl+H: show or hide the active panel's dot-files.

    DOS Navigator's nearest is ``ossShowHidden``, a system option for every
    panel; this is per panel, as Ctrl+Y's show mode is, and the key is ours.
    It was DN's *Directory Branch*, which does not exist yet and so gave it
    up.  A legacy terminal sends Ctrl+H as the byte 0x08, which reaches this
    only where the tty says Backspace is 0x7F -- xfce4-terminal, GNOME
    Terminal, xterm -- and is Backspace anywhere else, where the menu is the
    way in.
    """

    title = "Hidden"


class ToggleInfoLines(Command):
    """Alt+I: show or hide the active panel's footer -- the *Info divider*
    and the *Totals* and *Free space* lines under the listing.

    Ours, per panel as Ctrl+H is: DN changed them only through the
    *Display* boxes of Panel Options and New Manager defaults.  No title,
    so the Alt key bar keeps its room for the keys DN put there.
    """


class ArchiveFiles(Command):
    """Shift+F1, ``cmPanelArcFiles``."""

    title = "Arc"


class ExtractArchive(Command):
    """Shift+F2, ``cmExtractArchive``: the archives at the cursor or tagged,
    outside them, extracted -- the *Extract files* box asking where."""

    title = "Ext"


class ExtractTo(Command):
    """``cmExtractTo``: in an archive, what is tagged (or at the cursor)
    extracted through the *Extract files* box.

    DN put it on F4 in an archive panel's key bar (``hcArchives``); here F4
    stays Edit, which works in an archive, and this is Panel > *Extract
    to*: a recorded departure.
    """


class ArcTest(Command):
    """``cmArcTest``: in an archive, what is tagged (or the whole archive,
    at ``..``) read through and its checks made.

    DN's F6 in an archive panel; here Panel > *Test archive*, F6 staying
    Rename/Move -- the same departure as :class:`ExtractTo`.
    """


class EditNamed(Command):
    """Shift+F4, ``cmXEditFile``: edit a file whose name is asked for."""

    title = "Edit..."


@dataclass(frozen=True, slots=True)
class DeleteSingle(Command):
    """Shift+F8, ``cmSingleDel``: the file under the cursor, not the selection.

    Shift+Del too, the File menu's key for it.  *by_key* is that Shift+Del,
    which steps aside while the command line has text, where it cuts.
    """

    title = "Del"
    by_key: bool = False


@dataclass(frozen=True, slots=True)
class PutInClipboard(Command):
    """Ctrl+C, Ctrl+Ins: the selection's paths on the clipboard, and the
    entries kept to be copied by a paste (:mod:`navigator.lib.file_ops.clip`).

    Ctrl+Ins is DOS Navigator's own, ``_CtrlIns`` posting
    ``cmPutInClipboard``, which put the names there and kept nothing.
    *by_key*: with text on the command line it steps aside, and the key is
    the line's, as Del is.
    """

    by_key: bool = False


@dataclass(frozen=True, slots=True)
class CutToClipboard(Command):
    """Ctrl+X, Ctrl+Del: as :class:`PutInClipboard`, to be moved.  A departure:
    DN's panel Ctrl+Del took the entries off the listing, which was never
    ported.  With text on the line Ctrl+X walks the command history as before."""

    by_key: bool = False


@dataclass(frozen=True, slots=True)
class PasteFromClipboard(Command):
    """Ctrl+V, Shift+Ins: the clipped entries into the active panel's
    directory, through F5's or F6's dialog.  A departure, named after
    ``cmGetFromClipboard``.  Without a clip, or with text on the line, the key
    pastes text on the command line as before."""

    by_key: bool = False


@dataclass(frozen=True, slots=True)
class ClearClipboard(Command):
    """Esc while files wait to be pasted: forget them.  Otherwise Esc is what
    it was -- clearing the line, or *ESC for user screen*."""

    by_key: bool = False


__all__ = [
    "UserMenu",
    "View",
    "OpenWith",
    "ViewAsText",
    "ViewAsHex",
    "ViewAsDataBase",
    "Edit",
    "Copy",
    "RenameMove",
    "MakeLink",
    "ChangeAttributes",
    "MakeDirectory",
    "Delete",
    "SwitchPanel",
    "Rescan",
    "ChangeDirectory",
    "ToggleTree",
    "SortBy",
    "CountLength",
    "UuEncode",
    "UuDecode",
    "CalculateChecksums",
    "VerifyChecksums",
    "CompareDir",
    "DiffFiles",
    "SetSyncAction",
    "SetAllSyncActions",
    "Synchronize",
    "ChangeInactive",
    "GoToFile",
    "ReadFileList",
    "Panelize",
    "MultiRename",
    "UndoMultiRename",
    "RestoreTrash",
    "DirBranch",
    "SetupColumns",
    "AdvancedFilter",
    "DirHistory",
    "ListOfDirs",
    "QuickChange",
    "StoreQuickDir",
    "SwapPanels",
    "ChangeDrive",
    "ChangeLeft",
    "ChangeRight",
    "PanelSetup",
    "MakeList",
    "FastRename",
    "QuickRename",
    "FindFile",
    "Calculator",
    "PrintFile",
    "DiskInfo",
    "GoToTreeDirectory",
    "QuickView",
    "ToggleMark",
    "GoParent",
    "ScrollNames",
    "MoveSeparator",
    "SelectGroup",
    "UnselectGroup",
    "InvertSelection",
    "ToggleShowMode",
    "ToggleHidden",
    "ToggleInfoLines",
    "ArchiveFiles",
    "ExtractArchive",
    "EditNamed",
    "DeleteSingle",
    "PutInClipboard",
    "CutToClipboard",
    "PasteFromClipboard",
    "ClearClipboard",
]

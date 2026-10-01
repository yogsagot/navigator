"""What the user can ask Navigator for, by name rather than by key.

The key bar commands carry DOS Navigator's own captions as their titles --
the file panel's status line, ``StatusDef hcFilePanel`` in ``DN.DNR`` --
because the key bar is where they are read.  Most of them have no handler yet
-- View, Edit, Copy and the rest are the file operations still to be written
-- and a command nobody handles is a disabled one, so the key bar shows them
in the status line's *Disabled* colour until they exist.  That is the original
behaving as it did whenever a command was unavailable, not a placeholder look.

Where each is bound says whose it is: the panel commands on ``Manager``, since
they act on a panel; Help, the menu and the way out on the application, since
they mean the same wherever the focus is.
"""

from __future__ import annotations

from dataclasses import dataclass

from navkit.commands import Command

# The panel's quick search and the tree's are one command, so it is the
# library's: re-exported here, where the panel's key tables name it.
from navml.commands import QuickSearch


class Help(Command):
    title = "Help"


class About(Command):
    """≡ > About: DOS Navigator's ``cmAbout``, the name, version and author."""

    title = "About"


class UserMenu(Command):
    title = "User"


class View(Command):
    title = "View"


class ViewAsText(Command):
    """File > View > As Text: ``cmViewText``, the viewer opened in text mode."""


class ViewAsHex(Command):
    """File > View > As Hex: ``cmViewHex``, the viewer opened in hex mode."""


# -- the file viewer ---------------------------------------------------------
#
# ``StatusDef hcView``: bound in ``file_window.nml``, captioned as DN captioned
# them there, so the key bar is the viewer's while a viewer has the keyboard.


class Unwrap(Command):
    """F2, ``cmUnWrap``: wrap long lines, or stop."""

    title = "(Un)Wrap"


class HexMode(Command):
    """F4, ``cmHexMode``: text, hex, dump, and round again."""

    title = "Hex/ASCII/Dump"


class GotoAddress(Command):
    """F5, ``cmGotoCell``: go to a hex address.  Hex and dump only, as in DN."""

    title = "Goto"


class AddFilter(Command):
    """F6, ``cmAddFilter``: no filter, ``{ASCII}``, ``{32-255}``."""

    title = "Filter"


class SearchFor(Command):
    """F7, ``cmSearchFor``: the *Find* dialog."""

    title = "Search"


class ReverseSearch(Command):
    """Ctrl+F7, ``cmReverseSearch``: the last search again, the other way."""

    title = "Reverse Search"


class ContinueSearch(Command):
    """Shift+F7, ``cmContinueSearch``: the last search again."""

    title = "Continue Search"


class SearchAgain(Command):
    """Ctrl+L: ``cmContinueSearch`` again, bound with no caption as DN bound it."""


class CloseViewer(Command):
    """F3 in a viewer: close it, as Midnight Commander's F3 does.

    Not DOS Navigator's -- its ``hcView`` bound nothing to F3 -- and so bound
    with no caption: the key that opened the viewer closes it again, and the
    status line stays DN's.
    """


class Edit(Command):
    title = "Edit"


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


@dataclass(frozen=True, slots=True)
class Quit(Command):
    """Leave Navigator.

    *desktop* marks the Alt+X binding, which quits only while the desktop is
    what the user is looking at: with Ctrl+O's console over the windows, Meta+X
    belongs to the program in it.  One command with a field rather than two
    commands, because both mean *quit* and a key bar shows them as one.
    """

    title = "Exit"

    desktop: bool = False


class ToggleConsole(Command):
    """Ctrl+O: put the windows away to show the console, or bring them back."""


class ExecuteCommandLine(Command):
    """Enter with something on the command line: run it.

    DOS Navigator's ``cmExecCommandLine``, which the panel's own Enter sent
    first and fell back from when the line was blank (``FLPANELX.PAS``).
    Here that is a key table's rule rather than the panel's: bound on the
    application, so it is asked before the panel sees Enter, and disabled
    while the line is empty, so the key falls through to the panel.
    """


class CompleteCommandLine(Command):
    """Tab with something on the command line: complete the word at the caret.

    Not DOS Navigator's -- ``TCommandLine`` completed nothing, and Tab only
    ever switched panels.  Bound the way Enter is, so the rule is Enter's:
    with the line empty the command is disabled and Tab falls through to the
    panels, and with text on it the shell is asked what the word could be.
    """


class InsertName(Command):
    """Ctrl+Enter: the name under the panel's cursor, typed onto the command line.

    DOS Navigator's ``_CtrlEnter`` (``FLPANELX.PAS``) sending ``cmInsertName``.
    On ``..`` it is the panel's own directory, whole.  Alt+Enter is bound to
    it as well, Midnight Commander's key for the same thing, because a
    terminal that does not speak the kitty keyboard protocol sends Ctrl+Enter
    as a plain Enter.
    """


class InsertPath(Command):
    """Ctrl+Shift+Enter: as :class:`InsertName`, but the whole path.

    ``_CtrlEnter`` with Shift held, which prefixed the panel's directory.
    """


class CommandLineHome(Command):
    """Home with something on the command line: to its start, not the list's top."""


class CommandLineEnd(Command):
    """End with something on the command line: to its end, not the list's bottom."""


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


class ChooseTarget(Command):
    """F10 in the Copy dialog: pick where the files go from a tree.

    DOS Navigator's ``cmTree``, which ``StatusDef hcCopyDialog`` put on F10
    and the dialog's *Tree* button sent too.
    """

    title = "Tree"


class NewManager(Command):
    """Ctrl+F3: another file manager window, the size of the desktop.

    DOS Navigator's ``cmCreatePanel``, Manager > New.
    """

    title = "New Manager"


class OpenTreeWindow(Command):
    """Disk > Directory tree: a *Directory Tree* window on the desktop.

    DOS Navigator's ``cmCreateTree`` -- here opening the ``TTreeWindow`` that
    1.51 defined and never used.
    """

    title = "Tree"


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
    """Alt+C, ``cmChangeDrive``."""

    title = "Drive"


class PanelSetup(Command):
    """Alt+S, ``cmPanelSetup``."""

    title = "Setup"


class MakeList(Command):
    """Alt+L, ``cmMakeList``."""

    title = "List"


class FastRename(Command):
    """Alt+F6, ``cmFastRename``."""

    title = "Ren"


class FindFile(Command):
    """Alt+F7, ``cmFindFile``."""

    title = "Find"


class Calculator(Command):
    """Ctrl+F6, ``cmCalculator``."""

    title = "Calc"


class PrintFile(Command):
    """Ctrl+F9, ``cmPrintFile``."""

    title = "Print"


class ToggleDescriptions(Command):
    """Ctrl+K, ``cmToggleDescriptions``."""

    title = "Desc"


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


class ToggleMarkBySpace(Command):
    """Space with the command line empty: :class:`ToggleMark`.

    DN's ``fmoSpaceToggle``, on by default: ``kbSpace`` shared ``kbIns``'s
    branch but gave up whenever ``CmdLine.Str`` was not empty, so that a blank
    typed into a command still reached it.  A command of its own because that
    condition is the command line's, and ``Shell`` -- which owns the line --
    is what handles it.
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


class ArchiveFiles(Command):
    """Shift+F1, ``cmPanelArcFiles``."""

    title = "Arc"


class ExtractArchive(Command):
    """Shift+F2, ``cmExtractArchive``."""

    title = "Ext"


class PhoneBook(Command):
    """Shift+F3, ``cmPhoneBook``."""

    title = "Phones"


class EditNamed(Command):
    """Shift+F4, ``cmXEditFile``: edit a file whose name is asked for."""

    title = "Edit..."


class Reanimate(Command):
    """Shift+F6, ``cmReanimator``."""

    title = "Reanimate"


@dataclass(frozen=True, slots=True)
class DeleteSingle(Command):
    """Shift+F8, ``cmSingleDel``: the file under the cursor, not the selection.

    Shift+Del too, the File menu's key for it.  *by_key* is that Shift+Del,
    which steps aside while the command line has text, where it cuts.
    """

    title = "Del"
    by_key: bool = False


# -- the editor ------------------------------------------------------------------
#
# ``EDITOR COMMANDS`` in ``DN.DNR`` and ``StatusDef hcEditor``: one command per
# ``cm*`` the editor answers, named after it.  The movements carry *extend*,
# which is what Shift held with the key makes of them -- DN read the shift
# state off the BIOS (``BMarking``); a key table says it with a second binding.


@dataclass(frozen=True, slots=True)
class EditorMovement(Command):
    """A cursor movement; with *extend* it drags the block's end along."""

    extend: bool = False


@dataclass(frozen=True, slots=True)
class MoveLeft(EditorMovement):
    """``cmMoveLeft``: Left, ^S."""


@dataclass(frozen=True, slots=True)
class MoveRight(EditorMovement):
    """``cmMoveRight``: Right, ^D."""


@dataclass(frozen=True, slots=True)
class MoveUp(EditorMovement):
    """``cmMoveUp``: Up, ^E."""


@dataclass(frozen=True, slots=True)
class MoveDown(EditorMovement):
    """``cmMoveDown``: Down, ^X."""


@dataclass(frozen=True, slots=True)
class WordLeft(EditorMovement):
    """``cmWordLeft``: Ctrl+Left, ^A."""


@dataclass(frozen=True, slots=True)
class WordRight(EditorMovement):
    """``cmWordRight``: Ctrl+Right, ^F."""


@dataclass(frozen=True, slots=True)
class LineStart(EditorMovement):
    """Home: the horizontal scroll bar's minimum in DN, the line's first column."""


@dataclass(frozen=True, slots=True)
class LineEnd(EditorMovement):
    """``cmEnd``: End, after the line's last non-blank."""


@dataclass(frozen=True, slots=True)
class PageUp(EditorMovement):
    """``cmPgUp``: PgUp, ^R."""


@dataclass(frozen=True, slots=True)
class PageDown(EditorMovement):
    """``cmPgDn``: PgDn, ^C."""


@dataclass(frozen=True, slots=True)
class ScreenTop(EditorMovement):
    """``cmCtrlHome``: Ctrl+Home, the top row on screen."""


@dataclass(frozen=True, slots=True)
class ScreenBottom(EditorMovement):
    """``cmCtrlEnd``: Ctrl+End, the bottom row on screen."""


@dataclass(frozen=True, slots=True)
class TextStart(EditorMovement):
    """Ctrl+PgUp: the vertical scroll bar's minimum in DN, the first line."""


@dataclass(frozen=True, slots=True)
class TextEnd(EditorMovement):
    """Ctrl+PgDn: the last line."""


class ScrollUp(Command):
    """``cmScrollUp``: ^W, the text one line down under a cursor that stays."""


class ScrollDown(Command):
    """``cmScrollDn``: ^Z."""


class NewLine(Command):
    """``cmEnter``: Enter, and Ctrl+Enter, which DN kept for it whatever else."""


class InsertLine(Command):
    """``cmInsLine``: ^N, a line break after the cursor, which stays."""


class TabKey(Command):
    """``cmTab``: Tab, ^I."""


class DeleteBack(Command):
    """``cmDelBackChar``: Backspace, ^H."""


class DeleteChar(Command):
    """``cmDelChar``: Del, ^G."""


class DeleteWordLeft(Command):
    """``cmDelWordLeft``: Ctrl+Backspace."""


class DeleteWordRight(Command):
    """``cmDelWordRight``: ^T."""


class DeleteLine(Command):
    """``cmDeleteLine``: ^Y."""


class DeleteToEnd(Command):
    """``cmDeltoEOLN``: ^Q^Y."""


class SwitchInsert(Command):
    """``cmSwitchIns``: Ins, ^V -- insert and overwrite."""


class Undo(Command):
    """``cmUndo``: Alt+Backspace, ^Q^L."""

    title = "Undo"


class SaveText(Command):
    """``cmSaveText``: F2."""

    title = "Save"


__all__ = [
    "About",
    "ArchiveFiles",
    "Calculator",
    "ChangeDrive",
    "DeleteSingle",
    "DiskInfo",
    "CommandLineEnd",
    "CommandLineHome",
    "EditNamed",
    "ExecuteCommandLine",
    "ExtractArchive",
    "FastRename",
    "FindFile",
    "MakeList",
    "PanelSetup",
    "PhoneBook",
    "PrintFile",
    "QuickSearch",
    "QuickView",
    "Reanimate",
    "SortBy",
    "ToggleDescriptions",
    "InvertSelection",
    "SelectGroup",
    "ToggleMark",
    "ToggleMarkBySpace",
    "UnselectGroup",
    "ToggleShowMode",
    "ChangeDirectory",
    "ChooseTarget",
    "Copy",
    "Delete",
    "Edit",
    "Help",
    "MakeDirectory",
    "MakeLink",
    "NewManager",
    "OpenTreeWindow",
    "Quit",
    "RenameMove",
    "Rescan",
    "SwitchPanel",
    "ToggleConsole",
    "ToggleTree",
    "UserMenu",
    "View",
    "ViewAsHex",
    "ViewAsText",
    "AddFilter",
    "CloseViewer",
    "ContinueSearch",
    "GotoAddress",
    "HexMode",
    "ReverseSearch",
    "SearchAgain",
    "SearchFor",
    "Unwrap",
    "EditorMovement",
    "MoveLeft",
    "MoveRight",
    "MoveUp",
    "MoveDown",
    "WordLeft",
    "WordRight",
    "LineStart",
    "LineEnd",
    "PageUp",
    "PageDown",
    "ScreenTop",
    "ScreenBottom",
    "TextStart",
    "TextEnd",
    "ScrollUp",
    "ScrollDown",
    "NewLine",
    "InsertLine",
    "TabKey",
    "DeleteBack",
    "DeleteChar",
    "DeleteWordLeft",
    "DeleteWordRight",
    "DeleteLine",
    "DeleteToEnd",
    "SwitchInsert",
    "Undo",
    "SaveText",
]

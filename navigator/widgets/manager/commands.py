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


class ViewAsText(Command):
    """File > View > As Text: ``cmViewText``, the viewer opened in text mode."""


class ViewAsHex(Command):
    """File > View > As Hex: ``cmViewHex``, the viewer opened in hex mode."""


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


class HideInactive(Command):
    """Ctrl+P: hide the side without the keyboard, or show it again.

    DOS Navigator's ``cmSwitchOther``, Manager > Show/hide inactive panel.
    """


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

    DOS Navigator's drive letters; ``navigator/bookmarks.py`` has the
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


__all__ = [
    "UserMenu",
    "View",
    "ViewAsText",
    "ViewAsHex",
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
    "ChangeDrive",
    "ChangeLeft",
    "ChangeRight",
    "PanelSetup",
    "MakeList",
    "FastRename",
    "FindFile",
    "Calculator",
    "PrintFile",
    "DiskInfo",
    "QuickView",
    "ToggleMark",
    "GoParent",
    "ScrollNames",
    "SelectGroup",
    "UnselectGroup",
    "InvertSelection",
    "ToggleShowMode",
    "ToggleHidden",
    "ArchiveFiles",
    "ExtractArchive",
    "EditNamed",
    "DeleteSingle",
]

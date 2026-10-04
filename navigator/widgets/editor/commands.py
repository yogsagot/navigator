"""The editor's commands: what ``FileEditor`` and ``EditWindow`` handle."""

from __future__ import annotations

from dataclasses import dataclass

from navkit.commands import Command


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


class ClipboardCut(Command):
    """``cmCut``: Shift+Del -- the block to the clipboard, and out of the text.

    Not ``Cut``/``Copy``/``Paste``: ``Copy`` is F5's, and a handler named
    ``on_copy`` or ``on_paste`` would answer that command or a paste event.
    """

    title = "Cut"


class ClipboardCopy(Command):
    """``cmCopy``: Ctrl+Ins -- the block to the clipboard."""

    title = "Copy"


class ClipboardPaste(Command):
    """``cmPaste``: Shift+Ins -- the clipboard at the cursor."""

    title = "Paste"


class Clear(Command):
    """``cmClear``: Ctrl+Del, ^K^Y -- the block out of the text, the clipboard untouched."""

    title = "Clear"


# -- the ^K and ^Q block commands ----------------------------------------------
#
# WordStar's two-key commands, which DN's ``EDITOR COMMANDS`` kept: Ctrl+K
# then a letter, the letter with or without Ctrl.  Each named after its
# ``cm*`` in that table.


class BlockStart(Command):
    """``cmBlockStart``: ^K^B -- the block begins at the cursor."""

    title = "Block start"


class BlockEnd(Command):
    """``cmBlockEnd``: ^K^K -- the block ends at the cursor."""

    title = "Block end"


class HideBlock(Command):
    """``cmHideBlock``: ^K^H, Alt+H -- the block hidden, or shown again."""

    title = "Hide block"


class CopyBlock(Command):
    """``cmCopyBlock``: ^K^C -- a copy of the block at the cursor, marked in its place."""

    title = "Copy block"


class MoveBlock(Command):
    """``cmMoveBlock``: ^K^V -- the block moved to the cursor."""

    title = "Move block"


class IndentBlock(Command):
    """``cmIndentBlock``: ^K^I -- every line of the block a column further right."""

    title = "Indent"


class UnindentBlock(Command):
    """``cmUnindentBlock``: ^K^U -- every line of the block a column further left, where a blank allows."""

    title = "Unindent"


class UpcaseBlock(Command):
    """``cmUpcaseBlock``: ^K^[ -- the block in upper case."""

    title = "Uppercase"


class LowcaseBlock(Command):
    """``cmLowcaseBlock``: ^K^] -- the block in lower case."""

    title = "Lowercase"


class CapitalizeBlock(Command):
    """``cmCapitalizeBlock``: ^K^\\ -- each word of the block capitalised."""

    title = "Capitalize"


class SortBlock(Command):
    """``cmSortBlock``: ^K^S, Alt+T -- the column block's lines sorted by its columns."""

    title = "Sort"


class CalcBlock(Command):
    """``cmCalcBlock``: Alt+Ins, Block > *Calculate sum* -- the column block's numbers
    added up, the sum to the clipboard.  (DN's table also gave it ^K^U, which
    ``cmUnindentBlock`` had first and its menu shows.)"""

    title = "Calculate sum"


class PrintBlock(Command):
    """``cmPrintBlock``: ^K^P, Shift+F8 -- the block to the printer."""

    title = "Print Block"


class BracketPair(Command):
    """``cmBracketPair``: Alt+Left, Alt+Right, ^Q[, ^Q^] -- the cursor to the
    bracket that pairs with the one under it."""

    title = "Bracket pair"


class MarkWord(Command):
    """``cmMarkWord``: ^K^T -- the word at the cursor, marked."""

    title = "Mark word"


class MarkLine(Command):
    """``cmMarkLine``: ^K^L -- the cursor's line, marked."""

    title = "Mark line"


class MoveBlockStart(Command):
    """``cmMoveBlockStart``: ^Q^B -- the cursor to the block's start."""

    title = "Block start"


class MoveBlockEnd(Command):
    """``cmMoveBlockEnd``: ^Q^K -- the cursor to the block's end."""

    title = "Block end"


@dataclass(frozen=True, slots=True)
class PlaceMarker(Command):
    """``cmPlaceMarker``: ^K1 to ^K9 -- the cursor's place kept as marker *marker*."""

    title = "Place marker"

    marker: int = 1


@dataclass(frozen=True, slots=True)
class GotoMarker(Command):
    """``cmGotoMarker``: ^Q1 to ^Q9 -- the cursor to marker *marker*, centred."""

    title = "Go to marker"

    marker: int = 1


class BlockRead(Command):
    """``cmBlockRead``: ^K^R -- Editor > Edit > *Paste from...*: a file's text at the cursor, marked."""

    title = "Read block"


class BlockWrite(Command):
    """``cmBlockWrite``: ^K^W -- Editor > Edit > *Copy to...*: the block written to a file."""

    title = "Write block"


class InsertDate(Command):
    """``cmInsertDate``: ^Q^D -- Editor > Misc > *Insert date*: today's date at the cursor."""

    title = "Insert date"


class InsertTime(Command):
    """``cmInsertTime``: ^Q^T -- Editor > Misc > *Insert time*: the time now at the cursor."""

    title = "Insert time"


class SwitchBlock(Command):
    """``cmSwitchBlock``: ^B^V, Editor > Options > *Vertical blocks* -- column blocks
    or stream ones (``VertBlock``), the block marked kept and read the other way."""

    title = "Vertical blocks"


class Undo(Command):
    """``cmUndo``: Alt+Backspace, ^Q^L."""

    title = "Undo"


class SaveText(Command):
    """``cmSaveText``: F2."""

    title = "Save"


__all__ = [
    "Clear",
    "ClipboardCopy",
    "ClipboardCut",
    "ClipboardPaste",
    "EditorMovement",
    "BracketPair",
    "PrintBlock",
    "CalcBlock",
    "SortBlock",
    "GotoMarker",
    "PlaceMarker",
    "InsertDate",
    "BlockRead",
    "BlockWrite",
    "InsertTime",
    "BlockStart",
    "BlockEnd",
    "HideBlock",
    "CopyBlock",
    "MoveBlock",
    "IndentBlock",
    "UnindentBlock",
    "UpcaseBlock",
    "LowcaseBlock",
    "CapitalizeBlock",
    "MarkWord",
    "MarkLine",
    "MoveBlockStart",
    "MoveBlockEnd",
    "SwitchBlock",
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

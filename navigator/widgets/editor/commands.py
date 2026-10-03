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


class ClearBlock(Command):
    """``cmClear``: Ctrl+Del -- the block out of the text, the clipboard untouched."""

    title = "Clear"


# -- the ^K and ^Q block commands ----------------------------------------------
#
# WordStar's two-key commands, which DN's ``EDITOR COMMANDS`` kept: Ctrl+K
# then a letter, the letter with or without Ctrl.  Named after what they do,
# DN's own ``cm*`` names for them not being to hand.


class MarkBlockStart(Command):
    """^K B: the block begins at the cursor."""

    title = "Block start"


class MarkBlockEnd(Command):
    """^K K: the block ends at the cursor."""

    title = "Block end"


class HideBlock(Command):
    """^K H: unmark the block."""

    title = "Hide block"


class CopyBlock(Command):
    """^K C: a copy of the block at the cursor, marked in its place."""

    title = "Copy block"


class MoveBlock(Command):
    """^K V: the block moved to the cursor."""

    title = "Move block"


class IndentBlock(Command):
    """^K I: every line of the block a column further right."""

    title = "Indent"


class UnindentBlock(Command):
    """^K U: every line of the block a column further left, where a blank allows."""

    title = "Unindent"


class UppercaseBlock(Command):
    """^K [: the block in upper case."""

    title = "Uppercase"


class LowercaseBlock(Command):
    """^K ]: the block in lower case."""

    title = "Lowercase"


class CapitalizeBlock(Command):
    """^K \\: each word of the block capitalised."""

    title = "Capitalize"


class MarkWord(Command):
    """^K T: the word at the cursor, marked."""

    title = "Mark word"


class MarkLine(Command):
    """^K L: the cursor's line, marked."""

    title = "Mark line"


class GoBlockStart(Command):
    """^Q B: the cursor to the block's start."""

    title = "Block start"


class GoBlockEnd(Command):
    """^Q K: the cursor to the block's end."""

    title = "Block end"


class ReadBlock(Command):
    """^K R, Editor > Edit > *Paste from...*: a file's text at the cursor, marked."""

    title = "Read block"


class WriteBlock(Command):
    """^K W, Editor > Edit > *Copy to...*: the block written to a file."""

    title = "Write block"


class InsertDate(Command):
    """^Q D, Editor > Misc > *Insert date*: today's date at the cursor."""

    title = "Insert date"


class InsertTime(Command):
    """^Q T, Editor > Misc > *Insert time*: the time now at the cursor."""

    title = "Insert time"


class VerticalBlocks(Command):
    """Editor > Options > *Vertical blocks*: column blocks, or stream ones (DN's ``VertBlock``)."""

    title = "Vertical blocks"


class Undo(Command):
    """``cmUndo``: Alt+Backspace, ^Q^L."""

    title = "Undo"


class SaveText(Command):
    """``cmSaveText``: F2."""

    title = "Save"


__all__ = [
    "ClearBlock",
    "ClipboardCopy",
    "ClipboardCut",
    "ClipboardPaste",
    "EditorMovement",
    "InsertDate",
    "ReadBlock",
    "WriteBlock",
    "InsertTime",
    "MarkBlockStart",
    "MarkBlockEnd",
    "HideBlock",
    "CopyBlock",
    "MoveBlock",
    "IndentBlock",
    "UnindentBlock",
    "UppercaseBlock",
    "LowercaseBlock",
    "CapitalizeBlock",
    "MarkWord",
    "MarkLine",
    "GoBlockStart",
    "GoBlockEnd",
    "VerticalBlocks",
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

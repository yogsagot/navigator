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


class Undo(Command):
    """``cmUndo``: Alt+Backspace, ^Q^L."""

    title = "Undo"


class SaveText(Command):
    """``cmSaveText``: F2."""

    title = "Save"


__all__ = [
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

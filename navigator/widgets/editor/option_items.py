"""What the editor's and the viewer's option strips show (``navml``'s ``OptionStrip``).

A departure, as the strip is: DN showed these options only as the ``On``/``Off``
of the Editor menu's key column.  Switches are spelled by the glyph tier the
window may draw with -- a word on a plain terminal, a symbol on a Unicode one, a
Font Awesome icon on a Nerd Font (:mod:`navigator.icons`) -- and values (the
viewer's mode, the encoding, the file type) are always words.  The symbols were
chosen from what JetBrainsMono Nerd Font carries, so none falls back to another
font: ``⎀`` and ``↵`` gave way to ``⌶`` and ``↩`` for that reason.
"""

from __future__ import annotations

from typing import Any

from navkit.glyphs import GLYPHS_NERD, GLYPHS_UNICODE
from navkit.i18n import tr
from navml.widgets.option_strip import OptionItem

from navigator import highlight, icons
from navigator import viewer as viewer_model
from navigator.widgets.editor.commands import (
    ChooseFileType,
    SwitchBlock,
    SwitchBrackets,
    SwitchHiddenChars,
    SwitchHighLight,
    SwitchIndent,
    SwitchInsert,
    SwitchSave,
)
from navigator.widgets.viewer.commands import ChooseEncoding, HexMode, Unwrap

#: Each switch's spelling at the Unicode and the Nerd tier; the word for a
#: plain terminal is the caller's, so the catalogue extraction finds it.
STREAM_BLOCKS = ("↔", icons.OPTION_STREAM_BLOCKS)
COLUMN_BLOCKS = ("↕", icons.OPTION_COLUMN_BLOCKS)
INSERT = ("⌶", icons.OPTION_INSERT)
INDENT = ("⇥", icons.OPTION_INDENT)
WRAP = ("↩", icons.OPTION_WRAP)
BRACKETS = ("()", icons.OPTION_BRACKETS)
HIGHLIGHT = ("§", icons.OPTION_HIGHLIGHT)
HIDDEN = ("¶", icons.OPTION_HIDDEN)


def option_label(word: str, spellings: tuple[str, str], glyphs: int) -> str:
    """*word*, or the symbol *glyphs* -- a ``GLYPHS_*`` tier -- can draw instead."""
    unicode, nerd = spellings
    if glyphs >= GLYPHS_NERD:
        return nerd
    if glyphs >= GLYPHS_UNICODE:
        return unicode
    return word


def _type_label(widget: Any) -> str:
    """The file type in effect, with the file's own icon before it at the Nerd tier."""
    label = highlight.file_type_label(widget.file_type, widget.lexer_name)
    if widget.glyphs >= GLYPHS_NERD and widget.path is not None:
        return f"{icons.icon_for(widget.path.name, False)} {label}"
    return label


def editor_items(editor: Any) -> tuple[OptionItem, ...]:
    """The editor's: Insert/Overwrite, the block's kind, Autoindent, Auto wrap,
    AutoBrackets, Syntax highlight, Hidden characters, and the file type.

    The block's kind is the info line's ``(↔)``/``(↕)`` moved here, lit under
    *Vertical blocks*.  The info line shows it again while the strip is
    switched off."""
    def switch(command: Any, word: Any, spellings: tuple[str, str]) -> OptionItem:
        return OptionItem(command, lambda: option_label(word(), spellings, editor.glyphs))

    def block_label() -> str:
        if editor.vertical_blocks:
            return option_label("|", COLUMN_BLOCKS, editor.glyphs)
        return option_label("-", STREAM_BLOCKS, editor.glyphs)

    return (
        switch(SwitchInsert, lambda: tr("Ovr") if editor.overwrite else tr("Ins"), INSERT),
        OptionItem(SwitchBlock, block_label),
        switch(SwitchIndent, lambda: tr("Indent"), INDENT),
        switch(SwitchSave, lambda: tr("Wrap"), WRAP),
        switch(SwitchBrackets, lambda: tr("Brk"), BRACKETS),
        switch(SwitchHighLight, lambda: tr("Hi"), HIGHLIGHT),
        switch(SwitchHiddenChars, lambda: tr("Show"), HIDDEN),
        OptionItem(ChooseFileType, lambda: _type_label(editor), lit=lambda: False),
    )


def viewer_items(viewer: Any) -> tuple[OptionItem, ...]:
    """The viewer's: the mode, Wrap, Syntax highlight, Hidden characters, the
    encoding and the file type."""
    def switch(command: Any, word: Any, spellings: tuple[str, str]) -> OptionItem:
        return OptionItem(command, lambda: option_label(word(), spellings, viewer.glyphs))

    def mode() -> str:
        return {"hex": tr("Hex"), "dump": tr("Dump")}.get(viewer.mode) or tr("Text")

    def encoding() -> str:
        return dict(viewer_model.ENCODINGS).get(viewer.encoding, viewer.encoding).split()[0]

    return (
        OptionItem(HexMode, mode, lit=lambda: False),
        switch(Unwrap, lambda: tr("Wrap"), WRAP),
        switch(SwitchHighLight, lambda: tr("Hi"), HIGHLIGHT),
        switch(SwitchHiddenChars, lambda: tr("Show"), HIDDEN),
        OptionItem(ChooseEncoding, encoding, lit=lambda: False),
        OptionItem(ChooseFileType, lambda: _type_label(viewer), lit=lambda: False),
    )

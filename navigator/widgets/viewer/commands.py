"""The viewer's commands: what ``FileWindow`` handles."""

from __future__ import annotations

from dataclasses import dataclass

from navkit.commands import Command


# -- the file viewer ---------------------------------------------------------
#
# ``StatusDef hcView``: bound in ``file_window.nml``, captioned as DN captioned
# them there, so the key bar is the viewer's while a viewer has the keyboard.


class Unwrap(Command):
    """F2, ``cmUnWrap``: wrap long lines, or stop."""

    title = "(Un)Wrap"


class HexMode(Command):
    """F4, ``cmHexMode``: text, hex, dump, and round again."""

    #: DN's ``Hex/ASCII/Dump``: its text mode is UTF-8 here, not ASCII.
    title = "Hex/Text/Dump"


@dataclass(frozen=True, slots=True)
class SetViewMode(Command):
    """View > Text, Hex or Dump: one of the modes F4 cycles through, by name.
    A menu entry each, ticked while it is the viewer's mode."""

    mode: str = "text"


class GotoAddress(Command):
    """F5, ``cmGotoCell``: go to a hex address.  Hex and dump only, as in DN."""

    title = "Goto"


class AddFilter(Command):
    """F6, ``cmAddFilter``: no filter, ``{ASCII}``, ``{Printable}``."""

    title = "Filter"


@dataclass(frozen=True, slots=True)
class SetViewFilter(Command):
    """View > No filter, ASCII or Printable: one of the filters F6 cycles
    through, by its index in ``FILTER_TAGS``."""

    filter: int = 0


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


class SaveViewAs(Command):
    """Shift+F5, File > Save as: ``cmSaveAll`` -- the file viewed, written
    under another name, read in its encoding and written in the screen's."""

    title = "Save as"


class ChooseEncoding(Command):
    """Shift+F6, File > Encoding: ``cmLoadXlatTable`` -- the code page the
    file is read in, DN's ``XLT`` table."""

    title = "XLat"


class ShowFields(Command):
    """F2 in the dBase viewer: ``cmShowFields``, the file's structure."""

    title = "Fields"


class ShowMemo(Command):
    """F3 in the dBase viewer: ``cmShowMemo``, the memo at the cursor."""

    title = "View Memo"


class EditDbField(Command):
    """F4 in the dBase viewer: ``cmEditDBField``, the cell at the cursor changed."""

    title = "Edit Field"


class CloseViewer(Command):
    """F3 in a viewer: close it, as Midnight Commander's F3 does.

    Not DOS Navigator's -- its ``hcView`` bound nothing to F3 -- and so bound
    with no caption: the key that opened the viewer closes it again, and the
    status line stays DN's.
    """


__all__ = [
    "Unwrap",
    "HexMode",
    "SetViewMode",
    "GotoAddress",
    "AddFilter",
    "SetViewFilter",
    "SearchFor",
    "ReverseSearch",
    "ContinueSearch",
    "SearchAgain",
    "CloseViewer",
    "SaveViewAs",
    "ChooseEncoding",
    "ShowFields",
    "ShowMemo",
    "EditDbField",
]

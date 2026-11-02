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


class SwitchRendered(Command):
    """Shift+F4, View > *Markup view*: a Markdown, reST, HTML or PDF file rendered --
    headings, lists, tables -- or its source.  A departure: DN's viewer had no
    such reading.  Text mode only."""

    title = "Rendered"


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


class WriteModify(Command):
    """Shift+F2, View > Store: DN's ``cmSave`` in the viewer, which ran
    ``TFileViewer.WriteModify`` -- the bytes typed over in hex written into
    the file."""

    title = "Store"


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


class GotoCell(Command):
    """F6 in the spreadsheet: DN's ``cmGotoCell``, *Go to Cell Number*."""

    title = "Goto"


class FindCell(Command):
    """F7 in the spreadsheet: DN's ``cmFindCell``, *Find*."""

    title = "Search"


class ChangeWidth(Command):
    """Table > Column width: DN's ``cmChangeWidth`` -- Left and Right narrow
    and widen the cursor's column until Enter or Esc."""


class SortColumn(Command):
    """F5 in the spreadsheet: the rows ordered by the cursor's column,
    ascending, descending, then as in the file -- a departure: DN's
    spreadsheet had no sort, F5 was its *Recalc*."""

    title = "Sort"


class TableFormat(Command):
    """Shift+F6 in the spreadsheet: how the file is cut into cells -- its
    delimiter, whether its first row is a header, its encoding (a departure,
    on the viewer's *XLat* key)."""

    title = "Format"


class ViewSheetAsText(Command):
    """Shift+F4 in the spreadsheet: the same file in F3's text view, at the
    cursor's row; Shift+F4 there comes back (a departure, as *Markup view*)."""

    title = "Text"


class ShowCell(Command):
    """Enter in the spreadsheet: the cell at the cursor, whole, in a box --
    a departure: DN's Enter began editing it, and this window edits nothing."""


class CloseViewer(Command):
    """F3 in a viewer: close it, as Midnight Commander's F3 does.

    Not DOS Navigator's -- its ``hcView`` bound nothing to F3 -- and so bound
    with no caption: the key that opened the viewer closes it again, and the
    status line stays DN's.
    """


class NextDifference(Command):
    """N, Alt+Down in a *Compare files* window: the next difference, as
    Midnight Commander's ``mcdiff`` takes it on N and meld on Alt+Down.  Not
    DOS Navigator's, which compared no files line by line."""

    title = "Next"


class PreviousDifference(Command):
    """P, Alt+Up in a *Compare files* window: the previous difference."""

    title = "Prev"


__all__ = [
    "NextDifference",
    "PreviousDifference",
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
    "WriteModify",
    "SaveViewAs",
    "ChooseEncoding",
    "ShowFields",
    "ShowMemo",
    "EditDbField",
    "GotoCell",
    "FindCell",
    "ChangeWidth",
    "SortColumn",
    "TableFormat",
    "ViewSheetAsText",
    "ShowCell",
]

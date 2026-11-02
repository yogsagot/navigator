# navml: generated
"""Generated from ``sheet_window.nml``.

Do not edit: edit the markup and rerun ``python -m navml build``.
"""

from __future__ import annotations

#: Everything the generator needs for itself is underscored, so a document may
#: import any name at all without colliding with it -- there is no reserved
#: word.  A bare ``Label:`` head is what asks for ``_Component``; markup
#: never names it.  See *Importing another component* in navml/DESIGN.md.
from typing import Any as _Any

from navkit.i18n import tr as _tr
from navkit.reactive import bind as _bind

from navml.component import Component as _Component
from navkit.bidi import display_width    # sheet_window.nml:1
from navigator.widgets.viewer.commands import ChangeWidth, CloseViewer, ContinueSearch, FindCell, GotoCell, SearchAgain    # sheet_window.nml:2
from navigator.widgets.viewer.commands import ShowCell, SortColumn, TableFormat, ViewSheetAsText    # sheet_window.nml:3
from navigator.widgets.viewer.sheet_window.sheet_view import SheetView    # sheet_window.nml:4
from navml.commands import CloseWindow    # sheet_window.nml:5
from navml.widgets.dialog.static_text import StaticText    # sheet_window.nml:6
from navml.widgets.menu.menu_item import MenuItem    # sheet_window.nml:7
from navml.widgets.menu.menu_line import MenuLine    # sheet_window.nml:8
from navml.widgets.menu.sub_menu import SubMenu    # sheet_window.nml:9
from navml.widgets.window import Window    # sheet_window.nml:10

__navml_component__ = "SheetWindow"

__all__ = ["SheetWindow"]


class SheetWindow(Window, _Component):
    """F3 on a CSV or TSV file, and File > View > As Spreadsheet: DOS Navigator's

    ``TCalcWindow`` (CALC.PAS), which F3 opened on a ``.WKZ`` -- here view-only,
    on a delimited text file (``navigator.lib.viewer.table``).

    DN's window held a cell-name box, ``TCalcInfo``'s line and its own menu
    bar over ``TCalcView``; ``SheetView`` paints the first two itself, and the
    menu joins the main bar as *Table* while the window is active, as the
    viewer's *View* does.  ``record/records`` over the bottom frame, as the
    dBase viewer's ``TDBIndicator``, says how far the walk of a big file has
    got.  It opens zoomed, as the viewers do.  Its colours are DN's: the
    Editor/Spreadsheet group a ``TUniWindow`` takes.
    """

    #: The document this class was generated from.
    __navml_source__ = "sheet_window.nml"

    #: ``StatusDef hcSpreadSheet``'s keys that a view-only window keeps --
    #: F6 *Goto*, F7 *Search* -- and the viewer's: Esc and F3 close, Shift+F7
    #: and Ctrl+L search again.  F5 (DN's *Recalc*) sorts, Shift+F4 is the
    #: text, Shift+F6 (the viewer's *XLat*) the format: departures.
    keys = {    # sheet_window.nml:30
        'escape': CloseWindow,    # sheet_window.nml:31
        'f3': CloseViewer,    # sheet_window.nml:32
        'enter': ShowCell,    # sheet_window.nml:33
        'f5': SortColumn,    # sheet_window.nml:34
        'f6': GotoCell,    # sheet_window.nml:35
        'f7': FindCell,    # sheet_window.nml:36
        'shift+f7': ContinueSearch,    # sheet_window.nml:37
        'ctrl+l': SearchAgain,    # sheet_window.nml:38
        'shift+f4': ViewSheetAsText,    # sheet_window.nml:39
        'shift+f6': TableFormat,    # sheet_window.nml:40
    }

    #: Ids, annotated so the hand-written half completes them.
    sheet: SheetView    # sheet_window.nml:43
    indicator: StaticText    # sheet_window.nml:50
    table_menu: SubMenu    # sheet_window.nml:61

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.sheet = SheetView(parent=self)    # sheet_window.nml:42
        self.indicator = StaticText(parent=self)    # sheet_window.nml:49
        self.table_menu = SubMenu(parent=self)    # sheet_window.nml:60
        _w1 = MenuItem(parent=self.table_menu)    # sheet_window.nml:65
        _w2 = MenuItem(parent=self.table_menu)    # sheet_window.nml:69
        _w3 = MenuItem(parent=self.table_menu)    # sheet_window.nml:73
        _w4 = MenuItem(parent=self.table_menu)    # sheet_window.nml:77
        _w5 = MenuLine(parent=self.table_menu)    # sheet_window.nml:81
        _w6 = MenuItem(parent=self.table_menu)    # sheet_window.nml:82
        _w7 = MenuItem(parent=self.table_menu)    # sheet_window.nml:85
        _w8 = MenuItem(parent=self.table_menu)    # sheet_window.nml:88
        _w9 = MenuLine(parent=self.table_menu)    # sheet_window.nml:91
        _w10 = MenuItem(parent=self.table_menu)    # sheet_window.nml:92
        _w11 = MenuItem(parent=self.table_menu)    # sheet_window.nml:96

        self.zoomed = True    # sheet_window.nml:24

        self.sheet.x = 1    # sheet_window.nml:44
        self.sheet.y = 1    # sheet_window.nml:45
        self.sheet.width = _bind(lambda _o: max(0, _o.parent.width - 2))    # sheet_window.nml:46
        self.sheet.height = _bind(lambda _o: max(0, _o.parent.height - 2))    # sheet_window.nml:47

        self.indicator.name = 'indicator'    # sheet_window.nml:52
        self.indicator.x = 10    # sheet_window.nml:53
        self.indicator.y = _bind(lambda _o: max(0, _o.parent.height - 1))    # sheet_window.nml:54
        self.indicator.width = _bind(    # sheet_window.nml:55
            lambda _o: min(display_width(_o.text), max(0, _o.parent.width - 12))
        )
        self.indicator.height = 1    # sheet_window.nml:56

        self.table_menu.text = _bind(lambda _o: _tr('~T~able'), yielding=True)    # sheet_window.nml:62
        self.table_menu.tooltip = _bind(    # sheet_window.nml:63
            lambda _o: _tr('Cells, columns, sorting and search'),
            yielding=True,
        )
        self.table_menu.after = 'File'    # sheet_window.nml:64

        _w1.text = _bind(lambda _o: _tr('~V~iew cell...'), yielding=True)    # sheet_window.nml:66
        _w1.tooltip = _bind(    # sheet_window.nml:67
            lambda _o: _tr('The whole text of the cell at the cursor'),
            yielding=True,
        )
        _w1.command = ShowCell    # sheet_window.nml:68

        _w2.text = _bind(lambda _o: _tr('C~o~lumn width...'), yielding=True)    # sheet_window.nml:70
        _w2.tooltip = _bind(    # sheet_window.nml:71
            lambda _o: _tr('Left and Right narrow and widen the column; Enter ends'),
            yielding=True,
        )
        _w2.command = ChangeWidth    # sheet_window.nml:72

        _w3.text = _bind(lambda _o: _tr('~S~ort by column'), yielding=True)    # sheet_window.nml:74
        _w3.tooltip = _bind(    # sheet_window.nml:75
            lambda _o: _tr('Ascending, descending, then as in the file'),
            yielding=True,
        )
        _w3.command = SortColumn    # sheet_window.nml:76

        _w4.text = _bind(lambda _o: _tr('Fo~r~mat...'), yielding=True)    # sheet_window.nml:78
        _w4.tooltip = _bind(    # sheet_window.nml:79
            lambda _o: _tr('The delimiter, the header and the encoding'),
            yielding=True,
        )
        _w4.command = TableFormat    # sheet_window.nml:80

        _w6.text = _bind(lambda _o: _tr('~F~ind...'), yielding=True)    # sheet_window.nml:83
        _w6.command = FindCell    # sheet_window.nml:84

        _w7.text = _bind(lambda _o: _tr('Search a~g~ain'), yielding=True)    # sheet_window.nml:86
        _w7.command = ContinueSearch    # sheet_window.nml:87

        _w8.text = _bind(    # sheet_window.nml:89
            lambda _o: _tr('Go to cell ~n~umber...'),
            yielding=True,
        )
        _w8.command = GotoCell    # sheet_window.nml:90

        _w10.text = _bind(lambda _o: _tr('As ~t~ext'), yielding=True)    # sheet_window.nml:93
        _w10.tooltip = _bind(    # sheet_window.nml:94
            lambda _o: _tr('The same file in the text viewer'),
            yielding=True,
        )
        _w10.command = ViewSheetAsText    # sheet_window.nml:95

        _w11.text = _bind(lambda _o: _tr('~C~lose'), yielding=True)    # sheet_window.nml:97
        _w11.command = CloseWindow    # sheet_window.nml:98

# navml: generated
"""Generated from ``db_window.nml``.

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
from navkit.bidi import display_width    # db_window.nml:1
from navigator.widgets.viewer.commands import ChangeWidth, ChooseTable, ContinueSearch, EditDbField, RunQuery, SearchAgain, SearchFor    # db_window.nml:2
from navigator.widgets.viewer.commands import ShowFields, ShowMemo, SortColumn, TableFormat, ViewSheetAsText    # db_window.nml:3
from navigator.widgets.viewer.db_window.db_viewer import DBViewer    # db_window.nml:4
from navigator.widgets.manager.commands import EditNamed    # db_window.nml:5
from navml.commands import CloseWindow    # db_window.nml:6
from navml.widgets.dialog.static_text import StaticText    # db_window.nml:7
from navml.widgets.menu.menu_item import MenuItem    # db_window.nml:8
from navml.widgets.menu.menu_line import MenuLine    # db_window.nml:9
from navml.widgets.menu.sub_menu import SubMenu    # db_window.nml:10
from navml.widgets.window import Window    # db_window.nml:11

__navml_component__ = "DBWindow"

__all__ = ["DBWindow"]


class DBWindow(Window, _Component):
    """File > View > As DataBase, and F3 on a ``.dbf``: DOS Navigator's

    ``TDBWindow`` (DBVIEW.PAS), titled *dBase View* and the file.

    The records filling the inside of the frame, ``TDBIndicator``'s
    ``record/records`` over the bottom frame ten columns in.  It opens
    zoomed, as the file viewer does; DN filled the desktop with it too.  Its
    keys are ``StatusDef hcDBView``'s.

    A SQLite file opens here too, a table at a time and read-only (a
    departure): F5 *Tables* and F6 *Query* are for it alone, F4 is refused.
    So does a CSV or TSV file, read-only, where DN's ``.WKZ`` had a
    spreadsheet window of its own: Shift+F6 *Format* and Shift+F3 its text are
    for it alone.  F8 sorts any of them, and *Column width* -- the
    spreadsheet's ``cmChangeWidth`` -- and Ctrl+Left/Right resize a field.
    """

    #: The document this class was generated from.
    __navml_source__ = "db_window.nml"

    #: The keys this component binds, read through key_table().
    keys = {    # db_window.nml:30
        'escape': CloseWindow,    # db_window.nml:31
        'f2': ShowFields,    # db_window.nml:32
        'f3': ShowMemo,    # db_window.nml:33
        'f4': EditDbField,    # db_window.nml:34
        'f5': ChooseTable,    # db_window.nml:35
        'f6': RunQuery,    # db_window.nml:36
        'f8': SortColumn,    # db_window.nml:37
        'shift+f3': ViewSheetAsText,    # db_window.nml:41
        'shift+f4': EditNamed,    # db_window.nml:42
        'shift+f6': TableFormat,    # db_window.nml:43
        'f7': SearchFor,    # db_window.nml:44
        'shift+f7': ContinueSearch,    # db_window.nml:45
        'ctrl+l': SearchAgain,    # db_window.nml:46
    }

    #: Ids, annotated so the hand-written half completes them.
    viewer: DBViewer    # db_window.nml:49
    indicator: StaticText    # db_window.nml:56
    view_menu: SubMenu    # db_window.nml:69

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.viewer = DBViewer(parent=self)    # db_window.nml:48
        self.indicator = StaticText(parent=self)    # db_window.nml:55
        self.view_menu = SubMenu(parent=self)    # db_window.nml:68
        _w1 = MenuItem(parent=self.view_menu)    # db_window.nml:73
        _w2 = MenuItem(parent=self.view_menu)    # db_window.nml:77
        _w3 = MenuItem(parent=self.view_menu)    # db_window.nml:81
        _w4 = MenuItem(parent=self.view_menu)    # db_window.nml:85
        _w5 = MenuItem(parent=self.view_menu)    # db_window.nml:89
        _w6 = MenuLine(parent=self.view_menu)    # db_window.nml:93
        _w7 = MenuItem(parent=self.view_menu)    # db_window.nml:94
        _w8 = MenuItem(parent=self.view_menu)    # db_window.nml:98
        _w9 = MenuItem(parent=self.view_menu)    # db_window.nml:103
        _w10 = MenuItem(parent=self.view_menu)    # db_window.nml:107
        _w11 = MenuLine(parent=self.view_menu)    # db_window.nml:111
        _w12 = MenuItem(parent=self.view_menu)    # db_window.nml:112
        _w13 = MenuItem(parent=self.view_menu)    # db_window.nml:115
        _w14 = MenuLine(parent=self.view_menu)    # db_window.nml:118
        _w15 = MenuItem(parent=self.view_menu)    # db_window.nml:119

        self.zoomed = True    # db_window.nml:28

        self.viewer.x = 1    # db_window.nml:50
        self.viewer.y = 1    # db_window.nml:51
        self.viewer.width = _bind(lambda _o: max(0, _o.parent.width - 2))    # db_window.nml:52
        self.viewer.height = _bind(lambda _o: max(0, _o.parent.height - 2))    # db_window.nml:53

        self.indicator.name = 'indicator'    # db_window.nml:58
        self.indicator.x = 10    # db_window.nml:59
        self.indicator.y = _bind(lambda _o: max(0, _o.parent.height - 1))    # db_window.nml:60
        self.indicator.width = _bind(    # db_window.nml:61
            lambda _o: min(display_width(_o.text), max(0, _o.parent.width - 12))
        )
        self.indicator.height = 1    # db_window.nml:62

        self.view_menu.text = _bind(lambda _o: _tr('~V~iew'), yielding=True)    # db_window.nml:70
        self.view_menu.tooltip = _bind(    # db_window.nml:71
            lambda _o: _tr('Fields, memos, editing, tables and search'),
            yielding=True,
        )
        self.view_menu.after = 'File'    # db_window.nml:72

        _w1.text = _bind(lambda _o: _tr('~F~ields...'), yielding=True)    # db_window.nml:74
        _w1.tooltip = _bind(    # db_window.nml:75
            lambda _o: _tr("The file's structure: its fields and their types"),
            yielding=True,
        )
        _w1.command = ShowFields    # db_window.nml:76

        _w2.text = _bind(lambda _o: _tr('~M~emo view'), yielding=True)    # db_window.nml:78
        _w2.tooltip = _bind(    # db_window.nml:79
            lambda _o: _tr('The memo text of the cell at the cursor'),
            yielding=True,
        )
        _w2.command = ShowMemo    # db_window.nml:80

        _w3.text = _bind(lambda _o: _tr('~E~dit field...'), yielding=True)    # db_window.nml:82
        _w3.command = EditDbField    # db_window.nml:83

        _w4.text = _bind(lambda _o: _tr('~T~ables...'), yielding=True)    # db_window.nml:86
        _w4.tooltip = _bind(    # db_window.nml:87
            lambda _o: _tr('Another table or view of the SQLite file'),
            yielding=True,
        )
        _w4.command = ChooseTable    # db_window.nml:88

        _w5.text = _bind(lambda _o: _tr('~Q~uery...'), yielding=True)    # db_window.nml:90
        _w5.tooltip = _bind(    # db_window.nml:91
            lambda _o: _tr('Run a query that reads, and show its rows'),
            yielding=True,
        )
        _w5.command = RunQuery    # db_window.nml:92

        _w7.text = _bind(lambda _o: _tr('S~o~rt by column'), yielding=True)    # db_window.nml:95
        _w7.tooltip = _bind(    # db_window.nml:96
            lambda _o: _tr('Ascending, descending, then as in the file'),
            yielding=True,
        )
        _w7.command = SortColumn    # db_window.nml:97

        _w8.text = _bind(lambda _o: _tr('Column ~w~idth...'), yielding=True)    # db_window.nml:99
        _w8.tooltip = _bind(    # db_window.nml:100
            lambda _o: _tr('Left and Right narrow and widen the column; Enter ends'),
            yielding=True,
        )
        _w8.command = ChangeWidth    # db_window.nml:101

        _w9.text = _bind(lambda _o: _tr('Fo~r~mat...'), yielding=True)    # db_window.nml:104
        _w9.tooltip = _bind(    # db_window.nml:105
            lambda _o: _tr('The delimiter, the header and the encoding'),
            yielding=True,
        )
        _w9.command = TableFormat    # db_window.nml:106

        _w10.text = _bind(lambda _o: _tr('As te~x~t'), yielding=True)    # db_window.nml:108
        _w10.tooltip = _bind(    # db_window.nml:109
            lambda _o: _tr('The same file in the text viewer'),
            yielding=True,
        )
        _w10.command = ViewSheetAsText    # db_window.nml:110

        _w12.text = _bind(lambda _o: _tr('~S~earch...'), yielding=True)    # db_window.nml:113
        _w12.command = SearchFor    # db_window.nml:114

        _w13.text = _bind(lambda _o: _tr('Search a~g~ain'), yielding=True)    # db_window.nml:116
        _w13.command = ContinueSearch    # db_window.nml:117

        _w15.text = _bind(lambda _o: _tr('~C~lose'), yielding=True)    # db_window.nml:120
        _w15.command = CloseWindow    # db_window.nml:121

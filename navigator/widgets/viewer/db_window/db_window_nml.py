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
from navigator.widgets.viewer.commands import ContinueSearch, EditDbField, SearchAgain, SearchFor, ShowFields, ShowMemo    # db_window.nml:1
from navigator.widgets.viewer.db_window.db_viewer import DBViewer    # db_window.nml:2
from navml.commands import CloseWindow    # db_window.nml:3
from navml.widgets.dialog.static_text import StaticText    # db_window.nml:4
from navml.widgets.menu.menu_item import MenuItem    # db_window.nml:5
from navml.widgets.menu.menu_line import MenuLine    # db_window.nml:6
from navml.widgets.menu.sub_menu import SubMenu    # db_window.nml:7
from navml.widgets.window import Window    # db_window.nml:8

__navml_component__ = "DBWindow"

__all__ = ["DBWindow"]


class DBWindow(Window, _Component):
    """File > View > As DataBase, and F3 on a ``.dbf``: DOS Navigator's

    ``TDBWindow`` (DBVIEW.PAS), titled *dBase View* and the file.

    The records filling the inside of the frame, ``TDBIndicator``'s
    ``record/records`` over the bottom frame ten columns in.  It opens
    zoomed, as the file viewer does; DN filled the desktop with it too.  Its
    keys are ``StatusDef hcDBView``'s.
    """

    #: The document this class was generated from.
    __navml_source__ = "db_window.nml"

    #: The keys this component binds, read through key_table().
    keys = {    # db_window.nml:20
        'escape': CloseWindow,    # db_window.nml:21
        'f2': ShowFields,    # db_window.nml:22
        'f3': ShowMemo,    # db_window.nml:23
        'f4': EditDbField,    # db_window.nml:24
        'f7': SearchFor,    # db_window.nml:25
        'shift+f7': ContinueSearch,    # db_window.nml:26
        'ctrl+l': SearchAgain,    # db_window.nml:27
    }

    #: Ids, annotated so the hand-written half completes them.
    viewer: DBViewer    # db_window.nml:30
    indicator: StaticText    # db_window.nml:37
    view_menu: SubMenu    # db_window.nml:50

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.viewer = DBViewer(parent=self)    # db_window.nml:29
        self.indicator = StaticText(parent=self)    # db_window.nml:36
        self.view_menu = SubMenu(parent=self)    # db_window.nml:49
        _w1 = MenuItem(parent=self.view_menu)    # db_window.nml:54
        _w2 = MenuItem(parent=self.view_menu)    # db_window.nml:58
        _w3 = MenuItem(parent=self.view_menu)    # db_window.nml:62
        _w4 = MenuLine(parent=self.view_menu)    # db_window.nml:65
        _w5 = MenuItem(parent=self.view_menu)    # db_window.nml:66
        _w6 = MenuItem(parent=self.view_menu)    # db_window.nml:69
        _w7 = MenuLine(parent=self.view_menu)    # db_window.nml:72
        _w8 = MenuItem(parent=self.view_menu)    # db_window.nml:73

        self.zoomed = True    # db_window.nml:18

        self.viewer.x = 1    # db_window.nml:31
        self.viewer.y = 1    # db_window.nml:32
        self.viewer.width = _bind(lambda _o: max(0, _o.parent.width - 2))    # db_window.nml:33
        self.viewer.height = _bind(lambda _o: max(0, _o.parent.height - 2))    # db_window.nml:34

        self.indicator.name = 'indicator'    # db_window.nml:39
        self.indicator.x = 10    # db_window.nml:40
        self.indicator.y = _bind(lambda _o: max(0, _o.parent.height - 1))    # db_window.nml:41
        self.indicator.width = _bind(    # db_window.nml:42
            lambda _o: min(len(_o.text), max(0, _o.parent.width - 12))
        )
        self.indicator.height = 1    # db_window.nml:43

        self.view_menu.text = _bind(lambda _o: _tr('~V~iew'), yielding=True)    # db_window.nml:51
        self.view_menu.tooltip = _bind(    # db_window.nml:52
            lambda _o: _tr('Fields, memos, editing and search'),
            yielding=True,
        )
        self.view_menu.after = 'File'    # db_window.nml:53

        _w1.text = _bind(lambda _o: _tr('~F~ields...'), yielding=True)    # db_window.nml:55
        _w1.tooltip = _bind(    # db_window.nml:56
            lambda _o: _tr("The file's structure: its fields and their types"),
            yielding=True,
        )
        _w1.command = ShowFields    # db_window.nml:57

        _w2.text = _bind(lambda _o: _tr('~M~emo view'), yielding=True)    # db_window.nml:59
        _w2.tooltip = _bind(    # db_window.nml:60
            lambda _o: _tr('The memo text of the cell at the cursor'),
            yielding=True,
        )
        _w2.command = ShowMemo    # db_window.nml:61

        _w3.text = _bind(lambda _o: _tr('~E~dit field...'), yielding=True)    # db_window.nml:63
        _w3.command = EditDbField    # db_window.nml:64

        _w5.text = _bind(lambda _o: _tr('~S~earch...'), yielding=True)    # db_window.nml:67
        _w5.command = SearchFor    # db_window.nml:68

        _w6.text = _bind(lambda _o: _tr('Search a~g~ain'), yielding=True)    # db_window.nml:70
        _w6.command = ContinueSearch    # db_window.nml:71

        _w8.text = _bind(lambda _o: _tr('~C~lose'), yielding=True)    # db_window.nml:74
        _w8.command = CloseWindow    # db_window.nml:75

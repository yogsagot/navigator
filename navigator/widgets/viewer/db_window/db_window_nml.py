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

from navkit.reactive import bind as _bind

from navml.component import Component as _Component
from navigator.widgets.viewer.commands import ContinueSearch, EditDbField, SearchAgain, SearchFor, ShowFields, ShowMemo    # db_window.nml:1
from navigator.widgets.viewer.db_window.db_viewer import DBViewer    # db_window.nml:2
from navml.commands import CloseWindow    # db_window.nml:3
from navml.widgets.dialog.static_text import StaticText    # db_window.nml:4
from navml.widgets.window import Window    # db_window.nml:5

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
    keys = {    # db_window.nml:17
        'escape': CloseWindow,    # db_window.nml:18
        'f2': ShowFields,    # db_window.nml:19
        'f3': ShowMemo,    # db_window.nml:20
        'f4': EditDbField,    # db_window.nml:21
        'f7': SearchFor,    # db_window.nml:22
        'shift+f7': ContinueSearch,    # db_window.nml:23
        'ctrl+l': SearchAgain,    # db_window.nml:24
    }

    #: Ids, annotated so the hand-written half completes them.
    viewer: DBViewer    # db_window.nml:27
    indicator: StaticText    # db_window.nml:34

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.viewer = DBViewer(parent=self)    # db_window.nml:26
        self.indicator = StaticText(parent=self)    # db_window.nml:33

        self.zoomed = True    # db_window.nml:15

        self.viewer.x = 1    # db_window.nml:28
        self.viewer.y = 1    # db_window.nml:29
        self.viewer.width = _bind(lambda _o: max(0, _o.parent.width - 2))    # db_window.nml:30
        self.viewer.height = _bind(lambda _o: max(0, _o.parent.height - 2))    # db_window.nml:31

        self.indicator.x = 10    # db_window.nml:35
        self.indicator.y = _bind(lambda _o: max(0, _o.parent.height - 1))    # db_window.nml:36
        self.indicator.width = _bind(    # db_window.nml:37
            lambda _o: min(len(_o.text), max(0, _o.parent.width - 12))
        )
        self.indicator.height = 1    # db_window.nml:38

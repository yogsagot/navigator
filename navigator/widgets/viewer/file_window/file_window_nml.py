# navml: generated
"""Generated from ``file_window.nml``.

Do not edit: edit the markup and rerun ``python -m navml build``.
"""

from __future__ import annotations

#: Everything the generator needs for itself is underscored, so a document may
#: import any name at all without colliding with it -- there is no reserved
#: word.  A bare ``Label:`` head is what asks for ``_Component``; markup
#: never names it.  See *Importing another component* in navml/DESIGN.md.
from typing import Any as _Any

from navkit.events import Event as _Event
from navkit.reactive import bind as _bind

from navml.component import Component as _Component
from navigator.widgets.viewer.commands import AddFilter, CloseViewer, ContinueSearch, GotoAddress, HexMode    # file_window.nml:1
from navigator.widgets.viewer.commands import ReverseSearch, SearchAgain, SearchFor, SetViewFilter, SetViewMode, Unwrap    # file_window.nml:2
from navigator.widgets.viewer.file_viewer import FileViewer    # file_window.nml:3
from navml.commands import CloseWindow    # file_window.nml:4
from navml.widgets.dialog.scroll_bar import ScrollBar    # file_window.nml:5
from navml.widgets.dialog.static_text import StaticText    # file_window.nml:6
from navml.widgets.menu.menu_item import MenuItem    # file_window.nml:7
from navml.widgets.menu.menu_line import MenuLine    # file_window.nml:8
from navml.widgets.menu.sub_menu import SubMenu    # file_window.nml:9
from navml.widgets.window import Window    # file_window.nml:10

__navml_component__ = "FileWindow"

__all__ = ["FileWindow"]


class FileWindow(Window, _Component):
    """F3: DOS Navigator's ``TFileWindow`` (``FVIEWER.PAS``).

    A standard window titled with the file's path, the viewer filling the
    inside of its frame, ``TViewScroll`` on the right frame column and
    ``TViewInfo`` over the bottom one -- the three views ``TFileWindow.Init``
    inserts, in the places it puts them.

    **It opens zoomed**, where DN reused the last viewer's rectangle
    (``LastViewerBounds``) and filled the desktop only the first time.  Taken
    to match the file manager, which opens zoomed too; the zoom icon gives the
    window its own rectangle back.
    """

    #: The document this class was generated from.
    __navml_source__ = "file_window.nml"

    #: ``StatusDef hcView``, in its order: the plain row, then Ctrl's and
    #: Shift's.  What DN bound there and Navigator cannot do yet -- Shift+F2
    #: Store, Shift+F5 Save as, Shift+F6 XLat -- is left out, so the bar closes
    #: up round it.  Ctrl+L continues a search with no caption, as it did.
    #: F3 closes the viewer, as Midnight Commander's does -- not DN's, which
    #: bound nothing there -- and has no caption either, so the line is DN's.
    keys = {    # file_window.nml:32
        'escape': CloseWindow,    # file_window.nml:33
        'f3': CloseViewer,    # file_window.nml:34
        'f2': Unwrap,    # file_window.nml:35
        'f4': HexMode,    # file_window.nml:36
        'f5': GotoAddress,    # file_window.nml:37
        'f6': AddFilter,    # file_window.nml:38
        'f7': SearchFor,    # file_window.nml:39
        'ctrl+f7': ReverseSearch,    # file_window.nml:40
        'shift+f7': ContinueSearch,    # file_window.nml:41
        'ctrl+l': SearchAgain,    # file_window.nml:42
    }

    #: Ids, annotated so the hand-written half completes them.
    viewer: FileViewer    # file_window.nml:45
    bar: ScrollBar    # file_window.nml:55
    info: StaticText    # file_window.nml:66
    view_menu: SubMenu    # file_window.nml:83

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_bar_scroll(self, event: _Event) -> bool:    # file_window.nml:55
        """``bar`` raised an event whose handler is ``on_scroll``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.viewer = FileViewer(parent=self)    # file_window.nml:44
        self.bar = ScrollBar(parent=self)    # file_window.nml:54
        self.info = StaticText(parent=self)    # file_window.nml:65
        self.view_menu = SubMenu(parent=self)    # file_window.nml:82
        _w1 = MenuItem(parent=self.view_menu)    # file_window.nml:86
        _w2 = MenuItem(parent=self.view_menu)    # file_window.nml:89
        _w3 = MenuItem(parent=self.view_menu)    # file_window.nml:92
        _w4 = MenuLine(parent=self.view_menu)    # file_window.nml:95
        _w5 = MenuItem(parent=self.view_menu)    # file_window.nml:96
        _w6 = MenuItem(parent=self.view_menu)    # file_window.nml:99
        _w7 = MenuItem(parent=self.view_menu)    # file_window.nml:102
        _w8 = MenuItem(parent=self.view_menu)    # file_window.nml:105
        _w9 = MenuLine(parent=self.view_menu)    # file_window.nml:108
        _w10 = MenuItem(parent=self.view_menu)    # file_window.nml:109
        _w11 = MenuItem(parent=self.view_menu)    # file_window.nml:112
        _w12 = MenuItem(parent=self.view_menu)    # file_window.nml:115
        _w13 = MenuItem(parent=self.view_menu)    # file_window.nml:118
        _w14 = MenuLine(parent=self.view_menu)    # file_window.nml:121
        _w15 = MenuItem(parent=self.view_menu)    # file_window.nml:122
        _w16 = MenuItem(parent=self.view_menu)    # file_window.nml:125
        _w17 = MenuItem(parent=self.view_menu)    # file_window.nml:128
        _w18 = MenuLine(parent=self.view_menu)    # file_window.nml:131
        _w19 = MenuItem(parent=self.view_menu)    # file_window.nml:132

        self.zoomed = True    # file_window.nml:24

        self.viewer.x = 1    # file_window.nml:46
        self.viewer.y = 1    # file_window.nml:47
        self.viewer.width = _bind(lambda _o: max(0, _o.parent.width - 2))    # file_window.nml:48
        self.viewer.height = _bind(lambda _o: max(0, _o.parent.height - 2))    # file_window.nml:49

        self.bar.x = _bind(lambda _o: _o.parent.width - 1)    # file_window.nml:56
        self.bar.y = 1    # file_window.nml:57
        self.bar.width = 1    # file_window.nml:58
        self.bar.height = _bind(lambda _o: max(0, _o.parent.height - 2))    # file_window.nml:59
        self.bar.value = _bind(lambda _o: self.viewer.top)    # file_window.nml:60
        self.bar.maximum = _bind(lambda _o: self.viewer.size)    # file_window.nml:61
        self.bar.page = _bind(    # file_window.nml:62
            lambda _o: max(1, self.viewer.width * self.viewer.height)
        )
        self.bar.on_scroll = self.on_bar_scroll    # file_window.nml:55

        self.info.x = 1    # file_window.nml:67
        self.info.y = _bind(lambda _o: max(0, _o.parent.height - 1))    # file_window.nml:68
        self.info.width = _bind(    # file_window.nml:69
            lambda _o: min(len(self.viewer.info_text), max(0, _o.parent.width - 3))
        )
        self.info.height = 1    # file_window.nml:70
        self.info.text = _bind(lambda _o: self.viewer.info_text)    # file_window.nml:71

        self.view_menu.text = '~V~iew'    # file_window.nml:84
        self.view_menu.after = 'File'    # file_window.nml:85

        _w1.text = '~T~ext'    # file_window.nml:87
        _w1.command = SetViewMode('text')    # file_window.nml:88

        _w2.text = '~H~ex'    # file_window.nml:90
        _w2.command = SetViewMode('hex')    # file_window.nml:91

        _w3.text = '~D~ump'    # file_window.nml:93
        _w3.command = SetViewMode('dump')    # file_window.nml:94

        _w5.text = '~W~rap lines'    # file_window.nml:97
        _w5.command = Unwrap    # file_window.nml:98

        _w6.text = '~N~o filter'    # file_window.nml:100
        _w6.command = SetViewFilter(0)    # file_window.nml:101

        _w7.text = '~A~SCII filter'    # file_window.nml:103
        _w7.command = SetViewFilter(1)    # file_window.nml:104

        _w8.text = '~P~rintable filter'    # file_window.nml:106
        _w8.command = SetViewFilter(2)    # file_window.nml:107

        _w10.text = '~S~earch...'    # file_window.nml:110
        _w10.command = SearchFor    # file_window.nml:111

        _w11.text = 'Search a~g~ain'    # file_window.nml:113
        _w11.command = ContinueSearch    # file_window.nml:114

        _w12.text = 'Re~v~erse search'    # file_window.nml:116
        _w12.command = ReverseSearch    # file_window.nml:117

        _w13.text = 'Go to add~r~ess...'    # file_window.nml:119
        _w13.command = GotoAddress    # file_window.nml:120

        _w15.text = 'St~o~re'    # file_window.nml:123
        _w15.key = 'Shift-F2'    # file_window.nml:124

        _w16.text = 'Sav~e~ as...'    # file_window.nml:126
        _w16.key = 'Shift-F5'    # file_window.nml:127

        _w17.text = 'Encod~i~ng...'    # file_window.nml:129
        _w17.key = 'Shift-F6'    # file_window.nml:130

        _w19.text = '~C~lose'    # file_window.nml:133
        _w19.command = CloseWindow    # file_window.nml:134

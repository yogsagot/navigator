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
from navigator.widgets.viewer.commands import AddFilter, ChooseEncoding, CloseViewer, ContinueSearch, GotoAddress, HexMode, SaveViewAs    # file_window.nml:1
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
    #: Shift's.  Shift+F2's *Store* is left out, there being no hex editing
    #: to store, so the bar closes up round it; Shift+F6's *XLat* chooses an
    #: encoding.  Ctrl+L continues a search with no caption, as it did.
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
        'shift+f5': SaveViewAs,    # file_window.nml:41
        'shift+f6': ChooseEncoding,    # file_window.nml:42
        'shift+f7': ContinueSearch,    # file_window.nml:43
        'ctrl+l': SearchAgain,    # file_window.nml:44
    }

    #: Ids, annotated so the hand-written half completes them.
    viewer: FileViewer    # file_window.nml:47
    bar: ScrollBar    # file_window.nml:57
    info: StaticText    # file_window.nml:68
    view_menu: SubMenu    # file_window.nml:85

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_bar_scroll(self, event: _Event) -> bool:    # file_window.nml:57
        """``bar`` raised an event whose handler is ``on_scroll``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.viewer = FileViewer(parent=self)    # file_window.nml:46
        self.bar = ScrollBar(parent=self)    # file_window.nml:56
        self.info = StaticText(parent=self)    # file_window.nml:67
        self.view_menu = SubMenu(parent=self)    # file_window.nml:84
        _w1 = MenuItem(parent=self.view_menu)    # file_window.nml:88
        _w2 = MenuItem(parent=self.view_menu)    # file_window.nml:91
        _w3 = MenuItem(parent=self.view_menu)    # file_window.nml:94
        _w4 = MenuLine(parent=self.view_menu)    # file_window.nml:97
        _w5 = MenuItem(parent=self.view_menu)    # file_window.nml:98
        _w6 = MenuItem(parent=self.view_menu)    # file_window.nml:101
        _w7 = MenuItem(parent=self.view_menu)    # file_window.nml:104
        _w8 = MenuItem(parent=self.view_menu)    # file_window.nml:107
        _w9 = MenuLine(parent=self.view_menu)    # file_window.nml:110
        _w10 = MenuItem(parent=self.view_menu)    # file_window.nml:111
        _w11 = MenuItem(parent=self.view_menu)    # file_window.nml:114
        _w12 = MenuItem(parent=self.view_menu)    # file_window.nml:117
        _w13 = MenuItem(parent=self.view_menu)    # file_window.nml:120
        _w14 = MenuLine(parent=self.view_menu)    # file_window.nml:123
        _w15 = MenuItem(parent=self.view_menu)    # file_window.nml:124
        _w16 = MenuItem(parent=self.view_menu)    # file_window.nml:127
        _w17 = MenuItem(parent=self.view_menu)    # file_window.nml:131
        _w18 = MenuLine(parent=self.view_menu)    # file_window.nml:135
        _w19 = MenuItem(parent=self.view_menu)    # file_window.nml:136

        self.zoomed = True    # file_window.nml:24

        self.viewer.x = 1    # file_window.nml:48
        self.viewer.y = 1    # file_window.nml:49
        self.viewer.width = _bind(lambda _o: max(0, _o.parent.width - 2))    # file_window.nml:50
        self.viewer.height = _bind(lambda _o: max(0, _o.parent.height - 2))    # file_window.nml:51

        self.bar.x = _bind(lambda _o: _o.parent.width - 1)    # file_window.nml:58
        self.bar.y = 1    # file_window.nml:59
        self.bar.width = 1    # file_window.nml:60
        self.bar.height = _bind(lambda _o: max(0, _o.parent.height - 2))    # file_window.nml:61
        self.bar.value = _bind(lambda _o: self.viewer.top)    # file_window.nml:62
        self.bar.maximum = _bind(lambda _o: self.viewer.size)    # file_window.nml:63
        self.bar.page = _bind(    # file_window.nml:64
            lambda _o: max(1, self.viewer.width * self.viewer.height)
        )
        self.bar.on_scroll = self.on_bar_scroll    # file_window.nml:57

        self.info.x = 1    # file_window.nml:69
        self.info.y = _bind(lambda _o: max(0, _o.parent.height - 1))    # file_window.nml:70
        self.info.width = _bind(    # file_window.nml:71
            lambda _o: min(len(self.viewer.info_text), max(0, _o.parent.width - 3))
        )
        self.info.height = 1    # file_window.nml:72
        self.info.text = _bind(lambda _o: self.viewer.info_text)    # file_window.nml:73

        self.view_menu.text = '~V~iew'    # file_window.nml:86
        self.view_menu.after = 'File'    # file_window.nml:87

        _w1.text = '~T~ext'    # file_window.nml:89
        _w1.command = SetViewMode('text')    # file_window.nml:90

        _w2.text = '~H~ex'    # file_window.nml:92
        _w2.command = SetViewMode('hex')    # file_window.nml:93

        _w3.text = '~D~ump'    # file_window.nml:95
        _w3.command = SetViewMode('dump')    # file_window.nml:96

        _w5.text = '~W~rap lines'    # file_window.nml:99
        _w5.command = Unwrap    # file_window.nml:100

        _w6.text = '~N~o filter'    # file_window.nml:102
        _w6.command = SetViewFilter(0)    # file_window.nml:103

        _w7.text = '~A~SCII filter'    # file_window.nml:105
        _w7.command = SetViewFilter(1)    # file_window.nml:106

        _w8.text = '~P~rintable filter'    # file_window.nml:108
        _w8.command = SetViewFilter(2)    # file_window.nml:109

        _w10.text = '~S~earch...'    # file_window.nml:112
        _w10.command = SearchFor    # file_window.nml:113

        _w11.text = 'Search a~g~ain'    # file_window.nml:115
        _w11.command = ContinueSearch    # file_window.nml:116

        _w12.text = 'Re~v~erse search'    # file_window.nml:118
        _w12.command = ReverseSearch    # file_window.nml:119

        _w13.text = 'Go to add~r~ess...'    # file_window.nml:121
        _w13.command = GotoAddress    # file_window.nml:122

        _w15.text = 'St~o~re'    # file_window.nml:125
        _w15.key = 'Shift-F2'    # file_window.nml:126

        _w16.text = 'Sav~e~ as...'    # file_window.nml:128
        _w16.command = SaveViewAs    # file_window.nml:129
        _w16.key = 'Shift-F5'    # file_window.nml:130

        _w17.text = 'Encod~i~ng...'    # file_window.nml:132
        _w17.command = ChooseEncoding    # file_window.nml:133
        _w17.key = 'Shift-F6'    # file_window.nml:134

        _w19.text = '~C~lose'    # file_window.nml:137
        _w19.command = CloseWindow    # file_window.nml:138

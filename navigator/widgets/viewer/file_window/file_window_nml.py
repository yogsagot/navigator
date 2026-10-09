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
from navkit.i18n import tr as _tr
from navkit.reactive import bind as _bind

from navml.component import Component as _Component
from navigator.widgets.viewer.commands import AddFilter, ChooseEncoding, CloseViewer, ContinueSearch, GotoAddress, HexMode, SaveViewAs    # file_window.nml:1
from navigator.widgets.viewer.commands import ReverseSearch, SearchAgain, SearchFor, SetViewFilter, SetViewMode, Unwrap    # file_window.nml:2
from navigator.widgets.editor.commands import ChooseFileType, SwitchHighLight    # file_window.nml:3
from navigator.widgets.viewer.file_viewer import FileViewer    # file_window.nml:4
from navml.commands import CloseWindow    # file_window.nml:5
from navml.widgets.dialog.scroll_bar import ScrollBar    # file_window.nml:6
from navml.widgets.dialog.static_text import StaticText    # file_window.nml:7
from navml.widgets.menu.menu_item import MenuItem    # file_window.nml:8
from navml.widgets.menu.menu_line import MenuLine    # file_window.nml:9
from navml.widgets.menu.sub_menu import SubMenu    # file_window.nml:10
from navml.widgets.window import Window    # file_window.nml:11

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
    keys = {    # file_window.nml:33
        'escape': CloseWindow,    # file_window.nml:34
        'f3': CloseViewer,    # file_window.nml:35
        'f2': Unwrap,    # file_window.nml:36
        'f4': HexMode,    # file_window.nml:37
        'f5': GotoAddress,    # file_window.nml:38
        'f6': AddFilter,    # file_window.nml:39
        'f7': SearchFor,    # file_window.nml:40
        'ctrl+f7': ReverseSearch,    # file_window.nml:41
        'shift+f5': SaveViewAs,    # file_window.nml:42
        'shift+f6': ChooseEncoding,    # file_window.nml:43
        'shift+f7': ContinueSearch,    # file_window.nml:44
        'ctrl+l': SearchAgain,    # file_window.nml:45
        'ctrl+shift+h': ChooseFileType,    # file_window.nml:47
    }

    #: Ids, annotated so the hand-written half completes them.
    viewer: FileViewer    # file_window.nml:50
    bar: ScrollBar    # file_window.nml:60
    info: StaticText    # file_window.nml:71
    view_menu: SubMenu    # file_window.nml:88
    view_menu_file_type: SubMenu    # file_window.nml:109

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_bar_scroll(self, event: _Event) -> bool:    # file_window.nml:60
        """``bar`` raised an event whose handler is ``on_scroll``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.viewer = FileViewer(parent=self)    # file_window.nml:49
        self.bar = ScrollBar(parent=self)    # file_window.nml:59
        self.info = StaticText(parent=self)    # file_window.nml:70
        self.view_menu = SubMenu(parent=self)    # file_window.nml:87
        _w1 = MenuItem(parent=self.view_menu)    # file_window.nml:91
        _w2 = MenuItem(parent=self.view_menu)    # file_window.nml:94
        _w3 = MenuItem(parent=self.view_menu)    # file_window.nml:97
        _w4 = MenuLine(parent=self.view_menu)    # file_window.nml:100
        _w5 = MenuItem(parent=self.view_menu)    # file_window.nml:101
        _w6 = MenuItem(parent=self.view_menu)    # file_window.nml:104
        self.view_menu_file_type = SubMenu(parent=self.view_menu)    # file_window.nml:108
        _w7 = MenuItem(parent=self.view_menu)    # file_window.nml:112
        _w8 = MenuItem(parent=self.view_menu)    # file_window.nml:115
        _w9 = MenuItem(parent=self.view_menu)    # file_window.nml:118
        _w10 = MenuLine(parent=self.view_menu)    # file_window.nml:121
        _w11 = MenuItem(parent=self.view_menu)    # file_window.nml:122
        _w12 = MenuItem(parent=self.view_menu)    # file_window.nml:125
        _w13 = MenuItem(parent=self.view_menu)    # file_window.nml:128
        _w14 = MenuItem(parent=self.view_menu)    # file_window.nml:131
        _w15 = MenuLine(parent=self.view_menu)    # file_window.nml:134
        _w16 = MenuItem(parent=self.view_menu)    # file_window.nml:135
        _w17 = MenuItem(parent=self.view_menu)    # file_window.nml:138
        _w18 = MenuItem(parent=self.view_menu)    # file_window.nml:142
        _w19 = MenuLine(parent=self.view_menu)    # file_window.nml:146
        _w20 = MenuItem(parent=self.view_menu)    # file_window.nml:147

        self.zoomed = True    # file_window.nml:25

        self.viewer.x = 1    # file_window.nml:51
        self.viewer.y = 1    # file_window.nml:52
        self.viewer.width = _bind(lambda _o: max(0, _o.parent.width - 2))    # file_window.nml:53
        self.viewer.height = _bind(lambda _o: max(0, _o.parent.height - 2))    # file_window.nml:54

        self.bar.x = _bind(lambda _o: _o.parent.width - 1)    # file_window.nml:61
        self.bar.y = 1    # file_window.nml:62
        self.bar.width = 1    # file_window.nml:63
        self.bar.height = _bind(lambda _o: max(0, _o.parent.height - 2))    # file_window.nml:64
        self.bar.value = _bind(lambda _o: self.viewer.top)    # file_window.nml:65
        self.bar.maximum = _bind(lambda _o: self.viewer.size)    # file_window.nml:66
        self.bar.page = _bind(    # file_window.nml:67
            lambda _o: max(1, self.viewer.width * self.viewer.height)
        )
        self.bar.on_scroll = self.on_bar_scroll    # file_window.nml:60

        self.info.x = 1    # file_window.nml:72
        self.info.y = _bind(lambda _o: max(0, _o.parent.height - 1))    # file_window.nml:73
        self.info.width = _bind(    # file_window.nml:74
            lambda _o: min(len(self.viewer.info_text), max(0, _o.parent.width - 3))
        )
        self.info.height = 1    # file_window.nml:75
        self.info.text = _bind(lambda _o: self.viewer.info_text)    # file_window.nml:76

        self.view_menu.text = _bind(lambda _o: _tr('~V~iew'), yielding=True)    # file_window.nml:89
        self.view_menu.after = 'File'    # file_window.nml:90

        _w1.text = _bind(lambda _o: _tr('~T~ext'), yielding=True)    # file_window.nml:92
        _w1.command = SetViewMode('text')    # file_window.nml:93

        _w2.text = _bind(lambda _o: _tr('~H~ex'), yielding=True)    # file_window.nml:95
        _w2.command = SetViewMode('hex')    # file_window.nml:96

        _w3.text = _bind(lambda _o: _tr('~D~ump'), yielding=True)    # file_window.nml:98
        _w3.command = SetViewMode('dump')    # file_window.nml:99

        _w5.text = _bind(lambda _o: _tr('~W~rap lines'), yielding=True)    # file_window.nml:102
        _w5.command = Unwrap    # file_window.nml:103

        _w6.text = _bind(lambda _o: _tr('S~y~ntax highlight'), yielding=True)    # file_window.nml:105
        _w6.command = SwitchHighLight    # file_window.nml:106

        self.view_menu_file_type.text = _bind(    # file_window.nml:110
            lambda _o: _tr('~F~ile type'),
            yielding=True,
        )
        self.view_menu_file_type.key_command = ChooseFileType    # file_window.nml:111

        _w7.text = _bind(lambda _o: _tr('~N~o filter'), yielding=True)    # file_window.nml:113
        _w7.command = SetViewFilter(0)    # file_window.nml:114

        _w8.text = _bind(lambda _o: _tr('~A~SCII filter'), yielding=True)    # file_window.nml:116
        _w8.command = SetViewFilter(1)    # file_window.nml:117

        _w9.text = _bind(lambda _o: _tr('~P~rintable filter'), yielding=True)    # file_window.nml:119
        _w9.command = SetViewFilter(2)    # file_window.nml:120

        _w11.text = _bind(lambda _o: _tr('~S~earch...'), yielding=True)    # file_window.nml:123
        _w11.command = SearchFor    # file_window.nml:124

        _w12.text = _bind(lambda _o: _tr('Search a~g~ain'), yielding=True)    # file_window.nml:126
        _w12.command = ContinueSearch    # file_window.nml:127

        _w13.text = _bind(lambda _o: _tr('Re~v~erse search'), yielding=True)    # file_window.nml:129
        _w13.command = ReverseSearch    # file_window.nml:130

        _w14.text = _bind(lambda _o: _tr('Go to add~r~ess...'), yielding=True)    # file_window.nml:132
        _w14.command = GotoAddress    # file_window.nml:133

        _w16.text = _bind(lambda _o: _tr('St~o~re'), yielding=True)    # file_window.nml:136
        _w16.key = 'Shift-F2'    # file_window.nml:137

        _w17.text = _bind(lambda _o: _tr('Sav~e~ as...'), yielding=True)    # file_window.nml:139
        _w17.command = SaveViewAs    # file_window.nml:140
        _w17.key = 'Shift-F5'    # file_window.nml:141

        _w18.text = _bind(lambda _o: _tr('Encod~i~ng...'), yielding=True)    # file_window.nml:143
        _w18.command = ChooseEncoding    # file_window.nml:144
        _w18.key = 'Shift-F6'    # file_window.nml:145

        _w20.text = _bind(lambda _o: _tr('~C~lose'), yielding=True)    # file_window.nml:148
        _w20.command = CloseWindow    # file_window.nml:149

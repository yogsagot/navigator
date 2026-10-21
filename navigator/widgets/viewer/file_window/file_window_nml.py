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
from navigator.widgets.viewer.commands import ReverseSearch, SearchAgain, SearchFor, SetViewFilter, SetViewMode, SwitchRendered, Unwrap    # file_window.nml:2
from navigator.widgets.editor.commands import ChooseFileType, SwitchHiddenChars, SwitchHighLight    # file_window.nml:3
from navigator.settings import SETTINGS    # file_window.nml:4
from navigator.widgets.viewer.file_viewer import FileViewer    # file_window.nml:5
from navml.commands import CloseWindow    # file_window.nml:6
from navml.widgets.dialog.scroll_bar import ScrollBar    # file_window.nml:7
from navml.widgets.dialog.static_text import StaticText    # file_window.nml:8
from navml.widgets.menu.menu_item import MenuItem    # file_window.nml:9
from navml.widgets.menu.menu_line import MenuLine    # file_window.nml:10
from navml.widgets.menu.sub_menu import SubMenu    # file_window.nml:11
from navml.widgets.option_strip import OptionStrip    # file_window.nml:12
from navml.widgets.window import Window    # file_window.nml:13

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
    keys = {    # file_window.nml:35
        'escape': CloseWindow,    # file_window.nml:36
        'f3': CloseViewer,    # file_window.nml:37
        'f2': Unwrap,    # file_window.nml:38
        'f4': HexMode,    # file_window.nml:39
        'shift+f4': SwitchRendered,    # file_window.nml:41
        'f5': GotoAddress,    # file_window.nml:42
        'f6': AddFilter,    # file_window.nml:43
        'f7': SearchFor,    # file_window.nml:44
        'ctrl+f7': ReverseSearch,    # file_window.nml:45
        'shift+f5': SaveViewAs,    # file_window.nml:46
        'shift+f6': ChooseEncoding,    # file_window.nml:47
        'shift+f7': ContinueSearch,    # file_window.nml:48
        'ctrl+l': SearchAgain,    # file_window.nml:49
        'ctrl+shift+h': ChooseFileType,    # file_window.nml:51
        'ctrl+shift+8': SwitchHiddenChars,    # file_window.nml:53
    }

    #: Ids, annotated so the hand-written half completes them.
    viewer: FileViewer    # file_window.nml:56
    bar: ScrollBar    # file_window.nml:66
    info: StaticText    # file_window.nml:77
    md_mark: StaticText    # file_window.nml:90
    options: OptionStrip    # file_window.nml:103
    view_menu: SubMenu    # file_window.nml:122
    view_menu_rendered: MenuItem    # file_window.nml:142
    view_menu_file_type: SubMenu    # file_window.nml:156

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_bar_scroll(self, event: _Event) -> bool:    # file_window.nml:66
        """``bar`` raised an event whose handler is ``on_scroll``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.viewer = FileViewer(parent=self)    # file_window.nml:55
        self.bar = ScrollBar(parent=self)    # file_window.nml:65
        self.info = StaticText(parent=self)    # file_window.nml:76
        self.md_mark = StaticText(parent=self)    # file_window.nml:89
        self.options = OptionStrip(parent=self)    # file_window.nml:102
        self.view_menu = SubMenu(parent=self)    # file_window.nml:121
        _w1 = MenuItem(parent=self.view_menu)    # file_window.nml:125
        _w2 = MenuItem(parent=self.view_menu)    # file_window.nml:128
        _w3 = MenuItem(parent=self.view_menu)    # file_window.nml:131
        _w4 = MenuLine(parent=self.view_menu)    # file_window.nml:134
        _w5 = MenuItem(parent=self.view_menu)    # file_window.nml:135
        self.view_menu_rendered = MenuItem(parent=self.view_menu)    # file_window.nml:141
        _w6 = MenuItem(parent=self.view_menu)    # file_window.nml:146
        _w7 = MenuItem(parent=self.view_menu)    # file_window.nml:151
        self.view_menu_file_type = SubMenu(parent=self.view_menu)    # file_window.nml:155
        _w8 = MenuItem(parent=self.view_menu)    # file_window.nml:159
        _w9 = MenuItem(parent=self.view_menu)    # file_window.nml:162
        _w10 = MenuItem(parent=self.view_menu)    # file_window.nml:165
        _w11 = MenuLine(parent=self.view_menu)    # file_window.nml:168
        _w12 = MenuItem(parent=self.view_menu)    # file_window.nml:169
        _w13 = MenuItem(parent=self.view_menu)    # file_window.nml:172
        _w14 = MenuItem(parent=self.view_menu)    # file_window.nml:175
        _w15 = MenuItem(parent=self.view_menu)    # file_window.nml:178
        _w16 = MenuLine(parent=self.view_menu)    # file_window.nml:181
        _w17 = MenuItem(parent=self.view_menu)    # file_window.nml:182
        _w18 = MenuItem(parent=self.view_menu)    # file_window.nml:185
        _w19 = MenuItem(parent=self.view_menu)    # file_window.nml:189
        _w20 = MenuLine(parent=self.view_menu)    # file_window.nml:193
        _w21 = MenuItem(parent=self.view_menu)    # file_window.nml:194

        self.zoomed = True    # file_window.nml:27

        self.viewer.x = 1    # file_window.nml:57
        self.viewer.y = 1    # file_window.nml:58
        self.viewer.width = _bind(lambda _o: max(0, _o.parent.width - 2))    # file_window.nml:59
        self.viewer.height = _bind(lambda _o: max(0, _o.parent.height - 2))    # file_window.nml:60

        self.bar.x = _bind(lambda _o: _o.parent.width - 1)    # file_window.nml:67
        self.bar.y = 1    # file_window.nml:68
        self.bar.width = 1    # file_window.nml:69
        self.bar.height = _bind(lambda _o: max(0, _o.parent.height - 2))    # file_window.nml:70
        self.bar.value = _bind(lambda _o: self.viewer.top)    # file_window.nml:71
        self.bar.maximum = _bind(lambda _o: self.viewer.size)    # file_window.nml:72
        self.bar.page = _bind(    # file_window.nml:73
            lambda _o: max(1, self.viewer.width * self.viewer.height)
        )
        self.bar.on_scroll = self.on_bar_scroll    # file_window.nml:66

        self.info.name = 'info'    # file_window.nml:80
        self.info.x = 1    # file_window.nml:81
        self.info.y = _bind(lambda _o: max(0, _o.parent.height - 1))    # file_window.nml:82
        self.info.width = _bind(    # file_window.nml:83
            lambda _o: min(len(self.viewer.info_text), max(0, _o.parent.width - 3))
        )
        self.info.height = 1    # file_window.nml:84
        self.info.text = _bind(lambda _o: self.viewer.info_text)    # file_window.nml:85

        self.md_mark.x = _bind(lambda _o: self.info.x + self.info.width)    # file_window.nml:91
        self.md_mark.y = _bind(lambda _o: max(0, _o.parent.height - 1))    # file_window.nml:92
        self.md_mark.width = _bind(    # file_window.nml:93
            lambda _o: min(len(self.viewer.render_mark), max(0, _o.parent.width - 3 - self.info.width))
        )
        self.md_mark.height = 1    # file_window.nml:94
        self.md_mark.text = _bind(lambda _o: self.viewer.render_mark)    # file_window.nml:95
        self.md_mark.classes = _bind(    # file_window.nml:96
            lambda _o: frozenset({'rendered'}) if self.viewer.rendered else frozenset({'rendered', 'off'})
        )

        self.options.visible = _bind(    # file_window.nml:104
            lambda _o: self.active and SETTINGS.viewer.show_options
        )
        self.options.target = _bind(lambda _o: self.viewer)    # file_window.nml:105
        self.options.room = _bind(    # file_window.nml:106
            lambda _o: max(0, _o.parent.width - 3 - (self.md_mark.x + self.md_mark.width) - 1)
        )
        self.options.width = _bind(lambda _o: _o.used_width)    # file_window.nml:107
        self.options.x = _bind(    # file_window.nml:108
            lambda _o: max(0, _o.parent.width - 3 - _o.width)
        )
        self.options.y = _bind(lambda _o: max(0, _o.parent.height - 1))    # file_window.nml:109
        self.options.height = 1    # file_window.nml:110

        self.view_menu.text = _bind(lambda _o: _tr('~V~iew'), yielding=True)    # file_window.nml:123
        self.view_menu.after = 'File'    # file_window.nml:124

        _w1.text = _bind(lambda _o: _tr('~T~ext'), yielding=True)    # file_window.nml:126
        _w1.command = SetViewMode('text')    # file_window.nml:127

        _w2.text = _bind(lambda _o: _tr('~H~ex'), yielding=True)    # file_window.nml:129
        _w2.command = SetViewMode('hex')    # file_window.nml:130

        _w3.text = _bind(lambda _o: _tr('~D~ump'), yielding=True)    # file_window.nml:132
        _w3.command = SetViewMode('dump')    # file_window.nml:133

        _w5.text = _bind(lambda _o: _tr('~W~rap lines'), yielding=True)    # file_window.nml:136
        _w5.command = Unwrap    # file_window.nml:137

        self.view_menu_rendered.text = _bind(    # file_window.nml:143
            lambda _o: _tr('~M~arkup view'),
            yielding=True,
        )
        self.view_menu_rendered.command = SwitchRendered    # file_window.nml:144
        self.view_menu_rendered.key = 'Shift-F4'    # file_window.nml:145

        _w6.text = _bind(lambda _o: _tr('S~y~ntax highlight'), yielding=True)    # file_window.nml:147
        _w6.command = SwitchHighLight    # file_window.nml:148

        _w7.text = _bind(lambda _o: _tr('Hidden characters'), yielding=True)    # file_window.nml:152
        _w7.command = SwitchHiddenChars    # file_window.nml:153

        self.view_menu_file_type.text = _bind(    # file_window.nml:157
            lambda _o: _tr('~F~ile type'),
            yielding=True,
        )
        self.view_menu_file_type.key_command = ChooseFileType    # file_window.nml:158

        _w8.text = _bind(lambda _o: _tr('~N~o filter'), yielding=True)    # file_window.nml:160
        _w8.command = SetViewFilter(0)    # file_window.nml:161

        _w9.text = _bind(lambda _o: _tr('~A~SCII filter'), yielding=True)    # file_window.nml:163
        _w9.command = SetViewFilter(1)    # file_window.nml:164

        _w10.text = _bind(lambda _o: _tr('~P~rintable filter'), yielding=True)    # file_window.nml:166
        _w10.command = SetViewFilter(2)    # file_window.nml:167

        _w12.text = _bind(lambda _o: _tr('~S~earch...'), yielding=True)    # file_window.nml:170
        _w12.command = SearchFor    # file_window.nml:171

        _w13.text = _bind(lambda _o: _tr('Search a~g~ain'), yielding=True)    # file_window.nml:173
        _w13.command = ContinueSearch    # file_window.nml:174

        _w14.text = _bind(lambda _o: _tr('Re~v~erse search'), yielding=True)    # file_window.nml:176
        _w14.command = ReverseSearch    # file_window.nml:177

        _w15.text = _bind(lambda _o: _tr('Go to add~r~ess...'), yielding=True)    # file_window.nml:179
        _w15.command = GotoAddress    # file_window.nml:180

        _w17.text = _bind(lambda _o: _tr('St~o~re'), yielding=True)    # file_window.nml:183
        _w17.key = 'Shift-F2'    # file_window.nml:184

        _w18.text = _bind(lambda _o: _tr('Sav~e~ as...'), yielding=True)    # file_window.nml:186
        _w18.command = SaveViewAs    # file_window.nml:187
        _w18.key = 'Shift-F5'    # file_window.nml:188

        _w19.text = _bind(lambda _o: _tr('Encod~i~ng...'), yielding=True)    # file_window.nml:190
        _w19.command = ChooseEncoding    # file_window.nml:191
        _w19.key = 'Shift-F6'    # file_window.nml:192

        _w21.text = _bind(lambda _o: _tr('~C~lose'), yielding=True)    # file_window.nml:195
        _w21.command = CloseWindow    # file_window.nml:196

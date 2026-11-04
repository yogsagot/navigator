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
from navkit.bidi import display_width    # file_window.nml:1
from navigator.widgets.viewer.commands import AddFilter, ChooseEncoding, CloseViewer, ContinueSearch, FilterLines, FollowEnd, GotoAddress, HexMode, SaveViewAs    # file_window.nml:2
from navigator.widgets.viewer.commands import ReverseSearch, SearchAgain, SearchFor, SetViewFilter, SetViewMode, SwitchRendered, Unwrap, ViewAsTree, WriteModify    # file_window.nml:3
from navigator.widgets.editor.commands import ChooseFileType, SwitchHiddenChars, SwitchHighLight    # file_window.nml:4
from navigator.settings import SETTINGS    # file_window.nml:5
from navigator.widgets.viewer.file_viewer import FileViewer    # file_window.nml:6
from navml.commands import CloseWindow    # file_window.nml:7
from navml.widgets.dialog.scroll_bar import ScrollBar    # file_window.nml:8
from navml.widgets.dialog.static_text import StaticText    # file_window.nml:9
from navml.widgets.menu.menu_item import MenuItem    # file_window.nml:10
from navml.widgets.menu.menu_line import MenuLine    # file_window.nml:11
from navml.widgets.menu.sub_menu import SubMenu    # file_window.nml:12
from navml.widgets.option_strip import OptionStrip    # file_window.nml:13
from navml.widgets.window import Window    # file_window.nml:14

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
    #: Shift's.  Shift+F2's *Store* writes the bytes typed over in hex
    #: (``WriteModify``); Shift+F6's *XLat* chooses an encoding.  Ctrl+L continues a search with no caption, as it did.
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
        'shift+f2': WriteModify,    # file_window.nml:46
        'shift+f5': SaveViewAs,    # file_window.nml:47
        'shift+f6': ChooseEncoding,    # file_window.nml:48
        'shift+f7': ContinueSearch,    # file_window.nml:49
        'ctrl+l': SearchAgain,    # file_window.nml:50
        'ctrl+shift+h': ChooseFileType,    # file_window.nml:52
        'ctrl+shift+8': SwitchHiddenChars,    # file_window.nml:54
        'ctrl+t': FollowEnd,    # file_window.nml:57
        'ctrl+g': FilterLines,    # file_window.nml:58
    }

    #: Ids, annotated so the hand-written half completes them.
    viewer: FileViewer    # file_window.nml:61
    bar: ScrollBar    # file_window.nml:73
    info: StaticText    # file_window.nml:85
    md_mark: StaticText    # file_window.nml:98
    hbar: ScrollBar    # file_window.nml:113
    options: OptionStrip    # file_window.nml:129
    view_menu: SubMenu    # file_window.nml:147
    view_menu_mode: SubMenu    # file_window.nml:154
    view_menu_file_type: SubMenu    # file_window.nml:208
    view_menu_filter: SubMenu    # file_window.nml:212

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_bar_scroll(self, event: _Event) -> bool:    # file_window.nml:73
        """``bar`` raised an event whose handler is ``on_scroll``."""
        return False

    async def on_hbar_scroll(self, event: _Event) -> bool:    # file_window.nml:113
        """``hbar`` raised an event whose handler is ``on_scroll``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.viewer = FileViewer(parent=self)    # file_window.nml:60
        self.bar = ScrollBar(parent=self)    # file_window.nml:72
        self.info = StaticText(parent=self)    # file_window.nml:84
        self.md_mark = StaticText(parent=self)    # file_window.nml:97
        self.hbar = ScrollBar(parent=self)    # file_window.nml:112
        self.options = OptionStrip(parent=self)    # file_window.nml:128
        self.view_menu = SubMenu(parent=self)    # file_window.nml:146
        self.view_menu_mode = SubMenu(parent=self.view_menu)    # file_window.nml:153
        _w1 = MenuItem(parent=self.view_menu_mode)    # file_window.nml:159
        _w2 = MenuLine(parent=self.view_menu_mode)    # file_window.nml:162
        _w3 = MenuItem(parent=self.view_menu_mode)    # file_window.nml:163
        _w4 = MenuItem(parent=self.view_menu_mode)    # file_window.nml:166
        _w5 = MenuItem(parent=self.view_menu_mode)    # file_window.nml:169
        _w6 = MenuLine(parent=self.view_menu)    # file_window.nml:172
        _w7 = MenuItem(parent=self.view_menu)    # file_window.nml:173
        _w8 = MenuItem(parent=self.view_menu)    # file_window.nml:177
        _w9 = MenuItem(parent=self.view_menu)    # file_window.nml:181
        _w10 = MenuItem(parent=self.view_menu)    # file_window.nml:187
        _w11 = MenuItem(parent=self.view_menu)    # file_window.nml:194
        _w12 = MenuItem(parent=self.view_menu)    # file_window.nml:198
        _w13 = MenuItem(parent=self.view_menu)    # file_window.nml:203
        self.view_menu_file_type = SubMenu(parent=self.view_menu)    # file_window.nml:207
        self.view_menu_filter = SubMenu(parent=self.view_menu)    # file_window.nml:211
        _w14 = MenuItem(parent=self.view_menu_filter)    # file_window.nml:216
        _w15 = MenuLine(parent=self.view_menu_filter)    # file_window.nml:220
        _w16 = MenuItem(parent=self.view_menu_filter)    # file_window.nml:221
        _w17 = MenuItem(parent=self.view_menu_filter)    # file_window.nml:224
        _w18 = MenuItem(parent=self.view_menu_filter)    # file_window.nml:228
        _w19 = MenuLine(parent=self.view_menu)    # file_window.nml:232
        _w20 = MenuItem(parent=self.view_menu)    # file_window.nml:233
        _w21 = MenuItem(parent=self.view_menu)    # file_window.nml:236
        _w22 = MenuItem(parent=self.view_menu)    # file_window.nml:239
        _w23 = MenuItem(parent=self.view_menu)    # file_window.nml:242
        _w24 = MenuLine(parent=self.view_menu)    # file_window.nml:246
        _w25 = MenuItem(parent=self.view_menu)    # file_window.nml:249
        _w26 = MenuItem(parent=self.view_menu)    # file_window.nml:254
        _w27 = MenuItem(parent=self.view_menu)    # file_window.nml:258
        _w28 = MenuLine(parent=self.view_menu)    # file_window.nml:263
        _w29 = MenuItem(parent=self.view_menu)    # file_window.nml:264

        self.zoomed = True    # file_window.nml:28

        self.viewer.x = 1    # file_window.nml:62
        self.viewer.y = 1    # file_window.nml:63
        self.viewer.width = _bind(lambda _o: max(0, _o.parent.width - 2))    # file_window.nml:64
        self.viewer.height = _bind(lambda _o: max(0, _o.parent.height - 2))    # file_window.nml:65

        self.bar.visible = _bind(lambda _o: self.viewer.overflows)    # file_window.nml:74
        self.bar.x = _bind(lambda _o: _o.parent.width - 1)    # file_window.nml:75
        self.bar.y = 1    # file_window.nml:76
        self.bar.width = 1    # file_window.nml:77
        self.bar.height = _bind(lambda _o: max(0, _o.parent.height - 2))    # file_window.nml:78
        self.bar.value = _bind(lambda _o: self.viewer.top)    # file_window.nml:79
        self.bar.maximum = _bind(lambda _o: self.viewer.size)    # file_window.nml:80
        self.bar.page = _bind(    # file_window.nml:81
            lambda _o: max(1, self.viewer.width * self.viewer.height)
        )
        self.bar.on_scroll = self.on_bar_scroll    # file_window.nml:73

        self.info.name = 'info'    # file_window.nml:88
        self.info.x = 1    # file_window.nml:89
        self.info.y = _bind(lambda _o: max(0, _o.parent.height - 1))    # file_window.nml:90
        self.info.width = _bind(    # file_window.nml:91
            lambda _o: min(display_width(self.viewer.info_text), max(0, _o.parent.width - 3))
        )
        self.info.height = 1    # file_window.nml:92
        self.info.text = _bind(lambda _o: self.viewer.info_text)    # file_window.nml:93

        self.md_mark.x = _bind(lambda _o: self.info.x + self.info.width)    # file_window.nml:99
        self.md_mark.y = _bind(lambda _o: max(0, _o.parent.height - 1))    # file_window.nml:100
        self.md_mark.width = _bind(    # file_window.nml:101
            lambda _o: min(display_width(self.viewer.render_mark), max(0, _o.parent.width - 3 - self.info.width))
        )
        self.md_mark.height = 1    # file_window.nml:102
        self.md_mark.text = _bind(lambda _o: self.viewer.render_mark)    # file_window.nml:103
        self.md_mark.classes = _bind(    # file_window.nml:104
            lambda _o: frozenset({'rendered'}) if self.viewer.rendered else frozenset({'rendered', 'off'})
        )

        self.hbar.orientation = 'horizontal'    # file_window.nml:114
        self.hbar.visible = _bind(    # file_window.nml:115
            lambda _o: self.active and self.viewer.row_span > self.viewer.width and (_o.width >= 4)
        )
        self.hbar.x = _bind(lambda _o: self.md_mark.x + self.md_mark.width + 1)    # file_window.nml:116
        self.hbar.y = _bind(lambda _o: max(0, _o.parent.height - 1))    # file_window.nml:117
        self.hbar.width = _bind(    # file_window.nml:118
            lambda _o: max(0, (self.options.x - 1 if self.options.visible and self.options.width else _o.parent.width - 2) - _o.x)
        )
        self.hbar.height = 1    # file_window.nml:119
        self.hbar.value = _bind(lambda _o: self.viewer.x_delta)    # file_window.nml:120
        self.hbar.maximum = _bind(    # file_window.nml:121
            lambda _o: max(0, self.viewer.row_span - self.viewer.width)
        )
        self.hbar.page = _bind(lambda _o: max(1, self.viewer.width))    # file_window.nml:122
        self.hbar.on_scroll = self.on_hbar_scroll    # file_window.nml:113

        self.options.visible = _bind(    # file_window.nml:130
            lambda _o: self.active and SETTINGS.viewer.show_options
        )
        self.options.target = _bind(lambda _o: self.viewer)    # file_window.nml:131
        self.options.room = _bind(    # file_window.nml:132
            lambda _o: max(0, _o.parent.width - 3 - (self.md_mark.x + self.md_mark.width) - 1)
        )
        self.options.width = _bind(lambda _o: _o.used_width)    # file_window.nml:133
        self.options.x = _bind(    # file_window.nml:134
            lambda _o: max(0, _o.parent.width - 3 - _o.width)
        )
        self.options.y = _bind(lambda _o: max(0, _o.parent.height - 1))    # file_window.nml:135
        self.options.height = 1    # file_window.nml:136

        self.view_menu.text = _bind(lambda _o: _tr('~V~iew'), yielding=True)    # file_window.nml:148
        self.view_menu.tooltip = _bind(    # file_window.nml:149
            lambda _o: _tr('Text, hex or dump, wrapping, filters, search and encoding'),
            yielding=True,
        )
        self.view_menu.after = 'File'    # file_window.nml:150

        self.view_menu_mode.text = _bind(    # file_window.nml:155
            lambda _o: _tr('Mo~d~e'),
            yielding=True,
        )
        self.view_menu_mode.tooltip = _bind(    # file_window.nml:156
            lambda _o: _tr('Text, hex or dump'),
            yielding=True,
        )

        _w1.text = _bind(lambda _o: _tr('He~x~/Text/Dump'), yielding=True)    # file_window.nml:160
        _w1.command = HexMode    # file_window.nml:161

        _w3.text = _bind(lambda _o: _tr('~T~ext'), yielding=True)    # file_window.nml:164
        _w3.command = SetViewMode('text')    # file_window.nml:165

        _w4.text = _bind(lambda _o: _tr('~H~ex'), yielding=True)    # file_window.nml:167
        _w4.command = SetViewMode('hex')    # file_window.nml:168

        _w5.text = _bind(lambda _o: _tr('~D~ump'), yielding=True)    # file_window.nml:170
        _w5.command = SetViewMode('dump')    # file_window.nml:171

        _w7.text = _bind(lambda _o: _tr('~W~rap lines'), yielding=True)    # file_window.nml:174
        _w7.command = Unwrap    # file_window.nml:175

        _w8.text = _bind(lambda _o: _tr('Follow e~n~d'), yielding=True)    # file_window.nml:178
        _w8.tooltip = _bind(    # file_window.nml:179
            lambda _o: _tr('Keep the end of a growing file in view, as tail -f does'),
            yielding=True,
        )
        _w8.command = FollowEnd    # file_window.nml:180

        _w9.text = _bind(lambda _o: _tr('Fil~t~er lines...'), yielding=True)    # file_window.nml:182
        _w9.tooltip = _bind(    # file_window.nml:183
            lambda _o: _tr('Show only the lines matching a pattern, with their numbers'),
            yielding=True,
        )
        _w9.command = FilterLines    # file_window.nml:184

        _w10.text = _bind(lambda _o: _tr('~M~arkup view'), yielding=True)    # file_window.nml:188
        _w10.tooltip = _bind(    # file_window.nml:189
            lambda _o: _tr('Show a Markdown, reST, HTML or PDF file rendered, or its source'),
            yielding=True,
        )
        _w10.command = SwitchRendered    # file_window.nml:190
        _w10.key = 'Shift-F4'    # file_window.nml:191

        _w11.text = _bind(lambda _o: _tr('D~a~ta tree'), yielding=True)    # file_window.nml:195
        _w11.tooltip = _bind(    # file_window.nml:196
            lambda _o: _tr("Show the file's data -- JSON, YAML, TOML, XML or HTML -- as a tree"),
            yielding=True,
        )
        _w11.command = ViewAsTree    # file_window.nml:197

        _w12.text = _bind(lambda _o: _tr('S~y~ntax highlight'), yielding=True)    # file_window.nml:199
        _w12.command = SwitchHighLight    # file_window.nml:200

        _w13.text = _bind(    # file_window.nml:204
            lambda _o: _tr('Sh~o~w hidden characters'),
            yielding=True,
        )
        _w13.command = SwitchHiddenChars    # file_window.nml:205

        self.view_menu_file_type.text = _bind(    # file_window.nml:209
            lambda _o: _tr('~F~ile type'),
            yielding=True,
        )
        self.view_menu_file_type.key_command = ChooseFileType    # file_window.nml:210

        self.view_menu_filter.text = _bind(    # file_window.nml:213
            lambda _o: _tr('Fi~l~ters'),
            yielding=True,
        )
        self.view_menu_filter.tooltip = _bind(    # file_window.nml:214
            lambda _o: _tr('Hide characters: none, all but ASCII, or the control characters'),
            yielding=True,
        )

        _w14.text = _bind(lambda _o: _tr('Fi~l~ter'), yielding=True)    # file_window.nml:217
        _w14.tooltip = _bind(    # file_window.nml:218
            lambda _o: _tr('Hide characters: none, all but ASCII, or the control characters'),
            yielding=True,
        )
        _w14.command = AddFilter    # file_window.nml:219

        _w16.text = _bind(lambda _o: _tr('~N~o filter'), yielding=True)    # file_window.nml:222
        _w16.command = SetViewFilter(0)    # file_window.nml:223

        _w17.text = _bind(lambda _o: _tr('~A~SCII filter'), yielding=True)    # file_window.nml:225
        _w17.tooltip = _bind(    # file_window.nml:226
            lambda _o: _tr('Hide control characters and everything beyond ASCII'),
            yielding=True,
        )
        _w17.command = SetViewFilter(1)    # file_window.nml:227

        _w18.text = _bind(lambda _o: _tr('~P~rintable filter'), yielding=True)    # file_window.nml:229
        _w18.tooltip = _bind(    # file_window.nml:230
            lambda _o: _tr('Hide control characters'),
            yielding=True,
        )
        _w18.command = SetViewFilter(2)    # file_window.nml:231

        _w20.text = _bind(lambda _o: _tr('~S~earch...'), yielding=True)    # file_window.nml:234
        _w20.command = SearchFor    # file_window.nml:235

        _w21.text = _bind(lambda _o: _tr('Search a~g~ain'), yielding=True)    # file_window.nml:237
        _w21.command = ContinueSearch    # file_window.nml:238

        _w22.text = _bind(lambda _o: _tr('Re~v~erse search'), yielding=True)    # file_window.nml:240
        _w22.command = ReverseSearch    # file_window.nml:241

        _w23.text = _bind(lambda _o: _tr('Go to add~r~ess...'), yielding=True)    # file_window.nml:243
        _w23.tooltip = _bind(    # file_window.nml:244
            lambda _o: _tr('Jump to an offset in the file'),
            yielding=True,
        )
        _w23.command = GotoAddress    # file_window.nml:245

        _w25.text = _bind(lambda _o: _tr('Store'), yielding=True)    # file_window.nml:250
        _w25.tooltip = _bind(    # file_window.nml:251
            lambda _o: _tr('Write the bytes typed over in hex into the file'),
            yielding=True,
        )
        _w25.command = WriteModify    # file_window.nml:252
        _w25.key = 'Shift-F2'    # file_window.nml:253

        _w26.text = _bind(lambda _o: _tr('Sav~e~ as...'), yielding=True)    # file_window.nml:255
        _w26.command = SaveViewAs    # file_window.nml:256
        _w26.key = 'Shift-F5'    # file_window.nml:257

        _w27.text = _bind(lambda _o: _tr('Encod~i~ng...'), yielding=True)    # file_window.nml:259
        _w27.tooltip = _bind(    # file_window.nml:260
            lambda _o: _tr('The code page the file is read in'),
            yielding=True,
        )
        _w27.command = ChooseEncoding    # file_window.nml:261
        _w27.key = 'Shift-F6'    # file_window.nml:262

        _w29.text = _bind(lambda _o: _tr('~C~lose'), yielding=True)    # file_window.nml:265
        _w29.command = CloseWindow    # file_window.nml:266

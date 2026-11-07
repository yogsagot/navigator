# navml: generated
"""Generated from ``edit_window.nml``.

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
from navkit.bidi import display_width    # edit_window.nml:1
from navigator.commands import PrintFile    # edit_window.nml:2
from navigator.widgets.editor.commands import BlockStart, BlockEnd, MarkWord, MarkLine, MoveBlockStart, MoveBlockEnd, PlaceMarker, GotoMarker, DeleteWordRight, DeleteToEnd, ChooseEncoding, ChooseLineEnding, ChooseFileType, AsciiTable, CalcBlock, SwitchHiColumn, SwitchHiLine, SwitchHighLight, SwitchHiddenChars, SwitchFill, ShowFindBar, ShowReplaceBar, CapString, CapWord, LowString, LowWord, UpString, UpWord, DuplicateLine, DeleteLine, DeleteWordLeft, InsertLine, HideBlock, BracketPair, SwitchDrawMode, SwitchBack, SwitchIndent, SwitchBrackets, SwitchSave, SwitchWrap, FCenter, FJustify, FLeft, FRight, LCenter, LJustify, LLeft, LRight, SetMargins, ContSearch, LoadText, Replace, ReverseSearch, StartSearch, SaveAll, SaveTextAs, CapitalizeBlock, Clear, ClipboardCopy, ClipboardCut, ClipboardPaste, CopyBlock, GotoLineNumber, PrintBlock, IndentBlock, InsertDate, InsertTime, BlockRead, BlockWrite, LowcaseBlock, MoveBlock, SaveText, SortBlock, UnindentBlock, Undo, Redo, UpcaseBlock, SwitchBlock    # edit_window.nml:3
from navigator.widgets.editor.file_editor import FileEditor, FormatMarks, InfoLine    # edit_window.nml:4
from navigator.widgets.editor.find_bar import FindBar    # edit_window.nml:5
from navigator.settings import SETTINGS    # edit_window.nml:6
from navml.commands import CloseWindow    # edit_window.nml:7
from navml.widgets.option_strip import OptionStrip    # edit_window.nml:8
from navml.widgets.dialog.scroll_bar import ScrollBar    # edit_window.nml:9
from navml.widgets.menu.menu_item import MenuItem    # edit_window.nml:10
from navml.widgets.menu.menu_line import MenuLine    # edit_window.nml:11
from navml.widgets.menu.sub_menu import SubMenu    # edit_window.nml:12
from navml.widgets.window import Window    # edit_window.nml:13

__navml_component__ = "EditWindow"

__all__ = ["EditWindow"]


class EditWindow(Window, _Component):
    """F4: DOS Navigator's ``TEditWindow`` (``MICROED.PAS``).

    A standard window titled ``Edit - `` and the file's path, the editor filling
    the inside of its frame, a vertical scroll bar on the right frame column, a
    horizontal one along the bottom frame, and ``TInfoLine`` over the bottom
    frame's left end -- the views ``TEditWindow.Init`` inserts, in the places it
    puts them.  **It opens zoomed**, as the viewer does.

    Both scroll bars and the info line show only while the window is active, as
    ``TFileEditor.SetState`` hid the bars and ``TInfoLine.Draw`` drew nothing.
    """

    #: The document this class was generated from.
    __navml_source__ = "edit_window.nml"

    #: ``StatusDef hcEditor``: what it captions.  The editing keys are the
    #: editor's own table, and Esc and Alt+F3 close the window, asking first
    #: about a text that has changed.
    keys = {    # edit_window.nml:31
        'escape': CloseWindow,    # edit_window.nml:32
        'alt+f3': CloseWindow,    # edit_window.nml:33
        'f2': SaveText,    # edit_window.nml:34
        'ctrl+s': SaveText,    # edit_window.nml:37
        'f3': LoadText,    # edit_window.nml:38
        'shift+f2': SaveTextAs,    # edit_window.nml:39
        'ctrl+f2': SaveAll,    # edit_window.nml:40
        'f7': StartSearch,    # edit_window.nml:43
        'alt+f7': ReverseSearch,    # edit_window.nml:44
        'ctrl+f7': Replace,    # edit_window.nml:45
        'shift+f7': ContSearch,    # edit_window.nml:46
        'ctrl+shift+h': ChooseFileType,    # edit_window.nml:49
        'ctrl+shift+8': SwitchHiddenChars,    # edit_window.nml:52
        'f8': PrintFile,    # edit_window.nml:55
        'shift+f8': PrintBlock,    # edit_window.nml:56
    }

    #: Ids, annotated so the hand-written half completes them.
    editor: FileEditor    # edit_window.nml:59
    find_bar: FindBar    # edit_window.nml:69
    vbar: ScrollBar    # edit_window.nml:79
    hbar: ScrollBar    # edit_window.nml:99
    info: InfoLine    # edit_window.nml:112
    marks: FormatMarks    # edit_window.nml:127
    options: OptionStrip    # edit_window.nml:142
    edit_menu: SubMenu    # edit_window.nml:167
    edit_menu_delete: SubMenu    # edit_window.nml:216
    edit_menu_file: SubMenu    # edit_window.nml:241
    edit_menu_line_endings: SubMenu    # edit_window.nml:263
    edit_menu_encoding: SubMenu    # edit_window.nml:267
    edit_menu_search: SubMenu    # edit_window.nml:285
    edit_menu_place_marker: SubMenu    # edit_window.nml:329
    edit_menu_goto_marker: SubMenu    # edit_window.nml:369
    edit_menu_paragraph: SubMenu    # edit_window.nml:409
    edit_menu_line_format: SubMenu    # edit_window.nml:433
    edit_menu_block: SubMenu    # edit_window.nml:457
    edit_menu_misc: SubMenu    # edit_window.nml:536
    edit_menu_misc_uppercase: SubMenu    # edit_window.nml:561
    edit_menu_misc_lowercase: SubMenu    # edit_window.nml:576
    edit_menu_misc_capitalize: SubMenu    # edit_window.nml:591
    edit_menu_options: SubMenu    # edit_window.nml:606
    edit_menu_file_type: SubMenu    # edit_window.nml:651

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_vbar_scroll(self, event: _Event) -> bool:    # edit_window.nml:79
        """``vbar`` raised an event whose handler is ``on_scroll``."""
        return False

    async def on_hbar_scroll(self, event: _Event) -> bool:    # edit_window.nml:99
        """``hbar`` raised an event whose handler is ``on_scroll``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.editor = FileEditor(parent=self)    # edit_window.nml:58
        self.find_bar = FindBar(parent=self)    # edit_window.nml:68
        self.vbar = ScrollBar(parent=self)    # edit_window.nml:78
        self.hbar = ScrollBar(parent=self)    # edit_window.nml:98
        self.info = InfoLine(parent=self)    # edit_window.nml:111
        self.marks = FormatMarks(parent=self)    # edit_window.nml:126
        self.options = OptionStrip(parent=self)    # edit_window.nml:141
        self.edit_menu = SubMenu(parent=self)    # edit_window.nml:166
        _w1 = MenuItem(parent=self.edit_menu)    # edit_window.nml:175
        _w2 = MenuItem(parent=self.edit_menu)    # edit_window.nml:179
        _w3 = MenuLine(parent=self.edit_menu)    # edit_window.nml:183
        _w4 = MenuItem(parent=self.edit_menu)    # edit_window.nml:184
        _w5 = MenuItem(parent=self.edit_menu)    # edit_window.nml:188
        _w6 = MenuItem(parent=self.edit_menu)    # edit_window.nml:192
        _w7 = MenuItem(parent=self.edit_menu)    # edit_window.nml:196
        _w8 = MenuItem(parent=self.edit_menu)    # edit_window.nml:200
        _w9 = MenuLine(parent=self.edit_menu)    # edit_window.nml:204
        _w10 = MenuItem(parent=self.edit_menu)    # edit_window.nml:205
        self.edit_menu_delete = SubMenu(parent=self.edit_menu)    # edit_window.nml:215
        _w11 = MenuItem(parent=self.edit_menu_delete)    # edit_window.nml:219
        _w12 = MenuItem(parent=self.edit_menu_delete)    # edit_window.nml:223
        _w13 = MenuItem(parent=self.edit_menu_delete)    # edit_window.nml:227
        _w14 = MenuItem(parent=self.edit_menu_delete)    # edit_window.nml:231
        _w15 = MenuItem(parent=self.edit_menu)    # edit_window.nml:235
        _w16 = MenuLine(parent=self.edit_menu)    # edit_window.nml:239
        self.edit_menu_file = SubMenu(parent=self.edit_menu)    # edit_window.nml:240
        _w17 = MenuItem(parent=self.edit_menu_file)    # edit_window.nml:243
        _w18 = MenuItem(parent=self.edit_menu_file)    # edit_window.nml:247
        _w19 = MenuItem(parent=self.edit_menu_file)    # edit_window.nml:251
        _w20 = MenuItem(parent=self.edit_menu_file)    # edit_window.nml:255
        _w21 = MenuLine(parent=self.edit_menu_file)    # edit_window.nml:259
        self.edit_menu_line_endings = SubMenu(parent=self.edit_menu_file)    # edit_window.nml:262
        self.edit_menu_encoding = SubMenu(parent=self.edit_menu_file)    # edit_window.nml:266
        _w22 = MenuLine(parent=self.edit_menu_file)    # edit_window.nml:270
        _w23 = MenuItem(parent=self.edit_menu_file)    # edit_window.nml:271
        _w24 = MenuItem(parent=self.edit_menu_file)    # edit_window.nml:275
        _w25 = MenuLine(parent=self.edit_menu_file)    # edit_window.nml:279
        _w26 = MenuItem(parent=self.edit_menu_file)    # edit_window.nml:280
        self.edit_menu_search = SubMenu(parent=self.edit_menu)    # edit_window.nml:284
        _w27 = MenuItem(parent=self.edit_menu_search)    # edit_window.nml:288
        _w28 = MenuItem(parent=self.edit_menu_search)    # edit_window.nml:293
        _w29 = MenuLine(parent=self.edit_menu_search)    # edit_window.nml:297
        _w30 = MenuItem(parent=self.edit_menu_search)    # edit_window.nml:298
        _w31 = MenuItem(parent=self.edit_menu_search)    # edit_window.nml:302
        _w32 = MenuItem(parent=self.edit_menu_search)    # edit_window.nml:306
        _w33 = MenuItem(parent=self.edit_menu_search)    # edit_window.nml:310
        _w34 = MenuItem(parent=self.edit_menu_search)    # edit_window.nml:314
        _w35 = MenuItem(parent=self.edit_menu_search)    # edit_window.nml:319
        _w36 = MenuLine(parent=self.edit_menu_search)    # edit_window.nml:327
        self.edit_menu_place_marker = SubMenu(parent=self.edit_menu_search)    # edit_window.nml:328
        _w37 = MenuItem(parent=self.edit_menu_place_marker)    # edit_window.nml:332
        _w38 = MenuItem(parent=self.edit_menu_place_marker)    # edit_window.nml:336
        _w39 = MenuItem(parent=self.edit_menu_place_marker)    # edit_window.nml:340
        _w40 = MenuItem(parent=self.edit_menu_place_marker)    # edit_window.nml:344
        _w41 = MenuItem(parent=self.edit_menu_place_marker)    # edit_window.nml:348
        _w42 = MenuItem(parent=self.edit_menu_place_marker)    # edit_window.nml:352
        _w43 = MenuItem(parent=self.edit_menu_place_marker)    # edit_window.nml:356
        _w44 = MenuItem(parent=self.edit_menu_place_marker)    # edit_window.nml:360
        _w45 = MenuItem(parent=self.edit_menu_place_marker)    # edit_window.nml:364
        self.edit_menu_goto_marker = SubMenu(parent=self.edit_menu_search)    # edit_window.nml:368
        _w46 = MenuItem(parent=self.edit_menu_goto_marker)    # edit_window.nml:372
        _w47 = MenuItem(parent=self.edit_menu_goto_marker)    # edit_window.nml:376
        _w48 = MenuItem(parent=self.edit_menu_goto_marker)    # edit_window.nml:380
        _w49 = MenuItem(parent=self.edit_menu_goto_marker)    # edit_window.nml:384
        _w50 = MenuItem(parent=self.edit_menu_goto_marker)    # edit_window.nml:388
        _w51 = MenuItem(parent=self.edit_menu_goto_marker)    # edit_window.nml:392
        _w52 = MenuItem(parent=self.edit_menu_goto_marker)    # edit_window.nml:396
        _w53 = MenuItem(parent=self.edit_menu_goto_marker)    # edit_window.nml:400
        _w54 = MenuItem(parent=self.edit_menu_goto_marker)    # edit_window.nml:404
        self.edit_menu_paragraph = SubMenu(parent=self.edit_menu)    # edit_window.nml:408
        _w55 = MenuItem(parent=self.edit_menu_paragraph)    # edit_window.nml:411
        _w56 = MenuItem(parent=self.edit_menu_paragraph)    # edit_window.nml:416
        _w57 = MenuItem(parent=self.edit_menu_paragraph)    # edit_window.nml:420
        _w58 = MenuItem(parent=self.edit_menu_paragraph)    # edit_window.nml:424
        self.edit_menu_line_format = SubMenu(parent=self.edit_menu_paragraph)    # edit_window.nml:432
        _w59 = MenuItem(parent=self.edit_menu_line_format)    # edit_window.nml:436
        _w60 = MenuItem(parent=self.edit_menu_line_format)    # edit_window.nml:440
        _w61 = MenuItem(parent=self.edit_menu_line_format)    # edit_window.nml:444
        _w62 = MenuItem(parent=self.edit_menu_line_format)    # edit_window.nml:448
        _w63 = MenuLine(parent=self.edit_menu_paragraph)    # edit_window.nml:452
        _w64 = MenuItem(parent=self.edit_menu_paragraph)    # edit_window.nml:453
        self.edit_menu_block = SubMenu(parent=self.edit_menu)    # edit_window.nml:456
        _w65 = MenuItem(parent=self.edit_menu_block)    # edit_window.nml:462
        _w66 = MenuItem(parent=self.edit_menu_block)    # edit_window.nml:466
        _w67 = MenuItem(parent=self.edit_menu_block)    # edit_window.nml:470
        _w68 = MenuItem(parent=self.edit_menu_block)    # edit_window.nml:474
        _w69 = MenuLine(parent=self.edit_menu_block)    # edit_window.nml:478
        _w70 = MenuItem(parent=self.edit_menu_block)    # edit_window.nml:479
        _w71 = MenuItem(parent=self.edit_menu_block)    # edit_window.nml:483
        _w72 = MenuLine(parent=self.edit_menu_block)    # edit_window.nml:487
        _w73 = MenuItem(parent=self.edit_menu_block)    # edit_window.nml:488
        _w74 = MenuItem(parent=self.edit_menu_block)    # edit_window.nml:492
        _w75 = MenuItem(parent=self.edit_menu_block)    # edit_window.nml:496
        _w76 = MenuItem(parent=self.edit_menu_block)    # edit_window.nml:500
        _w77 = MenuItem(parent=self.edit_menu_block)    # edit_window.nml:505
        _w78 = MenuLine(parent=self.edit_menu_block)    # edit_window.nml:510
        _w79 = MenuItem(parent=self.edit_menu_block)    # edit_window.nml:511
        _w80 = MenuItem(parent=self.edit_menu_block)    # edit_window.nml:515
        _w81 = MenuItem(parent=self.edit_menu_block)    # edit_window.nml:519
        _w82 = MenuLine(parent=self.edit_menu_block)    # edit_window.nml:523
        _w83 = MenuItem(parent=self.edit_menu_block)    # edit_window.nml:524
        _w84 = MenuItem(parent=self.edit_menu_block)    # edit_window.nml:530
        self.edit_menu_misc = SubMenu(parent=self.edit_menu)    # edit_window.nml:535
        _w85 = MenuItem(parent=self.edit_menu_misc)    # edit_window.nml:538
        _w86 = MenuItem(parent=self.edit_menu_misc)    # edit_window.nml:542
        _w87 = MenuItem(parent=self.edit_menu_misc)    # edit_window.nml:546
        _w88 = MenuItem(parent=self.edit_menu_misc)    # edit_window.nml:550
        _w89 = MenuItem(parent=self.edit_menu_misc)    # edit_window.nml:554
        _w90 = MenuLine(parent=self.edit_menu_misc)    # edit_window.nml:559
        self.edit_menu_misc_uppercase = SubMenu(parent=self.edit_menu_misc)    # edit_window.nml:560
        _w91 = MenuItem(parent=self.edit_menu_misc_uppercase)    # edit_window.nml:563
        _w92 = MenuItem(parent=self.edit_menu_misc_uppercase)    # edit_window.nml:567
        _w93 = MenuItem(parent=self.edit_menu_misc_uppercase)    # edit_window.nml:571
        self.edit_menu_misc_lowercase = SubMenu(parent=self.edit_menu_misc)    # edit_window.nml:575
        _w94 = MenuItem(parent=self.edit_menu_misc_lowercase)    # edit_window.nml:578
        _w95 = MenuItem(parent=self.edit_menu_misc_lowercase)    # edit_window.nml:582
        _w96 = MenuItem(parent=self.edit_menu_misc_lowercase)    # edit_window.nml:586
        self.edit_menu_misc_capitalize = SubMenu(parent=self.edit_menu_misc)    # edit_window.nml:590
        _w97 = MenuItem(parent=self.edit_menu_misc_capitalize)    # edit_window.nml:593
        _w98 = MenuItem(parent=self.edit_menu_misc_capitalize)    # edit_window.nml:597
        _w99 = MenuItem(parent=self.edit_menu_misc_capitalize)    # edit_window.nml:601
        self.edit_menu_options = SubMenu(parent=self.edit_menu)    # edit_window.nml:605
        _w100 = MenuItem(parent=self.edit_menu_options)    # edit_window.nml:608
        _w101 = MenuItem(parent=self.edit_menu_options)    # edit_window.nml:612
        _w102 = MenuItem(parent=self.edit_menu_options)    # edit_window.nml:615
        _w103 = MenuItem(parent=self.edit_menu_options)    # edit_window.nml:618
        _w104 = MenuItem(parent=self.edit_menu_options)    # edit_window.nml:621
        _w105 = MenuItem(parent=self.edit_menu_options)    # edit_window.nml:625
        _w106 = MenuItem(parent=self.edit_menu_options)    # edit_window.nml:629
        _w107 = MenuItem(parent=self.edit_menu_options)    # edit_window.nml:633
        _w108 = MenuItem(parent=self.edit_menu_options)    # edit_window.nml:636
        _w109 = MenuItem(parent=self.edit_menu_options)    # edit_window.nml:639
        _w110 = MenuItem(parent=self.edit_menu_options)    # edit_window.nml:643
        self.edit_menu_file_type = SubMenu(parent=self.edit_menu)    # edit_window.nml:650

        self.zoomed = True    # edit_window.nml:26

        self.editor.x = 1    # edit_window.nml:60
        self.editor.y = 1    # edit_window.nml:61
        self.editor.width = _bind(lambda _o: max(0, _o.parent.width - 2))    # edit_window.nml:62
        self.editor.height = _bind(lambda _o: max(0, _o.parent.height - 2))    # edit_window.nml:63

        self.find_bar.width = _bind(    # edit_window.nml:70
            lambda _o: min(50, self.editor.width - 1) if self.editor.width >= 36 else 0
        )
        self.find_bar.height = _bind(lambda _o: 4 if _o.replace else 3)    # edit_window.nml:71
        self.find_bar.x = _bind(    # edit_window.nml:72
            lambda _o: self.editor.x + self.editor.width - _o.width - 1
        )
        self.find_bar.y = _bind(lambda _o: self.editor.y)    # edit_window.nml:73

        self.vbar.visible = _bind(    # edit_window.nml:80
            lambda _o: self.active and self.editor.overflows
        )
        self.vbar.x = _bind(lambda _o: _o.parent.width - 1)    # edit_window.nml:81
        self.vbar.y = 1    # edit_window.nml:82
        self.vbar.width = 1    # edit_window.nml:83
        self.vbar.height = _bind(lambda _o: max(0, _o.parent.height - 2))    # edit_window.nml:84
        self.vbar.value = _bind(lambda _o: self.editor.line)    # edit_window.nml:85
        self.vbar.maximum = _bind(    # edit_window.nml:86
            lambda _o: max(0, self.editor.line_count - 1)
        )
        self.vbar.page = _bind(lambda _o: max(1, self.editor.height))    # edit_window.nml:87
        self.vbar.on_scroll = self.on_vbar_scroll    # edit_window.nml:79

        self.hbar.orientation = 'horizontal'    # edit_window.nml:100
        self.hbar.visible = _bind(    # edit_window.nml:101
            lambda _o: self.active and self.editor.overflows_across and (_o.width >= 4)
        )
        self.hbar.x = _bind(    # edit_window.nml:102
            lambda _o: max(24, self.marks.x + self.marks.width + 1) if self.marks.visible and self.marks.width else 24
        )
        self.hbar.y = _bind(lambda _o: max(0, _o.parent.height - 1))    # edit_window.nml:103
        self.hbar.width = _bind(    # edit_window.nml:104
            lambda _o: max(0, (self.options.x - 1 if self.options.visible and self.options.width else _o.parent.width - 2) - _o.x)
        )
        self.hbar.height = 1    # edit_window.nml:105
        self.hbar.value = _bind(lambda _o: self.editor.col)    # edit_window.nml:106
        self.hbar.maximum = _bind(lambda _o: max(0, self.editor.row_span - 1))    # edit_window.nml:107
        self.hbar.page = _bind(lambda _o: max(1, self.editor.width))    # edit_window.nml:108
        self.hbar.on_scroll = self.on_hbar_scroll    # edit_window.nml:99

        self.info.name = 'info'    # edit_window.nml:114
        self.info.visible = _bind(lambda _o: self.active)    # edit_window.nml:115
        self.info.x = 2    # edit_window.nml:116
        self.info.y = _bind(lambda _o: max(0, _o.parent.height - 1))    # edit_window.nml:117
        self.info.width = _bind(    # edit_window.nml:118
            lambda _o: min(display_width(self.editor.info_text), max(0, _o.parent.width - 4))
        )
        self.info.height = 1    # edit_window.nml:119
        self.info.text = _bind(lambda _o: self.editor.info_text)    # edit_window.nml:120

        self.marks.name = 'info'    # edit_window.nml:128
        self.marks.visible = _bind(lambda _o: self.active)    # edit_window.nml:129
        self.marks.x = _bind(lambda _o: self.info.x + self.info.width + 1)    # edit_window.nml:130
        self.marks.y = _bind(lambda _o: max(0, _o.parent.height - 1))    # edit_window.nml:131
        self.marks.width = _bind(    # edit_window.nml:132
            lambda _o: min(display_width(self.editor.format_text), max(0, _o.parent.width - 3 - _o.x))
        )
        self.marks.height = 1    # edit_window.nml:133
        self.marks.text = _bind(lambda _o: self.editor.format_text)    # edit_window.nml:134

        self.options.visible = _bind(    # edit_window.nml:143
            lambda _o: self.active and SETTINGS.editor.show_options
        )
        self.options.target = _bind(lambda _o: self.editor)    # edit_window.nml:144
        self.options.room = _bind(    # edit_window.nml:145
            lambda _o: max(0, _o.parent.width - 3 - (self.marks.x + self.marks.width if self.marks.visible and self.marks.width else self.info.x + self.info.width) - 1)
        )
        self.options.width = _bind(lambda _o: _o.used_width)    # edit_window.nml:146
        self.options.x = _bind(    # edit_window.nml:147
            lambda _o: max(0, _o.parent.width - 3 - _o.width)
        )
        self.options.y = _bind(lambda _o: max(0, _o.parent.height - 1))    # edit_window.nml:148
        self.options.height = 1    # edit_window.nml:149

        self.edit_menu.text = _bind(lambda _o: _tr('~E~ditor'), yielding=True)    # edit_window.nml:168
        self.edit_menu.tooltip = _bind(    # edit_window.nml:169
            lambda _o: _tr('Editing, the file, search, paragraphs and blocks'),
            yielding=True,
        )
        self.edit_menu.after = 'File'    # edit_window.nml:170

        _w1.text = _bind(lambda _o: _tr('~U~ndo'), yielding=True)    # edit_window.nml:176
        _w1.command = Undo    # edit_window.nml:177
        _w1.key = 'Alt-BkSp'    # edit_window.nml:178

        _w2.text = _bind(lambda _o: _tr('R~e~do'), yielding=True)    # edit_window.nml:180
        _w2.command = Redo    # edit_window.nml:181
        _w2.key = 'Alt-Shift-BkSp'    # edit_window.nml:182

        _w4.text = _bind(lambda _o: _tr('Cu~t~'), yielding=True)    # edit_window.nml:185
        _w4.command = ClipboardCut    # edit_window.nml:186
        _w4.key = 'Shift-Del'    # edit_window.nml:187

        _w5.text = _bind(lambda _o: _tr('~C~opy'), yielding=True)    # edit_window.nml:189
        _w5.command = ClipboardCopy    # edit_window.nml:190
        _w5.key = 'Ctrl-Ins'    # edit_window.nml:191

        _w6.text = _bind(lambda _o: _tr('~P~aste'), yielding=True)    # edit_window.nml:193
        _w6.command = ClipboardPaste    # edit_window.nml:194
        _w6.key = 'Shift-Ins'    # edit_window.nml:195

        _w7.text = _bind(lambda _o: _tr('C~o~py to...'), yielding=True)    # edit_window.nml:197
        _w7.tooltip = _bind(    # edit_window.nml:198
            lambda _o: _tr('Write the block to a file'),
            yielding=True,
        )
        _w7.command = BlockWrite    # edit_window.nml:199

        _w8.text = _bind(lambda _o: _tr('P~a~ste from...'), yielding=True)    # edit_window.nml:201
        _w8.tooltip = _bind(    # edit_window.nml:202
            lambda _o: _tr("Insert a file's text at the cursor"),
            yielding=True,
        )
        _w8.command = BlockRead    # edit_window.nml:203

        _w10.text = _bind(lambda _o: _tr('C~l~ear'), yielding=True)    # edit_window.nml:206
        _w10.tooltip = _bind(    # edit_window.nml:207
            lambda _o: _tr('Delete the selection without copying it to the clipboard'),
            yielding=True,
        )
        _w10.command = Clear    # edit_window.nml:208
        _w10.key = 'Ctrl-Del'    # edit_window.nml:209

        self.edit_menu_delete.text = _bind(    # edit_window.nml:217
            lambda _o: _tr('~D~elete'),
            yielding=True,
        )
        self.edit_menu_delete.tooltip = _bind(    # edit_window.nml:218
            lambda _o: _tr('Delete a line, a word or the rest of the line'),
            yielding=True,
        )

        _w11.text = _bind(lambda _o: _tr('~D~elete line'), yielding=True)    # edit_window.nml:220
        _w11.command = DeleteLine    # edit_window.nml:221
        _w11.key = 'Ctrl-Y'    # edit_window.nml:222

        _w12.text = _bind(lambda _o: _tr('Delete ~w~ord left'), yielding=True)    # edit_window.nml:224
        _w12.command = DeleteWordLeft    # edit_window.nml:225
        _w12.key = 'Ctrl-BkSp'    # edit_window.nml:226

        _w13.text = _bind(lambda _o: _tr('Delete word ri~g~ht'), yielding=True)    # edit_window.nml:228
        _w13.tooltip = _bind(    # edit_window.nml:229
            lambda _o: _tr('Delete from the cursor to the start of the next word'),
            yielding=True,
        )
        _w13.command = DeleteWordRight    # edit_window.nml:230

        _w14.text = _bind(    # edit_window.nml:232
            lambda _o: _tr('Delete to e~n~d of line'),
            yielding=True,
        )
        _w14.tooltip = _bind(    # edit_window.nml:233
            lambda _o: _tr('Delete from the cursor to the end of the line'),
            yielding=True,
        )
        _w14.command = DeleteToEnd    # edit_window.nml:234

        _w15.text = _bind(lambda _o: _tr('Insert l~i~ne'), yielding=True)    # edit_window.nml:236
        _w15.command = InsertLine    # edit_window.nml:237
        _w15.key = 'Ctrl-N'    # edit_window.nml:238

        self.edit_menu_file.text = _bind(    # edit_window.nml:242
            lambda _o: _tr('~F~ile'),
            yielding=True,
        )

        _w17.text = _bind(lambda _o: _tr('~O~pen...'), yielding=True)    # edit_window.nml:244
        _w17.command = LoadText    # edit_window.nml:245
        _w17.key = 'F3'    # edit_window.nml:246

        _w18.text = _bind(lambda _o: _tr('~S~ave'), yielding=True)    # edit_window.nml:248
        _w18.command = SaveText    # edit_window.nml:249
        _w18.key = 'F2'    # edit_window.nml:250

        _w19.text = _bind(lambda _o: _tr('Save ~a~s...'), yielding=True)    # edit_window.nml:252
        _w19.command = SaveTextAs    # edit_window.nml:253
        _w19.key = 'Shift-F2'    # edit_window.nml:254

        _w20.text = _bind(lambda _o: _tr('Save a~l~l...'), yielding=True)    # edit_window.nml:256
        _w20.command = SaveAll    # edit_window.nml:257
        _w20.key = 'Ctrl-F2'    # edit_window.nml:258

        self.edit_menu_line_endings.text = _bind(    # edit_window.nml:264
            lambda _o: _tr('Line en~d~ings'),
            yielding=True,
        )
        self.edit_menu_line_endings.key_command = ChooseLineEnding    # edit_window.nml:265

        self.edit_menu_encoding.text = _bind(    # edit_window.nml:268
            lambda _o: _tr('En~c~oding'),
            yielding=True,
        )
        self.edit_menu_encoding.key_command = ChooseEncoding    # edit_window.nml:269

        _w23.text = _bind(lambda _o: _tr('~P~rint'), yielding=True)    # edit_window.nml:272
        _w23.command = PrintFile    # edit_window.nml:273
        _w23.key = 'F8'    # edit_window.nml:274

        _w24.text = _bind(lambda _o: _tr('Print ~b~lock'), yielding=True)    # edit_window.nml:276
        _w24.command = PrintBlock    # edit_window.nml:277
        _w24.key = 'Shift-F8'    # edit_window.nml:278

        _w26.text = _bind(lambda _o: _tr('E~x~it'), yielding=True)    # edit_window.nml:281
        _w26.command = CloseWindow    # edit_window.nml:282
        _w26.key = 'Ctrl-F4'    # edit_window.nml:283

        self.edit_menu_search.text = _bind(    # edit_window.nml:286
            lambda _o: _tr('~S~earch'),
            yielding=True,
        )

        _w27.text = _bind(lambda _o: _tr('Find ~b~ar'), yielding=True)    # edit_window.nml:289
        _w27.tooltip = _bind(    # edit_window.nml:290
            lambda _o: _tr('Search as you type, in a bar over the text'),
            yielding=True,
        )
        _w27.command = ShowFindBar    # edit_window.nml:291
        _w27.key = 'Ctrl-F'    # edit_window.nml:292

        _w28.text = _bind(lambda _o: _tr('Replace b~a~r'), yielding=True)    # edit_window.nml:294
        _w28.command = ShowReplaceBar    # edit_window.nml:295
        _w28.key = 'Ctrl-R'    # edit_window.nml:296

        _w30.text = _bind(lambda _o: _tr('~F~ind...'), yielding=True)    # edit_window.nml:299
        _w30.command = StartSearch    # edit_window.nml:300
        _w30.key = 'F7'    # edit_window.nml:301

        _w31.text = _bind(lambda _o: _tr('~R~eplace...'), yielding=True)    # edit_window.nml:303
        _w31.command = Replace    # edit_window.nml:304
        _w31.key = 'Ctrl-F7'    # edit_window.nml:305

        _w32.text = _bind(lambda _o: _tr('~S~earch again'), yielding=True)    # edit_window.nml:307
        _w32.command = ContSearch    # edit_window.nml:308
        _w32.key = 'Shift-F7'    # edit_window.nml:309

        _w33.text = _bind(lambda _o: _tr('Re~v~ersed search'), yielding=True)    # edit_window.nml:311
        _w33.command = ReverseSearch    # edit_window.nml:312
        _w33.key = 'Alt-F7'    # edit_window.nml:313

        _w34.text = _bind(    # edit_window.nml:315
            lambda _o: _tr('~G~o to line number...'),
            yielding=True,
        )
        _w34.command = GotoLineNumber    # edit_window.nml:316
        _w34.key = 'Alt-G'    # edit_window.nml:317

        _w35.text = _bind(lambda _o: _tr('~M~atching bracket'), yielding=True)    # edit_window.nml:320
        _w35.tooltip = _bind(    # edit_window.nml:321
            lambda _o: _tr('Jump to the bracket that pairs with the one at the cursor'),
            yielding=True,
        )
        _w35.command = BracketPair    # edit_window.nml:322
        _w35.key = 'Alt-Left'    # edit_window.nml:323

        self.edit_menu_place_marker.text = _bind(    # edit_window.nml:330
            lambda _o: _tr('Pla~c~e marker'),
            yielding=True,
        )
        self.edit_menu_place_marker.tooltip = _bind(    # edit_window.nml:331
            lambda _o: _tr("Keep the cursor's place as one of nine markers"),
            yielding=True,
        )

        _w37.text = _bind(lambda _o: _tr('Marker ~1~'), yielding=True)    # edit_window.nml:333
        _w37.tooltip = _bind(    # edit_window.nml:334
            lambda _o: _tr("Keep the cursor's place as marker 1"),
            yielding=True,
        )
        _w37.command = PlaceMarker(1)    # edit_window.nml:335

        _w38.text = _bind(lambda _o: _tr('Marker ~2~'), yielding=True)    # edit_window.nml:337
        _w38.tooltip = _bind(    # edit_window.nml:338
            lambda _o: _tr("Keep the cursor's place as marker 2"),
            yielding=True,
        )
        _w38.command = PlaceMarker(2)    # edit_window.nml:339

        _w39.text = _bind(lambda _o: _tr('Marker ~3~'), yielding=True)    # edit_window.nml:341
        _w39.tooltip = _bind(    # edit_window.nml:342
            lambda _o: _tr("Keep the cursor's place as marker 3"),
            yielding=True,
        )
        _w39.command = PlaceMarker(3)    # edit_window.nml:343

        _w40.text = _bind(lambda _o: _tr('Marker ~4~'), yielding=True)    # edit_window.nml:345
        _w40.tooltip = _bind(    # edit_window.nml:346
            lambda _o: _tr("Keep the cursor's place as marker 4"),
            yielding=True,
        )
        _w40.command = PlaceMarker(4)    # edit_window.nml:347

        _w41.text = _bind(lambda _o: _tr('Marker ~5~'), yielding=True)    # edit_window.nml:349
        _w41.tooltip = _bind(    # edit_window.nml:350
            lambda _o: _tr("Keep the cursor's place as marker 5"),
            yielding=True,
        )
        _w41.command = PlaceMarker(5)    # edit_window.nml:351

        _w42.text = _bind(lambda _o: _tr('Marker ~6~'), yielding=True)    # edit_window.nml:353
        _w42.tooltip = _bind(    # edit_window.nml:354
            lambda _o: _tr("Keep the cursor's place as marker 6"),
            yielding=True,
        )
        _w42.command = PlaceMarker(6)    # edit_window.nml:355

        _w43.text = _bind(lambda _o: _tr('Marker ~7~'), yielding=True)    # edit_window.nml:357
        _w43.tooltip = _bind(    # edit_window.nml:358
            lambda _o: _tr("Keep the cursor's place as marker 7"),
            yielding=True,
        )
        _w43.command = PlaceMarker(7)    # edit_window.nml:359

        _w44.text = _bind(lambda _o: _tr('Marker ~8~'), yielding=True)    # edit_window.nml:361
        _w44.tooltip = _bind(    # edit_window.nml:362
            lambda _o: _tr("Keep the cursor's place as marker 8"),
            yielding=True,
        )
        _w44.command = PlaceMarker(8)    # edit_window.nml:363

        _w45.text = _bind(lambda _o: _tr('Marker ~9~'), yielding=True)    # edit_window.nml:365
        _w45.tooltip = _bind(    # edit_window.nml:366
            lambda _o: _tr("Keep the cursor's place as marker 9"),
            yielding=True,
        )
        _w45.command = PlaceMarker(9)    # edit_window.nml:367

        self.edit_menu_goto_marker.text = _bind(    # edit_window.nml:370
            lambda _o: _tr('G~o~ to marker'),
            yielding=True,
        )
        self.edit_menu_goto_marker.tooltip = _bind(    # edit_window.nml:371
            lambda _o: _tr('Take the cursor back to a place kept as a marker'),
            yielding=True,
        )

        _w46.text = _bind(lambda _o: _tr('Marker ~1~'), yielding=True)    # edit_window.nml:373
        _w46.tooltip = _bind(    # edit_window.nml:374
            lambda _o: _tr('Take the cursor back to marker 1'),
            yielding=True,
        )
        _w46.command = GotoMarker(1)    # edit_window.nml:375

        _w47.text = _bind(lambda _o: _tr('Marker ~2~'), yielding=True)    # edit_window.nml:377
        _w47.tooltip = _bind(    # edit_window.nml:378
            lambda _o: _tr('Take the cursor back to marker 2'),
            yielding=True,
        )
        _w47.command = GotoMarker(2)    # edit_window.nml:379

        _w48.text = _bind(lambda _o: _tr('Marker ~3~'), yielding=True)    # edit_window.nml:381
        _w48.tooltip = _bind(    # edit_window.nml:382
            lambda _o: _tr('Take the cursor back to marker 3'),
            yielding=True,
        )
        _w48.command = GotoMarker(3)    # edit_window.nml:383

        _w49.text = _bind(lambda _o: _tr('Marker ~4~'), yielding=True)    # edit_window.nml:385
        _w49.tooltip = _bind(    # edit_window.nml:386
            lambda _o: _tr('Take the cursor back to marker 4'),
            yielding=True,
        )
        _w49.command = GotoMarker(4)    # edit_window.nml:387

        _w50.text = _bind(lambda _o: _tr('Marker ~5~'), yielding=True)    # edit_window.nml:389
        _w50.tooltip = _bind(    # edit_window.nml:390
            lambda _o: _tr('Take the cursor back to marker 5'),
            yielding=True,
        )
        _w50.command = GotoMarker(5)    # edit_window.nml:391

        _w51.text = _bind(lambda _o: _tr('Marker ~6~'), yielding=True)    # edit_window.nml:393
        _w51.tooltip = _bind(    # edit_window.nml:394
            lambda _o: _tr('Take the cursor back to marker 6'),
            yielding=True,
        )
        _w51.command = GotoMarker(6)    # edit_window.nml:395

        _w52.text = _bind(lambda _o: _tr('Marker ~7~'), yielding=True)    # edit_window.nml:397
        _w52.tooltip = _bind(    # edit_window.nml:398
            lambda _o: _tr('Take the cursor back to marker 7'),
            yielding=True,
        )
        _w52.command = GotoMarker(7)    # edit_window.nml:399

        _w53.text = _bind(lambda _o: _tr('Marker ~8~'), yielding=True)    # edit_window.nml:401
        _w53.tooltip = _bind(    # edit_window.nml:402
            lambda _o: _tr('Take the cursor back to marker 8'),
            yielding=True,
        )
        _w53.command = GotoMarker(8)    # edit_window.nml:403

        _w54.text = _bind(lambda _o: _tr('Marker ~9~'), yielding=True)    # edit_window.nml:405
        _w54.tooltip = _bind(    # edit_window.nml:406
            lambda _o: _tr('Take the cursor back to marker 9'),
            yielding=True,
        )
        _w54.command = GotoMarker(9)    # edit_window.nml:407

        self.edit_menu_paragraph.text = _bind(    # edit_window.nml:410
            lambda _o: _tr('Pa~r~agraph'),
            yielding=True,
        )

        _w55.text = _bind(lambda _o: _tr('~J~ustify'), yielding=True)    # edit_window.nml:412
        _w55.tooltip = _bind(    # edit_window.nml:413
            lambda _o: _tr("Justify the block's paragraph to both margins"),
            yielding=True,
        )
        _w55.command = FJustify    # edit_window.nml:414
        _w55.key = 'Alt-J'    # edit_window.nml:415

        _w56.text = _bind(lambda _o: _tr('~R~ight'), yielding=True)    # edit_window.nml:417
        _w56.command = FRight    # edit_window.nml:418
        _w56.key = 'Alt-R'    # edit_window.nml:419

        _w57.text = _bind(lambda _o: _tr('~L~eft'), yielding=True)    # edit_window.nml:421
        _w57.command = FLeft    # edit_window.nml:422
        _w57.key = 'Alt-L'    # edit_window.nml:423

        _w58.text = _bind(lambda _o: _tr('~C~enter'), yielding=True)    # edit_window.nml:425
        _w58.command = FCenter    # edit_window.nml:426
        _w58.key = 'Alt-C'    # edit_window.nml:427

        self.edit_menu_line_format.text = _bind(    # edit_window.nml:434
            lambda _o: _tr('Current li~n~e'),
            yielding=True,
        )
        self.edit_menu_line_format.tooltip = _bind(    # edit_window.nml:435
            lambda _o: _tr("Format the cursor's line alone"),
            yielding=True,
        )

        _w59.text = _bind(lambda _o: _tr('~J~ustify'), yielding=True)    # edit_window.nml:437
        _w59.tooltip = _bind(    # edit_window.nml:438
            lambda _o: _tr("Justify the cursor's line to both margins"),
            yielding=True,
        )
        _w59.command = LJustify    # edit_window.nml:439

        _w60.text = _bind(lambda _o: _tr('~R~ight'), yielding=True)    # edit_window.nml:441
        _w60.tooltip = _bind(    # edit_window.nml:442
            lambda _o: _tr("Put the cursor's line against the right margin"),
            yielding=True,
        )
        _w60.command = LRight    # edit_window.nml:443

        _w61.text = _bind(lambda _o: _tr('~L~eft'), yielding=True)    # edit_window.nml:445
        _w61.tooltip = _bind(    # edit_window.nml:446
            lambda _o: _tr("Put the cursor's line at the left margin"),
            yielding=True,
        )
        _w61.command = LLeft    # edit_window.nml:447

        _w62.text = _bind(lambda _o: _tr('~C~enter'), yielding=True)    # edit_window.nml:449
        _w62.tooltip = _bind(    # edit_window.nml:450
            lambda _o: _tr("Center the cursor's line between the margins"),
            yielding=True,
        )
        _w62.command = LCenter    # edit_window.nml:451

        _w64.text = _bind(lambda _o: _tr('~M~argins...'), yielding=True)    # edit_window.nml:454
        _w64.command = SetMargins    # edit_window.nml:455

        self.edit_menu_block.text = _bind(    # edit_window.nml:458
            lambda _o: _tr('~B~lock'),
            yielding=True,
        )

        _w65.text = _bind(lambda _o: _tr('Mar~k~ start'), yielding=True)    # edit_window.nml:463
        _w65.tooltip = _bind(    # edit_window.nml:464
            lambda _o: _tr('Begin the block at the cursor'),
            yielding=True,
        )
        _w65.command = BlockStart    # edit_window.nml:465

        _w66.text = _bind(lambda _o: _tr('Mark ~e~nd'), yielding=True)    # edit_window.nml:467
        _w66.tooltip = _bind(    # edit_window.nml:468
            lambda _o: _tr('End the block at the cursor'),
            yielding=True,
        )
        _w66.command = BlockEnd    # edit_window.nml:469

        _w67.text = _bind(lambda _o: _tr('Mark ~w~ord'), yielding=True)    # edit_window.nml:471
        _w67.tooltip = _bind(    # edit_window.nml:472
            lambda _o: _tr('Mark the word at the cursor as the block'),
            yielding=True,
        )
        _w67.command = MarkWord    # edit_window.nml:473

        _w68.text = _bind(lambda _o: _tr('Mark li~n~e'), yielding=True)    # edit_window.nml:475
        _w68.tooltip = _bind(    # edit_window.nml:476
            lambda _o: _tr("Mark the cursor's line as the block"),
            yielding=True,
        )
        _w68.command = MarkLine    # edit_window.nml:477

        _w70.text = _bind(lambda _o: _tr('~G~o to block start'), yielding=True)    # edit_window.nml:480
        _w70.tooltip = _bind(    # edit_window.nml:481
            lambda _o: _tr('Take the cursor to where the block begins'),
            yielding=True,
        )
        _w70.command = MoveBlockStart    # edit_window.nml:482

        _w71.text = _bind(lambda _o: _tr('Go to block en~d~'), yielding=True)    # edit_window.nml:484
        _w71.tooltip = _bind(    # edit_window.nml:485
            lambda _o: _tr('Take the cursor to where the block ends'),
            yielding=True,
        )
        _w71.command = MoveBlockEnd    # edit_window.nml:486

        _w73.text = _bind(lambda _o: _tr('~M~ove'), yielding=True)    # edit_window.nml:489
        _w73.command = MoveBlock    # edit_window.nml:490
        _w73.key = 'Alt-Shift-V'    # edit_window.nml:491

        _w74.text = _bind(lambda _o: _tr('~C~opy'), yielding=True)    # edit_window.nml:493
        _w74.command = CopyBlock    # edit_window.nml:494
        _w74.key = 'Alt-Shift-K'    # edit_window.nml:495

        _w75.text = _bind(lambda _o: _tr('~I~ndent'), yielding=True)    # edit_window.nml:497
        _w75.command = IndentBlock    # edit_window.nml:498
        _w75.key = 'Alt-Shift-I'    # edit_window.nml:499

        _w76.text = _bind(lambda _o: _tr('~U~nindent'), yielding=True)    # edit_window.nml:501
        _w76.command = UnindentBlock    # edit_window.nml:502
        _w76.key = 'Alt-Shift-O'    # edit_window.nml:503

        _w77.text = _bind(lambda _o: _tr('~H~ide/show block'), yielding=True)    # edit_window.nml:506
        _w77.tooltip = _bind(    # edit_window.nml:507
            lambda _o: _tr('Hide the marked block, or show it again'),
            yielding=True,
        )
        _w77.command = HideBlock    # edit_window.nml:508
        _w77.key = 'Alt-H'    # edit_window.nml:509

        _w79.text = _bind(lambda _o: _tr('U~p~percase'), yielding=True)    # edit_window.nml:512
        _w79.command = UpcaseBlock    # edit_window.nml:513
        _w79.key = 'Alt-Shift-U'    # edit_window.nml:514

        _w80.text = _bind(lambda _o: _tr('~L~owercase'), yielding=True)    # edit_window.nml:516
        _w80.command = LowcaseBlock    # edit_window.nml:517
        _w80.key = 'Alt-Shift-L'    # edit_window.nml:518

        _w81.text = _bind(lambda _o: _tr('Capi~t~alize'), yielding=True)    # edit_window.nml:520
        _w81.command = CapitalizeBlock    # edit_window.nml:521
        _w81.key = 'Alt-Shift-C'    # edit_window.nml:522

        _w83.text = _bind(lambda _o: _tr('~S~ort'), yielding=True)    # edit_window.nml:525
        _w83.tooltip = _bind(    # edit_window.nml:526
            lambda _o: _tr('Sort the lines by the column block'),
            yielding=True,
        )
        _w83.command = SortBlock    # edit_window.nml:527
        _w83.key = 'Alt-T'    # edit_window.nml:528

        _w84.text = _bind(lambda _o: _tr('C~a~lculate sum'), yielding=True)    # edit_window.nml:531
        _w84.tooltip = _bind(    # edit_window.nml:532
            lambda _o: _tr("Add up the column block's numbers; the sum goes to the clipboard"),
            yielding=True,
        )
        _w84.command = CalcBlock    # edit_window.nml:533
        _w84.key = 'Alt-Ins'    # edit_window.nml:534

        self.edit_menu_misc.text = _bind(    # edit_window.nml:537
            lambda _o: _tr('~M~isc'),
            yielding=True,
        )

        _w85.text = _bind(lambda _o: _tr('Insert ~d~ate'), yielding=True)    # edit_window.nml:539
        _w85.command = InsertDate    # edit_window.nml:540
        _w85.key = 'Alt-Shift-D'    # edit_window.nml:541

        _w86.text = _bind(lambda _o: _tr('Insert ~t~ime'), yielding=True)    # edit_window.nml:543
        _w86.command = InsertTime    # edit_window.nml:544
        _w86.key = 'Alt-Shift-T'    # edit_window.nml:545

        _w87.text = _bind(lambda _o: _tr('Du~p~licate line'), yielding=True)    # edit_window.nml:547
        _w87.command = DuplicateLine    # edit_window.nml:548
        _w87.key = 'F6'    # edit_window.nml:549

        _w88.text = _bind(lambda _o: _tr('Character ta~b~le'), yielding=True)    # edit_window.nml:551
        _w88.command = AsciiTable    # edit_window.nml:552
        _w88.key = 'Ctrl P'    # edit_window.nml:553

        _w89.text = _bind(lambda _o: _tr('Line Dra~w~ing'), yielding=True)    # edit_window.nml:555
        _w89.tooltip = _bind(    # edit_window.nml:556
            lambda _o: _tr('Draw lines with the arrow keys: off, single, double'),
            yielding=True,
        )
        _w89.command = SwitchDrawMode    # edit_window.nml:557
        _w89.key = 'F4'    # edit_window.nml:558

        self.edit_menu_misc_uppercase.text = _bind(    # edit_window.nml:562
            lambda _o: _tr('~U~ppercase'),
            yielding=True,
        )

        _w91.text = _bind(lambda _o: _tr('~W~ord'), yielding=True)    # edit_window.nml:564
        _w91.command = UpWord    # edit_window.nml:565
        _w91.key = 'Ctrl ['    # edit_window.nml:566

        _w92.text = _bind(lambda _o: _tr('~L~ine'), yielding=True)    # edit_window.nml:568
        _w92.command = UpString    # edit_window.nml:569
        _w92.key = 'Ctrl+Shift ['    # edit_window.nml:570

        _w93.text = _bind(lambda _o: _tr('~B~lock'), yielding=True)    # edit_window.nml:572
        _w93.command = UpcaseBlock    # edit_window.nml:573
        _w93.key = 'Alt-Shift-U'    # edit_window.nml:574

        self.edit_menu_misc_lowercase.text = _bind(    # edit_window.nml:577
            lambda _o: _tr('~L~owercase'),
            yielding=True,
        )

        _w94.text = _bind(lambda _o: _tr('~W~ord'), yielding=True)    # edit_window.nml:579
        _w94.command = LowWord    # edit_window.nml:580
        _w94.key = 'Ctrl ]'    # edit_window.nml:581

        _w95.text = _bind(lambda _o: _tr('~L~ine'), yielding=True)    # edit_window.nml:583
        _w95.command = LowString    # edit_window.nml:584
        _w95.key = 'Ctrl+Shift ]'    # edit_window.nml:585

        _w96.text = _bind(lambda _o: _tr('~B~lock'), yielding=True)    # edit_window.nml:587
        _w96.command = LowcaseBlock    # edit_window.nml:588
        _w96.key = 'Alt-Shift-L'    # edit_window.nml:589

        self.edit_menu_misc_capitalize.text = _bind(    # edit_window.nml:592
            lambda _o: _tr('~C~apitalize'),
            yielding=True,
        )

        _w97.text = _bind(lambda _o: _tr('~W~ord'), yielding=True)    # edit_window.nml:594
        _w97.command = CapWord    # edit_window.nml:595
        _w97.key = 'Ctrl \\'    # edit_window.nml:596

        _w98.text = _bind(lambda _o: _tr('~L~ine'), yielding=True)    # edit_window.nml:598
        _w98.command = CapString    # edit_window.nml:599
        _w98.key = 'Ctrl+Shift \\'    # edit_window.nml:600

        _w99.text = _bind(lambda _o: _tr('~B~lock'), yielding=True)    # edit_window.nml:602
        _w99.command = CapitalizeBlock    # edit_window.nml:603
        _w99.key = 'Alt-Shift-C'    # edit_window.nml:604

        self.edit_menu_options.text = _bind(    # edit_window.nml:607
            lambda _o: _tr('Optio~n~s'),
            yielding=True,
        )

        _w100.text = _bind(    # edit_window.nml:609
            lambda _o: _tr('~B~ackspace indents'),
            yielding=True,
        )
        _w100.tooltip = _bind(    # edit_window.nml:610
            lambda _o: _tr("Backspace at a line's start goes back to an indent above"),
            yielding=True,
        )
        _w100.command = SwitchBack    # edit_window.nml:611

        _w101.text = _bind(lambda _o: _tr('AutoB~r~ackets'), yielding=True)    # edit_window.nml:613
        _w101.command = SwitchBrackets    # edit_window.nml:614

        _w102.text = _bind(lambda _o: _tr('Auto~i~ndent'), yielding=True)    # edit_window.nml:616
        _w102.command = SwitchIndent    # edit_window.nml:617

        _w103.text = _bind(lambda _o: _tr('~A~uto wrap'), yielding=True)    # edit_window.nml:619
        _w103.command = SwitchSave    # edit_window.nml:620

        _w104.text = _bind(lambda _o: _tr('~J~ustify on wrap'), yielding=True)    # edit_window.nml:622
        _w104.tooltip = _bind(    # edit_window.nml:623
            lambda _o: _tr('Widen a wrapped line to the margin'),
            yielding=True,
        )
        _w104.command = SwitchWrap    # edit_window.nml:624

        _w105.text = _bind(lambda _o: _tr('~V~ertical blocks'), yielding=True)    # edit_window.nml:626
        _w105.tooltip = _bind(    # edit_window.nml:627
            lambda _o: _tr('Mark column blocks instead of line ones'),
            yielding=True,
        )
        _w105.command = SwitchBlock    # edit_window.nml:628

        _w106.text = _bind(lambda _o: _tr('Opti~m~al fill'), yielding=True)    # edit_window.nml:630
        _w106.tooltip = _bind(    # edit_window.nml:631
            lambda _o: _tr('Write blanks as tabs where they reach a tab stop'),
            yielding=True,
        )
        _w106.command = SwitchFill    # edit_window.nml:632

        _w107.text = _bind(    # edit_window.nml:634
            lambda _o: _tr('Current ~l~ine highlight'),
            yielding=True,
        )
        _w107.command = SwitchHiLine    # edit_window.nml:635

        _w108.text = _bind(    # edit_window.nml:637
            lambda _o: _tr('Current ~c~olumn highlight'),
            yielding=True,
        )
        _w108.command = SwitchHiColumn    # edit_window.nml:638

        _w109.text = _bind(lambda _o: _tr('Syntax ~h~ighlight'), yielding=True)    # edit_window.nml:640
        _w109.command = SwitchHighLight    # edit_window.nml:641

        _w110.text = _bind(    # edit_window.nml:644
            lambda _o: _tr('Show hi~d~den characters'),
            yielding=True,
        )
        _w110.command = SwitchHiddenChars    # edit_window.nml:645

        self.edit_menu_file_type.text = _bind(    # edit_window.nml:652
            lambda _o: _tr('File t~y~pe'),
            yielding=True,
        )
        self.edit_menu_file_type.key_command = ChooseFileType    # edit_window.nml:653

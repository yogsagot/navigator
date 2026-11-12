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
from navigator.commands import NewView, PrintFile    # edit_window.nml:2
from navigator.widgets.manager.commands import Calculator, EditNamed    # edit_window.nml:3
from navigator.widgets.editor.commands import BlockStart, BlockEnd, MarkWord, MarkLine, MoveBlockStart, MoveBlockEnd, PlaceMarker, GotoMarker, DeleteWordRight, DeleteToEnd, ChooseEncoding, ChooseLineEnding, ChooseFileType, AsciiTable, CalcBlock, SwitchHiColumn, SwitchHiLine, SwitchHighLight, SwitchHiddenChars, SwitchFill, SwitchTabs, SwitchLineNumbers, SwitchSoftWrap, ShowFindBar, ShowReplaceBar, CapString, CapWord, LowString, LowWord, UpString, UpWord, DuplicateLine, DeleteLine, DeleteWordLeft, InsertLine, HideBlock, BracketPair, SwitchDrawMode, SwitchBack, SwitchIndent, SwitchBrackets, SwitchSave, SwitchWrap, FCenter, FJustify, FLeft, FRight, LCenter, LJustify, LLeft, LRight, SetMargins, ContSearch, LoadText, Replace, ReverseSearch, StartSearch, SaveAll, SaveTextAs, CapitalizeBlock, Clear, ClipboardCopy, ClipboardCut, ClipboardPaste, CopyBlock, GotoLineNumber, PrintBlock, IndentBlock, InsertDate, InsertTime, BlockRead, BlockWrite, LowcaseBlock, MoveBlock, SaveText, SortBlock, UnindentBlock, Undo, Redo, UpcaseBlock, SwitchBlock    # edit_window.nml:4
from navigator.widgets.editor.file_editor import FileEditor, FormatMarks, InfoLine, LineGutter, gutter_width    # edit_window.nml:5
from navigator.widgets.editor.find_bar import FindBar    # edit_window.nml:6
from navigator.settings import SETTINGS    # edit_window.nml:7
from navml.commands import CloseWindow    # edit_window.nml:8
from navml.widgets.menu.commands import MainMenu    # edit_window.nml:9
from navml.widgets.option_strip import OptionStrip    # edit_window.nml:10
from navml.widgets.dialog.scroll_bar import ScrollBar    # edit_window.nml:11
from navml.widgets.menu.menu_item import MenuItem    # edit_window.nml:12
from navml.widgets.menu.menu_line import MenuLine    # edit_window.nml:13
from navml.widgets.menu.sub_menu import SubMenu    # edit_window.nml:14
from navml.widgets.window import Window    # edit_window.nml:15

__navml_component__ = "EditWindow"

__all__ = ["EditWindow"]


class EditWindow(Window, _Component):
    """F4: DOS Navigator's ``TEditWindow`` (``MICROED.PAS``).

    A standard window titled ``Edit - `` and the file's path, the editor filling
    the inside of its frame, a vertical scroll bar on the right frame column, a
    horizontal one along the bottom frame, and ``TInfoLine`` over the bottom
    frame's left end -- the views ``TEditWindow.Init`` inserts, in the places it
    puts them.  **It opens zoomed**, as the viewer does -- unless *Store editor
    position* has a last editor rectangle (``file_history.place_last_edit``).

    Both scroll bars and the info line show only while the window is active, as
    ``TFileEditor.SetState`` hid the bars and ``TInfoLine.Draw`` drew nothing.
    """

    #: The document this class was generated from.
    __navml_source__ = "edit_window.nml"

    #: ``StatusDef hcEditor``: what it captions.  The editing keys are the
    #: editor's own table, and Esc and Alt+F3 close the window, asking first
    #: about a text that has changed.
    keys = {    # edit_window.nml:34
        'escape': CloseWindow,    # edit_window.nml:35
        'alt+f3': CloseWindow,    # edit_window.nml:36
        'f2': SaveText,    # edit_window.nml:37
        'ctrl+s': SaveText,    # edit_window.nml:40
        'f3': LoadText,    # edit_window.nml:41
        'shift+f2': SaveTextAs,    # edit_window.nml:42
        'ctrl+f2': SaveAll,    # edit_window.nml:43
        'f7': StartSearch,    # edit_window.nml:47
        'alt+f7': ReverseSearch,    # edit_window.nml:48
        'ctrl+f7': Replace,    # edit_window.nml:49
        'shift+f7': ContSearch,    # edit_window.nml:50
        'ctrl+l': ContSearch,    # edit_window.nml:51
        'ctrl+f6': Calculator,    # edit_window.nml:54
        'shift+f4': EditNamed,    # edit_window.nml:55
        'ctrl+shift+h': ChooseFileType,    # edit_window.nml:58
        'ctrl+shift+8': SwitchHiddenChars,    # edit_window.nml:61
        'f8': PrintFile,    # edit_window.nml:64
        'shift+f8': PrintBlock,    # edit_window.nml:65
    }

    #: Ids, annotated so the hand-written half completes them.
    gutter: LineGutter    # edit_window.nml:73
    editor: FileEditor    # edit_window.nml:83
    find_bar: FindBar    # edit_window.nml:94
    vbar: ScrollBar    # edit_window.nml:104
    hbar: ScrollBar    # edit_window.nml:125
    info: InfoLine    # edit_window.nml:140
    marks: FormatMarks    # edit_window.nml:155
    options: OptionStrip    # edit_window.nml:170
    edit_menu: SubMenu    # edit_window.nml:200
    edit_menu_delete: SubMenu    # edit_window.nml:225
    edit_menu_file: SubMenu    # edit_window.nml:236
    edit_menu_line_endings: SubMenu    # edit_window.nml:248
    edit_menu_encoding: SubMenu    # edit_window.nml:250
    edit_menu_search: SubMenu    # edit_window.nml:259
    edit_menu_place_marker: SubMenu    # edit_window.nml:278
    edit_menu_goto_marker: SubMenu    # edit_window.nml:299
    edit_menu_paragraph: SubMenu    # edit_window.nml:320
    edit_menu_line_format: SubMenu    # edit_window.nml:331
    edit_menu_block: SubMenu    # edit_window.nml:344
    edit_menu_misc: SubMenu    # edit_window.nml:380
    edit_menu_misc_uppercase: SubMenu    # edit_window.nml:389
    edit_menu_misc_lowercase: SubMenu    # edit_window.nml:394
    edit_menu_misc_capitalize: SubMenu    # edit_window.nml:399
    edit_menu_options: SubMenu    # edit_window.nml:404
    edit_menu_file_type: SubMenu    # edit_window.nml:435

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_vbar_scroll(self, event: _Event) -> bool:    # edit_window.nml:104
        """``vbar`` raised an event whose handler is ``on_scroll``."""
        return False

    async def on_hbar_scroll(self, event: _Event) -> bool:    # edit_window.nml:125
        """``hbar`` raised an event whose handler is ``on_scroll``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.gutter = LineGutter(parent=self)    # edit_window.nml:72
        self.editor = FileEditor(parent=self)    # edit_window.nml:82
        self.find_bar = FindBar(parent=self)    # edit_window.nml:93
        self.vbar = ScrollBar(parent=self)    # edit_window.nml:103
        self.hbar = ScrollBar(parent=self)    # edit_window.nml:124
        self.info = InfoLine(parent=self)    # edit_window.nml:139
        self.marks = FormatMarks(parent=self)    # edit_window.nml:154
        self.options = OptionStrip(parent=self)    # edit_window.nml:169
        self.edit_menu = SubMenu(parent=self)    # edit_window.nml:199
        _w1 = MenuItem(parent=self.edit_menu)    # edit_window.nml:206
        _w2 = MenuItem(parent=self.edit_menu)    # edit_window.nml:207
        _w3 = MenuLine(parent=self.edit_menu)    # edit_window.nml:208
        _w4 = MenuItem(parent=self.edit_menu)    # edit_window.nml:209
        _w5 = MenuItem(parent=self.edit_menu)    # edit_window.nml:210
        _w6 = MenuItem(parent=self.edit_menu)    # edit_window.nml:211
        _w7 = MenuItem(parent=self.edit_menu)    # edit_window.nml:212
        _w8 = MenuItem(parent=self.edit_menu)    # edit_window.nml:214
        _w9 = MenuLine(parent=self.edit_menu)    # edit_window.nml:216
        _w10 = MenuItem(parent=self.edit_menu)    # edit_window.nml:217
        self.edit_menu_delete = SubMenu(parent=self.edit_menu)    # edit_window.nml:224
        _w11 = MenuItem(parent=self.edit_menu_delete)    # edit_window.nml:227
        _w12 = MenuItem(parent=self.edit_menu_delete)    # edit_window.nml:228
        _w13 = MenuItem(parent=self.edit_menu_delete)    # edit_window.nml:229
        _w14 = MenuItem(parent=self.edit_menu_delete)    # edit_window.nml:231
        _w15 = MenuItem(parent=self.edit_menu)    # edit_window.nml:233
        _w16 = MenuLine(parent=self.edit_menu)    # edit_window.nml:234
        self.edit_menu_file = SubMenu(parent=self.edit_menu)    # edit_window.nml:235
        _w17 = MenuItem(parent=self.edit_menu_file)    # edit_window.nml:237
        _w18 = MenuItem(parent=self.edit_menu_file)    # edit_window.nml:238
        _w19 = MenuItem(parent=self.edit_menu_file)    # edit_window.nml:239
        _w20 = MenuItem(parent=self.edit_menu_file)    # edit_window.nml:240
        _w21 = MenuItem(parent=self.edit_menu_file)    # edit_window.nml:242
        _w22 = MenuLine(parent=self.edit_menu_file)    # edit_window.nml:244
        self.edit_menu_line_endings = SubMenu(parent=self.edit_menu_file)    # edit_window.nml:247
        self.edit_menu_encoding = SubMenu(parent=self.edit_menu_file)    # edit_window.nml:249
        _w23 = MenuLine(parent=self.edit_menu_file)    # edit_window.nml:251
        _w24 = MenuItem(parent=self.edit_menu_file)    # edit_window.nml:252
        _w25 = MenuItem(parent=self.edit_menu_file)    # edit_window.nml:253
        _w26 = MenuLine(parent=self.edit_menu_file)    # edit_window.nml:254
        _w27 = MenuItem(parent=self.edit_menu_file)    # edit_window.nml:256
        _w28 = MenuItem(parent=self.edit_menu_file)    # edit_window.nml:257
        self.edit_menu_search = SubMenu(parent=self.edit_menu)    # edit_window.nml:258
        _w29 = MenuItem(parent=self.edit_menu_search)    # edit_window.nml:261
        _w30 = MenuItem(parent=self.edit_menu_search)    # edit_window.nml:263
        _w31 = MenuLine(parent=self.edit_menu_search)    # edit_window.nml:264
        _w32 = MenuItem(parent=self.edit_menu_search)    # edit_window.nml:265
        _w33 = MenuItem(parent=self.edit_menu_search)    # edit_window.nml:266
        _w34 = MenuItem(parent=self.edit_menu_search)    # edit_window.nml:267
        _w35 = MenuItem(parent=self.edit_menu_search)    # edit_window.nml:268
        _w36 = MenuItem(parent=self.edit_menu_search)    # edit_window.nml:269
        _w37 = MenuItem(parent=self.edit_menu_search)    # edit_window.nml:271
        _w38 = MenuLine(parent=self.edit_menu_search)    # edit_window.nml:276
        self.edit_menu_place_marker = SubMenu(parent=self.edit_menu_search)    # edit_window.nml:277
        _w39 = MenuItem(parent=self.edit_menu_place_marker)    # edit_window.nml:280
        _w40 = MenuItem(parent=self.edit_menu_place_marker)    # edit_window.nml:282
        _w41 = MenuItem(parent=self.edit_menu_place_marker)    # edit_window.nml:284
        _w42 = MenuItem(parent=self.edit_menu_place_marker)    # edit_window.nml:286
        _w43 = MenuItem(parent=self.edit_menu_place_marker)    # edit_window.nml:288
        _w44 = MenuItem(parent=self.edit_menu_place_marker)    # edit_window.nml:290
        _w45 = MenuItem(parent=self.edit_menu_place_marker)    # edit_window.nml:292
        _w46 = MenuItem(parent=self.edit_menu_place_marker)    # edit_window.nml:294
        _w47 = MenuItem(parent=self.edit_menu_place_marker)    # edit_window.nml:296
        self.edit_menu_goto_marker = SubMenu(parent=self.edit_menu_search)    # edit_window.nml:298
        _w48 = MenuItem(parent=self.edit_menu_goto_marker)    # edit_window.nml:301
        _w49 = MenuItem(parent=self.edit_menu_goto_marker)    # edit_window.nml:303
        _w50 = MenuItem(parent=self.edit_menu_goto_marker)    # edit_window.nml:305
        _w51 = MenuItem(parent=self.edit_menu_goto_marker)    # edit_window.nml:307
        _w52 = MenuItem(parent=self.edit_menu_goto_marker)    # edit_window.nml:309
        _w53 = MenuItem(parent=self.edit_menu_goto_marker)    # edit_window.nml:311
        _w54 = MenuItem(parent=self.edit_menu_goto_marker)    # edit_window.nml:313
        _w55 = MenuItem(parent=self.edit_menu_goto_marker)    # edit_window.nml:315
        _w56 = MenuItem(parent=self.edit_menu_goto_marker)    # edit_window.nml:317
        self.edit_menu_paragraph = SubMenu(parent=self.edit_menu)    # edit_window.nml:319
        _w57 = MenuItem(parent=self.edit_menu_paragraph)    # edit_window.nml:321
        _w58 = MenuItem(parent=self.edit_menu_paragraph)    # edit_window.nml:323
        _w59 = MenuItem(parent=self.edit_menu_paragraph)    # edit_window.nml:324
        _w60 = MenuItem(parent=self.edit_menu_paragraph)    # edit_window.nml:325
        self.edit_menu_line_format = SubMenu(parent=self.edit_menu_paragraph)    # edit_window.nml:330
        _w61 = MenuItem(parent=self.edit_menu_line_format)    # edit_window.nml:333
        _w62 = MenuItem(parent=self.edit_menu_line_format)    # edit_window.nml:335
        _w63 = MenuItem(parent=self.edit_menu_line_format)    # edit_window.nml:337
        _w64 = MenuItem(parent=self.edit_menu_line_format)    # edit_window.nml:339
        _w65 = MenuLine(parent=self.edit_menu_paragraph)    # edit_window.nml:341
        _w66 = MenuItem(parent=self.edit_menu_paragraph)    # edit_window.nml:342
        self.edit_menu_block = SubMenu(parent=self.edit_menu)    # edit_window.nml:343
        _w67 = MenuItem(parent=self.edit_menu_block)    # edit_window.nml:348
        _w68 = MenuItem(parent=self.edit_menu_block)    # edit_window.nml:350
        _w69 = MenuItem(parent=self.edit_menu_block)    # edit_window.nml:352
        _w70 = MenuItem(parent=self.edit_menu_block)    # edit_window.nml:354
        _w71 = MenuLine(parent=self.edit_menu_block)    # edit_window.nml:356
        _w72 = MenuItem(parent=self.edit_menu_block)    # edit_window.nml:357
        _w73 = MenuItem(parent=self.edit_menu_block)    # edit_window.nml:359
        _w74 = MenuLine(parent=self.edit_menu_block)    # edit_window.nml:361
        _w75 = MenuItem(parent=self.edit_menu_block)    # edit_window.nml:362
        _w76 = MenuItem(parent=self.edit_menu_block)    # edit_window.nml:363
        _w77 = MenuItem(parent=self.edit_menu_block)    # edit_window.nml:364
        _w78 = MenuItem(parent=self.edit_menu_block)    # edit_window.nml:365
        _w79 = MenuItem(parent=self.edit_menu_block)    # edit_window.nml:367
        _w80 = MenuLine(parent=self.edit_menu_block)    # edit_window.nml:369
        _w81 = MenuItem(parent=self.edit_menu_block)    # edit_window.nml:370
        _w82 = MenuItem(parent=self.edit_menu_block)    # edit_window.nml:371
        _w83 = MenuItem(parent=self.edit_menu_block)    # edit_window.nml:372
        _w84 = MenuLine(parent=self.edit_menu_block)    # edit_window.nml:373
        _w85 = MenuItem(parent=self.edit_menu_block)    # edit_window.nml:374
        _w86 = MenuItem(parent=self.edit_menu_block)    # edit_window.nml:377
        self.edit_menu_misc = SubMenu(parent=self.edit_menu)    # edit_window.nml:379
        _w87 = MenuItem(parent=self.edit_menu_misc)    # edit_window.nml:381
        _w88 = MenuItem(parent=self.edit_menu_misc)    # edit_window.nml:382
        _w89 = MenuItem(parent=self.edit_menu_misc)    # edit_window.nml:383
        _w90 = MenuItem(parent=self.edit_menu_misc)    # edit_window.nml:384
        _w91 = MenuItem(parent=self.edit_menu_misc)    # edit_window.nml:385
        _w92 = MenuLine(parent=self.edit_menu_misc)    # edit_window.nml:387
        self.edit_menu_misc_uppercase = SubMenu(parent=self.edit_menu_misc)    # edit_window.nml:388
        _w93 = MenuItem(parent=self.edit_menu_misc_uppercase)    # edit_window.nml:390
        _w94 = MenuItem(parent=self.edit_menu_misc_uppercase)    # edit_window.nml:391
        _w95 = MenuItem(parent=self.edit_menu_misc_uppercase)    # edit_window.nml:392
        self.edit_menu_misc_lowercase = SubMenu(parent=self.edit_menu_misc)    # edit_window.nml:393
        _w96 = MenuItem(parent=self.edit_menu_misc_lowercase)    # edit_window.nml:395
        _w97 = MenuItem(parent=self.edit_menu_misc_lowercase)    # edit_window.nml:396
        _w98 = MenuItem(parent=self.edit_menu_misc_lowercase)    # edit_window.nml:397
        self.edit_menu_misc_capitalize = SubMenu(parent=self.edit_menu_misc)    # edit_window.nml:398
        _w99 = MenuItem(parent=self.edit_menu_misc_capitalize)    # edit_window.nml:400
        _w100 = MenuItem(parent=self.edit_menu_misc_capitalize)    # edit_window.nml:401
        _w101 = MenuItem(parent=self.edit_menu_misc_capitalize)    # edit_window.nml:402
        self.edit_menu_options = SubMenu(parent=self.edit_menu)    # edit_window.nml:403
        _w102 = MenuItem(parent=self.edit_menu_options)    # edit_window.nml:405
        _w103 = MenuItem(parent=self.edit_menu_options)    # edit_window.nml:407
        _w104 = MenuItem(parent=self.edit_menu_options)    # edit_window.nml:408
        _w105 = MenuItem(parent=self.edit_menu_options)    # edit_window.nml:409
        _w106 = MenuItem(parent=self.edit_menu_options)    # edit_window.nml:410
        _w107 = MenuItem(parent=self.edit_menu_options)    # edit_window.nml:412
        _w108 = MenuItem(parent=self.edit_menu_options)    # edit_window.nml:414
        _w109 = MenuItem(parent=self.edit_menu_options)    # edit_window.nml:417
        _w110 = MenuItem(parent=self.edit_menu_options)    # edit_window.nml:420
        _w111 = MenuItem(parent=self.edit_menu_options)    # edit_window.nml:423
        _w112 = MenuItem(parent=self.edit_menu_options)    # edit_window.nml:425
        _w113 = MenuItem(parent=self.edit_menu_options)    # edit_window.nml:426
        _w114 = MenuItem(parent=self.edit_menu_options)    # edit_window.nml:427
        _w115 = MenuItem(parent=self.edit_menu_options)    # edit_window.nml:429
        self.edit_menu_file_type = SubMenu(parent=self.edit_menu)    # edit_window.nml:434

        self.zoomed = True    # edit_window.nml:29
        self.first_focus = _bind(lambda _o: self.editor)    # edit_window.nml:67

        self.gutter.target = _bind(lambda _o: self.editor)    # edit_window.nml:74
        self.gutter.visible = _bind(lambda _o: self.editor.line_numbers)    # edit_window.nml:75
        self.gutter.x = 1    # edit_window.nml:76
        self.gutter.width = _bind(    # edit_window.nml:77
            lambda _o: min(gutter_width(self.editor.line_count), max(0, _o.parent.width - 3)) if self.editor.line_numbers else 0
        )
        self.gutter.y = 1    # edit_window.nml:79
        self.gutter.height = _bind(lambda _o: max(0, _o.parent.height - 2))    # edit_window.nml:80

        self.editor.x = _bind(lambda _o: 1 + self.gutter.width)    # edit_window.nml:84
        self.editor.width = _bind(    # edit_window.nml:85
            lambda _o: max(0, _o.parent.width - 2 - self.gutter.width)
        )
        self.editor.y = 1    # edit_window.nml:87
        self.editor.height = _bind(lambda _o: max(0, _o.parent.height - 2))    # edit_window.nml:88

        self.find_bar.width = _bind(    # edit_window.nml:95
            lambda _o: min(50, self.editor.width - 1) if self.editor.width >= 36 else 0
        )
        self.find_bar.height = _bind(lambda _o: 4 if _o.replace else 3)    # edit_window.nml:96
        self.find_bar.x = _bind(    # edit_window.nml:97
            lambda _o: self.editor.x + self.editor.width - _o.width - 1
        )
        self.find_bar.y = _bind(lambda _o: self.editor.y)    # edit_window.nml:98

        self.vbar.visible = _bind(    # edit_window.nml:105
            lambda _o: self.active and self.editor.overflows
        )
        self.vbar.width = 1    # edit_window.nml:106
        self.vbar.value = _bind(lambda _o: self.editor.line)    # edit_window.nml:111
        self.vbar.maximum = _bind(    # edit_window.nml:112
            lambda _o: max(0, self.editor.line_count - 1)
        )
        self.vbar.page = _bind(lambda _o: max(1, self.editor.height))    # edit_window.nml:113
        self.vbar.x = _bind(lambda _o: max(0, _o.parent.width - _o.width))    # edit_window.nml:108
        self.vbar.y = 1    # edit_window.nml:109
        self.vbar.height = _bind(lambda _o: max(0, _o.parent.height - 2))    # edit_window.nml:110
        self.vbar.on_scroll = self.on_vbar_scroll    # edit_window.nml:104

        self.hbar.orientation = 'horizontal'    # edit_window.nml:126
        self.hbar.visible = _bind(    # edit_window.nml:127
            lambda _o: self.active and self.editor.overflows_across and (_o.width >= 4)
        )
        self.hbar.x = _bind(    # edit_window.nml:128
            lambda _o: max(24, self.marks.x + self.marks.width + 1) if self.marks.visible and self.marks.width else 24
        )
        self.hbar.height = 1    # edit_window.nml:129
        self.hbar.value = _bind(lambda _o: self.editor.col)    # edit_window.nml:134
        self.hbar.maximum = _bind(lambda _o: max(0, self.editor.row_span - 1))    # edit_window.nml:135
        self.hbar.page = _bind(lambda _o: max(1, self.editor.width))    # edit_window.nml:136
        self.hbar.width = _bind(    # edit_window.nml:131
            lambda _o: max(0, (self.options.x - 1 if self.options.visible and self.options.width else _o.parent.width - 2) - _o.x)
        )
        self.hbar.y = _bind(lambda _o: max(0, _o.parent.height - _o.height))    # edit_window.nml:133
        self.hbar.on_scroll = self.on_hbar_scroll    # edit_window.nml:125

        self.info.name = 'info'    # edit_window.nml:142
        self.info.visible = _bind(lambda _o: self.active)    # edit_window.nml:143
        self.info.x = 2    # edit_window.nml:144
        self.info.width = _bind(    # edit_window.nml:145
            lambda _o: min(display_width(self.editor.info_text), max(0, _o.parent.width - 4))
        )
        self.info.text = _bind(lambda _o: self.editor.info_text)    # edit_window.nml:148
        self.info.y = _bind(lambda _o: max(0, _o.parent.height - _o.height))    # edit_window.nml:147

        self.marks.name = 'info'    # edit_window.nml:156
        self.marks.visible = _bind(lambda _o: self.active)    # edit_window.nml:157
        self.marks.width = _bind(    # edit_window.nml:158
            lambda _o: min(display_width(self.editor.format_text), max(0, _o.parent.width - 3 - _o.x))
        )
        self.marks.text = _bind(lambda _o: self.editor.format_text)    # edit_window.nml:162
        self.marks.x = _bind(lambda _o: self.info.x + self.info.width + 1)    # edit_window.nml:160
        self.marks.y = _bind(lambda _o: max(0, _o.parent.height - _o.height))    # edit_window.nml:161

        self.options.visible = _bind(    # edit_window.nml:171
            lambda _o: self.active and SETTINGS.editor.show_options
        )
        self.options.target = _bind(lambda _o: self.editor)    # edit_window.nml:172
        self.options.room = _bind(    # edit_window.nml:173
            lambda _o: max(0, _o.parent.width - 3 - (self.marks.x + self.marks.width if self.marks.visible and self.marks.width else self.info.x + self.info.width) - 1)
        )
        self.options.width = _bind(lambda _o: _o.used_width)    # edit_window.nml:174
        self.options.height = 1    # edit_window.nml:175
        self.options.x = _bind(    # edit_window.nml:177
            lambda _o: max(0, _o.parent.width - 3 - _o.width)
        )
        self.options.y = _bind(lambda _o: max(0, _o.parent.height - _o.height))    # edit_window.nml:178

        self.edit_menu.text = _bind(lambda _o: _tr('~E~ditor'), yielding=True)    # edit_window.nml:199
        self.edit_menu.after = 'File'    # edit_window.nml:199
        self.edit_menu.tooltip = _bind(    # edit_window.nml:201
            lambda _o: _tr('Editing, the file, search, paragraphs and blocks'),
            yielding=True,
        )

        _w1.text = _bind(lambda _o: _tr('~U~ndo'), yielding=True)    # edit_window.nml:206
        _w1.command = Undo    # edit_window.nml:206
        _w1.key = 'Alt-BkSp'    # edit_window.nml:206

        _w2.text = _bind(lambda _o: _tr('R~e~do'), yielding=True)    # edit_window.nml:207
        _w2.command = Redo    # edit_window.nml:207
        _w2.key = 'Alt-Shift-BkSp'    # edit_window.nml:207

        _w4.text = _bind(lambda _o: _tr('Cu~t~'), yielding=True)    # edit_window.nml:209
        _w4.command = ClipboardCut    # edit_window.nml:209
        _w4.key = 'Shift-Del'    # edit_window.nml:209

        _w5.text = _bind(lambda _o: _tr('~C~opy'), yielding=True)    # edit_window.nml:210
        _w5.command = ClipboardCopy    # edit_window.nml:210
        _w5.key = 'Ctrl-Ins'    # edit_window.nml:210

        _w6.text = _bind(lambda _o: _tr('~P~aste'), yielding=True)    # edit_window.nml:211
        _w6.command = ClipboardPaste    # edit_window.nml:211
        _w6.key = 'Shift-Ins'    # edit_window.nml:211

        _w7.text = _bind(lambda _o: _tr('C~o~py to...'), yielding=True)    # edit_window.nml:212
        _w7.command = BlockWrite    # edit_window.nml:212
        _w7.tooltip = _bind(    # edit_window.nml:213
            lambda _o: _tr('Write the block to a file'),
            yielding=True,
        )

        _w8.text = _bind(lambda _o: _tr('P~a~ste from...'), yielding=True)    # edit_window.nml:214
        _w8.command = BlockRead    # edit_window.nml:214
        _w8.tooltip = _bind(    # edit_window.nml:215
            lambda _o: _tr("Insert a file's text at the cursor"),
            yielding=True,
        )

        _w10.text = _bind(lambda _o: _tr('C~l~ear'), yielding=True)    # edit_window.nml:217
        _w10.command = Clear    # edit_window.nml:217
        _w10.key = 'Ctrl-Del'    # edit_window.nml:217
        _w10.tooltip = _bind(    # edit_window.nml:218
            lambda _o: _tr('Delete the selection without copying it to the clipboard'),
            yielding=True,
        )

        self.edit_menu_delete.text = _bind(    # edit_window.nml:224
            lambda _o: _tr('~D~elete'),
            yielding=True,
        )
        self.edit_menu_delete.tooltip = _bind(    # edit_window.nml:226
            lambda _o: _tr('Delete a line, a word or the rest of the line'),
            yielding=True,
        )

        _w11.text = _bind(lambda _o: _tr('~D~elete line'), yielding=True)    # edit_window.nml:227
        _w11.command = DeleteLine    # edit_window.nml:227
        _w11.key = 'Ctrl-Y'    # edit_window.nml:227

        _w12.text = _bind(lambda _o: _tr('Delete ~w~ord left'), yielding=True)    # edit_window.nml:228
        _w12.command = DeleteWordLeft    # edit_window.nml:228
        _w12.key = 'Ctrl-BkSp'    # edit_window.nml:228

        _w13.text = _bind(lambda _o: _tr('Delete word ri~g~ht'), yielding=True)    # edit_window.nml:229
        _w13.command = DeleteWordRight    # edit_window.nml:229
        _w13.tooltip = _bind(    # edit_window.nml:230
            lambda _o: _tr('Delete from the cursor to the start of the next word'),
            yielding=True,
        )

        _w14.text = _bind(    # edit_window.nml:231
            lambda _o: _tr('Delete to e~n~d of line'),
            yielding=True,
        )
        _w14.command = DeleteToEnd    # edit_window.nml:231
        _w14.tooltip = _bind(    # edit_window.nml:232
            lambda _o: _tr('Delete from the cursor to the end of the line'),
            yielding=True,
        )

        _w15.text = _bind(lambda _o: _tr('Insert l~i~ne'), yielding=True)    # edit_window.nml:233
        _w15.command = InsertLine    # edit_window.nml:233
        _w15.key = 'Ctrl-N'    # edit_window.nml:233

        self.edit_menu_file.text = _bind(    # edit_window.nml:235
            lambda _o: _tr('~F~ile'),
            yielding=True,
        )

        _w17.text = _bind(lambda _o: _tr('~O~pen...'), yielding=True)    # edit_window.nml:237
        _w17.command = LoadText    # edit_window.nml:237
        _w17.key = 'F3'    # edit_window.nml:237

        _w18.text = _bind(lambda _o: _tr('~S~ave'), yielding=True)    # edit_window.nml:238
        _w18.command = SaveText    # edit_window.nml:238
        _w18.key = 'F2'    # edit_window.nml:238

        _w19.text = _bind(lambda _o: _tr('Save ~a~s...'), yielding=True)    # edit_window.nml:239
        _w19.command = SaveTextAs    # edit_window.nml:239
        _w19.key = 'Shift-F2'    # edit_window.nml:239

        _w20.text = _bind(lambda _o: _tr('Save a~l~l...'), yielding=True)    # edit_window.nml:240
        _w20.command = SaveAll    # edit_window.nml:240
        _w20.key = 'Ctrl-F2'    # edit_window.nml:240

        _w21.text = _bind(lambda _o: _tr('New ~v~iew'), yielding=True)    # edit_window.nml:242
        _w21.command = NewView    # edit_window.nml:242
        _w21.tooltip = _bind(    # edit_window.nml:243
            lambda _o: _tr('Open another window on this text'),
            yielding=True,
        )

        self.edit_menu_line_endings.text = _bind(    # edit_window.nml:247
            lambda _o: _tr('Line en~d~ings'),
            yielding=True,
        )
        self.edit_menu_line_endings.key_command = ChooseLineEnding    # edit_window.nml:247

        self.edit_menu_encoding.text = _bind(    # edit_window.nml:249
            lambda _o: _tr('En~c~oding'),
            yielding=True,
        )
        self.edit_menu_encoding.key_command = ChooseEncoding    # edit_window.nml:249

        _w24.text = _bind(lambda _o: _tr('~P~rint'), yielding=True)    # edit_window.nml:252
        _w24.command = PrintFile    # edit_window.nml:252
        _w24.key = 'F8'    # edit_window.nml:252

        _w25.text = _bind(lambda _o: _tr('Print ~b~lock'), yielding=True)    # edit_window.nml:253
        _w25.command = PrintBlock    # edit_window.nml:253
        _w25.key = 'Shift-F8'    # edit_window.nml:253

        _w27.text = _bind(lambda _o: _tr('~M~ain menu'), yielding=True)    # edit_window.nml:256
        _w27.command = MainMenu    # edit_window.nml:256
        _w27.key = 'F10'    # edit_window.nml:256

        _w28.text = _bind(lambda _o: _tr('E~x~it'), yielding=True)    # edit_window.nml:257
        _w28.command = CloseWindow    # edit_window.nml:257
        _w28.key = 'Ctrl-F4'    # edit_window.nml:257

        self.edit_menu_search.text = _bind(    # edit_window.nml:258
            lambda _o: _tr('~S~earch'),
            yielding=True,
        )

        _w29.text = _bind(lambda _o: _tr('Find ~b~ar'), yielding=True)    # edit_window.nml:261
        _w29.command = ShowFindBar    # edit_window.nml:261
        _w29.key = 'Ctrl-F'    # edit_window.nml:261
        _w29.tooltip = _bind(    # edit_window.nml:262
            lambda _o: _tr('Search as you type, in a bar over the text'),
            yielding=True,
        )

        _w30.text = _bind(lambda _o: _tr('Replace b~a~r'), yielding=True)    # edit_window.nml:263
        _w30.command = ShowReplaceBar    # edit_window.nml:263
        _w30.key = 'Ctrl-R'    # edit_window.nml:263

        _w32.text = _bind(lambda _o: _tr('~F~ind...'), yielding=True)    # edit_window.nml:265
        _w32.command = StartSearch    # edit_window.nml:265
        _w32.key = 'F7'    # edit_window.nml:265

        _w33.text = _bind(lambda _o: _tr('~R~eplace...'), yielding=True)    # edit_window.nml:266
        _w33.command = Replace    # edit_window.nml:266
        _w33.key = 'Ctrl-F7'    # edit_window.nml:266

        _w34.text = _bind(lambda _o: _tr('~S~earch again'), yielding=True)    # edit_window.nml:267
        _w34.command = ContSearch    # edit_window.nml:267
        _w34.key = 'Shift-F7'    # edit_window.nml:267

        _w35.text = _bind(lambda _o: _tr('Re~v~ersed search'), yielding=True)    # edit_window.nml:268
        _w35.command = ReverseSearch    # edit_window.nml:268
        _w35.key = 'Alt-F7'    # edit_window.nml:268

        _w36.text = _bind(    # edit_window.nml:269
            lambda _o: _tr('~G~o to line number...'),
            yielding=True,
        )
        _w36.command = GotoLineNumber    # edit_window.nml:269
        _w36.key = 'Alt-G'    # edit_window.nml:269

        _w37.text = _bind(lambda _o: _tr('~M~atching bracket'), yielding=True)    # edit_window.nml:271
        _w37.command = BracketPair    # edit_window.nml:271
        _w37.key = 'Alt-Left'    # edit_window.nml:271
        _w37.tooltip = _bind(    # edit_window.nml:272
            lambda _o: _tr('Jump to the bracket that pairs with the one at the cursor'),
            yielding=True,
        )

        self.edit_menu_place_marker.text = _bind(    # edit_window.nml:277
            lambda _o: _tr('Pla~c~e marker'),
            yielding=True,
        )
        self.edit_menu_place_marker.tooltip = _bind(    # edit_window.nml:279
            lambda _o: _tr("Keep the cursor's place as one of nine markers"),
            yielding=True,
        )

        _w39.text = _bind(lambda _o: _tr('Marker ~1~'), yielding=True)    # edit_window.nml:280
        _w39.command = PlaceMarker(1)    # edit_window.nml:280
        _w39.tooltip = _bind(    # edit_window.nml:281
            lambda _o: _tr("Keep the cursor's place as marker 1"),
            yielding=True,
        )

        _w40.text = _bind(lambda _o: _tr('Marker ~2~'), yielding=True)    # edit_window.nml:282
        _w40.command = PlaceMarker(2)    # edit_window.nml:282
        _w40.tooltip = _bind(    # edit_window.nml:283
            lambda _o: _tr("Keep the cursor's place as marker 2"),
            yielding=True,
        )

        _w41.text = _bind(lambda _o: _tr('Marker ~3~'), yielding=True)    # edit_window.nml:284
        _w41.command = PlaceMarker(3)    # edit_window.nml:284
        _w41.tooltip = _bind(    # edit_window.nml:285
            lambda _o: _tr("Keep the cursor's place as marker 3"),
            yielding=True,
        )

        _w42.text = _bind(lambda _o: _tr('Marker ~4~'), yielding=True)    # edit_window.nml:286
        _w42.command = PlaceMarker(4)    # edit_window.nml:286
        _w42.tooltip = _bind(    # edit_window.nml:287
            lambda _o: _tr("Keep the cursor's place as marker 4"),
            yielding=True,
        )

        _w43.text = _bind(lambda _o: _tr('Marker ~5~'), yielding=True)    # edit_window.nml:288
        _w43.command = PlaceMarker(5)    # edit_window.nml:288
        _w43.tooltip = _bind(    # edit_window.nml:289
            lambda _o: _tr("Keep the cursor's place as marker 5"),
            yielding=True,
        )

        _w44.text = _bind(lambda _o: _tr('Marker ~6~'), yielding=True)    # edit_window.nml:290
        _w44.command = PlaceMarker(6)    # edit_window.nml:290
        _w44.tooltip = _bind(    # edit_window.nml:291
            lambda _o: _tr("Keep the cursor's place as marker 6"),
            yielding=True,
        )

        _w45.text = _bind(lambda _o: _tr('Marker ~7~'), yielding=True)    # edit_window.nml:292
        _w45.command = PlaceMarker(7)    # edit_window.nml:292
        _w45.tooltip = _bind(    # edit_window.nml:293
            lambda _o: _tr("Keep the cursor's place as marker 7"),
            yielding=True,
        )

        _w46.text = _bind(lambda _o: _tr('Marker ~8~'), yielding=True)    # edit_window.nml:294
        _w46.command = PlaceMarker(8)    # edit_window.nml:294
        _w46.tooltip = _bind(    # edit_window.nml:295
            lambda _o: _tr("Keep the cursor's place as marker 8"),
            yielding=True,
        )

        _w47.text = _bind(lambda _o: _tr('Marker ~9~'), yielding=True)    # edit_window.nml:296
        _w47.command = PlaceMarker(9)    # edit_window.nml:296
        _w47.tooltip = _bind(    # edit_window.nml:297
            lambda _o: _tr("Keep the cursor's place as marker 9"),
            yielding=True,
        )

        self.edit_menu_goto_marker.text = _bind(    # edit_window.nml:298
            lambda _o: _tr('G~o~ to marker'),
            yielding=True,
        )
        self.edit_menu_goto_marker.tooltip = _bind(    # edit_window.nml:300
            lambda _o: _tr('Take the cursor back to a place kept as a marker'),
            yielding=True,
        )

        _w48.text = _bind(lambda _o: _tr('Marker ~1~'), yielding=True)    # edit_window.nml:301
        _w48.command = GotoMarker(1)    # edit_window.nml:301
        _w48.tooltip = _bind(    # edit_window.nml:302
            lambda _o: _tr('Take the cursor back to marker 1'),
            yielding=True,
        )

        _w49.text = _bind(lambda _o: _tr('Marker ~2~'), yielding=True)    # edit_window.nml:303
        _w49.command = GotoMarker(2)    # edit_window.nml:303
        _w49.tooltip = _bind(    # edit_window.nml:304
            lambda _o: _tr('Take the cursor back to marker 2'),
            yielding=True,
        )

        _w50.text = _bind(lambda _o: _tr('Marker ~3~'), yielding=True)    # edit_window.nml:305
        _w50.command = GotoMarker(3)    # edit_window.nml:305
        _w50.tooltip = _bind(    # edit_window.nml:306
            lambda _o: _tr('Take the cursor back to marker 3'),
            yielding=True,
        )

        _w51.text = _bind(lambda _o: _tr('Marker ~4~'), yielding=True)    # edit_window.nml:307
        _w51.command = GotoMarker(4)    # edit_window.nml:307
        _w51.tooltip = _bind(    # edit_window.nml:308
            lambda _o: _tr('Take the cursor back to marker 4'),
            yielding=True,
        )

        _w52.text = _bind(lambda _o: _tr('Marker ~5~'), yielding=True)    # edit_window.nml:309
        _w52.command = GotoMarker(5)    # edit_window.nml:309
        _w52.tooltip = _bind(    # edit_window.nml:310
            lambda _o: _tr('Take the cursor back to marker 5'),
            yielding=True,
        )

        _w53.text = _bind(lambda _o: _tr('Marker ~6~'), yielding=True)    # edit_window.nml:311
        _w53.command = GotoMarker(6)    # edit_window.nml:311
        _w53.tooltip = _bind(    # edit_window.nml:312
            lambda _o: _tr('Take the cursor back to marker 6'),
            yielding=True,
        )

        _w54.text = _bind(lambda _o: _tr('Marker ~7~'), yielding=True)    # edit_window.nml:313
        _w54.command = GotoMarker(7)    # edit_window.nml:313
        _w54.tooltip = _bind(    # edit_window.nml:314
            lambda _o: _tr('Take the cursor back to marker 7'),
            yielding=True,
        )

        _w55.text = _bind(lambda _o: _tr('Marker ~8~'), yielding=True)    # edit_window.nml:315
        _w55.command = GotoMarker(8)    # edit_window.nml:315
        _w55.tooltip = _bind(    # edit_window.nml:316
            lambda _o: _tr('Take the cursor back to marker 8'),
            yielding=True,
        )

        _w56.text = _bind(lambda _o: _tr('Marker ~9~'), yielding=True)    # edit_window.nml:317
        _w56.command = GotoMarker(9)    # edit_window.nml:317
        _w56.tooltip = _bind(    # edit_window.nml:318
            lambda _o: _tr('Take the cursor back to marker 9'),
            yielding=True,
        )

        self.edit_menu_paragraph.text = _bind(    # edit_window.nml:319
            lambda _o: _tr('Pa~r~agraph'),
            yielding=True,
        )

        _w57.text = _bind(lambda _o: _tr('~J~ustify'), yielding=True)    # edit_window.nml:321
        _w57.command = FJustify    # edit_window.nml:321
        _w57.key = 'Alt-J'    # edit_window.nml:321
        _w57.tooltip = _bind(    # edit_window.nml:322
            lambda _o: _tr("Justify the block's paragraph to both margins"),
            yielding=True,
        )

        _w58.text = _bind(lambda _o: _tr('~R~ight'), yielding=True)    # edit_window.nml:323
        _w58.command = FRight    # edit_window.nml:323
        _w58.key = 'Alt-R'    # edit_window.nml:323

        _w59.text = _bind(lambda _o: _tr('~L~eft'), yielding=True)    # edit_window.nml:324
        _w59.command = FLeft    # edit_window.nml:324
        _w59.key = 'Alt-L'    # edit_window.nml:324

        _w60.text = _bind(lambda _o: _tr('~C~enter'), yielding=True)    # edit_window.nml:325
        _w60.command = FCenter    # edit_window.nml:325
        _w60.key = 'Alt-C'    # edit_window.nml:325

        self.edit_menu_line_format.text = _bind(    # edit_window.nml:330
            lambda _o: _tr('Current li~n~e'),
            yielding=True,
        )
        self.edit_menu_line_format.tooltip = _bind(    # edit_window.nml:332
            lambda _o: _tr("Format the cursor's line alone"),
            yielding=True,
        )

        _w61.text = _bind(lambda _o: _tr('~J~ustify'), yielding=True)    # edit_window.nml:333
        _w61.command = LJustify    # edit_window.nml:333
        _w61.tooltip = _bind(    # edit_window.nml:334
            lambda _o: _tr("Justify the cursor's line to both margins"),
            yielding=True,
        )

        _w62.text = _bind(lambda _o: _tr('~R~ight'), yielding=True)    # edit_window.nml:335
        _w62.command = LRight    # edit_window.nml:335
        _w62.tooltip = _bind(    # edit_window.nml:336
            lambda _o: _tr("Put the cursor's line against the right margin"),
            yielding=True,
        )

        _w63.text = _bind(lambda _o: _tr('~L~eft'), yielding=True)    # edit_window.nml:337
        _w63.command = LLeft    # edit_window.nml:337
        _w63.tooltip = _bind(    # edit_window.nml:338
            lambda _o: _tr("Put the cursor's line at the left margin"),
            yielding=True,
        )

        _w64.text = _bind(lambda _o: _tr('~C~enter'), yielding=True)    # edit_window.nml:339
        _w64.command = LCenter    # edit_window.nml:339
        _w64.tooltip = _bind(    # edit_window.nml:340
            lambda _o: _tr("Center the cursor's line between the margins"),
            yielding=True,
        )

        _w66.text = _bind(lambda _o: _tr('~M~argins...'), yielding=True)    # edit_window.nml:342
        _w66.command = SetMargins    # edit_window.nml:342

        self.edit_menu_block.text = _bind(    # edit_window.nml:343
            lambda _o: _tr('~B~lock'),
            yielding=True,
        )

        _w67.text = _bind(lambda _o: _tr('Mar~k~ start'), yielding=True)    # edit_window.nml:348
        _w67.command = BlockStart    # edit_window.nml:348
        _w67.tooltip = _bind(    # edit_window.nml:349
            lambda _o: _tr('Begin the block at the cursor'),
            yielding=True,
        )

        _w68.text = _bind(lambda _o: _tr('Mark ~e~nd'), yielding=True)    # edit_window.nml:350
        _w68.command = BlockEnd    # edit_window.nml:350
        _w68.tooltip = _bind(    # edit_window.nml:351
            lambda _o: _tr('End the block at the cursor'),
            yielding=True,
        )

        _w69.text = _bind(lambda _o: _tr('Mark ~w~ord'), yielding=True)    # edit_window.nml:352
        _w69.command = MarkWord    # edit_window.nml:352
        _w69.tooltip = _bind(    # edit_window.nml:353
            lambda _o: _tr('Mark the word at the cursor as the block'),
            yielding=True,
        )

        _w70.text = _bind(lambda _o: _tr('Mark li~n~e'), yielding=True)    # edit_window.nml:354
        _w70.command = MarkLine    # edit_window.nml:354
        _w70.tooltip = _bind(    # edit_window.nml:355
            lambda _o: _tr("Mark the cursor's line as the block"),
            yielding=True,
        )

        _w72.text = _bind(lambda _o: _tr('~G~o to block start'), yielding=True)    # edit_window.nml:357
        _w72.command = MoveBlockStart    # edit_window.nml:357
        _w72.tooltip = _bind(    # edit_window.nml:358
            lambda _o: _tr('Take the cursor to where the block begins'),
            yielding=True,
        )

        _w73.text = _bind(lambda _o: _tr('Go to block en~d~'), yielding=True)    # edit_window.nml:359
        _w73.command = MoveBlockEnd    # edit_window.nml:359
        _w73.tooltip = _bind(    # edit_window.nml:360
            lambda _o: _tr('Take the cursor to where the block ends'),
            yielding=True,
        )

        _w75.text = _bind(lambda _o: _tr('~M~ove'), yielding=True)    # edit_window.nml:362
        _w75.command = MoveBlock    # edit_window.nml:362
        _w75.key = 'Alt-Shift-V'    # edit_window.nml:362

        _w76.text = _bind(lambda _o: _tr('~C~opy'), yielding=True)    # edit_window.nml:363
        _w76.command = CopyBlock    # edit_window.nml:363
        _w76.key = 'Alt-Shift-K'    # edit_window.nml:363

        _w77.text = _bind(lambda _o: _tr('~I~ndent'), yielding=True)    # edit_window.nml:364
        _w77.command = IndentBlock    # edit_window.nml:364
        _w77.key = 'Alt-Shift-I'    # edit_window.nml:364

        _w78.text = _bind(lambda _o: _tr('~U~nindent'), yielding=True)    # edit_window.nml:365
        _w78.command = UnindentBlock    # edit_window.nml:365
        _w78.key = 'Alt-Shift-O'    # edit_window.nml:365

        _w79.text = _bind(lambda _o: _tr('~H~ide/show block'), yielding=True)    # edit_window.nml:367
        _w79.command = HideBlock    # edit_window.nml:367
        _w79.key = 'Alt-H'    # edit_window.nml:367
        _w79.tooltip = _bind(    # edit_window.nml:368
            lambda _o: _tr('Hide the marked block, or show it again'),
            yielding=True,
        )

        _w81.text = _bind(lambda _o: _tr('U~p~percase'), yielding=True)    # edit_window.nml:370
        _w81.command = UpcaseBlock    # edit_window.nml:370
        _w81.key = 'Alt-Shift-U'    # edit_window.nml:370

        _w82.text = _bind(lambda _o: _tr('~L~owercase'), yielding=True)    # edit_window.nml:371
        _w82.command = LowcaseBlock    # edit_window.nml:371
        _w82.key = 'Alt-Shift-L'    # edit_window.nml:371

        _w83.text = _bind(lambda _o: _tr('Capi~t~alize'), yielding=True)    # edit_window.nml:372
        _w83.command = CapitalizeBlock    # edit_window.nml:372
        _w83.key = 'Alt-Shift-C'    # edit_window.nml:372

        _w85.text = _bind(lambda _o: _tr('~S~ort'), yielding=True)    # edit_window.nml:374
        _w85.command = SortBlock    # edit_window.nml:374
        _w85.key = 'Alt-T'    # edit_window.nml:374
        _w85.tooltip = _bind(    # edit_window.nml:375
            lambda _o: _tr('Sort the lines by the column block'),
            yielding=True,
        )

        _w86.text = _bind(lambda _o: _tr('C~a~lculate sum'), yielding=True)    # edit_window.nml:377
        _w86.command = CalcBlock    # edit_window.nml:377
        _w86.key = 'Alt-Ins'    # edit_window.nml:377
        _w86.tooltip = _bind(    # edit_window.nml:378
            lambda _o: _tr("Add up the column block's numbers; the sum goes to the clipboard"),
            yielding=True,
        )

        self.edit_menu_misc.text = _bind(    # edit_window.nml:379
            lambda _o: _tr('~M~isc'),
            yielding=True,
        )

        _w87.text = _bind(lambda _o: _tr('Insert ~d~ate'), yielding=True)    # edit_window.nml:381
        _w87.command = InsertDate    # edit_window.nml:381
        _w87.key = 'Alt-Shift-D'    # edit_window.nml:381

        _w88.text = _bind(lambda _o: _tr('Insert ~t~ime'), yielding=True)    # edit_window.nml:382
        _w88.command = InsertTime    # edit_window.nml:382
        _w88.key = 'Alt-Shift-T'    # edit_window.nml:382

        _w89.text = _bind(lambda _o: _tr('Du~p~licate line'), yielding=True)    # edit_window.nml:383
        _w89.command = DuplicateLine    # edit_window.nml:383
        _w89.key = 'F6'    # edit_window.nml:383

        _w90.text = _bind(lambda _o: _tr('Character ta~b~le'), yielding=True)    # edit_window.nml:384
        _w90.command = AsciiTable    # edit_window.nml:384
        _w90.key = 'Ctrl P'    # edit_window.nml:384

        _w91.text = _bind(lambda _o: _tr('Line Dra~w~ing'), yielding=True)    # edit_window.nml:385
        _w91.command = SwitchDrawMode    # edit_window.nml:385
        _w91.key = 'F4'    # edit_window.nml:385
        _w91.tooltip = _bind(    # edit_window.nml:386
            lambda _o: _tr('Draw lines with the arrow keys: off, single, double'),
            yielding=True,
        )

        self.edit_menu_misc_uppercase.text = _bind(    # edit_window.nml:388
            lambda _o: _tr('~U~ppercase'),
            yielding=True,
        )

        _w93.text = _bind(lambda _o: _tr('~W~ord'), yielding=True)    # edit_window.nml:390
        _w93.command = UpWord    # edit_window.nml:390
        _w93.key = 'Ctrl ['    # edit_window.nml:390

        _w94.text = _bind(lambda _o: _tr('~L~ine'), yielding=True)    # edit_window.nml:391
        _w94.command = UpString    # edit_window.nml:391
        _w94.key = 'Ctrl+Shift ['    # edit_window.nml:391

        _w95.text = _bind(lambda _o: _tr('~B~lock'), yielding=True)    # edit_window.nml:392
        _w95.command = UpcaseBlock    # edit_window.nml:392
        _w95.key = 'Alt-Shift-U'    # edit_window.nml:392

        self.edit_menu_misc_lowercase.text = _bind(    # edit_window.nml:393
            lambda _o: _tr('~L~owercase'),
            yielding=True,
        )

        _w96.text = _bind(lambda _o: _tr('~W~ord'), yielding=True)    # edit_window.nml:395
        _w96.command = LowWord    # edit_window.nml:395
        _w96.key = 'Ctrl ]'    # edit_window.nml:395

        _w97.text = _bind(lambda _o: _tr('~L~ine'), yielding=True)    # edit_window.nml:396
        _w97.command = LowString    # edit_window.nml:396
        _w97.key = 'Ctrl+Shift ]'    # edit_window.nml:396

        _w98.text = _bind(lambda _o: _tr('~B~lock'), yielding=True)    # edit_window.nml:397
        _w98.command = LowcaseBlock    # edit_window.nml:397
        _w98.key = 'Alt-Shift-L'    # edit_window.nml:397

        self.edit_menu_misc_capitalize.text = _bind(    # edit_window.nml:398
            lambda _o: _tr('~C~apitalize'),
            yielding=True,
        )

        _w99.text = _bind(lambda _o: _tr('~W~ord'), yielding=True)    # edit_window.nml:400
        _w99.command = CapWord    # edit_window.nml:400
        _w99.key = 'Ctrl \\'    # edit_window.nml:400

        _w100.text = _bind(lambda _o: _tr('~L~ine'), yielding=True)    # edit_window.nml:401
        _w100.command = CapString    # edit_window.nml:401
        _w100.key = 'Ctrl+Shift \\'    # edit_window.nml:401

        _w101.text = _bind(lambda _o: _tr('~B~lock'), yielding=True)    # edit_window.nml:402
        _w101.command = CapitalizeBlock    # edit_window.nml:402
        _w101.key = 'Alt-Shift-C'    # edit_window.nml:402

        self.edit_menu_options.text = _bind(    # edit_window.nml:403
            lambda _o: _tr('Optio~n~s'),
            yielding=True,
        )

        _w102.text = _bind(    # edit_window.nml:405
            lambda _o: _tr('~B~ackspace indents'),
            yielding=True,
        )
        _w102.command = SwitchBack    # edit_window.nml:405
        _w102.tooltip = _bind(    # edit_window.nml:406
            lambda _o: _tr("Backspace at a line's start goes back to an indent above"),
            yielding=True,
        )

        _w103.text = _bind(lambda _o: _tr('AutoB~r~ackets'), yielding=True)    # edit_window.nml:407
        _w103.command = SwitchBrackets    # edit_window.nml:407

        _w104.text = _bind(lambda _o: _tr('Auto~i~ndent'), yielding=True)    # edit_window.nml:408
        _w104.command = SwitchIndent    # edit_window.nml:408

        _w105.text = _bind(lambda _o: _tr('~A~uto wrap'), yielding=True)    # edit_window.nml:409
        _w105.command = SwitchSave    # edit_window.nml:409

        _w106.text = _bind(lambda _o: _tr('~J~ustify on wrap'), yielding=True)    # edit_window.nml:410
        _w106.command = SwitchWrap    # edit_window.nml:410
        _w106.tooltip = _bind(    # edit_window.nml:411
            lambda _o: _tr('Widen a wrapped line to the margin'),
            yielding=True,
        )

        _w107.text = _bind(lambda _o: _tr('~V~ertical blocks'), yielding=True)    # edit_window.nml:412
        _w107.command = SwitchBlock    # edit_window.nml:412
        _w107.tooltip = _bind(    # edit_window.nml:413
            lambda _o: _tr('Mark column blocks instead of line ones'),
            yielding=True,
        )

        _w108.text = _bind(lambda _o: _tr('Opti~m~al fill'), yielding=True)    # edit_window.nml:414
        _w108.command = SwitchFill    # edit_window.nml:414
        _w108.tooltip = _bind(    # edit_window.nml:415
            lambda _o: _tr('Write blanks as tabs where they reach a tab stop'),
            yielding=True,
        )

        _w109.text = _bind(lambda _o: _tr('~T~ab characters'), yielding=True)    # edit_window.nml:417
        _w109.command = SwitchTabs    # edit_window.nml:417
        _w109.tooltip = _bind(    # edit_window.nml:418
            lambda _o: _tr('Tab types tab characters, not spaces'),
            yielding=True,
        )

        _w110.text = _bind(lambda _o: _tr('Soft ~w~rap'), yielding=True)    # edit_window.nml:420
        _w110.command = SwitchSoftWrap    # edit_window.nml:420
        _w110.tooltip = _bind(    # edit_window.nml:421
            lambda _o: _tr('Show long lines wrapped at the edge, the text unchanged'),
            yielding=True,
        )

        _w111.text = _bind(lambda _o: _tr('Line ~n~umbers'), yielding=True)    # edit_window.nml:423
        _w111.command = SwitchLineNumbers    # edit_window.nml:423
        _w111.tooltip = _bind(    # edit_window.nml:424
            lambda _o: _tr('Number the lines in a gutter beside the text'),
            yielding=True,
        )

        _w112.text = _bind(    # edit_window.nml:425
            lambda _o: _tr('Current ~l~ine highlight'),
            yielding=True,
        )
        _w112.command = SwitchHiLine    # edit_window.nml:425

        _w113.text = _bind(    # edit_window.nml:426
            lambda _o: _tr('Current ~c~olumn highlight'),
            yielding=True,
        )
        _w113.command = SwitchHiColumn    # edit_window.nml:426

        _w114.text = _bind(lambda _o: _tr('Syntax ~h~ighlight'), yielding=True)    # edit_window.nml:427
        _w114.command = SwitchHighLight    # edit_window.nml:427

        _w115.text = _bind(    # edit_window.nml:429
            lambda _o: _tr('Show hi~d~den characters'),
            yielding=True,
        )
        _w115.command = SwitchHiddenChars    # edit_window.nml:429

        self.edit_menu_file_type.text = _bind(    # edit_window.nml:434
            lambda _o: _tr('File t~y~pe'),
            yielding=True,
        )
        self.edit_menu_file_type.key_command = ChooseFileType    # edit_window.nml:434

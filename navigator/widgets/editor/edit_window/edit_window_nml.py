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
from navigator.widgets.editor.commands import ChooseFileType, AsciiTable, CalcBlock, SwitchHiColumn, SwitchHiLine, SwitchHighLight, SwitchHiddenChars, SwitchFill, ShowFindBar, ShowReplaceBar, CapString, CapWord, LowString, LowWord, UpString, UpWord, DuplicateLine, DeleteLine, DeleteWordLeft, InsertLine, HideBlock, BracketPair, SwitchDrawMode, SwitchBack, SwitchIndent, SwitchBrackets, SwitchSave, SwitchWrap, FCenter, FJustify, FLeft, FRight, SetMargins, ContSearch, LoadText, Replace, ReverseSearch, StartSearch, SaveAll, SaveTextAs, CapitalizeBlock, Clear, ClipboardCopy, ClipboardCut, ClipboardPaste, CopyBlock, GotoLineNumber, PrintBlock, IndentBlock, InsertDate, InsertTime, BlockRead, BlockWrite, LowcaseBlock, MoveBlock, SaveText, SortBlock, UnindentBlock, Undo, Redo, UpcaseBlock, SwitchBlock    # edit_window.nml:3
from navigator.widgets.editor.file_editor import FileEditor, InfoLine    # edit_window.nml:4
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
    vbar: ScrollBar    # edit_window.nml:77
    hbar: ScrollBar    # edit_window.nml:92
    info: InfoLine    # edit_window.nml:105
    options: OptionStrip    # edit_window.nml:121
    edit_menu: SubMenu    # edit_window.nml:146
    edit_menu_file: SubMenu    # edit_window.nml:205
    edit_menu_search: SubMenu    # edit_window.nml:238
    edit_menu_paragraph: SubMenu    # edit_window.nml:278
    edit_menu_block: SubMenu    # edit_window.nml:302
    edit_menu_misc: SubMenu    # edit_window.nml:352
    edit_menu_misc_uppercase: SubMenu    # edit_window.nml:377
    edit_menu_misc_lowercase: SubMenu    # edit_window.nml:392
    edit_menu_misc_capitalize: SubMenu    # edit_window.nml:407
    edit_menu_options: SubMenu    # edit_window.nml:422
    edit_menu_file_type: SubMenu    # edit_window.nml:467

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_vbar_scroll(self, event: _Event) -> bool:    # edit_window.nml:77
        """``vbar`` raised an event whose handler is ``on_scroll``."""
        return False

    async def on_hbar_scroll(self, event: _Event) -> bool:    # edit_window.nml:92
        """``hbar`` raised an event whose handler is ``on_scroll``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.editor = FileEditor(parent=self)    # edit_window.nml:58
        self.find_bar = FindBar(parent=self)    # edit_window.nml:68
        self.vbar = ScrollBar(parent=self)    # edit_window.nml:76
        self.hbar = ScrollBar(parent=self)    # edit_window.nml:91
        self.info = InfoLine(parent=self)    # edit_window.nml:104
        self.options = OptionStrip(parent=self)    # edit_window.nml:120
        self.edit_menu = SubMenu(parent=self)    # edit_window.nml:145
        _w1 = MenuItem(parent=self.edit_menu)    # edit_window.nml:154
        _w2 = MenuItem(parent=self.edit_menu)    # edit_window.nml:158
        _w3 = MenuLine(parent=self.edit_menu)    # edit_window.nml:162
        _w4 = MenuItem(parent=self.edit_menu)    # edit_window.nml:163
        _w5 = MenuItem(parent=self.edit_menu)    # edit_window.nml:167
        _w6 = MenuItem(parent=self.edit_menu)    # edit_window.nml:171
        _w7 = MenuItem(parent=self.edit_menu)    # edit_window.nml:175
        _w8 = MenuItem(parent=self.edit_menu)    # edit_window.nml:179
        _w9 = MenuLine(parent=self.edit_menu)    # edit_window.nml:183
        _w10 = MenuItem(parent=self.edit_menu)    # edit_window.nml:184
        _w11 = MenuItem(parent=self.edit_menu)    # edit_window.nml:190
        _w12 = MenuItem(parent=self.edit_menu)    # edit_window.nml:195
        _w13 = MenuItem(parent=self.edit_menu)    # edit_window.nml:199
        _w14 = MenuLine(parent=self.edit_menu)    # edit_window.nml:203
        self.edit_menu_file = SubMenu(parent=self.edit_menu)    # edit_window.nml:204
        _w15 = MenuItem(parent=self.edit_menu_file)    # edit_window.nml:207
        _w16 = MenuItem(parent=self.edit_menu_file)    # edit_window.nml:211
        _w17 = MenuItem(parent=self.edit_menu_file)    # edit_window.nml:215
        _w18 = MenuItem(parent=self.edit_menu_file)    # edit_window.nml:219
        _w19 = MenuLine(parent=self.edit_menu_file)    # edit_window.nml:223
        _w20 = MenuItem(parent=self.edit_menu_file)    # edit_window.nml:224
        _w21 = MenuItem(parent=self.edit_menu_file)    # edit_window.nml:228
        _w22 = MenuLine(parent=self.edit_menu_file)    # edit_window.nml:232
        _w23 = MenuItem(parent=self.edit_menu_file)    # edit_window.nml:233
        self.edit_menu_search = SubMenu(parent=self.edit_menu)    # edit_window.nml:237
        _w24 = MenuItem(parent=self.edit_menu_search)    # edit_window.nml:241
        _w25 = MenuItem(parent=self.edit_menu_search)    # edit_window.nml:246
        _w26 = MenuLine(parent=self.edit_menu_search)    # edit_window.nml:250
        _w27 = MenuItem(parent=self.edit_menu_search)    # edit_window.nml:251
        _w28 = MenuItem(parent=self.edit_menu_search)    # edit_window.nml:255
        _w29 = MenuItem(parent=self.edit_menu_search)    # edit_window.nml:259
        _w30 = MenuItem(parent=self.edit_menu_search)    # edit_window.nml:263
        _w31 = MenuItem(parent=self.edit_menu_search)    # edit_window.nml:267
        _w32 = MenuItem(parent=self.edit_menu_search)    # edit_window.nml:272
        self.edit_menu_paragraph = SubMenu(parent=self.edit_menu)    # edit_window.nml:277
        _w33 = MenuItem(parent=self.edit_menu_paragraph)    # edit_window.nml:280
        _w34 = MenuItem(parent=self.edit_menu_paragraph)    # edit_window.nml:285
        _w35 = MenuItem(parent=self.edit_menu_paragraph)    # edit_window.nml:289
        _w36 = MenuItem(parent=self.edit_menu_paragraph)    # edit_window.nml:293
        _w37 = MenuLine(parent=self.edit_menu_paragraph)    # edit_window.nml:297
        _w38 = MenuItem(parent=self.edit_menu_paragraph)    # edit_window.nml:298
        self.edit_menu_block = SubMenu(parent=self.edit_menu)    # edit_window.nml:301
        _w39 = MenuItem(parent=self.edit_menu_block)    # edit_window.nml:304
        _w40 = MenuItem(parent=self.edit_menu_block)    # edit_window.nml:308
        _w41 = MenuItem(parent=self.edit_menu_block)    # edit_window.nml:312
        _w42 = MenuItem(parent=self.edit_menu_block)    # edit_window.nml:316
        _w43 = MenuItem(parent=self.edit_menu_block)    # edit_window.nml:321
        _w44 = MenuLine(parent=self.edit_menu_block)    # edit_window.nml:326
        _w45 = MenuItem(parent=self.edit_menu_block)    # edit_window.nml:327
        _w46 = MenuItem(parent=self.edit_menu_block)    # edit_window.nml:331
        _w47 = MenuItem(parent=self.edit_menu_block)    # edit_window.nml:335
        _w48 = MenuLine(parent=self.edit_menu_block)    # edit_window.nml:339
        _w49 = MenuItem(parent=self.edit_menu_block)    # edit_window.nml:340
        _w50 = MenuItem(parent=self.edit_menu_block)    # edit_window.nml:346
        self.edit_menu_misc = SubMenu(parent=self.edit_menu)    # edit_window.nml:351
        _w51 = MenuItem(parent=self.edit_menu_misc)    # edit_window.nml:354
        _w52 = MenuItem(parent=self.edit_menu_misc)    # edit_window.nml:358
        _w53 = MenuItem(parent=self.edit_menu_misc)    # edit_window.nml:362
        _w54 = MenuItem(parent=self.edit_menu_misc)    # edit_window.nml:366
        _w55 = MenuItem(parent=self.edit_menu_misc)    # edit_window.nml:370
        _w56 = MenuLine(parent=self.edit_menu_misc)    # edit_window.nml:375
        self.edit_menu_misc_uppercase = SubMenu(parent=self.edit_menu_misc)    # edit_window.nml:376
        _w57 = MenuItem(parent=self.edit_menu_misc_uppercase)    # edit_window.nml:379
        _w58 = MenuItem(parent=self.edit_menu_misc_uppercase)    # edit_window.nml:383
        _w59 = MenuItem(parent=self.edit_menu_misc_uppercase)    # edit_window.nml:387
        self.edit_menu_misc_lowercase = SubMenu(parent=self.edit_menu_misc)    # edit_window.nml:391
        _w60 = MenuItem(parent=self.edit_menu_misc_lowercase)    # edit_window.nml:394
        _w61 = MenuItem(parent=self.edit_menu_misc_lowercase)    # edit_window.nml:398
        _w62 = MenuItem(parent=self.edit_menu_misc_lowercase)    # edit_window.nml:402
        self.edit_menu_misc_capitalize = SubMenu(parent=self.edit_menu_misc)    # edit_window.nml:406
        _w63 = MenuItem(parent=self.edit_menu_misc_capitalize)    # edit_window.nml:409
        _w64 = MenuItem(parent=self.edit_menu_misc_capitalize)    # edit_window.nml:413
        _w65 = MenuItem(parent=self.edit_menu_misc_capitalize)    # edit_window.nml:417
        self.edit_menu_options = SubMenu(parent=self.edit_menu)    # edit_window.nml:421
        _w66 = MenuItem(parent=self.edit_menu_options)    # edit_window.nml:424
        _w67 = MenuItem(parent=self.edit_menu_options)    # edit_window.nml:428
        _w68 = MenuItem(parent=self.edit_menu_options)    # edit_window.nml:431
        _w69 = MenuItem(parent=self.edit_menu_options)    # edit_window.nml:434
        _w70 = MenuItem(parent=self.edit_menu_options)    # edit_window.nml:437
        _w71 = MenuItem(parent=self.edit_menu_options)    # edit_window.nml:441
        _w72 = MenuItem(parent=self.edit_menu_options)    # edit_window.nml:445
        _w73 = MenuItem(parent=self.edit_menu_options)    # edit_window.nml:449
        _w74 = MenuItem(parent=self.edit_menu_options)    # edit_window.nml:452
        _w75 = MenuItem(parent=self.edit_menu_options)    # edit_window.nml:455
        _w76 = MenuItem(parent=self.edit_menu_options)    # edit_window.nml:459
        self.edit_menu_file_type = SubMenu(parent=self.edit_menu)    # edit_window.nml:466

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

        self.vbar.visible = _bind(lambda _o: self.active)    # edit_window.nml:78
        self.vbar.x = _bind(lambda _o: _o.parent.width - 1)    # edit_window.nml:79
        self.vbar.y = 1    # edit_window.nml:80
        self.vbar.width = 1    # edit_window.nml:81
        self.vbar.height = _bind(lambda _o: max(0, _o.parent.height - 2))    # edit_window.nml:82
        self.vbar.value = _bind(lambda _o: self.editor.line)    # edit_window.nml:83
        self.vbar.maximum = _bind(    # edit_window.nml:84
            lambda _o: max(0, self.editor.line_count - 1)
        )
        self.vbar.page = _bind(lambda _o: max(1, self.editor.height))    # edit_window.nml:85
        self.vbar.on_scroll = self.on_vbar_scroll    # edit_window.nml:77

        self.hbar.orientation = 'horizontal'    # edit_window.nml:93
        self.hbar.visible = _bind(lambda _o: self.active and _o.width >= 4)    # edit_window.nml:94
        self.hbar.x = 24    # edit_window.nml:95
        self.hbar.y = _bind(lambda _o: max(0, _o.parent.height - 1))    # edit_window.nml:96
        self.hbar.width = _bind(    # edit_window.nml:97
            lambda _o: max(0, (self.options.x - 1 if self.options.visible and self.options.width else _o.parent.width - 2) - 24)
        )
        self.hbar.height = 1    # edit_window.nml:98
        self.hbar.value = _bind(lambda _o: self.editor.col)    # edit_window.nml:99
        self.hbar.maximum = _bind(lambda _o: max(255, self.editor.col))    # edit_window.nml:100
        self.hbar.page = _bind(lambda _o: max(1, self.editor.width))    # edit_window.nml:101
        self.hbar.on_scroll = self.on_hbar_scroll    # edit_window.nml:92

        self.info.name = 'info'    # edit_window.nml:107
        self.info.visible = _bind(lambda _o: self.active)    # edit_window.nml:108
        self.info.x = 2    # edit_window.nml:109
        self.info.y = _bind(lambda _o: max(0, _o.parent.height - 1))    # edit_window.nml:110
        self.info.width = _bind(    # edit_window.nml:111
            lambda _o: min(display_width(self.editor.info_text), max(0, _o.parent.width - 4))
        )
        self.info.height = 1    # edit_window.nml:112
        self.info.text = _bind(lambda _o: self.editor.info_text)    # edit_window.nml:113

        self.options.visible = _bind(    # edit_window.nml:122
            lambda _o: self.active and SETTINGS.editor.show_options
        )
        self.options.target = _bind(lambda _o: self.editor)    # edit_window.nml:123
        self.options.room = _bind(    # edit_window.nml:124
            lambda _o: max(0, _o.parent.width - 3 - (self.info.x + self.info.width) - 1)
        )
        self.options.width = _bind(lambda _o: _o.used_width)    # edit_window.nml:125
        self.options.x = _bind(    # edit_window.nml:126
            lambda _o: max(0, _o.parent.width - 3 - _o.width)
        )
        self.options.y = _bind(lambda _o: max(0, _o.parent.height - 1))    # edit_window.nml:127
        self.options.height = 1    # edit_window.nml:128

        self.edit_menu.text = _bind(lambda _o: _tr('~E~ditor'), yielding=True)    # edit_window.nml:147
        self.edit_menu.tooltip = _bind(    # edit_window.nml:148
            lambda _o: _tr('Editing, the file, search, paragraphs and blocks'),
            yielding=True,
        )
        self.edit_menu.after = 'File'    # edit_window.nml:149

        _w1.text = _bind(lambda _o: _tr('~U~ndo'), yielding=True)    # edit_window.nml:155
        _w1.command = Undo    # edit_window.nml:156
        _w1.key = 'Alt-BkSp'    # edit_window.nml:157

        _w2.text = _bind(lambda _o: _tr('R~e~do'), yielding=True)    # edit_window.nml:159
        _w2.command = Redo    # edit_window.nml:160
        _w2.key = 'Alt-Shift-BkSp'    # edit_window.nml:161

        _w4.text = _bind(lambda _o: _tr('Cu~t~'), yielding=True)    # edit_window.nml:164
        _w4.command = ClipboardCut    # edit_window.nml:165
        _w4.key = 'Shift-Del'    # edit_window.nml:166

        _w5.text = _bind(lambda _o: _tr('~C~opy'), yielding=True)    # edit_window.nml:168
        _w5.command = ClipboardCopy    # edit_window.nml:169
        _w5.key = 'Ctrl-Ins'    # edit_window.nml:170

        _w6.text = _bind(lambda _o: _tr('~P~aste'), yielding=True)    # edit_window.nml:172
        _w6.command = ClipboardPaste    # edit_window.nml:173
        _w6.key = 'Shift-Ins'    # edit_window.nml:174

        _w7.text = _bind(lambda _o: _tr('C~o~py to...'), yielding=True)    # edit_window.nml:176
        _w7.tooltip = _bind(    # edit_window.nml:177
            lambda _o: _tr('Write the block to a file'),
            yielding=True,
        )
        _w7.command = BlockWrite    # edit_window.nml:178

        _w8.text = _bind(lambda _o: _tr('P~a~ste from...'), yielding=True)    # edit_window.nml:180
        _w8.tooltip = _bind(    # edit_window.nml:181
            lambda _o: _tr("Insert a file's text at the cursor"),
            yielding=True,
        )
        _w8.command = BlockRead    # edit_window.nml:182

        _w10.text = _bind(lambda _o: _tr('C~l~ear'), yielding=True)    # edit_window.nml:185
        _w10.tooltip = _bind(    # edit_window.nml:186
            lambda _o: _tr('Delete the selection without copying it to the clipboard'),
            yielding=True,
        )
        _w10.command = Clear    # edit_window.nml:187
        _w10.key = 'Ctrl-Del'    # edit_window.nml:188

        _w11.text = _bind(lambda _o: _tr('~D~elete line'), yielding=True)    # edit_window.nml:191
        _w11.command = DeleteLine    # edit_window.nml:192
        _w11.key = 'Ctrl-Y'    # edit_window.nml:193

        _w12.text = _bind(lambda _o: _tr('Delete ~w~ord left'), yielding=True)    # edit_window.nml:196
        _w12.command = DeleteWordLeft    # edit_window.nml:197
        _w12.key = 'Ctrl-BkSp'    # edit_window.nml:198

        _w13.text = _bind(lambda _o: _tr('Insert l~i~ne'), yielding=True)    # edit_window.nml:200
        _w13.command = InsertLine    # edit_window.nml:201
        _w13.key = 'Ctrl-N'    # edit_window.nml:202

        self.edit_menu_file.text = _bind(    # edit_window.nml:206
            lambda _o: _tr('~F~ile'),
            yielding=True,
        )

        _w15.text = _bind(lambda _o: _tr('~O~pen...'), yielding=True)    # edit_window.nml:208
        _w15.command = LoadText    # edit_window.nml:209
        _w15.key = 'F3'    # edit_window.nml:210

        _w16.text = _bind(lambda _o: _tr('~S~ave'), yielding=True)    # edit_window.nml:212
        _w16.command = SaveText    # edit_window.nml:213
        _w16.key = 'F2'    # edit_window.nml:214

        _w17.text = _bind(lambda _o: _tr('Save ~a~s...'), yielding=True)    # edit_window.nml:216
        _w17.command = SaveTextAs    # edit_window.nml:217
        _w17.key = 'Shift-F2'    # edit_window.nml:218

        _w18.text = _bind(lambda _o: _tr('Save a~l~l...'), yielding=True)    # edit_window.nml:220
        _w18.command = SaveAll    # edit_window.nml:221
        _w18.key = 'Ctrl-F2'    # edit_window.nml:222

        _w20.text = _bind(lambda _o: _tr('~P~rint'), yielding=True)    # edit_window.nml:225
        _w20.command = PrintFile    # edit_window.nml:226
        _w20.key = 'F8'    # edit_window.nml:227

        _w21.text = _bind(lambda _o: _tr('Print ~b~lock'), yielding=True)    # edit_window.nml:229
        _w21.command = PrintBlock    # edit_window.nml:230
        _w21.key = 'Shift-F8'    # edit_window.nml:231

        _w23.text = _bind(lambda _o: _tr('E~x~it'), yielding=True)    # edit_window.nml:234
        _w23.command = CloseWindow    # edit_window.nml:235
        _w23.key = 'Ctrl-F4'    # edit_window.nml:236

        self.edit_menu_search.text = _bind(    # edit_window.nml:239
            lambda _o: _tr('~S~earch'),
            yielding=True,
        )

        _w24.text = _bind(lambda _o: _tr('Find ~b~ar'), yielding=True)    # edit_window.nml:242
        _w24.tooltip = _bind(    # edit_window.nml:243
            lambda _o: _tr('Search as you type, in a bar over the text'),
            yielding=True,
        )
        _w24.command = ShowFindBar    # edit_window.nml:244
        _w24.key = 'Ctrl-F'    # edit_window.nml:245

        _w25.text = _bind(lambda _o: _tr('Replace b~a~r'), yielding=True)    # edit_window.nml:247
        _w25.command = ShowReplaceBar    # edit_window.nml:248
        _w25.key = 'Ctrl-R'    # edit_window.nml:249

        _w27.text = _bind(lambda _o: _tr('~F~ind...'), yielding=True)    # edit_window.nml:252
        _w27.command = StartSearch    # edit_window.nml:253
        _w27.key = 'F7'    # edit_window.nml:254

        _w28.text = _bind(lambda _o: _tr('~R~eplace...'), yielding=True)    # edit_window.nml:256
        _w28.command = Replace    # edit_window.nml:257
        _w28.key = 'Ctrl-F7'    # edit_window.nml:258

        _w29.text = _bind(lambda _o: _tr('~S~earch again'), yielding=True)    # edit_window.nml:260
        _w29.command = ContSearch    # edit_window.nml:261
        _w29.key = 'Shift-F7'    # edit_window.nml:262

        _w30.text = _bind(lambda _o: _tr('Re~v~ersed search'), yielding=True)    # edit_window.nml:264
        _w30.command = ReverseSearch    # edit_window.nml:265
        _w30.key = 'Alt-F7'    # edit_window.nml:266

        _w31.text = _bind(    # edit_window.nml:268
            lambda _o: _tr('~G~o to line number...'),
            yielding=True,
        )
        _w31.command = GotoLineNumber    # edit_window.nml:269
        _w31.key = 'Alt-G'    # edit_window.nml:270

        _w32.text = _bind(lambda _o: _tr('~M~atching bracket'), yielding=True)    # edit_window.nml:273
        _w32.tooltip = _bind(    # edit_window.nml:274
            lambda _o: _tr('Jump to the bracket that pairs with the one at the cursor'),
            yielding=True,
        )
        _w32.command = BracketPair    # edit_window.nml:275
        _w32.key = 'Alt-Left'    # edit_window.nml:276

        self.edit_menu_paragraph.text = _bind(    # edit_window.nml:279
            lambda _o: _tr('Pa~r~agraph'),
            yielding=True,
        )

        _w33.text = _bind(lambda _o: _tr('~J~ustify'), yielding=True)    # edit_window.nml:281
        _w33.tooltip = _bind(    # edit_window.nml:282
            lambda _o: _tr("Justify the block's paragraph to both margins"),
            yielding=True,
        )
        _w33.command = FJustify    # edit_window.nml:283
        _w33.key = 'Alt-J'    # edit_window.nml:284

        _w34.text = _bind(lambda _o: _tr('~R~ight'), yielding=True)    # edit_window.nml:286
        _w34.command = FRight    # edit_window.nml:287
        _w34.key = 'Alt-R'    # edit_window.nml:288

        _w35.text = _bind(lambda _o: _tr('~L~eft'), yielding=True)    # edit_window.nml:290
        _w35.command = FLeft    # edit_window.nml:291
        _w35.key = 'Alt-L'    # edit_window.nml:292

        _w36.text = _bind(lambda _o: _tr('~C~enter'), yielding=True)    # edit_window.nml:294
        _w36.command = FCenter    # edit_window.nml:295
        _w36.key = 'Alt-C'    # edit_window.nml:296

        _w38.text = _bind(lambda _o: _tr('~M~argins...'), yielding=True)    # edit_window.nml:299
        _w38.command = SetMargins    # edit_window.nml:300

        self.edit_menu_block.text = _bind(    # edit_window.nml:303
            lambda _o: _tr('~B~lock'),
            yielding=True,
        )

        _w39.text = _bind(lambda _o: _tr('~M~ove'), yielding=True)    # edit_window.nml:305
        _w39.command = MoveBlock    # edit_window.nml:306
        _w39.key = 'Alt-Shift-V'    # edit_window.nml:307

        _w40.text = _bind(lambda _o: _tr('~C~opy'), yielding=True)    # edit_window.nml:309
        _w40.command = CopyBlock    # edit_window.nml:310
        _w40.key = 'Alt-Shift-K'    # edit_window.nml:311

        _w41.text = _bind(lambda _o: _tr('~I~ndent'), yielding=True)    # edit_window.nml:313
        _w41.command = IndentBlock    # edit_window.nml:314
        _w41.key = 'Alt-Shift-I'    # edit_window.nml:315

        _w42.text = _bind(lambda _o: _tr('~U~nindent'), yielding=True)    # edit_window.nml:317
        _w42.command = UnindentBlock    # edit_window.nml:318
        _w42.key = 'Alt-Shift-O'    # edit_window.nml:319

        _w43.text = _bind(lambda _o: _tr('~H~ide/show block'), yielding=True)    # edit_window.nml:322
        _w43.tooltip = _bind(    # edit_window.nml:323
            lambda _o: _tr('Hide the marked block, or show it again'),
            yielding=True,
        )
        _w43.command = HideBlock    # edit_window.nml:324
        _w43.key = 'Alt-H'    # edit_window.nml:325

        _w45.text = _bind(lambda _o: _tr('U~p~percase'), yielding=True)    # edit_window.nml:328
        _w45.command = UpcaseBlock    # edit_window.nml:329
        _w45.key = 'Alt-Shift-U'    # edit_window.nml:330

        _w46.text = _bind(lambda _o: _tr('~L~owercase'), yielding=True)    # edit_window.nml:332
        _w46.command = LowcaseBlock    # edit_window.nml:333
        _w46.key = 'Alt-Shift-L'    # edit_window.nml:334

        _w47.text = _bind(lambda _o: _tr('Capi~t~alize'), yielding=True)    # edit_window.nml:336
        _w47.command = CapitalizeBlock    # edit_window.nml:337
        _w47.key = 'Alt-Shift-C'    # edit_window.nml:338

        _w49.text = _bind(lambda _o: _tr('~S~ort'), yielding=True)    # edit_window.nml:341
        _w49.tooltip = _bind(    # edit_window.nml:342
            lambda _o: _tr('Sort the lines by the column block'),
            yielding=True,
        )
        _w49.command = SortBlock    # edit_window.nml:343
        _w49.key = 'Alt-T'    # edit_window.nml:344

        _w50.text = _bind(lambda _o: _tr('C~a~lculate sum'), yielding=True)    # edit_window.nml:347
        _w50.tooltip = _bind(    # edit_window.nml:348
            lambda _o: _tr("Add up the column block's numbers; the sum goes to the clipboard"),
            yielding=True,
        )
        _w50.command = CalcBlock    # edit_window.nml:349
        _w50.key = 'Alt-Ins'    # edit_window.nml:350

        self.edit_menu_misc.text = _bind(    # edit_window.nml:353
            lambda _o: _tr('~M~isc'),
            yielding=True,
        )

        _w51.text = _bind(lambda _o: _tr('Insert ~d~ate'), yielding=True)    # edit_window.nml:355
        _w51.command = InsertDate    # edit_window.nml:356
        _w51.key = 'Alt-Shift-D'    # edit_window.nml:357

        _w52.text = _bind(lambda _o: _tr('Insert ~t~ime'), yielding=True)    # edit_window.nml:359
        _w52.command = InsertTime    # edit_window.nml:360
        _w52.key = 'Alt-Shift-T'    # edit_window.nml:361

        _w53.text = _bind(lambda _o: _tr('Du~p~licate line'), yielding=True)    # edit_window.nml:363
        _w53.command = DuplicateLine    # edit_window.nml:364
        _w53.key = 'F6'    # edit_window.nml:365

        _w54.text = _bind(lambda _o: _tr('Character ta~b~le'), yielding=True)    # edit_window.nml:367
        _w54.command = AsciiTable    # edit_window.nml:368
        _w54.key = 'Ctrl P'    # edit_window.nml:369

        _w55.text = _bind(lambda _o: _tr('Line Dra~w~ing'), yielding=True)    # edit_window.nml:371
        _w55.tooltip = _bind(    # edit_window.nml:372
            lambda _o: _tr('Draw lines with the arrow keys: off, single, double'),
            yielding=True,
        )
        _w55.command = SwitchDrawMode    # edit_window.nml:373
        _w55.key = 'F4'    # edit_window.nml:374

        self.edit_menu_misc_uppercase.text = _bind(    # edit_window.nml:378
            lambda _o: _tr('~U~ppercase'),
            yielding=True,
        )

        _w57.text = _bind(lambda _o: _tr('~W~ord'), yielding=True)    # edit_window.nml:380
        _w57.command = UpWord    # edit_window.nml:381
        _w57.key = 'Ctrl ['    # edit_window.nml:382

        _w58.text = _bind(lambda _o: _tr('~L~ine'), yielding=True)    # edit_window.nml:384
        _w58.command = UpString    # edit_window.nml:385
        _w58.key = 'Ctrl+Shift ['    # edit_window.nml:386

        _w59.text = _bind(lambda _o: _tr('~B~lock'), yielding=True)    # edit_window.nml:388
        _w59.command = UpcaseBlock    # edit_window.nml:389
        _w59.key = 'Alt-Shift-U'    # edit_window.nml:390

        self.edit_menu_misc_lowercase.text = _bind(    # edit_window.nml:393
            lambda _o: _tr('~L~owercase'),
            yielding=True,
        )

        _w60.text = _bind(lambda _o: _tr('~W~ord'), yielding=True)    # edit_window.nml:395
        _w60.command = LowWord    # edit_window.nml:396
        _w60.key = 'Ctrl ]'    # edit_window.nml:397

        _w61.text = _bind(lambda _o: _tr('~L~ine'), yielding=True)    # edit_window.nml:399
        _w61.command = LowString    # edit_window.nml:400
        _w61.key = 'Ctrl+Shift ]'    # edit_window.nml:401

        _w62.text = _bind(lambda _o: _tr('~B~lock'), yielding=True)    # edit_window.nml:403
        _w62.command = LowcaseBlock    # edit_window.nml:404
        _w62.key = 'Alt-Shift-L'    # edit_window.nml:405

        self.edit_menu_misc_capitalize.text = _bind(    # edit_window.nml:408
            lambda _o: _tr('~C~apitalize'),
            yielding=True,
        )

        _w63.text = _bind(lambda _o: _tr('~W~ord'), yielding=True)    # edit_window.nml:410
        _w63.command = CapWord    # edit_window.nml:411
        _w63.key = 'Ctrl \\'    # edit_window.nml:412

        _w64.text = _bind(lambda _o: _tr('~L~ine'), yielding=True)    # edit_window.nml:414
        _w64.command = CapString    # edit_window.nml:415
        _w64.key = 'Ctrl+Shift \\'    # edit_window.nml:416

        _w65.text = _bind(lambda _o: _tr('~B~lock'), yielding=True)    # edit_window.nml:418
        _w65.command = CapitalizeBlock    # edit_window.nml:419
        _w65.key = 'Alt-Shift-C'    # edit_window.nml:420

        self.edit_menu_options.text = _bind(    # edit_window.nml:423
            lambda _o: _tr('Optio~n~s'),
            yielding=True,
        )

        _w66.text = _bind(lambda _o: _tr('~B~ackspace indents'), yielding=True)    # edit_window.nml:425
        _w66.tooltip = _bind(    # edit_window.nml:426
            lambda _o: _tr("Backspace at a line's start goes back to an indent above"),
            yielding=True,
        )
        _w66.command = SwitchBack    # edit_window.nml:427

        _w67.text = _bind(lambda _o: _tr('AutoB~r~ackets'), yielding=True)    # edit_window.nml:429
        _w67.command = SwitchBrackets    # edit_window.nml:430

        _w68.text = _bind(lambda _o: _tr('Auto~i~ndent'), yielding=True)    # edit_window.nml:432
        _w68.command = SwitchIndent    # edit_window.nml:433

        _w69.text = _bind(lambda _o: _tr('~A~uto wrap'), yielding=True)    # edit_window.nml:435
        _w69.command = SwitchSave    # edit_window.nml:436

        _w70.text = _bind(lambda _o: _tr('~J~ustify on wrap'), yielding=True)    # edit_window.nml:438
        _w70.tooltip = _bind(    # edit_window.nml:439
            lambda _o: _tr('Widen a wrapped line to the margin'),
            yielding=True,
        )
        _w70.command = SwitchWrap    # edit_window.nml:440

        _w71.text = _bind(lambda _o: _tr('~V~ertical blocks'), yielding=True)    # edit_window.nml:442
        _w71.tooltip = _bind(    # edit_window.nml:443
            lambda _o: _tr('Mark column blocks instead of line ones'),
            yielding=True,
        )
        _w71.command = SwitchBlock    # edit_window.nml:444

        _w72.text = _bind(lambda _o: _tr('Opti~m~al fill'), yielding=True)    # edit_window.nml:446
        _w72.tooltip = _bind(    # edit_window.nml:447
            lambda _o: _tr('Write blanks as tabs where they reach a tab stop'),
            yielding=True,
        )
        _w72.command = SwitchFill    # edit_window.nml:448

        _w73.text = _bind(    # edit_window.nml:450
            lambda _o: _tr('Current ~l~ine highlight'),
            yielding=True,
        )
        _w73.command = SwitchHiLine    # edit_window.nml:451

        _w74.text = _bind(    # edit_window.nml:453
            lambda _o: _tr('Current ~c~olumn highlight'),
            yielding=True,
        )
        _w74.command = SwitchHiColumn    # edit_window.nml:454

        _w75.text = _bind(lambda _o: _tr('Syntax ~h~ighlight'), yielding=True)    # edit_window.nml:456
        _w75.command = SwitchHighLight    # edit_window.nml:457

        _w76.text = _bind(    # edit_window.nml:460
            lambda _o: _tr('Show hi~d~den characters'),
            yielding=True,
        )
        _w76.command = SwitchHiddenChars    # edit_window.nml:461

        self.edit_menu_file_type.text = _bind(    # edit_window.nml:468
            lambda _o: _tr('File t~y~pe'),
            yielding=True,
        )
        self.edit_menu_file_type.key_command = ChooseFileType    # edit_window.nml:469

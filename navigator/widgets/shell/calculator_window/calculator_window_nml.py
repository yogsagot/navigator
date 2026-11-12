# navml: generated
"""Generated from ``calculator_window.nml``.

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
from navkit.reactive import reactive as _reactive

from navml.component import Component as _Component
from navigator.widgets.shell.calculator_window.bit_grid import BitGrid    # calculator_window.nml:1
from navigator.widgets.shell.calculator_window.calc_line import CalcLine    # calculator_window.nml:2
from navigator.widgets.shell.calculator_window.commands import CalculatorClassic, CalculatorCopy, CalculatorProgramming, CalculatorScientific, CalculatorSimple, ToggleBitKeypad    # calculator_window.nml:3
from navigator.widgets.manager.commands import Calculator    # calculator_window.nml:4
from navigator.widgets.shell.calculator_window.keypad import Keypad    # calculator_window.nml:5
from navkit.widget import Widget    # calculator_window.nml:6
from navml.commands import CloseWindow    # calculator_window.nml:7
from navml.widgets.dialog.button import Button    # calculator_window.nml:8
from navml.widgets.dialog.button_row import ButtonRow    # calculator_window.nml:9
from navml.widgets.dialog.check_boxes import CheckBoxes    # calculator_window.nml:10
from navml.widgets.dialog.commands import Cancel, Default, SelectNext, SelectPrevious    # calculator_window.nml:11
from navml.widgets.dialog.history import History    # calculator_window.nml:12
from navml.widgets.dialog.label import Label    # calculator_window.nml:13
from navml.widgets.dialog.radio_buttons import RadioButtons    # calculator_window.nml:14
from navml.widgets.dialog.static_text import StaticText    # calculator_window.nml:15
from navml.widgets.menu.menu_item import MenuItem    # calculator_window.nml:16
from navml.widgets.menu.menu_line import MenuLine    # calculator_window.nml:17
from navml.widgets.menu.sub_menu import SubMenu    # calculator_window.nml:18
from navml.widgets.window import Window    # calculator_window.nml:19

__navml_component__ = "CalculatorWindow"

__all__ = ["CalculatorWindow"]


class CalculatorWindow(Window, _Component):
    """Ctrl+F6, Utilities > Calculator: DOS Navigator's ``dlgCalculator``, and

    three faces beside it.

    A dialog DN put on the desktop as a window (``InsertWindow``), so it stays
    up beside the others; one at a time.  *Classic* is DN's, laid out where
    the resource and ``InsertCalc`` put things: the expression with its
    history, *Copy As*'s five forms, the indicator's five rows beside them --
    decimal, hexadecimal, binary, octal and the exponent form, worked out as
    the line is typed -- and *Evaluate*, *Copy* and *Close* along the bottom.
    Help is left out.

    **A departure, asked for**: *Simple* (the default), *Scientific* and
    *Programming* put a pad of keys under the same line, with its value worked
    out under it, and the strip of four along the top, the window's own
    *Calculator* menu and Ctrl+1..4 (Ctrl+F6 again, where a terminal sends no
    Ctrl+digit) choose between them.  The window takes each face's size.
    """

    #: The document this class was generated from.
    __navml_source__ = "calculator_window.nml"

    #: A dialog's keys, which a window does not have of its own: Esc closes,
    #: Enter evaluates, Tab walks the controls -- this window's alone.
    keys = {    # calculator_window.nml:58
        'escape': Cancel,    # calculator_window.nml:59
        'enter': Default,    # calculator_window.nml:60
        'tab': SelectNext,    # calculator_window.nml:61
        'shift+tab': SelectPrevious,    # calculator_window.nml:62
        'ctrl+1': CalculatorSimple,    # calculator_window.nml:63
        'ctrl+2': CalculatorClassic,    # calculator_window.nml:64
        'ctrl+3': CalculatorScientific,    # calculator_window.nml:65
        'ctrl+4': CalculatorProgramming,    # calculator_window.nml:66
        'ctrl+f6': Calculator,    # calculator_window.nml:68
    }

    #: ``simple``, ``classic``, ``scientific`` or ``programming``; the Python
    #: half's ``set_mode`` is what changes it.
    mode: str = _reactive('simple')    # calculator_window.nml:44

    #: The indicator's five rows (``TIndicator.Draw``), the Python half's.
    rows = _reactive(factory=lambda: ['', '', '', '', ''])    # calculator_window.nml:46

    #: The pads' value under the line, the Python half's.
    result: str = _reactive('')    # calculator_window.nml:48

    #: Scientific's ``M``, ``2nd`` and ``hyp`` marks, the Python half's.
    marks: str = _reactive('')    # calculator_window.nml:50

    #: Programming's four forms: hexadecimal, decimal, octal and binary.
    forms = _reactive(factory=lambda: ['', '', '', ''])    # calculator_window.nml:52

    #: Programming's bits to flip shown in place of its keys.
    bit_keypad: bool = _reactive(False)    # calculator_window.nml:54

    #: Ids, annotated so the hand-written half completes them.
    mode_strip: RadioButtons    # calculator_window.nml:73
    expression_caption: Label    # calculator_window.nml:85
    line: CalcLine    # calculator_window.nml:95
    history: History    # calculator_window.nml:107
    result_row: StaticText    # calculator_window.nml:118
    angle: RadioButtons    # calculator_window.nml:129
    marks_row: StaticText    # calculator_window.nml:139
    classic: Widget    # calculator_window.nml:151
    copy_caption: Label    # calculator_window.nml:160
    copy_as: RadioButtons    # calculator_window.nml:168
    row0: StaticText    # calculator_window.nml:177
    row1: StaticText    # calculator_window.nml:187
    row2: StaticText    # calculator_window.nml:197
    row3: StaticText    # calculator_window.nml:207
    row4: StaticText    # calculator_window.nml:217
    evaluate_button: Button    # calculator_window.nml:228
    copy_button: Button    # calculator_window.nml:247
    close_button: Button    # calculator_window.nml:251
    programming: Widget    # calculator_window.nml:257
    base: RadioButtons    # calculator_window.nml:266
    hex_row: StaticText    # calculator_window.nml:275
    dec_row: StaticText    # calculator_window.nml:285
    oct_row: StaticText    # calculator_window.nml:295
    bin_row: StaticText    # calculator_window.nml:305
    word: RadioButtons    # calculator_window.nml:315
    signed: CheckBoxes    # calculator_window.nml:324
    pad: Keypad    # calculator_window.nml:335
    bit_grid: BitGrid    # calculator_window.nml:349
    calculator_menu: SubMenu    # calculator_window.nml:361

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_evaluate_button_click(self, event: _Event) -> bool:    # calculator_window.nml:228
        """``evaluate_button`` raised an event whose handler is ``on_click``."""
        return False

    async def on_copy_button_click(self, event: _Event) -> bool:    # calculator_window.nml:247
        """``copy_button`` raised an event whose handler is ``on_click``."""
        return False

    async def on_close_button_click(self, event: _Event) -> bool:    # calculator_window.nml:251
        """``close_button`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.mode_strip = RadioButtons(parent=self)    # calculator_window.nml:72
        self.expression_caption = Label(parent=self)    # calculator_window.nml:84
        self.line = CalcLine(parent=self)    # calculator_window.nml:94
        self.history = History(parent=self)    # calculator_window.nml:106
        self.result_row = StaticText(parent=self)    # calculator_window.nml:117
        self.angle = RadioButtons(parent=self)    # calculator_window.nml:128
        self.marks_row = StaticText(parent=self)    # calculator_window.nml:138
        self.classic = Widget(parent=self)    # calculator_window.nml:150
        self.copy_caption = Label(parent=self.classic)    # calculator_window.nml:159
        self.copy_as = RadioButtons(parent=self.classic)    # calculator_window.nml:167
        self.row0 = StaticText(parent=self.classic)    # calculator_window.nml:176
        self.row1 = StaticText(parent=self.classic)    # calculator_window.nml:186
        self.row2 = StaticText(parent=self.classic)    # calculator_window.nml:196
        self.row3 = StaticText(parent=self.classic)    # calculator_window.nml:206
        self.row4 = StaticText(parent=self.classic)    # calculator_window.nml:216
        self.evaluate_button = Button(parent=self.classic)    # calculator_window.nml:227
        _w1 = ButtonRow(parent=self.classic)    # calculator_window.nml:237
        self.copy_button = Button(parent=_w1)    # calculator_window.nml:246
        self.close_button = Button(parent=_w1)    # calculator_window.nml:250
        self.programming = Widget(parent=self)    # calculator_window.nml:256
        self.base = RadioButtons(parent=self.programming)    # calculator_window.nml:265
        self.hex_row = StaticText(parent=self.programming)    # calculator_window.nml:274
        self.dec_row = StaticText(parent=self.programming)    # calculator_window.nml:284
        self.oct_row = StaticText(parent=self.programming)    # calculator_window.nml:294
        self.bin_row = StaticText(parent=self.programming)    # calculator_window.nml:304
        self.word = RadioButtons(parent=self.programming)    # calculator_window.nml:314
        self.signed = CheckBoxes(parent=self.programming)    # calculator_window.nml:323
        self.pad = Keypad(parent=self)    # calculator_window.nml:334
        self.bit_grid = BitGrid(parent=self)    # calculator_window.nml:348
        self.calculator_menu = SubMenu(parent=self)    # calculator_window.nml:360
        _w2 = MenuItem(parent=self.calculator_menu)    # calculator_window.nml:363
        _w3 = MenuItem(parent=self.calculator_menu)    # calculator_window.nml:364
        _w4 = MenuItem(parent=self.calculator_menu)    # calculator_window.nml:365
        _w5 = MenuItem(parent=self.calculator_menu)    # calculator_window.nml:366
        _w6 = MenuLine(parent=self.calculator_menu)    # calculator_window.nml:367
        _w7 = MenuItem(parent=self.calculator_menu)    # calculator_window.nml:368
        _w8 = MenuItem(parent=self.calculator_menu)    # calculator_window.nml:369
        _w9 = MenuLine(parent=self.calculator_menu)    # calculator_window.nml:370
        _w10 = MenuItem(parent=self.calculator_menu)    # calculator_window.nml:371

        self.title = _bind(lambda _o: _tr('Calculator'), yielding=True)    # calculator_window.nml:38
        self.zoomable = False    # calculator_window.nml:39
        self.resizable = False    # calculator_window.nml:40

        self.mode_strip.y = 1    # calculator_window.nml:74
        self.mode_strip.height = _bind(    # calculator_window.nml:75
            lambda _o: 2 if self.mode in ('simple', 'classic') else 1
        )
        self.mode_strip.items = _bind(    # calculator_window.nml:81
            lambda _o: [_tr('~S~imple'), _tr('C~l~assic'), _tr('Sc~i~entific'), _tr('Pro~g~ramming')],
            yielding=True,
        )
        self.mode_strip.tooltips = _bind(    # calculator_window.nml:82
            lambda _o: [_tr('A pocket calculator'), _tr("DOS Navigator's calculator: the expression in five forms"), _tr('Functions, angles, memory and the last answer'), _tr('A word of 8 to 64 bits in four bases')],
            yielding=True,
        )
        self.mode_strip.x = 2    # calculator_window.nml:77
        self.mode_strip.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # calculator_window.nml:78

        self.expression_caption.visible = _bind(    # calculator_window.nml:86
            lambda _o: self.mode == 'classic'
        )
        self.expression_caption.x = 2    # calculator_window.nml:87
        self.expression_caption.y = 4    # calculator_window.nml:88
        self.expression_caption.width = 12    # calculator_window.nml:89
        self.expression_caption.text = _bind(    # calculator_window.nml:90
            lambda _o: _tr('Ex~p~ression'),
            yielding=True,
        )
        self.expression_caption.link = _bind(lambda _o: self.line)    # calculator_window.nml:91

        self.line.tooltip = _bind(    # calculator_window.nml:96
            lambda _o: _tr('Numbers as 12, 1.5, 1E+3, $FF, 0x1F, 101b, 17o; + - * / ^ %, & | \\ ~ << >>, comparisons, IF, SIN, SQRT, LN, PI'),
            yielding=True,
        )
        self.line.x = 2    # calculator_window.nml:97
        self.line.y = _bind(    # calculator_window.nml:98
            lambda _o: 5 if self.mode == 'classic' else 4 if self.mode == 'simple' else 3
        )
        self.line.width = _bind(lambda _o: max(1, _o.parent.width - 7))    # calculator_window.nml:99

        self.history.link = _bind(lambda _o: self.line)    # calculator_window.nml:108
        self.history.history_id = 'calc'    # calculator_window.nml:109
        self.history.y = _bind(lambda _o: self.line.y)    # calculator_window.nml:110
        self.history.width = 3    # calculator_window.nml:111
        self.history.height = 1    # calculator_window.nml:112
        self.history.x = _bind(    # calculator_window.nml:114
            lambda _o: max(0, _o.parent.width - 2 - _o.width)
        )

        self.result_row.visible = _bind(    # calculator_window.nml:119
            lambda _o: self.mode in ('simple', 'scientific')
        )
        self.result_row.y = _bind(lambda _o: self.line.y + 1)    # calculator_window.nml:120
        self.result_row.align = 'right'    # calculator_window.nml:124
        self.result_row.text = _bind(lambda _o: self.result)    # calculator_window.nml:125
        self.result_row.tooltip = _bind(    # calculator_window.nml:126
            lambda _o: _tr("The line's value; Enter or = puts it in the line"),
            yielding=True,
        )
        self.result_row.x = 2    # calculator_window.nml:122
        self.result_row.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # calculator_window.nml:123

        self.angle.visible = _bind(lambda _o: self.mode == 'scientific')    # calculator_window.nml:130
        self.angle.x = 2    # calculator_window.nml:131
        self.angle.y = 5    # calculator_window.nml:132
        self.angle.width = 30    # calculator_window.nml:133
        self.angle.height = 1    # calculator_window.nml:134
        self.angle.items = _bind(    # calculator_window.nml:135
            lambda _o: [_tr('~D~eg'), _tr('~R~ad'), _tr('Gr~a~d')],
            yielding=True,
        )
        self.angle.tooltips = _bind(    # calculator_window.nml:136
            lambda _o: [_tr('Angles in degrees, a turn 360'), _tr('Angles in radians, a turn 2π'), _tr('Angles in grads, a turn 400')],
            yielding=True,
        )

        self.marks_row.visible = _bind(lambda _o: self.mode == 'scientific')    # calculator_window.nml:140
        self.marks_row.y = 5    # calculator_window.nml:141
        self.marks_row.align = 'right'    # calculator_window.nml:145
        self.marks_row.text = _bind(lambda _o: self.marks)    # calculator_window.nml:146
        self.marks_row.tooltip = _bind(    # calculator_window.nml:147
            lambda _o: _tr("M: a value in memory; 2nd and hyp: the keys' other functions"),
            yielding=True,
        )
        self.marks_row.x = 34    # calculator_window.nml:143
        self.marks_row.width = _bind(lambda _o: max(0, _o.parent.width - 36))    # calculator_window.nml:144

        self.classic.visible = _bind(lambda _o: self.mode == 'classic')    # calculator_window.nml:152
        self.classic.y = 7    # calculator_window.nml:153
        self.classic.height = 9    # calculator_window.nml:154
        self.classic.x = 0    # calculator_window.nml:156
        self.classic.width = _bind(lambda _o: max(0, _o.parent.width))    # calculator_window.nml:157

        self.copy_caption.x = 2    # calculator_window.nml:161
        self.copy_caption.y = 0    # calculator_window.nml:162
        self.copy_caption.width = 10    # calculator_window.nml:163
        self.copy_caption.text = _bind(    # calculator_window.nml:164
            lambda _o: _tr('Copy ~A~s'),
            yielding=True,
        )
        self.copy_caption.link = _bind(lambda _o: self.copy_as)    # calculator_window.nml:165

        self.copy_as.x = 2    # calculator_window.nml:169
        self.copy_as.y = 1    # calculator_window.nml:170
        self.copy_as.width = 9    # calculator_window.nml:171
        self.copy_as.height = 5    # calculator_window.nml:172
        self.copy_as.items = _bind(    # calculator_window.nml:173
            lambda _o: [_tr('~D~EC'), _tr('~H~EX'), _tr('~B~IN'), _tr('~O~CT'), _tr('~E~XP')],
            yielding=True,
        )
        self.copy_as.tooltips = _bind(    # calculator_window.nml:174
            lambda _o: [_tr('Copy copies the value in decimal'), _tr('Copy copies the value in hexadecimal'), _tr('Copy copies the value in binary'), _tr('Copy copies the value in octal'), _tr('Copy copies the value in scientific notation')],
            yielding=True,
        )

        self.row0.y = 1    # calculator_window.nml:178
        self.row0.align = 'right'    # calculator_window.nml:182
        self.row0.text = _bind(lambda _o: self.rows[0])    # calculator_window.nml:183
        self.row0.tooltip = _bind(    # calculator_window.nml:184
            lambda _o: _tr('The value in decimal'),
            yielding=True,
        )
        self.row0.x = 12    # calculator_window.nml:180
        self.row0.width = _bind(lambda _o: max(0, _o.parent.width - 14))    # calculator_window.nml:181

        self.row1.y = 2    # calculator_window.nml:188
        self.row1.align = 'right'    # calculator_window.nml:192
        self.row1.text = _bind(lambda _o: self.rows[1])    # calculator_window.nml:193
        self.row1.tooltip = _bind(    # calculator_window.nml:194
            lambda _o: _tr("The whole part in hexadecimal, two's complement in 64 bits"),
            yielding=True,
        )
        self.row1.x = 12    # calculator_window.nml:190
        self.row1.width = _bind(lambda _o: max(0, _o.parent.width - 14))    # calculator_window.nml:191

        self.row2.y = 3    # calculator_window.nml:198
        self.row2.align = 'right'    # calculator_window.nml:202
        self.row2.text = _bind(lambda _o: self.rows[2])    # calculator_window.nml:203
        self.row2.tooltip = _bind(    # calculator_window.nml:204
            lambda _o: _tr("The whole part in binary, two's complement in 64 bits"),
            yielding=True,
        )
        self.row2.x = 12    # calculator_window.nml:200
        self.row2.width = _bind(lambda _o: max(0, _o.parent.width - 14))    # calculator_window.nml:201

        self.row3.y = 4    # calculator_window.nml:208
        self.row3.align = 'right'    # calculator_window.nml:212
        self.row3.text = _bind(lambda _o: self.rows[3])    # calculator_window.nml:213
        self.row3.tooltip = _bind(    # calculator_window.nml:214
            lambda _o: _tr("The whole part in octal, two's complement in 64 bits"),
            yielding=True,
        )
        self.row3.x = 12    # calculator_window.nml:210
        self.row3.width = _bind(lambda _o: max(0, _o.parent.width - 14))    # calculator_window.nml:211

        self.row4.y = 5    # calculator_window.nml:218
        self.row4.align = 'right'    # calculator_window.nml:222
        self.row4.text = _bind(lambda _o: self.rows[4])    # calculator_window.nml:223
        self.row4.tooltip = _bind(    # calculator_window.nml:224
            lambda _o: _tr('The value in scientific notation'),
            yielding=True,
        )
        self.row4.x = 12    # calculator_window.nml:220
        self.row4.width = _bind(lambda _o: max(0, _o.parent.width - 14))    # calculator_window.nml:221

        self.evaluate_button.text = _bind(    # calculator_window.nml:229
            lambda _o: _tr('E~v~aluate'),
            yielding=True,
        )
        self.evaluate_button.default = True    # calculator_window.nml:230
        self.evaluate_button.x = 3    # calculator_window.nml:231
        self.evaluate_button.y = 7    # calculator_window.nml:232
        self.evaluate_button.width = 12    # calculator_window.nml:233
        self.evaluate_button.height = 2    # calculator_window.nml:234
        self.evaluate_button.on_click = self.on_evaluate_button_click    # calculator_window.nml:228

        _w1.justify = 'start'    # calculator_window.nml:238
        _w1.button_width = 10    # calculator_window.nml:239
        _w1.spacing = 1    # calculator_window.nml:240
        _w1.y = 7# calculator_window.nml:241
        _w1.x = 16# calculator_window.nml:243
        _w1.width = _bind(lambda _o: max(0, _o.parent.width - 16))    # calculator_window.nml:244

        self.copy_button.text = _bind(lambda _o: _tr('~C~opy'), yielding=True)    # calculator_window.nml:248
        self.copy_button.on_click = self.on_copy_button_click    # calculator_window.nml:247

        self.close_button.text = _bind(lambda _o: _tr('Close'), yielding=True)    # calculator_window.nml:252
        self.close_button.on_click = self.on_close_button_click    # calculator_window.nml:251

        self.programming.visible = _bind(lambda _o: self.mode == 'programming')    # calculator_window.nml:258
        self.programming.y = 4    # calculator_window.nml:259
        self.programming.height = 5    # calculator_window.nml:260
        self.programming.x = 0    # calculator_window.nml:262
        self.programming.width = _bind(lambda _o: max(0, _o.parent.width))    # calculator_window.nml:263

        self.base.x = 2    # calculator_window.nml:267
        self.base.y = 0    # calculator_window.nml:268
        self.base.width = 9    # calculator_window.nml:269
        self.base.height = 4    # calculator_window.nml:270
        self.base.items = _bind(    # calculator_window.nml:271
            lambda _o: [_tr('~H~EX'), _tr('~D~EC'), _tr('~O~CT'), _tr('~B~IN')],
            yielding=True,
        )
        self.base.tooltips = _bind(    # calculator_window.nml:272
            lambda _o: [_tr('Type the numbers in hexadecimal'), _tr('Type the numbers in decimal'), _tr('Type the numbers in octal'), _tr('Type the numbers in binary')],
            yielding=True,
        )

        self.hex_row.y = 0    # calculator_window.nml:276
        self.hex_row.align = 'right'    # calculator_window.nml:280
        self.hex_row.text = _bind(lambda _o: self.forms[0])    # calculator_window.nml:281
        self.hex_row.tooltip = _bind(    # calculator_window.nml:282
            lambda _o: _tr("The value in hexadecimal, two's complement in the word"),
            yielding=True,
        )
        self.hex_row.x = 12    # calculator_window.nml:278
        self.hex_row.width = _bind(lambda _o: max(0, _o.parent.width - 14))    # calculator_window.nml:279

        self.dec_row.y = 1    # calculator_window.nml:286
        self.dec_row.align = 'right'    # calculator_window.nml:290
        self.dec_row.text = _bind(lambda _o: self.forms[1])    # calculator_window.nml:291
        self.dec_row.tooltip = _bind(    # calculator_window.nml:292
            lambda _o: _tr('The value in decimal'),
            yielding=True,
        )
        self.dec_row.x = 12    # calculator_window.nml:288
        self.dec_row.width = _bind(lambda _o: max(0, _o.parent.width - 14))    # calculator_window.nml:289

        self.oct_row.y = 2    # calculator_window.nml:296
        self.oct_row.align = 'right'    # calculator_window.nml:300
        self.oct_row.text = _bind(lambda _o: self.forms[2])    # calculator_window.nml:301
        self.oct_row.tooltip = _bind(    # calculator_window.nml:302
            lambda _o: _tr("The value in octal, two's complement in the word"),
            yielding=True,
        )
        self.oct_row.x = 12    # calculator_window.nml:298
        self.oct_row.width = _bind(lambda _o: max(0, _o.parent.width - 14))    # calculator_window.nml:299

        self.bin_row.y = 3    # calculator_window.nml:306
        self.bin_row.align = 'right'    # calculator_window.nml:310
        self.bin_row.text = _bind(lambda _o: self.forms[3])    # calculator_window.nml:311
        self.bin_row.tooltip = _bind(    # calculator_window.nml:312
            lambda _o: _tr("The value in binary, two's complement in the word"),
            yielding=True,
        )
        self.bin_row.x = 12    # calculator_window.nml:308
        self.bin_row.width = _bind(lambda _o: max(0, _o.parent.width - 14))    # calculator_window.nml:309

        self.word.x = 2    # calculator_window.nml:316
        self.word.y = 4    # calculator_window.nml:317
        self.word.width = 42    # calculator_window.nml:318
        self.word.height = 1    # calculator_window.nml:319
        self.word.items = _bind(    # calculator_window.nml:320
            lambda _o: [_tr('~Q~WORD'), _tr('D~W~ORD'), _tr('WO~R~D'), _tr('B~Y~TE')],
            yielding=True,
        )
        self.word.tooltips = _bind(    # calculator_window.nml:321
            lambda _o: [_tr('A word of 64 bits'), _tr('A word of 32 bits'), _tr('A word of 16 bits'), _tr('A word of 8 bits')],
            yielding=True,
        )

        self.signed.y = 4    # calculator_window.nml:325
        self.signed.height = 1    # calculator_window.nml:326
        self.signed.items = _bind(lambda _o: [_tr('Sig~n~ed')], yielding=True)    # calculator_window.nml:330
        self.signed.tooltips = _bind(    # calculator_window.nml:331
            lambda _o: [_tr("The word read as two's complement; unticked, unsigned")],
            yielding=True,
        )
        self.signed.x = 46    # calculator_window.nml:328
        self.signed.width = _bind(lambda _o: max(0, _o.parent.width - 48))    # calculator_window.nml:329

        self.pad.visible = _bind(    # calculator_window.nml:336
            lambda _o: self.mode != 'classic' and (not (self.mode == 'programming' and self.bit_keypad))
        )
        self.pad.y = _bind(lambda _o: 10 if self.mode == 'programming' else 7)    # calculator_window.nml:337
        self.pad.height = _bind(    # calculator_window.nml:338
            lambda _o: 10 if self.mode == 'programming' else 12
        )
        self.pad.x = 2    # calculator_window.nml:340
        self.pad.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # calculator_window.nml:341

        self.bit_grid.visible = _bind(    # calculator_window.nml:350
            lambda _o: self.mode == 'programming' and self.bit_keypad
        )
        self.bit_grid.y = 10    # calculator_window.nml:351
        self.bit_grid.height = 10    # calculator_window.nml:352
        self.bit_grid.tooltip = _bind(    # calculator_window.nml:356
            lambda _o: _tr('Click a bit, or Space on it, to flip it'),
            yielding=True,
        )
        self.bit_grid.x = 2    # calculator_window.nml:354
        self.bit_grid.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # calculator_window.nml:355

        self.calculator_menu.text = _bind(    # calculator_window.nml:360
            lambda _o: _tr('~C~alculator'),
            yielding=True,
        )
        self.calculator_menu.after = 'File'    # calculator_window.nml:360
        self.calculator_menu.tooltip = _bind(    # calculator_window.nml:362
            lambda _o: _tr("The calculator's faces, copying its value and closing it"),
            yielding=True,
        )

        _w2.text = _bind(lambda _o: _tr('~S~imple'), yielding=True)    # calculator_window.nml:363
        _w2.command = CalculatorSimple    # calculator_window.nml:363

        _w3.text = _bind(lambda _o: _tr('C~l~assic'), yielding=True)    # calculator_window.nml:364
        _w3.command = CalculatorClassic    # calculator_window.nml:364

        _w4.text = _bind(lambda _o: _tr('Sc~i~entific'), yielding=True)    # calculator_window.nml:365
        _w4.command = CalculatorScientific    # calculator_window.nml:365

        _w5.text = _bind(lambda _o: _tr('Pro~g~ramming'), yielding=True)    # calculator_window.nml:366
        _w5.command = CalculatorProgramming    # calculator_window.nml:366

        _w7.text = _bind(lambda _o: _tr('~C~opy'), yielding=True)    # calculator_window.nml:368
        _w7.command = CalculatorCopy    # calculator_window.nml:368

        _w8.text = _bind(    # calculator_window.nml:369
            lambda _o: _tr('~B~it toggling keypad'),
            yielding=True,
        )
        _w8.command = ToggleBitKeypad    # calculator_window.nml:369

        _w10.text = _bind(lambda _o: _tr('Cl~o~se'), yielding=True)    # calculator_window.nml:371
        _w10.command = CloseWindow    # calculator_window.nml:371

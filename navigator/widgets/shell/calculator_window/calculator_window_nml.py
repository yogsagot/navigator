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
from navigator.widgets.shell.calculator_window.calc_line import CalcLine    # calculator_window.nml:1
from navml.widgets.dialog.button import Button    # calculator_window.nml:2
from navml.widgets.dialog.commands import Cancel, Default, SelectNext, SelectPrevious    # calculator_window.nml:3
from navml.widgets.dialog.history import History    # calculator_window.nml:4
from navml.widgets.dialog.label import Label    # calculator_window.nml:5
from navml.widgets.dialog.radio_buttons import RadioButtons    # calculator_window.nml:6
from navml.widgets.dialog.static_text import StaticText    # calculator_window.nml:7
from navml.widgets.window import Window    # calculator_window.nml:8

__navml_component__ = "CalculatorWindow"

__all__ = ["CalculatorWindow"]


class CalculatorWindow(Window, _Component):
    """Ctrl+F6, Utilities > Calculator: DOS Navigator's ``dlgCalculator``.

    A dialog DN put on the desktop as a window (``InsertWindow``), so it stays
    up beside the others; one at a time.  Laid out where the resource and
    ``InsertCalc`` put things: the expression with its history, *Copy As*'s
    five forms, the indicator's five rows beside them -- decimal, hexadecimal,
    binary, octal and the exponent form, worked out as the line is typed --
    and *Evaluate*, *Copy* and *Close* along the bottom.  Help is left out.
    """

    #: The document this class was generated from.
    __navml_source__ = "calculator_window.nml"

    #: A dialog's keys, which a window does not have of its own: Esc closes,
    #: Enter evaluates, Tab walks the controls -- this window's alone.
    keys = {    # calculator_window.nml:28
        'escape': Cancel,    # calculator_window.nml:29
        'enter': Default,    # calculator_window.nml:30
        'tab': SelectNext,    # calculator_window.nml:31
        'shift+tab': SelectPrevious,    # calculator_window.nml:32
    }

    #: The indicator's five rows (``TIndicator.Draw``), the Python half's.
    rows = _reactive(factory=lambda: ['', '', '', '', ''])    # calculator_window.nml:24

    #: Ids, annotated so the hand-written half completes them.
    expression_caption: Label    # calculator_window.nml:35
    line: CalcLine    # calculator_window.nml:45
    history: History    # calculator_window.nml:53
    copy_caption: Label    # calculator_window.nml:62
    copy_as: RadioButtons    # calculator_window.nml:71
    row0: StaticText    # calculator_window.nml:80
    row1: StaticText    # calculator_window.nml:90
    row2: StaticText    # calculator_window.nml:100
    row3: StaticText    # calculator_window.nml:110
    row4: StaticText    # calculator_window.nml:120
    evaluate_button: Button    # calculator_window.nml:131
    copy_button: Button    # calculator_window.nml:141
    close_button: Button    # calculator_window.nml:149

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_evaluate_button_click(self, event: _Event) -> bool:    # calculator_window.nml:131
        """``evaluate_button`` raised an event whose handler is ``on_click``."""
        return False

    async def on_copy_button_click(self, event: _Event) -> bool:    # calculator_window.nml:141
        """``copy_button`` raised an event whose handler is ``on_click``."""
        return False

    async def on_close_button_click(self, event: _Event) -> bool:    # calculator_window.nml:149
        """``close_button`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.expression_caption = Label(parent=self)    # calculator_window.nml:34
        self.line = CalcLine(parent=self)    # calculator_window.nml:44
        self.history = History(parent=self)    # calculator_window.nml:52
        self.copy_caption = Label(parent=self)    # calculator_window.nml:61
        self.copy_as = RadioButtons(parent=self)    # calculator_window.nml:70
        self.row0 = StaticText(parent=self)    # calculator_window.nml:79
        self.row1 = StaticText(parent=self)    # calculator_window.nml:89
        self.row2 = StaticText(parent=self)    # calculator_window.nml:99
        self.row3 = StaticText(parent=self)    # calculator_window.nml:109
        self.row4 = StaticText(parent=self)    # calculator_window.nml:119
        self.evaluate_button = Button(parent=self)    # calculator_window.nml:130
        self.copy_button = Button(parent=self)    # calculator_window.nml:140
        self.close_button = Button(parent=self)    # calculator_window.nml:148

        self.title = _bind(lambda _o: _tr('Calculator'), yielding=True)    # calculator_window.nml:19
        self.zoomable = False    # calculator_window.nml:20
        self.resizable = False    # calculator_window.nml:21

        self.expression_caption.x = 2    # calculator_window.nml:36
        self.expression_caption.y = 2    # calculator_window.nml:37
        self.expression_caption.width = 12    # calculator_window.nml:38
        self.expression_caption.height = 1    # calculator_window.nml:39
        self.expression_caption.text = _bind(    # calculator_window.nml:40
            lambda _o: _tr('Ex~p~ression'),
            yielding=True,
        )
        self.expression_caption.link = _bind(lambda _o: self.line)    # calculator_window.nml:41

        self.line.tooltip = _bind(    # calculator_window.nml:46
            lambda _o: _tr('Numbers as 12, 1.5, 1E+3, $FF, 0x1F, 101b, 17o; + - * / ^ %, & | \\ ~ << >>, comparisons, IF, SIN, SQRT, LN, PI'),
            yielding=True,
        )
        self.line.x = 2    # calculator_window.nml:47
        self.line.y = 3    # calculator_window.nml:48
        self.line.width = _bind(lambda _o: max(1, _o.parent.width - 7))    # calculator_window.nml:49
        self.line.height = 1    # calculator_window.nml:50

        self.history.link = _bind(lambda _o: self.line)    # calculator_window.nml:54
        self.history.history_id = 'calc'    # calculator_window.nml:55
        self.history.x = _bind(lambda _o: max(0, _o.parent.width - 5))    # calculator_window.nml:56
        self.history.y = 3    # calculator_window.nml:57
        self.history.width = 3    # calculator_window.nml:58
        self.history.height = 1    # calculator_window.nml:59

        self.copy_caption.x = 2    # calculator_window.nml:63
        self.copy_caption.y = 5    # calculator_window.nml:64
        self.copy_caption.width = 10    # calculator_window.nml:65
        self.copy_caption.height = 1    # calculator_window.nml:66
        self.copy_caption.text = _bind(    # calculator_window.nml:67
            lambda _o: _tr('Copy ~A~s'),
            yielding=True,
        )
        self.copy_caption.link = _bind(lambda _o: self.copy_as)    # calculator_window.nml:68

        self.copy_as.x = 2    # calculator_window.nml:72
        self.copy_as.y = 6    # calculator_window.nml:73
        self.copy_as.width = 9    # calculator_window.nml:74
        self.copy_as.height = 5    # calculator_window.nml:75
        self.copy_as.items = _bind(    # calculator_window.nml:76
            lambda _o: [_tr('~D~EC'), _tr('~H~EX'), _tr('~B~IN'), _tr('~O~CT'), _tr('~E~XP')],
            yielding=True,
        )
        self.copy_as.tooltips = _bind(    # calculator_window.nml:77
            lambda _o: [_tr('Copy copies the value in decimal'), _tr('Copy copies the value in hexadecimal'), _tr('Copy copies the value in binary'), _tr('Copy copies the value in octal'), _tr('Copy copies the value in scientific notation')],
            yielding=True,
        )

        self.row0.x = 12    # calculator_window.nml:81
        self.row0.y = 6    # calculator_window.nml:82
        self.row0.width = _bind(lambda _o: max(0, _o.parent.width - 14))    # calculator_window.nml:83
        self.row0.height = 1    # calculator_window.nml:84
        self.row0.align = 'right'    # calculator_window.nml:85
        self.row0.text = _bind(lambda _o: self.rows[0])    # calculator_window.nml:86
        self.row0.tooltip = _bind(    # calculator_window.nml:87
            lambda _o: _tr('The value in decimal'),
            yielding=True,
        )

        self.row1.x = 12    # calculator_window.nml:91
        self.row1.y = 7    # calculator_window.nml:92
        self.row1.width = _bind(lambda _o: max(0, _o.parent.width - 14))    # calculator_window.nml:93
        self.row1.height = 1    # calculator_window.nml:94
        self.row1.align = 'right'    # calculator_window.nml:95
        self.row1.text = _bind(lambda _o: self.rows[1])    # calculator_window.nml:96
        self.row1.tooltip = _bind(    # calculator_window.nml:97
            lambda _o: _tr("The whole part in hexadecimal, two's complement in 64 bits"),
            yielding=True,
        )

        self.row2.x = 12    # calculator_window.nml:101
        self.row2.y = 8    # calculator_window.nml:102
        self.row2.width = _bind(lambda _o: max(0, _o.parent.width - 14))    # calculator_window.nml:103
        self.row2.height = 1    # calculator_window.nml:104
        self.row2.align = 'right'    # calculator_window.nml:105
        self.row2.text = _bind(lambda _o: self.rows[2])    # calculator_window.nml:106
        self.row2.tooltip = _bind(    # calculator_window.nml:107
            lambda _o: _tr("The whole part in binary, two's complement in 64 bits"),
            yielding=True,
        )

        self.row3.x = 12    # calculator_window.nml:111
        self.row3.y = 9    # calculator_window.nml:112
        self.row3.width = _bind(lambda _o: max(0, _o.parent.width - 14))    # calculator_window.nml:113
        self.row3.height = 1    # calculator_window.nml:114
        self.row3.align = 'right'    # calculator_window.nml:115
        self.row3.text = _bind(lambda _o: self.rows[3])    # calculator_window.nml:116
        self.row3.tooltip = _bind(    # calculator_window.nml:117
            lambda _o: _tr("The whole part in octal, two's complement in 64 bits"),
            yielding=True,
        )

        self.row4.x = 12    # calculator_window.nml:121
        self.row4.y = 10    # calculator_window.nml:122
        self.row4.width = _bind(lambda _o: max(0, _o.parent.width - 14))    # calculator_window.nml:123
        self.row4.height = 1    # calculator_window.nml:124
        self.row4.align = 'right'    # calculator_window.nml:125
        self.row4.text = _bind(lambda _o: self.rows[4])    # calculator_window.nml:126
        self.row4.tooltip = _bind(    # calculator_window.nml:127
            lambda _o: _tr('The value in scientific notation'),
            yielding=True,
        )

        self.evaluate_button.text = _bind(    # calculator_window.nml:132
            lambda _o: _tr('E~v~aluate'),
            yielding=True,
        )
        self.evaluate_button.default = True    # calculator_window.nml:133
        self.evaluate_button.x = 3    # calculator_window.nml:134
        self.evaluate_button.y = 12    # calculator_window.nml:135
        self.evaluate_button.width = 12    # calculator_window.nml:136
        self.evaluate_button.height = 2    # calculator_window.nml:137
        self.evaluate_button.on_click = self.on_evaluate_button_click    # calculator_window.nml:131

        self.copy_button.text = _bind(lambda _o: _tr('~C~opy'), yielding=True)    # calculator_window.nml:142
        self.copy_button.x = 16    # calculator_window.nml:143
        self.copy_button.y = 12    # calculator_window.nml:144
        self.copy_button.width = 10    # calculator_window.nml:145
        self.copy_button.height = 2    # calculator_window.nml:146
        self.copy_button.on_click = self.on_copy_button_click    # calculator_window.nml:141

        self.close_button.text = _bind(lambda _o: _tr('Close'), yielding=True)    # calculator_window.nml:150
        self.close_button.x = 27    # calculator_window.nml:151
        self.close_button.y = 12    # calculator_window.nml:152
        self.close_button.width = 10    # calculator_window.nml:153
        self.close_button.height = 2    # calculator_window.nml:154
        self.close_button.on_click = self.on_close_button_click    # calculator_window.nml:149

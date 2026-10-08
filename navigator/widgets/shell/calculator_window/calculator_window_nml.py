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
    history: History    # calculator_window.nml:52
    copy_caption: Label    # calculator_window.nml:61
    copy_as: RadioButtons    # calculator_window.nml:70
    row0: StaticText    # calculator_window.nml:78
    row1: StaticText    # calculator_window.nml:87
    row2: StaticText    # calculator_window.nml:96
    row3: StaticText    # calculator_window.nml:105
    row4: StaticText    # calculator_window.nml:114
    evaluate_button: Button    # calculator_window.nml:124
    copy_button: Button    # calculator_window.nml:134
    close_button: Button    # calculator_window.nml:142

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_evaluate_button_click(self, event: _Event) -> bool:    # calculator_window.nml:124
        """``evaluate_button`` raised an event whose handler is ``on_click``."""
        return False

    async def on_copy_button_click(self, event: _Event) -> bool:    # calculator_window.nml:134
        """``copy_button`` raised an event whose handler is ``on_click``."""
        return False

    async def on_close_button_click(self, event: _Event) -> bool:    # calculator_window.nml:142
        """``close_button`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.expression_caption = Label(parent=self)    # calculator_window.nml:34
        self.line = CalcLine(parent=self)    # calculator_window.nml:44
        self.history = History(parent=self)    # calculator_window.nml:51
        self.copy_caption = Label(parent=self)    # calculator_window.nml:60
        self.copy_as = RadioButtons(parent=self)    # calculator_window.nml:69
        self.row0 = StaticText(parent=self)    # calculator_window.nml:77
        self.row1 = StaticText(parent=self)    # calculator_window.nml:86
        self.row2 = StaticText(parent=self)    # calculator_window.nml:95
        self.row3 = StaticText(parent=self)    # calculator_window.nml:104
        self.row4 = StaticText(parent=self)    # calculator_window.nml:113
        self.evaluate_button = Button(parent=self)    # calculator_window.nml:123
        self.copy_button = Button(parent=self)    # calculator_window.nml:133
        self.close_button = Button(parent=self)    # calculator_window.nml:141

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

        self.line.x = 2    # calculator_window.nml:46
        self.line.y = 3    # calculator_window.nml:47
        self.line.width = _bind(lambda _o: max(1, _o.parent.width - 7))    # calculator_window.nml:48
        self.line.height = 1    # calculator_window.nml:49

        self.history.link = _bind(lambda _o: self.line)    # calculator_window.nml:53
        self.history.history_id = 'calc'    # calculator_window.nml:54
        self.history.x = _bind(lambda _o: max(0, _o.parent.width - 5))    # calculator_window.nml:55
        self.history.y = 3    # calculator_window.nml:56
        self.history.width = 3    # calculator_window.nml:57
        self.history.height = 1    # calculator_window.nml:58

        self.copy_caption.x = 2    # calculator_window.nml:62
        self.copy_caption.y = 5    # calculator_window.nml:63
        self.copy_caption.width = 10    # calculator_window.nml:64
        self.copy_caption.height = 1    # calculator_window.nml:65
        self.copy_caption.text = _bind(    # calculator_window.nml:66
            lambda _o: _tr('Copy ~A~s'),
            yielding=True,
        )
        self.copy_caption.link = _bind(lambda _o: self.copy_as)    # calculator_window.nml:67

        self.copy_as.x = 2    # calculator_window.nml:71
        self.copy_as.y = 6    # calculator_window.nml:72
        self.copy_as.width = 9    # calculator_window.nml:73
        self.copy_as.height = 5    # calculator_window.nml:74
        self.copy_as.items = _bind(    # calculator_window.nml:75
            lambda _o: [_tr('~D~EC'), _tr('~H~EX'), _tr('~B~IN'), _tr('~O~CT'), _tr('~E~XP')],
            yielding=True,
        )

        self.row0.x = 12    # calculator_window.nml:79
        self.row0.y = 6    # calculator_window.nml:80
        self.row0.width = _bind(lambda _o: max(0, _o.parent.width - 14))    # calculator_window.nml:81
        self.row0.height = 1    # calculator_window.nml:82
        self.row0.align = 'right'    # calculator_window.nml:83
        self.row0.text = _bind(lambda _o: self.rows[0])    # calculator_window.nml:84

        self.row1.x = 12    # calculator_window.nml:88
        self.row1.y = 7    # calculator_window.nml:89
        self.row1.width = _bind(lambda _o: max(0, _o.parent.width - 14))    # calculator_window.nml:90
        self.row1.height = 1    # calculator_window.nml:91
        self.row1.align = 'right'    # calculator_window.nml:92
        self.row1.text = _bind(lambda _o: self.rows[1])    # calculator_window.nml:93

        self.row2.x = 12    # calculator_window.nml:97
        self.row2.y = 8    # calculator_window.nml:98
        self.row2.width = _bind(lambda _o: max(0, _o.parent.width - 14))    # calculator_window.nml:99
        self.row2.height = 1    # calculator_window.nml:100
        self.row2.align = 'right'    # calculator_window.nml:101
        self.row2.text = _bind(lambda _o: self.rows[2])    # calculator_window.nml:102

        self.row3.x = 12    # calculator_window.nml:106
        self.row3.y = 9    # calculator_window.nml:107
        self.row3.width = _bind(lambda _o: max(0, _o.parent.width - 14))    # calculator_window.nml:108
        self.row3.height = 1    # calculator_window.nml:109
        self.row3.align = 'right'    # calculator_window.nml:110
        self.row3.text = _bind(lambda _o: self.rows[3])    # calculator_window.nml:111

        self.row4.x = 12    # calculator_window.nml:115
        self.row4.y = 10    # calculator_window.nml:116
        self.row4.width = _bind(lambda _o: max(0, _o.parent.width - 14))    # calculator_window.nml:117
        self.row4.height = 1    # calculator_window.nml:118
        self.row4.align = 'right'    # calculator_window.nml:119
        self.row4.text = _bind(lambda _o: self.rows[4])    # calculator_window.nml:120

        self.evaluate_button.text = _bind(    # calculator_window.nml:125
            lambda _o: _tr('E~v~aluate'),
            yielding=True,
        )
        self.evaluate_button.default = True    # calculator_window.nml:126
        self.evaluate_button.x = 3    # calculator_window.nml:127
        self.evaluate_button.y = 12    # calculator_window.nml:128
        self.evaluate_button.width = 12    # calculator_window.nml:129
        self.evaluate_button.height = 2    # calculator_window.nml:130
        self.evaluate_button.on_click = self.on_evaluate_button_click    # calculator_window.nml:124

        self.copy_button.text = _bind(lambda _o: _tr('~C~opy'), yielding=True)    # calculator_window.nml:135
        self.copy_button.x = 16    # calculator_window.nml:136
        self.copy_button.y = 12    # calculator_window.nml:137
        self.copy_button.width = 10    # calculator_window.nml:138
        self.copy_button.height = 2    # calculator_window.nml:139
        self.copy_button.on_click = self.on_copy_button_click    # calculator_window.nml:134

        self.close_button.text = _bind(lambda _o: _tr('Close'), yielding=True)    # calculator_window.nml:143
        self.close_button.x = 27    # calculator_window.nml:144
        self.close_button.y = 12    # calculator_window.nml:145
        self.close_button.width = 10    # calculator_window.nml:146
        self.close_button.height = 2    # calculator_window.nml:147
        self.close_button.on_click = self.on_close_button_click    # calculator_window.nml:142

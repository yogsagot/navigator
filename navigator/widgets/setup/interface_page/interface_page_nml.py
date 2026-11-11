# navml: generated
"""Generated from ``interface_page.nml``.

Do not edit: edit the markup and rerun ``python -m navml build``.
"""

from __future__ import annotations

#: Everything the generator needs for itself is underscored, so a document may
#: import any name at all without colliding with it -- there is no reserved
#: word.  A bare ``Label:`` head is what asks for ``_Component``; markup
#: never names it.  See *Importing another component* in navml/DESIGN.md.
from typing import Any as _Any

from navkit.i18n import tr as _tr
from navkit.reactive import bind as _bind
from navkit.reactive import reactive as _reactive

from navml.component import Component as _Component
from navml.widgets.dialog.check_boxes import CheckBoxes    # interface_page.nml:1
from navml.widgets.dialog.choice_field import ChoiceField    # interface_page.nml:2
from navml.widgets.dialog.label import Label    # interface_page.nml:3
from navml.widgets.dialog.masked_field import MaskedField    # interface_page.nml:4
from navml.widgets.dialog.radio_buttons import RadioButtons    # interface_page.nml:5

__navml_component__ = "InterfacePage"

__all__ = ["InterfacePage"]


class InterfacePage(_Component):
    """Options > Configuration > Interface: DOS Navigator's ``dlgInterfaceSetup``.

    The resource's twelve boxes in its two columns of six, at its width; Help
    is left out, having nothing to show yet.  *History size* below them is a
    departure: DN's lists were a fixed 20 long, and *Tooltip delay* beside it
    (DN had no tooltips); so is *Language*, DN's being
    the resource set it was installed with, *Colours*, ``[appearance]``'s
    depth, where DN's was the video mode a DOS adapter was put in, *Glyphs*
    and *Marks*.
    """

    #: The document this class was generated from.
    __navml_source__ = "interface_page.nml"

    #: The caption on its tab, which *Settings* gives it.
    title: str = _reactive('')    # interface_page.nml:18

    #: Ids, annotated so the hand-written half completes them.
    options: CheckBoxes    # interface_page.nml:21
    history_size: MaskedField    # interface_page.nml:30
    tooltip_delay: MaskedField    # interface_page.nml:44
    language: ChoiceField    # interface_page.nml:58
    colors: ChoiceField    # interface_page.nml:69
    glyphs_tier: ChoiceField    # interface_page.nml:80
    dim_modal: CheckBoxes    # interface_page.nml:93
    marks: ChoiceField    # interface_page.nml:105
    direction: ChoiceField    # interface_page.nml:116
    settings_tabs_caption: Label    # interface_page.nml:127
    settings_tabs: RadioButtons    # interface_page.nml:136
    window_strip_caption: Label    # interface_page.nml:145
    window_strip: RadioButtons    # interface_page.nml:154

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.options = CheckBoxes(parent=self)    # interface_page.nml:20
        self.history_size = MaskedField(parent=self)    # interface_page.nml:29
        self.tooltip_delay = MaskedField(parent=self)    # interface_page.nml:43
        self.language = ChoiceField(parent=self)    # interface_page.nml:57
        self.colors = ChoiceField(parent=self)    # interface_page.nml:68
        self.glyphs_tier = ChoiceField(parent=self)    # interface_page.nml:79
        self.dim_modal = CheckBoxes(parent=self)    # interface_page.nml:92
        self.marks = ChoiceField(parent=self)    # interface_page.nml:104
        self.direction = ChoiceField(parent=self)    # interface_page.nml:115
        self.settings_tabs_caption = Label(parent=self)    # interface_page.nml:126
        self.settings_tabs = RadioButtons(parent=self)    # interface_page.nml:135
        self.window_strip_caption = Label(parent=self)    # interface_page.nml:144
        self.window_strip = RadioButtons(parent=self)    # interface_page.nml:153

        self.options.y = 1    # interface_page.nml:22
        self.options.height = 6    # interface_page.nml:23
        self.options.items = _bind(    # interface_page.nml:27
            lambda _o: [_tr('~C~lock'), _tr('Hide ~m~enu bar'), _tr('Hide ~s~tatus line'), _tr('ESC for ~u~ser screen'), _tr('Hide Command ~L~ine'), _tr('~A~uto hide Command Line'), _tr('~B~lock Insert Cursor'), _tr('Store edi~t~or position'), _tr('Store vie~w~er position'), _tr('Track ~e~diting history'), _tr('Track ~v~iewing history'), _tr('Track ~d~irectories')],
            yielding=True,
        )
        self.options.x = 2    # interface_page.nml:25
        self.options.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # interface_page.nml:26

        self.history_size.x = 2    # interface_page.nml:31
        self.history_size.y = 8    # interface_page.nml:32
        self.history_size.width = 20    # interface_page.nml:33
        self.history_size.height = 1    # interface_page.nml:34
        self.history_size.label_text = _bind(    # interface_page.nml:35
            lambda _o: _tr('~H~istory size'),
            yielding=True,
        )
        self.history_size.label_width = 15    # interface_page.nml:36
        self.history_size.mask = '999'    # interface_page.nml:37
        self.history_size.page_keys = False    # interface_page.nml:39

        self.tooltip_delay.x = 26    # interface_page.nml:45
        self.tooltip_delay.y = 8    # interface_page.nml:46
        self.tooltip_delay.width = 26    # interface_page.nml:47
        self.tooltip_delay.height = 1    # interface_page.nml:48
        self.tooltip_delay.label_text = _bind(    # interface_page.nml:49
            lambda _o: _tr('Tooltip delay (ms)'),
            yielding=True,
        )
        self.tooltip_delay.label_width = 20    # interface_page.nml:50
        self.tooltip_delay.mask = '9999'    # interface_page.nml:51
        self.tooltip_delay.page_keys = False    # interface_page.nml:52

        self.language.x = 2    # interface_page.nml:59
        self.language.y = 10    # interface_page.nml:60
        self.language.width = 40    # interface_page.nml:61
        self.language.height = 1    # interface_page.nml:62
        self.language.label_text = _bind(    # interface_page.nml:63
            lambda _o: _tr('La~n~guage'),
            yielding=True,
        )
        self.language.label_width = 15    # interface_page.nml:64

        self.colors.x = 2    # interface_page.nml:70
        self.colors.y = 11    # interface_page.nml:71
        self.colors.width = 40    # interface_page.nml:72
        self.colors.height = 1    # interface_page.nml:73
        self.colors.label_text = _bind(    # interface_page.nml:74
            lambda _o: _tr('Colou~r~s'),
            yielding=True,
        )
        self.colors.label_width = 15    # interface_page.nml:75

        self.glyphs_tier.x = 2    # interface_page.nml:81
        self.glyphs_tier.y = 12    # interface_page.nml:82
        self.glyphs_tier.width = 40    # interface_page.nml:83
        self.glyphs_tier.height = 1    # interface_page.nml:84
        self.glyphs_tier.label_text = _bind(    # interface_page.nml:85
            lambda _o: _tr('Gl~y~phs'),
            yielding=True,
        )
        self.glyphs_tier.label_width = 15    # interface_page.nml:86

        self.dim_modal.y = 11    # interface_page.nml:94
        self.dim_modal.height = 1    # interface_page.nml:95
        self.dim_modal.items = _bind(    # interface_page.nml:99
            lambda _o: [_tr('Dim behind dialogs')],
            yielding=True,
        )
        self.dim_modal.x = 44    # interface_page.nml:97
        self.dim_modal.width = _bind(lambda _o: max(0, _o.parent.width - 46))    # interface_page.nml:98

        self.marks.x = 2    # interface_page.nml:106
        self.marks.y = 13    # interface_page.nml:107
        self.marks.width = 40    # interface_page.nml:108
        self.marks.height = 1    # interface_page.nml:109
        self.marks.label_text = _bind(lambda _o: _tr('Mar~k~s'), yielding=True)    # interface_page.nml:110
        self.marks.label_width = 15    # interface_page.nml:111

        self.direction.x = 2    # interface_page.nml:117
        self.direction.y = 14    # interface_page.nml:118
        self.direction.width = 40    # interface_page.nml:119
        self.direction.height = 1    # interface_page.nml:120
        self.direction.label_text = _bind(    # interface_page.nml:121
            lambda _o: _tr('Te~x~t direction'),
            yielding=True,
        )
        self.direction.label_width = 15    # interface_page.nml:122

        self.settings_tabs_caption.x = 2    # interface_page.nml:128
        self.settings_tabs_caption.y = 15    # interface_page.nml:129
        self.settings_tabs_caption.width = 15    # interface_page.nml:130
        self.settings_tabs_caption.height = 1    # interface_page.nml:131
        self.settings_tabs_caption.text = _bind(    # interface_page.nml:132
            lambda _o: _tr('Settin~g~s tabs'),
            yielding=True,
        )
        self.settings_tabs_caption.link = _bind(lambda _o: self.settings_tabs)    # interface_page.nml:133

        self.settings_tabs.x = 17    # interface_page.nml:137
        self.settings_tabs.y = 15    # interface_page.nml:138
        self.settings_tabs.width = 50    # interface_page.nml:139
        self.settings_tabs.height = 1    # interface_page.nml:140
        self.settings_tabs.items = _bind(    # interface_page.nml:141
            lambda _o: [_tr('~O~n top'), _tr('On the le~f~t'), _tr('Sim~p~le')],
            yielding=True,
        )

        self.window_strip_caption.x = 2    # interface_page.nml:146
        self.window_strip_caption.y = 16    # interface_page.nml:147
        self.window_strip_caption.width = 15    # interface_page.nml:148
        self.window_strip_caption.height = 1    # interface_page.nml:149
        self.window_strip_caption.text = _bind(    # interface_page.nml:150
            lambda _o: _tr('W~i~ndow strip'),
            yielding=True,
        )
        self.window_strip_caption.link = _bind(lambda _o: self.window_strip)    # interface_page.nml:151

        self.window_strip.x = 17    # interface_page.nml:155
        self.window_strip.y = 16    # interface_page.nml:156
        self.window_strip.width = 50    # interface_page.nml:157
        self.window_strip.height = 1    # interface_page.nml:158
        self.window_strip.items = _bind(    # interface_page.nml:159
            lambda _o: [_tr('Off'), _tr('Numbers'), _tr('With titles')],
            yielding=True,
        )

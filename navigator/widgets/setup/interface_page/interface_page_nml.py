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
    departure: DN's lists were a fixed 20 long; so is *Language*, DN's being
    the resource set it was installed with, *Colours*, ``[appearance]``'s
    depth, where DN's was the video mode a DOS adapter was put in, *Glyphs*
    and *Marks*.
    """

    #: The document this class was generated from.
    __navml_source__ = "interface_page.nml"

    #: The caption on its tab, which *Settings* gives it.
    title: str = _reactive('')    # interface_page.nml:17

    #: Ids, annotated so the hand-written half completes them.
    options: CheckBoxes    # interface_page.nml:20
    history_size: MaskedField    # interface_page.nml:28
    language: ChoiceField    # interface_page.nml:43
    colors: ChoiceField    # interface_page.nml:54
    glyphs_tier: ChoiceField    # interface_page.nml:65
    marks: ChoiceField    # interface_page.nml:77
    settings_tabs_caption: Label    # interface_page.nml:88
    settings_tabs: RadioButtons    # interface_page.nml:97
    window_strip_caption: Label    # interface_page.nml:106
    window_strip: RadioButtons    # interface_page.nml:115

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.options = CheckBoxes(parent=self)    # interface_page.nml:19
        self.history_size = MaskedField(parent=self)    # interface_page.nml:27
        self.language = ChoiceField(parent=self)    # interface_page.nml:42
        self.colors = ChoiceField(parent=self)    # interface_page.nml:53
        self.glyphs_tier = ChoiceField(parent=self)    # interface_page.nml:64
        self.marks = ChoiceField(parent=self)    # interface_page.nml:76
        self.settings_tabs_caption = Label(parent=self)    # interface_page.nml:87
        self.settings_tabs = RadioButtons(parent=self)    # interface_page.nml:96
        self.window_strip_caption = Label(parent=self)    # interface_page.nml:105
        self.window_strip = RadioButtons(parent=self)    # interface_page.nml:114

        self.options.x = 2    # interface_page.nml:21
        self.options.y = 1    # interface_page.nml:22
        self.options.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # interface_page.nml:23
        self.options.height = 6    # interface_page.nml:24
        self.options.items = _bind(    # interface_page.nml:25
            lambda _o: [_tr('~C~lock'), _tr('Hide ~m~enu bar'), _tr('Hide ~s~tatus line'), _tr('ESC for ~u~ser screen'), _tr('Hide Command ~L~ine'), _tr('~A~uto hide Command Line'), _tr('~B~lock Insert Cursor'), _tr('Store edi~t~or position'), _tr('Store vie~w~er position'), _tr('Track ~e~diting history'), _tr('Track ~v~iewing history'), _tr('Track ~d~irectories')],
            yielding=True,
        )

        self.history_size.x = 2    # interface_page.nml:29
        self.history_size.y = 8    # interface_page.nml:30
        self.history_size.width = 20    # interface_page.nml:31
        self.history_size.height = 1    # interface_page.nml:32
        self.history_size.label_text = _bind(    # interface_page.nml:33
            lambda _o: _tr('~H~istory size'),
            yielding=True,
        )
        self.history_size.label_width = 15    # interface_page.nml:34
        self.history_size.mask = '999'    # interface_page.nml:35
        self.history_size.page_keys = False    # interface_page.nml:37

        self.language.x = 2    # interface_page.nml:44
        self.language.y = 10    # interface_page.nml:45
        self.language.width = 40    # interface_page.nml:46
        self.language.height = 1    # interface_page.nml:47
        self.language.label_text = _bind(    # interface_page.nml:48
            lambda _o: _tr('La~n~guage'),
            yielding=True,
        )
        self.language.label_width = 15    # interface_page.nml:49

        self.colors.x = 2    # interface_page.nml:55
        self.colors.y = 11    # interface_page.nml:56
        self.colors.width = 40    # interface_page.nml:57
        self.colors.height = 1    # interface_page.nml:58
        self.colors.label_text = _bind(    # interface_page.nml:59
            lambda _o: _tr('Colou~r~s'),
            yielding=True,
        )
        self.colors.label_width = 15    # interface_page.nml:60

        self.glyphs_tier.x = 2    # interface_page.nml:66
        self.glyphs_tier.y = 12    # interface_page.nml:67
        self.glyphs_tier.width = 40    # interface_page.nml:68
        self.glyphs_tier.height = 1    # interface_page.nml:69
        self.glyphs_tier.label_text = _bind(    # interface_page.nml:70
            lambda _o: _tr('Gl~y~phs'),
            yielding=True,
        )
        self.glyphs_tier.label_width = 15    # interface_page.nml:71

        self.marks.x = 2    # interface_page.nml:78
        self.marks.y = 13    # interface_page.nml:79
        self.marks.width = 40    # interface_page.nml:80
        self.marks.height = 1    # interface_page.nml:81
        self.marks.label_text = _bind(lambda _o: _tr('Mar~k~s'), yielding=True)    # interface_page.nml:82
        self.marks.label_width = 15    # interface_page.nml:83

        self.settings_tabs_caption.x = 2    # interface_page.nml:89
        self.settings_tabs_caption.y = 15    # interface_page.nml:90
        self.settings_tabs_caption.width = 15    # interface_page.nml:91
        self.settings_tabs_caption.height = 1    # interface_page.nml:92
        self.settings_tabs_caption.text = _bind(    # interface_page.nml:93
            lambda _o: _tr('Settin~g~s tabs'),
            yielding=True,
        )
        self.settings_tabs_caption.link = _bind(lambda _o: self.settings_tabs)    # interface_page.nml:94

        self.settings_tabs.x = 17    # interface_page.nml:98
        self.settings_tabs.y = 15    # interface_page.nml:99
        self.settings_tabs.width = 36    # interface_page.nml:100
        self.settings_tabs.height = 1    # interface_page.nml:101
        self.settings_tabs.items = _bind(    # interface_page.nml:102
            lambda _o: [_tr('~O~n top'), _tr('On the le~f~t')],
            yielding=True,
        )

        self.window_strip_caption.x = 2    # interface_page.nml:107
        self.window_strip_caption.y = 16    # interface_page.nml:108
        self.window_strip_caption.width = 15    # interface_page.nml:109
        self.window_strip_caption.height = 1    # interface_page.nml:110
        self.window_strip_caption.text = _bind(    # interface_page.nml:111
            lambda _o: _tr('W~i~ndow strip'),
            yielding=True,
        )
        self.window_strip_caption.link = _bind(lambda _o: self.window_strip)    # interface_page.nml:112

        self.window_strip.x = 17    # interface_page.nml:116
        self.window_strip.y = 16    # interface_page.nml:117
        self.window_strip.width = 50    # interface_page.nml:118
        self.window_strip.height = 1    # interface_page.nml:119
        self.window_strip.items = _bind(    # interface_page.nml:120
            lambda _o: [_tr('Off'), _tr('Numbers'), _tr('With titles')],
            yielding=True,
        )

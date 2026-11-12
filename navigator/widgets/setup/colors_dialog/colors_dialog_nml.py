# navml: generated
"""Generated from ``colors_dialog.nml``.

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

from navml.component import Component as _Component
from navml.widgets.dialog.check_boxes import CheckBoxes    # colors_dialog.nml:1
from navml.widgets.dialog.color_selector import ColorDisplay, ColorSelector    # colors_dialog.nml:2
from navml.widgets.dialog.dialog import Dialog    # colors_dialog.nml:3
from navml.widgets.dialog.field import Field    # colors_dialog.nml:4
from navml.widgets.dialog.label import Label    # colors_dialog.nml:5
from navml.widgets.dialog.list_viewer import ListViewer    # colors_dialog.nml:6
from navml.widgets.dialog.static_text import StaticText    # colors_dialog.nml:7

__navml_component__ = "ColorsDialog"

__all__ = ["ColorsDialog"]


class ColorsDialog(Dialog, _Component):
    """Options > Colors: DOS Navigator's ``dlgColors``, Turbo Vision's

    ``TColorDialog`` as COLORSEL.PAS built it.

    *Group* and *Item* on the left, the *Foreground* and *Background* grids and
    the sample on the right, as ``TColorDialog.Init`` placed them.  Below them
    what a terminal draws that DOS could not: either colour as any colour at
    all -- a name, ``#rrggbb`` or the terminal's ``default`` -- and the five
    text attributes, each ``[?]`` until it is set (``inherit``: the entry says
    nothing, so it is whatever the row sits on).  DN's monochrome and
    black-and-white selectors are left out, as there is no such screen.
    """

    #: The document this class was generated from.
    __navml_source__ = "colors_dialog.nml"

    #: Ids, annotated so the hand-written half completes them.
    group_caption: Label    # colors_dialog.nml:25
    groups: ListViewer    # colors_dialog.nml:33
    item_caption: Label    # colors_dialog.nml:40
    items: ListViewer    # colors_dialog.nml:48
    foreground_caption: Label    # colors_dialog.nml:55
    foreground: ColorSelector    # colors_dialog.nml:63
    background_caption: Label    # colors_dialog.nml:70
    background: ColorSelector    # colors_dialog.nml:78
    sample: ColorDisplay    # colors_dialog.nml:86
    hint: StaticText    # colors_dialog.nml:93
    foreground_value: Field    # colors_dialog.nml:101
    background_value: Field    # colors_dialog.nml:109
    attributes: CheckBoxes    # colors_dialog.nml:118

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.group_caption = Label(parent=self)    # colors_dialog.nml:24
        self.groups = ListViewer(parent=self)    # colors_dialog.nml:32
        self.item_caption = Label(parent=self)    # colors_dialog.nml:39
        self.items = ListViewer(parent=self)    # colors_dialog.nml:47
        self.foreground_caption = Label(parent=self)    # colors_dialog.nml:54
        self.foreground = ColorSelector(parent=self)    # colors_dialog.nml:62
        self.background_caption = Label(parent=self)    # colors_dialog.nml:69
        self.background = ColorSelector(parent=self)    # colors_dialog.nml:77
        self.sample = ColorDisplay(parent=self)    # colors_dialog.nml:85
        self.hint = StaticText(parent=self)    # colors_dialog.nml:92
        self.foreground_value = Field(parent=self)    # colors_dialog.nml:100
        self.background_value = Field(parent=self)    # colors_dialog.nml:108
        self.attributes = CheckBoxes(parent=self)    # colors_dialog.nml:117

        self.modal_width = 70    # colors_dialog.nml:20
        self.modal_height = 24    # colors_dialog.nml:21
        self.title = _bind(lambda _o: _tr('Colors'), yielding=True)    # colors_dialog.nml:22

        self.group_caption.x = 2    # colors_dialog.nml:26
        self.group_caption.y = 2    # colors_dialog.nml:27
        self.group_caption.width = 21    # colors_dialog.nml:28
        self.group_caption.text = _bind(    # colors_dialog.nml:29
            lambda _o: _tr('~G~roup'),
            yielding=True,
        )
        self.group_caption.link = _bind(lambda _o: self.groups)    # colors_dialog.nml:30

        self.groups.x = 3    # colors_dialog.nml:34
        self.groups.y = 3    # colors_dialog.nml:35
        self.groups.width = 21    # colors_dialog.nml:36
        self.groups.height = 12    # colors_dialog.nml:37

        self.item_caption.x = 25    # colors_dialog.nml:41
        self.item_caption.y = 2    # colors_dialog.nml:42
        self.item_caption.width = 7    # colors_dialog.nml:43
        self.item_caption.text = _bind(lambda _o: _tr('~I~tem'), yielding=True)    # colors_dialog.nml:44
        self.item_caption.link = _bind(lambda _o: self.items)    # colors_dialog.nml:45

        self.items.x = 26    # colors_dialog.nml:49
        self.items.y = 3    # colors_dialog.nml:50
        self.items.width = 24    # colors_dialog.nml:51
        self.items.height = 12    # colors_dialog.nml:52

        self.foreground_caption.x = 54    # colors_dialog.nml:56
        self.foreground_caption.y = 2    # colors_dialog.nml:57
        self.foreground_caption.width = 12    # colors_dialog.nml:58
        self.foreground_caption.text = _bind(    # colors_dialog.nml:59
            lambda _o: _tr('~F~oreground'),
            yielding=True,
        )
        self.foreground_caption.link = _bind(lambda _o: self.foreground)    # colors_dialog.nml:60

        self.foreground.x = 54    # colors_dialog.nml:64
        self.foreground.y = 3    # colors_dialog.nml:65
        self.foreground.width = 12    # colors_dialog.nml:66
        self.foreground.height = 4    # colors_dialog.nml:67

        self.background_caption.x = 54    # colors_dialog.nml:71
        self.background_caption.y = 8    # colors_dialog.nml:72
        self.background_caption.width = 12    # colors_dialog.nml:73
        self.background_caption.text = _bind(    # colors_dialog.nml:74
            lambda _o: _tr('~B~ackground'),
            yielding=True,
        )
        self.background_caption.link = _bind(lambda _o: self.background)    # colors_dialog.nml:75

        self.background.x = 54    # colors_dialog.nml:79
        self.background.y = 9    # colors_dialog.nml:80
        self.background.width = 12    # colors_dialog.nml:81
        self.background.height = 4    # colors_dialog.nml:82

        self.sample.x = 54    # colors_dialog.nml:87
        self.sample.y = 14    # colors_dialog.nml:88
        self.sample.width = 12    # colors_dialog.nml:89
        self.sample.height = 1    # colors_dialog.nml:90

        self.hint.y = 15    # colors_dialog.nml:94
        self.hint.text = _bind(    # colors_dialog.nml:98
            lambda _o: _tr("Any colour: a name, #rrggbb, or default for the terminal's own"),
            yielding=True,
        )
        self.hint.x = 3    # colors_dialog.nml:96
        self.hint.width = _bind(lambda _o: max(0, _o.parent.width - 6))    # colors_dialog.nml:97

        self.foreground_value.x = 2    # colors_dialog.nml:102
        self.foreground_value.y = 16    # colors_dialog.nml:103
        self.foreground_value.width = 31    # colors_dialog.nml:104
        self.foreground_value.label_text = _bind(    # colors_dialog.nml:105
            lambda _o: _tr('Fo~r~eground'),
            yielding=True,
        )
        self.foreground_value.label_width = 12    # colors_dialog.nml:106

        self.background_value.x = 35    # colors_dialog.nml:110
        self.background_value.y = 16    # colors_dialog.nml:111
        self.background_value.width = 31    # colors_dialog.nml:112
        self.background_value.label_text = _bind(    # colors_dialog.nml:113
            lambda _o: _tr('Bac~k~ground'),
            yielding=True,
        )
        self.background_value.label_width = 12    # colors_dialog.nml:114

        self.attributes.y = 18    # colors_dialog.nml:119
        self.attributes.height = 1    # colors_dialog.nml:120
        self.attributes.items = _bind(    # colors_dialog.nml:124
            lambda _o: [_tr('Bo~l~d'), _tr('~D~im'), _tr('I~t~alic'), _tr('~U~nderline'), _tr('R~e~verse')],
            yielding=True,
        )
        self.attributes.x = 3    # colors_dialog.nml:122
        self.attributes.width = _bind(lambda _o: max(0, _o.parent.width - 6))    # colors_dialog.nml:123

        self._navml_built(__class__)

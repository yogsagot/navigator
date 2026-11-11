# navml: generated
"""Generated from ``editor_defaults_page.nml``.

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
from navml.widgets.dialog.check_boxes import CheckBoxes    # editor_defaults_page.nml:1
from navml.widgets.dialog.choice_field import ChoiceField    # editor_defaults_page.nml:2
from navml.widgets.dialog.label import Label    # editor_defaults_page.nml:3
from navml.widgets.dialog.masked_field import MaskedField    # editor_defaults_page.nml:4
from navml.widgets.dialog.radio_buttons import RadioButtons    # editor_defaults_page.nml:5

__navml_component__ = "EditorDefaultsPage"

__all__ = ["EditorDefaultsPage"]


class EditorDefaultsPage(_Component):
    """Options > Configuration > Editor/Viewer: DOS Navigator's ``dlgEditorDefaults``.

    The resource's two clusters, four numbers and the line divisor, less *Use
    EMS memory* and *Use XMS memory*.  The numbers are three-digit masked lines
    rather than DN's free input lines, so nothing but a number goes in.  Four
    columns wider than DN's 52; Help is left out, having nothing to show yet.
    The line divisor lists LF first, a departure from DN's CR+LF, CR, LF:
    POSIX's own ending leads.  *Option strip* in each cluster is a departure
    too, the strip being one (``OptionStrip``), and so is *Fallback encoding*,
    what a file that is not UTF-8 is read as (``[editor] fallback_encoding``).
    So is *Tab key inserts tabs* (``[editor] insert_tabs``; DN's Tab wrote
    blanks): the editor cluster is a row taller for it, all below a row down.
    *Line numbers* (``[editor] line_numbers``; DN numbered no lines) fills
    the cluster's last place, with no hot key: the page has no letter of it left.
    """

    #: The document this class was generated from.
    __navml_source__ = "editor_defaults_page.nml"

    #: The caption on its tab, which *Settings* gives it.
    title: str = _reactive('')    # editor_defaults_page.nml:23

    #: Ids, annotated so the hand-written half completes them.
    editor_caption: Label    # editor_defaults_page.nml:26
    editor: CheckBoxes    # editor_defaults_page.nml:35
    viewer_caption: Label    # editor_defaults_page.nml:44
    viewer: CheckBoxes    # editor_defaults_page.nml:53
    left_margin: MaskedField    # editor_defaults_page.nml:61
    right_margin: MaskedField    # editor_defaults_page.nml:73
    paragraph: MaskedField    # editor_defaults_page.nml:85
    tab_size: MaskedField    # editor_defaults_page.nml:97
    divisor_caption: Label    # editor_defaults_page.nml:109
    line_divisor: RadioButtons    # editor_defaults_page.nml:118
    fallback_encoding: ChoiceField    # editor_defaults_page.nml:126

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.editor_caption = Label(parent=self)    # editor_defaults_page.nml:25
        self.editor = CheckBoxes(parent=self)    # editor_defaults_page.nml:34
        self.viewer_caption = Label(parent=self)    # editor_defaults_page.nml:43
        self.viewer = CheckBoxes(parent=self)    # editor_defaults_page.nml:52
        self.left_margin = MaskedField(parent=self)    # editor_defaults_page.nml:60
        self.right_margin = MaskedField(parent=self)    # editor_defaults_page.nml:72
        self.paragraph = MaskedField(parent=self)    # editor_defaults_page.nml:84
        self.tab_size = MaskedField(parent=self)    # editor_defaults_page.nml:96
        self.divisor_caption = Label(parent=self)    # editor_defaults_page.nml:108
        self.line_divisor = RadioButtons(parent=self)    # editor_defaults_page.nml:117
        self.fallback_encoding = ChoiceField(parent=self)    # editor_defaults_page.nml:125

        self.editor_caption.x = 2    # editor_defaults_page.nml:27
        self.editor_caption.y = 1    # editor_defaults_page.nml:28
        self.editor_caption.width = 16    # editor_defaults_page.nml:29
        self.editor_caption.height = 1    # editor_defaults_page.nml:30
        self.editor_caption.text = _bind(    # editor_defaults_page.nml:31
            lambda _o: _tr('Editor options'),
            yielding=True,
        )
        self.editor_caption.link = _bind(lambda _o: self.editor)    # editor_defaults_page.nml:32

        self.editor.y = 2    # editor_defaults_page.nml:36
        self.editor.height = 8    # editor_defaults_page.nml:37
        self.editor.items = _bind(    # editor_defaults_page.nml:41
            lambda _o: [_tr('~C~reate backup files'), _tr('~B~ackspace unindents'), _tr('Au~t~oBrackets'), _tr('~A~uto indent'), _tr('A~u~towrap'), _tr('~J~ustify on wrap'), _tr('~V~ertical blocks'), _tr('Opti~m~al fill'), _tr('~H~ighlight line'), _tr('H~i~ghlight column'), _tr('~P~ersistent blocks'), _tr('~O~verwrite blocks'), _tr('Lock ~f~ile'), _tr('Tab ~k~ey inserts tabs'), _tr('Line numbers'), _tr('Option ~s~trip')],
            yielding=True,
        )
        self.editor.x = 2    # editor_defaults_page.nml:39
        self.editor.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # editor_defaults_page.nml:40

        self.viewer_caption.x = 2    # editor_defaults_page.nml:45
        self.viewer_caption.y = 11    # editor_defaults_page.nml:46
        self.viewer_caption.width = 16    # editor_defaults_page.nml:47
        self.viewer_caption.height = 1    # editor_defaults_page.nml:48
        self.viewer_caption.text = _bind(    # editor_defaults_page.nml:49
            lambda _o: _tr('Viewer options'),
            yielding=True,
        )
        self.viewer_caption.link = _bind(lambda _o: self.viewer)    # editor_defaults_page.nml:50

        self.viewer.x = 2    # editor_defaults_page.nml:54
        self.viewer.y = 12    # editor_defaults_page.nml:55
        self.viewer.width = 20    # editor_defaults_page.nml:56
        self.viewer.height = 3    # editor_defaults_page.nml:57
        self.viewer.items = _bind(    # editor_defaults_page.nml:58
            lambda _o: [_tr('He~x~ mode'), _tr('~W~rap lines'), _tr('Optio~n~ strip')],
            yielding=True,
        )

        self.left_margin.x = 30    # editor_defaults_page.nml:62
        self.left_margin.y = 11    # editor_defaults_page.nml:63
        self.left_margin.width = 20    # editor_defaults_page.nml:64
        self.left_margin.height = 1    # editor_defaults_page.nml:65
        self.left_margin.label_text = _bind(    # editor_defaults_page.nml:66
            lambda _o: _tr('~L~eft margin'),
            yielding=True,
        )
        self.left_margin.label_width = 15    # editor_defaults_page.nml:67
        self.left_margin.mask = '999'    # editor_defaults_page.nml:68
        self.left_margin.page_keys = False    # editor_defaults_page.nml:70

        self.right_margin.x = 30    # editor_defaults_page.nml:74
        self.right_margin.y = 12    # editor_defaults_page.nml:75
        self.right_margin.width = 20    # editor_defaults_page.nml:76
        self.right_margin.height = 1    # editor_defaults_page.nml:77
        self.right_margin.label_text = _bind(    # editor_defaults_page.nml:78
            lambda _o: _tr('~R~ight margin'),
            yielding=True,
        )
        self.right_margin.label_width = 15    # editor_defaults_page.nml:79
        self.right_margin.mask = '999'    # editor_defaults_page.nml:80
        self.right_margin.page_keys = False    # editor_defaults_page.nml:82

        self.paragraph.x = 30    # editor_defaults_page.nml:86
        self.paragraph.y = 13    # editor_defaults_page.nml:87
        self.paragraph.width = 20    # editor_defaults_page.nml:88
        self.paragraph.height = 1    # editor_defaults_page.nml:89
        self.paragraph.label_text = _bind(    # editor_defaults_page.nml:90
            lambda _o: _tr('Para~g~raph'),
            yielding=True,
        )
        self.paragraph.label_width = 15    # editor_defaults_page.nml:91
        self.paragraph.mask = '999'    # editor_defaults_page.nml:92
        self.paragraph.page_keys = False    # editor_defaults_page.nml:94

        self.tab_size.x = 30    # editor_defaults_page.nml:98
        self.tab_size.y = 15    # editor_defaults_page.nml:99
        self.tab_size.width = 20    # editor_defaults_page.nml:100
        self.tab_size.height = 1    # editor_defaults_page.nml:101
        self.tab_size.label_text = _bind(    # editor_defaults_page.nml:102
            lambda _o: _tr('Tab si~z~e'),
            yielding=True,
        )
        self.tab_size.label_width = 15    # editor_defaults_page.nml:103
        self.tab_size.mask = '999'    # editor_defaults_page.nml:104
        self.tab_size.page_keys = False    # editor_defaults_page.nml:106

        self.divisor_caption.x = 2    # editor_defaults_page.nml:110
        self.divisor_caption.y = 15    # editor_defaults_page.nml:111
        self.divisor_caption.width = 24    # editor_defaults_page.nml:112
        self.divisor_caption.height = 1    # editor_defaults_page.nml:113
        self.divisor_caption.text = _bind(    # editor_defaults_page.nml:114
            lambda _o: _tr('Line ~d~ivisor (editor)'),
            yielding=True,
        )
        self.divisor_caption.link = _bind(lambda _o: self.line_divisor)    # editor_defaults_page.nml:115

        self.line_divisor.x = 2    # editor_defaults_page.nml:119
        self.line_divisor.y = 16    # editor_defaults_page.nml:120
        self.line_divisor.width = 26    # editor_defaults_page.nml:121
        self.line_divisor.height = 1    # editor_defaults_page.nml:122
        self.line_divisor.items = _bind(    # editor_defaults_page.nml:123
            lambda _o: [_tr('LF'), _tr('CR+LF'), _tr('CR')],
            yielding=True,
        )

        self.fallback_encoding.y = 16    # editor_defaults_page.nml:127
        self.fallback_encoding.height = 1    # editor_defaults_page.nml:128
        self.fallback_encoding.label_text = _bind(    # editor_defaults_page.nml:132
            lambda _o: _tr('Fallback ~e~ncoding'),
            yielding=True,
        )
        self.fallback_encoding.label_width = 17    # editor_defaults_page.nml:133
        self.fallback_encoding.x = 30    # editor_defaults_page.nml:130
        self.fallback_encoding.width = _bind(    # editor_defaults_page.nml:131
            lambda _o: max(0, _o.parent.width - 32)
        )

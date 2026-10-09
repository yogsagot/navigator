# navml: generated
"""Generated from ``editor_defaults_dialog.nml``.

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
from navml.widgets.dialog.check_boxes import CheckBoxes    # editor_defaults_dialog.nml:1
from navml.widgets.dialog.dialog import Dialog    # editor_defaults_dialog.nml:2
from navml.widgets.dialog.label import Label    # editor_defaults_dialog.nml:3
from navml.widgets.dialog.masked_field import MaskedField    # editor_defaults_dialog.nml:4
from navml.widgets.dialog.radio_buttons import RadioButtons    # editor_defaults_dialog.nml:5

__navml_component__ = "EditorDefaultsDialog"

__all__ = ["EditorDefaultsDialog"]


class EditorDefaultsDialog(Dialog, _Component):
    """Options > Configuration > Editor/Viewer: DOS Navigator's ``dlgEditorDefaults``.

    The resource's two clusters, four numbers and the line divisor, less *Use
    EMS memory* and *Use XMS memory*.  The numbers are three-digit masked lines
    rather than DN's free input lines, so nothing but a number goes in.  Four
    columns wider than DN's 52; Help is left out, having nothing to show yet.
    The line divisor lists LF first, a departure from DN's CR+LF, CR, LF:
    POSIX's own ending leads.  *Option strip* in each cluster is a departure
    too, the strip being one (``OptionStrip``).
    """

    #: The document this class was generated from.
    __navml_source__ = "editor_defaults_dialog.nml"

    #: Ids, annotated so the hand-written half completes them.
    editor_caption: Label    # editor_defaults_dialog.nml:22
    editor: CheckBoxes    # editor_defaults_dialog.nml:31
    viewer_caption: Label    # editor_defaults_dialog.nml:39
    viewer: CheckBoxes    # editor_defaults_dialog.nml:48
    left_margin: MaskedField    # editor_defaults_dialog.nml:56
    right_margin: MaskedField    # editor_defaults_dialog.nml:66
    paragraph: MaskedField    # editor_defaults_dialog.nml:76
    tab_size: MaskedField    # editor_defaults_dialog.nml:86
    divisor_caption: Label    # editor_defaults_dialog.nml:96
    line_divisor: RadioButtons    # editor_defaults_dialog.nml:105

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.editor_caption = Label(parent=self)    # editor_defaults_dialog.nml:21
        self.editor = CheckBoxes(parent=self)    # editor_defaults_dialog.nml:30
        self.viewer_caption = Label(parent=self)    # editor_defaults_dialog.nml:38
        self.viewer = CheckBoxes(parent=self)    # editor_defaults_dialog.nml:47
        self.left_margin = MaskedField(parent=self)    # editor_defaults_dialog.nml:55
        self.right_margin = MaskedField(parent=self)    # editor_defaults_dialog.nml:65
        self.paragraph = MaskedField(parent=self)    # editor_defaults_dialog.nml:75
        self.tab_size = MaskedField(parent=self)    # editor_defaults_dialog.nml:85
        self.divisor_caption = Label(parent=self)    # editor_defaults_dialog.nml:95
        self.line_divisor = RadioButtons(parent=self)    # editor_defaults_dialog.nml:104

        self.modal_width = 56    # editor_defaults_dialog.nml:17
        self.modal_height = 21    # editor_defaults_dialog.nml:18
        self.title = _bind(    # editor_defaults_dialog.nml:19
            lambda _o: _tr('Editor/Viewer Defaults'),
            yielding=True,
        )

        self.editor_caption.x = 2    # editor_defaults_dialog.nml:23
        self.editor_caption.y = 1    # editor_defaults_dialog.nml:24
        self.editor_caption.width = 16    # editor_defaults_dialog.nml:25
        self.editor_caption.height = 1    # editor_defaults_dialog.nml:26
        self.editor_caption.text = _bind(    # editor_defaults_dialog.nml:27
            lambda _o: _tr('Editor options'),
            yielding=True,
        )
        self.editor_caption.link = _bind(lambda _o: self.editor)    # editor_defaults_dialog.nml:28

        self.editor.x = 2    # editor_defaults_dialog.nml:32
        self.editor.y = 2    # editor_defaults_dialog.nml:33
        self.editor.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # editor_defaults_dialog.nml:34
        self.editor.height = 7    # editor_defaults_dialog.nml:35
        self.editor.items = _bind(    # editor_defaults_dialog.nml:36
            lambda _o: [_tr('~C~reate backup files'), _tr('~B~ackspace unindents'), _tr('Au~t~oBrackets'), _tr('~A~uto indent'), _tr('A~u~towrap'), _tr('~J~ustify on wrap'), _tr('~V~ertical blocks'), _tr('Opti~m~al fill'), _tr('~H~ighlight line'), _tr('H~i~ghlight column'), _tr('~P~ersistent blocks'), _tr('~O~verwrite blocks'), _tr('Lock ~f~ile'), _tr('Option ~s~trip')],
            yielding=True,
        )

        self.viewer_caption.x = 2    # editor_defaults_dialog.nml:40
        self.viewer_caption.y = 10    # editor_defaults_dialog.nml:41
        self.viewer_caption.width = 16    # editor_defaults_dialog.nml:42
        self.viewer_caption.height = 1    # editor_defaults_dialog.nml:43
        self.viewer_caption.text = _bind(    # editor_defaults_dialog.nml:44
            lambda _o: _tr('Viewer options'),
            yielding=True,
        )
        self.viewer_caption.link = _bind(lambda _o: self.viewer)    # editor_defaults_dialog.nml:45

        self.viewer.x = 2    # editor_defaults_dialog.nml:49
        self.viewer.y = 11    # editor_defaults_dialog.nml:50
        self.viewer.width = 20    # editor_defaults_dialog.nml:51
        self.viewer.height = 3    # editor_defaults_dialog.nml:52
        self.viewer.items = _bind(    # editor_defaults_dialog.nml:53
            lambda _o: [_tr('He~x~ mode'), _tr('~W~rap lines'), _tr('Optio~n~ strip')],
            yielding=True,
        )

        self.left_margin.x = 30    # editor_defaults_dialog.nml:57
        self.left_margin.y = 10    # editor_defaults_dialog.nml:58
        self.left_margin.width = 20    # editor_defaults_dialog.nml:59
        self.left_margin.height = 1    # editor_defaults_dialog.nml:60
        self.left_margin.label_text = _bind(    # editor_defaults_dialog.nml:61
            lambda _o: _tr('~L~eft margin'),
            yielding=True,
        )
        self.left_margin.label_width = 15    # editor_defaults_dialog.nml:62
        self.left_margin.mask = '999'    # editor_defaults_dialog.nml:63

        self.right_margin.x = 30    # editor_defaults_dialog.nml:67
        self.right_margin.y = 11    # editor_defaults_dialog.nml:68
        self.right_margin.width = 20    # editor_defaults_dialog.nml:69
        self.right_margin.height = 1    # editor_defaults_dialog.nml:70
        self.right_margin.label_text = _bind(    # editor_defaults_dialog.nml:71
            lambda _o: _tr('~R~ight margin'),
            yielding=True,
        )
        self.right_margin.label_width = 15    # editor_defaults_dialog.nml:72
        self.right_margin.mask = '999'    # editor_defaults_dialog.nml:73

        self.paragraph.x = 30    # editor_defaults_dialog.nml:77
        self.paragraph.y = 12    # editor_defaults_dialog.nml:78
        self.paragraph.width = 20    # editor_defaults_dialog.nml:79
        self.paragraph.height = 1    # editor_defaults_dialog.nml:80
        self.paragraph.label_text = _bind(    # editor_defaults_dialog.nml:81
            lambda _o: _tr('Para~g~raph'),
            yielding=True,
        )
        self.paragraph.label_width = 15    # editor_defaults_dialog.nml:82
        self.paragraph.mask = '999'    # editor_defaults_dialog.nml:83

        self.tab_size.x = 30    # editor_defaults_dialog.nml:87
        self.tab_size.y = 14    # editor_defaults_dialog.nml:88
        self.tab_size.width = 20    # editor_defaults_dialog.nml:89
        self.tab_size.height = 1    # editor_defaults_dialog.nml:90
        self.tab_size.label_text = _bind(    # editor_defaults_dialog.nml:91
            lambda _o: _tr('Tab si~z~e'),
            yielding=True,
        )
        self.tab_size.label_width = 15    # editor_defaults_dialog.nml:92
        self.tab_size.mask = '999'    # editor_defaults_dialog.nml:93

        self.divisor_caption.x = 2    # editor_defaults_dialog.nml:97
        self.divisor_caption.y = 14    # editor_defaults_dialog.nml:98
        self.divisor_caption.width = 24    # editor_defaults_dialog.nml:99
        self.divisor_caption.height = 1    # editor_defaults_dialog.nml:100
        self.divisor_caption.text = _bind(    # editor_defaults_dialog.nml:101
            lambda _o: _tr('Line ~d~ivisor (editor)'),
            yielding=True,
        )
        self.divisor_caption.link = _bind(lambda _o: self.line_divisor)    # editor_defaults_dialog.nml:102

        self.line_divisor.x = 2    # editor_defaults_dialog.nml:106
        self.line_divisor.y = 15    # editor_defaults_dialog.nml:107
        self.line_divisor.width = 26    # editor_defaults_dialog.nml:108
        self.line_divisor.height = 1    # editor_defaults_dialog.nml:109
        self.line_divisor.items = _bind(    # editor_defaults_dialog.nml:110
            lambda _o: [_tr('LF'), _tr('CR+LF'), _tr('CR')],
            yielding=True,
        )

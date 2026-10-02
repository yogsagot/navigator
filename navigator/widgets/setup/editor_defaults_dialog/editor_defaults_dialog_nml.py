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
    """

    #: The document this class was generated from.
    __navml_source__ = "editor_defaults_dialog.nml"

    #: Ids, annotated so the hand-written half completes them.
    editor_caption: Label    # editor_defaults_dialog.nml:19
    editor: CheckBoxes    # editor_defaults_dialog.nml:28
    viewer_caption: Label    # editor_defaults_dialog.nml:36
    viewer: CheckBoxes    # editor_defaults_dialog.nml:45
    left_margin: MaskedField    # editor_defaults_dialog.nml:53
    right_margin: MaskedField    # editor_defaults_dialog.nml:63
    paragraph: MaskedField    # editor_defaults_dialog.nml:73
    tab_size: MaskedField    # editor_defaults_dialog.nml:83
    divisor_caption: Label    # editor_defaults_dialog.nml:93
    line_divisor: RadioButtons    # editor_defaults_dialog.nml:102

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.editor_caption = Label(parent=self)    # editor_defaults_dialog.nml:18
        self.editor = CheckBoxes(parent=self)    # editor_defaults_dialog.nml:27
        self.viewer_caption = Label(parent=self)    # editor_defaults_dialog.nml:35
        self.viewer = CheckBoxes(parent=self)    # editor_defaults_dialog.nml:44
        self.left_margin = MaskedField(parent=self)    # editor_defaults_dialog.nml:52
        self.right_margin = MaskedField(parent=self)    # editor_defaults_dialog.nml:62
        self.paragraph = MaskedField(parent=self)    # editor_defaults_dialog.nml:72
        self.tab_size = MaskedField(parent=self)    # editor_defaults_dialog.nml:82
        self.divisor_caption = Label(parent=self)    # editor_defaults_dialog.nml:92
        self.line_divisor = RadioButtons(parent=self)    # editor_defaults_dialog.nml:101

        self.modal_width = 56    # editor_defaults_dialog.nml:14
        self.modal_height = 21    # editor_defaults_dialog.nml:15
        self.title = 'Editor/Viewer Defaults'    # editor_defaults_dialog.nml:16

        self.editor_caption.x = 2    # editor_defaults_dialog.nml:20
        self.editor_caption.y = 1    # editor_defaults_dialog.nml:21
        self.editor_caption.width = 16    # editor_defaults_dialog.nml:22
        self.editor_caption.height = 1    # editor_defaults_dialog.nml:23
        self.editor_caption.text = 'Editor options'    # editor_defaults_dialog.nml:24
        self.editor_caption.link = _bind(lambda _o: self.editor)    # editor_defaults_dialog.nml:25

        self.editor.x = 2    # editor_defaults_dialog.nml:29
        self.editor.y = 2    # editor_defaults_dialog.nml:30
        self.editor.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # editor_defaults_dialog.nml:31
        self.editor.height = 7    # editor_defaults_dialog.nml:32
        self.editor.items = ['~C~reate backup files', '~B~ackspace unindents', 'Au~t~oBrackets', '~A~uto indent', 'A~u~towrap', '~J~ustify on wrap', '~V~ertical blocks', 'Opti~m~al fill', '~H~ighlight line', 'H~i~ghlight column', '~P~ersistent blocks', '~O~verwrite blocks', 'Lock ~f~ile']    # editor_defaults_dialog.nml:33

        self.viewer_caption.x = 2    # editor_defaults_dialog.nml:37
        self.viewer_caption.y = 10    # editor_defaults_dialog.nml:38
        self.viewer_caption.width = 16    # editor_defaults_dialog.nml:39
        self.viewer_caption.height = 1    # editor_defaults_dialog.nml:40
        self.viewer_caption.text = 'Viewer options'    # editor_defaults_dialog.nml:41
        self.viewer_caption.link = _bind(lambda _o: self.viewer)    # editor_defaults_dialog.nml:42

        self.viewer.x = 2    # editor_defaults_dialog.nml:46
        self.viewer.y = 11    # editor_defaults_dialog.nml:47
        self.viewer.width = 20    # editor_defaults_dialog.nml:48
        self.viewer.height = 2    # editor_defaults_dialog.nml:49
        self.viewer.items = ['He~x~ mode', '~W~rap lines']    # editor_defaults_dialog.nml:50

        self.left_margin.x = 30    # editor_defaults_dialog.nml:54
        self.left_margin.y = 10    # editor_defaults_dialog.nml:55
        self.left_margin.width = 20    # editor_defaults_dialog.nml:56
        self.left_margin.height = 1    # editor_defaults_dialog.nml:57
        self.left_margin.label_text = '~L~eft margin'    # editor_defaults_dialog.nml:58
        self.left_margin.label_width = 15    # editor_defaults_dialog.nml:59
        self.left_margin.mask = '999'    # editor_defaults_dialog.nml:60

        self.right_margin.x = 30    # editor_defaults_dialog.nml:64
        self.right_margin.y = 11    # editor_defaults_dialog.nml:65
        self.right_margin.width = 20    # editor_defaults_dialog.nml:66
        self.right_margin.height = 1    # editor_defaults_dialog.nml:67
        self.right_margin.label_text = '~R~ight margin'    # editor_defaults_dialog.nml:68
        self.right_margin.label_width = 15    # editor_defaults_dialog.nml:69
        self.right_margin.mask = '999'    # editor_defaults_dialog.nml:70

        self.paragraph.x = 30    # editor_defaults_dialog.nml:74
        self.paragraph.y = 12    # editor_defaults_dialog.nml:75
        self.paragraph.width = 20    # editor_defaults_dialog.nml:76
        self.paragraph.height = 1    # editor_defaults_dialog.nml:77
        self.paragraph.label_text = 'Para~g~raph'    # editor_defaults_dialog.nml:78
        self.paragraph.label_width = 15    # editor_defaults_dialog.nml:79
        self.paragraph.mask = '999'    # editor_defaults_dialog.nml:80

        self.tab_size.x = 30    # editor_defaults_dialog.nml:84
        self.tab_size.y = 14    # editor_defaults_dialog.nml:85
        self.tab_size.width = 20    # editor_defaults_dialog.nml:86
        self.tab_size.height = 1    # editor_defaults_dialog.nml:87
        self.tab_size.label_text = 'Tab si~z~e'    # editor_defaults_dialog.nml:88
        self.tab_size.label_width = 15    # editor_defaults_dialog.nml:89
        self.tab_size.mask = '999'    # editor_defaults_dialog.nml:90

        self.divisor_caption.x = 2    # editor_defaults_dialog.nml:94
        self.divisor_caption.y = 14    # editor_defaults_dialog.nml:95
        self.divisor_caption.width = 24    # editor_defaults_dialog.nml:96
        self.divisor_caption.height = 1    # editor_defaults_dialog.nml:97
        self.divisor_caption.text = 'Line ~d~ivisor (editor)'    # editor_defaults_dialog.nml:98
        self.divisor_caption.link = _bind(lambda _o: self.line_divisor)    # editor_defaults_dialog.nml:99

        self.line_divisor.x = 2    # editor_defaults_dialog.nml:103
        self.line_divisor.y = 15    # editor_defaults_dialog.nml:104
        self.line_divisor.width = 26    # editor_defaults_dialog.nml:105
        self.line_divisor.height = 1    # editor_defaults_dialog.nml:106
        self.line_divisor.items = ['CR+LF', 'CR', 'LF']    # editor_defaults_dialog.nml:107

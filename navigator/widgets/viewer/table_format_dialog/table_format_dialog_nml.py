# navml: generated
"""Generated from ``table_format_dialog.nml``.

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
from navml.widgets.dialog.check_boxes import CheckBoxes    # table_format_dialog.nml:1
from navml.widgets.dialog.choice_field import ChoiceField    # table_format_dialog.nml:2
from navml.widgets.dialog.dialog import Dialog    # table_format_dialog.nml:3
from navml.widgets.dialog.field import Field    # table_format_dialog.nml:4
from navml.widgets.dialog.label import Label    # table_format_dialog.nml:5
from navml.widgets.dialog.radio_buttons import RadioButtons    # table_format_dialog.nml:6

__navml_component__ = "TableFormatDialog"

__all__ = ["TableFormatDialog"]


class TableFormatDialog(Dialog, _Component):
    """Shift+F6 in the spreadsheet: how a CSV or TSV file is cut into cells --

    not DN's, whose ``.WKZ`` said so itself.  The delimiter (*Other* takes the
    character typed beside it), whether the first row names the columns, and
    the encoding, one of the viewer's (``viewer.ENCODINGS``).
    """

    #: The document this class was generated from.
    __navml_source__ = "table_format_dialog.nml"

    #: Ids, annotated so the hand-written half completes them.
    delimiter_caption: Label    # table_format_dialog.nml:19
    delimiter: RadioButtons    # table_format_dialog.nml:27
    other: Field    # table_format_dialog.nml:35
    options: CheckBoxes    # table_format_dialog.nml:43
    encoding: ChoiceField    # table_format_dialog.nml:51

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.delimiter_caption = Label(parent=self)    # table_format_dialog.nml:18
        self.delimiter = RadioButtons(parent=self)    # table_format_dialog.nml:26
        self.other = Field(parent=self)    # table_format_dialog.nml:34
        self.options = CheckBoxes(parent=self)    # table_format_dialog.nml:42
        self.encoding = ChoiceField(parent=self)    # table_format_dialog.nml:50

        self.modal_width = 50    # table_format_dialog.nml:13
        self.modal_height = 14    # table_format_dialog.nml:14
        self.title = _bind(lambda _o: _tr('Format'), yielding=True)    # table_format_dialog.nml:15
        self.buttons = 'ok-cancel'    # table_format_dialog.nml:16

        self.delimiter_caption.x = 3    # table_format_dialog.nml:20
        self.delimiter_caption.y = 2    # table_format_dialog.nml:21
        self.delimiter_caption.width = 20    # table_format_dialog.nml:22
        self.delimiter_caption.text = _bind(    # table_format_dialog.nml:23
            lambda _o: _tr('Delimiter'),
            yielding=True,
        )
        self.delimiter_caption.link = _bind(lambda _o: self.delimiter)    # table_format_dialog.nml:24

        self.delimiter.x = 3    # table_format_dialog.nml:28
        self.delimiter.y = 3    # table_format_dialog.nml:29
        self.delimiter.width = 18    # table_format_dialog.nml:30
        self.delimiter.height = 5    # table_format_dialog.nml:31
        self.delimiter.items = _bind(    # table_format_dialog.nml:32
            lambda _o: [_tr('~C~omma'), _tr('~S~emicolon'), _tr('~T~ab'), _tr('~P~ipe'), _tr('~O~ther')],
            yielding=True,
        )

        self.other.x = 23    # table_format_dialog.nml:36
        self.other.y = 7    # table_format_dialog.nml:37
        self.other.width = 12    # table_format_dialog.nml:38
        self.other.label_text = _bind(lambda _o: _tr('C~h~ar'), yielding=True)    # table_format_dialog.nml:39
        self.other.label_width = 6    # table_format_dialog.nml:40

        self.options.x = 23    # table_format_dialog.nml:44
        self.options.y = 3    # table_format_dialog.nml:45
        self.options.width = 25    # table_format_dialog.nml:46
        self.options.height = 1    # table_format_dialog.nml:47
        self.options.items = _bind(    # table_format_dialog.nml:48
            lambda _o: [_tr('~F~irst row is a header')],
            yielding=True,
        )

        self.encoding.y = 9    # table_format_dialog.nml:52
        self.encoding.label_text = _bind(    # table_format_dialog.nml:56
            lambda _o: _tr('~E~ncoding'),
            yielding=True,
        )
        self.encoding.label_width = 10    # table_format_dialog.nml:57
        self.encoding.x = 3    # table_format_dialog.nml:54
        self.encoding.width = _bind(lambda _o: max(0, _o.parent.width - 6))    # table_format_dialog.nml:55

        self._navml_built(__class__)

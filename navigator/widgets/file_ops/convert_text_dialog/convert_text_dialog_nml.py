# navml: generated
"""Generated from ``convert_text_dialog.nml``.

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

from navml.component import Component as _Component
from navml.widgets.dialog.button import Button    # convert_text_dialog.nml:1
from navml.widgets.dialog.button_row import ButtonRow    # convert_text_dialog.nml:2
from navml.widgets.dialog.check_boxes import CheckBoxes    # convert_text_dialog.nml:3
from navml.widgets.dialog.choice_field import ChoiceField    # convert_text_dialog.nml:4
from navml.widgets.dialog.dialog import Dialog    # convert_text_dialog.nml:5
from navml.widgets.dialog.label import Label    # convert_text_dialog.nml:6
from navml.widgets.dialog.radio_buttons import RadioButtons    # convert_text_dialog.nml:7

__navml_component__ = "ConvertTextDialog"

__all__ = ["ConvertTextDialog"]


class ConvertTextDialog(Dialog, _Component):
    """File > Encoding > Convert text.  Not DN's: a departure, asked for -- DOS

    Navigator converted no text files (``navigator.lib.file_ops.textconv``).

    The encoding the files are written in and what one that is not UTF-8 is
    read as, then the line endings beside keeping the times.
    """

    #: The document this class was generated from.
    __navml_source__ = "convert_text_dialog.nml"

    #: Ids, annotated so the hand-written half completes them.
    encoding: ChoiceField    # convert_text_dialog.nml:28
    fallback: ChoiceField    # convert_text_dialog.nml:37
    ending_caption: Label    # convert_text_dialog.nml:46
    ending: RadioButtons    # convert_text_dialog.nml:54
    options: CheckBoxes    # convert_text_dialog.nml:62
    pick: Button    # convert_text_dialog.nml:78
    abandon: Button    # convert_text_dialog.nml:84

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_abandon_click(self, event: _Event) -> bool:    # convert_text_dialog.nml:84
        """``abandon`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.encoding = ChoiceField(parent=self)    # convert_text_dialog.nml:27
        self.fallback = ChoiceField(parent=self)    # convert_text_dialog.nml:36
        self.ending_caption = Label(parent=self)    # convert_text_dialog.nml:45
        self.ending = RadioButtons(parent=self)    # convert_text_dialog.nml:53
        self.options = CheckBoxes(parent=self)    # convert_text_dialog.nml:61
        _w1 = ButtonRow(parent=self)    # convert_text_dialog.nml:70
        self.pick = Button(parent=_w1)    # convert_text_dialog.nml:77
        self.abandon = Button(parent=_w1)    # convert_text_dialog.nml:83

        self.modal_width = 70    # convert_text_dialog.nml:15
        self.modal_height = 14    # convert_text_dialog.nml:16
        self.title = _bind(lambda _o: _tr('Convert Text Files'), yielding=True)    # convert_text_dialog.nml:17
        self.help_topic = 'file-operations.md#convert-text'    # convert_text_dialog.nml:18
        self.buttons = 'none'    # convert_text_dialog.nml:19
        self.first_focus = _bind(lambda _o: self.ending)    # convert_text_dialog.nml:23
        self.buttons_row = _bind(lambda _o: (self.pick, self.abandon))    # convert_text_dialog.nml:25

        self.encoding.y = 1    # convert_text_dialog.nml:29
        self.encoding.label_text = _bind(    # convert_text_dialog.nml:33
            lambda _o: _tr('~E~ncoding'),
            yielding=True,
        )
        self.encoding.label_width = 24    # convert_text_dialog.nml:34
        self.encoding.x = 2    # convert_text_dialog.nml:31
        self.encoding.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # convert_text_dialog.nml:32

        self.fallback.y = 2    # convert_text_dialog.nml:38
        self.fallback.label_text = _bind(    # convert_text_dialog.nml:42
            lambda _o: _tr('Read ~n~on-UTF-8 as'),
            yielding=True,
        )
        self.fallback.label_width = 24    # convert_text_dialog.nml:43
        self.fallback.x = 2    # convert_text_dialog.nml:40
        self.fallback.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # convert_text_dialog.nml:41

        self.ending_caption.x = 2    # convert_text_dialog.nml:47
        self.ending_caption.y = 4    # convert_text_dialog.nml:48
        self.ending_caption.width = 14    # convert_text_dialog.nml:49
        self.ending_caption.text = _bind(    # convert_text_dialog.nml:50
            lambda _o: _tr('~L~ine endings'),
            yielding=True,
        )
        self.ending_caption.link = _bind(lambda _o: self.ending)    # convert_text_dialog.nml:51

        self.ending.x = 2    # convert_text_dialog.nml:55
        self.ending.y = 5    # convert_text_dialog.nml:56
        self.ending.width = 28    # convert_text_dialog.nml:57
        self.ending.height = 4    # convert_text_dialog.nml:58
        self.ending.items = _bind(    # convert_text_dialog.nml:59
            lambda _o: [_tr("Kee~p~ each line's"), _tr('L~F~ (Unix)'), _tr('~C~RLF (DOS, Windows)'), _tr('C~R~ (classic Mac)')],
            yielding=True,
        )

        self.options.y = 5    # convert_text_dialog.nml:63
        self.options.height = 1    # convert_text_dialog.nml:64
        self.options.items = _bind(    # convert_text_dialog.nml:68
            lambda _o: [_tr('Keep file ~t~imes')],
            yielding=True,
        )
        self.options.x = 32    # convert_text_dialog.nml:66
        self.options.width = _bind(lambda _o: max(0, _o.parent.width - 34))    # convert_text_dialog.nml:67

        _w1.justify = 'start'    # convert_text_dialog.nml:71
        _w1.x = 17# convert_text_dialog.nml:73
        _w1.width = _bind(lambda _o: max(0, _o.parent.width - 17))    # convert_text_dialog.nml:74
        _w1.y = _bind(lambda _o: max(0, _o.parent.height - 2 - _o.height))    # convert_text_dialog.nml:75

        self.pick.text = _bind(lambda _o: _tr('O~K~'), yielding=True)    # convert_text_dialog.nml:79
        self.pick.default = True    # convert_text_dialog.nml:80

        async def _on_click(event):    # convert_text_dialog.nml:81
            self.close(self.accept())
            return True
        self.pick.on_click = _on_click

        self.abandon.text = _bind(lambda _o: _tr('Cancel'), yielding=True)    # convert_text_dialog.nml:85
        self.abandon.on_click = self.on_abandon_click    # convert_text_dialog.nml:84

        self._navml_built(__class__)

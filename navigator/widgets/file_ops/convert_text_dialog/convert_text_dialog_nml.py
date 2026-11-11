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
    encoding: ChoiceField    # convert_text_dialog.nml:21
    fallback: ChoiceField    # convert_text_dialog.nml:31
    ending_caption: Label    # convert_text_dialog.nml:41
    ending: RadioButtons    # convert_text_dialog.nml:50
    options: CheckBoxes    # convert_text_dialog.nml:58
    pick: Button    # convert_text_dialog.nml:74
    abandon: Button    # convert_text_dialog.nml:79

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_pick_click(self, event: _Event) -> bool:    # convert_text_dialog.nml:74
        """``pick`` raised an event whose handler is ``on_click``."""
        return False

    async def on_abandon_click(self, event: _Event) -> bool:    # convert_text_dialog.nml:79
        """``abandon`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.encoding = ChoiceField(parent=self)    # convert_text_dialog.nml:20
        self.fallback = ChoiceField(parent=self)    # convert_text_dialog.nml:30
        self.ending_caption = Label(parent=self)    # convert_text_dialog.nml:40
        self.ending = RadioButtons(parent=self)    # convert_text_dialog.nml:49
        self.options = CheckBoxes(parent=self)    # convert_text_dialog.nml:57
        _w1 = ButtonRow(parent=self)    # convert_text_dialog.nml:66
        self.pick = Button(parent=_w1)    # convert_text_dialog.nml:73
        self.abandon = Button(parent=_w1)    # convert_text_dialog.nml:78

        self.modal_width = 60    # convert_text_dialog.nml:15
        self.modal_height = 14    # convert_text_dialog.nml:16
        self.title = _bind(lambda _o: _tr('Convert Text Files'), yielding=True)    # convert_text_dialog.nml:17
        self.buttons = 'none'    # convert_text_dialog.nml:18

        self.encoding.y = 1    # convert_text_dialog.nml:22
        self.encoding.height = 1    # convert_text_dialog.nml:23
        self.encoding.label_text = _bind(    # convert_text_dialog.nml:27
            lambda _o: _tr('~E~ncoding'),
            yielding=True,
        )
        self.encoding.label_width = 22    # convert_text_dialog.nml:28
        self.encoding.x = 2    # convert_text_dialog.nml:25
        self.encoding.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # convert_text_dialog.nml:26

        self.fallback.y = 2    # convert_text_dialog.nml:32
        self.fallback.height = 1    # convert_text_dialog.nml:33
        self.fallback.label_text = _bind(    # convert_text_dialog.nml:37
            lambda _o: _tr('Read ~n~on-UTF-8 as'),
            yielding=True,
        )
        self.fallback.label_width = 22    # convert_text_dialog.nml:38
        self.fallback.x = 2    # convert_text_dialog.nml:35
        self.fallback.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # convert_text_dialog.nml:36

        self.ending_caption.x = 2    # convert_text_dialog.nml:42
        self.ending_caption.y = 4    # convert_text_dialog.nml:43
        self.ending_caption.width = 14    # convert_text_dialog.nml:44
        self.ending_caption.height = 1    # convert_text_dialog.nml:45
        self.ending_caption.text = _bind(    # convert_text_dialog.nml:46
            lambda _o: _tr('~L~ine endings'),
            yielding=True,
        )
        self.ending_caption.link = _bind(lambda _o: self.ending)    # convert_text_dialog.nml:47

        self.ending.x = 2    # convert_text_dialog.nml:51
        self.ending.y = 5    # convert_text_dialog.nml:52
        self.ending.width = 28    # convert_text_dialog.nml:53
        self.ending.height = 4    # convert_text_dialog.nml:54
        self.ending.items = _bind(    # convert_text_dialog.nml:55
            lambda _o: [_tr("Kee~p~ each line's"), _tr('L~F~ (Unix)'), _tr('~C~RLF (DOS, Windows)'), _tr('C~R~ (classic Mac)')],
            yielding=True,
        )

        self.options.y = 5    # convert_text_dialog.nml:59
        self.options.height = 1    # convert_text_dialog.nml:60
        self.options.items = _bind(    # convert_text_dialog.nml:64
            lambda _o: [_tr('Keep file ~t~imes')],
            yielding=True,
        )
        self.options.x = 32    # convert_text_dialog.nml:62
        self.options.width = _bind(lambda _o: max(0, _o.parent.width - 34))    # convert_text_dialog.nml:63

        _w1.justify = 'start'    # convert_text_dialog.nml:67
        _w1.x = 17# convert_text_dialog.nml:69
        _w1.width = _bind(lambda _o: max(0, _o.parent.width - 17))    # convert_text_dialog.nml:70
        _w1.y = _bind(lambda _o: max(0, _o.parent.height - 2 - _o.height))    # convert_text_dialog.nml:71

        self.pick.text = _bind(lambda _o: _tr('O~K~'), yielding=True)    # convert_text_dialog.nml:75
        self.pick.default = True    # convert_text_dialog.nml:76
        self.pick.on_click = self.on_pick_click    # convert_text_dialog.nml:74

        self.abandon.text = _bind(lambda _o: _tr('Cancel'), yielding=True)    # convert_text_dialog.nml:80
        self.abandon.on_click = self.on_abandon_click    # convert_text_dialog.nml:79

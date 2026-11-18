# navml: generated
"""Generated from ``compare_dialog.nml``.

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
from navml.widgets.dialog.button import Button    # compare_dialog.nml:1
from navml.widgets.dialog.button_row import ButtonRow    # compare_dialog.nml:2
from navml.widgets.dialog.check_boxes import CheckBoxes    # compare_dialog.nml:3
from navml.widgets.dialog.commands import Help    # compare_dialog.nml:4
from navml.widgets.dialog.dialog import Dialog    # compare_dialog.nml:5
from navml.widgets.dialog.label import Label    # compare_dialog.nml:6
from navml.widgets.dialog.radio_buttons import RadioButtons    # compare_dialog.nml:7

__navml_component__ = "CompareDialog"

__all__ = ["CompareDialog"]


class CompareDialog(Dialog, _Component):
    """Panel > Compare directories: DOS Navigator's ``dlgCompareDirs``.

    *Options* over *Selection mode*, as ``DN.DNR`` stacks them; the buttons go
    under them rather than down the right, where this library puts every
    dialog's: OK, Cancel and Help.

    **A departure**: a third mode, *Window, recursive* -- what differs down
    both trees, listed in the *Synchronize* window (``SyncWindow``) rather
    than tagged.  Select stays first and is chosen every time, so the dialog
    opens as DN's did.
    """

    #: The document this class was generated from.
    __navml_source__ = "compare_dialog.nml"

    #: Ids, annotated so the hand-written half completes them.
    options_caption: Label    # compare_dialog.nml:29
    options: CheckBoxes    # compare_dialog.nml:38
    mode_caption: Label    # compare_dialog.nml:48
    mode: RadioButtons    # compare_dialog.nml:56
    pick: Button    # compare_dialog.nml:74
    abandon: Button    # compare_dialog.nml:79
    helper: Button    # compare_dialog.nml:84

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_pick_click(self, event: _Event) -> bool:    # compare_dialog.nml:74
        """``pick`` raised an event whose handler is ``on_click``."""
        return False

    async def on_abandon_click(self, event: _Event) -> bool:    # compare_dialog.nml:79
        """``abandon`` raised an event whose handler is ``on_click``."""
        return False

    async def on_helper_click(self, event: _Event) -> bool:    # compare_dialog.nml:84
        """``helper`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.options_caption = Label(parent=self)    # compare_dialog.nml:28
        self.options = CheckBoxes(parent=self)    # compare_dialog.nml:37
        self.mode_caption = Label(parent=self)    # compare_dialog.nml:47
        self.mode = RadioButtons(parent=self)    # compare_dialog.nml:55
        _w1 = ButtonRow(parent=self)    # compare_dialog.nml:64
        self.pick = Button(parent=_w1)    # compare_dialog.nml:73
        self.abandon = Button(parent=_w1)    # compare_dialog.nml:78
        self.helper = Button(parent=_w1)    # compare_dialog.nml:83

        self.help_topic = 'compare.md#compare-directories'    # compare_dialog.nml:20
        self.modal_width = 34    # compare_dialog.nml:21
        self.modal_height = 16    # compare_dialog.nml:22
        self.title = _bind(    # compare_dialog.nml:23
            lambda _o: _tr('Compare directories'),
            yielding=True,
        )
        self.buttons = 'none'    # compare_dialog.nml:24
        self.buttons_row = _bind(    # compare_dialog.nml:26
            lambda _o: (self.pick, self.abandon, self.helper)
        )

        self.options_caption.x = 2    # compare_dialog.nml:30
        self.options_caption.y = 1    # compare_dialog.nml:31
        self.options_caption.width = 12    # compare_dialog.nml:32
        self.options_caption.text = _bind(    # compare_dialog.nml:33
            lambda _o: _tr('Options'),
            yielding=True,
        )
        self.options_caption.link = _bind(lambda _o: self.options)    # compare_dialog.nml:34

        self.options.x = 2    # compare_dialog.nml:39
        self.options.y = 2    # compare_dialog.nml:40
        self.options.width = 26    # compare_dialog.nml:41
        self.options.height = 4    # compare_dialog.nml:42
        self.options.items = _bind(    # compare_dialog.nml:43
            lambda _o: [_tr('Compare ~s~ize'), _tr('Compare ~t~ime'), _tr('Compare ~a~ttributes'), _tr('Compare ~c~ontents')],
            yielding=True,
        )
        self.options.tooltips = _bind(    # compare_dialog.nml:44
            lambda _o: [_tr('Files of different sizes are different'), _tr('A newer file is different from an older one'), _tr('Files with different permissions are different'), _tr('Read files of the same size through and compare them: slow, but certain')],
            yielding=True,
        )
        self.options.value = 3    # compare_dialog.nml:45

        self.mode_caption.x = 2    # compare_dialog.nml:49
        self.mode_caption.y = 7    # compare_dialog.nml:50
        self.mode_caption.width = 16    # compare_dialog.nml:51
        self.mode_caption.text = _bind(    # compare_dialog.nml:52
            lambda _o: _tr('Selection mode'),
            yielding=True,
        )
        self.mode_caption.link = _bind(lambda _o: self.mode)    # compare_dialog.nml:53

        self.mode.x = 2    # compare_dialog.nml:57
        self.mode.y = 8    # compare_dialog.nml:58
        self.mode.width = 26    # compare_dialog.nml:59
        self.mode.height = 3    # compare_dialog.nml:60
        self.mode.items = _bind(    # compare_dialog.nml:61
            lambda _o: [_tr('S~e~lect'), _tr('~U~nselect'), _tr('~W~indow, recursive')],
            yielding=True,
        )

        _w1.justify = 'start'    # compare_dialog.nml:65
        _w1.button_width = 10    # compare_dialog.nml:66
        _w1.spacing = 0    # compare_dialog.nml:67
        _w1.x = 2# compare_dialog.nml:69
        _w1.width = _bind(lambda _o: max(0, _o.parent.width - 2))    # compare_dialog.nml:70
        _w1.y = _bind(lambda _o: max(0, _o.parent.height - 2 - _o.height))    # compare_dialog.nml:71

        self.pick.text = _bind(lambda _o: _tr('O~K~'), yielding=True)    # compare_dialog.nml:75
        self.pick.default = True    # compare_dialog.nml:76
        self.pick.on_click = self.on_pick_click    # compare_dialog.nml:74

        self.abandon.text = _bind(lambda _o: _tr('Cancel'), yielding=True)    # compare_dialog.nml:80
        self.abandon.on_click = self.on_abandon_click    # compare_dialog.nml:79

        self.helper.text = _bind(lambda _o: _tr('Help'), yielding=True)    # compare_dialog.nml:85
        self.helper.command = Help    # compare_dialog.nml:86
        self.helper.on_click = self.on_helper_click    # compare_dialog.nml:84

        self._navml_built(__class__)

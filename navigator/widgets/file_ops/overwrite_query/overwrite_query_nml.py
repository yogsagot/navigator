# navml: generated
"""Generated from ``overwrite_query.nml``.

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
from navml.widgets.dialog.button import Button    # overwrite_query.nml:1
from navml.widgets.dialog.button_row import ButtonRow    # overwrite_query.nml:2
from navml.widgets.dialog.check_boxes import CheckBoxes    # overwrite_query.nml:3
from navml.widgets.dialog.dialog import Dialog    # overwrite_query.nml:4
from navml.widgets.dialog.static_text import StaticText    # overwrite_query.nml:5

__navml_component__ = "OverwriteQuery"

__all__ = ["OverwriteQuery"]


class OverwriteQuery(Dialog, _Component):
    """A file the copy is about to land on: DOS Navigator's ``dlgOverwriteQuery``.

    The text is ``Overwrite``'s in ``FILECOPY.PAS`` -- the name, then
    ``dlFCOver``'s three centred lines -- and the buttons are the resource's
    five in its order, *Overwrite* two columns wider than the rest as it was
    there.  Six columns wider than DN's 60, because this library's buttons are
    eleven wide with their markers and five of them do not fit in 60.
    """

    #: The document this class was generated from.
    __navml_source__ = "overwrite_query.nml"

    #: Ids, annotated so the hand-written half completes them.
    details: StaticText    # overwrite_query.nml:21
    for_all: CheckBoxes    # overwrite_query.nml:32
    overwrite: Button    # overwrite_query.nml:42
    append: Button    # overwrite_query.nml:61
    rename: Button    # overwrite_query.nml:66
    skip: Button    # overwrite_query.nml:71
    abandon: Button    # overwrite_query.nml:76

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_abandon_click(self, event: _Event) -> bool:    # overwrite_query.nml:76
        """``abandon`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.details = StaticText(parent=self)    # overwrite_query.nml:20
        self.for_all = CheckBoxes(parent=self)    # overwrite_query.nml:31
        self.overwrite = Button(parent=self)    # overwrite_query.nml:41
        _w1 = ButtonRow(parent=self)    # overwrite_query.nml:52
        self.append = Button(parent=_w1)    # overwrite_query.nml:60
        self.rename = Button(parent=_w1)    # overwrite_query.nml:65
        self.skip = Button(parent=_w1)    # overwrite_query.nml:70
        self.abandon = Button(parent=_w1)    # overwrite_query.nml:75

        self.modal_width = 66    # overwrite_query.nml:15
        self.modal_height = 13    # overwrite_query.nml:16
        self.title = _bind(lambda _o: _tr('Confirm'), yielding=True)    # overwrite_query.nml:17
        self.buttons = 'none'    # overwrite_query.nml:18

        self.details.y = 2    # overwrite_query.nml:22
        self.details.height = 5    # overwrite_query.nml:23
        self.details.align = 'center'    # overwrite_query.nml:27
        self.details.x = 1    # overwrite_query.nml:25
        self.details.width = _bind(lambda _o: max(0, _o.parent.width - 2))    # overwrite_query.nml:26

        self.for_all.y = 8    # overwrite_query.nml:33
        self.for_all.height = 1    # overwrite_query.nml:34
        self.for_all.items = _bind(    # overwrite_query.nml:38
            lambda _o: [_tr('Accept choice for ~a~ll files')],
            yielding=True,
        )
        self.for_all.tooltips = _bind(    # overwrite_query.nml:39
            lambda _o: [_tr('Give this answer for every file that is already there')],
            yielding=True,
        )
        self.for_all.x = 4    # overwrite_query.nml:36
        self.for_all.width = _bind(lambda _o: max(0, _o.parent.width - 8))    # overwrite_query.nml:37

        self.overwrite.text = _bind(    # overwrite_query.nml:43
            lambda _o: _tr('~O~verwrite'),
            yielding=True,
        )
        self.overwrite.default = True    # overwrite_query.nml:44
        self.overwrite.x = 2    # overwrite_query.nml:45
        self.overwrite.width = 13    # overwrite_query.nml:46
        self.overwrite.height = 2    # overwrite_query.nml:47
        self.overwrite.y = _bind(    # overwrite_query.nml:49
            lambda _o: max(0, _o.parent.height - 2 - _o.height)
        )

        async def _on_click(event):    # overwrite_query.nml:50
            self._answer('overwrite')
            return True
        self.overwrite.on_click = _on_click

        _w1.justify = 'start'    # overwrite_query.nml:53
        _w1.spacing = 1    # overwrite_query.nml:54
        _w1.x = 16# overwrite_query.nml:56
        _w1.width = _bind(lambda _o: max(0, _o.parent.width - 16))    # overwrite_query.nml:57
        _w1.y = _bind(lambda _o: max(0, _o.parent.height - 2 - _o.height))    # overwrite_query.nml:58

        self.append.text = _bind(lambda _o: _tr('A~p~pend'), yielding=True)    # overwrite_query.nml:62

        async def _on_click(event):    # overwrite_query.nml:63
            self._answer('append')
            return True
        self.append.on_click = _on_click

        self.rename.text = _bind(lambda _o: _tr('~R~ename'), yielding=True)    # overwrite_query.nml:67

        async def _on_click(event):    # overwrite_query.nml:68
            self.spawn(self.ask_name())
            return True
        self.rename.on_click = _on_click

        self.skip.text = _bind(lambda _o: _tr('~S~kip'), yielding=True)    # overwrite_query.nml:72

        async def _on_click(event):    # overwrite_query.nml:73
            self._answer('skip')
            return True
        self.skip.on_click = _on_click

        self.abandon.text = _bind(lambda _o: _tr('Cancel'), yielding=True)    # overwrite_query.nml:77
        self.abandon.on_click = self.on_abandon_click    # overwrite_query.nml:76

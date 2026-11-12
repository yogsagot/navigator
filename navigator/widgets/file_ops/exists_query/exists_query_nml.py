# navml: generated
"""Generated from ``exists_query.nml``.

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
from navml.widgets.dialog.button import Button    # exists_query.nml:1
from navml.widgets.dialog.button_row import ButtonRow    # exists_query.nml:2
from navml.widgets.dialog.dialog import Dialog    # exists_query.nml:3
from navml.widgets.dialog.static_text import StaticText    # exists_query.nml:4

__navml_component__ = "ExistsQuery"

__all__ = ["ExistsQuery"]


class ExistsQuery(Dialog, _Component):
    """``dlFileExist`` with ``mfYesButton + mfNoButton + mfAllButton +

    mfCancelButton``: what UU Encode and UU Decode ask of a file that is there
    already.  *Yes* first and the default, as the message box had it.
    """

    #: The document this class was generated from.
    __navml_source__ = "exists_query.nml"

    #: Ids, annotated so the hand-written half completes them.
    details: StaticText    # exists_query.nml:18
    agree: Button    # exists_query.nml:34
    refuse: Button    # exists_query.nml:40
    every: Button    # exists_query.nml:45
    abandon: Button    # exists_query.nml:50

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_abandon_click(self, event: _Event) -> bool:    # exists_query.nml:50
        """``abandon`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.details = StaticText(parent=self)    # exists_query.nml:17
        _w1 = ButtonRow(parent=self)    # exists_query.nml:27
        self.agree = Button(parent=_w1)    # exists_query.nml:33
        self.refuse = Button(parent=_w1)    # exists_query.nml:39
        self.every = Button(parent=_w1)    # exists_query.nml:44
        self.abandon = Button(parent=_w1)    # exists_query.nml:49

        self.modal_width = 58    # exists_query.nml:10
        self.modal_height = 9    # exists_query.nml:11
        self.title = _bind(lambda _o: _tr('Confirm'), yielding=True)    # exists_query.nml:12
        self.buttons = 'none'    # exists_query.nml:13
        self.buttons_row = _bind(    # exists_query.nml:15
            lambda _o: (self.agree, self.refuse, self.every, self.abandon)
        )

        self.details.y = 1    # exists_query.nml:19
        self.details.height = 2    # exists_query.nml:20
        self.details.align = 'center'    # exists_query.nml:24
        self.details.x = 1    # exists_query.nml:22
        self.details.width = _bind(lambda _o: max(0, _o.parent.width - 2))    # exists_query.nml:23

        _w1.x = 0# exists_query.nml:29
        _w1.width = _bind(lambda _o: max(0, _o.parent.width))    # exists_query.nml:30
        _w1.y = _bind(lambda _o: max(0, _o.parent.height - 2 - _o.height))    # exists_query.nml:31

        self.agree.text = _bind(lambda _o: _tr('~Y~es'), yielding=True)    # exists_query.nml:35
        self.agree.default = True    # exists_query.nml:36

        async def _on_click(event):    # exists_query.nml:37
            self.close('yes')
            return True
        self.agree.on_click = _on_click

        self.refuse.text = _bind(lambda _o: _tr('~N~o'), yielding=True)    # exists_query.nml:41

        async def _on_click(event):    # exists_query.nml:42
            self.close('no')
            return True
        self.refuse.on_click = _on_click

        self.every.text = _bind(lambda _o: _tr('~A~ll'), yielding=True)    # exists_query.nml:46

        async def _on_click(event):    # exists_query.nml:47
            self.close('all')
            return True
        self.every.on_click = _on_click

        self.abandon.text = _bind(lambda _o: _tr('Cancel'), yielding=True)    # exists_query.nml:51
        self.abandon.on_click = self.on_abandon_click    # exists_query.nml:50

        self._navml_built(__class__)

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
from navkit.reactive import bind as _bind

from navml.component import Component as _Component
from navml.widgets.dialog.button import Button    # exists_query.nml:1
from navml.widgets.dialog.dialog import Dialog    # exists_query.nml:2
from navml.widgets.dialog.static_text import StaticText    # exists_query.nml:3

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
    details: StaticText    # exists_query.nml:14
    agree: Button    # exists_query.nml:22
    refuse: Button    # exists_query.nml:31
    every: Button    # exists_query.nml:39
    abandon: Button    # exists_query.nml:47

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_agree_click(self, event: _Event) -> bool:    # exists_query.nml:22
        """``agree`` raised an event whose handler is ``on_click``."""
        return False

    async def on_refuse_click(self, event: _Event) -> bool:    # exists_query.nml:31
        """``refuse`` raised an event whose handler is ``on_click``."""
        return False

    async def on_every_click(self, event: _Event) -> bool:    # exists_query.nml:39
        """``every`` raised an event whose handler is ``on_click``."""
        return False

    async def on_abandon_click(self, event: _Event) -> bool:    # exists_query.nml:47
        """``abandon`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.details = StaticText(parent=self)    # exists_query.nml:13
        self.agree = Button(parent=self)    # exists_query.nml:21
        self.refuse = Button(parent=self)    # exists_query.nml:30
        self.every = Button(parent=self)    # exists_query.nml:38
        self.abandon = Button(parent=self)    # exists_query.nml:46

        self.modal_width = 58    # exists_query.nml:9
        self.modal_height = 9    # exists_query.nml:10
        self.title = 'Confirm'    # exists_query.nml:11

        self.details.x = 1    # exists_query.nml:15
        self.details.y = 1    # exists_query.nml:16
        self.details.width = _bind(lambda _o: max(0, _o.parent.width - 2))    # exists_query.nml:17
        self.details.height = 2    # exists_query.nml:18
        self.details.align = 'center'    # exists_query.nml:19

        self.agree.text = '~Y~es'    # exists_query.nml:23
        self.agree.default = True    # exists_query.nml:24
        self.agree.x = _bind(lambda _o: self.slot(0))    # exists_query.nml:25
        self.agree.y = _bind(lambda _o: max(0, _o.parent.height - 4))    # exists_query.nml:26
        self.agree.width = 11    # exists_query.nml:27
        self.agree.height = 2    # exists_query.nml:28
        self.agree.on_click = self.on_agree_click    # exists_query.nml:22

        self.refuse.text = '~N~o'    # exists_query.nml:32
        self.refuse.x = _bind(lambda _o: self.slot(1))    # exists_query.nml:33
        self.refuse.y = _bind(lambda _o: max(0, _o.parent.height - 4))    # exists_query.nml:34
        self.refuse.width = 11    # exists_query.nml:35
        self.refuse.height = 2    # exists_query.nml:36
        self.refuse.on_click = self.on_refuse_click    # exists_query.nml:31

        self.every.text = '~A~ll'    # exists_query.nml:40
        self.every.x = _bind(lambda _o: self.slot(2))    # exists_query.nml:41
        self.every.y = _bind(lambda _o: max(0, _o.parent.height - 4))    # exists_query.nml:42
        self.every.width = 11    # exists_query.nml:43
        self.every.height = 2    # exists_query.nml:44
        self.every.on_click = self.on_every_click    # exists_query.nml:39

        self.abandon.text = 'Cancel'    # exists_query.nml:48
        self.abandon.x = _bind(lambda _o: self.slot(3))    # exists_query.nml:49
        self.abandon.y = _bind(lambda _o: max(0, _o.parent.height - 4))    # exists_query.nml:50
        self.abandon.width = 11    # exists_query.nml:51
        self.abandon.height = 2    # exists_query.nml:52
        self.abandon.on_click = self.on_abandon_click    # exists_query.nml:47

# navml: generated
"""Generated from ``erase_query.nml``.

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
from navkit.reactive import reactive as _reactive

from navml.component import Component as _Component
from navml.widgets.dialog.button import Button    # erase_query.nml:1
from navml.widgets.dialog.dialog import Dialog    # erase_query.nml:2
from navml.widgets.dialog.static_text import StaticText    # erase_query.nml:3

__navml_component__ = "EraseQuery"

__all__ = ["EraseQuery"]


class EraseQuery(Dialog, _Component):
    """What a delete asks on the way, as ``ERASER.PAS``'s message boxes asked it.

    ``not-empty`` is ``dlEraseDirNotEmpty``: *No*, *Yes*, *All*, *Cancel* in
    that order and the focus on *No*, so Enter on it deletes nothing.
    ``read-only`` is ``dlEraseRO``: *Yes*, *No*, *All*, and Esc for Cancel.
    The buttons are placed by :meth:`slot`, because which comes first is the
    kind's.
    """

    #: The document this class was generated from.
    __navml_source__ = "erase_query.nml"

    #: ``not-empty`` or ``read-only``.
    kind: str = _reactive('not-empty')    # erase_query.nml:19

    #: Ids, annotated so the hand-written half completes them.
    details: StaticText    # erase_query.nml:22
    refuse: Button    # erase_query.nml:31
    agree: Button    # erase_query.nml:41
    every: Button    # erase_query.nml:51
    abandon: Button    # erase_query.nml:60

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_refuse_click(self, event: _Event) -> bool:    # erase_query.nml:31
        """``refuse`` raised an event whose handler is ``on_click``."""
        return False

    async def on_agree_click(self, event: _Event) -> bool:    # erase_query.nml:41
        """``agree`` raised an event whose handler is ``on_click``."""
        return False

    async def on_every_click(self, event: _Event) -> bool:    # erase_query.nml:51
        """``every`` raised an event whose handler is ``on_click``."""
        return False

    async def on_abandon_click(self, event: _Event) -> bool:    # erase_query.nml:60
        """``abandon`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.details = StaticText(parent=self)    # erase_query.nml:21
        self.refuse = Button(parent=self)    # erase_query.nml:30
        self.agree = Button(parent=self)    # erase_query.nml:40
        self.every = Button(parent=self)    # erase_query.nml:50
        self.abandon = Button(parent=self)    # erase_query.nml:59

        self.modal_width = 54    # erase_query.nml:13
        self.modal_height = 10    # erase_query.nml:14
        self.title = _bind(lambda _o: _tr('Confirm'), yielding=True)    # erase_query.nml:15
        self.buttons = 'none'    # erase_query.nml:16

        self.details.y = 1    # erase_query.nml:23
        self.details.height = 3    # erase_query.nml:24
        self.details.align = 'center'    # erase_query.nml:28
        self.details.x = 1    # erase_query.nml:26
        self.details.width = _bind(lambda _o: max(0, _o.parent.width - 2))    # erase_query.nml:27

        self.refuse.text = _bind(lambda _o: _tr('~N~o'), yielding=True)    # erase_query.nml:32
        self.refuse.default = _bind(lambda _o: self.kind == 'not-empty')    # erase_query.nml:33
        self.refuse.x = _bind(    # erase_query.nml:34
            lambda _o: self.slot(0 if self.kind == 'not-empty' else 1)
        )
        self.refuse.width = 11    # erase_query.nml:35
        self.refuse.height = 2    # erase_query.nml:36
        self.refuse.y = _bind(    # erase_query.nml:38
            lambda _o: max(0, _o.parent.height - 2 - _o.height)
        )
        self.refuse.on_click = self.on_refuse_click    # erase_query.nml:31

        self.agree.text = _bind(lambda _o: _tr('~Y~es'), yielding=True)    # erase_query.nml:42
        self.agree.default = _bind(lambda _o: self.kind != 'not-empty')    # erase_query.nml:43
        self.agree.x = _bind(    # erase_query.nml:44
            lambda _o: self.slot(1 if self.kind == 'not-empty' else 0)
        )
        self.agree.width = 11    # erase_query.nml:45
        self.agree.height = 2    # erase_query.nml:46
        self.agree.y = _bind(    # erase_query.nml:48
            lambda _o: max(0, _o.parent.height - 2 - _o.height)
        )
        self.agree.on_click = self.on_agree_click    # erase_query.nml:41

        self.every.text = _bind(lambda _o: _tr('~A~ll'), yielding=True)    # erase_query.nml:52
        self.every.x = _bind(lambda _o: self.slot(2))    # erase_query.nml:53
        self.every.width = 11    # erase_query.nml:54
        self.every.height = 2    # erase_query.nml:55
        self.every.y = _bind(    # erase_query.nml:57
            lambda _o: max(0, _o.parent.height - 2 - _o.height)
        )
        self.every.on_click = self.on_every_click    # erase_query.nml:51

        self.abandon.text = _bind(lambda _o: _tr('Cancel'), yielding=True)    # erase_query.nml:61
        self.abandon.visible = _bind(lambda _o: self.kind == 'not-empty')    # erase_query.nml:62
        self.abandon.x = _bind(lambda _o: self.slot(3))    # erase_query.nml:63
        self.abandon.width = 11    # erase_query.nml:64
        self.abandon.height = 2    # erase_query.nml:65
        self.abandon.y = _bind(    # erase_query.nml:67
            lambda _o: max(0, _o.parent.height - 2 - _o.height)
        )
        self.abandon.on_click = self.on_abandon_click    # erase_query.nml:60

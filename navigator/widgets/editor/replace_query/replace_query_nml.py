# navml: generated
"""Generated from ``replace_query.nml``.

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
from navml.widgets.dialog.button import Button    # replace_query.nml:1
from navml.widgets.dialog.button_row import ButtonRow    # replace_query.nml:2
from navml.widgets.dialog.dialog import Dialog    # replace_query.nml:3

__navml_component__ = "ReplaceQuery"

__all__ = ["ReplaceQuery"]


class ReplaceQuery(Dialog, _Component):
    """``dlQueryReplace``, a 50 by 8 ``mfQuery`` box, *Query*: Yes, No, All and Cancel,

    the buttons in their flags' order, 10 wide and 2 apart, centred (``MessageBoxRect``).
    """

    #: The document this class was generated from.
    __navml_source__ = "replace_query.nml"

    #: Ids, annotated so the hand-written half completes them.
    pick: Button    # replace_query.nml:24
    skip: Button    # replace_query.nml:30
    every: Button    # replace_query.nml:36
    abandon: Button    # replace_query.nml:41

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_abandon_click(self, event: _Event) -> bool:    # replace_query.nml:41
        """``abandon`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        _w1 = ButtonRow(parent=self)    # replace_query.nml:16
        self.pick = Button(parent=_w1)    # replace_query.nml:23
        self.skip = Button(parent=_w1)    # replace_query.nml:29
        self.every = Button(parent=_w1)    # replace_query.nml:35
        self.abandon = Button(parent=_w1)    # replace_query.nml:40

        self.modal_width = 50    # replace_query.nml:8
        self.modal_height = 8    # replace_query.nml:9
        self.title = _bind(lambda _o: _tr('Query'), yielding=True)    # replace_query.nml:10
        self.buttons = 'none'    # replace_query.nml:11
        self.prompt = _bind(    # replace_query.nml:12
            lambda _o: _tr('Replace this occurence?'),
            yielding=True,
        )
        self.buttons_row = _bind(    # replace_query.nml:14
            lambda _o: (self.pick, self.skip, self.every, self.abandon)
        )

        _w1.button_width = 10    # replace_query.nml:17
        _w1.x = 0# replace_query.nml:19
        _w1.width = _bind(lambda _o: max(0, _o.parent.width))    # replace_query.nml:20
        _w1.y = _bind(lambda _o: max(0, _o.parent.height - 2 - _o.height))    # replace_query.nml:21

        self.pick.text = _bind(lambda _o: _tr('~Y~es'), yielding=True)    # replace_query.nml:25
        self.pick.default = True    # replace_query.nml:26

        async def _on_click(event):    # replace_query.nml:27
            self.close('yes')
            return True
        self.pick.on_click = _on_click

        self.skip.text = _bind(lambda _o: _tr('~N~o'), yielding=True)    # replace_query.nml:31

        async def _on_click(event):    # replace_query.nml:32
            self.close('no')
            return True
        self.skip.on_click = _on_click

        self.every.text = _bind(lambda _o: _tr('~A~ll'), yielding=True)    # replace_query.nml:37

        async def _on_click(event):    # replace_query.nml:38
            self.close('all')
            return True
        self.every.on_click = _on_click

        self.abandon.text = _bind(lambda _o: _tr('Cancel'), yielding=True)    # replace_query.nml:42
        self.abandon.on_click = self.on_abandon_click    # replace_query.nml:41

        self._navml_built(__class__)

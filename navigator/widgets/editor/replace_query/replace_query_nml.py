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
from navml.widgets.dialog.dialog import Dialog    # replace_query.nml:2

__navml_component__ = "ReplaceQuery"

__all__ = ["ReplaceQuery"]


class ReplaceQuery(Dialog, _Component):
    """``dlQueryReplace``, a 50 by 8 ``mfQuery`` box, *Query*: Yes, No, All and Cancel,

    the buttons in their flags' order, 10 wide and 2 apart, centred (``MessageBoxRect``).
    """

    #: The document this class was generated from.
    __navml_source__ = "replace_query.nml"

    #: Ids, annotated so the hand-written half completes them.
    pick: Button    # replace_query.nml:13
    skip: Button    # replace_query.nml:22
    every: Button    # replace_query.nml:31
    abandon: Button    # replace_query.nml:39

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_pick_click(self, event: _Event) -> bool:    # replace_query.nml:13
        """``pick`` raised an event whose handler is ``on_click``."""
        return False

    async def on_skip_click(self, event: _Event) -> bool:    # replace_query.nml:22
        """``skip`` raised an event whose handler is ``on_click``."""
        return False

    async def on_every_click(self, event: _Event) -> bool:    # replace_query.nml:31
        """``every`` raised an event whose handler is ``on_click``."""
        return False

    async def on_abandon_click(self, event: _Event) -> bool:    # replace_query.nml:39
        """``abandon`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.pick = Button(parent=self)    # replace_query.nml:12
        self.skip = Button(parent=self)    # replace_query.nml:21
        self.every = Button(parent=self)    # replace_query.nml:30
        self.abandon = Button(parent=self)    # replace_query.nml:38

        self.modal_width = 50    # replace_query.nml:7
        self.modal_height = 8    # replace_query.nml:8
        self.title = _bind(lambda _o: _tr('Query'), yielding=True)    # replace_query.nml:9
        self.prompt = _bind(    # replace_query.nml:10
            lambda _o: _tr('Replace this occurence?'),
            yielding=True,
        )

        self.pick.text = _bind(lambda _o: _tr('~Y~es'), yielding=True)    # replace_query.nml:14
        self.pick.default = True    # replace_query.nml:15
        self.pick.x = 2    # replace_query.nml:16
        self.pick.y = _bind(lambda _o: max(0, _o.parent.height - 4))    # replace_query.nml:17
        self.pick.width = 10    # replace_query.nml:18
        self.pick.height = 2    # replace_query.nml:19
        self.pick.on_click = self.on_pick_click    # replace_query.nml:13

        self.skip.text = _bind(lambda _o: _tr('~N~o'), yielding=True)    # replace_query.nml:23
        self.skip.x = 14    # replace_query.nml:24
        self.skip.y = _bind(lambda _o: max(0, _o.parent.height - 4))    # replace_query.nml:25
        self.skip.width = 10    # replace_query.nml:26
        self.skip.height = 2    # replace_query.nml:27
        self.skip.on_click = self.on_skip_click    # replace_query.nml:22

        self.every.text = _bind(lambda _o: _tr('~A~ll'), yielding=True)    # replace_query.nml:32
        self.every.x = 26    # replace_query.nml:33
        self.every.y = _bind(lambda _o: max(0, _o.parent.height - 4))    # replace_query.nml:34
        self.every.width = 10    # replace_query.nml:35
        self.every.height = 2    # replace_query.nml:36
        self.every.on_click = self.on_every_click    # replace_query.nml:31

        self.abandon.text = _bind(lambda _o: _tr('Cancel'), yielding=True)    # replace_query.nml:40
        self.abandon.x = 38    # replace_query.nml:41
        self.abandon.y = _bind(lambda _o: max(0, _o.parent.height - 4))    # replace_query.nml:42
        self.abandon.width = 10    # replace_query.nml:43
        self.abandon.height = 2    # replace_query.nml:44
        self.abandon.on_click = self.on_abandon_click    # replace_query.nml:39

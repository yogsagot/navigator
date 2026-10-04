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
from navkit.reactive import bind as _bind

from navml.component import Component as _Component
from navml.widgets.dialog.button import Button    # replace_query.nml:1
from navml.widgets.dialog.dialog import Dialog    # replace_query.nml:2

__navml_component__ = "ReplaceQuery"

__all__ = ["ReplaceQuery"]


class ReplaceQuery(Dialog, _Component):
    """``dlQueryReplace``, a 50 by 8 ``mfQuery`` box: Yes, All, No and Cancel."""

    #: The document this class was generated from.
    __navml_source__ = "replace_query.nml"

    #: Ids, annotated so the hand-written half completes them.
    pick: Button    # replace_query.nml:12
    every: Button    # replace_query.nml:22
    skip: Button    # replace_query.nml:30
    abandon: Button    # replace_query.nml:38

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_pick_click(self, event: _Event) -> bool:    # replace_query.nml:12
        """``pick`` raised an event whose handler is ``on_click``."""
        return False

    async def on_every_click(self, event: _Event) -> bool:    # replace_query.nml:22
        """``every`` raised an event whose handler is ``on_click``."""
        return False

    async def on_skip_click(self, event: _Event) -> bool:    # replace_query.nml:30
        """``skip`` raised an event whose handler is ``on_click``."""
        return False

    async def on_abandon_click(self, event: _Event) -> bool:    # replace_query.nml:38
        """``abandon`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.pick = Button(parent=self)    # replace_query.nml:11
        self.every = Button(parent=self)    # replace_query.nml:21
        self.skip = Button(parent=self)    # replace_query.nml:29
        self.abandon = Button(parent=self)    # replace_query.nml:37

        self.modal_width = 50    # replace_query.nml:6
        self.modal_height = 8    # replace_query.nml:7
        self.title = 'Confirm'    # replace_query.nml:8
        self.prompt = 'Replace this occurence?'    # replace_query.nml:9

        self.pick.text = '~Y~es'    # replace_query.nml:13
        self.pick.default = True    # replace_query.nml:14
        self.pick.x = 3    # replace_query.nml:15
        self.pick.y = _bind(lambda _o: max(0, _o.parent.height - 4))    # replace_query.nml:16
        self.pick.width = 10    # replace_query.nml:17
        self.pick.height = 2    # replace_query.nml:18
        self.pick.on_click = self.on_pick_click    # replace_query.nml:12

        self.every.text = '~A~ll'    # replace_query.nml:23
        self.every.x = 14    # replace_query.nml:24
        self.every.y = _bind(lambda _o: max(0, _o.parent.height - 4))    # replace_query.nml:25
        self.every.width = 10    # replace_query.nml:26
        self.every.height = 2    # replace_query.nml:27
        self.every.on_click = self.on_every_click    # replace_query.nml:22

        self.skip.text = '~N~o'    # replace_query.nml:31
        self.skip.x = 25    # replace_query.nml:32
        self.skip.y = _bind(lambda _o: max(0, _o.parent.height - 4))    # replace_query.nml:33
        self.skip.width = 10    # replace_query.nml:34
        self.skip.height = 2    # replace_query.nml:35
        self.skip.on_click = self.on_skip_click    # replace_query.nml:30

        self.abandon.text = 'Cancel'    # replace_query.nml:39
        self.abandon.x = 36    # replace_query.nml:40
        self.abandon.y = _bind(lambda _o: max(0, _o.parent.height - 4))    # replace_query.nml:41
        self.abandon.width = 10    # replace_query.nml:42
        self.abandon.height = 2    # replace_query.nml:43
        self.abandon.on_click = self.on_abandon_click    # replace_query.nml:38

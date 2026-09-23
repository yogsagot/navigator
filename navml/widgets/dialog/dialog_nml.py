# navml: generated
"""Generated from ``dialog.nml``.

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
from navkit.reactive import reactive as _reactive

from navml.component import Component as _Component
from navml.widgets.button import Button    # dialog.nml:1
from navml.widgets.label import Label    # dialog.nml:2

__navml_component__ = "Dialog"

__all__ = ["Dialog"]


class Dialog(_Component):
    """A prompt with three buttons.

    The worked example of a component whose *children* raise the events its
    hand-written half handles: two of the buttons are routed by the
    ``on_<id>_<event>`` convention and the third by an explicit markup line,
    which is the escape hatch for a handler named after what the component
    does rather than after what happened.
    """

    #: The document this class was generated from.
    __navml_source__ = "dialog.nml"

    prompt: str = _reactive('')    # dialog.nml:12

    #: Ids, annotated so the hand-written half completes them.
    message: Label    # dialog.nml:15
    ok: Button    # dialog.nml:24
    cancel: Button    # dialog.nml:32
    info: Button    # dialog.nml:40

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_ok_click(self, event: _Event) -> bool:    # dialog.nml:24
        """``ok`` raised an event whose handler is ``on_click``."""
        return False

    async def on_cancel_click(self, event: _Event) -> bool:    # dialog.nml:32
        """``cancel`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.message = Label(parent=self)    # dialog.nml:14
        self.ok = Button(parent=self)    # dialog.nml:23
        self.cancel = Button(parent=self)    # dialog.nml:31
        self.info = Button(parent=self)    # dialog.nml:39

        self.message.x = 1    # dialog.nml:16
        self.message.y = 1    # dialog.nml:17
        self.message.width = _bind(lambda _o: max(0, _o.parent.width - 2))    # dialog.nml:18
        self.message.height = 1    # dialog.nml:19
        self.message.text = _bind(lambda _o: _o.parent.prompt)    # dialog.nml:20
        self.message.align = 'left'    # dialog.nml:21

        self.ok.x = 1    # dialog.nml:25
        self.ok.y = 3    # dialog.nml:26
        self.ok.width = 10    # dialog.nml:27
        self.ok.height = 1    # dialog.nml:28
        self.ok.text = 'OK'    # dialog.nml:29
        self.ok.on_click = self.on_ok_click    # dialog.nml:24

        self.cancel.x = 12    # dialog.nml:33
        self.cancel.y = 3    # dialog.nml:34
        self.cancel.width = 10    # dialog.nml:35
        self.cancel.height = 1    # dialog.nml:36
        self.cancel.text = 'Cancel'    # dialog.nml:37
        self.cancel.on_click = self.on_cancel_click    # dialog.nml:32

        self.info.x = 23    # dialog.nml:41
        self.info.y = 3    # dialog.nml:42
        self.info.width = 10    # dialog.nml:43
        self.info.height = 1    # dialog.nml:44
        self.info.text = 'Help'    # dialog.nml:45

        async def _on_click(event):    # dialog.nml:46
            await self.show_info(event)
            return True
        self.info.on_click = _on_click

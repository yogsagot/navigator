# navml: generated
"""Generated from ``dialog.nml``.

Do not edit: edit the markup and rerun ``python -m navml build``.

(Written by hand until the parser and the code generator exist, as a stand-in
for what they will emit.)
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
from navml.widgets.button import Button  # dialog.nml:1
from navml.widgets.label import Label  # dialog.nml:2

__navml_component__ = "Dialog"

__all__ = ["Dialog"]


class Dialog(_Component):
    """A prompt with three buttons, and the worked example of a component
    whose *children* raise the events its hand-written half handles.

    Two of the buttons are handled by the ``on_<id>_<event>`` convention --
    see *Which child it was is a question the generator answers* in
    navml/DESIGN.md -- and the third by an explicit markup line, which is the
    escape hatch for a handler named after what the component does rather than
    after what happened.
    """

    #: The document this class was generated from.
    __navml_source__ = "dialog.nml"

    prompt: str = _reactive("")                                  # dialog.nml:5

    #: Ids, annotated so the hand-written half completes them.
    message: Label
    ok: Button
    cancel: Button
    info: Button

    # One stub per (id, emitted event), each wired in ``__init__`` below.
    # They return False, so a component that overrides neither is exactly a
    # component that never mentioned them: the click carries on up to whatever
    # the document's own ``on_click`` does with it.  The hand-written half is
    # the *derived* class, so its override wins over the stub without either
    # half naming the other.

    async def on_ok_click(self, event: _Event) -> bool:         # dialog.nml:17
        """``ok`` raised an event whose handler is ``on_click``."""
        return False

    async def on_cancel_click(self, event: _Event) -> bool:     # dialog.nml:25
        """``cancel`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.message = Label(parent=self)                        # dialog.nml:7
        self.message.x = 1                                       # dialog.nml:9
        self.message.y = 1                                      # dialog.nml:10
        self.message.width = _bind(                             # dialog.nml:11
            lambda _o: max(0, _o.parent.width - 2)
        )
        self.message.height = 1                                 # dialog.nml:12
        self.message.text = _bind(                              # dialog.nml:13
            lambda _o: _o.parent.prompt
        )
        self.message.align = "left"                             # dialog.nml:14

        self.ok = Button(parent=self)                           # dialog.nml:16
        self.ok.x = 1                                           # dialog.nml:18
        self.ok.y = 3                                           # dialog.nml:19
        self.ok.width = 10                                      # dialog.nml:20
        self.ok.height = 1                                      # dialog.nml:21
        self.ok.text = "OK"                                     # dialog.nml:22
        self.ok.on_click = self.on_ok_click                     # dialog.nml:17

        self.cancel = Button(parent=self)                       # dialog.nml:24
        self.cancel.x = 12                                      # dialog.nml:26
        self.cancel.y = 3                                       # dialog.nml:27
        self.cancel.width = 10                                  # dialog.nml:28
        self.cancel.height = 1                                  # dialog.nml:29
        self.cancel.text = "Cancel"                             # dialog.nml:30
        self.cancel.on_click = self.on_cancel_click             # dialog.nml:25

        self.info = Button(parent=self)                         # dialog.nml:32
        self.info.x = 23                                        # dialog.nml:34
        self.info.y = 3                                         # dialog.nml:35
        self.info.width = 10                                    # dialog.nml:36
        self.info.height = 1                                    # dialog.nml:37
        self.info.text = "Help"                                 # dialog.nml:38

        # An explicit handler line suppresses the convention: no
        # ``on_info_click`` stub exists and none is wired, because this
        # assignment would have overwritten it.
        async def _on_click(event):                             # dialog.nml:39
            await self.show_info(event)
            return True

        self.info.on_click = _on_click

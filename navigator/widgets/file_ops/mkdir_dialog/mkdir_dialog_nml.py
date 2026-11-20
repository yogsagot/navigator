# navml: generated
"""Generated from ``mkdir_dialog.nml``.

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
from navml.widgets.dialog.button import Button    # mkdir_dialog.nml:1
from navml.widgets.dialog.button_row import ButtonRow    # mkdir_dialog.nml:2
from navml.widgets.dialog.commands import Help    # mkdir_dialog.nml:3
from navml.widgets.dialog.dialog import Dialog    # mkdir_dialog.nml:4
from navml.widgets.dialog.field import Field    # mkdir_dialog.nml:5

__navml_component__ = "MkdirDialog"

__all__ = ["MkdirDialog"]


class MkdirDialog(Dialog, _Component):
    """F7: make a directory in the active panel.

    The smallest dialog Navigator actually wants, and the first one wired into
    the application -- an ``InputLine``, a ``Label`` that focuses it, ``dlgMkDir``'s
    OK, Cancel and Help, and an answer that ends in a directory on disk.

    The size is set by *assigning the properties the base binds from*, never by
    assigning ``width`` -- a value over a live binding raises, and the binding
    is installed by ``super().__init__()`` before this document's own lines run.
    """

    #: The document this class was generated from.
    __navml_source__ = "mkdir_dialog.nml"

    #: Ids, annotated so the hand-written half completes them.
    entry: Field    # mkdir_dialog.nml:31
    pick: Button    # mkdir_dialog.nml:51
    abandon: Button    # mkdir_dialog.nml:56
    helper: Button    # mkdir_dialog.nml:61

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_pick_click(self, event: _Event) -> bool:    # mkdir_dialog.nml:51
        """``pick`` raised an event whose handler is ``on_click``."""
        return False

    async def on_abandon_click(self, event: _Event) -> bool:    # mkdir_dialog.nml:56
        """``abandon`` raised an event whose handler is ``on_click``."""
        return False

    async def on_helper_click(self, event: _Event) -> bool:    # mkdir_dialog.nml:61
        """``helper`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.entry = Field(parent=self)    # mkdir_dialog.nml:28
        _w1 = ButtonRow(parent=self)    # mkdir_dialog.nml:44
        self.pick = Button(parent=_w1)    # mkdir_dialog.nml:50
        self.abandon = Button(parent=_w1)    # mkdir_dialog.nml:55
        self.helper = Button(parent=_w1)    # mkdir_dialog.nml:60

        self.help_topic = 'file-operations.md#make-a-directory'    # mkdir_dialog.nml:17
        self.modal_width = 52    # mkdir_dialog.nml:18
        self.modal_height = 8    # mkdir_dialog.nml:19
        self.title = _bind(lambda _o: _tr('Make directory'), yielding=True)    # mkdir_dialog.nml:20
        self.buttons = 'none'    # mkdir_dialog.nml:21
        self.buttons_row = _bind(    # mkdir_dialog.nml:23
            lambda _o: (self.pick, self.abandon, self.helper)
        )
        self.close_on_outside_click = True    # mkdir_dialog.nml:26

        self.entry.y = 2    # mkdir_dialog.nml:32
        self.entry.label_text = _bind(    # mkdir_dialog.nml:37
            lambda _o: _tr('~D~irectory name'),
            yielding=True,
        )
        self.entry.label_width = 21    # mkdir_dialog.nml:38
        self.entry.history_id = 'mkdir'    # mkdir_dialog.nml:41
        self.entry.x = 2    # mkdir_dialog.nml:34
        self.entry.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # mkdir_dialog.nml:35

        _w1.x = 0# mkdir_dialog.nml:46
        _w1.width = _bind(lambda _o: max(0, _o.parent.width))    # mkdir_dialog.nml:47
        _w1.y = _bind(lambda _o: max(0, _o.parent.height - 2 - _o.height))    # mkdir_dialog.nml:48

        self.pick.text = _bind(lambda _o: _tr('O~K~'), yielding=True)    # mkdir_dialog.nml:52
        self.pick.default = True    # mkdir_dialog.nml:53
        self.pick.on_click = self.on_pick_click    # mkdir_dialog.nml:51

        self.abandon.text = _bind(lambda _o: _tr('Cancel'), yielding=True)    # mkdir_dialog.nml:57
        self.abandon.on_click = self.on_abandon_click    # mkdir_dialog.nml:56

        self.helper.text = _bind(lambda _o: _tr('Help'), yielding=True)    # mkdir_dialog.nml:62
        self.helper.command = Help    # mkdir_dialog.nml:63
        self.helper.on_click = self.on_helper_click    # mkdir_dialog.nml:61

        self._navml_built(__class__)

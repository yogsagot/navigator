# navml: generated
"""Generated from ``goto_line_dialog.nml``.

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
from navml.widgets.dialog.button_row import ButtonRow    # goto_line_dialog.nml:1
from navml.widgets.dialog.button import Button    # goto_line_dialog.nml:2
from navml.widgets.dialog.commands import Help    # goto_line_dialog.nml:3
from navml.widgets.dialog.dialog import Dialog    # goto_line_dialog.nml:4
from navml.widgets.dialog.field import Field    # goto_line_dialog.nml:5

__navml_component__ = "GotoLineDialog"

__all__ = ["GotoLineDialog"]


class GotoLineDialog(Dialog, _Component):
    """Alt+G in the editor: DOS Navigator's ``dlgGotoLine``, *Goto Line*.

    The label at column 3, the line from 16 to 28 and its history after it, as
    the resource has them.  A row taller than DN's 34 by 7, for the blank row
    the viewer's *Goto Address* keeps between line and buttons.
    OK, Cancel and Help ten wide and touching from column 2, the resource's own
    row: this library's three would pass the frame.
    """

    #: The document this class was generated from.
    __navml_source__ = "goto_line_dialog.nml"

    #: Ids, annotated so the hand-written half completes them.
    number: Field    # goto_line_dialog.nml:24
    pick: Button    # goto_line_dialog.nml:43
    abandon: Button    # goto_line_dialog.nml:48
    helper: Button    # goto_line_dialog.nml:53

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_pick_click(self, event: _Event) -> bool:    # goto_line_dialog.nml:43
        """``pick`` raised an event whose handler is ``on_click``."""
        return False

    async def on_abandon_click(self, event: _Event) -> bool:    # goto_line_dialog.nml:48
        """``abandon`` raised an event whose handler is ``on_click``."""
        return False

    async def on_helper_click(self, event: _Event) -> bool:    # goto_line_dialog.nml:53
        """``helper`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.number = Field(parent=self)    # goto_line_dialog.nml:23
        _w1 = ButtonRow(parent=self)    # goto_line_dialog.nml:33
        self.pick = Button(parent=_w1)    # goto_line_dialog.nml:42
        self.abandon = Button(parent=_w1)    # goto_line_dialog.nml:47
        self.helper = Button(parent=_w1)    # goto_line_dialog.nml:52

        self.modal_width = 34    # goto_line_dialog.nml:15
        self.modal_height = 8    # goto_line_dialog.nml:16
        self.title = _bind(lambda _o: _tr('Goto Line'), yielding=True)    # goto_line_dialog.nml:17
        self.help_topic = 'editor.md#go-to-a-line'    # goto_line_dialog.nml:18
        self.buttons = 'none'    # goto_line_dialog.nml:19
        self.buttons_row = _bind(    # goto_line_dialog.nml:21
            lambda _o: (self.pick, self.abandon, self.helper)
        )

        self.number.y = 2    # goto_line_dialog.nml:25
        self.number.label_text = _bind(    # goto_line_dialog.nml:29
            lambda _o: _tr('~L~ine number'),
            yielding=True,
        )
        self.number.label_width = 13    # goto_line_dialog.nml:30
        self.number.history_id = 'goto_line'    # goto_line_dialog.nml:31
        self.number.x = 3    # goto_line_dialog.nml:27
        self.number.width = _bind(lambda _o: max(0, _o.parent.width - 6))    # goto_line_dialog.nml:28

        _w1.justify = 'start'    # goto_line_dialog.nml:34
        _w1.button_width = 10    # goto_line_dialog.nml:35
        _w1.spacing = 0    # goto_line_dialog.nml:36
        _w1.x = 2# goto_line_dialog.nml:38
        _w1.width = _bind(lambda _o: max(0, _o.parent.width - 2))    # goto_line_dialog.nml:39
        _w1.y = _bind(lambda _o: max(0, _o.parent.height - 2 - _o.height))    # goto_line_dialog.nml:40

        self.pick.text = _bind(lambda _o: _tr('O~K~'), yielding=True)    # goto_line_dialog.nml:44
        self.pick.default = True    # goto_line_dialog.nml:45
        self.pick.on_click = self.on_pick_click    # goto_line_dialog.nml:43

        self.abandon.text = _bind(lambda _o: _tr('Cancel'), yielding=True)    # goto_line_dialog.nml:49
        self.abandon.on_click = self.on_abandon_click    # goto_line_dialog.nml:48

        self.helper.text = _bind(lambda _o: _tr('Help'), yielding=True)    # goto_line_dialog.nml:54
        self.helper.command = Help    # goto_line_dialog.nml:55
        self.helper.on_click = self.on_helper_click    # goto_line_dialog.nml:53

        self._navml_built(__class__)

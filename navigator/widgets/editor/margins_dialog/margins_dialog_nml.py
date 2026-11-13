# navml: generated
"""Generated from ``margins_dialog.nml``.

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
from navml.widgets.dialog.button import Button    # margins_dialog.nml:1
from navml.widgets.dialog.button_row import ButtonRow    # margins_dialog.nml:2
from navml.widgets.dialog.commands import Help    # margins_dialog.nml:3
from navml.widgets.dialog.dialog import Dialog    # margins_dialog.nml:4
from navml.widgets.dialog.field import Field    # margins_dialog.nml:5

__navml_component__ = "MarginsDialog"

__all__ = ["MarginsDialog"]


class MarginsDialog(Dialog, _Component):
    """Editor > Paragraph > *Margins...*: DOS Navigator's ``dlgEditorFormat``,

    *Format Margins*, 39 by 11 -- three lines from column 20 with their labels
    at 2, and OK, Cancel and Help along row 8, the resource's every rectangle.
    """

    #: The document this class was generated from.
    __navml_source__ = "margins_dialog.nml"

    #: Ids, annotated so the hand-written half completes them.
    left: Field    # margins_dialog.nml:20
    right: Field    # margins_dialog.nml:28
    indent: Field    # margins_dialog.nml:36
    pick: Button    # margins_dialog.nml:53
    abandon: Button    # margins_dialog.nml:59
    helper: Button    # margins_dialog.nml:64

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_abandon_click(self, event: _Event) -> bool:    # margins_dialog.nml:59
        """``abandon`` raised an event whose handler is ``on_click``."""
        return False

    async def on_helper_click(self, event: _Event) -> bool:    # margins_dialog.nml:64
        """``helper`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.left = Field(parent=self)    # margins_dialog.nml:19
        self.right = Field(parent=self)    # margins_dialog.nml:27
        self.indent = Field(parent=self)    # margins_dialog.nml:35
        _w1 = ButtonRow(parent=self)    # margins_dialog.nml:43
        self.pick = Button(parent=_w1)    # margins_dialog.nml:52
        self.abandon = Button(parent=_w1)    # margins_dialog.nml:58
        self.helper = Button(parent=_w1)    # margins_dialog.nml:63

        self.modal_width = 39    # margins_dialog.nml:11
        self.modal_height = 11    # margins_dialog.nml:12
        self.title = _bind(lambda _o: _tr('Format Margins'), yielding=True)    # margins_dialog.nml:13
        self.help_topic = 'editor.md#margins'    # margins_dialog.nml:14
        self.buttons = 'none'    # margins_dialog.nml:15
        self.buttons_row = _bind(    # margins_dialog.nml:17
            lambda _o: (self.pick, self.abandon, self.helper)
        )

        self.left.x = 2    # margins_dialog.nml:21
        self.left.y = 2    # margins_dialog.nml:22
        self.left.width = 35    # margins_dialog.nml:23
        self.left.label_text = _bind(    # margins_dialog.nml:24
            lambda _o: _tr('~L~eft margin'),
            yielding=True,
        )
        self.left.label_width = 18    # margins_dialog.nml:25

        self.right.x = 2    # margins_dialog.nml:29
        self.right.y = 4    # margins_dialog.nml:30
        self.right.width = 35    # margins_dialog.nml:31
        self.right.label_text = _bind(    # margins_dialog.nml:32
            lambda _o: _tr('~R~ight margin'),
            yielding=True,
        )
        self.right.label_width = 18    # margins_dialog.nml:33

        self.indent.x = 2    # margins_dialog.nml:37
        self.indent.y = 6    # margins_dialog.nml:38
        self.indent.width = 35    # margins_dialog.nml:39
        self.indent.label_text = _bind(    # margins_dialog.nml:40
            lambda _o: _tr('~P~aragraph'),
            yielding=True,
        )
        self.indent.label_width = 18    # margins_dialog.nml:41

        _w1.justify = 'start'    # margins_dialog.nml:44
        _w1.button_width = 10    # margins_dialog.nml:45
        _w1.spacing = 0    # margins_dialog.nml:46
        _w1.y = 8# margins_dialog.nml:47
        _w1.x = 7# margins_dialog.nml:49
        _w1.width = _bind(lambda _o: max(0, _o.parent.width - 7))    # margins_dialog.nml:50

        self.pick.text = _bind(lambda _o: _tr('O~K~'), yielding=True)    # margins_dialog.nml:54
        self.pick.default = True    # margins_dialog.nml:55

        async def _on_click(event):    # margins_dialog.nml:56
            self.close(self.accept())
            return True
        self.pick.on_click = _on_click

        self.abandon.text = _bind(lambda _o: _tr('Cancel'), yielding=True)    # margins_dialog.nml:60
        self.abandon.on_click = self.on_abandon_click    # margins_dialog.nml:59

        self.helper.text = _bind(lambda _o: _tr('Help'), yielding=True)    # margins_dialog.nml:65
        self.helper.command = Help    # margins_dialog.nml:66
        self.helper.on_click = self.on_helper_click    # margins_dialog.nml:64

        self._navml_built(__class__)

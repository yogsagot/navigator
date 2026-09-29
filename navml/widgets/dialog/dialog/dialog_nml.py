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
from navml.commands import Cancel, Default, SelectNext, SelectPrevious    # dialog.nml:1
from navml.widgets.dialog.button import Button    # dialog.nml:2
from navml.widgets.layout.horizontal_layout import HorizontalLayout    # dialog.nml:3
from navml.widgets.dialog.static_text import StaticText    # dialog.nml:4
from navml.widgets.dialog.modal import Modal    # dialog.nml:5

__navml_component__ = "Dialog"

__all__ = ["Dialog"]


class Dialog(Modal, _Component):
    """A modal window with an OK and a Cancel, and an answer.

    Still the worked example of a component whose *children* raise the events
    its hand-written half handles -- a dialog with two buttons in it is what
    the ``on_<id>_<event>`` convention was written for, and it is now a widget
    that earns the example rather than a demonstration built to carry it.

    Its size and its place are :class:`~navml.widgets.dialog.modal.Modal`'s: a derived
    document says ``modal_width: 44``, and the centring is the base's binding.
    """

    #: The document this class was generated from.
    __navml_source__ = "dialog.nml"

    #: Turbo Vision's dialog keys.  Reached only once a key has passed the
    #: control that has the keyboard, so an input line that wants Enter or Tab
    #: for itself takes it first.
    keys = {    # dialog.nml:30
        'escape': Cancel,    # dialog.nml:31
        'enter': Default,    # dialog.nml:32
        'tab': SelectNext,    # dialog.nml:33
        'shift+tab': SelectPrevious,    # dialog.nml:34
    }

    #: ``ok``, ``ok-cancel``, ``ok-cancel-help`` or ``yes-no-cancel``
    #: (``mfYesNoCancel``, OK captioned *Yes*).  Which buttons is a
    #: *visibility* question, because markup has no conditional and needs
    #: none: all four are declared and a hidden one is already out of the
    #: tab order, out of the shortcut walk and out of the paint.
    buttons: str = _reactive('ok-cancel')    # dialog.nml:22

    #: The line of text above the buttons.
    prompt: str = _reactive('')    # dialog.nml:25

    #: Ids, annotated so the hand-written half completes them.
    message: StaticText    # dialog.nml:37
    row: HorizontalLayout    # dialog.nml:49
    ok: Button    # dialog.nml:58
    no: Button    # dialog.nml:67
    cancel: Button    # dialog.nml:75
    info: Button    # dialog.nml:88

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_ok_click(self, event: _Event) -> bool:    # dialog.nml:58
        """``ok`` raised an event whose handler is ``on_click``."""
        return False

    async def on_no_click(self, event: _Event) -> bool:    # dialog.nml:67
        """``no`` raised an event whose handler is ``on_click``."""
        return False

    async def on_cancel_click(self, event: _Event) -> bool:    # dialog.nml:75
        """``cancel`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.message = StaticText(parent=self)    # dialog.nml:36
        self.row = HorizontalLayout(parent=self)    # dialog.nml:48
        self.ok = Button(parent=self.row)    # dialog.nml:57
        self.no = Button(parent=self.row)    # dialog.nml:66
        self.cancel = Button(parent=self.row)    # dialog.nml:74
        self.info = Button(parent=self.row)    # dialog.nml:87

        self.message.x = 2    # dialog.nml:38
        self.message.y = 2    # dialog.nml:39
        self.message.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # dialog.nml:40
        self.message.height = _bind(lambda _o: max(1, _o.parent.height - 6))    # dialog.nml:41
        self.message.text = _bind(lambda _o: _o.parent.prompt)    # dialog.nml:42
        self.message.wrap = True    # dialog.nml:43

        self.row.x = 0    # dialog.nml:50
        self.row.y = _bind(lambda _o: max(0, _o.parent.height - 4))    # dialog.nml:51
        self.row.width = _bind(lambda _o: _o.parent.width)    # dialog.nml:52
        self.row.height = 2    # dialog.nml:53
        self.row.spacing = 2    # dialog.nml:54
        self.row.justify = 'center'    # dialog.nml:55

        self.ok.text = _bind(    # dialog.nml:59
            lambda _o: '~Y~es' if self.buttons == 'yes-no-cancel' else 'O~K~'
        )
        self.ok.default = True    # dialog.nml:60
        self.ok.inline_style = 'basis: 11; grow: 0'    # dialog.nml:61
        self.ok.on_click = self.on_ok_click    # dialog.nml:58

        self.no.text = '~N~o'    # dialog.nml:68
        self.no.visible = _bind(lambda _o: self.buttons == 'yes-no-cancel')    # dialog.nml:69
        self.no.inline_style = 'basis: 11; grow: 0'    # dialog.nml:70
        self.no.on_click = self.on_no_click    # dialog.nml:67

        self.cancel.text = '~C~ancel'    # dialog.nml:76
        self.cancel.visible = _bind(lambda _o: self.buttons != 'ok')    # dialog.nml:77
        self.cancel.inline_style = 'basis: 11; grow: 0'    # dialog.nml:78
        self.cancel.on_click = self.on_cancel_click    # dialog.nml:75

        self.info.text = '~H~elp'    # dialog.nml:89
        self.info.visible = _bind(lambda _o: self.buttons == 'ok-cancel-help')    # dialog.nml:90
        self.info.inline_style = 'basis: 11; grow: 0'    # dialog.nml:91

        async def _on_click(event):    # dialog.nml:94
            await self.show_info(event)
            return True
        self.info.on_click = _on_click

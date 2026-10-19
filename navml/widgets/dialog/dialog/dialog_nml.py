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
from navkit.i18n import tr as _tr
from navkit.reactive import bind as _bind
from navkit.reactive import reactive as _reactive

from navml.component import Component as _Component
from navml.widgets.dialog.commands import Cancel, Default, SelectNext, SelectPrevious    # dialog.nml:1
from navml.widgets.dialog.button import Button    # dialog.nml:2
from navml.widgets.layout.horizontal_layout import HorizontalLayout    # dialog.nml:3
from navml.widgets.dialog.static_text import StaticText    # dialog.nml:4
from navml.widgets.dialog.modal import Modal    # dialog.nml:5
from navml.widgets.menu.commands import ShowContextMenu    # dialog.nml:6

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
    keys = {    # dialog.nml:38
        'escape': Cancel,    # dialog.nml:39
        'enter': Default,    # dialog.nml:40
        'tab': SelectNext,    # dialog.nml:41
        'shift+tab': SelectPrevious,    # dialog.nml:42
        'menu': ShowContextMenu,    # dialog.nml:45
        'shift+f10': ShowContextMenu,    # dialog.nml:46
    }

    #: ``ok``, ``ok-cancel``, ``ok-cancel-help``, ``yes-no-cancel``
    #: (``mfYesNoCancel``, OK captioned *Yes*) or ``yes-no`` (``mfYesButton +
    #: mfNoButton``, the same without Cancel; Esc still answers ``None``).  Which buttons is a
    #: *visibility* question, because markup has no conditional and needs
    #: none: all four are declared and a hidden one is already out of the
    #: tab order, out of the shortcut walk and out of the paint.
    buttons: str = _reactive('ok-cancel')    # dialog.nml:24

    #: The line of text above the buttons.
    prompt: str = _reactive('')    # dialog.nml:27

    #: Whether a click outside the dialog cancels it, as Esc does.  Off,
    #: because a dialog usually holds the user's work and a stray click must
    #: not cost it; a small one that is opened from another dialog -- and is
    #: cheap to open again -- says yes in its own document.
    close_on_outside_click: bool = _reactive(False)    # dialog.nml:33

    #: Ids, annotated so the hand-written half completes them.
    message: StaticText    # dialog.nml:49
    row: HorizontalLayout    # dialog.nml:61
    ok: Button    # dialog.nml:70
    no: Button    # dialog.nml:79
    cancel: Button    # dialog.nml:87
    info: Button    # dialog.nml:100

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_ok_click(self, event: _Event) -> bool:    # dialog.nml:70
        """``ok`` raised an event whose handler is ``on_click``."""
        return False

    async def on_no_click(self, event: _Event) -> bool:    # dialog.nml:79
        """``no`` raised an event whose handler is ``on_click``."""
        return False

    async def on_cancel_click(self, event: _Event) -> bool:    # dialog.nml:87
        """``cancel`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.message = StaticText(parent=self)    # dialog.nml:48
        self.row = HorizontalLayout(parent=self)    # dialog.nml:60
        self.ok = Button(parent=self.row)    # dialog.nml:69
        self.no = Button(parent=self.row)    # dialog.nml:78
        self.cancel = Button(parent=self.row)    # dialog.nml:86
        self.info = Button(parent=self.row)    # dialog.nml:99

        self.message.x = 2    # dialog.nml:50
        self.message.y = 2    # dialog.nml:51
        self.message.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # dialog.nml:52
        self.message.height = _bind(lambda _o: max(1, _o.parent.height - 6))    # dialog.nml:53
        self.message.text = _bind(lambda _o: _o.parent.prompt)    # dialog.nml:54
        self.message.wrap = True    # dialog.nml:55

        self.row.x = 0    # dialog.nml:62
        self.row.y = _bind(lambda _o: max(0, _o.parent.height - 4))    # dialog.nml:63
        self.row.width = _bind(lambda _o: _o.parent.width)    # dialog.nml:64
        self.row.height = 2    # dialog.nml:65
        self.row.spacing = 2    # dialog.nml:66
        self.row.justify = 'center'    # dialog.nml:67

        self.ok.text = _bind(    # dialog.nml:71
            lambda _o: _tr('~Y~es') if self.buttons in ('yes-no-cancel', 'yes-no') else _tr('O~K~'),
            yielding=True,
        )
        self.ok.default = True    # dialog.nml:72
        self.ok.inline_style = 'basis: 11; grow: 0'    # dialog.nml:73
        self.ok.on_click = self.on_ok_click    # dialog.nml:70

        self.no.text = _bind(lambda _o: _tr('~N~o'), yielding=True)    # dialog.nml:80
        self.no.visible = _bind(    # dialog.nml:81
            lambda _o: self.buttons in ('yes-no-cancel', 'yes-no')
        )
        self.no.inline_style = 'basis: 11; grow: 0'    # dialog.nml:82
        self.no.on_click = self.on_no_click    # dialog.nml:79

        self.cancel.text = _bind(lambda _o: _tr('~C~ancel'), yielding=True)    # dialog.nml:88
        self.cancel.visible = _bind(    # dialog.nml:89
            lambda _o: self.buttons not in ('ok', 'yes-no')
        )
        self.cancel.inline_style = 'basis: 11; grow: 0'    # dialog.nml:90
        self.cancel.on_click = self.on_cancel_click    # dialog.nml:87

        self.info.text = _bind(lambda _o: _tr('~H~elp'), yielding=True)    # dialog.nml:101
        self.info.visible = _bind(lambda _o: self.buttons == 'ok-cancel-help')    # dialog.nml:102
        self.info.inline_style = 'basis: 11; grow: 0'    # dialog.nml:103

        async def _on_click(event):    # dialog.nml:106
            await self.show_info(event)
            return True
        self.info.on_click = _on_click

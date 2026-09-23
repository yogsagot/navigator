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
from navml.widgets.static_text import StaticText    # dialog.nml:2
from navml.widgets.modal import Modal    # dialog.nml:3

__navml_component__ = "Dialog"

__all__ = ["Dialog"]


class Dialog(Modal, _Component):
    """A modal window with an OK and a Cancel, and an answer.

    Still the worked example of a component whose *children* raise the events
    its hand-written half handles -- a dialog with two buttons in it is what
    the ``on_<id>_<event>`` convention was written for, and it is now a widget
    that earns the example rather than a demonstration built to carry it.

    Its size and its place are :class:`~navml.widgets.modal.Modal`'s: a derived
    document says ``modal_width: 44``, and the centring is the base's binding.
    """

    #: The document this class was generated from.
    __navml_source__ = "dialog.nml"

    #: ``ok``, ``ok-cancel`` or ``ok-cancel-help``.  Which buttons is a
    #: *visibility* question, because markup has no conditional and needs
    #: none: all three are declared and a hidden one is already out of the
    #: tab order, out of the shortcut walk and out of the paint.
    buttons: str = _reactive('ok-cancel')    # dialog.nml:19

    #: The line of text above the buttons.
    prompt: str = _reactive('')    # dialog.nml:22

    #: Where the row of buttons starts, so that it stays centred whether two
    #: of them are showing or three.  A *conditional expression* rather than a
    #: conditional: markup has no branch and needs none here, because what
    #: varies is a value and not the shape of the tree.  Each button is 11
    #: columns -- nine of face, two of bracket, one of shadow -- with two
    #: between, so three span 37 and two span 24.
    button_row = _reactive()    # dialog.nml:30

    #: Ids, annotated so the hand-written half completes them.
    message: StaticText    # dialog.nml:33
    ok: Button    # dialog.nml:42
    cancel: Button    # dialog.nml:51
    info: Button    # dialog.nml:64

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_ok_click(self, event: _Event) -> bool:    # dialog.nml:42
        """``ok`` raised an event whose handler is ``on_click``."""
        return False

    async def on_cancel_click(self, event: _Event) -> bool:    # dialog.nml:51
        """``cancel`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.message = StaticText(parent=self)    # dialog.nml:32
        self.ok = Button(parent=self)    # dialog.nml:41
        self.cancel = Button(parent=self)    # dialog.nml:50
        self.info = Button(parent=self)    # dialog.nml:63

        self.button_row = _bind(lambda _o: (_o.width - 37) // 2 if _o.buttons == 'ok-cancel-help' else (_o.width - 24) // 2)    # dialog.nml:30

        self.message.x = 2    # dialog.nml:34
        self.message.y = 2    # dialog.nml:35
        self.message.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # dialog.nml:36
        self.message.height = _bind(lambda _o: max(1, _o.parent.height - 6))    # dialog.nml:37
        self.message.text = _bind(lambda _o: _o.parent.prompt)    # dialog.nml:38
        self.message.wrap = True    # dialog.nml:39

        self.ok.text = 'O~K~'    # dialog.nml:43
        self.ok.default = True    # dialog.nml:44
        self.ok.x = _bind(lambda _o: max(1, _o.parent.button_row))    # dialog.nml:45
        self.ok.y = _bind(lambda _o: max(0, _o.parent.height - 4))    # dialog.nml:46
        self.ok.width = 11    # dialog.nml:47
        self.ok.height = 2    # dialog.nml:48
        self.ok.on_click = self.on_ok_click    # dialog.nml:42

        self.cancel.text = '~C~ancel'    # dialog.nml:52
        self.cancel.visible = _bind(lambda _o: _o.parent.buttons != 'ok')    # dialog.nml:53
        self.cancel.x = _bind(lambda _o: max(1, _o.parent.button_row + 13))    # dialog.nml:54
        self.cancel.width = 11    # dialog.nml:55
        self.cancel.height = 2    # dialog.nml:56
        self.cancel.y = _bind(lambda _o: max(0, _o.parent.height - 4))    # dialog.nml:57
        self.cancel.on_click = self.on_cancel_click    # dialog.nml:51

        self.info.text = '~H~elp'    # dialog.nml:65
        self.info.visible = _bind(    # dialog.nml:66
            lambda _o: _o.parent.buttons == 'ok-cancel-help'
        )
        self.info.x = _bind(lambda _o: max(1, _o.parent.button_row + 26))    # dialog.nml:67
        self.info.width = 11    # dialog.nml:68
        self.info.height = 2    # dialog.nml:69
        self.info.y = _bind(lambda _o: max(0, _o.parent.height - 4))    # dialog.nml:70

        async def _on_click(event):    # dialog.nml:71
            await self.show_info(event)
            return True
        self.info.on_click = _on_click

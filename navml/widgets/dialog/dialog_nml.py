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
from navml.widgets.window import Window    # dialog.nml:3

__navml_component__ = "Dialog"

__all__ = ["Dialog"]


class Dialog(Window, _Component):
    """A modal window with an OK and a Cancel, and an answer.

    Still the worked example of a component whose *children* raise the events
    its hand-written half handles -- a dialog with two buttons in it is what
    the ``on_<id>_<event>`` convention was written for, and it is now a widget
    that earns the example rather than a demonstration built to carry it.

    **The geometry is bound, and that is not a style choice.**  ``Widget.add``
    lays a child out into its parent's size, and ``Component.layout`` only
    steps around a side that carries a *binding* -- so a dialog whose width is
    a literal is resized to the whole terminal the moment it is overlaid.
    Routing the size through a declared property is also what lets a derived
    dialog change it: ``dialog_width: 44`` is a literal onto an attribute
    nothing has bound, where ``width: 44`` would be a value over a live binding
    and would raise.
    """

    #: The document this class was generated from.
    __navml_source__ = "dialog.nml"

    #: The size the dialog asks for.  Overridden by a derived document.
    dialog_width: int = _reactive(50)    # dialog.nml:22
    dialog_height: int = _reactive(10)    # dialog.nml:23

    #: ``ok``, ``ok-cancel`` or ``ok-cancel-help``.  Which buttons is a
    #: *visibility* question, because markup has no conditional and needs
    #: none: all three are declared and a hidden one is already out of the
    #: tab order, out of the shortcut walk and out of the paint.
    buttons: str = _reactive('ok-cancel')    # dialog.nml:29

    #: The line of text above the buttons.
    prompt: str = _reactive('')    # dialog.nml:32

    #: Where the row of buttons starts, so that it stays centred whether two
    #: of them are showing or three.  A *conditional expression* rather than a
    #: conditional: markup has no branch and needs none here, because what
    #: varies is a value and not the shape of the tree.  Each button is 11
    #: columns -- nine of face, two of bracket, one of shadow -- with two
    #: between, so three span 37 and two span 24.
    button_row = _reactive()    # dialog.nml:40

    #: Ids, annotated so the hand-written half completes them.
    message: StaticText    # dialog.nml:48
    ok: Button    # dialog.nml:57
    cancel: Button    # dialog.nml:66
    info: Button    # dialog.nml:79

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_ok_click(self, event: _Event) -> bool:    # dialog.nml:57
        """``ok`` raised an event whose handler is ``on_click``."""
        return False

    async def on_cancel_click(self, event: _Event) -> bool:    # dialog.nml:66
        """``cancel`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.message = StaticText(parent=self)    # dialog.nml:47
        self.ok = Button(parent=self)    # dialog.nml:56
        self.cancel = Button(parent=self)    # dialog.nml:65
        self.info = Button(parent=self)    # dialog.nml:78

        self.button_row = _bind(lambda _o: (_o.width - 37) // 2 if _o.buttons == 'ok-cancel-help' else (_o.width - 24) // 2)    # dialog.nml:40
        self.width = _bind(lambda _o: _o.dialog_width)    # dialog.nml:42
        self.height = _bind(lambda _o: _o.dialog_height)    # dialog.nml:43
        self.x = _bind(lambda _o: max(0, (_o.parent.width - _o.width) // 2))    # dialog.nml:44
        self.y = _bind(lambda _o: max(0, (_o.parent.height - _o.height) // 2))    # dialog.nml:45

        self.message.x = 2    # dialog.nml:49
        self.message.y = 2    # dialog.nml:50
        self.message.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # dialog.nml:51
        self.message.height = _bind(lambda _o: max(1, _o.parent.height - 6))    # dialog.nml:52
        self.message.text = _bind(lambda _o: _o.parent.prompt)    # dialog.nml:53
        self.message.wrap = True    # dialog.nml:54

        self.ok.text = 'O~K~'    # dialog.nml:58
        self.ok.default = True    # dialog.nml:59
        self.ok.x = _bind(lambda _o: max(1, _o.parent.button_row))    # dialog.nml:60
        self.ok.y = _bind(lambda _o: max(0, _o.parent.height - 4))    # dialog.nml:61
        self.ok.width = 11    # dialog.nml:62
        self.ok.height = 2    # dialog.nml:63
        self.ok.on_click = self.on_ok_click    # dialog.nml:57

        self.cancel.text = '~C~ancel'    # dialog.nml:67
        self.cancel.visible = _bind(lambda _o: _o.parent.buttons != 'ok')    # dialog.nml:68
        self.cancel.x = _bind(lambda _o: max(1, _o.parent.button_row + 13))    # dialog.nml:69
        self.cancel.width = 11    # dialog.nml:70
        self.cancel.height = 2    # dialog.nml:71
        self.cancel.y = _bind(lambda _o: max(0, _o.parent.height - 4))    # dialog.nml:72
        self.cancel.on_click = self.on_cancel_click    # dialog.nml:66

        self.info.text = '~H~elp'    # dialog.nml:80
        self.info.visible = _bind(    # dialog.nml:81
            lambda _o: _o.parent.buttons == 'ok-cancel-help'
        )
        self.info.x = _bind(lambda _o: max(1, _o.parent.button_row + 26))    # dialog.nml:82
        self.info.width = 11    # dialog.nml:83
        self.info.height = 2    # dialog.nml:84
        self.info.y = _bind(lambda _o: max(0, _o.parent.height - 4))    # dialog.nml:85

        async def _on_click(event):    # dialog.nml:86
            await self.show_info(event)
            return True
        self.info.on_click = _on_click

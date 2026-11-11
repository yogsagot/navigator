# navml: generated
"""Generated from ``error_dialog.nml``.

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
from navml.widgets.dialog.button import Button    # error_dialog.nml:1
from navml.widgets.dialog.button_row import ButtonRow    # error_dialog.nml:2
from navml.widgets.dialog.dialog import Dialog    # error_dialog.nml:3
from navml.widgets.dialog.static_text import StaticText    # error_dialog.nml:4
from navigator.widgets.shell.error_dialog.trace_list import TraceList    # error_dialog.nml:5

__navml_component__ = "ErrorDialog"

__all__ = ["ErrorDialog"]


class ErrorDialog(Dialog, _Component):
    """An exception escaped Navigator's code: what it was, and where.

    Not DOS Navigator's -- a failure there was Turbo Pascal's ``Runtime error
    NNN at XXXX:YYYY`` and the end of the program.  Options > Configuration >
    System Setup's *On error* picks this box or that ending (the traceback
    printed once the terminal is given back); a failure is never silent either
    way, and is appended to ``errors.log`` as well.  *Continue* carries on,
    *Copy* puts the whole traceback on the clipboard, *Quit* ends Navigator
    printing it.
    """

    #: The document this class was generated from.
    __navml_source__ = "error_dialog.nml"

    #: Ids, annotated so the hand-written half completes them.
    summary: StaticText    # error_dialog.nml:24
    trace: TraceList    # error_dialog.nml:37
    logged: StaticText    # error_dialog.nml:45
    resume: Button    # error_dialog.nml:63
    copy: Button    # error_dialog.nml:68
    quit: Button    # error_dialog.nml:72

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_resume_click(self, event: _Event) -> bool:    # error_dialog.nml:63
        """``resume`` raised an event whose handler is ``on_click``."""
        return False

    async def on_copy_click(self, event: _Event) -> bool:    # error_dialog.nml:68
        """``copy`` raised an event whose handler is ``on_click``."""
        return False

    async def on_quit_click(self, event: _Event) -> bool:    # error_dialog.nml:72
        """``quit`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.summary = StaticText(parent=self)    # error_dialog.nml:23
        self.trace = TraceList(parent=self)    # error_dialog.nml:36
        self.logged = StaticText(parent=self)    # error_dialog.nml:44
        _w1 = ButtonRow(parent=self)    # error_dialog.nml:54
        self.resume = Button(parent=_w1)    # error_dialog.nml:62
        self.copy = Button(parent=_w1)    # error_dialog.nml:67
        self.quit = Button(parent=_w1)    # error_dialog.nml:71

        self.modal_width = _bind(    # error_dialog.nml:19
            lambda _o: max(60, _o.parent.width - 4) if _o.parent is not None else 76
        )
        self.modal_height = _bind(    # error_dialog.nml:20
            lambda _o: max(16, _o.parent.height - 2) if _o.parent is not None else 20
        )
        self.title = _bind(lambda _o: _tr('Error'), yielding=True)    # error_dialog.nml:21

        self.summary.name = 'summary'    # error_dialog.nml:25
        self.summary.y = 1    # error_dialog.nml:26
        self.summary.height = 2    # error_dialog.nml:27
        self.summary.wrap = True    # error_dialog.nml:31
        self.summary.x = 2    # error_dialog.nml:29
        self.summary.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # error_dialog.nml:30

        self.trace.y = 3    # error_dialog.nml:38
        self.trace.height = _bind(lambda _o: max(1, _o.parent.height - 9))    # error_dialog.nml:39
        self.trace.x = 2    # error_dialog.nml:41
        self.trace.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # error_dialog.nml:42

        self.logged.name = 'logged'    # error_dialog.nml:46
        self.logged.height = 1    # error_dialog.nml:47
        self.logged.x = 2    # error_dialog.nml:49
        self.logged.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # error_dialog.nml:50
        self.logged.y = _bind(    # error_dialog.nml:51
            lambda _o: max(0, _o.parent.height - 5 - _o.height)
        )

        _w1.button_width = 14    # error_dialog.nml:55
        _w1.spacing = 1    # error_dialog.nml:56
        _w1.x = 0# error_dialog.nml:58
        _w1.width = _bind(lambda _o: max(0, _o.parent.width))    # error_dialog.nml:59
        _w1.y = _bind(lambda _o: max(0, _o.parent.height - 2 - _o.height))    # error_dialog.nml:60

        self.resume.text = _bind(lambda _o: _tr('~C~ontinue'), yielding=True)    # error_dialog.nml:64
        self.resume.default = True    # error_dialog.nml:65
        self.resume.on_click = self.on_resume_click    # error_dialog.nml:63

        self.copy.text = _bind(lambda _o: _tr('C~o~py'), yielding=True)    # error_dialog.nml:69
        self.copy.on_click = self.on_copy_click    # error_dialog.nml:68

        self.quit.text = _bind(lambda _o: _tr('~Q~uit'), yielding=True)    # error_dialog.nml:73
        self.quit.on_click = self.on_quit_click    # error_dialog.nml:72

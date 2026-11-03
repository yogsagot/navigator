# navml: generated
"""Generated from ``replace_query.nml``.

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
from navml.widgets.dialog.button import Button    # replace_query.nml:1
from navml.widgets.dialog.dialog import Dialog    # replace_query.nml:2
from navml.widgets.dialog.static_text import StaticText    # replace_query.nml:3
from navigator.widgets.file_ops.replace_query.change_list import ChangeList    # replace_query.nml:4

__navml_component__ = "ReplaceQuery"

__all__ = ["ReplaceQuery"]


class ReplaceQuery(Dialog, _Component):
    """File > Replace in files, a file holding the text: replace in it?

    Not DN's -- a departure, asked for (``navigator.lib.file_ops.filereplace``):
    the file's name and how many replacements over every line they change,
    each as it is over what it will be, and buttons asked as ``dlgOverwriteQuery``
    and ``dlEraseRO`` asked theirs -- *Yes*, *All* the files after it too,
    *Skip*, *Cancel* the whole replace.  As wide and tall as the screen lets,
    up to 76 by 22, so the lines show as much as they can.
    """

    #: The document this class was generated from.
    __navml_source__ = "replace_query.nml"

    #: Ids, annotated so the hand-written half completes them.
    details: StaticText    # replace_query.nml:20
    changes: ChangeList    # replace_query.nml:28
    agree: Button    # replace_query.nml:35
    every: Button    # replace_query.nml:44
    skip: Button    # replace_query.nml:52
    abandon: Button    # replace_query.nml:60

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_agree_click(self, event: _Event) -> bool:    # replace_query.nml:35
        """``agree`` raised an event whose handler is ``on_click``."""
        return False

    async def on_every_click(self, event: _Event) -> bool:    # replace_query.nml:44
        """``every`` raised an event whose handler is ``on_click``."""
        return False

    async def on_skip_click(self, event: _Event) -> bool:    # replace_query.nml:52
        """``skip`` raised an event whose handler is ``on_click``."""
        return False

    async def on_abandon_click(self, event: _Event) -> bool:    # replace_query.nml:60
        """``abandon`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.details = StaticText(parent=self)    # replace_query.nml:19
        self.changes = ChangeList(parent=self)    # replace_query.nml:27
        self.agree = Button(parent=self)    # replace_query.nml:34
        self.every = Button(parent=self)    # replace_query.nml:43
        self.skip = Button(parent=self)    # replace_query.nml:51
        self.abandon = Button(parent=self)    # replace_query.nml:59

        self.modal_width = _bind(    # replace_query.nml:15
            lambda _o: max(40, min(76, _o.parent.width - 4)) if _o.parent is not None else 76
        )
        self.modal_height = _bind(    # replace_query.nml:16
            lambda _o: max(12, min(22, _o.parent.height - 2)) if _o.parent is not None else 22
        )
        self.title = _bind(lambda _o: _tr('Replace'), yielding=True)    # replace_query.nml:17

        self.details.x = 1    # replace_query.nml:21
        self.details.y = 1    # replace_query.nml:22
        self.details.width = _bind(lambda _o: max(0, _o.parent.width - 2))    # replace_query.nml:23
        self.details.height = 2    # replace_query.nml:24
        self.details.align = 'center'    # replace_query.nml:25

        self.changes.x = 2    # replace_query.nml:29
        self.changes.y = 3    # replace_query.nml:30
        self.changes.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # replace_query.nml:31
        self.changes.height = _bind(lambda _o: max(1, _o.parent.height - 8))    # replace_query.nml:32

        self.agree.text = _bind(lambda _o: _tr('~Y~es'), yielding=True)    # replace_query.nml:36
        self.agree.default = True    # replace_query.nml:37
        self.agree.x = _bind(lambda _o: self.slot(0))    # replace_query.nml:38
        self.agree.y = _bind(lambda _o: max(0, _o.parent.height - 4))    # replace_query.nml:39
        self.agree.width = 11    # replace_query.nml:40
        self.agree.height = 2    # replace_query.nml:41
        self.agree.on_click = self.on_agree_click    # replace_query.nml:35

        self.every.text = _bind(lambda _o: _tr('~A~ll'), yielding=True)    # replace_query.nml:45
        self.every.x = _bind(lambda _o: self.slot(1))    # replace_query.nml:46
        self.every.y = _bind(lambda _o: max(0, _o.parent.height - 4))    # replace_query.nml:47
        self.every.width = 11    # replace_query.nml:48
        self.every.height = 2    # replace_query.nml:49
        self.every.on_click = self.on_every_click    # replace_query.nml:44

        self.skip.text = _bind(lambda _o: _tr('~S~kip'), yielding=True)    # replace_query.nml:53
        self.skip.x = _bind(lambda _o: self.slot(2))    # replace_query.nml:54
        self.skip.y = _bind(lambda _o: max(0, _o.parent.height - 4))    # replace_query.nml:55
        self.skip.width = 11    # replace_query.nml:56
        self.skip.height = 2    # replace_query.nml:57
        self.skip.on_click = self.on_skip_click    # replace_query.nml:52

        self.abandon.text = _bind(lambda _o: _tr('Cancel'), yielding=True)    # replace_query.nml:61
        self.abandon.x = _bind(lambda _o: self.slot(3))    # replace_query.nml:62
        self.abandon.y = _bind(lambda _o: max(0, _o.parent.height - 4))    # replace_query.nml:63
        self.abandon.width = 11    # replace_query.nml:64
        self.abandon.height = 2    # replace_query.nml:65
        self.abandon.on_click = self.on_abandon_click    # replace_query.nml:60

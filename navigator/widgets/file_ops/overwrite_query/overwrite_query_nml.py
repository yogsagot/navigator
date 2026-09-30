# navml: generated
"""Generated from ``overwrite_query.nml``.

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

from navml.component import Component as _Component
from navml.widgets.dialog.button import Button    # overwrite_query.nml:1
from navml.widgets.dialog.check_boxes import CheckBoxes    # overwrite_query.nml:2
from navml.widgets.dialog.dialog import Dialog    # overwrite_query.nml:3
from navml.widgets.dialog.static_text import StaticText    # overwrite_query.nml:4

__navml_component__ = "OverwriteQuery"

__all__ = ["OverwriteQuery"]


class OverwriteQuery(Dialog, _Component):
    """A file the copy is about to land on: DOS Navigator's ``dlgOverwriteQuery``.

    The text is ``Overwrite``'s in ``FILECOPY.PAS`` -- the name, then
    ``dlFCOver``'s three centred lines -- and the buttons are the resource's
    five in its order, *Overwrite* two columns wider than the rest as it was
    there.  Six columns wider than DN's 60, because this library's buttons are
    eleven wide with their markers and five of them do not fit in 60.
    """

    #: The document this class was generated from.
    __navml_source__ = "overwrite_query.nml"

    #: Ids, annotated so the hand-written half completes them.
    details: StaticText    # overwrite_query.nml:19
    for_all: CheckBoxes    # overwrite_query.nml:29
    overwrite: Button    # overwrite_query.nml:37
    append: Button    # overwrite_query.nml:46
    rename: Button    # overwrite_query.nml:54
    skip: Button    # overwrite_query.nml:62
    abandon: Button    # overwrite_query.nml:70

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_overwrite_click(self, event: _Event) -> bool:    # overwrite_query.nml:37
        """``overwrite`` raised an event whose handler is ``on_click``."""
        return False

    async def on_append_click(self, event: _Event) -> bool:    # overwrite_query.nml:46
        """``append`` raised an event whose handler is ``on_click``."""
        return False

    async def on_rename_click(self, event: _Event) -> bool:    # overwrite_query.nml:54
        """``rename`` raised an event whose handler is ``on_click``."""
        return False

    async def on_skip_click(self, event: _Event) -> bool:    # overwrite_query.nml:62
        """``skip`` raised an event whose handler is ``on_click``."""
        return False

    async def on_abandon_click(self, event: _Event) -> bool:    # overwrite_query.nml:70
        """``abandon`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.details = StaticText(parent=self)    # overwrite_query.nml:18
        self.for_all = CheckBoxes(parent=self)    # overwrite_query.nml:28
        self.overwrite = Button(parent=self)    # overwrite_query.nml:36
        self.append = Button(parent=self)    # overwrite_query.nml:45
        self.rename = Button(parent=self)    # overwrite_query.nml:53
        self.skip = Button(parent=self)    # overwrite_query.nml:61
        self.abandon = Button(parent=self)    # overwrite_query.nml:69

        self.modal_width = 66    # overwrite_query.nml:14
        self.modal_height = 13    # overwrite_query.nml:15
        self.title = 'Confirm'    # overwrite_query.nml:16

        self.details.x = 1    # overwrite_query.nml:20
        self.details.y = 2    # overwrite_query.nml:21
        self.details.width = _bind(lambda _o: max(0, _o.parent.width - 2))    # overwrite_query.nml:22
        self.details.height = 5    # overwrite_query.nml:23
        self.details.align = 'center'    # overwrite_query.nml:24

        self.for_all.x = 4    # overwrite_query.nml:30
        self.for_all.y = 8    # overwrite_query.nml:31
        self.for_all.width = _bind(lambda _o: max(0, _o.parent.width - 8))    # overwrite_query.nml:32
        self.for_all.height = 1    # overwrite_query.nml:33
        self.for_all.items = ['Accept choice for ~a~ll files']    # overwrite_query.nml:34

        self.overwrite.text = '~O~verwrite'    # overwrite_query.nml:38
        self.overwrite.default = True    # overwrite_query.nml:39
        self.overwrite.x = 2    # overwrite_query.nml:40
        self.overwrite.y = _bind(lambda _o: max(0, _o.parent.height - 4))    # overwrite_query.nml:41
        self.overwrite.width = 13    # overwrite_query.nml:42
        self.overwrite.height = 2    # overwrite_query.nml:43
        self.overwrite.on_click = self.on_overwrite_click    # overwrite_query.nml:37

        self.append.text = 'A~p~pend'    # overwrite_query.nml:47
        self.append.x = 16    # overwrite_query.nml:48
        self.append.y = _bind(lambda _o: max(0, _o.parent.height - 4))    # overwrite_query.nml:49
        self.append.width = 11    # overwrite_query.nml:50
        self.append.height = 2    # overwrite_query.nml:51
        self.append.on_click = self.on_append_click    # overwrite_query.nml:46

        self.rename.text = '~R~ename'    # overwrite_query.nml:55
        self.rename.x = 28    # overwrite_query.nml:56
        self.rename.y = _bind(lambda _o: max(0, _o.parent.height - 4))    # overwrite_query.nml:57
        self.rename.width = 11    # overwrite_query.nml:58
        self.rename.height = 2    # overwrite_query.nml:59
        self.rename.on_click = self.on_rename_click    # overwrite_query.nml:54

        self.skip.text = '~S~kip'    # overwrite_query.nml:63
        self.skip.x = 40    # overwrite_query.nml:64
        self.skip.y = _bind(lambda _o: max(0, _o.parent.height - 4))    # overwrite_query.nml:65
        self.skip.width = 11    # overwrite_query.nml:66
        self.skip.height = 2    # overwrite_query.nml:67
        self.skip.on_click = self.on_skip_click    # overwrite_query.nml:62

        self.abandon.text = 'Cancel'    # overwrite_query.nml:71
        self.abandon.x = 52    # overwrite_query.nml:72
        self.abandon.y = _bind(lambda _o: max(0, _o.parent.height - 4))    # overwrite_query.nml:73
        self.abandon.width = 11    # overwrite_query.nml:74
        self.abandon.height = 2    # overwrite_query.nml:75
        self.abandon.on_click = self.on_abandon_click    # overwrite_query.nml:70

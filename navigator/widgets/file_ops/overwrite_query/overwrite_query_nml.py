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
from navkit.i18n import tr as _tr
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
    for_all: CheckBoxes    # overwrite_query.nml:30
    overwrite: Button    # overwrite_query.nml:40
    append: Button    # overwrite_query.nml:50
    rename: Button    # overwrite_query.nml:59
    skip: Button    # overwrite_query.nml:68
    abandon: Button    # overwrite_query.nml:77

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_overwrite_click(self, event: _Event) -> bool:    # overwrite_query.nml:40
        """``overwrite`` raised an event whose handler is ``on_click``."""
        return False

    async def on_append_click(self, event: _Event) -> bool:    # overwrite_query.nml:50
        """``append`` raised an event whose handler is ``on_click``."""
        return False

    async def on_rename_click(self, event: _Event) -> bool:    # overwrite_query.nml:59
        """``rename`` raised an event whose handler is ``on_click``."""
        return False

    async def on_skip_click(self, event: _Event) -> bool:    # overwrite_query.nml:68
        """``skip`` raised an event whose handler is ``on_click``."""
        return False

    async def on_abandon_click(self, event: _Event) -> bool:    # overwrite_query.nml:77
        """``abandon`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.details = StaticText(parent=self)    # overwrite_query.nml:18
        self.for_all = CheckBoxes(parent=self)    # overwrite_query.nml:29
        self.overwrite = Button(parent=self)    # overwrite_query.nml:39
        self.append = Button(parent=self)    # overwrite_query.nml:49
        self.rename = Button(parent=self)    # overwrite_query.nml:58
        self.skip = Button(parent=self)    # overwrite_query.nml:67
        self.abandon = Button(parent=self)    # overwrite_query.nml:76

        self.modal_width = 66    # overwrite_query.nml:14
        self.modal_height = 13    # overwrite_query.nml:15
        self.title = _bind(lambda _o: _tr('Confirm'), yielding=True)    # overwrite_query.nml:16

        self.details.y = 2    # overwrite_query.nml:20
        self.details.height = 5    # overwrite_query.nml:21
        self.details.align = 'center'    # overwrite_query.nml:25
        self.details.x = 1    # overwrite_query.nml:23
        self.details.width = _bind(lambda _o: max(0, _o.parent.width - 2))    # overwrite_query.nml:24

        self.for_all.y = 8    # overwrite_query.nml:31
        self.for_all.height = 1    # overwrite_query.nml:32
        self.for_all.items = _bind(    # overwrite_query.nml:36
            lambda _o: [_tr('Accept choice for ~a~ll files')],
            yielding=True,
        )
        self.for_all.tooltips = _bind(    # overwrite_query.nml:37
            lambda _o: [_tr('Give this answer for every file that is already there')],
            yielding=True,
        )
        self.for_all.x = 4    # overwrite_query.nml:34
        self.for_all.width = _bind(lambda _o: max(0, _o.parent.width - 8))    # overwrite_query.nml:35

        self.overwrite.text = _bind(    # overwrite_query.nml:41
            lambda _o: _tr('~O~verwrite'),
            yielding=True,
        )
        self.overwrite.default = True    # overwrite_query.nml:42
        self.overwrite.x = 2    # overwrite_query.nml:43
        self.overwrite.width = 13    # overwrite_query.nml:44
        self.overwrite.height = 2    # overwrite_query.nml:45
        self.overwrite.y = _bind(    # overwrite_query.nml:47
            lambda _o: max(0, _o.parent.height - 2 - _o.height)
        )
        self.overwrite.on_click = self.on_overwrite_click    # overwrite_query.nml:40

        self.append.text = _bind(lambda _o: _tr('A~p~pend'), yielding=True)    # overwrite_query.nml:51
        self.append.x = 16    # overwrite_query.nml:52
        self.append.width = 11    # overwrite_query.nml:53
        self.append.height = 2    # overwrite_query.nml:54
        self.append.y = _bind(    # overwrite_query.nml:56
            lambda _o: max(0, _o.parent.height - 2 - _o.height)
        )
        self.append.on_click = self.on_append_click    # overwrite_query.nml:50

        self.rename.text = _bind(lambda _o: _tr('~R~ename'), yielding=True)    # overwrite_query.nml:60
        self.rename.x = 28    # overwrite_query.nml:61
        self.rename.width = 11    # overwrite_query.nml:62
        self.rename.height = 2    # overwrite_query.nml:63
        self.rename.y = _bind(    # overwrite_query.nml:65
            lambda _o: max(0, _o.parent.height - 2 - _o.height)
        )
        self.rename.on_click = self.on_rename_click    # overwrite_query.nml:59

        self.skip.text = _bind(lambda _o: _tr('~S~kip'), yielding=True)    # overwrite_query.nml:69
        self.skip.x = 40    # overwrite_query.nml:70
        self.skip.width = 11    # overwrite_query.nml:71
        self.skip.height = 2    # overwrite_query.nml:72
        self.skip.y = _bind(    # overwrite_query.nml:74
            lambda _o: max(0, _o.parent.height - 2 - _o.height)
        )
        self.skip.on_click = self.on_skip_click    # overwrite_query.nml:68

        self.abandon.text = _bind(lambda _o: _tr('Cancel'), yielding=True)    # overwrite_query.nml:78
        self.abandon.x = 52    # overwrite_query.nml:79
        self.abandon.width = 11    # overwrite_query.nml:80
        self.abandon.height = 2    # overwrite_query.nml:81
        self.abandon.y = _bind(    # overwrite_query.nml:83
            lambda _o: max(0, _o.parent.height - 2 - _o.height)
        )
        self.abandon.on_click = self.on_abandon_click    # overwrite_query.nml:77

# navml: generated
"""Generated from ``relink_dialog.nml``.

Do not edit: edit the markup and rerun ``python -m navml build``.
"""

from __future__ import annotations

#: Everything the generator needs for itself is underscored, so a document may
#: import any name at all without colliding with it -- there is no reserved
#: word.  A bare ``Label:`` head is what asks for ``_Component``; markup
#: never names it.  See *Importing another component* in navml/DESIGN.md.
from typing import Any as _Any

from navkit.i18n import tr as _tr
from navkit.reactive import bind as _bind

from navml.component import Component as _Component
from navigator.widgets.file_ops.relink_dialog.relink_preview import RelinkPreview    # relink_dialog.nml:1
from navml.widgets.dialog.dialog import Dialog    # relink_dialog.nml:2
from navml.widgets.dialog.field import Field    # relink_dialog.nml:3
from navml.widgets.dialog.static_text import StaticText    # relink_dialog.nml:4

__navml_component__ = "RelinkDialog"

__all__ = ["RelinkDialog"]


class RelinkDialog(Dialog, _Component):
    """File > Symlink > Edit link target with several links selected: one

    replacement in all their targets, for a tree that moved.  A departure;
    Multi-rename's box cut down to its *Search for* / *Replace with*.
    """

    #: The document this class was generated from.
    __navml_source__ = "relink_dialog.nml"

    #: Ids, annotated so the hand-written half completes them.
    search: Field    # relink_dialog.nml:15
    replace: Field    # relink_dialog.nml:25
    preview: RelinkPreview    # relink_dialog.nml:35
    status: StaticText    # relink_dialog.nml:43

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.search = Field(parent=self)    # relink_dialog.nml:14
        self.replace = Field(parent=self)    # relink_dialog.nml:24
        self.preview = RelinkPreview(parent=self)    # relink_dialog.nml:34
        self.status = StaticText(parent=self)    # relink_dialog.nml:42

        self.modal_width = 76    # relink_dialog.nml:10
        self.modal_height = 20    # relink_dialog.nml:11
        self.title = _bind(    # relink_dialog.nml:12
            lambda _o: _tr('Change link targets'),
            yielding=True,
        )

        self.search.y = 1    # relink_dialog.nml:16
        self.search.label_text = _bind(    # relink_dialog.nml:20
            lambda _o: _tr('~S~earch for'),
            yielding=True,
        )
        self.search.label_width = 14    # relink_dialog.nml:21
        self.search.history_id = 'relink_search'    # relink_dialog.nml:22
        self.search.x = 2    # relink_dialog.nml:18
        self.search.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # relink_dialog.nml:19

        self.replace.y = 2    # relink_dialog.nml:26
        self.replace.label_text = _bind(    # relink_dialog.nml:30
            lambda _o: _tr('Re~p~lace with'),
            yielding=True,
        )
        self.replace.label_width = 14    # relink_dialog.nml:31
        self.replace.history_id = 'relink_replace'    # relink_dialog.nml:32
        self.replace.x = 2    # relink_dialog.nml:28
        self.replace.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # relink_dialog.nml:29

        self.preview.x = 2    # relink_dialog.nml:37
        self.preview.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # relink_dialog.nml:38
        self.preview.y = 4    # relink_dialog.nml:39
        self.preview.height = _bind(lambda _o: max(0, _o.parent.height - 9))    # relink_dialog.nml:40

        self.status.align = 'center'    # relink_dialog.nml:48
        self.status.x = 2    # relink_dialog.nml:45
        self.status.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # relink_dialog.nml:46
        self.status.y = _bind(    # relink_dialog.nml:47
            lambda _o: max(0, _o.parent.height - 4 - _o.height)
        )

        self._navml_built(__class__)

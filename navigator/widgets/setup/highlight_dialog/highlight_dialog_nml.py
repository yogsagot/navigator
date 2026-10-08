# navml: generated
"""Generated from ``highlight_dialog.nml``.

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
from navml.widgets.dialog.dialog import Dialog    # highlight_dialog.nml:1
from navml.widgets.dialog.field import Field    # highlight_dialog.nml:2

__navml_component__ = "HighlightDialog"

__all__ = ["HighlightDialog"]


class HighlightDialog(Dialog, _Component):
    """Options > File Manager > Highlight groups: DOS Navigator's ``dlgHighlightGroups``.

    Its five lines in its rows, each with DN's shared ``hsCustoms`` history,
    the dialog wider for Navigator's masks.  DN called the lines *Custom 1*
    to *Custom 5*; Navigator named the five groups (``filetypes.CUSTOM``),
    and the Colors dialog shows them by these names, so the lines say which
    is which.  Help is left out, having nothing to show yet.
    """

    #: The document this class was generated from.
    __navml_source__ = "highlight_dialog.nml"

    #: Ids, annotated so the hand-written half completes them.
    image: Field    # highlight_dialog.nml:17
    media: Field    # highlight_dialog.nml:27
    document: Field    # highlight_dialog.nml:37
    source: Field    # highlight_dialog.nml:47
    temp: Field    # highlight_dialog.nml:57

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.image = Field(parent=self)    # highlight_dialog.nml:16
        self.media = Field(parent=self)    # highlight_dialog.nml:26
        self.document = Field(parent=self)    # highlight_dialog.nml:36
        self.source = Field(parent=self)    # highlight_dialog.nml:46
        self.temp = Field(parent=self)    # highlight_dialog.nml:56

        self.modal_width = 66    # highlight_dialog.nml:12
        self.modal_height = 16    # highlight_dialog.nml:13
        self.title = _bind(lambda _o: _tr('Highlight groups'), yielding=True)    # highlight_dialog.nml:14

        self.image.x = 2    # highlight_dialog.nml:18
        self.image.y = 2    # highlight_dialog.nml:19
        self.image.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # highlight_dialog.nml:20
        self.image.height = 1    # highlight_dialog.nml:21
        self.image.label_text = _bind(    # highlight_dialog.nml:22
            lambda _o: _tr('~I~mages'),
            yielding=True,
        )
        self.image.label_width = 18    # highlight_dialog.nml:23
        self.image.history_id = 'customs'    # highlight_dialog.nml:24

        self.media.x = 2    # highlight_dialog.nml:28
        self.media.y = 4    # highlight_dialog.nml:29
        self.media.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # highlight_dialog.nml:30
        self.media.height = 1    # highlight_dialog.nml:31
        self.media.label_text = _bind(    # highlight_dialog.nml:32
            lambda _o: _tr('~A~udio and video'),
            yielding=True,
        )
        self.media.label_width = 18    # highlight_dialog.nml:33
        self.media.history_id = 'customs'    # highlight_dialog.nml:34

        self.document.x = 2    # highlight_dialog.nml:38
        self.document.y = 6    # highlight_dialog.nml:39
        self.document.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # highlight_dialog.nml:40
        self.document.height = 1    # highlight_dialog.nml:41
        self.document.label_text = _bind(    # highlight_dialog.nml:42
            lambda _o: _tr('~D~ocuments'),
            yielding=True,
        )
        self.document.label_width = 18    # highlight_dialog.nml:43
        self.document.history_id = 'customs'    # highlight_dialog.nml:44

        self.source.x = 2    # highlight_dialog.nml:48
        self.source.y = 8    # highlight_dialog.nml:49
        self.source.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # highlight_dialog.nml:50
        self.source.height = 1    # highlight_dialog.nml:51
        self.source.label_text = _bind(    # highlight_dialog.nml:52
            lambda _o: _tr('~S~ource code'),
            yielding=True,
        )
        self.source.label_width = 18    # highlight_dialog.nml:53
        self.source.history_id = 'customs'    # highlight_dialog.nml:54

        self.temp.x = 2    # highlight_dialog.nml:58
        self.temp.y = 10    # highlight_dialog.nml:59
        self.temp.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # highlight_dialog.nml:60
        self.temp.height = 1    # highlight_dialog.nml:61
        self.temp.label_text = _bind(    # highlight_dialog.nml:62
            lambda _o: _tr('~T~emporary files'),
            yielding=True,
        )
        self.temp.label_width = 18    # highlight_dialog.nml:63
        self.temp.history_id = 'customs'    # highlight_dialog.nml:64

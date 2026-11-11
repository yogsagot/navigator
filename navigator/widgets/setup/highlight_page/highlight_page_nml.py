# navml: generated
"""Generated from ``highlight_page.nml``.

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
from navkit.reactive import reactive as _reactive

from navml.component import Component as _Component
from navml.widgets.dialog.field import Field    # highlight_page.nml:1

__navml_component__ = "HighlightPage"

__all__ = ["HighlightPage"]


class HighlightPage(_Component):
    """Options > File Manager > Highlight groups: DOS Navigator's ``dlgHighlightGroups``.

    Its five lines in its rows, each with DN's shared ``hsCustoms`` history,
    the dialog wider for Navigator's masks.  DN called the lines *Custom 1*
    to *Custom 5*; Navigator named the five groups (``filetypes.CUSTOM``),
    and the Colors dialog shows them by these names, so the lines say which
    is which.  Help is left out, having nothing to show yet.
    """

    #: The document this class was generated from.
    __navml_source__ = "highlight_page.nml"

    #: The caption on its tab, which *Settings* gives it.
    title: str = _reactive('')    # highlight_page.nml:12

    #: Ids, annotated so the hand-written half completes them.
    image: Field    # highlight_page.nml:15
    media: Field    # highlight_page.nml:26
    document: Field    # highlight_page.nml:37
    source: Field    # highlight_page.nml:48
    temp: Field    # highlight_page.nml:59

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.image = Field(parent=self)    # highlight_page.nml:14
        self.media = Field(parent=self)    # highlight_page.nml:25
        self.document = Field(parent=self)    # highlight_page.nml:36
        self.source = Field(parent=self)    # highlight_page.nml:47
        self.temp = Field(parent=self)    # highlight_page.nml:58

        self.image.y = 2    # highlight_page.nml:16
        self.image.height = 1    # highlight_page.nml:17
        self.image.label_text = _bind(    # highlight_page.nml:21
            lambda _o: _tr('~I~mages'),
            yielding=True,
        )
        self.image.label_width = 18    # highlight_page.nml:22
        self.image.history_id = 'customs'    # highlight_page.nml:23
        self.image.x = 2    # highlight_page.nml:19
        self.image.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # highlight_page.nml:20

        self.media.y = 4    # highlight_page.nml:27
        self.media.height = 1    # highlight_page.nml:28
        self.media.label_text = _bind(    # highlight_page.nml:32
            lambda _o: _tr('~A~udio and video'),
            yielding=True,
        )
        self.media.label_width = 18    # highlight_page.nml:33
        self.media.history_id = 'customs'    # highlight_page.nml:34
        self.media.x = 2    # highlight_page.nml:30
        self.media.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # highlight_page.nml:31

        self.document.y = 6    # highlight_page.nml:38
        self.document.height = 1    # highlight_page.nml:39
        self.document.label_text = _bind(    # highlight_page.nml:43
            lambda _o: _tr('~D~ocuments'),
            yielding=True,
        )
        self.document.label_width = 18    # highlight_page.nml:44
        self.document.history_id = 'customs'    # highlight_page.nml:45
        self.document.x = 2    # highlight_page.nml:41
        self.document.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # highlight_page.nml:42

        self.source.y = 8    # highlight_page.nml:49
        self.source.height = 1    # highlight_page.nml:50
        self.source.label_text = _bind(    # highlight_page.nml:54
            lambda _o: _tr('~S~ource code'),
            yielding=True,
        )
        self.source.label_width = 18    # highlight_page.nml:55
        self.source.history_id = 'customs'    # highlight_page.nml:56
        self.source.x = 2    # highlight_page.nml:52
        self.source.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # highlight_page.nml:53

        self.temp.y = 10    # highlight_page.nml:60
        self.temp.height = 1    # highlight_page.nml:61
        self.temp.label_text = _bind(    # highlight_page.nml:65
            lambda _o: _tr('~T~emporary files'),
            yielding=True,
        )
        self.temp.label_width = 18    # highlight_page.nml:66
        self.temp.history_id = 'customs'    # highlight_page.nml:67
        self.temp.x = 2    # highlight_page.nml:63
        self.temp.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # highlight_page.nml:64

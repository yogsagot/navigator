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
from navigator.widgets.setup.settings_page import SettingsPage    # highlight_page.nml:2

__navml_component__ = "HighlightPage"

__all__ = ["HighlightPage"]


class HighlightPage(SettingsPage, _Component):
    """Options > File Manager > Highlight groups: DOS Navigator's ``dlgHighlightGroups``.

    Its five lines in its rows, each with DN's shared ``hsCustoms`` history,
    the dialog wider for Navigator's masks.  DN called the lines *Custom 1*
    to *Custom 5*; Navigator named the five groups (``filetypes.CUSTOM``),
    and the Colors dialog shows them by these names, so the lines say which
    is which.
    """

    #: The document this class was generated from.
    __navml_source__ = "highlight_page.nml"

    help_topic = 'settings.md#highlight'    # highlight_page.nml:12
    section_name = 'highlight_groups'    # highlight_page.nml:13

    #: The caption on its tab, which *Settings* gives it.
    title: str = _reactive('')    # highlight_page.nml:16

    #: Ids, annotated so the hand-written half completes them.
    image: Field    # highlight_page.nml:19
    media: Field    # highlight_page.nml:30
    document: Field    # highlight_page.nml:41
    source: Field    # highlight_page.nml:52
    temp: Field    # highlight_page.nml:63

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.image = Field(parent=self)    # highlight_page.nml:18
        self.media = Field(parent=self)    # highlight_page.nml:29
        self.document = Field(parent=self)    # highlight_page.nml:40
        self.source = Field(parent=self)    # highlight_page.nml:51
        self.temp = Field(parent=self)    # highlight_page.nml:62

        self.image.key = 'image'    # highlight_page.nml:20
        self.image.y = 2    # highlight_page.nml:21
        self.image.label_text = _bind(    # highlight_page.nml:25
            lambda _o: _tr('~I~mages'),
            yielding=True,
        )
        self.image.label_width = 18    # highlight_page.nml:26
        self.image.history_id = 'customs'    # highlight_page.nml:27
        self.image.x = 2    # highlight_page.nml:23
        self.image.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # highlight_page.nml:24

        self.media.key = 'media'    # highlight_page.nml:31
        self.media.y = 4    # highlight_page.nml:32
        self.media.label_text = _bind(    # highlight_page.nml:36
            lambda _o: _tr('~A~udio and video'),
            yielding=True,
        )
        self.media.label_width = 18    # highlight_page.nml:37
        self.media.history_id = 'customs'    # highlight_page.nml:38
        self.media.x = 2    # highlight_page.nml:34
        self.media.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # highlight_page.nml:35

        self.document.key = 'document'    # highlight_page.nml:42
        self.document.y = 6    # highlight_page.nml:43
        self.document.label_text = _bind(    # highlight_page.nml:47
            lambda _o: _tr('~D~ocuments'),
            yielding=True,
        )
        self.document.label_width = 18    # highlight_page.nml:48
        self.document.history_id = 'customs'    # highlight_page.nml:49
        self.document.x = 2    # highlight_page.nml:45
        self.document.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # highlight_page.nml:46

        self.source.key = 'source'    # highlight_page.nml:53
        self.source.y = 8    # highlight_page.nml:54
        self.source.label_text = _bind(    # highlight_page.nml:58
            lambda _o: _tr('~S~ource code'),
            yielding=True,
        )
        self.source.label_width = 18    # highlight_page.nml:59
        self.source.history_id = 'customs'    # highlight_page.nml:60
        self.source.x = 2    # highlight_page.nml:56
        self.source.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # highlight_page.nml:57

        self.temp.key = 'temp'    # highlight_page.nml:64
        self.temp.y = 10    # highlight_page.nml:65
        self.temp.label_text = _bind(    # highlight_page.nml:69
            lambda _o: _tr('~T~emporary files'),
            yielding=True,
        )
        self.temp.label_width = 18    # highlight_page.nml:70
        self.temp.history_id = 'customs'    # highlight_page.nml:71
        self.temp.x = 2    # highlight_page.nml:67
        self.temp.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # highlight_page.nml:68

        self._navml_built(__class__)

# navml: generated
"""Generated from ``viewer_types_page.nml``.

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
from navml.widgets.dialog.check_boxes import CheckBoxes    # viewer_types_page.nml:1
from navml.widgets.dialog.input_line import InputLine    # viewer_types_page.nml:2
from navml.widgets.dialog.label import Label    # viewer_types_page.nml:3
from navml.widgets.dialog.static_text import StaticText    # viewer_types_page.nml:4

__navml_component__ = "ViewerTypesPage"

__all__ = ["ViewerTypesPage"]


class ViewerTypesPage(_Component):
    """Options > Settings > *Viewer file types*: which files F3 shows rendered --

    a Markdown page, a picture, a spreadsheet, a tree, a database -- and by
    what masks (``[viewer] render_*``, ``*_masks``).  Not DN's: its viewer
    rendered nothing, so these are departures' settings, given a page so that
    none is the ini file's alone.  View > *Markup view* still switches one
    file; this sets what F3 starts with.
    """

    #: The document this class was generated from.
    __navml_source__ = "viewer_types_page.nml"

    #: The caption on its tab, which *Settings* gives it.
    title: str = _reactive('')    # viewer_types_page.nml:14

    #: Ids, annotated so the hand-written half completes them.
    heading: StaticText    # viewer_types_page.nml:18
    masks_heading: StaticText    # viewer_types_page.nml:25
    markdown: CheckBoxes    # viewer_types_page.nml:33
    markdown_masks: InputLine    # viewer_types_page.nml:41
    rst: CheckBoxes    # viewer_types_page.nml:47
    rst_masks: InputLine    # viewer_types_page.nml:55
    html: CheckBoxes    # viewer_types_page.nml:61
    html_masks: InputLine    # viewer_types_page.nml:69
    pdf: CheckBoxes    # viewer_types_page.nml:75
    pdf_masks: InputLine    # viewer_types_page.nml:83
    images: CheckBoxes    # viewer_types_page.nml:89
    images_masks: InputLine    # viewer_types_page.nml:97
    tables: CheckBoxes    # viewer_types_page.nml:103
    tables_masks: InputLine    # viewer_types_page.nml:111
    structured: CheckBoxes    # viewer_types_page.nml:117
    structured_masks: InputLine    # viewer_types_page.nml:125
    database_caption: Label    # viewer_types_page.nml:133
    database_masks: InputLine    # viewer_types_page.nml:141

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.heading = StaticText(parent=self)    # viewer_types_page.nml:17
        self.masks_heading = StaticText(parent=self)    # viewer_types_page.nml:24
        self.markdown = CheckBoxes(parent=self)    # viewer_types_page.nml:32
        self.markdown_masks = InputLine(parent=self)    # viewer_types_page.nml:40
        self.rst = CheckBoxes(parent=self)    # viewer_types_page.nml:46
        self.rst_masks = InputLine(parent=self)    # viewer_types_page.nml:54
        self.html = CheckBoxes(parent=self)    # viewer_types_page.nml:60
        self.html_masks = InputLine(parent=self)    # viewer_types_page.nml:68
        self.pdf = CheckBoxes(parent=self)    # viewer_types_page.nml:74
        self.pdf_masks = InputLine(parent=self)    # viewer_types_page.nml:82
        self.images = CheckBoxes(parent=self)    # viewer_types_page.nml:88
        self.images_masks = InputLine(parent=self)    # viewer_types_page.nml:96
        self.tables = CheckBoxes(parent=self)    # viewer_types_page.nml:102
        self.tables_masks = InputLine(parent=self)    # viewer_types_page.nml:110
        self.structured = CheckBoxes(parent=self)    # viewer_types_page.nml:116
        self.structured_masks = InputLine(parent=self)    # viewer_types_page.nml:124
        self.database_caption = Label(parent=self)    # viewer_types_page.nml:132
        self.database_masks = InputLine(parent=self)    # viewer_types_page.nml:140

        self.heading.x = 2    # viewer_types_page.nml:19
        self.heading.y = 1    # viewer_types_page.nml:20
        self.heading.width = 25    # viewer_types_page.nml:21
        self.heading.text = _bind(lambda _o: _tr('F3 renders'), yielding=True)    # viewer_types_page.nml:22

        self.masks_heading.y = 1    # viewer_types_page.nml:26
        self.masks_heading.text = _bind(    # viewer_types_page.nml:30
            lambda _o: _tr('Masks, separated by ;'),
            yielding=True,
        )
        self.masks_heading.x = 28    # viewer_types_page.nml:28
        self.masks_heading.width = _bind(    # viewer_types_page.nml:29
            lambda _o: max(0, _o.parent.width - 30)
        )

        self.markdown.x = 2    # viewer_types_page.nml:34
        self.markdown.y = 2    # viewer_types_page.nml:35
        self.markdown.width = 26    # viewer_types_page.nml:36
        self.markdown.height = 1    # viewer_types_page.nml:37
        self.markdown.items = _bind(    # viewer_types_page.nml:38
            lambda _o: [_tr('~M~arkdown')],
            yielding=True,
        )

        self.markdown_masks.x = 28    # viewer_types_page.nml:42
        self.markdown_masks.y = 2    # viewer_types_page.nml:43
        self.markdown_masks.width = _bind(    # viewer_types_page.nml:44
            lambda _o: max(1, _o.parent.width - 30)
        )

        self.rst.x = 2    # viewer_types_page.nml:48
        self.rst.y = 3    # viewer_types_page.nml:49
        self.rst.width = 26    # viewer_types_page.nml:50
        self.rst.height = 1    # viewer_types_page.nml:51
        self.rst.items = _bind(    # viewer_types_page.nml:52
            lambda _o: [_tr('~r~eStructuredText')],
            yielding=True,
        )

        self.rst_masks.x = 28    # viewer_types_page.nml:56
        self.rst_masks.y = 3    # viewer_types_page.nml:57
        self.rst_masks.width = _bind(lambda _o: max(1, _o.parent.width - 30))    # viewer_types_page.nml:58

        self.html.x = 2    # viewer_types_page.nml:62
        self.html.y = 4    # viewer_types_page.nml:63
        self.html.width = 26    # viewer_types_page.nml:64
        self.html.height = 1    # viewer_types_page.nml:65
        self.html.items = _bind(lambda _o: [_tr('~H~TML')], yielding=True)    # viewer_types_page.nml:66

        self.html_masks.x = 28    # viewer_types_page.nml:70
        self.html_masks.y = 4    # viewer_types_page.nml:71
        self.html_masks.width = _bind(lambda _o: max(1, _o.parent.width - 30))    # viewer_types_page.nml:72

        self.pdf.x = 2    # viewer_types_page.nml:76
        self.pdf.y = 5    # viewer_types_page.nml:77
        self.pdf.width = 26    # viewer_types_page.nml:78
        self.pdf.height = 1    # viewer_types_page.nml:79
        self.pdf.items = _bind(lambda _o: [_tr('~P~DF')], yielding=True)    # viewer_types_page.nml:80

        self.pdf_masks.x = 28    # viewer_types_page.nml:84
        self.pdf_masks.y = 5    # viewer_types_page.nml:85
        self.pdf_masks.width = _bind(lambda _o: max(1, _o.parent.width - 30))    # viewer_types_page.nml:86

        self.images.x = 2    # viewer_types_page.nml:90
        self.images.y = 6    # viewer_types_page.nml:91
        self.images.width = 26    # viewer_types_page.nml:92
        self.images.height = 1    # viewer_types_page.nml:93
        self.images.items = _bind(    # viewer_types_page.nml:94
            lambda _o: [_tr('P~i~ctures')],
            yielding=True,
        )

        self.images_masks.x = 28    # viewer_types_page.nml:98
        self.images_masks.y = 6    # viewer_types_page.nml:99
        self.images_masks.width = _bind(    # viewer_types_page.nml:100
            lambda _o: max(1, _o.parent.width - 30)
        )

        self.tables.x = 2    # viewer_types_page.nml:104
        self.tables.y = 7    # viewer_types_page.nml:105
        self.tables.width = 26    # viewer_types_page.nml:106
        self.tables.height = 1    # viewer_types_page.nml:107
        self.tables.items = _bind(    # viewer_types_page.nml:108
            lambda _o: [_tr('~T~ables (CSV, TSV)')],
            yielding=True,
        )

        self.tables_masks.x = 28    # viewer_types_page.nml:112
        self.tables_masks.y = 7    # viewer_types_page.nml:113
        self.tables_masks.width = _bind(    # viewer_types_page.nml:114
            lambda _o: max(1, _o.parent.width - 30)
        )

        self.structured.x = 2    # viewer_types_page.nml:118
        self.structured.y = 8    # viewer_types_page.nml:119
        self.structured.width = 26    # viewer_types_page.nml:120
        self.structured.height = 1    # viewer_types_page.nml:121
        self.structured.items = _bind(    # viewer_types_page.nml:122
            lambda _o: [_tr('~S~tructured, as a tree')],
            yielding=True,
        )

        self.structured_masks.x = 28    # viewer_types_page.nml:126
        self.structured_masks.y = 8    # viewer_types_page.nml:127
        self.structured_masks.width = _bind(    # viewer_types_page.nml:128
            lambda _o: max(1, _o.parent.width - 30)
        )

        self.database_caption.x = 6    # viewer_types_page.nml:134
        self.database_caption.y = 9    # viewer_types_page.nml:135
        self.database_caption.width = 22    # viewer_types_page.nml:136
        self.database_caption.text = _bind(    # viewer_types_page.nml:137
            lambda _o: _tr('SQ~L~ite databases'),
            yielding=True,
        )
        self.database_caption.link = _bind(lambda _o: self.database_masks)    # viewer_types_page.nml:138

        self.database_masks.x = 28    # viewer_types_page.nml:142
        self.database_masks.y = 9    # viewer_types_page.nml:143
        self.database_masks.width = _bind(    # viewer_types_page.nml:144
            lambda _o: max(1, _o.parent.width - 30)
        )

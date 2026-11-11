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
    masks_heading: StaticText    # viewer_types_page.nml:26
    markdown: CheckBoxes    # viewer_types_page.nml:35
    markdown_masks: InputLine    # viewer_types_page.nml:43
    rst: CheckBoxes    # viewer_types_page.nml:50
    rst_masks: InputLine    # viewer_types_page.nml:58
    html: CheckBoxes    # viewer_types_page.nml:65
    html_masks: InputLine    # viewer_types_page.nml:73
    pdf: CheckBoxes    # viewer_types_page.nml:80
    pdf_masks: InputLine    # viewer_types_page.nml:88
    images: CheckBoxes    # viewer_types_page.nml:95
    images_masks: InputLine    # viewer_types_page.nml:103
    tables: CheckBoxes    # viewer_types_page.nml:110
    tables_masks: InputLine    # viewer_types_page.nml:118
    structured: CheckBoxes    # viewer_types_page.nml:125
    structured_masks: InputLine    # viewer_types_page.nml:133
    database_caption: Label    # viewer_types_page.nml:142
    database_masks: InputLine    # viewer_types_page.nml:151

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.heading = StaticText(parent=self)    # viewer_types_page.nml:17
        self.masks_heading = StaticText(parent=self)    # viewer_types_page.nml:25
        self.markdown = CheckBoxes(parent=self)    # viewer_types_page.nml:34
        self.markdown_masks = InputLine(parent=self)    # viewer_types_page.nml:42
        self.rst = CheckBoxes(parent=self)    # viewer_types_page.nml:49
        self.rst_masks = InputLine(parent=self)    # viewer_types_page.nml:57
        self.html = CheckBoxes(parent=self)    # viewer_types_page.nml:64
        self.html_masks = InputLine(parent=self)    # viewer_types_page.nml:72
        self.pdf = CheckBoxes(parent=self)    # viewer_types_page.nml:79
        self.pdf_masks = InputLine(parent=self)    # viewer_types_page.nml:87
        self.images = CheckBoxes(parent=self)    # viewer_types_page.nml:94
        self.images_masks = InputLine(parent=self)    # viewer_types_page.nml:102
        self.tables = CheckBoxes(parent=self)    # viewer_types_page.nml:109
        self.tables_masks = InputLine(parent=self)    # viewer_types_page.nml:117
        self.structured = CheckBoxes(parent=self)    # viewer_types_page.nml:124
        self.structured_masks = InputLine(parent=self)    # viewer_types_page.nml:132
        self.database_caption = Label(parent=self)    # viewer_types_page.nml:141
        self.database_masks = InputLine(parent=self)    # viewer_types_page.nml:150

        self.heading.x = 2    # viewer_types_page.nml:19
        self.heading.y = 1    # viewer_types_page.nml:20
        self.heading.width = 25    # viewer_types_page.nml:21
        self.heading.height = 1    # viewer_types_page.nml:22
        self.heading.text = _bind(lambda _o: _tr('F3 renders'), yielding=True)    # viewer_types_page.nml:23

        self.masks_heading.y = 1    # viewer_types_page.nml:27
        self.masks_heading.height = 1    # viewer_types_page.nml:28
        self.masks_heading.text = _bind(    # viewer_types_page.nml:32
            lambda _o: _tr('Masks, separated by ;'),
            yielding=True,
        )
        self.masks_heading.x = 28    # viewer_types_page.nml:30
        self.masks_heading.width = _bind(    # viewer_types_page.nml:31
            lambda _o: max(0, _o.parent.width - 30)
        )

        self.markdown.x = 2    # viewer_types_page.nml:36
        self.markdown.y = 2    # viewer_types_page.nml:37
        self.markdown.width = 26    # viewer_types_page.nml:38
        self.markdown.height = 1    # viewer_types_page.nml:39
        self.markdown.items = _bind(    # viewer_types_page.nml:40
            lambda _o: [_tr('~M~arkdown')],
            yielding=True,
        )

        self.markdown_masks.x = 28    # viewer_types_page.nml:44
        self.markdown_masks.y = 2    # viewer_types_page.nml:45
        self.markdown_masks.width = _bind(    # viewer_types_page.nml:46
            lambda _o: max(1, _o.parent.width - 30)
        )
        self.markdown_masks.height = 1    # viewer_types_page.nml:47

        self.rst.x = 2    # viewer_types_page.nml:51
        self.rst.y = 3    # viewer_types_page.nml:52
        self.rst.width = 26    # viewer_types_page.nml:53
        self.rst.height = 1    # viewer_types_page.nml:54
        self.rst.items = _bind(    # viewer_types_page.nml:55
            lambda _o: [_tr('~r~eStructuredText')],
            yielding=True,
        )

        self.rst_masks.x = 28    # viewer_types_page.nml:59
        self.rst_masks.y = 3    # viewer_types_page.nml:60
        self.rst_masks.width = _bind(lambda _o: max(1, _o.parent.width - 30))    # viewer_types_page.nml:61
        self.rst_masks.height = 1    # viewer_types_page.nml:62

        self.html.x = 2    # viewer_types_page.nml:66
        self.html.y = 4    # viewer_types_page.nml:67
        self.html.width = 26    # viewer_types_page.nml:68
        self.html.height = 1    # viewer_types_page.nml:69
        self.html.items = _bind(lambda _o: [_tr('~H~TML')], yielding=True)    # viewer_types_page.nml:70

        self.html_masks.x = 28    # viewer_types_page.nml:74
        self.html_masks.y = 4    # viewer_types_page.nml:75
        self.html_masks.width = _bind(lambda _o: max(1, _o.parent.width - 30))    # viewer_types_page.nml:76
        self.html_masks.height = 1    # viewer_types_page.nml:77

        self.pdf.x = 2    # viewer_types_page.nml:81
        self.pdf.y = 5    # viewer_types_page.nml:82
        self.pdf.width = 26    # viewer_types_page.nml:83
        self.pdf.height = 1    # viewer_types_page.nml:84
        self.pdf.items = _bind(lambda _o: [_tr('~P~DF')], yielding=True)    # viewer_types_page.nml:85

        self.pdf_masks.x = 28    # viewer_types_page.nml:89
        self.pdf_masks.y = 5    # viewer_types_page.nml:90
        self.pdf_masks.width = _bind(lambda _o: max(1, _o.parent.width - 30))    # viewer_types_page.nml:91
        self.pdf_masks.height = 1    # viewer_types_page.nml:92

        self.images.x = 2    # viewer_types_page.nml:96
        self.images.y = 6    # viewer_types_page.nml:97
        self.images.width = 26    # viewer_types_page.nml:98
        self.images.height = 1    # viewer_types_page.nml:99
        self.images.items = _bind(    # viewer_types_page.nml:100
            lambda _o: [_tr('P~i~ctures')],
            yielding=True,
        )

        self.images_masks.x = 28    # viewer_types_page.nml:104
        self.images_masks.y = 6    # viewer_types_page.nml:105
        self.images_masks.width = _bind(    # viewer_types_page.nml:106
            lambda _o: max(1, _o.parent.width - 30)
        )
        self.images_masks.height = 1    # viewer_types_page.nml:107

        self.tables.x = 2    # viewer_types_page.nml:111
        self.tables.y = 7    # viewer_types_page.nml:112
        self.tables.width = 26    # viewer_types_page.nml:113
        self.tables.height = 1    # viewer_types_page.nml:114
        self.tables.items = _bind(    # viewer_types_page.nml:115
            lambda _o: [_tr('~T~ables (CSV, TSV)')],
            yielding=True,
        )

        self.tables_masks.x = 28    # viewer_types_page.nml:119
        self.tables_masks.y = 7    # viewer_types_page.nml:120
        self.tables_masks.width = _bind(    # viewer_types_page.nml:121
            lambda _o: max(1, _o.parent.width - 30)
        )
        self.tables_masks.height = 1    # viewer_types_page.nml:122

        self.structured.x = 2    # viewer_types_page.nml:126
        self.structured.y = 8    # viewer_types_page.nml:127
        self.structured.width = 26    # viewer_types_page.nml:128
        self.structured.height = 1    # viewer_types_page.nml:129
        self.structured.items = _bind(    # viewer_types_page.nml:130
            lambda _o: [_tr('~S~tructured, as a tree')],
            yielding=True,
        )

        self.structured_masks.x = 28    # viewer_types_page.nml:134
        self.structured_masks.y = 8    # viewer_types_page.nml:135
        self.structured_masks.width = _bind(    # viewer_types_page.nml:136
            lambda _o: max(1, _o.parent.width - 30)
        )
        self.structured_masks.height = 1    # viewer_types_page.nml:137

        self.database_caption.x = 6    # viewer_types_page.nml:143
        self.database_caption.y = 9    # viewer_types_page.nml:144
        self.database_caption.width = 22    # viewer_types_page.nml:145
        self.database_caption.height = 1    # viewer_types_page.nml:146
        self.database_caption.text = _bind(    # viewer_types_page.nml:147
            lambda _o: _tr('SQ~L~ite databases'),
            yielding=True,
        )
        self.database_caption.link = _bind(lambda _o: self.database_masks)    # viewer_types_page.nml:148

        self.database_masks.x = 28    # viewer_types_page.nml:152
        self.database_masks.y = 9    # viewer_types_page.nml:153
        self.database_masks.width = _bind(    # viewer_types_page.nml:154
            lambda _o: max(1, _o.parent.width - 30)
        )
        self.database_masks.height = 1    # viewer_types_page.nml:155

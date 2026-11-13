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
from navigator.widgets.setup.settings_page import SettingsPage    # viewer_types_page.nml:5

__navml_component__ = "ViewerTypesPage"

__all__ = ["ViewerTypesPage"]


class ViewerTypesPage(SettingsPage, _Component):
    """Options > Settings > *Viewer file types*: which files F3 shows rendered --

    a Markdown page, a picture, a spreadsheet, a tree, a database -- and by
    what masks (``[viewer] render_*``, ``*_masks``).  Not DN's: its viewer
    rendered nothing, so these are departures' settings, given a page so that
    none is the ini file's alone.  View > *Markup view* still switches one
    file; this sets what F3 starts with.
    """

    #: The document this class was generated from.
    __navml_source__ = "viewer_types_page.nml"

    help_topic = 'settings.md#viewer-types'    # viewer_types_page.nml:14
    section_name = 'viewer'    # viewer_types_page.nml:15

    #: The caption on its tab, which *Settings* gives it.
    title: str = _reactive('')    # viewer_types_page.nml:18

    #: Ids, annotated so the hand-written half completes them.
    heading: StaticText    # viewer_types_page.nml:22
    masks_heading: StaticText    # viewer_types_page.nml:29
    markdown: CheckBoxes    # viewer_types_page.nml:37
    markdown_masks: InputLine    # viewer_types_page.nml:46
    rst: CheckBoxes    # viewer_types_page.nml:53
    rst_masks: InputLine    # viewer_types_page.nml:62
    html: CheckBoxes    # viewer_types_page.nml:69
    html_masks: InputLine    # viewer_types_page.nml:78
    pdf: CheckBoxes    # viewer_types_page.nml:85
    pdf_masks: InputLine    # viewer_types_page.nml:94
    images: CheckBoxes    # viewer_types_page.nml:101
    images_masks: InputLine    # viewer_types_page.nml:110
    tables: CheckBoxes    # viewer_types_page.nml:117
    tables_masks: InputLine    # viewer_types_page.nml:126
    structured: CheckBoxes    # viewer_types_page.nml:133
    structured_masks: InputLine    # viewer_types_page.nml:142
    database_caption: Label    # viewer_types_page.nml:151
    database_masks: InputLine    # viewer_types_page.nml:159

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.heading = StaticText(parent=self)    # viewer_types_page.nml:21
        self.masks_heading = StaticText(parent=self)    # viewer_types_page.nml:28
        self.markdown = CheckBoxes(parent=self)    # viewer_types_page.nml:36
        self.markdown_masks = InputLine(parent=self)    # viewer_types_page.nml:45
        self.rst = CheckBoxes(parent=self)    # viewer_types_page.nml:52
        self.rst_masks = InputLine(parent=self)    # viewer_types_page.nml:61
        self.html = CheckBoxes(parent=self)    # viewer_types_page.nml:68
        self.html_masks = InputLine(parent=self)    # viewer_types_page.nml:77
        self.pdf = CheckBoxes(parent=self)    # viewer_types_page.nml:84
        self.pdf_masks = InputLine(parent=self)    # viewer_types_page.nml:93
        self.images = CheckBoxes(parent=self)    # viewer_types_page.nml:100
        self.images_masks = InputLine(parent=self)    # viewer_types_page.nml:109
        self.tables = CheckBoxes(parent=self)    # viewer_types_page.nml:116
        self.tables_masks = InputLine(parent=self)    # viewer_types_page.nml:125
        self.structured = CheckBoxes(parent=self)    # viewer_types_page.nml:132
        self.structured_masks = InputLine(parent=self)    # viewer_types_page.nml:141
        self.database_caption = Label(parent=self)    # viewer_types_page.nml:150
        self.database_masks = InputLine(parent=self)    # viewer_types_page.nml:158

        self.heading.x = 2    # viewer_types_page.nml:23
        self.heading.y = 1    # viewer_types_page.nml:24
        self.heading.width = 25    # viewer_types_page.nml:25
        self.heading.text = _bind(lambda _o: _tr('F3 renders'), yielding=True)    # viewer_types_page.nml:26

        self.masks_heading.y = 1    # viewer_types_page.nml:30
        self.masks_heading.text = _bind(    # viewer_types_page.nml:34
            lambda _o: _tr('Masks, separated by ;'),
            yielding=True,
        )
        self.masks_heading.x = 28    # viewer_types_page.nml:32
        self.masks_heading.width = _bind(    # viewer_types_page.nml:33
            lambda _o: max(0, _o.parent.width - 30)
        )

        self.markdown.key = 'render_markdown'    # viewer_types_page.nml:38
        self.markdown.x = 2    # viewer_types_page.nml:39
        self.markdown.y = 2    # viewer_types_page.nml:40
        self.markdown.width = 26    # viewer_types_page.nml:41
        self.markdown.height = 1    # viewer_types_page.nml:42
        self.markdown.items = _bind(    # viewer_types_page.nml:43
            lambda _o: [_tr('~M~arkdown')],
            yielding=True,
        )

        self.markdown_masks.key = 'markdown_masks'    # viewer_types_page.nml:47
        self.markdown_masks.x = 28    # viewer_types_page.nml:48
        self.markdown_masks.y = 2    # viewer_types_page.nml:49
        self.markdown_masks.width = _bind(    # viewer_types_page.nml:50
            lambda _o: max(1, _o.parent.width - 30)
        )

        self.rst.key = 'render_rst'    # viewer_types_page.nml:54
        self.rst.x = 2    # viewer_types_page.nml:55
        self.rst.y = 3    # viewer_types_page.nml:56
        self.rst.width = 26    # viewer_types_page.nml:57
        self.rst.height = 1    # viewer_types_page.nml:58
        self.rst.items = _bind(    # viewer_types_page.nml:59
            lambda _o: [_tr('~r~eStructuredText')],
            yielding=True,
        )

        self.rst_masks.key = 'rst_masks'    # viewer_types_page.nml:63
        self.rst_masks.x = 28    # viewer_types_page.nml:64
        self.rst_masks.y = 3    # viewer_types_page.nml:65
        self.rst_masks.width = _bind(lambda _o: max(1, _o.parent.width - 30))    # viewer_types_page.nml:66

        self.html.key = 'render_html'    # viewer_types_page.nml:70
        self.html.x = 2    # viewer_types_page.nml:71
        self.html.y = 4    # viewer_types_page.nml:72
        self.html.width = 26    # viewer_types_page.nml:73
        self.html.height = 1    # viewer_types_page.nml:74
        self.html.items = _bind(lambda _o: [_tr('~H~TML')], yielding=True)    # viewer_types_page.nml:75

        self.html_masks.key = 'html_masks'    # viewer_types_page.nml:79
        self.html_masks.x = 28    # viewer_types_page.nml:80
        self.html_masks.y = 4    # viewer_types_page.nml:81
        self.html_masks.width = _bind(lambda _o: max(1, _o.parent.width - 30))    # viewer_types_page.nml:82

        self.pdf.key = 'render_pdf'    # viewer_types_page.nml:86
        self.pdf.x = 2    # viewer_types_page.nml:87
        self.pdf.y = 5    # viewer_types_page.nml:88
        self.pdf.width = 26    # viewer_types_page.nml:89
        self.pdf.height = 1    # viewer_types_page.nml:90
        self.pdf.items = _bind(lambda _o: [_tr('~P~DF')], yielding=True)    # viewer_types_page.nml:91

        self.pdf_masks.key = 'pdf_masks'    # viewer_types_page.nml:95
        self.pdf_masks.x = 28    # viewer_types_page.nml:96
        self.pdf_masks.y = 5    # viewer_types_page.nml:97
        self.pdf_masks.width = _bind(lambda _o: max(1, _o.parent.width - 30))    # viewer_types_page.nml:98

        self.images.key = 'render_images'    # viewer_types_page.nml:102
        self.images.x = 2    # viewer_types_page.nml:103
        self.images.y = 6    # viewer_types_page.nml:104
        self.images.width = 26    # viewer_types_page.nml:105
        self.images.height = 1    # viewer_types_page.nml:106
        self.images.items = _bind(    # viewer_types_page.nml:107
            lambda _o: [_tr('P~i~ctures')],
            yielding=True,
        )

        self.images_masks.key = 'image_masks'    # viewer_types_page.nml:111
        self.images_masks.x = 28    # viewer_types_page.nml:112
        self.images_masks.y = 6    # viewer_types_page.nml:113
        self.images_masks.width = _bind(    # viewer_types_page.nml:114
            lambda _o: max(1, _o.parent.width - 30)
        )

        self.tables.key = 'render_tables'    # viewer_types_page.nml:118
        self.tables.x = 2    # viewer_types_page.nml:119
        self.tables.y = 7    # viewer_types_page.nml:120
        self.tables.width = 26    # viewer_types_page.nml:121
        self.tables.height = 1    # viewer_types_page.nml:122
        self.tables.items = _bind(    # viewer_types_page.nml:123
            lambda _o: [_tr('~T~ables (CSV, TSV)')],
            yielding=True,
        )

        self.tables_masks.key = 'table_masks'    # viewer_types_page.nml:127
        self.tables_masks.x = 28    # viewer_types_page.nml:128
        self.tables_masks.y = 7    # viewer_types_page.nml:129
        self.tables_masks.width = _bind(    # viewer_types_page.nml:130
            lambda _o: max(1, _o.parent.width - 30)
        )

        self.structured.key = 'render_structured'    # viewer_types_page.nml:134
        self.structured.x = 2    # viewer_types_page.nml:135
        self.structured.y = 8    # viewer_types_page.nml:136
        self.structured.width = 26    # viewer_types_page.nml:137
        self.structured.height = 1    # viewer_types_page.nml:138
        self.structured.items = _bind(    # viewer_types_page.nml:139
            lambda _o: [_tr('~S~tructured, as a tree')],
            yielding=True,
        )

        self.structured_masks.key = 'structured_masks'    # viewer_types_page.nml:143
        self.structured_masks.x = 28    # viewer_types_page.nml:144
        self.structured_masks.y = 8    # viewer_types_page.nml:145
        self.structured_masks.width = _bind(    # viewer_types_page.nml:146
            lambda _o: max(1, _o.parent.width - 30)
        )

        self.database_caption.x = 6    # viewer_types_page.nml:152
        self.database_caption.y = 9    # viewer_types_page.nml:153
        self.database_caption.width = 22    # viewer_types_page.nml:154
        self.database_caption.text = _bind(    # viewer_types_page.nml:155
            lambda _o: _tr('SQ~L~ite databases'),
            yielding=True,
        )
        self.database_caption.link = _bind(lambda _o: self.database_masks)    # viewer_types_page.nml:156

        self.database_masks.key = 'database_masks'    # viewer_types_page.nml:160
        self.database_masks.x = 28    # viewer_types_page.nml:161
        self.database_masks.y = 9    # viewer_types_page.nml:162
        self.database_masks.width = _bind(    # viewer_types_page.nml:163
            lambda _o: max(1, _o.parent.width - 30)
        )

        self._navml_built(__class__)

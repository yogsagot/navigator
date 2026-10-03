# navml: generated
"""Generated from ``bookmark_label_dialog.nml``.

Do not edit: edit the markup and rerun ``python -m navml build``.
"""

from __future__ import annotations

#: Everything the generator needs for itself is underscored, so a document may
#: import any name at all without colliding with it -- there is no reserved
#: word.  A bare ``Label:`` head is what asks for ``_Component``; markup
#: never names it.  See *Importing another component* in navml/DESIGN.md.
from typing import Any as _Any

from navkit.reactive import bind as _bind

from navml.component import Component as _Component
from navml.widgets.dialog.dialog import Dialog    # bookmark_label_dialog.nml:1
from navml.widgets.dialog.field import Field    # bookmark_label_dialog.nml:2

__navml_component__ = "BookmarkLabelDialog"

__all__ = ["BookmarkLabelDialog"]


class BookmarkLabelDialog(Dialog, _Component):
    """F2 in the bookmarks box: the label shown in place of a bookmark's path.

    DN's ``InputBox`` shape, as F7's dialog is; a dialog of its own only because
    an empty answer here means "no label", where ``MkdirDialog`` answers None.
    """

    #: The document this class was generated from.
    __navml_source__ = "bookmark_label_dialog.nml"

    #: Ids, annotated so the hand-written half completes them.
    entry: Field    # bookmark_label_dialog.nml:16

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.entry = Field(parent=self)    # bookmark_label_dialog.nml:15

        self.modal_width = 48    # bookmark_label_dialog.nml:9
        self.modal_height = 8    # bookmark_label_dialog.nml:10
        self.title = 'Bookmark label'    # bookmark_label_dialog.nml:11
        self.close_on_outside_click = True    # bookmark_label_dialog.nml:13

        self.entry.x = 2    # bookmark_label_dialog.nml:17
        self.entry.y = 2    # bookmark_label_dialog.nml:18
        self.entry.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # bookmark_label_dialog.nml:19
        self.entry.height = 1    # bookmark_label_dialog.nml:20
        self.entry.label_text = '~L~abel'    # bookmark_label_dialog.nml:21
        self.entry.label_width = 8    # bookmark_label_dialog.nml:22

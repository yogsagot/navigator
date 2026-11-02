# navml: generated
"""Generated from ``miller_view.nml``.

Do not edit: edit the markup and rerun ``python -m navml build``.
"""

from __future__ import annotations

#: Everything the generator needs for itself is underscored, so a document may
#: import any name at all without colliding with it -- there is no reserved
#: word.  A bare ``Label:`` head is what asks for ``_Component``; markup
#: never names it.  See *Importing another component* in navml/DESIGN.md.
from typing import Any as _Any

from navml.component import Component as _Component
from navigator.widgets.viewer.quick_viewer import QuickViewer    # miller_view.nml:1

__navml_component__ = "MillerView"

__all__ = ["MillerView"]


class MillerView(_Component):
    """Miller columns (Alt+F12): the columns from the root down to the directory

    being browsed, and the preview after them.  The columns come and go with
    the chain (``open_at``, ``close``), so the markup holds only what is always
    there: the file half of the preview.
    """

    #: The document this class was generated from.
    __navml_source__ = "miller_view.nml"

    #: Ids, annotated so the hand-written half completes them.
    preview_file: QuickViewer    # miller_view.nml:12

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.preview_file = QuickViewer(parent=self)    # miller_view.nml:11

        self.preview_file.visible = False    # miller_view.nml:13

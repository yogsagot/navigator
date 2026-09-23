# navml: generated
"""Generated from ``mkdir_dialog.nml``.

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
from navml.widgets.dialog import Dialog    # mkdir_dialog.nml:1
from navml.widgets.field import Field    # mkdir_dialog.nml:2

__navml_component__ = "MkdirDialog"

__all__ = ["MkdirDialog"]


class MkdirDialog(Dialog, _Component):
    """F7: make a directory in the active panel.

    The smallest dialog Navigator actually wants, and the first one wired into
    the application -- an ``InputLine``, a ``Label`` that focuses it, the two
    buttons ``Dialog`` already has, and an answer that ends in a directory on
    disk.

    The size is set by *assigning the properties the base binds from*, never by
    assigning ``width`` -- a value over a live binding raises, and the binding
    is installed by ``super().__init__()`` before this document's own lines run.
    """

    #: The document this class was generated from.
    __navml_source__ = "mkdir_dialog.nml"

    #: Ids, annotated so the hand-written half completes them.
    entry: Field    # mkdir_dialog.nml:22

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.entry = Field(parent=self)    # mkdir_dialog.nml:19

        self.modal_width = 48    # mkdir_dialog.nml:15
        self.modal_height = 8    # mkdir_dialog.nml:16
        self.title = 'Make directory'    # mkdir_dialog.nml:17

        self.entry.x = 2    # mkdir_dialog.nml:23
        self.entry.y = 2    # mkdir_dialog.nml:24
        self.entry.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # mkdir_dialog.nml:25
        self.entry.height = 1    # mkdir_dialog.nml:26
        self.entry.label_text = '~N~ame'    # mkdir_dialog.nml:27
        self.entry.label_width = 7    # mkdir_dialog.nml:28

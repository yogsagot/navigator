# navml: generated
"""Generated from ``panel.nml``.

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
from navigator.settings import SETTINGS    # panel.nml:1
from navigator.widgets.manager.panel.option_items import PanelOptionStrip, panel_items    # panel.nml:2
from navml.widgets.dialog.list_viewer import ListViewer    # panel.nml:3

__navml_component__ = "Panel"

__all__ = ["Panel"]


class Panel(ListViewer, _Component):
    """One side of the desktop: a directory, listed (``TFilePanel``).  The listing,

    its model and its painting are the hand-written half's; the markup holds
    the one child a panel has of its own.
    """

    #: The document this class was generated from.
    __navml_source__ = "panel.nml"

    #: Ids, annotated so the hand-written half completes them.
    options: PanelOptionStrip    # panel.nml:15

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.options = PanelOptionStrip(parent=self)    # panel.nml:14

        self.options.name = 'options'    # panel.nml:16
        self.options.target = _bind(lambda _o: self)    # panel.nml:17
        self.options.items = _bind(lambda _o: panel_items(self))    # panel.nml:18
        self.options.room = _bind(lambda _o: _o.parent._options_room())    # panel.nml:19
        self.options.x = _bind(    # panel.nml:20
            lambda _o: max(0, _o.parent.width - 3 - _o.width)
        )
        self.options.y = _bind(lambda _o: max(0, _o.parent.height - 1))    # panel.nml:21
        self.options.width = _bind(lambda _o: _o.used_width)    # panel.nml:22
        self.options.height = 1    # panel.nml:23
        self.options.visible = _bind(    # panel.nml:24
            lambda _o: _o.parent.framed and _o.parent.error is None and SETTINGS.file_manager.show_options
        )

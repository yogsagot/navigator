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

from navkit.events import Event as _Event
from navkit.reactive import bind as _bind

from navml.component import Component as _Component
from navigator.settings import SETTINGS    # panel.nml:1
from navigator.widgets.manager.panel.option_items import PanelOptionStrip, panel_items    # panel.nml:2
from navml.widgets.dialog.list_viewer import ListViewer    # panel.nml:3
from navml.widgets.dialog.scroll_bar import ScrollBar    # panel.nml:4

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
    options: PanelOptionStrip    # panel.nml:16
    hbar: ScrollBar    # panel.nml:35

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_hbar_scroll(self, event: _Event) -> bool:    # panel.nml:35
        """``hbar`` raised an event whose handler is ``on_scroll``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.options = PanelOptionStrip(parent=self)    # panel.nml:15
        self.hbar = ScrollBar(parent=self)    # panel.nml:34

        self.options.name = 'options'    # panel.nml:17
        self.options.target = _bind(lambda _o: self)    # panel.nml:18
        self.options.items = _bind(lambda _o: panel_items(self))    # panel.nml:19
        self.options.room = _bind(lambda _o: _o.parent._options_room())    # panel.nml:20
        self.options.width = _bind(lambda _o: _o.used_width)    # panel.nml:21
        self.options.height = 1    # panel.nml:22
        self.options.visible = _bind(    # panel.nml:26
            lambda _o: _o.parent.framed and _o.parent.error is None and SETTINGS.file_manager.show_options
        )
        self.options.x = _bind(    # panel.nml:24
            lambda _o: max(0, _o.parent.width - 3 - _o.width)
        )
        self.options.y = _bind(lambda _o: max(0, _o.parent.height - _o.height))    # panel.nml:25

        self.hbar.orientation = 'horizontal'    # panel.nml:36
        self.hbar.x = 1    # panel.nml:37
        self.hbar.width = _bind(    # panel.nml:38
            lambda _o: max(0, (self.options.x - 1 if self.options.visible and self.options.width else _o.parent.width - 1) - _o.x)
        )
        self.hbar.height = 1    # panel.nml:39
        self.hbar.value = _bind(lambda _o: _o.parent.name_offset)    # panel.nml:42
        self.hbar.maximum = _bind(lambda _o: _o.parent.max_name_scroll)    # panel.nml:43
        self.hbar.page = _bind(lambda _o: max(1, _o.parent.name_room))    # panel.nml:44
        self.hbar.visible = _bind(    # panel.nml:45
            lambda _o: _o.parent.framed and _o.parent.error is None and (_o.parent.quick_search is None) and (_o.parent.view_mode != 'list') and (_o.parent.max_name_scroll > 0 or _o.parent.name_offset > 0) and (_o.width >= 4)
        )
        self.hbar.y = _bind(lambda _o: max(0, _o.parent.height - _o.height))    # panel.nml:41
        self.hbar.on_scroll = self.on_hbar_scroll    # panel.nml:35

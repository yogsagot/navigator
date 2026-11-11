# navml: generated
"""Generated from ``filter_dialog.nml``.

Do not edit: edit the markup and rerun ``python -m navml build``.
"""

from __future__ import annotations

#: Everything the generator needs for itself is underscored, so a document may
#: import any name at all without colliding with it -- there is no reserved
#: word.  A bare ``Label:`` head is what asks for ``_Component``; markup
#: never names it.  See *Importing another component* in navml/DESIGN.md.
from typing import Any as _Any

from navkit.events import Event as _Event
from navkit.i18n import tr as _tr
from navkit.reactive import bind as _bind

from navml.component import Component as _Component
from navigator.widgets.manager.filter_dialog.filter_list import FilterList    # filter_dialog.nml:1
from navml.widgets.dialog.button import Button    # filter_dialog.nml:2
from navml.widgets.dialog.button_row import ButtonRow    # filter_dialog.nml:3
from navml.widgets.dialog.dialog import Dialog    # filter_dialog.nml:4

__navml_component__ = "FilterDialog"

__all__ = ["FilterDialog"]


class FilterDialog(Dialog, _Component):
    """Alt+Del, Panel > Selection > Advanced filter: DOS Navigator's ``dlgAdvancedFilter``.

    The list of masks over *Show*, *Hide* and *Close*, as ``DN.DNR`` and
    ``MakeDialog`` laid them out, a column wider.  Help is left out.
    """

    #: The document this class was generated from.
    __navml_source__ = "filter_dialog.nml"

    #: Ids, annotated so the hand-written half completes them.
    masks: FilterList    # filter_dialog.nml:16
    show: Button    # filter_dialog.nml:34
    hide: Button    # filter_dialog.nml:40
    abandon: Button    # filter_dialog.nml:44

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_show_click(self, event: _Event) -> bool:    # filter_dialog.nml:34
        """``show`` raised an event whose handler is ``on_click``."""
        return False

    async def on_hide_click(self, event: _Event) -> bool:    # filter_dialog.nml:40
        """``hide`` raised an event whose handler is ``on_click``."""
        return False

    async def on_abandon_click(self, event: _Event) -> bool:    # filter_dialog.nml:44
        """``abandon`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.masks = FilterList(parent=self)    # filter_dialog.nml:15
        _w1 = ButtonRow(parent=self)    # filter_dialog.nml:24
        self.show = Button(parent=_w1)    # filter_dialog.nml:33
        self.hide = Button(parent=_w1)    # filter_dialog.nml:39
        self.abandon = Button(parent=self)    # filter_dialog.nml:43

        self.modal_width = 38    # filter_dialog.nml:11
        self.modal_height = 16    # filter_dialog.nml:12
        self.title = _bind(lambda _o: _tr('Filter'), yielding=True)    # filter_dialog.nml:13

        self.masks.x = 3    # filter_dialog.nml:18
        self.masks.width = _bind(lambda _o: max(0, _o.parent.width - 6))    # filter_dialog.nml:19
        self.masks.y = 2    # filter_dialog.nml:20
        self.masks.height = _bind(lambda _o: max(0, _o.parent.height - 7))    # filter_dialog.nml:21

        _w1.justify = 'start'    # filter_dialog.nml:25
        _w1.button_width = 10    # filter_dialog.nml:26
        _w1.spacing = 1    # filter_dialog.nml:27
        _w1.x = 2# filter_dialog.nml:29
        _w1.width = _bind(lambda _o: max(0, _o.parent.width - 2))    # filter_dialog.nml:30
        _w1.y = _bind(lambda _o: max(0, _o.parent.height - 2 - _o.height))    # filter_dialog.nml:31

        self.show.text = _bind(lambda _o: _tr('~S~how'), yielding=True)    # filter_dialog.nml:35
        self.show.default = True    # filter_dialog.nml:36
        self.show.on_click = self.on_show_click    # filter_dialog.nml:34

        self.hide.text = _bind(lambda _o: _tr('~H~ide'), yielding=True)    # filter_dialog.nml:41
        self.hide.on_click = self.on_hide_click    # filter_dialog.nml:40

        self.abandon.text = _bind(lambda _o: _tr('Close'), yielding=True)    # filter_dialog.nml:45
        self.abandon.x = 24    # filter_dialog.nml:46
        self.abandon.width = 11    # filter_dialog.nml:47
        self.abandon.height = 2    # filter_dialog.nml:48
        self.abandon.y = _bind(    # filter_dialog.nml:50
            lambda _o: max(0, _o.parent.height - 2 - _o.height)
        )
        self.abandon.on_click = self.on_abandon_click    # filter_dialog.nml:44

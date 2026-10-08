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
from navml.widgets.dialog.dialog import Dialog    # filter_dialog.nml:3

__navml_component__ = "FilterDialog"

__all__ = ["FilterDialog"]


class FilterDialog(Dialog, _Component):
    """Alt+Del, Panel > Advanced filter: DOS Navigator's ``dlgAdvancedFilter``.

    The list of masks over *Show*, *Hide* and *Close*, as ``DN.DNR`` and
    ``MakeDialog`` laid them out, a column wider.  Help is left out.
    """

    #: The document this class was generated from.
    __navml_source__ = "filter_dialog.nml"

    #: Ids, annotated so the hand-written half completes them.
    masks: FilterList    # filter_dialog.nml:15
    show: Button    # filter_dialog.nml:23
    hide: Button    # filter_dialog.nml:33
    abandon: Button    # filter_dialog.nml:41

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_show_click(self, event: _Event) -> bool:    # filter_dialog.nml:23
        """``show`` raised an event whose handler is ``on_click``."""
        return False

    async def on_hide_click(self, event: _Event) -> bool:    # filter_dialog.nml:33
        """``hide`` raised an event whose handler is ``on_click``."""
        return False

    async def on_abandon_click(self, event: _Event) -> bool:    # filter_dialog.nml:41
        """``abandon`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.masks = FilterList(parent=self)    # filter_dialog.nml:14
        self.show = Button(parent=self)    # filter_dialog.nml:22
        self.hide = Button(parent=self)    # filter_dialog.nml:32
        self.abandon = Button(parent=self)    # filter_dialog.nml:40

        self.modal_width = 38    # filter_dialog.nml:10
        self.modal_height = 16    # filter_dialog.nml:11
        self.title = _bind(lambda _o: _tr('Filter'), yielding=True)    # filter_dialog.nml:12

        self.masks.x = 3    # filter_dialog.nml:16
        self.masks.y = 2    # filter_dialog.nml:17
        self.masks.width = _bind(lambda _o: max(0, _o.parent.width - 6))    # filter_dialog.nml:18
        self.masks.height = _bind(lambda _o: max(0, _o.parent.height - 7))    # filter_dialog.nml:19

        self.show.text = _bind(lambda _o: _tr('~S~how'), yielding=True)    # filter_dialog.nml:24
        self.show.default = True    # filter_dialog.nml:25
        self.show.x = 2    # filter_dialog.nml:26
        self.show.y = _bind(lambda _o: max(0, _o.parent.height - 4))    # filter_dialog.nml:27
        self.show.width = 10    # filter_dialog.nml:28
        self.show.height = 2    # filter_dialog.nml:29
        self.show.on_click = self.on_show_click    # filter_dialog.nml:23

        self.hide.text = _bind(lambda _o: _tr('~H~ide'), yielding=True)    # filter_dialog.nml:34
        self.hide.x = 13    # filter_dialog.nml:35
        self.hide.y = _bind(lambda _o: max(0, _o.parent.height - 4))    # filter_dialog.nml:36
        self.hide.width = 10    # filter_dialog.nml:37
        self.hide.height = 2    # filter_dialog.nml:38
        self.hide.on_click = self.on_hide_click    # filter_dialog.nml:33

        self.abandon.text = _bind(lambda _o: _tr('Close'), yielding=True)    # filter_dialog.nml:42
        self.abandon.x = 24    # filter_dialog.nml:43
        self.abandon.y = _bind(lambda _o: max(0, _o.parent.height - 4))    # filter_dialog.nml:44
        self.abandon.width = 11    # filter_dialog.nml:45
        self.abandon.height = 2    # filter_dialog.nml:46
        self.abandon.on_click = self.on_abandon_click    # filter_dialog.nml:41

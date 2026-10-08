# navml: generated
"""Generated from ``file_history_dialog.nml``.

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
from navigator.widgets.shell.file_record_list import FileRecordList    # file_history_dialog.nml:1
from navml.widgets.dialog.button import Button    # file_history_dialog.nml:2
from navml.widgets.dialog.dialog import Dialog    # file_history_dialog.nml:3

__navml_component__ = "FileHistoryDialog"

__all__ = ["FileHistoryDialog"]


class FileHistoryDialog(Dialog, _Component):
    """Alt+PgDn and Alt+PgUp: DOS Navigator's ``dlgViewHistory`` and

    ``dlgEditHistory`` (``DN.DNR``), one document because the two are one
    layout -- a 59 by 17 dialog, the list ``GetDialog`` (``HISTRIES.PAS``)
    inserts from column 2 to the scroll bar at 56 and from row 2 to 12, and
    *Open*, *Delete record* and *Cancel* along row 14.  The title is the
    caller's.  ``Dialog``'s own row of buttons is not this layout's, and the
    hand-written half hides it.
    """

    #: The document this class was generated from.
    __navml_source__ = "file_history_dialog.nml"

    #: Ids, annotated so the hand-written half completes them.
    records: FileRecordList    # file_history_dialog.nml:17
    pick: Button    # file_history_dialog.nml:25
    drop: Button    # file_history_dialog.nml:35
    abandon: Button    # file_history_dialog.nml:43

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_records_chosen(self, event: _Event) -> bool:    # file_history_dialog.nml:17
        """``records`` raised an event whose handler is ``on_chosen``."""
        return False

    async def on_pick_click(self, event: _Event) -> bool:    # file_history_dialog.nml:25
        """``pick`` raised an event whose handler is ``on_click``."""
        return False

    async def on_drop_click(self, event: _Event) -> bool:    # file_history_dialog.nml:35
        """``drop`` raised an event whose handler is ``on_click``."""
        return False

    async def on_abandon_click(self, event: _Event) -> bool:    # file_history_dialog.nml:43
        """``abandon`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.records = FileRecordList(parent=self)    # file_history_dialog.nml:16
        self.pick = Button(parent=self)    # file_history_dialog.nml:24
        self.drop = Button(parent=self)    # file_history_dialog.nml:34
        self.abandon = Button(parent=self)    # file_history_dialog.nml:42

        self.modal_width = 59    # file_history_dialog.nml:13
        self.modal_height = 17    # file_history_dialog.nml:14

        self.records.framed = False    # file_history_dialog.nml:18
        self.records.x = 2    # file_history_dialog.nml:19
        self.records.y = 2    # file_history_dialog.nml:20
        self.records.width = 55    # file_history_dialog.nml:21
        self.records.height = 11    # file_history_dialog.nml:22
        self.records.on_chosen = self.on_records_chosen    # file_history_dialog.nml:17

        self.pick.text = _bind(lambda _o: _tr('~O~pen'), yielding=True)    # file_history_dialog.nml:26
        self.pick.default = True    # file_history_dialog.nml:27
        self.pick.x = 4    # file_history_dialog.nml:28
        self.pick.y = 14    # file_history_dialog.nml:29
        self.pick.width = 10    # file_history_dialog.nml:30
        self.pick.height = 2    # file_history_dialog.nml:31
        self.pick.on_click = self.on_pick_click    # file_history_dialog.nml:25

        self.drop.text = _bind(    # file_history_dialog.nml:36
            lambda _o: _tr('~D~elete record'),
            yielding=True,
        )
        self.drop.x = 21    # file_history_dialog.nml:37
        self.drop.y = 14    # file_history_dialog.nml:38
        self.drop.width = 17    # file_history_dialog.nml:39
        self.drop.height = 2    # file_history_dialog.nml:40
        self.drop.on_click = self.on_drop_click    # file_history_dialog.nml:35

        self.abandon.text = _bind(lambda _o: _tr('Cancel'), yielding=True)    # file_history_dialog.nml:44
        self.abandon.x = 44    # file_history_dialog.nml:45
        self.abandon.y = 14    # file_history_dialog.nml:46
        self.abandon.width = 10    # file_history_dialog.nml:47
        self.abandon.height = 2    # file_history_dialog.nml:48
        self.abandon.on_click = self.on_abandon_click    # file_history_dialog.nml:43

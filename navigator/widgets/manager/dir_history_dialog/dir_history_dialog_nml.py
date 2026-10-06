# navml: generated
"""Generated from ``dir_history_dialog.nml``.

Do not edit: edit the markup and rerun ``python -m navml build``.
"""

from __future__ import annotations

#: Everything the generator needs for itself is underscored, so a document may
#: import any name at all without colliding with it -- there is no reserved
#: word.  A bare ``Label:`` head is what asks for ``_Component``; markup
#: never names it.  See *Importing another component* in navml/DESIGN.md.
from typing import Any as _Any

from navkit.events import Event as _Event

from navml.component import Component as _Component
from navigator.widgets.manager.dir_history_dialog.dir_list import DirList    # dir_history_dialog.nml:1
from navml.widgets.dialog.button import Button    # dir_history_dialog.nml:2
from navml.widgets.dialog.dialog import Dialog    # dir_history_dialog.nml:3

__navml_component__ = "DirHistoryDialog"

__all__ = ["DirHistoryDialog"]


class DirHistoryDialog(Dialog, _Component):
    """Alt+Backspace, Panel > History of directories: DOS Navigator's

    ``dlgDirectoryHistory`` -- the directories the panels have been to, the
    last first, over *Go to*, *Delete record* and *Cancel*, where ``DN.DNR``
    put them.
    """

    #: The document this class was generated from.
    __navml_source__ = "dir_history_dialog.nml"

    #: Ids, annotated so the hand-written half completes them.
    places: DirList    # dir_history_dialog.nml:15
    pick: Button    # dir_history_dialog.nml:23
    drop: Button    # dir_history_dialog.nml:33
    abandon: Button    # dir_history_dialog.nml:41

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_places_chosen(self, event: _Event) -> bool:    # dir_history_dialog.nml:15
        """``places`` raised an event whose handler is ``on_chosen``."""
        return False

    async def on_pick_click(self, event: _Event) -> bool:    # dir_history_dialog.nml:23
        """``pick`` raised an event whose handler is ``on_click``."""
        return False

    async def on_drop_click(self, event: _Event) -> bool:    # dir_history_dialog.nml:33
        """``drop`` raised an event whose handler is ``on_click``."""
        return False

    async def on_abandon_click(self, event: _Event) -> bool:    # dir_history_dialog.nml:41
        """``abandon`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.places = DirList(parent=self)    # dir_history_dialog.nml:14
        self.pick = Button(parent=self)    # dir_history_dialog.nml:22
        self.drop = Button(parent=self)    # dir_history_dialog.nml:32
        self.abandon = Button(parent=self)    # dir_history_dialog.nml:40

        self.modal_width = 59    # dir_history_dialog.nml:10
        self.modal_height = 17    # dir_history_dialog.nml:11
        self.title = 'Directories History'    # dir_history_dialog.nml:12

        self.places.framed = False    # dir_history_dialog.nml:16
        self.places.x = 2    # dir_history_dialog.nml:17
        self.places.y = 2    # dir_history_dialog.nml:18
        self.places.width = 55    # dir_history_dialog.nml:19
        self.places.height = 11    # dir_history_dialog.nml:20
        self.places.on_chosen = self.on_places_chosen    # dir_history_dialog.nml:15

        self.pick.text = '~G~o to'    # dir_history_dialog.nml:24
        self.pick.default = True    # dir_history_dialog.nml:25
        self.pick.x = 4    # dir_history_dialog.nml:26
        self.pick.y = 14    # dir_history_dialog.nml:27
        self.pick.width = 11    # dir_history_dialog.nml:28
        self.pick.height = 2    # dir_history_dialog.nml:29
        self.pick.on_click = self.on_pick_click    # dir_history_dialog.nml:23

        self.drop.text = '~D~elete record'    # dir_history_dialog.nml:34
        self.drop.x = 21    # dir_history_dialog.nml:35
        self.drop.y = 14    # dir_history_dialog.nml:36
        self.drop.width = 17    # dir_history_dialog.nml:37
        self.drop.height = 2    # dir_history_dialog.nml:38
        self.drop.on_click = self.on_drop_click    # dir_history_dialog.nml:33

        self.abandon.text = 'Cancel'    # dir_history_dialog.nml:42
        self.abandon.x = 44    # dir_history_dialog.nml:43
        self.abandon.y = 14    # dir_history_dialog.nml:44
        self.abandon.width = 11    # dir_history_dialog.nml:45
        self.abandon.height = 2    # dir_history_dialog.nml:46
        self.abandon.on_click = self.on_abandon_click    # dir_history_dialog.nml:41

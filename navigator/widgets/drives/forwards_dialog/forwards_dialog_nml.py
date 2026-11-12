# navml: generated
"""Generated from ``forwards_dialog.nml``.

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

from navml.component import Component as _Component
from navml.widgets.dialog.button import Button    # forwards_dialog.nml:1
from navml.widgets.dialog.dialog import Dialog    # forwards_dialog.nml:2
from navml.widgets.dialog.label import Label    # forwards_dialog.nml:3
from navml.widgets.dialog.list_viewer import ListViewer    # forwards_dialog.nml:4

__navml_component__ = "ForwardsDialog"

__all__ = ["ForwardsDialog"]


class ForwardsDialog(Dialog, _Component):
    """The SSH link manager's *Forwards...*: a connection's port forwards, one a

    row, added, edited and deleted here and kept with the connection when the
    manager saves it.  Ours: DN's link was a cable.  The list on the left, the
    buttons down the right as *Saved links* has them, OK and Cancel under.
    """

    #: The document this class was generated from.
    __navml_source__ = "forwards_dialog.nml"

    #: Ids, annotated so the hand-written half completes them.
    forwards_caption: Label    # forwards_dialog.nml:16
    forwards: ListViewer    # forwards_dialog.nml:24
    append: Button    # forwards_dialog.nml:31
    edit: Button    # forwards_dialog.nml:40
    delete: Button    # forwards_dialog.nml:49

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.forwards_caption = Label(parent=self)    # forwards_dialog.nml:15
        self.forwards = ListViewer(parent=self)    # forwards_dialog.nml:23
        self.append = Button(parent=self)    # forwards_dialog.nml:30
        self.edit = Button(parent=self)    # forwards_dialog.nml:39
        self.delete = Button(parent=self)    # forwards_dialog.nml:48

        self.modal_width = 66    # forwards_dialog.nml:11
        self.modal_height = 17    # forwards_dialog.nml:12
        self.title = _bind(lambda _o: _tr('Port forwards'), yielding=True)    # forwards_dialog.nml:13

        self.forwards_caption.x = 2    # forwards_dialog.nml:17
        self.forwards_caption.y = 1    # forwards_dialog.nml:18
        self.forwards_caption.width = 20    # forwards_dialog.nml:19
        self.forwards_caption.text = _bind(    # forwards_dialog.nml:20
            lambda _o: _tr('~F~orwards'),
            yielding=True,
        )
        self.forwards_caption.link = _bind(lambda _o: self.forwards)    # forwards_dialog.nml:21

        self.forwards.x = 2    # forwards_dialog.nml:25
        self.forwards.y = 2    # forwards_dialog.nml:26
        self.forwards.width = 48    # forwards_dialog.nml:27
        self.forwards.height = 10    # forwards_dialog.nml:28

        self.append.text = _bind(lambda _o: _tr('~A~dd...'), yielding=True)    # forwards_dialog.nml:32
        self.append.x = 52    # forwards_dialog.nml:33
        self.append.y = 2    # forwards_dialog.nml:34
        self.append.width = 12    # forwards_dialog.nml:35
        self.append.height = 2    # forwards_dialog.nml:36

        async def _on_click(event):    # forwards_dialog.nml:37
            self.spawn(self.add_forward())
            return True
        self.append.on_click = _on_click

        self.edit.text = _bind(lambda _o: _tr('~E~dit...'), yielding=True)    # forwards_dialog.nml:41
        self.edit.x = 52    # forwards_dialog.nml:42
        self.edit.y = 4    # forwards_dialog.nml:43
        self.edit.width = 12    # forwards_dialog.nml:44
        self.edit.height = 2    # forwards_dialog.nml:45

        async def _on_click(event):    # forwards_dialog.nml:46
            self.spawn(self.edit_forward())
            return True
        self.edit.on_click = _on_click

        self.delete.text = _bind(lambda _o: _tr('~D~elete'), yielding=True)    # forwards_dialog.nml:50
        self.delete.x = 52    # forwards_dialog.nml:51
        self.delete.y = 6    # forwards_dialog.nml:52
        self.delete.width = 12    # forwards_dialog.nml:53
        self.delete.height = 2    # forwards_dialog.nml:54

        async def _on_click(event):    # forwards_dialog.nml:55
            self.spawn(self.delete_forward())
            return True
        self.delete.on_click = _on_click

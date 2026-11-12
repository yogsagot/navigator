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

from navkit.events import Event as _Event
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
    edit: Button    # forwards_dialog.nml:39
    delete: Button    # forwards_dialog.nml:47

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_append_click(self, event: _Event) -> bool:    # forwards_dialog.nml:31
        """``append`` raised an event whose handler is ``on_click``."""
        return False

    async def on_edit_click(self, event: _Event) -> bool:    # forwards_dialog.nml:39
        """``edit`` raised an event whose handler is ``on_click``."""
        return False

    async def on_delete_click(self, event: _Event) -> bool:    # forwards_dialog.nml:47
        """``delete`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.forwards_caption = Label(parent=self)    # forwards_dialog.nml:15
        self.forwards = ListViewer(parent=self)    # forwards_dialog.nml:23
        self.append = Button(parent=self)    # forwards_dialog.nml:30
        self.edit = Button(parent=self)    # forwards_dialog.nml:38
        self.delete = Button(parent=self)    # forwards_dialog.nml:46

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
        self.append.on_click = self.on_append_click    # forwards_dialog.nml:31

        self.edit.text = _bind(lambda _o: _tr('~E~dit...'), yielding=True)    # forwards_dialog.nml:40
        self.edit.x = 52    # forwards_dialog.nml:41
        self.edit.y = 4    # forwards_dialog.nml:42
        self.edit.width = 12    # forwards_dialog.nml:43
        self.edit.height = 2    # forwards_dialog.nml:44
        self.edit.on_click = self.on_edit_click    # forwards_dialog.nml:39

        self.delete.text = _bind(lambda _o: _tr('~D~elete'), yielding=True)    # forwards_dialog.nml:48
        self.delete.x = 52    # forwards_dialog.nml:49
        self.delete.y = 6    # forwards_dialog.nml:50
        self.delete.width = 12    # forwards_dialog.nml:51
        self.delete.height = 2    # forwards_dialog.nml:52
        self.delete.on_click = self.on_delete_click    # forwards_dialog.nml:47

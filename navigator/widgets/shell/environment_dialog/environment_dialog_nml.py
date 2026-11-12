# navml: generated
"""Generated from ``environment_dialog.nml``.

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
from navml.widgets.dialog.button import Button    # environment_dialog.nml:1
from navml.widgets.dialog.dialog import Dialog    # environment_dialog.nml:2
from navml.widgets.dialog.field import Field    # environment_dialog.nml:3
from navml.widgets.dialog.label import Label    # environment_dialog.nml:4
from navml.widgets.dialog.list_viewer import ListViewer    # environment_dialog.nml:5

__navml_component__ = "EnvironmentDialog"

__all__ = ["EnvironmentDialog"]


class EnvironmentDialog(Dialog, _Component):
    """Utilities > Edit environment: DOS Navigator's ``dlgEditEnvironment``.

    The names on the left, the focused one's value on the line under them,
    and OK, *Rename*, *Append*, *Delete* and Cancel down the right, as
    ``DN.DNR`` and ``MakeDialog`` laid them out, a little larger.  The title
    drops DN's *DOS*.  Help is left out.
    """

    #: The document this class was generated from.
    __navml_source__ = "environment_dialog.nml"

    #: Ids, annotated so the hand-written half completes them.
    names_caption: Label    # environment_dialog.nml:22
    names: ListViewer    # environment_dialog.nml:31
    value: Field    # environment_dialog.nml:40
    pick: Button    # environment_dialog.nml:49
    rename: Button    # environment_dialog.nml:60
    append: Button    # environment_dialog.nml:70
    delete: Button    # environment_dialog.nml:80
    abandon: Button    # environment_dialog.nml:89

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_abandon_click(self, event: _Event) -> bool:    # environment_dialog.nml:89
        """``abandon`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.names_caption = Label(parent=self)    # environment_dialog.nml:21
        self.names = ListViewer(parent=self)    # environment_dialog.nml:30
        self.value = Field(parent=self)    # environment_dialog.nml:39
        self.pick = Button(parent=self)    # environment_dialog.nml:48
        self.rename = Button(parent=self)    # environment_dialog.nml:59
        self.append = Button(parent=self)    # environment_dialog.nml:69
        self.delete = Button(parent=self)    # environment_dialog.nml:79
        self.abandon = Button(parent=self)    # environment_dialog.nml:88

        self.modal_width = 62    # environment_dialog.nml:14
        self.modal_height = 20    # environment_dialog.nml:15
        self.title = _bind(    # environment_dialog.nml:16
            lambda _o: _tr('Environment Variables Editor'),
            yielding=True,
        )
        self.buttons = 'none'    # environment_dialog.nml:17
        self.buttons_row = _bind(    # environment_dialog.nml:19
            lambda _o: (self.pick, self.rename, self.append, self.delete, self.abandon)
        )

        self.names_caption.x = 2    # environment_dialog.nml:23
        self.names_caption.y = 1    # environment_dialog.nml:24
        self.names_caption.width = 12    # environment_dialog.nml:25
        self.names_caption.text = _bind(    # environment_dialog.nml:26
            lambda _o: _tr('~V~ariables'),
            yielding=True,
        )
        self.names_caption.link = _bind(lambda _o: self.names)    # environment_dialog.nml:27

        self.names.x = 2    # environment_dialog.nml:32
        self.names.y = 2    # environment_dialog.nml:33
        self.names.width = 45    # environment_dialog.nml:34
        self.names.height = 13    # environment_dialog.nml:35

        self.value.y = 16    # environment_dialog.nml:41
        self.value.label_text = _bind(lambda _o: _tr('Val~u~e'), yielding=True)    # environment_dialog.nml:45
        self.value.label_width = 7    # environment_dialog.nml:46
        self.value.x = 2    # environment_dialog.nml:43
        self.value.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # environment_dialog.nml:44

        self.pick.text = _bind(lambda _o: _tr('O~K~'), yielding=True)    # environment_dialog.nml:50
        self.pick.default = True    # environment_dialog.nml:51
        self.pick.x = 49    # environment_dialog.nml:52
        self.pick.y = 2    # environment_dialog.nml:53
        self.pick.width = 11    # environment_dialog.nml:54
        self.pick.height = 2    # environment_dialog.nml:55

        async def _on_click(event):    # environment_dialog.nml:56
            self.close(self.accept())
            return True
        self.pick.on_click = _on_click

        self.rename.text = _bind(lambda _o: _tr('~R~ename'), yielding=True)    # environment_dialog.nml:61
        self.rename.x = 49    # environment_dialog.nml:62
        self.rename.y = 4    # environment_dialog.nml:63
        self.rename.width = 11    # environment_dialog.nml:64
        self.rename.height = 2    # environment_dialog.nml:65

        async def _on_click(event):    # environment_dialog.nml:66
            self.spawn(self.rename_variable())
            return True
        self.rename.on_click = _on_click

        self.append.text = _bind(lambda _o: _tr('~A~ppend'), yielding=True)    # environment_dialog.nml:71
        self.append.x = 49    # environment_dialog.nml:72
        self.append.y = 6    # environment_dialog.nml:73
        self.append.width = 11    # environment_dialog.nml:74
        self.append.height = 2    # environment_dialog.nml:75

        async def _on_click(event):    # environment_dialog.nml:76
            self.spawn(self.append_variable())
            return True
        self.append.on_click = _on_click

        self.delete.text = _bind(lambda _o: _tr('~D~elete'), yielding=True)    # environment_dialog.nml:81
        self.delete.x = 49    # environment_dialog.nml:82
        self.delete.y = 8    # environment_dialog.nml:83
        self.delete.width = 11    # environment_dialog.nml:84
        self.delete.height = 2    # environment_dialog.nml:85

        async def _on_click(event):    # environment_dialog.nml:86
            self.spawn(self.delete_variable())
            return True
        self.delete.on_click = _on_click

        self.abandon.text = _bind(lambda _o: _tr('Cancel'), yielding=True)    # environment_dialog.nml:90
        self.abandon.x = 49    # environment_dialog.nml:91
        self.abandon.y = 10    # environment_dialog.nml:92
        self.abandon.width = 11    # environment_dialog.nml:93
        self.abandon.height = 2    # environment_dialog.nml:94
        self.abandon.on_click = self.on_abandon_click    # environment_dialog.nml:89

        self._navml_built(__class__)

# navml: generated
"""Generated from ``links_dialog.nml``.

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
from navigator.widgets.drives.commands import AddLink, DeleteLink, EditLink, MoveLinkDown, MoveLinkUp    # links_dialog.nml:1
from navigator.widgets.drives.links_dialog.link_list import LinkList    # links_dialog.nml:2
from navml.widgets.dialog.button import Button    # links_dialog.nml:3
from navml.widgets.dialog.dialog import Dialog    # links_dialog.nml:4
from navml.widgets.dialog.label import Label    # links_dialog.nml:5

__navml_component__ = "LinksDialog"

__all__ = ["LinksDialog"]


class LinksDialog(Dialog, _Component):
    """Utilities > Saved links: the connection profiles in one box, to edit,

    add, delete, reorder -- and connect to.  Ours: DN's link was one cable,
    with nothing to keep.  Laid out as *Edit environment* is, the list on the
    left and the buttons down the right; what is done is kept on OK only.
    """

    #: The document this class was generated from.
    __navml_source__ = "links_dialog.nml"

    #: The keys this component binds, read through key_table().
    keys = {    # links_dialog.nml:17
        'insert': AddLink,    # links_dialog.nml:18
        'f2': EditLink,    # links_dialog.nml:19
        'delete': DeleteLink,    # links_dialog.nml:20
        'ctrl+up': MoveLinkUp,    # links_dialog.nml:21
        'ctrl+down': MoveLinkDown,    # links_dialog.nml:22
    }

    #: Ids, annotated so the hand-written half completes them.
    links_caption: Label    # links_dialog.nml:25
    links: LinkList    # links_dialog.nml:33
    connect: Button    # links_dialog.nml:40
    edit: Button    # links_dialog.nml:49
    append: Button    # links_dialog.nml:58
    delete: Button    # links_dialog.nml:67
    pick: Button    # links_dialog.nml:76
    abandon: Button    # links_dialog.nml:85

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_connect_click(self, event: _Event) -> bool:    # links_dialog.nml:40
        """``connect`` raised an event whose handler is ``on_click``."""
        return False

    async def on_abandon_click(self, event: _Event) -> bool:    # links_dialog.nml:85
        """``abandon`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.links_caption = Label(parent=self)    # links_dialog.nml:24
        self.links = LinkList(parent=self)    # links_dialog.nml:32
        self.connect = Button(parent=self)    # links_dialog.nml:39
        self.edit = Button(parent=self)    # links_dialog.nml:48
        self.append = Button(parent=self)    # links_dialog.nml:57
        self.delete = Button(parent=self)    # links_dialog.nml:66
        self.pick = Button(parent=self)    # links_dialog.nml:75
        self.abandon = Button(parent=self)    # links_dialog.nml:84

        self.modal_width = 70    # links_dialog.nml:12
        self.modal_height = 18    # links_dialog.nml:13
        self.title = _bind(lambda _o: _tr('Saved links'), yielding=True)    # links_dialog.nml:14
        self.buttons = 'none'    # links_dialog.nml:15

        self.links_caption.x = 2    # links_dialog.nml:26
        self.links_caption.y = 1    # links_dialog.nml:27
        self.links_caption.width = 12    # links_dialog.nml:28
        self.links_caption.text = _bind(    # links_dialog.nml:29
            lambda _o: _tr('~L~inks'),
            yielding=True,
        )
        self.links_caption.link = _bind(lambda _o: self.links)    # links_dialog.nml:30

        self.links.x = 2    # links_dialog.nml:34
        self.links.y = 2    # links_dialog.nml:35
        self.links.width = 52    # links_dialog.nml:36
        self.links.height = 13    # links_dialog.nml:37

        self.connect.text = _bind(lambda _o: _tr('~C~onnect'), yielding=True)    # links_dialog.nml:41
        self.connect.default = True    # links_dialog.nml:42
        self.connect.x = 56    # links_dialog.nml:43
        self.connect.y = 2    # links_dialog.nml:44
        self.connect.width = 12    # links_dialog.nml:45
        self.connect.height = 2    # links_dialog.nml:46
        self.connect.on_click = self.on_connect_click    # links_dialog.nml:40

        self.edit.text = _bind(lambda _o: _tr('~E~dit...'), yielding=True)    # links_dialog.nml:50
        self.edit.x = 56    # links_dialog.nml:51
        self.edit.y = 4    # links_dialog.nml:52
        self.edit.width = 12    # links_dialog.nml:53
        self.edit.height = 2    # links_dialog.nml:54

        async def _on_click(event):    # links_dialog.nml:55
            self.spawn(self.edit_link())
            return True
        self.edit.on_click = _on_click

        self.append.text = _bind(lambda _o: _tr('~A~dd...'), yielding=True)    # links_dialog.nml:59
        self.append.x = 56    # links_dialog.nml:60
        self.append.y = 6    # links_dialog.nml:61
        self.append.width = 12    # links_dialog.nml:62
        self.append.height = 2    # links_dialog.nml:63

        async def _on_click(event):    # links_dialog.nml:64
            self.spawn(self.add_link())
            return True
        self.append.on_click = _on_click

        self.delete.text = _bind(lambda _o: _tr('~D~elete'), yielding=True)    # links_dialog.nml:68
        self.delete.x = 56    # links_dialog.nml:69
        self.delete.y = 8    # links_dialog.nml:70
        self.delete.width = 12    # links_dialog.nml:71
        self.delete.height = 2    # links_dialog.nml:72

        async def _on_click(event):    # links_dialog.nml:73
            self.spawn(self.delete_link())
            return True
        self.delete.on_click = _on_click

        self.pick.text = _bind(lambda _o: _tr('O~K~'), yielding=True)    # links_dialog.nml:77
        self.pick.x = 56    # links_dialog.nml:78
        self.pick.y = 11    # links_dialog.nml:79
        self.pick.width = 12    # links_dialog.nml:80
        self.pick.height = 2    # links_dialog.nml:81

        async def _on_click(event):    # links_dialog.nml:82
            self.close(self.accept())
            return True
        self.pick.on_click = _on_click

        self.abandon.text = _bind(lambda _o: _tr('Cancel'), yielding=True)    # links_dialog.nml:86
        self.abandon.x = 56    # links_dialog.nml:87
        self.abandon.y = 13    # links_dialog.nml:88
        self.abandon.width = 12    # links_dialog.nml:89
        self.abandon.height = 2    # links_dialog.nml:90
        self.abandon.on_click = self.on_abandon_click    # links_dialog.nml:85

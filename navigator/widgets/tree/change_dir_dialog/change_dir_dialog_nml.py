# navml: generated
"""Generated from ``change_dir_dialog.nml``.

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
from navml.widgets.dialog.button import Button    # change_dir_dialog.nml:1
from navml.widgets.dialog.dialog import Dialog    # change_dir_dialog.nml:2
from navml.widgets.dialog.static_text import StaticText    # change_dir_dialog.nml:3
from navml.widgets.dialog.tree_view import TreeView    # change_dir_dialog.nml:4

__navml_component__ = "ChangeDirDialog"

__all__ = ["ChangeDirDialog"]


class ChangeDirDialog(Dialog, _Component):
    """Panel > Change directory (Alt+T): DOS Navigator's ``TTreeDialog``, which

    ``ChangeDir`` opens as *Choose Directory*.

    Every rectangle is ``TTreeDialog.Init``'s, in a 49 by 17 dialog: the tree
    fills the left of it with no frame of its own -- the dialog's is its frame,
    and its scroll bar is its last column -- the path under the cursor is the
    one row beneath it, and the buttons stand in a column on the right, eleven
    wide, three rows apart.  ``Dialog``'s own row of buttons along the bottom is
    not this dialog's, and the hand-written half hides it.
    """

    #: The document this class was generated from.
    __navml_source__ = "change_dir_dialog.nml"

    #: Ids, annotated so the hand-written half completes them.
    tree: TreeView    # change_dir_dialog.nml:21
    where: StaticText    # change_dir_dialog.nml:31
    pick: Button    # change_dir_dialog.nml:40
    drive: Button    # change_dir_dialog.nml:51
    reread: Button    # change_dir_dialog.nml:60
    mkdir: Button    # change_dir_dialog.nml:68
    abandon: Button    # change_dir_dialog.nml:76

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_tree_chosen(self, event: _Event) -> bool:    # change_dir_dialog.nml:21
        """``tree`` raised an event whose handler is ``on_chosen``."""
        return False

    async def on_pick_click(self, event: _Event) -> bool:    # change_dir_dialog.nml:40
        """``pick`` raised an event whose handler is ``on_click``."""
        return False

    async def on_drive_click(self, event: _Event) -> bool:    # change_dir_dialog.nml:51
        """``drive`` raised an event whose handler is ``on_click``."""
        return False

    async def on_reread_click(self, event: _Event) -> bool:    # change_dir_dialog.nml:60
        """``reread`` raised an event whose handler is ``on_click``."""
        return False

    async def on_mkdir_click(self, event: _Event) -> bool:    # change_dir_dialog.nml:68
        """``mkdir`` raised an event whose handler is ``on_click``."""
        return False

    async def on_abandon_click(self, event: _Event) -> bool:    # change_dir_dialog.nml:76
        """``abandon`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.tree = TreeView(parent=self)    # change_dir_dialog.nml:20
        self.where = StaticText(parent=self)    # change_dir_dialog.nml:30
        self.pick = Button(parent=self)    # change_dir_dialog.nml:39
        self.drive = Button(parent=self)    # change_dir_dialog.nml:50
        self.reread = Button(parent=self)    # change_dir_dialog.nml:59
        self.mkdir = Button(parent=self)    # change_dir_dialog.nml:67
        self.abandon = Button(parent=self)    # change_dir_dialog.nml:75

        self.modal_width = 49    # change_dir_dialog.nml:16
        self.modal_height = 17    # change_dir_dialog.nml:17
        self.title = 'Choose Directory'    # change_dir_dialog.nml:18

        self.tree.framed = False    # change_dir_dialog.nml:22
        self.tree.x = 1    # change_dir_dialog.nml:23
        self.tree.y = 1    # change_dir_dialog.nml:24
        self.tree.width = 34    # change_dir_dialog.nml:25
        self.tree.height = 14    # change_dir_dialog.nml:26
        self.tree.on_chosen = self.on_tree_chosen    # change_dir_dialog.nml:21

        self.where.name = 'info'    # change_dir_dialog.nml:32
        self.where.x = 1    # change_dir_dialog.nml:33
        self.where.y = 15    # change_dir_dialog.nml:34
        self.where.width = 33    # change_dir_dialog.nml:35
        self.where.height = 1    # change_dir_dialog.nml:36
        self.where.text = _bind(    # change_dir_dialog.nml:37
            lambda _o: ' ' + str(self.tree.selected_node.data) if self.tree.selected_node is not None else ''
        )

        self.pick.text = 'O~K~'    # change_dir_dialog.nml:41
        self.pick.default = True    # change_dir_dialog.nml:42
        self.pick.x = 36    # change_dir_dialog.nml:43
        self.pick.y = 2    # change_dir_dialog.nml:44
        self.pick.width = 11    # change_dir_dialog.nml:45
        self.pick.height = 2    # change_dir_dialog.nml:46
        self.pick.on_click = self.on_pick_click    # change_dir_dialog.nml:40

        self.drive.text = '~D~rive...'    # change_dir_dialog.nml:52
        self.drive.disabled = True    # change_dir_dialog.nml:53
        self.drive.x = 36    # change_dir_dialog.nml:54
        self.drive.y = 5    # change_dir_dialog.nml:55
        self.drive.width = 11    # change_dir_dialog.nml:56
        self.drive.height = 2    # change_dir_dialog.nml:57
        self.drive.on_click = self.on_drive_click    # change_dir_dialog.nml:51

        self.reread.text = '~R~e-read'    # change_dir_dialog.nml:61
        self.reread.x = 36    # change_dir_dialog.nml:62
        self.reread.y = 8    # change_dir_dialog.nml:63
        self.reread.width = 11    # change_dir_dialog.nml:64
        self.reread.height = 2    # change_dir_dialog.nml:65
        self.reread.on_click = self.on_reread_click    # change_dir_dialog.nml:60

        self.mkdir.text = '~M~kDir'    # change_dir_dialog.nml:69
        self.mkdir.x = 36    # change_dir_dialog.nml:70
        self.mkdir.y = 11    # change_dir_dialog.nml:71
        self.mkdir.width = 11    # change_dir_dialog.nml:72
        self.mkdir.height = 2    # change_dir_dialog.nml:73
        self.mkdir.on_click = self.on_mkdir_click    # change_dir_dialog.nml:68

        self.abandon.text = 'Cancel'    # change_dir_dialog.nml:77
        self.abandon.x = 36    # change_dir_dialog.nml:78
        self.abandon.y = 14    # change_dir_dialog.nml:79
        self.abandon.width = 11    # change_dir_dialog.nml:80
        self.abandon.height = 2    # change_dir_dialog.nml:81
        self.abandon.on_click = self.on_abandon_click    # change_dir_dialog.nml:76

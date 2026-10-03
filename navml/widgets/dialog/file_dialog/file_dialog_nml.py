# navml: generated
"""Generated from ``file_dialog.nml``.

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
from navml.widgets.dialog.button import Button    # file_dialog.nml:1
from navml.widgets.dialog.dialog import Dialog    # file_dialog.nml:2
from navml.widgets.dialog.field import Field    # file_dialog.nml:3
from navml.widgets.dialog.file_list import FileInfoPane, FileList    # file_dialog.nml:4
from navml.widgets.dialog.label import Label    # file_dialog.nml:5

__navml_component__ = "FileDialog"

__all__ = ["FileDialog"]


class FileDialog(Dialog, _Component):
    """DOS Navigator's ``TFileDialog`` (``DNSTDDLG.PAS``), as ``GetFileNameDialog``

    built it with OK and Help.

    Every rectangle is ``TFileDialog.Init``'s, a 47 by 19 dialog: the name line
    from column 3 with its label over it and the history button after it, the
    *Files* and *Directories* lists side by side from row 6, nine rows deep,
    each with its scroll bar as its last column, the buttons down the right ten
    wide and three rows apart, and the info pane over rows 16 and 17.
    ``Dialog``'s own row of buttons and its message are not this layout, and
    the hand-written half hides them.
    """

    #: The document this class was generated from.
    __navml_source__ = "file_dialog.nml"

    #: Ids, annotated so the hand-written half completes them.
    caption: Label    # file_dialog.nml:24
    target: Field    # file_dialog.nml:33
    files_caption: Label    # file_dialog.nml:42
    files: FileList    # file_dialog.nml:51
    dirs_caption: Label    # file_dialog.nml:59
    dirs: FileList    # file_dialog.nml:68
    pick: Button    # file_dialog.nml:78
    abandon: Button    # file_dialog.nml:87
    helper: Button    # file_dialog.nml:96
    info: FileInfoPane    # file_dialog.nml:105

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_files_chosen(self, event: _Event) -> bool:    # file_dialog.nml:51
        """``files`` raised an event whose handler is ``on_chosen``."""
        return False

    async def on_dirs_chosen(self, event: _Event) -> bool:    # file_dialog.nml:68
        """``dirs`` raised an event whose handler is ``on_chosen``."""
        return False

    async def on_pick_click(self, event: _Event) -> bool:    # file_dialog.nml:78
        """``pick`` raised an event whose handler is ``on_click``."""
        return False

    async def on_abandon_click(self, event: _Event) -> bool:    # file_dialog.nml:87
        """``abandon`` raised an event whose handler is ``on_click``."""
        return False

    async def on_helper_click(self, event: _Event) -> bool:    # file_dialog.nml:96
        """``helper`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.caption = Label(parent=self)    # file_dialog.nml:23
        self.target = Field(parent=self)    # file_dialog.nml:32
        self.files_caption = Label(parent=self)    # file_dialog.nml:41
        self.files = FileList(parent=self)    # file_dialog.nml:50
        self.dirs_caption = Label(parent=self)    # file_dialog.nml:58
        self.dirs = FileList(parent=self)    # file_dialog.nml:67
        self.pick = Button(parent=self)    # file_dialog.nml:77
        self.abandon = Button(parent=self)    # file_dialog.nml:86
        self.helper = Button(parent=self)    # file_dialog.nml:95
        self.info = FileInfoPane(parent=self)    # file_dialog.nml:104

        self.modal_width = 47    # file_dialog.nml:18
        self.modal_height = 19    # file_dialog.nml:19
        self.title = 'Open file'    # file_dialog.nml:20

        self.caption.text = '~N~ame'    # file_dialog.nml:25
        self.caption.link = _bind(lambda _o: self.target.entry)    # file_dialog.nml:26
        self.caption.x = 2    # file_dialog.nml:27
        self.caption.y = 2    # file_dialog.nml:28
        self.caption.width = 29    # file_dialog.nml:29
        self.caption.height = 1    # file_dialog.nml:30

        self.target.x = 3    # file_dialog.nml:34
        self.target.y = 3    # file_dialog.nml:35
        self.target.width = 31    # file_dialog.nml:36
        self.target.height = 1    # file_dialog.nml:37
        self.target.label_text = ''    # file_dialog.nml:38
        self.target.label_width = 0    # file_dialog.nml:39

        self.files_caption.text = '~F~iles'    # file_dialog.nml:43
        self.files_caption.link = _bind(lambda _o: self.files)    # file_dialog.nml:44
        self.files_caption.x = 2    # file_dialog.nml:45
        self.files_caption.y = 5    # file_dialog.nml:46
        self.files_caption.width = 15    # file_dialog.nml:47
        self.files_caption.height = 1    # file_dialog.nml:48

        self.files.framed = False    # file_dialog.nml:52
        self.files.x = 3    # file_dialog.nml:53
        self.files.y = 6    # file_dialog.nml:54
        self.files.width = 15    # file_dialog.nml:55
        self.files.height = 9    # file_dialog.nml:56
        self.files.on_chosen = self.on_files_chosen    # file_dialog.nml:51

        self.dirs_caption.text = '~D~irectories'    # file_dialog.nml:60
        self.dirs_caption.link = _bind(lambda _o: self.dirs)    # file_dialog.nml:61
        self.dirs_caption.x = 19    # file_dialog.nml:62
        self.dirs_caption.y = 5    # file_dialog.nml:63
        self.dirs_caption.width = 15    # file_dialog.nml:64
        self.dirs_caption.height = 1    # file_dialog.nml:65

        self.dirs.framed = False    # file_dialog.nml:69
        self.dirs.x = 20    # file_dialog.nml:70
        self.dirs.y = 6    # file_dialog.nml:71
        self.dirs.width = 15    # file_dialog.nml:72
        self.dirs.height = 9    # file_dialog.nml:73
        self.dirs.on_chosen = self.on_dirs_chosen    # file_dialog.nml:68

        self.pick.text = 'O~K~'    # file_dialog.nml:79
        self.pick.default = True    # file_dialog.nml:80
        self.pick.x = 35    # file_dialog.nml:81
        self.pick.y = 3    # file_dialog.nml:82
        self.pick.width = 10    # file_dialog.nml:83
        self.pick.height = 2    # file_dialog.nml:84
        self.pick.on_click = self.on_pick_click    # file_dialog.nml:78

        self.abandon.text = 'Cancel'    # file_dialog.nml:88
        self.abandon.x = 35    # file_dialog.nml:89
        self.abandon.y = 6    # file_dialog.nml:90
        self.abandon.width = 10    # file_dialog.nml:91
        self.abandon.height = 2    # file_dialog.nml:92
        self.abandon.on_click = self.on_abandon_click    # file_dialog.nml:87

        self.helper.text = '~H~elp'    # file_dialog.nml:97
        self.helper.disabled = True    # file_dialog.nml:98
        self.helper.x = 35    # file_dialog.nml:99
        self.helper.y = 9    # file_dialog.nml:100
        self.helper.width = 10    # file_dialog.nml:101
        self.helper.height = 2    # file_dialog.nml:102
        self.helper.on_click = self.on_helper_click    # file_dialog.nml:96

        self.info.x = 1    # file_dialog.nml:106
        self.info.y = 16    # file_dialog.nml:107
        self.info.width = 45    # file_dialog.nml:108
        self.info.height = 2    # file_dialog.nml:109

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
from navkit.i18n import tr as _tr
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

    **Not ``TFileDialog.Init``'s rectangles.**  The original was a fixed 47 by
    19, sized for a 80 by 25 screen and 8.3 names: fifteen columns showed one
    of today's names in part.  This one takes the screen less a margin, never
    less than the original's, and every control is placed against the
    dialog's edges, so they grow with it: the name line along the top with its
    label over it, the lists from row 6 down to the info pane's two rows at
    the bottom, the buttons down the right ten wide and three rows apart.

    **The lists are swapped**: *Directories* on the left, narrower, and *Files*
    on the right, taking three fifths of the room -- where one goes, then what
    is there, read left to right, the way the tab order goes.

    ``Dialog``'s own row of buttons and its message are not this layout, and
    the hand-written half hides them.
    """

    #: The document this class was generated from.
    __navml_source__ = "file_dialog.nml"

    #: Ids, annotated so the hand-written half completes them.
    caption: Label    # file_dialog.nml:31
    target: Field    # file_dialog.nml:40
    dirs_caption: Label    # file_dialog.nml:49
    dirs: FileList    # file_dialog.nml:58
    files_caption: Label    # file_dialog.nml:66
    files: FileList    # file_dialog.nml:75
    pick: Button    # file_dialog.nml:85
    abandon: Button    # file_dialog.nml:94
    helper: Button    # file_dialog.nml:103
    info: FileInfoPane    # file_dialog.nml:112

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_dirs_chosen(self, event: _Event) -> bool:    # file_dialog.nml:58
        """``dirs`` raised an event whose handler is ``on_chosen``."""
        return False

    async def on_files_chosen(self, event: _Event) -> bool:    # file_dialog.nml:75
        """``files`` raised an event whose handler is ``on_chosen``."""
        return False

    async def on_pick_click(self, event: _Event) -> bool:    # file_dialog.nml:85
        """``pick`` raised an event whose handler is ``on_click``."""
        return False

    async def on_abandon_click(self, event: _Event) -> bool:    # file_dialog.nml:94
        """``abandon`` raised an event whose handler is ``on_click``."""
        return False

    async def on_helper_click(self, event: _Event) -> bool:    # file_dialog.nml:103
        """``helper`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.caption = Label(parent=self)    # file_dialog.nml:30
        self.target = Field(parent=self)    # file_dialog.nml:39
        self.dirs_caption = Label(parent=self)    # file_dialog.nml:48
        self.dirs = FileList(parent=self)    # file_dialog.nml:57
        self.files_caption = Label(parent=self)    # file_dialog.nml:65
        self.files = FileList(parent=self)    # file_dialog.nml:74
        self.pick = Button(parent=self)    # file_dialog.nml:84
        self.abandon = Button(parent=self)    # file_dialog.nml:93
        self.helper = Button(parent=self)    # file_dialog.nml:102
        self.info = FileInfoPane(parent=self)    # file_dialog.nml:111

        self.modal_width = _bind(    # file_dialog.nml:25
            lambda _o: max(47, _o.parent.width - 6) if _o.parent is not None else 47
        )
        self.modal_height = _bind(    # file_dialog.nml:26
            lambda _o: max(19, _o.parent.height - 4) if _o.parent is not None else 19
        )
        self.title = _bind(lambda _o: _tr('Open file'), yielding=True)    # file_dialog.nml:27

        self.caption.text = _bind(lambda _o: _tr('~N~ame'), yielding=True)    # file_dialog.nml:32
        self.caption.link = _bind(lambda _o: self.target.entry)    # file_dialog.nml:33
        self.caption.x = 2    # file_dialog.nml:34
        self.caption.y = 2    # file_dialog.nml:35
        self.caption.width = _bind(lambda _o: max(0, _o.parent.width - 18))    # file_dialog.nml:36
        self.caption.height = 1    # file_dialog.nml:37

        self.target.x = 3    # file_dialog.nml:41
        self.target.y = 3    # file_dialog.nml:42
        self.target.width = _bind(lambda _o: max(0, _o.parent.width - 16))    # file_dialog.nml:43
        self.target.height = 1    # file_dialog.nml:44
        self.target.label_text = ''    # file_dialog.nml:45
        self.target.label_width = 0    # file_dialog.nml:46

        self.dirs_caption.text = _bind(    # file_dialog.nml:50
            lambda _o: _tr('~D~irectories'),
            yielding=True,
        )
        self.dirs_caption.link = _bind(lambda _o: self.dirs)    # file_dialog.nml:51
        self.dirs_caption.x = 2    # file_dialog.nml:52
        self.dirs_caption.y = 5    # file_dialog.nml:53
        self.dirs_caption.width = _bind(lambda _o: self.dirs.width)    # file_dialog.nml:54
        self.dirs_caption.height = 1    # file_dialog.nml:55

        self.dirs.framed = False    # file_dialog.nml:59
        self.dirs.x = 3    # file_dialog.nml:60
        self.dirs.y = 6    # file_dialog.nml:61
        self.dirs.width = _bind(    # file_dialog.nml:62
            lambda _o: max(0, _o.parent.width - 17) * 2 // 5
        )
        self.dirs.height = _bind(lambda _o: max(0, _o.parent.height - 10))    # file_dialog.nml:63
        self.dirs.on_chosen = self.on_dirs_chosen    # file_dialog.nml:58

        self.files_caption.text = _bind(    # file_dialog.nml:67
            lambda _o: _tr('~F~iles'),
            yielding=True,
        )
        self.files_caption.link = _bind(lambda _o: self.files)    # file_dialog.nml:68
        self.files_caption.x = _bind(lambda _o: self.files.x - 1)    # file_dialog.nml:69
        self.files_caption.y = 5    # file_dialog.nml:70
        self.files_caption.width = _bind(lambda _o: self.files.width)    # file_dialog.nml:71
        self.files_caption.height = 1    # file_dialog.nml:72

        self.files.framed = False    # file_dialog.nml:76
        self.files.x = _bind(lambda _o: self.dirs.x + self.dirs.width + 2)    # file_dialog.nml:77
        self.files.y = 6    # file_dialog.nml:78
        self.files.width = _bind(    # file_dialog.nml:79
            lambda _o: max(0, _o.parent.width - 17 - self.dirs.width)
        )
        self.files.height = _bind(lambda _o: max(0, _o.parent.height - 10))    # file_dialog.nml:80
        self.files.on_chosen = self.on_files_chosen    # file_dialog.nml:75

        self.pick.text = _bind(lambda _o: _tr('O~K~'), yielding=True)    # file_dialog.nml:86
        self.pick.default = True    # file_dialog.nml:87
        self.pick.x = _bind(lambda _o: max(0, _o.parent.width - 12))    # file_dialog.nml:88
        self.pick.y = 3    # file_dialog.nml:89
        self.pick.width = 10    # file_dialog.nml:90
        self.pick.height = 2    # file_dialog.nml:91
        self.pick.on_click = self.on_pick_click    # file_dialog.nml:85

        self.abandon.text = _bind(lambda _o: _tr('Cancel'), yielding=True)    # file_dialog.nml:95
        self.abandon.x = _bind(lambda _o: max(0, _o.parent.width - 12))    # file_dialog.nml:96
        self.abandon.y = 6    # file_dialog.nml:97
        self.abandon.width = 10    # file_dialog.nml:98
        self.abandon.height = 2    # file_dialog.nml:99
        self.abandon.on_click = self.on_abandon_click    # file_dialog.nml:94

        self.helper.text = _bind(lambda _o: _tr('~H~elp'), yielding=True)    # file_dialog.nml:104
        self.helper.disabled = True    # file_dialog.nml:105
        self.helper.x = _bind(lambda _o: max(0, _o.parent.width - 12))    # file_dialog.nml:106
        self.helper.y = 9    # file_dialog.nml:107
        self.helper.width = 10    # file_dialog.nml:108
        self.helper.height = 2    # file_dialog.nml:109
        self.helper.on_click = self.on_helper_click    # file_dialog.nml:103

        self.info.x = 1    # file_dialog.nml:113
        self.info.y = _bind(lambda _o: max(0, _o.parent.height - 3))    # file_dialog.nml:114
        self.info.width = _bind(lambda _o: max(0, _o.parent.width - 2))    # file_dialog.nml:115
        self.info.height = 2    # file_dialog.nml:116

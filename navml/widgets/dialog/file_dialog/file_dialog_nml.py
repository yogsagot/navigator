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
    caption: Label    # file_dialog.nml:34
    target: Field    # file_dialog.nml:43
    dirs_caption: Label    # file_dialog.nml:52
    dirs: FileList    # file_dialog.nml:60
    files_caption: Label    # file_dialog.nml:69
    files: FileList    # file_dialog.nml:77
    pick: Button    # file_dialog.nml:88
    abandon: Button    # file_dialog.nml:98
    helper: Button    # file_dialog.nml:108
    info: FileInfoPane    # file_dialog.nml:118

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_dirs_chosen(self, event: _Event) -> bool:    # file_dialog.nml:60
        """``dirs`` raised an event whose handler is ``on_chosen``."""
        return False

    async def on_files_chosen(self, event: _Event) -> bool:    # file_dialog.nml:77
        """``files`` raised an event whose handler is ``on_chosen``."""
        return False

    async def on_pick_click(self, event: _Event) -> bool:    # file_dialog.nml:88
        """``pick`` raised an event whose handler is ``on_click``."""
        return False

    async def on_abandon_click(self, event: _Event) -> bool:    # file_dialog.nml:98
        """``abandon`` raised an event whose handler is ``on_click``."""
        return False

    async def on_helper_click(self, event: _Event) -> bool:    # file_dialog.nml:108
        """``helper`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.caption = Label(parent=self)    # file_dialog.nml:33
        self.target = Field(parent=self)    # file_dialog.nml:42
        self.dirs_caption = Label(parent=self)    # file_dialog.nml:51
        self.dirs = FileList(parent=self)    # file_dialog.nml:59
        self.files_caption = Label(parent=self)    # file_dialog.nml:68
        self.files = FileList(parent=self)    # file_dialog.nml:76
        self.pick = Button(parent=self)    # file_dialog.nml:87
        self.abandon = Button(parent=self)    # file_dialog.nml:97
        self.helper = Button(parent=self)    # file_dialog.nml:107
        self.info = FileInfoPane(parent=self)    # file_dialog.nml:117

        self.modal_width = _bind(    # file_dialog.nml:25
            lambda _o: max(47, _o.parent.width - 6) if _o.parent is not None else 47
        )
        self.modal_height = _bind(    # file_dialog.nml:26
            lambda _o: max(19, _o.parent.height - 4) if _o.parent is not None else 19
        )
        self.title = _bind(lambda _o: _tr('Open file'), yielding=True)    # file_dialog.nml:27
        self.buttons = 'none'    # file_dialog.nml:28
        self.buttons_row = _bind(    # file_dialog.nml:30
            lambda _o: (self.pick, self.abandon, self.helper)
        )

        self.caption.text = _bind(lambda _o: _tr('~N~ame'), yielding=True)    # file_dialog.nml:35
        self.caption.link = _bind(lambda _o: self.target.entry)    # file_dialog.nml:36
        self.caption.y = 2    # file_dialog.nml:37
        self.caption.x = 2    # file_dialog.nml:39
        self.caption.width = _bind(lambda _o: max(0, _o.parent.width - 18))    # file_dialog.nml:40

        self.target.y = 3    # file_dialog.nml:44
        self.target.label_text = ''    # file_dialog.nml:48
        self.target.label_width = 0    # file_dialog.nml:49
        self.target.x = 3    # file_dialog.nml:46
        self.target.width = _bind(lambda _o: max(0, _o.parent.width - 16))    # file_dialog.nml:47

        self.dirs_caption.text = _bind(    # file_dialog.nml:53
            lambda _o: _tr('~D~irectories'),
            yielding=True,
        )
        self.dirs_caption.link = _bind(lambda _o: self.dirs)    # file_dialog.nml:54
        self.dirs_caption.x = 2    # file_dialog.nml:55
        self.dirs_caption.y = 5    # file_dialog.nml:56
        self.dirs_caption.width = _bind(lambda _o: self.dirs.width)    # file_dialog.nml:57

        self.dirs.framed = False    # file_dialog.nml:61
        self.dirs.x = 3    # file_dialog.nml:62
        self.dirs.width = _bind(    # file_dialog.nml:63
            lambda _o: max(0, _o.parent.width - 17) * 2 // 5
        )
        self.dirs.y = 6    # file_dialog.nml:65
        self.dirs.height = _bind(lambda _o: max(0, _o.parent.height - 10))    # file_dialog.nml:66
        self.dirs.on_chosen = self.on_dirs_chosen    # file_dialog.nml:60

        self.files_caption.text = _bind(    # file_dialog.nml:70
            lambda _o: _tr('~F~iles'),
            yielding=True,
        )
        self.files_caption.link = _bind(lambda _o: self.files)    # file_dialog.nml:71
        self.files_caption.x = _bind(lambda _o: self.files.x - 1)    # file_dialog.nml:72
        self.files_caption.y = 5    # file_dialog.nml:73
        self.files_caption.width = _bind(lambda _o: self.files.width)    # file_dialog.nml:74

        self.files.framed = False    # file_dialog.nml:78
        self.files.x = _bind(lambda _o: self.dirs.x + self.dirs.width + 2)    # file_dialog.nml:80
        self.files.width = _bind(    # file_dialog.nml:81
            lambda _o: max(0, _o.parent.width - 12 - _o.x)
        )
        self.files.y = 6    # file_dialog.nml:82
        self.files.height = _bind(lambda _o: max(0, _o.parent.height - 10))    # file_dialog.nml:83
        self.files.on_chosen = self.on_files_chosen    # file_dialog.nml:77

        self.pick.text = _bind(lambda _o: _tr('O~K~'), yielding=True)    # file_dialog.nml:89
        self.pick.default = True    # file_dialog.nml:90
        self.pick.y = 3    # file_dialog.nml:91
        self.pick.width = 10    # file_dialog.nml:92
        self.pick.height = 2    # file_dialog.nml:93
        self.pick.x = _bind(lambda _o: max(0, _o.parent.width - 2 - _o.width))    # file_dialog.nml:95
        self.pick.on_click = self.on_pick_click    # file_dialog.nml:88

        self.abandon.text = _bind(lambda _o: _tr('Cancel'), yielding=True)    # file_dialog.nml:99
        self.abandon.y = 6    # file_dialog.nml:100
        self.abandon.width = 10    # file_dialog.nml:101
        self.abandon.height = 2    # file_dialog.nml:102
        self.abandon.x = _bind(    # file_dialog.nml:104
            lambda _o: max(0, _o.parent.width - 2 - _o.width)
        )
        self.abandon.on_click = self.on_abandon_click    # file_dialog.nml:98

        self.helper.text = _bind(lambda _o: _tr('~H~elp'), yielding=True)    # file_dialog.nml:109
        self.helper.disabled = True    # file_dialog.nml:110
        self.helper.y = 9    # file_dialog.nml:111
        self.helper.width = 10    # file_dialog.nml:112
        self.helper.height = 2    # file_dialog.nml:113
        self.helper.x = _bind(    # file_dialog.nml:115
            lambda _o: max(0, _o.parent.width - 2 - _o.width)
        )
        self.helper.on_click = self.on_helper_click    # file_dialog.nml:108

        self.info.height = 2    # file_dialog.nml:119
        self.info.x = 1    # file_dialog.nml:121
        self.info.width = _bind(lambda _o: max(0, _o.parent.width - 2))    # file_dialog.nml:122
        self.info.y = _bind(    # file_dialog.nml:123
            lambda _o: max(0, _o.parent.height - 1 - _o.height)
        )

        self._navml_built(__class__)

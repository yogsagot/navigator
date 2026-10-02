# navml: generated
"""Generated from ``system_setup_dialog.nml``.

Do not edit: edit the markup and rerun ``python -m navml build``.
"""

from __future__ import annotations

#: Everything the generator needs for itself is underscored, so a document may
#: import any name at all without colliding with it -- there is no reserved
#: word.  A bare ``Label:`` head is what asks for ``_Component``; markup
#: never names it.  See *Importing another component* in navml/DESIGN.md.
from typing import Any as _Any

from navkit.reactive import bind as _bind

from navml.component import Component as _Component
from navml.widgets.dialog.check_boxes import CheckBoxes    # system_setup_dialog.nml:1
from navml.widgets.dialog.dialog import Dialog    # system_setup_dialog.nml:2
from navml.widgets.dialog.field import Field    # system_setup_dialog.nml:3
from navml.widgets.dialog.label import Label    # system_setup_dialog.nml:4

__navml_component__ = "SystemSetupDialog"

__all__ = ["SystemSetupDialog"]


class SystemSetupDialog(Dialog, _Component):
    """Options > Configuration > System Setup: DOS Navigator's ``dlgSystemSetup``.

    The resource's *Options* and *Temporary directory*, less what only meant
    something on DOS -- *Disable XMS/EMS usage*, *OS-dependent Disk Access*,
    *Clear read-only from CD*, *"Fast" command execution* (DN's INT 2Fh reload
    trick), *Advanced copy* (XMS/EMS buffers), the two video modes and the
    per-drive list -- so it is nine rows shorter.  *Flush disk buffers* is
    kept as what it means on POSIX: syncing what a copy wrote.  Help is left out, having nothing to show yet.
    *Use internal terminal* is not DN's but a departure: whether Ctrl+O shows
    the console in Navigator, or hands the real terminal over as mc does.
    """

    #: The document this class was generated from.
    __navml_source__ = "system_setup_dialog.nml"

    #: Ids, annotated so the hand-written half completes them.
    options_caption: Label    # system_setup_dialog.nml:22
    options: CheckBoxes    # system_setup_dialog.nml:31
    temp_caption: Label    # system_setup_dialog.nml:39
    temp_dir: Field    # system_setup_dialog.nml:48

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.options_caption = Label(parent=self)    # system_setup_dialog.nml:21
        self.options = CheckBoxes(parent=self)    # system_setup_dialog.nml:30
        self.temp_caption = Label(parent=self)    # system_setup_dialog.nml:38
        self.temp_dir = Field(parent=self)    # system_setup_dialog.nml:47

        self.modal_width = 60    # system_setup_dialog.nml:17
        self.modal_height = 13    # system_setup_dialog.nml:18
        self.title = 'System Setup'    # system_setup_dialog.nml:19

        self.options_caption.x = 3    # system_setup_dialog.nml:23
        self.options_caption.y = 1    # system_setup_dialog.nml:24
        self.options_caption.width = 12    # system_setup_dialog.nml:25
        self.options_caption.height = 1    # system_setup_dialog.nml:26
        self.options_caption.text = '~O~ptions'    # system_setup_dialog.nml:27
        self.options_caption.link = _bind(lambda _o: self.options)    # system_setup_dialog.nml:28

        self.options.x = 3    # system_setup_dialog.nml:32
        self.options.y = 2    # system_setup_dialog.nml:33
        self.options.width = _bind(lambda _o: max(0, _o.parent.width - 6))    # system_setup_dialog.nml:34
        self.options.height = 3    # system_setup_dialog.nml:35
        self.options.items = ['Internal ~e~ditor', 'Internal ~v~iewer', '~U~se system clipboard', '~S~how hidden files', 'S~y~nc after copying', 'Use internal te~r~minal']    # system_setup_dialog.nml:36

        self.temp_caption.x = 3    # system_setup_dialog.nml:40
        self.temp_caption.y = 6    # system_setup_dialog.nml:41
        self.temp_caption.width = 24    # system_setup_dialog.nml:42
        self.temp_caption.height = 1    # system_setup_dialog.nml:43
        self.temp_caption.text = '~T~emporary directory'    # system_setup_dialog.nml:44
        self.temp_caption.link = _bind(lambda _o: self.temp_dir.entry)    # system_setup_dialog.nml:45

        self.temp_dir.x = 3    # system_setup_dialog.nml:49
        self.temp_dir.y = 7    # system_setup_dialog.nml:50
        self.temp_dir.width = _bind(lambda _o: max(0, _o.parent.width - 6))    # system_setup_dialog.nml:51
        self.temp_dir.height = 1    # system_setup_dialog.nml:52
        self.temp_dir.label_text = ''    # system_setup_dialog.nml:53
        self.temp_dir.label_width = 0    # system_setup_dialog.nml:54

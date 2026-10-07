# navml: generated
"""Generated from ``system_info_dialog.nml``.

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
from navml.widgets.dialog.dialog import Dialog    # system_info_dialog.nml:1
from navml.widgets.dialog.group_box import GroupBox    # system_info_dialog.nml:2
from navml.widgets.dialog.static_text import StaticText    # system_info_dialog.nml:3

__navml_component__ = "SystemInfoDialog"

__all__ = ["SystemInfoDialog"]


class SystemInfoDialog(Dialog, _Component):
    """Utilities > System Information: DOS Navigator's ``SystemInfo`` dialog.

    Its 70 by 22 and its four ``ofFramed`` boxes, each titled on its frame --
    *Main board* across the top, *Disk drives* under it, *Memory* and *Other*
    side by side at the foot -- filled with Linux's answers
    (:mod:`navigator.sysinfo`); OK alone, centred.
    """

    #: The document this class was generated from.
    __navml_source__ = "system_info_dialog.nml"

    #: Ids, annotated so the hand-written half completes them.
    board_box: GroupBox    # system_info_dialog.nml:18
    board: StaticText    # system_info_dialog.nml:26
    disks_box: GroupBox    # system_info_dialog.nml:33
    disks: StaticText    # system_info_dialog.nml:41
    memory_box: GroupBox    # system_info_dialog.nml:48
    memory: StaticText    # system_info_dialog.nml:56
    other_box: GroupBox    # system_info_dialog.nml:63
    other: StaticText    # system_info_dialog.nml:71

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.board_box = GroupBox(parent=self)    # system_info_dialog.nml:17
        self.board = StaticText(parent=self.board_box)    # system_info_dialog.nml:25
        self.disks_box = GroupBox(parent=self)    # system_info_dialog.nml:32
        self.disks = StaticText(parent=self.disks_box)    # system_info_dialog.nml:40
        self.memory_box = GroupBox(parent=self)    # system_info_dialog.nml:47
        self.memory = StaticText(parent=self.memory_box)    # system_info_dialog.nml:55
        self.other_box = GroupBox(parent=self)    # system_info_dialog.nml:62
        self.other = StaticText(parent=self.other_box)    # system_info_dialog.nml:70

        self.modal_width = 70    # system_info_dialog.nml:12
        self.modal_height = 22    # system_info_dialog.nml:13
        self.title = 'System Information'    # system_info_dialog.nml:14
        self.buttons = 'ok'    # system_info_dialog.nml:15

        self.board_box.x = 3    # system_info_dialog.nml:19
        self.board_box.y = 1    # system_info_dialog.nml:20
        self.board_box.width = 64    # system_info_dialog.nml:21
        self.board_box.height = 5    # system_info_dialog.nml:22
        self.board_box.title = 'Main board'    # system_info_dialog.nml:23

        self.board.x = 2    # system_info_dialog.nml:27
        self.board.y = 1    # system_info_dialog.nml:28
        self.board.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # system_info_dialog.nml:29
        self.board.height = _bind(lambda _o: max(0, _o.parent.height - 2))    # system_info_dialog.nml:30

        self.disks_box.x = 3    # system_info_dialog.nml:34
        self.disks_box.y = 6    # system_info_dialog.nml:35
        self.disks_box.width = 64    # system_info_dialog.nml:36
        self.disks_box.height = 6    # system_info_dialog.nml:37
        self.disks_box.title = 'Disk drives'    # system_info_dialog.nml:38

        self.disks.x = 2    # system_info_dialog.nml:42
        self.disks.y = 1    # system_info_dialog.nml:43
        self.disks.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # system_info_dialog.nml:44
        self.disks.height = _bind(lambda _o: max(0, _o.parent.height - 2))    # system_info_dialog.nml:45

        self.memory_box.x = 3    # system_info_dialog.nml:49
        self.memory_box.y = 12    # system_info_dialog.nml:50
        self.memory_box.width = 26    # system_info_dialog.nml:51
        self.memory_box.height = 6    # system_info_dialog.nml:52
        self.memory_box.title = 'Memory'    # system_info_dialog.nml:53

        self.memory.x = 2    # system_info_dialog.nml:57
        self.memory.y = 1    # system_info_dialog.nml:58
        self.memory.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # system_info_dialog.nml:59
        self.memory.height = _bind(lambda _o: max(0, _o.parent.height - 2))    # system_info_dialog.nml:60

        self.other_box.x = 30    # system_info_dialog.nml:64
        self.other_box.y = 12    # system_info_dialog.nml:65
        self.other_box.width = 37    # system_info_dialog.nml:66
        self.other_box.height = 6    # system_info_dialog.nml:67
        self.other_box.title = 'Other'    # system_info_dialog.nml:68

        self.other.x = 2    # system_info_dialog.nml:72
        self.other.y = 1    # system_info_dialog.nml:73
        self.other.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # system_info_dialog.nml:74
        self.other.height = _bind(lambda _o: max(0, _o.parent.height - 2))    # system_info_dialog.nml:75

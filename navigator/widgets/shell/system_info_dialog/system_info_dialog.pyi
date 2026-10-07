# navml: generated
"""The merged surface of ``navigator.widgets.shell.system_info_dialog.system_info_dialog``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.group_box import GroupBox
from navml.widgets.dialog.static_text import StaticText

from typing import Any
from navigator.sysinfo import SystemFacts, lines


class SystemInfoDialog(Dialog, _Component):
    board_box: GroupBox
    board: StaticText
    disks_box: GroupBox
    disks: StaticText
    memory_box: GroupBox
    memory: StaticText
    other_box: GroupBox
    other: StaticText
    def __init__(self, facts: SystemFacts | None = ..., **kwargs: Any) -> None: ...

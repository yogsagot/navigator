# navml: generated
"""Generated from ``monitor_window.nml``.

Do not edit: edit the markup and rerun ``python -m navml build``.
"""

from __future__ import annotations

#: Everything the generator needs for itself is underscored, so a document may
#: import any name at all without colliding with it -- there is no reserved
#: word.  A bare ``Label:`` head is what asks for ``_Component``; markup
#: never names it.  See *Importing another component* in navml/DESIGN.md.
from typing import Any as _Any

from navkit.i18n import tr as _tr
from navkit.reactive import bind as _bind

from navml.component import Component as _Component
from navigator.widgets.manager.commands import Rescan    # monitor_window.nml:1
from navigator.widgets.shell.monitor_meters import CpuMeters, MemoryMeters, SensorList    # monitor_window.nml:2
from navml.commands import CloseWindow    # monitor_window.nml:3
from navml.widgets.dialog.commands import SelectNext, SelectPrevious    # monitor_window.nml:4
from navml.widgets.dialog.group_box import GroupBox    # monitor_window.nml:5
from navml.widgets.menu.menu_item import MenuItem    # monitor_window.nml:6
from navml.widgets.menu.menu_line import MenuLine    # monitor_window.nml:7
from navml.widgets.menu.sub_menu import SubMenu    # monitor_window.nml:8
from navml.widgets.window import Window    # monitor_window.nml:9

__navml_component__ = "MonitorWindow"

__all__ = ["MonitorWindow"]


class MonitorWindow(Window, _Component):
    """Utilities > System monitor: every processor's load, the memory and the

    sensors, read again every ``[monitor] refresh`` seconds.  **Not DOS
    Navigator's**: a departure, asked for -- DOS had one processor and nothing
    to measure it by.  The window beside Process list, built as it is;
    ``navigator/lib/system/monitor.py`` says how ``/proc`` and ``/sys`` are read.

    Three boxes, titled on their frames as System Information's are: *CPU* --
    every processor together, then each one in columns, its share and its
    clock; *Memory* -- what is in use, the commit charge (*Virtual*) and swap;
    *Sensors* -- each chip's temperatures and fans, left out where there are
    none.  **The window opens at the size its content needs**, so 4 processors
    and 64 give boxes of different heights, and it fits itself again when a
    processor or a sensor comes or goes -- until the user moves, resizes,
    zooms or tiles it, when the size is theirs.  A box too short for what it
    lists scrolls (the arrows, PgUp/PgDn, the wheel); Tab goes from one to the
    other.  Esc closes it; Ctrl+R and Alt+R read again at once.
    """

    #: The document this class was generated from.
    __navml_source__ = "monitor_window.nml"

    #: The keys this component binds, read through key_table().
    keys = {    # monitor_window.nml:32
        'escape': CloseWindow,    # monitor_window.nml:33
        'ctrl+r': Rescan,    # monitor_window.nml:34
        'alt+r': Rescan,    # monitor_window.nml:35
        'tab': SelectNext,    # monitor_window.nml:36
        'shift+tab': SelectPrevious,    # monitor_window.nml:37
    }

    #: Ids, annotated so the hand-written half completes them.
    cpu_box: GroupBox    # monitor_window.nml:50
    cpu: CpuMeters    # monitor_window.nml:59
    memory_box: GroupBox    # monitor_window.nml:67
    memory: MemoryMeters    # monitor_window.nml:76
    sensor_box: GroupBox    # monitor_window.nml:84
    sensors: SensorList    # monitor_window.nml:94
    monitor_menu: SubMenu    # monitor_window.nml:104

    #: The commands this component handles itself.
    async def on_rescan(self, event: _Any) -> bool:    # monitor_window.nml:41
        """``Rescan``."""
        self.reload()
        return True

    async def on_select_next(self, event: _Any) -> bool:    # monitor_window.nml:42
        """``SelectNext``."""
        self._step(1)
        return True

    async def on_select_previous(self, event: _Any) -> bool:    # monitor_window.nml:43
        """``SelectPrevious``."""
        self._step(-1)
        return True

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.cpu_box = GroupBox(parent=self)    # monitor_window.nml:49
        self.cpu = CpuMeters(parent=self.cpu_box)    # monitor_window.nml:58
        self.memory_box = GroupBox(parent=self)    # monitor_window.nml:66
        self.memory = MemoryMeters(parent=self.memory_box)    # monitor_window.nml:75
        self.sensor_box = GroupBox(parent=self)    # monitor_window.nml:83
        self.sensors = SensorList(parent=self.sensor_box)    # monitor_window.nml:93
        self.monitor_menu = SubMenu(parent=self)    # monitor_window.nml:103
        _w1 = MenuItem(parent=self.monitor_menu)    # monitor_window.nml:106
        _w2 = MenuLine(parent=self.monitor_menu)    # monitor_window.nml:107
        _w3 = MenuItem(parent=self.monitor_menu)    # monitor_window.nml:108

        self.title = _bind(lambda _o: _tr('System monitor'), yielding=True)    # monitor_window.nml:28
        self.min_width = 40    # monitor_window.nml:29
        self.min_height = 11    # monitor_window.nml:30
        self.first_focus = _bind(lambda _o: self.cpu)    # monitor_window.nml:45
        self.local_menu = _bind(lambda _o: self.monitor_menu)    # monitor_window.nml:47

        self.cpu_box.y = 1    # monitor_window.nml:51
        self.cpu_box.height = _bind(lambda _o: self.heights[0])    # monitor_window.nml:52
        self.cpu_box.title = _bind(lambda _o: _tr('CPU'), yielding=True)    # monitor_window.nml:56
        self.cpu_box.x = 2    # monitor_window.nml:54
        self.cpu_box.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # monitor_window.nml:55

        self.cpu.x = 2    # monitor_window.nml:61
        self.cpu.width = _bind(lambda _o: max(0, _o.parent.width - 3))    # monitor_window.nml:62
        self.cpu.y = 1    # monitor_window.nml:63
        self.cpu.height = _bind(lambda _o: max(0, _o.parent.height - 2))    # monitor_window.nml:64

        self.memory_box.height = _bind(lambda _o: self.heights[1])    # monitor_window.nml:68
        self.memory_box.title = _bind(lambda _o: _tr('Memory'), yielding=True)    # monitor_window.nml:73
        self.memory_box.x = 2    # monitor_window.nml:70
        self.memory_box.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # monitor_window.nml:71
        self.memory_box.y = _bind(    # monitor_window.nml:72
            lambda _o: self.cpu_box.y + self.cpu_box.height
        )

        self.memory.x = 2    # monitor_window.nml:78
        self.memory.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # monitor_window.nml:79
        self.memory.y = 1    # monitor_window.nml:80
        self.memory.height = _bind(lambda _o: max(0, _o.parent.height - 2))    # monitor_window.nml:81

        self.sensor_box.height = _bind(lambda _o: self.heights[2])    # monitor_window.nml:85
        self.sensor_box.visible = _bind(lambda _o: self.heights[2] >= 3)    # monitor_window.nml:90
        self.sensor_box.title = _bind(lambda _o: _tr('Sensors'), yielding=True)    # monitor_window.nml:91
        self.sensor_box.x = 2    # monitor_window.nml:87
        self.sensor_box.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # monitor_window.nml:88
        self.sensor_box.y = _bind(    # monitor_window.nml:89
            lambda _o: self.memory_box.y + self.memory_box.height
        )

        self.sensors.x = 2    # monitor_window.nml:96
        self.sensors.width = _bind(lambda _o: max(0, _o.parent.width - 3))    # monitor_window.nml:97
        self.sensors.y = 1    # monitor_window.nml:98
        self.sensors.height = _bind(lambda _o: max(0, _o.parent.height - 2))    # monitor_window.nml:99

        self.monitor_menu.text = _bind(    # monitor_window.nml:103
            lambda _o: _tr('Mo~n~itor'),
            yielding=True,
        )
        self.monitor_menu.after = 'File'    # monitor_window.nml:103
        self.monitor_menu.tooltip = _bind(    # monitor_window.nml:105
            lambda _o: _tr('The processors, the memory and the sensors'),
            yielding=True,
        )

        _w1.text = _bind(lambda _o: _tr('~R~e-read'), yielding=True)    # monitor_window.nml:106
        _w1.command = Rescan    # monitor_window.nml:106
        _w1.key = 'Ctrl-R'    # monitor_window.nml:106

        _w3.text = _bind(lambda _o: _tr('~C~lose'), yielding=True)    # monitor_window.nml:108
        _w3.command = CloseWindow    # monitor_window.nml:108

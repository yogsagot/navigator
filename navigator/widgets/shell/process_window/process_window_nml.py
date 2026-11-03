# navml: generated
"""Generated from ``process_window.nml``.

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
from navigator.widgets.manager.commands import Rescan    # process_window.nml:1
from navigator.widgets.shell.commands import KillProcess, ProcessDetails, ProcessMineOnly, ProcessSortCommand, ProcessSortCpu, ProcessSortMemory, ProcessSortPid, ProcessSortState, ProcessSortUser, ProcessTree, SignalProcess    # process_window.nml:2
from navigator.widgets.shell.process_list import ProcessList    # process_window.nml:3
from navml.commands import CloseWindow    # process_window.nml:4
from navml.widgets.dialog.button import Button    # process_window.nml:5
from navml.widgets.dialog.check_boxes import CheckBoxes    # process_window.nml:6
from navml.widgets.dialog.commands import QuickSearch, SelectNext, SelectPrevious    # process_window.nml:7
from navml.widgets.dialog.static_text import StaticText    # process_window.nml:8
from navml.widgets.menu.menu_item import MenuItem    # process_window.nml:9
from navml.widgets.menu.menu_line import MenuLine    # process_window.nml:10
from navml.widgets.menu.sub_menu import SubMenu    # process_window.nml:11
from navml.widgets.window import Window    # process_window.nml:12

__navml_component__ = "ProcessWindow"

__all__ = ["ProcessWindow"]


class ProcessWindow(Window, _Component):
    """Utilities > Process list: every running process -- its number, owner,

    state, CPU share, resident memory and command -- a row each, read again
    every ``[processes] refresh`` seconds.  **Not DOS Navigator's**: a
    departure, asked for -- DOS ran one program at a time.  It is FAR
    Manager's process panel, in a window as Disk > Volumes is;
    ``navigator/lib/system/processes.py`` says how ``/proc`` is read.

    Laid out as Disk > Volumes is: the list without a frame of its own, one
    column into the window's; under it the status line -- how many processes,
    and what is being searched for -- then *Mine only* and *Tree* on the left,
    *Signal*, *Kill*, *Details* and *Close* on the right.

    Ctrl+P, Ctrl+U, Ctrl+E, Ctrl+L, Ctrl+Z and Ctrl+N sort by number, user,
    state, CPU (the load), memory (the size) and command (the name), as does a
    click on a column's title; the same again turns the order round.  Not the
    Ctrl+F keys FAR sorts a panel by: the desktop and the global table hold
    them here.  Ctrl+T shows each process under its parent; Ctrl+H only the
    user's own.  F3 tells what ``/proc`` says of the one under the cursor; F7
    sends it a signal chosen from a box, F8 or Del asks it to end (SIGTERM).
    A signal the user may not send is offered *As root*, through the root
    helper's ``kill``.  Ctrl+S, or typing, searches.  Esc closes the window;
    Ctrl+R and Alt+R read again at once.
    """

    #: The document this class was generated from.
    __navml_source__ = "process_window.nml"

    #: The keys this component binds, read through key_table().
    keys = {    # process_window.nml:39
        'escape': CloseWindow,    # process_window.nml:40
        'ctrl+r': Rescan,    # process_window.nml:41
        'alt+r': Rescan,    # process_window.nml:42
        'ctrl+p': ProcessSortPid,    # process_window.nml:43
        'ctrl+u': ProcessSortUser,    # process_window.nml:44
        'ctrl+e': ProcessSortState,    # process_window.nml:45
        'ctrl+l': ProcessSortCpu,    # process_window.nml:46
        'ctrl+z': ProcessSortMemory,    # process_window.nml:47
        'ctrl+n': ProcessSortCommand,    # process_window.nml:48
        'ctrl+t': ProcessTree,    # process_window.nml:49
        'ctrl+h': ProcessMineOnly,    # process_window.nml:50
        'f3': ProcessDetails,    # process_window.nml:51
        'f7': SignalProcess,    # process_window.nml:52
        'f8': KillProcess,    # process_window.nml:53
        'delete': KillProcess,    # process_window.nml:54
        'tab': SelectNext,    # process_window.nml:55
        'shift+tab': SelectPrevious,    # process_window.nml:56
    }

    #: Ids, annotated so the hand-written half completes them.
    processes: ProcessList    # process_window.nml:59
    status: StaticText    # process_window.nml:67
    mine_box: CheckBoxes    # process_window.nml:74
    tree_box: CheckBoxes    # process_window.nml:83
    signal_button: Button    # process_window.nml:92
    kill_button: Button    # process_window.nml:101
    details_button: Button    # process_window.nml:110
    close_button: Button    # process_window.nml:120
    process_menu: SubMenu    # process_window.nml:131

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_processes_chosen(self, event: _Event) -> bool:    # process_window.nml:59
        """``processes`` raised an event whose handler is ``on_chosen``."""
        return False

    async def on_processes_sort_chosen(self, event: _Event) -> bool:    # process_window.nml:59
        """``processes`` raised an event whose handler is ``on_sort_chosen``."""
        return False

    async def on_signal_button_click(self, event: _Event) -> bool:    # process_window.nml:92
        """``signal_button`` raised an event whose handler is ``on_click``."""
        return False

    async def on_kill_button_click(self, event: _Event) -> bool:    # process_window.nml:101
        """``kill_button`` raised an event whose handler is ``on_click``."""
        return False

    async def on_details_button_click(self, event: _Event) -> bool:    # process_window.nml:110
        """``details_button`` raised an event whose handler is ``on_click``."""
        return False

    async def on_close_button_click(self, event: _Event) -> bool:    # process_window.nml:120
        """``close_button`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.processes = ProcessList(parent=self)    # process_window.nml:58
        self.status = StaticText(parent=self)    # process_window.nml:66
        self.mine_box = CheckBoxes(parent=self)    # process_window.nml:73
        self.tree_box = CheckBoxes(parent=self)    # process_window.nml:82
        self.signal_button = Button(parent=self)    # process_window.nml:91
        self.kill_button = Button(parent=self)    # process_window.nml:100
        self.details_button = Button(parent=self)    # process_window.nml:109
        self.close_button = Button(parent=self)    # process_window.nml:119
        self.process_menu = SubMenu(parent=self)    # process_window.nml:130
        _w1 = MenuItem(parent=self.process_menu)    # process_window.nml:135
        _w2 = MenuLine(parent=self.process_menu)    # process_window.nml:139
        _w3 = MenuItem(parent=self.process_menu)    # process_window.nml:140
        _w4 = MenuItem(parent=self.process_menu)    # process_window.nml:144
        _w5 = MenuItem(parent=self.process_menu)    # process_window.nml:148
        _w6 = MenuItem(parent=self.process_menu)    # process_window.nml:152
        _w7 = MenuItem(parent=self.process_menu)    # process_window.nml:156
        _w8 = MenuItem(parent=self.process_menu)    # process_window.nml:160
        _w9 = MenuLine(parent=self.process_menu)    # process_window.nml:164
        _w10 = MenuItem(parent=self.process_menu)    # process_window.nml:165
        _w11 = MenuItem(parent=self.process_menu)    # process_window.nml:170
        _w12 = MenuItem(parent=self.process_menu)    # process_window.nml:175
        _w13 = MenuLine(parent=self.process_menu)    # process_window.nml:179
        _w14 = MenuItem(parent=self.process_menu)    # process_window.nml:180
        _w15 = MenuItem(parent=self.process_menu)    # process_window.nml:184
        _w16 = MenuItem(parent=self.process_menu)    # process_window.nml:188
        _w17 = MenuLine(parent=self.process_menu)    # process_window.nml:192
        _w18 = MenuItem(parent=self.process_menu)    # process_window.nml:193

        self.title = _bind(lambda _o: _tr('Process list'), yielding=True)    # process_window.nml:37

        self.processes.framed = False    # process_window.nml:60
        self.processes.x = 1    # process_window.nml:61
        self.processes.y = 1    # process_window.nml:62
        self.processes.width = _bind(lambda _o: max(0, _o.parent.width - 1))    # process_window.nml:63
        self.processes.height = _bind(lambda _o: max(0, _o.parent.height - 5))    # process_window.nml:64
        self.processes.on_chosen = self.on_processes_chosen    # process_window.nml:59
        self.processes.on_sort_chosen = self.on_processes_sort_chosen    # process_window.nml:59

        self.status.x = 2    # process_window.nml:68
        self.status.y = _bind(lambda _o: max(0, _o.parent.height - 4))    # process_window.nml:69
        self.status.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # process_window.nml:70
        self.status.height = 1    # process_window.nml:71

        self.mine_box.x = 2    # process_window.nml:75
        self.mine_box.y = _bind(lambda _o: max(0, _o.parent.height - 3))    # process_window.nml:76
        self.mine_box.width = 16    # process_window.nml:77
        self.mine_box.height = 1    # process_window.nml:78
        self.mine_box.items = _bind(    # process_window.nml:79
            lambda _o: [_tr('~M~ine only')],
            yielding=True,
        )
        self.mine_box.tooltips = _bind(    # process_window.nml:80
            lambda _o: [_tr('Only your own processes')],
            yielding=True,
        )

        self.tree_box.x = 2    # process_window.nml:84
        self.tree_box.y = _bind(lambda _o: max(0, _o.parent.height - 2))    # process_window.nml:85
        self.tree_box.width = 16    # process_window.nml:86
        self.tree_box.height = 1    # process_window.nml:87
        self.tree_box.items = _bind(lambda _o: [_tr('~T~ree')], yielding=True)    # process_window.nml:88
        self.tree_box.tooltips = _bind(    # process_window.nml:89
            lambda _o: [_tr('Each process under its parent')],
            yielding=True,
        )

        self.signal_button.text = _bind(    # process_window.nml:93
            lambda _o: _tr('~S~ignal'),
            yielding=True,
        )
        self.signal_button.x = _bind(lambda _o: max(0, _o.parent.width - 47))    # process_window.nml:94
        self.signal_button.y = _bind(lambda _o: max(0, _o.parent.height - 3))    # process_window.nml:95
        self.signal_button.width = 11    # process_window.nml:96
        self.signal_button.height = 2    # process_window.nml:97
        self.signal_button.disabled = _bind(    # process_window.nml:98
            lambda _o: not self.allows('signal')
        )
        self.signal_button.on_click = self.on_signal_button_click    # process_window.nml:92

        self.kill_button.text = _bind(lambda _o: _tr('~K~ill'), yielding=True)    # process_window.nml:102
        self.kill_button.x = _bind(lambda _o: max(0, _o.parent.width - 35))    # process_window.nml:103
        self.kill_button.y = _bind(lambda _o: max(0, _o.parent.height - 3))    # process_window.nml:104
        self.kill_button.width = 9    # process_window.nml:105
        self.kill_button.height = 2    # process_window.nml:106
        self.kill_button.disabled = _bind(lambda _o: not self.allows('signal'))    # process_window.nml:107
        self.kill_button.on_click = self.on_kill_button_click    # process_window.nml:101

        self.details_button.text = _bind(    # process_window.nml:111
            lambda _o: _tr('~D~etails'),
            yielding=True,
        )
        self.details_button.default = True    # process_window.nml:112
        self.details_button.x = _bind(lambda _o: max(0, _o.parent.width - 25))    # process_window.nml:113
        self.details_button.y = _bind(lambda _o: max(0, _o.parent.height - 3))    # process_window.nml:114
        self.details_button.width = 12    # process_window.nml:115
        self.details_button.height = 2    # process_window.nml:116
        self.details_button.disabled = _bind(    # process_window.nml:117
            lambda _o: not self.allows('details')
        )
        self.details_button.on_click = self.on_details_button_click    # process_window.nml:110

        self.close_button.text = _bind(lambda _o: _tr('Close'), yielding=True)    # process_window.nml:121
        self.close_button.x = _bind(lambda _o: max(0, _o.parent.width - 12))    # process_window.nml:122
        self.close_button.y = _bind(lambda _o: max(0, _o.parent.height - 3))    # process_window.nml:123
        self.close_button.width = 10    # process_window.nml:124
        self.close_button.height = 2    # process_window.nml:125
        self.close_button.on_click = self.on_close_button_click    # process_window.nml:120

        self.process_menu.text = _bind(    # process_window.nml:132
            lambda _o: _tr('~P~rocesses'),
            yielding=True,
        )
        self.process_menu.tooltip = _bind(    # process_window.nml:133
            lambda _o: _tr('Sort, search and signal the running processes'),
            yielding=True,
        )
        self.process_menu.after = 'File'    # process_window.nml:134

        _w1.text = _bind(lambda _o: _tr('~R~e-read'), yielding=True)    # process_window.nml:136
        _w1.command = Rescan    # process_window.nml:137
        _w1.key = 'Ctrl-R'    # process_window.nml:138

        _w3.text = _bind(lambda _o: _tr('Sort by ~P~ID'), yielding=True)    # process_window.nml:141
        _w3.command = ProcessSortPid    # process_window.nml:142
        _w3.key = 'Ctrl-P'    # process_window.nml:143

        _w4.text = _bind(lambda _o: _tr('Sort by ~u~ser'), yielding=True)    # process_window.nml:145
        _w4.command = ProcessSortUser    # process_window.nml:146
        _w4.key = 'Ctrl-U'    # process_window.nml:147

        _w5.text = _bind(lambda _o: _tr('Sort by s~t~ate'), yielding=True)    # process_window.nml:149
        _w5.command = ProcessSortState    # process_window.nml:150
        _w5.key = 'Ctrl-E'    # process_window.nml:151

        _w6.text = _bind(lambda _o: _tr('Sort by CPU ~l~oad'), yielding=True)    # process_window.nml:153
        _w6.command = ProcessSortCpu    # process_window.nml:154
        _w6.key = 'Ctrl-L'    # process_window.nml:155

        _w7.text = _bind(lambda _o: _tr('Sort by ~m~emory'), yielding=True)    # process_window.nml:157
        _w7.command = ProcessSortMemory    # process_window.nml:158
        _w7.key = 'Ctrl-Z'    # process_window.nml:159

        _w8.text = _bind(lambda _o: _tr('Sort by comma~n~d'), yielding=True)    # process_window.nml:161
        _w8.command = ProcessSortCommand    # process_window.nml:162
        _w8.key = 'Ctrl-N'    # process_window.nml:163

        _w10.text = _bind(lambda _o: _tr('Tr~e~e'), yielding=True)    # process_window.nml:166
        _w10.tooltip = _bind(    # process_window.nml:167
            lambda _o: _tr('Each process under its parent'),
            yielding=True,
        )
        _w10.command = ProcessTree    # process_window.nml:168
        _w10.key = 'Ctrl-T'    # process_window.nml:169

        _w11.text = _bind(lambda _o: _tr('M~i~ne only'), yielding=True)    # process_window.nml:171
        _w11.tooltip = _bind(    # process_window.nml:172
            lambda _o: _tr('Only your own processes'),
            yielding=True,
        )
        _w11.command = ProcessMineOnly    # process_window.nml:173
        _w11.key = 'Ctrl-H'    # process_window.nml:174

        _w12.text = _bind(lambda _o: _tr('~Q~uick search'), yielding=True)    # process_window.nml:176
        _w12.command = QuickSearch    # process_window.nml:177
        _w12.key = 'Ctrl-S'    # process_window.nml:178

        _w14.text = _bind(lambda _o: _tr('~D~etails...'), yielding=True)    # process_window.nml:181
        _w14.command = ProcessDetails    # process_window.nml:182
        _w14.key = 'F3'    # process_window.nml:183

        _w15.text = _bind(lambda _o: _tr('~S~ignal...'), yielding=True)    # process_window.nml:185
        _w15.command = SignalProcess    # process_window.nml:186
        _w15.key = 'F7'    # process_window.nml:187

        _w16.text = _bind(lambda _o: _tr('~K~ill...'), yielding=True)    # process_window.nml:189
        _w16.command = KillProcess    # process_window.nml:190
        _w16.key = 'F8'    # process_window.nml:191

        _w18.text = _bind(lambda _o: _tr('~C~lose'), yielding=True)    # process_window.nml:194
        _w18.command = CloseWindow    # process_window.nml:195

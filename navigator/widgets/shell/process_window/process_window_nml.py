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
from navigator.widgets.shell.commands import FilterProcesses, KillProcess, ProcessDetails, ProcessMineOnly, ProcessSortCommand, ProcessSortCpu, ProcessSortMemory, ProcessSortPid, ProcessSortState, ProcessSortUser, ProcessTree, SignalProcess    # process_window.nml:2
from navigator.widgets.shell.process_list import ProcessFilter, ProcessList    # process_window.nml:3
from navml.commands import CloseWindow    # process_window.nml:4
from navml.widgets.dialog.button import Button    # process_window.nml:5
from navml.widgets.dialog.check_boxes import CheckBoxes    # process_window.nml:6
from navml.widgets.dialog.commands import SelectNext, SelectPrevious    # process_window.nml:7
from navml.widgets.dialog.label import Label    # process_window.nml:8
from navml.widgets.dialog.static_text import StaticText    # process_window.nml:9
from navml.widgets.menu.menu_item import MenuItem    # process_window.nml:10
from navml.widgets.menu.menu_line import MenuLine    # process_window.nml:11
from navml.widgets.menu.sub_menu import SubMenu    # process_window.nml:12
from navml.widgets.window import Window    # process_window.nml:13

__navml_component__ = "ProcessWindow"

__all__ = ["ProcessWindow"]


class ProcessWindow(Window, _Component):
    """Utilities > Process list: every running process -- its number, owner,

    state, CPU share, resident memory and command -- a row each, read again
    every ``[processes] refresh`` seconds.  **Not DOS Navigator's**: a
    departure, asked for -- DOS ran one program at a time.  It is FAR
    Manager's process panel, in a window as Disk > Volumes is;
    ``navigator/lib/system/processes.py`` says how ``/proc`` is read.

    Laid out as Disk > Volumes is, with htop's filter line over it: *Filter*
    and an X that empties it across the top; the list without a frame of its
    own, one column into the window's; under it the status line -- how many
    processes, and how many the filter lets through -- then *Mine only* and
    *Tree* on the left, *Signal*, *Kill*, *Details* and *Close* on the right.
    The boxes are as wide as their captions, and the window never narrower
    than the boxes and the buttons side by side, which once covered *Mine
    only* in a window opened on an 80-column screen.

    Ctrl+P, Ctrl+U, Ctrl+E, Ctrl+L, Ctrl+Z and Ctrl+N sort by number, user,
    state, CPU (the load), memory (the size) and command (the name), as does a
    click on a column's title; the same again turns the order round.  Not the
    Ctrl+F keys FAR sorts a panel by: the desktop and the global table hold
    them here.  Ctrl+T shows each process under its parent; Ctrl+H only the
    user's own.  F3 tells what ``/proc`` says of the one under the cursor; F7
    sends it a signal chosen from a box, F8 or Del asks it to end (SIGTERM).
    A signal the user may not send is offered *As root*, through the root
    helper's ``kill``.  Typing on the list, Ctrl+S, F4 or Alt+F goes to the
    filter, which narrows the list as it is typed; in a tree a match keeps its
    parents, dimmed.  Esc empties the filter, then closes the window; Ctrl+R
    and Alt+R read again at once.
    """

    #: The document this class was generated from.
    __navml_source__ = "process_window.nml"

    #: The keys this component binds, read through key_table().
    keys = {    # process_window.nml:47
        'escape': CloseWindow,    # process_window.nml:48
        'ctrl+r': Rescan,    # process_window.nml:49
        'alt+r': Rescan,    # process_window.nml:50
        'ctrl+p': ProcessSortPid,    # process_window.nml:51
        'ctrl+u': ProcessSortUser,    # process_window.nml:52
        'ctrl+e': ProcessSortState,    # process_window.nml:53
        'ctrl+l': ProcessSortCpu,    # process_window.nml:54
        'ctrl+z': ProcessSortMemory,    # process_window.nml:55
        'ctrl+n': ProcessSortCommand,    # process_window.nml:56
        'ctrl+t': ProcessTree,    # process_window.nml:57
        'ctrl+h': ProcessMineOnly,    # process_window.nml:58
        'ctrl+s': FilterProcesses,    # process_window.nml:59
        'f4': FilterProcesses,    # process_window.nml:60
        'f3': ProcessDetails,    # process_window.nml:61
        'f7': SignalProcess,    # process_window.nml:62
        'f8': KillProcess,    # process_window.nml:63
        'delete': KillProcess,    # process_window.nml:64
        'tab': SelectNext,    # process_window.nml:65
        'shift+tab': SelectPrevious,    # process_window.nml:66
    }

    #: Ids, annotated so the hand-written half completes them.
    filter_caption: Label    # process_window.nml:70
    filter: ProcessFilter    # process_window.nml:81
    clear_filter: Button    # process_window.nml:90
    processes: ProcessList    # process_window.nml:99
    status: StaticText    # process_window.nml:107
    mine_box: CheckBoxes    # process_window.nml:115
    tree_box: CheckBoxes    # process_window.nml:124
    signal_button: Button    # process_window.nml:133
    kill_button: Button    # process_window.nml:142
    details_button: Button    # process_window.nml:151
    close_button: Button    # process_window.nml:161
    process_menu: SubMenu    # process_window.nml:172

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_clear_filter_click(self, event: _Event) -> bool:    # process_window.nml:90
        """``clear_filter`` raised an event whose handler is ``on_click``."""
        return False

    async def on_processes_chosen(self, event: _Event) -> bool:    # process_window.nml:99
        """``processes`` raised an event whose handler is ``on_chosen``."""
        return False

    async def on_processes_sort_chosen(self, event: _Event) -> bool:    # process_window.nml:99
        """``processes`` raised an event whose handler is ``on_sort_chosen``."""
        return False

    async def on_signal_button_click(self, event: _Event) -> bool:    # process_window.nml:133
        """``signal_button`` raised an event whose handler is ``on_click``."""
        return False

    async def on_kill_button_click(self, event: _Event) -> bool:    # process_window.nml:142
        """``kill_button`` raised an event whose handler is ``on_click``."""
        return False

    async def on_details_button_click(self, event: _Event) -> bool:    # process_window.nml:151
        """``details_button`` raised an event whose handler is ``on_click``."""
        return False

    async def on_close_button_click(self, event: _Event) -> bool:    # process_window.nml:161
        """``close_button`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.filter_caption = Label(parent=self)    # process_window.nml:69
        self.filter = ProcessFilter(parent=self)    # process_window.nml:80
        self.clear_filter = Button(parent=self)    # process_window.nml:89
        self.processes = ProcessList(parent=self)    # process_window.nml:98
        self.status = StaticText(parent=self)    # process_window.nml:106
        self.mine_box = CheckBoxes(parent=self)    # process_window.nml:114
        self.tree_box = CheckBoxes(parent=self)    # process_window.nml:123
        self.signal_button = Button(parent=self)    # process_window.nml:132
        self.kill_button = Button(parent=self)    # process_window.nml:141
        self.details_button = Button(parent=self)    # process_window.nml:150
        self.close_button = Button(parent=self)    # process_window.nml:160
        self.process_menu = SubMenu(parent=self)    # process_window.nml:171
        _w1 = MenuItem(parent=self.process_menu)    # process_window.nml:176
        _w2 = MenuLine(parent=self.process_menu)    # process_window.nml:180
        _w3 = MenuItem(parent=self.process_menu)    # process_window.nml:181
        _w4 = MenuItem(parent=self.process_menu)    # process_window.nml:185
        _w5 = MenuItem(parent=self.process_menu)    # process_window.nml:189
        _w6 = MenuItem(parent=self.process_menu)    # process_window.nml:193
        _w7 = MenuItem(parent=self.process_menu)    # process_window.nml:197
        _w8 = MenuItem(parent=self.process_menu)    # process_window.nml:201
        _w9 = MenuLine(parent=self.process_menu)    # process_window.nml:205
        _w10 = MenuItem(parent=self.process_menu)    # process_window.nml:206
        _w11 = MenuItem(parent=self.process_menu)    # process_window.nml:211
        _w12 = MenuItem(parent=self.process_menu)    # process_window.nml:216
        _w13 = MenuLine(parent=self.process_menu)    # process_window.nml:221
        _w14 = MenuItem(parent=self.process_menu)    # process_window.nml:222
        _w15 = MenuItem(parent=self.process_menu)    # process_window.nml:226
        _w16 = MenuItem(parent=self.process_menu)    # process_window.nml:230
        _w17 = MenuLine(parent=self.process_menu)    # process_window.nml:234
        _w18 = MenuItem(parent=self.process_menu)    # process_window.nml:235

        self.title = _bind(lambda _o: _tr('Process list'), yielding=True)    # process_window.nml:44
        self.min_width = _bind(    # process_window.nml:45
            lambda _o: 50 + max(self.mine_box.width, self.tree_box.width)
        )

        self.filter_caption.x = 2    # process_window.nml:71
        self.filter_caption.y = 1    # process_window.nml:72
        self.filter_caption.width = _bind(    # process_window.nml:73
            lambda _o: self.caption_width(_o.text) + 1
        )
        self.filter_caption.height = 1    # process_window.nml:74
        self.filter_caption.text = _bind(    # process_window.nml:75
            lambda _o: _tr('~F~ilter'),
            yielding=True,
        )
        self.filter_caption.link = _bind(lambda _o: self.filter)    # process_window.nml:76

        self.filter.x = _bind(    # process_window.nml:82
            lambda _o: self.filter_caption.x + self.filter_caption.width
        )
        self.filter.y = 1    # process_window.nml:83
        self.filter.width = _bind(    # process_window.nml:84
            lambda _o: max(1, _o.parent.width - 6 - _o.x)
        )
        self.filter.height = 1    # process_window.nml:85
        self.filter.tooltip = _bind(    # process_window.nml:86
            lambda _o: _tr('Show only the processes whose command, name, user or PID holds this'),
            yielding=True,
        )

        self.clear_filter.flat = True    # process_window.nml:91
        self.clear_filter.x = _bind(lambda _o: max(0, _o.parent.width - 5))    # process_window.nml:92
        self.clear_filter.y = 1    # process_window.nml:93
        self.clear_filter.width = 3    # process_window.nml:94
        self.clear_filter.height = 1    # process_window.nml:95
        self.clear_filter.tooltip = _bind(    # process_window.nml:96
            lambda _o: _tr('Clear the filter'),
            yielding=True,
        )
        self.clear_filter.on_click = self.on_clear_filter_click    # process_window.nml:90

        self.processes.framed = False    # process_window.nml:100
        self.processes.x = 1    # process_window.nml:101
        self.processes.y = 2    # process_window.nml:102
        self.processes.width = _bind(lambda _o: max(0, _o.parent.width - 1))    # process_window.nml:103
        self.processes.height = _bind(lambda _o: max(0, _o.parent.height - 6))    # process_window.nml:104
        self.processes.on_chosen = self.on_processes_chosen    # process_window.nml:99
        self.processes.on_sort_chosen = self.on_processes_sort_chosen    # process_window.nml:99

        self.status.x = 2    # process_window.nml:108
        self.status.y = _bind(lambda _o: max(0, _o.parent.height - 4))    # process_window.nml:109
        self.status.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # process_window.nml:110
        self.status.height = 1    # process_window.nml:111

        self.mine_box.x = 2    # process_window.nml:116
        self.mine_box.y = _bind(lambda _o: max(0, _o.parent.height - 3))    # process_window.nml:117
        self.mine_box.width = _bind(lambda _o: _o.column_x(1))    # process_window.nml:118
        self.mine_box.height = 1    # process_window.nml:119
        self.mine_box.items = _bind(    # process_window.nml:120
            lambda _o: [_tr('~M~ine only')],
            yielding=True,
        )
        self.mine_box.tooltips = _bind(    # process_window.nml:121
            lambda _o: [_tr('Only your own processes')],
            yielding=True,
        )

        self.tree_box.x = 2    # process_window.nml:125
        self.tree_box.y = _bind(lambda _o: max(0, _o.parent.height - 2))    # process_window.nml:126
        self.tree_box.width = _bind(lambda _o: _o.column_x(1))    # process_window.nml:127
        self.tree_box.height = 1    # process_window.nml:128
        self.tree_box.items = _bind(lambda _o: [_tr('~T~ree')], yielding=True)    # process_window.nml:129
        self.tree_box.tooltips = _bind(    # process_window.nml:130
            lambda _o: [_tr('Each process under its parent')],
            yielding=True,
        )

        self.signal_button.text = _bind(    # process_window.nml:134
            lambda _o: _tr('~S~ignal'),
            yielding=True,
        )
        self.signal_button.x = _bind(lambda _o: max(0, _o.parent.width - 47))    # process_window.nml:135
        self.signal_button.y = _bind(lambda _o: max(0, _o.parent.height - 3))    # process_window.nml:136
        self.signal_button.width = 11    # process_window.nml:137
        self.signal_button.height = 2    # process_window.nml:138
        self.signal_button.disabled = _bind(    # process_window.nml:139
            lambda _o: not self.allows('signal')
        )
        self.signal_button.on_click = self.on_signal_button_click    # process_window.nml:133

        self.kill_button.text = _bind(lambda _o: _tr('~K~ill'), yielding=True)    # process_window.nml:143
        self.kill_button.x = _bind(lambda _o: max(0, _o.parent.width - 35))    # process_window.nml:144
        self.kill_button.y = _bind(lambda _o: max(0, _o.parent.height - 3))    # process_window.nml:145
        self.kill_button.width = 9    # process_window.nml:146
        self.kill_button.height = 2    # process_window.nml:147
        self.kill_button.disabled = _bind(lambda _o: not self.allows('signal'))    # process_window.nml:148
        self.kill_button.on_click = self.on_kill_button_click    # process_window.nml:142

        self.details_button.text = _bind(    # process_window.nml:152
            lambda _o: _tr('~D~etails'),
            yielding=True,
        )
        self.details_button.default = True    # process_window.nml:153
        self.details_button.x = _bind(lambda _o: max(0, _o.parent.width - 25))    # process_window.nml:154
        self.details_button.y = _bind(lambda _o: max(0, _o.parent.height - 3))    # process_window.nml:155
        self.details_button.width = 12    # process_window.nml:156
        self.details_button.height = 2    # process_window.nml:157
        self.details_button.disabled = _bind(    # process_window.nml:158
            lambda _o: not self.allows('details')
        )
        self.details_button.on_click = self.on_details_button_click    # process_window.nml:151

        self.close_button.text = _bind(lambda _o: _tr('Close'), yielding=True)    # process_window.nml:162
        self.close_button.x = _bind(lambda _o: max(0, _o.parent.width - 12))    # process_window.nml:163
        self.close_button.y = _bind(lambda _o: max(0, _o.parent.height - 3))    # process_window.nml:164
        self.close_button.width = 10    # process_window.nml:165
        self.close_button.height = 2    # process_window.nml:166
        self.close_button.on_click = self.on_close_button_click    # process_window.nml:161

        self.process_menu.text = _bind(    # process_window.nml:173
            lambda _o: _tr('~P~rocesses'),
            yielding=True,
        )
        self.process_menu.tooltip = _bind(    # process_window.nml:174
            lambda _o: _tr('Sort, search and signal the running processes'),
            yielding=True,
        )
        self.process_menu.after = 'File'    # process_window.nml:175

        _w1.text = _bind(lambda _o: _tr('~R~e-read'), yielding=True)    # process_window.nml:177
        _w1.command = Rescan    # process_window.nml:178
        _w1.key = 'Ctrl-R'    # process_window.nml:179

        _w3.text = _bind(lambda _o: _tr('Sort by ~P~ID'), yielding=True)    # process_window.nml:182
        _w3.command = ProcessSortPid    # process_window.nml:183
        _w3.key = 'Ctrl-P'    # process_window.nml:184

        _w4.text = _bind(lambda _o: _tr('Sort by ~u~ser'), yielding=True)    # process_window.nml:186
        _w4.command = ProcessSortUser    # process_window.nml:187
        _w4.key = 'Ctrl-U'    # process_window.nml:188

        _w5.text = _bind(lambda _o: _tr('Sort by s~t~ate'), yielding=True)    # process_window.nml:190
        _w5.command = ProcessSortState    # process_window.nml:191
        _w5.key = 'Ctrl-E'    # process_window.nml:192

        _w6.text = _bind(lambda _o: _tr('Sort by CPU ~l~oad'), yielding=True)    # process_window.nml:194
        _w6.command = ProcessSortCpu    # process_window.nml:195
        _w6.key = 'Ctrl-L'    # process_window.nml:196

        _w7.text = _bind(lambda _o: _tr('Sort by ~m~emory'), yielding=True)    # process_window.nml:198
        _w7.command = ProcessSortMemory    # process_window.nml:199
        _w7.key = 'Ctrl-Z'    # process_window.nml:200

        _w8.text = _bind(lambda _o: _tr('Sort by comma~n~d'), yielding=True)    # process_window.nml:202
        _w8.command = ProcessSortCommand    # process_window.nml:203
        _w8.key = 'Ctrl-N'    # process_window.nml:204

        _w10.text = _bind(lambda _o: _tr('Tr~e~e'), yielding=True)    # process_window.nml:207
        _w10.tooltip = _bind(    # process_window.nml:208
            lambda _o: _tr('Each process under its parent'),
            yielding=True,
        )
        _w10.command = ProcessTree    # process_window.nml:209
        _w10.key = 'Ctrl-T'    # process_window.nml:210

        _w11.text = _bind(lambda _o: _tr('M~i~ne only'), yielding=True)    # process_window.nml:212
        _w11.tooltip = _bind(    # process_window.nml:213
            lambda _o: _tr('Only your own processes'),
            yielding=True,
        )
        _w11.command = ProcessMineOnly    # process_window.nml:214
        _w11.key = 'Ctrl-H'    # process_window.nml:215

        _w12.text = _bind(lambda _o: _tr('~F~ilter'), yielding=True)    # process_window.nml:217
        _w12.tooltip = _bind(    # process_window.nml:218
            lambda _o: _tr('Show only the processes whose command, name, user or PID holds what is typed'),
            yielding=True,
        )
        _w12.command = FilterProcesses    # process_window.nml:219
        _w12.key = 'F4'    # process_window.nml:220

        _w14.text = _bind(lambda _o: _tr('~D~etails...'), yielding=True)    # process_window.nml:223
        _w14.command = ProcessDetails    # process_window.nml:224
        _w14.key = 'F3'    # process_window.nml:225

        _w15.text = _bind(lambda _o: _tr('~S~ignal...'), yielding=True)    # process_window.nml:227
        _w15.command = SignalProcess    # process_window.nml:228
        _w15.key = 'F7'    # process_window.nml:229

        _w16.text = _bind(lambda _o: _tr('~K~ill...'), yielding=True)    # process_window.nml:231
        _w16.command = KillProcess    # process_window.nml:232
        _w16.key = 'F8'    # process_window.nml:233

        _w18.text = _bind(lambda _o: _tr('~C~lose'), yielding=True)    # process_window.nml:236
        _w18.command = CloseWindow    # process_window.nml:237

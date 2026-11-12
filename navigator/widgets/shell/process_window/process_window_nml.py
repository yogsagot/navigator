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
from navml.widgets.dialog.scroll_bar import ScrollBar    # process_window.nml:13
from navml.widgets.window import Window    # process_window.nml:14
from navkit.i18n import verbatim    # process_window.nml:15

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
    The boxes and the buttons are as wide as their captions, the buttons
    lined up from the right edge, and the window never narrower than all of
    them side by side: the buttons once covered *Mine only* in a window
    opened on an 80-column screen, and a fixed width cut a translated caption.

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
    keys = {    # process_window.nml:50
        'escape': CloseWindow,    # process_window.nml:51
        'ctrl+r': Rescan,    # process_window.nml:52
        'alt+r': Rescan,    # process_window.nml:53
        'ctrl+p': ProcessSortPid,    # process_window.nml:54
        'ctrl+u': ProcessSortUser,    # process_window.nml:55
        'ctrl+e': ProcessSortState,    # process_window.nml:56
        'ctrl+l': ProcessSortCpu,    # process_window.nml:57
        'ctrl+z': ProcessSortMemory,    # process_window.nml:58
        'ctrl+n': ProcessSortCommand,    # process_window.nml:59
        'ctrl+t': ProcessTree,    # process_window.nml:60
        'ctrl+h': ProcessMineOnly,    # process_window.nml:61
        'ctrl+s': FilterProcesses,    # process_window.nml:62
        'f4': FilterProcesses,    # process_window.nml:63
        'f3': ProcessDetails,    # process_window.nml:64
        'f7': SignalProcess,    # process_window.nml:65
        'f8': KillProcess,    # process_window.nml:66
        'delete': KillProcess,    # process_window.nml:67
        'tab': SelectNext,    # process_window.nml:68
        'shift+tab': SelectPrevious,    # process_window.nml:69
    }

    #: Ids, annotated so the hand-written half completes them.
    filter_caption: Label    # process_window.nml:89
    filter: ProcessFilter    # process_window.nml:99
    clear_filter: Button    # process_window.nml:108
    processes: ProcessList    # process_window.nml:120
    hbar: ScrollBar    # process_window.nml:133
    status: StaticText    # process_window.nml:146
    mine_box: CheckBoxes    # process_window.nml:154
    tree_box: CheckBoxes    # process_window.nml:164
    signal_button: Button    # process_window.nml:174
    kill_button: Button    # process_window.nml:185
    details_button: Button    # process_window.nml:196
    close_button: Button    # process_window.nml:208
    process_menu: SubMenu    # process_window.nml:221

    #: The commands this component handles itself.
    async def on_process_sort_pid(self, event: _Any) -> bool:    # process_window.nml:73
        """``ProcessSortPid``."""
        self._sort_by('pid')
        return True

    async def on_process_sort_user(self, event: _Any) -> bool:    # process_window.nml:74
        """``ProcessSortUser``."""
        self._sort_by('user')
        return True

    async def on_process_sort_state(self, event: _Any) -> bool:    # process_window.nml:75
        """``ProcessSortState``."""
        self._sort_by('state')
        return True

    async def on_process_sort_cpu(self, event: _Any) -> bool:    # process_window.nml:76
        """``ProcessSortCpu``."""
        self._sort_by('cpu')
        return True

    async def on_process_sort_memory(self, event: _Any) -> bool:    # process_window.nml:77
        """``ProcessSortMemory``."""
        self._sort_by('memory')
        return True

    async def on_process_sort_command(self, event: _Any) -> bool:    # process_window.nml:78
        """``ProcessSortCommand``."""
        self._sort_by('command')
        return True

    async def on_process_tree(self, event: _Any) -> bool:    # process_window.nml:79
        """``ProcessTree``."""
        self.tree = not self.tree
        return True

    async def on_process_mine_only(self, event: _Any) -> bool:    # process_window.nml:80
        """``ProcessMineOnly``."""
        self.mine_only = not self.mine_only
        return True

    async def on_rescan(self, event: _Any) -> bool:    # process_window.nml:81
        """``Rescan``."""
        self.reload()
        return True

    async def on_select_next(self, event: _Any) -> bool:    # process_window.nml:82
        """``SelectNext``."""
        self._step(1)
        return True

    async def on_select_previous(self, event: _Any) -> bool:    # process_window.nml:83
        """``SelectPrevious``."""
        self._step(-1)
        return True

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_clear_filter_click(self, event: _Event) -> bool:    # process_window.nml:108
        """``clear_filter`` raised an event whose handler is ``on_click``."""
        return False

    async def on_processes_chosen(self, event: _Event) -> bool:    # process_window.nml:120
        """``processes`` raised an event whose handler is ``on_chosen``."""
        return False

    async def on_processes_sort_chosen(self, event: _Event) -> bool:    # process_window.nml:120
        """``processes`` raised an event whose handler is ``on_sort_chosen``."""
        return False

    async def on_hbar_scroll(self, event: _Event) -> bool:    # process_window.nml:133
        """``hbar`` raised an event whose handler is ``on_scroll``."""
        return False

    async def on_signal_button_click(self, event: _Event) -> bool:    # process_window.nml:174
        """``signal_button`` raised an event whose handler is ``on_click``."""
        return False

    async def on_kill_button_click(self, event: _Event) -> bool:    # process_window.nml:185
        """``kill_button`` raised an event whose handler is ``on_click``."""
        return False

    async def on_details_button_click(self, event: _Event) -> bool:    # process_window.nml:196
        """``details_button`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.filter_caption = Label(parent=self)    # process_window.nml:88
        self.filter = ProcessFilter(parent=self)    # process_window.nml:98
        self.clear_filter = Button(parent=self)    # process_window.nml:107
        self.processes = ProcessList(parent=self)    # process_window.nml:119
        self.hbar = ScrollBar(parent=self)    # process_window.nml:132
        self.status = StaticText(parent=self)    # process_window.nml:145
        self.mine_box = CheckBoxes(parent=self)    # process_window.nml:153
        self.tree_box = CheckBoxes(parent=self)    # process_window.nml:163
        self.signal_button = Button(parent=self)    # process_window.nml:173
        self.kill_button = Button(parent=self)    # process_window.nml:184
        self.details_button = Button(parent=self)    # process_window.nml:195
        self.close_button = Button(parent=self)    # process_window.nml:207
        self.process_menu = SubMenu(parent=self)    # process_window.nml:220
        _w1 = MenuItem(parent=self.process_menu)    # process_window.nml:223
        _w2 = MenuLine(parent=self.process_menu)    # process_window.nml:224
        _w3 = MenuItem(parent=self.process_menu)    # process_window.nml:225
        _w4 = MenuItem(parent=self.process_menu)    # process_window.nml:226
        _w5 = MenuItem(parent=self.process_menu)    # process_window.nml:227
        _w6 = MenuItem(parent=self.process_menu)    # process_window.nml:228
        _w7 = MenuItem(parent=self.process_menu)    # process_window.nml:229
        _w8 = MenuItem(parent=self.process_menu)    # process_window.nml:230
        _w9 = MenuLine(parent=self.process_menu)    # process_window.nml:231
        _w10 = MenuItem(parent=self.process_menu)    # process_window.nml:232
        _w11 = MenuItem(parent=self.process_menu)    # process_window.nml:234
        _w12 = MenuItem(parent=self.process_menu)    # process_window.nml:236
        _w13 = MenuLine(parent=self.process_menu)    # process_window.nml:238
        _w14 = MenuItem(parent=self.process_menu)    # process_window.nml:239
        _w15 = MenuItem(parent=self.process_menu)    # process_window.nml:240
        _w16 = MenuItem(parent=self.process_menu)    # process_window.nml:241
        _w17 = MenuLine(parent=self.process_menu)    # process_window.nml:242
        _w18 = MenuItem(parent=self.process_menu)    # process_window.nml:243

        self.title = _bind(lambda _o: _tr('Process list'), yielding=True)    # process_window.nml:47
        self.min_width = _bind(    # process_window.nml:48
            lambda _o: max(self.mine_box.width, self.tree_box.width) + self.signal_button.width + self.kill_button.width + self.details_button.width + self.close_button.width + 8
        )
        self.first_focus = _bind(lambda _o: self.processes)    # process_window.nml:85

        self.filter_caption.x = 2    # process_window.nml:90
        self.filter_caption.y = 1    # process_window.nml:91
        self.filter_caption.width = _bind(    # process_window.nml:92
            lambda _o: self.caption_width(_o.text) + 1
        )
        self.filter_caption.text = _bind(    # process_window.nml:93
            lambda _o: _tr('~F~ilter'),
            yielding=True,
        )
        self.filter_caption.link = _bind(lambda _o: self.filter)    # process_window.nml:94

        self.filter.y = 1    # process_window.nml:100
        self.filter.width = _bind(    # process_window.nml:101
            lambda _o: max(1, _o.parent.width - 6 - _o.x)
        )
        self.filter.tooltip = _bind(    # process_window.nml:104
            lambda _o: _tr('Show only the processes whose command, name, user or PID holds this'),
            yielding=True,
        )
        self.filter.x = _bind(    # process_window.nml:103
            lambda _o: self.filter_caption.x + self.filter_caption.width
        )

        self.clear_filter.text = verbatim('X')    # process_window.nml:110
        self.clear_filter.flat = True    # process_window.nml:111
        self.clear_filter.y = 1    # process_window.nml:112
        self.clear_filter.width = 3    # process_window.nml:113
        self.clear_filter.height = 1    # process_window.nml:114
        self.clear_filter.tooltip = _bind(    # process_window.nml:117
            lambda _o: _tr('Clear the filter'),
            yielding=True,
        )
        self.clear_filter.x = _bind(    # process_window.nml:116
            lambda _o: max(0, _o.parent.width - 2 - _o.width)
        )
        self.clear_filter.on_click = self.on_clear_filter_click    # process_window.nml:108

        self.processes.framed = False    # process_window.nml:121
        self.processes.x = 1    # process_window.nml:123
        self.processes.width = _bind(lambda _o: max(0, _o.parent.width - 1))    # process_window.nml:124
        self.processes.y = 2    # process_window.nml:125
        self.processes.height = _bind(lambda _o: max(0, _o.parent.height - 6))    # process_window.nml:126
        self.processes.on_chosen = self.on_processes_chosen    # process_window.nml:120
        self.processes.on_sort_chosen = self.on_processes_sort_chosen    # process_window.nml:120

        self.hbar.orientation = 'horizontal'    # process_window.nml:134
        self.hbar.visible = _bind(    # process_window.nml:135
            lambda _o: self.processes.overflows_across and _o.width >= 4
        )
        self.hbar.x = _bind(    # process_window.nml:136
            lambda _o: self.processes.x + self.processes.command_x
        )
        self.hbar.width = _bind(lambda _o: max(0, _o.parent.width - 2 - _o.x))    # process_window.nml:137
        self.hbar.height = 1    # process_window.nml:138
        self.hbar.value = _bind(lambda _o: self.processes.x_delta)    # process_window.nml:141
        self.hbar.maximum = _bind(    # process_window.nml:142
            lambda _o: max(0, self.processes.command_span - self.processes.command_room, self.processes.x_delta)
        )
        self.hbar.page = _bind(lambda _o: self.processes.command_room)    # process_window.nml:143
        self.hbar.y = _bind(lambda _o: max(0, _o.parent.height - _o.height))    # process_window.nml:140
        self.hbar.on_scroll = self.on_hbar_scroll    # process_window.nml:133

        self.status.x = 2    # process_window.nml:148
        self.status.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # process_window.nml:149
        self.status.y = _bind(    # process_window.nml:150
            lambda _o: max(0, _o.parent.height - 3 - _o.height)
        )

        self.mine_box.x = 2    # process_window.nml:155
        self.mine_box.width = _bind(lambda _o: _o.column_x(1))    # process_window.nml:156
        self.mine_box.height = 1    # process_window.nml:157
        self.mine_box.items = _bind(    # process_window.nml:160
            lambda _o: [_tr('~M~ine only')],
            yielding=True,
        )
        self.mine_box.tooltips = _bind(    # process_window.nml:161
            lambda _o: [_tr('Only your own processes')],
            yielding=True,
        )
        self.mine_box.y = _bind(    # process_window.nml:159
            lambda _o: max(0, _o.parent.height - 2 - _o.height)
        )

        self.tree_box.x = 2    # process_window.nml:165
        self.tree_box.width = _bind(lambda _o: _o.column_x(1))    # process_window.nml:166
        self.tree_box.height = 1    # process_window.nml:167
        self.tree_box.items = _bind(lambda _o: [_tr('~T~ree')], yielding=True)    # process_window.nml:170
        self.tree_box.tooltips = _bind(    # process_window.nml:171
            lambda _o: [_tr('Each process under its parent')],
            yielding=True,
        )
        self.tree_box.y = _bind(    # process_window.nml:169
            lambda _o: max(0, _o.parent.height - 1 - _o.height)
        )

        self.signal_button.text = _bind(    # process_window.nml:175
            lambda _o: _tr('~S~ignal'),
            yielding=True,
        )
        self.signal_button.width = _bind(    # process_window.nml:176
            lambda _o: self.caption_width(_o.text) + 5
        )
        self.signal_button.height = 2    # process_window.nml:177
        self.signal_button.disabled = _bind(    # process_window.nml:181
            lambda _o: not self.allows('signal')
        )
        self.signal_button.command = SignalProcess    # process_window.nml:182
        self.signal_button.x = _bind(    # process_window.nml:179
            lambda _o: max(0, self.kill_button.x - 1 - _o.width)
        )
        self.signal_button.y = _bind(    # process_window.nml:180
            lambda _o: max(0, _o.parent.height - 1 - _o.height)
        )
        self.signal_button.on_click = self.on_signal_button_click    # process_window.nml:174

        self.kill_button.text = _bind(lambda _o: _tr('~K~ill'), yielding=True)    # process_window.nml:186
        self.kill_button.width = _bind(    # process_window.nml:187
            lambda _o: self.caption_width(_o.text) + 5
        )
        self.kill_button.height = 2    # process_window.nml:188
        self.kill_button.disabled = _bind(lambda _o: not self.allows('signal'))    # process_window.nml:192
        self.kill_button.command = KillProcess    # process_window.nml:193
        self.kill_button.x = _bind(    # process_window.nml:190
            lambda _o: max(0, self.details_button.x - 1 - _o.width)
        )
        self.kill_button.y = _bind(    # process_window.nml:191
            lambda _o: max(0, _o.parent.height - 1 - _o.height)
        )
        self.kill_button.on_click = self.on_kill_button_click    # process_window.nml:185

        self.details_button.text = _bind(    # process_window.nml:197
            lambda _o: _tr('~D~etails'),
            yielding=True,
        )
        self.details_button.default = True    # process_window.nml:198
        self.details_button.width = _bind(    # process_window.nml:199
            lambda _o: self.caption_width(_o.text) + 5
        )
        self.details_button.height = 2    # process_window.nml:200
        self.details_button.disabled = _bind(    # process_window.nml:204
            lambda _o: not self.allows('details')
        )
        self.details_button.command = ProcessDetails    # process_window.nml:205
        self.details_button.x = _bind(    # process_window.nml:202
            lambda _o: max(0, self.close_button.x - 1 - _o.width)
        )
        self.details_button.y = _bind(    # process_window.nml:203
            lambda _o: max(0, _o.parent.height - 1 - _o.height)
        )
        self.details_button.on_click = self.on_details_button_click    # process_window.nml:196

        self.close_button.text = _bind(lambda _o: _tr('Close'), yielding=True)    # process_window.nml:209
        self.close_button.width = _bind(    # process_window.nml:210
            lambda _o: self.caption_width(_o.text) + 5
        )
        self.close_button.height = 2    # process_window.nml:211
        self.close_button.x = _bind(    # process_window.nml:213
            lambda _o: max(0, _o.parent.width - 2 - _o.width)
        )
        self.close_button.y = _bind(    # process_window.nml:214
            lambda _o: max(0, _o.parent.height - 1 - _o.height)
        )

        async def _on_click(event):    # process_window.nml:215
            self.request_close()
            return True
        self.close_button.on_click = _on_click

        self.process_menu.text = _bind(    # process_window.nml:220
            lambda _o: _tr('~P~rocesses'),
            yielding=True,
        )
        self.process_menu.after = 'File'    # process_window.nml:220
        self.process_menu.tooltip = _bind(    # process_window.nml:222
            lambda _o: _tr('Sort, search and signal the running processes'),
            yielding=True,
        )

        _w1.text = _bind(lambda _o: _tr('~R~e-read'), yielding=True)    # process_window.nml:223
        _w1.command = Rescan    # process_window.nml:223
        _w1.key = 'Ctrl-R'    # process_window.nml:223

        _w3.text = _bind(lambda _o: _tr('Sort by ~P~ID'), yielding=True)    # process_window.nml:225
        _w3.command = ProcessSortPid    # process_window.nml:225
        _w3.key = 'Ctrl-P'    # process_window.nml:225

        _w4.text = _bind(lambda _o: _tr('Sort by ~u~ser'), yielding=True)    # process_window.nml:226
        _w4.command = ProcessSortUser    # process_window.nml:226
        _w4.key = 'Ctrl-U'    # process_window.nml:226

        _w5.text = _bind(lambda _o: _tr('Sort by s~t~ate'), yielding=True)    # process_window.nml:227
        _w5.command = ProcessSortState    # process_window.nml:227
        _w5.key = 'Ctrl-E'    # process_window.nml:227

        _w6.text = _bind(lambda _o: _tr('Sort by CPU ~l~oad'), yielding=True)    # process_window.nml:228
        _w6.command = ProcessSortCpu    # process_window.nml:228
        _w6.key = 'Ctrl-L'    # process_window.nml:228

        _w7.text = _bind(lambda _o: _tr('Sort by ~m~emory'), yielding=True)    # process_window.nml:229
        _w7.command = ProcessSortMemory    # process_window.nml:229
        _w7.key = 'Ctrl-Z'    # process_window.nml:229

        _w8.text = _bind(lambda _o: _tr('Sort by comma~n~d'), yielding=True)    # process_window.nml:230
        _w8.command = ProcessSortCommand    # process_window.nml:230
        _w8.key = 'Ctrl-N'    # process_window.nml:230

        _w10.text = _bind(lambda _o: _tr('Tr~e~e'), yielding=True)    # process_window.nml:232
        _w10.command = ProcessTree    # process_window.nml:232
        _w10.key = 'Ctrl-T'    # process_window.nml:232
        _w10.tooltip = _bind(    # process_window.nml:233
            lambda _o: _tr('Each process under its parent'),
            yielding=True,
        )

        _w11.text = _bind(lambda _o: _tr('M~i~ne only'), yielding=True)    # process_window.nml:234
        _w11.command = ProcessMineOnly    # process_window.nml:234
        _w11.key = 'Ctrl-H'    # process_window.nml:234
        _w11.tooltip = _bind(    # process_window.nml:235
            lambda _o: _tr('Only your own processes'),
            yielding=True,
        )

        _w12.text = _bind(lambda _o: _tr('~F~ilter'), yielding=True)    # process_window.nml:236
        _w12.command = FilterProcesses    # process_window.nml:236
        _w12.key = 'F4'    # process_window.nml:236
        _w12.tooltip = _bind(    # process_window.nml:237
            lambda _o: _tr('Show only the processes whose command, name, user or PID holds what is typed'),
            yielding=True,
        )

        _w14.text = _bind(lambda _o: _tr('~D~etails...'), yielding=True)    # process_window.nml:239
        _w14.command = ProcessDetails    # process_window.nml:239
        _w14.key = 'F3'    # process_window.nml:239

        _w15.text = _bind(lambda _o: _tr('~S~ignal...'), yielding=True)    # process_window.nml:240
        _w15.command = SignalProcess    # process_window.nml:240
        _w15.key = 'F7'    # process_window.nml:240

        _w16.text = _bind(lambda _o: _tr('~K~ill...'), yielding=True)    # process_window.nml:241
        _w16.command = KillProcess    # process_window.nml:241
        _w16.key = 'F8'    # process_window.nml:241

        _w18.text = _bind(lambda _o: _tr('~C~lose'), yielding=True)    # process_window.nml:243
        _w18.command = CloseWindow    # process_window.nml:243

        self._navml_built(__class__)
